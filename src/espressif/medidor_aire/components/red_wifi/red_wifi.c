#include <string.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "freertos/event_groups.h"
#include "esp_system.h"
#include "esp_wifi.h"
#include "esp_event.h"
#include "esp_log.h"
#include "red_wifi.h"
#include "mqtt_client.h"
#include "sensor_sgp30.h"

// Macros heredadas de tu Kconfig
#define EXAMPLE_ESP_WIFI_SSID      CONFIG_ESP_WIFI_SSID
#define EXAMPLE_ESP_WIFI_PASS      CONFIG_ESP_WIFI_PASSWORD
#define EXAMPLE_ESP_MAXIMUM_RETRY  CONFIG_ESP_MAXIMUM_RETRY

// (Omito las macros de seguridad WPA3/WEP por brevedad, pero puedes pegarlas aquí tal cual estaban en el original)

static EventGroupHandle_t s_wifi_event_group;
#define WIFI_CONNECTED_BIT BIT0
#define WIFI_FAIL_BIT      BIT1

static const char *TAG = "wifi_comp";
static int s_retry_num = 0;

// Variable global para el cliente MQTT dentro de este archivo
static esp_mqtt_client_handle_t mqtt_client = NULL;

// Handler para gestionar los eventos propios del protocolo MQTT
static void mqtt_event_handler(void *handler_args, esp_event_base_t base, int32_t event_id, void *event_data) {
    esp_mqtt_event_handle_t event = event_data;
    switch ((esp_mqtt_event_id_t)event_id) {
        case MQTT_EVENT_CONNECTED:
            ESP_LOGI(TAG, "MQTT Conectado al broker exitosamente");
            break;
        case MQTT_EVENT_DISCONNECTED:
            ESP_LOGW(TAG, "MQTT Desconectado del broker");
            break;
        case MQTT_EVENT_PUBLISHED:
            ESP_LOGI(TAG, "MQTT Mensaje publicado (msg_id=%d)", event->msg_id);
            break;
        case MQTT_EVENT_ERROR:
            ESP_LOGE(TAG, "MQTT Error crítico");
            break;
        default:
            break;
    }
}

// Función para inicializar el cliente MQTT
static void mqtt_app_start(void) {
    esp_mqtt_client_config_t mqtt_cfg = {
        .broker.address.uri = "mqtt://test.mosquitto.org", // Broker público para pruebas
    };

    ESP_LOGI(TAG, "Iniciando cliente MQTT...");
    mqtt_client = esp_mqtt_client_init(&mqtt_cfg);
    esp_mqtt_client_register_event(mqtt_client, ESP_EVENT_ANY_ID, mqtt_event_handler, NULL);
    esp_mqtt_client_start(mqtt_client);
}

// 1. Crear el handler específico para Wi-Fi
static void wifi_telemetry_handler(void* handler_arg, esp_event_base_t base, int32_t id, void* event_data) {
    if (base == SENSOR_EVENT_BASE && id == SENSOR_EVENT_DATA_READY) {
        sgp30_data_t* data = (sgp30_data_t*)event_data;
        ESP_LOGI(TAG, "[WI-FI] Dato listo para enviar -> CO2: %d ppm | TVOC: %d ppb", data->co2, data->tvoc);

        // ¡Aquí enviaremos el dato por MQTT, HTTP, Websockets, etc!
        if (mqtt_client != NULL) {
            char payload[64];
            // Formateamos el string en formato JSON tal como recomiendan las notas de Espressif
            snprintf(payload, sizeof(payload), "{\"co2eq\":%d,\"tvoc\":%d}", data->co2, data->tvoc);

            // Publicamos: Topic, Payload, Longitud(0=auto), QoS(1), Retain(0)
            int msg_id = esp_mqtt_client_publish(mqtt_client, "/sensor/sgp30/telemetria", payload, 0, 1, 0);
            ESP_LOGI(TAG, "[WI-FI] Dato enviado por MQTT (msg_id=%d) -> %s", msg_id, payload);
        }
    }
}

