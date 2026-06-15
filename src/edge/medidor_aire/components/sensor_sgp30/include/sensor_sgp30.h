#pragma once
#include <stdint.h>
#include "esp_event.h"

// 1. Declaramos la base del evento para que otros archivos la vean
ESP_EVENT_DECLARE_BASE(SENSOR_EVENT_BASE);

// 2. Exponemos el ID del evento
typedef enum {
    SENSOR_EVENT_DATA_READY
} sensor_event_id_t;

// 3. Exponemos la estructura de los datos (El paquete)
typedef struct {
    uint16_t co2;
    uint16_t tvoc;
} sgp30_data_t;

void sensor_sgp30_start(void);
