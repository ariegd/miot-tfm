#include <string.h>
#include <sys/socket.h>
#include <netdb.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "freertos/event_groups.h"
#include "esp_system.h"
#include "esp_wifi.h"
#include "esp_event.h"
#include "esp_log.h"
#include "red_wifi.h"
#include "sensor_sgp30.h"
#include <time.h>
#include <sys/time.h>
#include "esp_sntp.h"

// Componente CoAP nativo de ESP-IDF
#include "coap3/coap.h"

// Macros heredadas de tu Kconfig para Wi-Fi
#define EXAMPLE_ESP_WIFI_SSID      CONFIG_ESP_WIFI_SSID
#define EXAMPLE_ESP_WIFI_PASS      CONFIG_ESP_WIFI_PASSWORD
#define EXAMPLE_ESP_MAXIMUM_RETRY  CONFIG_ESP_MAXIMUM_RETRY

// Configuración de red del Servidor CoAP (Gateway / Fog Node)
#define COAP_SERVER_IP             CONFIG_COAP_SERVER_IP  
#define COAP_SERVER_PORT           CONFIG_COAP_SERVER_PORT

static EventGroupHandle_t s_wifi_event_group;
#define WIFI_CONNECTED_BIT BIT0
#define WIFI_FAIL_BIT      BIT1

static const char *TAG = "wifi_coap_client";
static int s_retry_num = 0;

// Contexto y sesión persistente UDP de CoAP
static coap_context_t *coap_ctx = NULL;
static coap_session_t *coap_session = NULL;

// Inicializa el entorno e hilos de red para CoAP sobre UDP
static void coap_client_start(void) {
    ESP_LOGI(TAG, "Configurando sesión cliente CoAP hacia [%s:%s]...", COAP_SERVER_IP, COAP_SERVER_PORT);
    
    coap_address_t dst_addr;
    struct addrinfo hints, *res;
    
    memset(&hints, 0, sizeof(hints));
    hints.ai_family = AF_INET;
    hints.ai_socktype = SOCK_DGRAM; // Protocolo UDP obligatorio para CoAP estándar

    if (getaddrinfo(COAP_SERVER_IP, COAP_SERVER_PORT, &hints, &res) != 0) {
        ESP_LOGE(TAG, "Error: No se pudo resolver la dirección IP del Servidor CoAP");
        return;
    }

    coap_address_init(&dst_addr);
    dst_addr.size = res->ai_addrlen;
    memcpy(&dst_addr.addr, res->ai_addr, res->ai_addrlen);
    freeaddrinfo(res);

    // Crear el contexto global del stack libcoap
    coap_ctx = coap_new_context(NULL);
    if (!coap_ctx) {
        ESP_LOGE(TAG, "Error al crear el contexto de CoAP");
        return;
    }

    // Establecer la sesión cliente UDP sin encriptación (CoAP estándar)
    coap_session = coap_new_client_session(coap_ctx, NULL, &dst_addr, COAP_PROTO_UDP);
    if (!coap_session) {
        ESP_LOGE(TAG, "Fallo al conectar la sesión UDP con el Gateway");
        coap_free_context(coap_ctx);
        coap_ctx = NULL;
        return;
    }

    ESP_LOGI(TAG, "Cliente CoAP inicializado y listo para transmitir.");
}

