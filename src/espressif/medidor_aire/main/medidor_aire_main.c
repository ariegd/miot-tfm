#include "esp_log.h"
#include "nvs_flash.h"
#include "esp_netif.h"
#include "esp_event.h"
#include "sensor_sgp30.h"
#include "red_wifi.h"
#include "red_ble.h"
#include "boton_boot.h"

static const char *TAG = "MEDIDOR_AIRE";

void app_main(void)
{
    // 1. Inicializar hardware base (NVS, Event Loop)
    ESP_ERROR_CHECK(nvs_flash_init());
    ESP_ERROR_CHECK(esp_netif_init());
    ESP_ERROR_CHECK(esp_event_loop_create_default());

    // 3. Leer NVS para saber en qué modo estamos
    bool modo_wifi = leer_modo_desde_nvs();

    // 4. Arrancar solo la red necesaria
    if (modo_wifi) {
        ESP_LOGI(TAG, "Arrancando en modo WI-FI...");
        red_wifi_start();
    } else {
        ESP_LOGI(TAG, "Arrancando en modo BLUETOOTH...");
        red_ble_start();
    }

    // 5. Configurar botón
    configurar_boton_boot();

    // 6. Arrancar el sensor (Este arranca SIEMPRE, no le importa la red)
    sensor_sgp30_start();
}
