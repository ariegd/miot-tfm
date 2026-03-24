#include <stdio.h>
#include <inttypes.h>
#include "sdkconfig.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "esp_log.h"
#include "driver/i2c.h"
#include "sgp30/sgp30.h"

#define I2C_MASTER_SDA_IO           4
#define I2C_MASTER_SCL_IO           5
#define I2C_MASTER_NUM              0
#define I2C_MASTER_FREQ_HZ          100000

static const char *TAG = "MEDIDOR_AIRE";

// Configuración global extraída de tu documentación
static sgp30_config_t sgp30_config = {
    .i2c_master_port = I2C_MASTER_NUM,
    .i2c_address = 0x58
};

// --- INICIALIZACIÓN DE HARDWARE I2C ---
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
// LA TAREA DEL SENSOR (Independiente y a prueba de fallos)
// ---------------------------------------------------------
void sgp30_task(void *pvParameters) {
    ESP_LOGI(TAG, "Tarea del sensor iniciada. Calentando SGP30...");

    // Inicialización de la API proporcionada en tu documentación
    esp_err_t ret = sgp30_init(&sgp30_config);
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "Fallo al inicializar SGP30");
        vTaskDelete(NULL); // Destruye esta tarea si falla el hardware
    }

    uint8_t serial_id[6];
    if (sgp30_get_serial_id(serial_id) == ESP_OK) {
        ESP_LOGI(TAG, "Sensor listo! Serial ID: %02X%02X%02X%02X%02X%02X",
                 serial_id[0], serial_id[1], serial_id[2],
                 serial_id[3], serial_id[4], serial_id[5]);
    }

    // Variables para el Ritmo Absoluto (Evita el desfase de tiempo)
    TickType_t xLastWakeTime = xTaskGetTickCount();
    const TickType_t xFrequency = pdMS_TO_TICKS(1000); // 1000 ms exactos

    ESP_LOGI(TAG, "Iniciando lecturas periódicas...");

    // Bucle infinito propio de la tarea (Aislado del resto del sistema)
    while (1) {
        // Pausa precisa: el procesador queda libre para otras cosas (como WiFi) durante 1 seg
        vTaskDelayUntil(&xLastWakeTime, xFrequency);

        uint16_t co2, tvoc;
        ret = sgp30_read_measurements(&co2, &tvoc);

        if (ret == ESP_OK) {
            printf("CO2: %d ppm \t TVOC: %d ppb\n", co2, tvoc);
        } else {
            ESP_LOGW(TAG, "Error I2C temporal: %s", esp_err_to_name(ret));
        }
    }
}

// --- FUNCIÓN PRINCIPAL ---
void app_main(void) {
    ESP_LOGI(TAG, "Iniciando hardware base...");
    ESP_ERROR_CHECK(i2c_master_init());

    // Crear la tarea dedicada en FreeRTOS
    // Esto crea un hilo de ejecución totalmente independiente para el sensor
    xTaskCreate(
        sgp30_task,          // Función que ejecuta la tarea
        "sgp30_task",        // Nombre para depuración
        4096,                // Memoria RAM asignada (Stack de 4KB)
    NULL,                // Parámetros (ninguno)
    5,                   // Prioridad alta (Recomendado para tareas I2C)
    NULL                 // Handle de la tarea (no lo necesitamos)
    );

    ESP_LOGI(TAG, "app_main() finalizada. FreeRTOS toma el control de las tareas.");
}
