/*
 * SPDX-FileCopyrightText: 2025 Chieh-Min Wang
 *
 * SPDX-License-Identifier: Apache-2.0
 */

#include "sgp30/sgp30.h"
#include "driver/i2c.h"
#include "esp_log.h"
#include <string.h>

static const char *TAG = "sgp30";
static uint8_t s_i2c_port;
static uint8_t s_i2c_addr;

// SGP30 commands
#define SGP30_CMD_INIT_AIR_QUALITY    0x2003
#define SGP30_CMD_MEASURE_AIR_QUALITY 0x2008
#define SGP30_CMD_GET_SERIAL_ID       0x3682

// Command execution delays (in milliseconds)
#define SGP30_WARMUP_TIME_MS          15000  // 15 seconds warmup time
#define SGP30_MEASURE_TIME_MS         12     // 12ms per measurement

static esp_err_t sgp30_write_cmd(uint16_t cmd)
{
    i2c_cmd_handle_t handle = i2c_cmd_link_create();
    i2c_master_start(handle);
    i2c_master_write_byte(handle, (s_i2c_addr << 1) | I2C_MASTER_WRITE, true);
    i2c_master_write_byte(handle, cmd >> 8, true);    // High byte
    i2c_master_write_byte(handle, cmd & 0xFF, true);  // Low byte
    i2c_master_stop(handle);
    esp_err_t ret = i2c_master_cmd_begin(s_i2c_port, handle, pdMS_TO_TICKS(100));
    i2c_cmd_link_delete(handle);
    return ret;
}

esp_err_t sgp30_init(const sgp30_config_t* config)
{
    if (config == NULL) {
        return ESP_ERR_INVALID_ARG;
    }

    // Store configuration
    s_i2c_port = config->i2c_master_port;
    s_i2c_addr = config->i2c_address;

    // Send init air quality command
    esp_err_t ret = sgp30_write_cmd(SGP30_CMD_INIT_AIR_QUALITY);
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "Failed to initialize SGP30");
        return ret;
    }

    // Wait for initialization (15s warmup recommended)
    ESP_LOGI(TAG, "Waiting for SGP30 warmup (%d seconds)...", SGP30_WARMUP_TIME_MS / 1000);
    vTaskDelay(pdMS_TO_TICKS(SGP30_WARMUP_TIME_MS));

    return ESP_OK;
}

esp_err_t sgp30_read_measurements(uint16_t* co2, uint16_t* tvoc)
{
    if (co2 == NULL || tvoc == NULL) {
        return ESP_ERR_INVALID_ARG;
    }

    uint8_t data[6];

    // Send measure command
    esp_err_t ret = sgp30_write_cmd(SGP30_CMD_MEASURE_AIR_QUALITY);
    if (ret != ESP_OK) {
        return ret;
    }

    // Wait for measurement
    vTaskDelay(pdMS_TO_TICKS(SGP30_MEASURE_TIME_MS));

    // Read the data
    i2c_cmd_handle_t handle = i2c_cmd_link_create();
    i2c_master_start(handle);
    i2c_master_write_byte(handle, (s_i2c_addr << 1) | I2C_MASTER_READ, true);
    i2c_master_read(handle, data, 6, I2C_MASTER_LAST_NACK);
    i2c_master_stop(handle);
    ret = i2c_master_cmd_begin(s_i2c_port, handle, pdMS_TO_TICKS(100));
    i2c_cmd_link_delete(handle);

    if (ret == ESP_OK) {
        *co2 = (data[0] << 8) | data[1];
        *tvoc = (data[3] << 8) | data[4];
    }

    return ret;
}

esp_err_t sgp30_get_serial_id(uint8_t* serial_id)
{
    if (serial_id == NULL) {
        return ESP_ERR_INVALID_ARG;
    }

    uint8_t data[6];

    // Send get serial ID command
    esp_err_t ret = sgp30_write_cmd(SGP30_CMD_GET_SERIAL_ID);
    if (ret != ESP_OK) {
        return ret;
    }

    // Read the serial ID
    i2c_cmd_handle_t handle = i2c_cmd_link_create();
    i2c_master_start(handle);
    i2c_master_write_byte(handle, (s_i2c_addr << 1) | I2C_MASTER_READ, true);
    i2c_master_read(handle, data, 6, I2C_MASTER_LAST_NACK);
    i2c_master_stop(handle);
    ret = i2c_master_cmd_begin(s_i2c_port, handle, pdMS_TO_TICKS(100));
    i2c_cmd_link_delete(handle);

    if (ret == ESP_OK) {
        memcpy(serial_id, data, 6);
    }

    return ret;
}