// El Handler Asíncrono (Exactamente igual que el original)
static void event_handler(void* arg, esp_event_base_t event_base, int32_t event_id, void* event_data) {
    if (event_base == WIFI_EVENT && event_id == WIFI_EVENT_STA_START) {
        esp_wifi_connect();
    } else if (event_base == WIFI_EVENT && event_id == WIFI_EVENT_STA_DISCONNECTED) {
        if (s_retry_num < EXAMPLE_ESP_MAXIMUM_RETRY) {
            esp_wifi_connect();
            s_retry_num++;
            ESP_LOGI(TAG, "Reintentando conectar al AP...");
        } else {
            xEventGroupSetBits(s_wifi_event_group, WIFI_FAIL_BIT);
        }
        ESP_LOGI(TAG,"Fallo al conectar al AP");
    } else if (event_base == IP_EVENT && event_id == IP_EVENT_STA_GOT_IP) {
        ip_event_got_ip_t* event = (ip_event_got_ip_t*) event_data;
        ESP_LOGI(TAG, "IP obtenida:" IPSTR, IP2STR(&event->ip_info.ip));
        s_retry_num = 0;
        xEventGroupSetBits(s_wifi_event_group, WIFI_CONNECTED_BIT);
    }
}

// Nuestra función pública
void red_wifi_start(void) {
    s_wifi_event_group = xEventGroupCreate();

    // ESTO SÍ ES DEL COMPONENTE:
    esp_netif_create_default_wifi_sta();

    wifi_init_config_t cfg = WIFI_INIT_CONFIG_DEFAULT();
    ESP_ERROR_CHECK(esp_wifi_init(&cfg));

    esp_event_handler_instance_t instance_any_id;
    esp_event_handler_instance_t instance_got_ip;
    ESP_ERROR_CHECK(esp_event_handler_instance_register(WIFI_EVENT, ESP_EVENT_ANY_ID, &event_handler, NULL, &instance_any_id));
    ESP_ERROR_CHECK(esp_event_handler_instance_register(IP_EVENT, IP_EVENT_STA_GOT_IP, &event_handler, NULL, &instance_got_ip));

    wifi_config_t wifi_config = {
        .sta = {
            .ssid = EXAMPLE_ESP_WIFI_SSID,
            .password = EXAMPLE_ESP_WIFI_PASS,
            // .threshold.authmode = ESP_WIFI_SCAN_AUTH_MODE_THRESHOLD, // (Añadir si usas las macros WPA3 completas)
        },
    };

    ESP_ERROR_CHECK(esp_wifi_set_mode(WIFI_MODE_STA) );
    ESP_ERROR_CHECK(esp_wifi_set_config(WIFI_IF_STA, &wifi_config) );
    ESP_ERROR_CHECK(esp_wifi_start() );

    ESP_LOGI(TAG, "Antena Wi-Fi iniciada. Esperando conexión...");

    // Opcional: Esperar a que conecte o falle para avisar al main
    EventBits_t bits = xEventGroupWaitBits(s_wifi_event_group, WIFI_CONNECTED_BIT | WIFI_FAIL_BIT, pdFALSE, pdFALSE, portMAX_DELAY);
    /*
    if (bits & WIFI_CONNECTED_BIT) {
        ESP_LOGI(TAG, "¡Conectado exitosamente al SSID:%s!", EXAMPLE_ESP_WIFI_SSID);
    } else if (bits & WIFI_FAIL_BIT) {
        ESP_LOGI(TAG, "Fallo absoluto al conectar al SSID:%s", EXAMPLE_ESP_WIFI_SSID);
    }
    */

    // 2. Dentro de tu función red_wifi_start(void), justo al final (después de comprobar que tienes IP):
    if (bits & WIFI_CONNECTED_BIT) {
        ESP_LOGI(TAG, "¡Conectado exitosamente al SSID:%s!", EXAMPLE_ESP_WIFI_SSID);

        // 1. Arrancamos el cliente MQTT
        mqtt_app_start();

        // 3. Registramos el handler AL ESTAR CONECTADOS
        ESP_ERROR_CHECK(esp_event_handler_register(SENSOR_EVENT_BASE, SENSOR_EVENT_DATA_READY, wifi_telemetry_handler, NULL));

    } else if (bits & WIFI_FAIL_BIT) {
        ESP_LOGI(TAG, "Fallo absoluto al conectar al SSID:%s", EXAMPLE_ESP_WIFI_SSID);
    }
}
