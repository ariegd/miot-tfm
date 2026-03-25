idf_component_register(SRCS "medidor_aire_main.c"
                       PRIV_REQUIRES spi_flash
                       INCLUDE_DIRS ""
                       REQUIRES sensor_sgp30 red_wifi)
