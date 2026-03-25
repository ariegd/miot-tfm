idf_component_register(SRCS "red_wifi.c"
                    INCLUDE_DIRS "include"
                    REQUIRES esp_wifi nvs_flash sensor_sgp30 espressif__mqtt)
