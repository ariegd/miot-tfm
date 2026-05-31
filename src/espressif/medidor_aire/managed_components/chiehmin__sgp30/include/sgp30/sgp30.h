/*
 * SPDX-FileCopyrightText: 2025 Chieh-Min Wang
 *
 * SPDX-License-Identifier: Apache-2.0
 */

#pragma once

#include <esp_err.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

/**
 * @brief SGP30 air quality sensor configuration parameters
 */
typedef struct {
    int i2c_master_port;      /*!< I2C port number */
    uint8_t i2c_address;      /*!< I2C address of SGP30 (default 0x58) */
} sgp30_config_t;

/**
 * @brief Initialize the SGP30 sensor
 *
 * This function initializes the SGP30 sensor with the given configuration.
 * It sends the init_air_quality command and waits for the 15s warmup period.
 *
 * @param[in] config Pointer to sgp30_config_t configuration structure
 * @return
 *     - ESP_OK if initialization was successful
 *     - ESP_ERR_INVALID_ARG if config is NULL
 *     - ESP_ERR_TIMEOUT if device not responding
 *     - ESP_FAIL for other errors
 */
esp_err_t sgp30_init(const sgp30_config_t* config);

/**
 * @brief Read CO2 and TVOC measurements from SGP30
 *
 * @param[out] co2  Pointer to store CO2 value (in ppm)
 * @param[out] tvoc Pointer to store TVOC value (in ppb)
 * @return
 *     - ESP_OK if read was successful
 *     - ESP_ERR_INVALID_ARG if either co2 or tvoc is NULL
 *     - ESP_ERR_TIMEOUT if device not responding
 *     - ESP_FAIL for other errors
 */
esp_err_t sgp30_read_measurements(uint16_t* co2, uint16_t* tvoc);

/**
 * @brief Get the SGP30 serial ID
 *
 * @param[out] serial_id Buffer to store the 48-bit serial ID (6 bytes)
 * @return
 *     - ESP_OK if read was successful
 *     - ESP_ERR_INVALID_ARG if serial_id is NULL
 *     - ESP_ERR_TIMEOUT if device not responding
 *     - ESP_FAIL for other errors
 */
esp_err_t sgp30_get_serial_id(uint8_t* serial_id);

#ifdef __cplusplus
}
#endif
