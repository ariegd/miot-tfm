# SGP30 Air Quality Sensor Component for ESP-IDF

This component provides a driver for the Sensirion SGP30 air quality sensor, which measures CO2 and TVOC (Total Volatile Organic Compounds) levels. It's designed to work with the ESP-IDF framework.

## Features

- Easy to use API for SGP30 sensor
- CO2 and TVOC measurements
- Serial ID reading support
- Proper error handling
- Configurable I2C port and address

## Installation

To add this component to your project, run:

```bash
idf.py add-dependency "chiehmin/sgp30^1.0.0"
```

## Usage

```c
#include "sgp30/sgp30.h"

// Initialize the sensor
sgp30_config_t config = {
    .i2c_master_port = 0,  // I2C port number
    .i2c_address = 0x58    // Default SGP30 address
};

esp_err_t ret = sgp30_init(&config);
if (ret != ESP_OK) {
    // Handle error
}

// Read measurements
uint16_t co2, tvoc;
ret = sgp30_read_measurements(&co2, &tvoc);
if (ret == ESP_OK) {
    printf("CO2: %d ppm, TVOC: %d ppb\n", co2, tvoc);
}

// Read serial ID (optional)
uint8_t serial_id[6];
ret = sgp30_get_serial_id(serial_id);
if (ret == ESP_OK) {
    printf("Serial ID: %02X%02X%02X%02X%02X%02X\n",
           serial_id[0], serial_id[1], serial_id[2],
           serial_id[3], serial_id[4], serial_id[5]);
}
```

## API Reference

### Configuration

```c
typedef struct {
    uint8_t i2c_master_port;  // I2C port number
    uint8_t i2c_address;      // I2C device address
} sgp30_config_t;
```

### Functions

- `esp_err_t sgp30_init(const sgp30_config_t* config)` - Initialize the SGP30 sensor
- `esp_err_t sgp30_read_measurements(uint16_t* co2, uint16_t* tvoc)` - Read CO2 and TVOC measurements
- `esp_err_t sgp30_get_serial_id(uint8_t* serial_id)` - Read the sensor's serial ID

## License

Apache License 2.0
