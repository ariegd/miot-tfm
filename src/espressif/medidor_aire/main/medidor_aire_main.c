/*
 * SPDX-FileCopyrightText: 2010-2022 Espressif Systems (Shanghai) CO LTD
 *
 * SPDX-License-Identifier: CC0-1.0
 */

#include <stdio.h>
#include <inttypes.h>
#include "sdkconfig.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "esp_chip_info.h"
#include "esp_flash.h"
#include "esp_system.h"
#include "sensor_sgp30.h"

void app_main(void)
{
    // 1. Inicializar hardware base (NVS, Event Loop)
    //nvs_init();
    //esp_event_loop_create_default();

    // 2. Arrancar el sensor (Este arranca SIEMPRE, no le importa la red)
    sensor_sgp30_start();
}
