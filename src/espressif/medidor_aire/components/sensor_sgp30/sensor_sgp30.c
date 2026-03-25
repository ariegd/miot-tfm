#include <stdio.h>
#include <inttypes.h>
#include "sdkconfig.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "esp_log.h"
#include "esp_event.h"
#include "driver/i2c.h"
#include "sgp30/sgp30.h"
#include "sensor_sgp30.h"

#define I2C_MASTER_SDA_IO           4
#define I2C_MASTER_SCL_IO           5
#define I2C_MASTER_NUM              0
#define I2C_MASTER_FREQ_HZ          100000

static const char *TAG = "SENSOR_SGP30";

ESP_EVENT_DEFINE_BASE(SENSOR_EVENT_BASE);

typedef enum {
    SENSOR_EVENT_DATA_READY
} sensor_event_id_t;

// Estructura para empaquetar los datos y mandarlos por el evento
typedef struct {
    uint16_t co2;
    uint16_t tvoc;
} sgp30_data_t;

static sgp30_config_t sgp30_config = {
    .i2c_master_port = I2C_MASTER_NUM,
    .i2c_address = 0x58
};

static esp_err_t i2c_master_init(void) {
    i2c_config_t conf = {
        .mode = I2C_MODE_MASTER,
        .sda_io_num = I2C_MASTER_SDA_IO,
        .sda_pullup_en = GPIO_PULLUP_ENABLE,
        .scl_io_num = I2C_MASTER_SCL_IO,
        .scl_pullup_en = GPIO_PULLUP_ENABLE,
        .master.clk_speed = I2C_MASTER_FREQ_HZ,
    };
    i2c_param_config(I2C_MASTER_NUM, &conf);
    return i2c_driver_install(I2C_MASTER_NUM, conf.mode, 0, 0, 0);
}

// ---------------------------------------------------------
// EL CONSUMIDOR: Event Handler (Reactivo y Rápido)
// ---------------------------------------------------------
static void sensor_data_handler(void* handler_arg, esp_event_base_t base, int32_t id, void* event_data) {
    if (base == SENSOR_EVENT_BASE && id == SENSOR_EVENT_DATA_READY) {
        // Desempaquetamos los datos que nos llegaron
        sgp30_data_t* data = (sgp30_data_t*)event_data;
        printf("EVENTO RECIBIDO -> CO2: %d ppm \t TVOC: %d ppb\n", data->co2, data->tvoc);

        // ¡Aquí en el futuro mandarás el dato por MQTT o WiFi!
    }
}

// ---------------------------------------------------------
// EL PRODUCTOR: Tarea Aislada I2C (El motor que nunca falla)
// ---------------------------------------------------------
void sgp30_task(void *pvParameters) {
    TickType_t xLastWakeTime = xTaskGetTickCount();
    const TickType_t xFrequency = pdMS_TO_TICKS(1000); // 1 segundo exacto

    while (1) {
        // Pausa precisa y obligatoria para que el sensor respire
        vTaskDelayUntil(&xLastWakeTime, xFrequency);

        uint16_t co2, tvoc;
        esp_err_t ret = sgp30_read_measurements(&co2, &tvoc);

        if (ret == ESP_OK) {
            // Si la lectura es exitosa, empaquetamos y disparamos el evento
            sgp30_data_t sensor_data = { .co2 = co2, .tvoc = tvoc };
            esp_event_post(SENSOR_EVENT_BASE, SENSOR_EVENT_DATA_READY, &sensor_data, sizeof(sgp30_data_t), portMAX_DELAY);
        } else {
            ESP_LOGW(TAG, "Error I2C en la tarea aislada (sin colgar el sistema): %s", esp_err_to_name(ret));
        }
    }
}

// ---------------------------------------------------------
// FUNCIÓN PRINCIPAL
// ---------------------------------------------------------
void sensor_sgp30_start(void) {
    ESP_LOGI(TAG, "Iniciando sistema... Configurando I2C.");
    ESP_ERROR_CHECK(i2c_master_init());

    // Crear el Bucle de Eventos por defecto (La espina dorsal de tu app)
    //ESP_ERROR_CHECK(esp_event_loop_create_default());

    // Registrar el handler para que escuche cuando haya datos
    ESP_ERROR_CHECK(esp_event_handler_register(SENSOR_EVENT_BASE, SENSOR_EVENT_DATA_READY, sensor_data_handler, NULL));

    ESP_LOGI(TAG, "Inicializando sensor (Bloqueo de 15s por Warmup)...");
    if (sgp30_init(&sgp30_config) != ESP_OK) {
        ESP_LOGE(TAG, "Error fatal: No se detecta el SGP30");
        return;
    }
    ESP_LOGI(TAG, "Warmup completado. Arrancando el motor Productor-Consumidor...");

    // Crear la tarea aislada que se peleará con el hardware.
    // Le damos prioridad alta (5) para que los tiempos I2C sean exactos.
    xTaskCreate(sgp30_task, "sgp30_task", 4096, NULL, 5, NULL);
}