// Handler reactivo: Se dispara cada vez que el SGP30 publica una lectura en el event loop
static void wifi_telemetry_handler(void* handler_arg, esp_event_base_t base, int32_t id, void* event_data) {
    if (base == SENSOR_EVENT_BASE && id == SENSOR_EVENT_DATA_READY) {
        sgp30_data_t* data = (sgp30_data_t*)event_data;
        
        if (coap_session == NULL) {
            ESP_LOGW(TAG, "Envío CoAP cancelado: la sesión no está lista.");
            return;
        }

        // Obtener el timestamp Unix actual en milisegundos desde el RTC sincronizado por SNTP
        struct timeval tv;
        gettimeofday(&tv, NULL);
        long long t_origen = ((long long)tv.tv_sec * 1000) + (tv.tv_usec / 1000);

        // Formatear el payload estrictamente como JSON para cumplir con la Raspberry Pi
        char payload[64];
        snprintf(payload, sizeof(payload), "{\"co2\":%d,\"t_origen\":%lld}", data->co2, t_origen);

        /* Creación del PDU CoAP:
           - Usamos COAP_MESSAGE_NON (Mensaje No Confirmable): Ideal para telemetría continua (1s) 
           - Método: COAP_REQUEST_POST
        */
        coap_pdu_t *pdu = coap_new_pdu(COAP_MESSAGE_NON, COAP_REQUEST_POST, coap_session);
        if (!pdu) {
            ESP_LOGE(TAG, "Imposible generar un nuevo PDU CoAP");
            return;
        }

        // Registrar la Uri-Path. Equivale a apuntar a: coap://<IP>/co2
        coap_add_option(pdu, COAP_OPTION_URI_PATH, 3, (const uint8_t *)"co2");

        // Añadir cabecera Content-Format: application/json (ID: 50 según IANA)
        uint8_t opt_buf[4];
        coap_add_option(pdu, COAP_OPTION_CONTENT_FORMAT,
                        coap_encode_var_safe(opt_buf, sizeof(opt_buf), COAP_MEDIATYPE_APPLICATION_JSON),
                        opt_buf);

        // Adjuntar los datos medidos al paquete
        coap_add_data(pdu, strlen(payload), (const uint8_t *)payload);

        // Envío asíncrono del datagrama por la red
        coap_mid_t mid = coap_send(coap_session, pdu);
        if (mid == COAP_INVALID_MID) {
            ESP_LOGE(TAG, "Fallo en la transmisión del paquete CoAP");
        } else {
            ESP_LOGI(TAG, "[CoAP POST] Enviado JSON -> %s", payload);
        }

        // Despachar el ciclo interno de Entrada/Salida de libcoap sin bloquear la tarea
        coap_io_process(coap_ctx, COAP_IO_NO_WAIT);
    }
}

// Manejador del ciclo de vida de la conexión Wi-Fi
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
        ESP_LOGI(TAG, "Fallo al conectar al AP");
    } else if (event_base == IP_EVENT && event_id == IP_EVENT_STA_GOT_IP) {
        ip_event_got_ip_t* event = (ip_event_got_ip_t*) event_data;
        ESP_LOGI(TAG, "IP obtenida: " IPSTR, IP2STR(&event->ip_info.ip));
        s_retry_num = 0;
        xEventGroupSetBits(s_wifi_event_group, WIFI_CONNECTED_BIT);
    }
}

// Inicialización del subsistema de red inalámbrica
void red_wifi_start(void) {
    s_wifi_event_group = xEventGroupCreate();

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
        },
    };

    ESP_ERROR_CHECK(esp_wifi_set_mode(WIFI_MODE_STA));
    ESP_ERROR_CHECK(esp_wifi_set_config(WIFI_IF_STA, &wifi_config));
    ESP_ERROR_CHECK(esp_wifi_start());

    ESP_LOGI(TAG, "Antena Wi-Fi iniciada. Esperando conexión...");

    EventBits_t bits = xEventGroupWaitBits(s_wifi_event_group, WIFI_CONNECTED_BIT | WIFI_FAIL_BIT, pdFALSE, pdFALSE, portMAX_DELAY);

    if (bits & WIFI_CONNECTED_BIT) {
        ESP_LOGI(TAG, "¡Conectado exitosamente al SSID: %s!", EXAMPLE_ESP_WIFI_SSID);

        // Inicialización de SNTP apuntando al pool global de servidores de tiempo
        esp_sntp_setoperatingmode(SNTP_OPMODE_POLL);
        esp_sntp_setservername(0, "pool.ntp.org"); 
        esp_sntp_init();
        ESP_LOGI(TAG, "Servicio SNTP inicializado.");

        // 1. Iniciamos la sesión persistente hacia el servidor CoAP de la RPi
        coap_client_start();

        // 2. Registramos el manejador en el bus de eventos global para procesar los datos listos del SGP30
        ESP_ERROR_CHECK(esp_event_handler_register(SENSOR_EVENT_BASE, SENSOR_EVENT_DATA_READY, wifi_telemetry_handler, NULL));

    } else if (bits & WIFI_FAIL_BIT) {
        ESP_LOGI(TAG, "Fallo absoluto al conectar al SSID: %s", EXAMPLE_ESP_WIFI_SSID);
    }
}

