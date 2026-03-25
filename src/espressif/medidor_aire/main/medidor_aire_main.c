#include "nvs_flash.h"
#include "esp_netif.h"
#include "esp_event.h"
#include "sensor_sgp30.h"
#include "red_wifi.h"
#include "red_ble.h"

void app_main(void)
{
    // 1. Inicializar hardware base (NVS, Event Loop)
    ESP_ERROR_CHECK(nvs_flash_init());
    ESP_ERROR_CHECK(esp_netif_init());
    ESP_ERROR_CHECK(esp_event_loop_create_default());

    // 2. Arrancar el componente Wi-Fi
    //red_wifi_start();

    // 3. ARRANCAR MODO BLE (Consumidor Portátil)
    red_ble_start();

    // 4. Arrancar el sensor (Este arranca SIEMPRE, no le importa la red)
    sensor_sgp30_start();


    /*
    // 3. Leer NVS para saber en qué modo estamos
    bool modo_wifi = leer_modo_desde_nvs();

    // 4. Arrancar solo la red necesaria (EXCLUSIÓN MUTUA)
    if (modo_wifi) {
        red_wifi_start();
    } else {
        red_ble_start();
    }
    */
}
