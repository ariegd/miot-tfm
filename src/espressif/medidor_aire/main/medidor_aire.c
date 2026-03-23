#include <stdio.h>
#include <inttypes.h>
#include "sdkconfig.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "esp_log.h"
#include "driver/i2c.h"       // Controlador de hardware I2C de Espressif
#include "sgp30/sgp30.h"      // El componente que acabas de instalar

// Definimos nuestros pines físicos basados en tu conexión
#define I2C_MASTER_SDA_IO           4
#define I2C_MASTER_SCL_IO           5
#define I2C_MASTER_NUM              0       // Puerto I2C número 0
#define I2C_MASTER_FREQ_HZ          100000  // Frecuencia estándar de 100kHz

static const char *TAG = "MEDIDOR_AIRE";

/**
 * @brief Función para inicializar los pines físicos del ESP32-C3 como I2C
 */
static esp_err_t i2c_master_init(void)
{
    int i2c_master_port = I2C_MASTER_NUM;

    i2c_config_t conf = {
        .mode = I2C_MODE_MASTER,
        .sda_io_num = I2C_MASTER_SDA_IO,
        .sda_pullup_en = GPIO_PULLUP_ENABLE,
        .scl_io_num = I2C_MASTER_SCL_IO,
        .scl_pullup_en = GPIO_PULLUP_ENABLE,
        .master.clk_speed = I2C_MASTER_FREQ_HZ,
    };

    i2c_param_config(i2c_master_port, &conf);

    // Instala el driver en el sistema operativo
    return i2c_driver_install(i2c_master_port, conf.mode, 0, 0, 0);
}

void app_main(void)
{
    ESP_LOGI(TAG, "Iniciando sistema...");

    // 1. Inicializar el hardware (Pines 4 y 5)
    ESP_ERROR_CHECK(i2c_master_init());
    ESP_LOGI(TAG, "Bus I2C inicializado correctamente en pines 4(SDA) y 5(SCL)");

    // 2. Configurar el sensor SGP30
    sgp30_config_t config = {
        .i2c_master_port = I2C_MASTER_NUM,  // Debe coincidir con el puerto inicializado arriba
        .i2c_address = 0x58                 // Dirección por defecto que vimos en el escáner
    };

    // 3. Inicializar el SGP30
    esp_err_t ret = sgp30_init(&config);
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "Error al inicializar el sensor SGP30. Revisa las conexiones.");
        return; // Si falla, detenemos el programa aquí
    }

    // 4. Leer y mostrar el ID de serie único del chip
    uint8_t serial_id[6];
    ret = sgp30_get_serial_id(serial_id);
    if (ret == ESP_OK) {
        ESP_LOGI(TAG, "Sensor detectado! Serial ID: %02X%02X%02X%02X%02X%02X",
                 serial_id[0], serial_id[1], serial_id[2],
                 serial_id[3], serial_id[4], serial_id[5]);
    }

    ESP_LOGI(TAG, "Comenzando las lecturas. El SGP30 necesita unos 15 seg de calentamiento...");

    // Configuramos el tiempo exacto para vTaskDelayUntil
    TickType_t xLastWakeTime;
    const TickType_t xFrequency = pdMS_TO_TICKS(1000); // Exactamente 1000 ms

    // Guardamos la marca de tiempo actual antes de entrar al bucle
    xLastWakeTime = xTaskGetTickCount();

    // 5. Bucle infinito con precisión absoluta
    while (1) {
        // Esta función garantiza que el bucle se ejecute cada 1000ms exactos
        vTaskDelayUntil(&xLastWakeTime, xFrequency);

        uint16_t co2, tvoc;
        ret = sgp30_read_measurements(&co2, &tvoc);

        if (ret == ESP_OK) {
            printf("CO2: %d ppm \t TVOC: %d ppb\n", co2, tvoc);
        } else {
            ESP_LOGW(TAG, "Fallo al leer las mediciones este segundo");
        }
    }
}
