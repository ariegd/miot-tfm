#include <stdbool.h>
#include "esp_log.h"
#include "nvs_flash.h"
#include "nvs.h"
#include "driver/gpio.h"
#include "esp_system.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "boton_boot.h"

// En el ESP32-C3, el botón "BOOT" suele estar en el GPIO 9
#define BOOT_BUTTON_PIN 9

static const char *TAG = "BOTON_BOOT";

// 2. Función para leer la NVS
bool leer_modo_desde_nvs() {
    nvs_handle_t my_handle;
    esp_err_t err = nvs_open("storage", NVS_READWRITE, &my_handle);
    uint8_t modo_wifi = 1; // Por defecto 1 (Wi-Fi)

    if (err == ESP_OK) {
        err = nvs_get_u8(my_handle, "modo_red", &modo_wifi);
        if (err == ESP_ERR_NVS_NOT_FOUND) {
            // Si no existe la variable, la creamos con el valor por defecto
            nvs_set_u8(my_handle, "modo_red", modo_wifi);
            nvs_commit(my_handle);
        }
        nvs_close(my_handle);
    }
    return modo_wifi == 1; // Devuelve true si es 1 (Wi-Fi)
}

// 3. Función para cambiar el modo y reiniciar
void alternar_modo_y_reiniciar() {
    bool modo_actual = leer_modo_desde_nvs();
    nvs_handle_t my_handle;

    if (nvs_open("storage", NVS_READWRITE, &my_handle) == ESP_OK) {
        // Guardamos lo contrario a lo que había (!modo_actual)
        nvs_set_u8(my_handle, "modo_red", !modo_actual);
        nvs_commit(my_handle);
        nvs_close(my_handle);
    }

    ESP_LOGW(TAG, "Cambiando de red. Reiniciando dispositivo en 2 segundos...");
    vTaskDelay(pdMS_TO_TICKS(2000));
    esp_restart(); // Reinicio limpio por software
}

// 4. La tarea del botón BOOT
void tarea_vigilar_boton(void *arg) {
    int estado_anterior = 1; // El botón en reposo lee 1 (Pull-up)

    while(1) {
        int estado_actual = gpio_get_level(BOOT_BUTTON_PIN);

        // Si estaba en 1 y ahora es 0, es que lo acabamos de pulsar
        if (estado_actual == 0 && estado_anterior == 1) {
            vTaskDelay(pdMS_TO_TICKS(50)); // Filtro Antirrebote de 50ms

            if (gpio_get_level(BOOT_BUTTON_PIN) == 0) { // Sigue pulsado
                alternar_modo_y_reiniciar();
            }
        }
        estado_anterior = estado_actual;
        vTaskDelay(pdMS_TO_TICKS(100)); // Descansar 100ms para no consumir CPU
    }
}

void configurar_boton_boot() {
    // Configurar el pin físico
    gpio_reset_pin(BOOT_BUTTON_PIN);
    gpio_set_direction(BOOT_BUTTON_PIN, GPIO_MODE_INPUT);
    gpio_set_pull_mode(BOOT_BUTTON_PIN, GPIO_PULLUP_ONLY);

    // Lanzar la tarea que se queda vigilando en segundo plano
    xTaskCreate(tarea_vigilar_boton, "vigilar_boton", 2048, NULL, 5, NULL);
}
