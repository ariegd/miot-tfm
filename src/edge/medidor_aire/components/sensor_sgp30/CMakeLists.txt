idf_component_register(SRCS "sensor_sgp30.c"
                       INCLUDE_DIRS "include"
                       REQUIRES spi_flash esp_event esp_timer)
