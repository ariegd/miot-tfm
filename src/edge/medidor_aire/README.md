| Supported Targets | ESP32 | ESP32-C2 | ESP32-C3 | ESP32-C5 | ESP32-C6 | ESP32-C61 | ESP32-H2 | ESP32-H21 | ESP32-H4 | ESP32-P4 | ESP32-S2 | ESP32-S3 | Linux |
| ----------------- | ----- | -------- | -------- | -------- | -------- | --------- | -------- | --------- | -------- | -------- | -------- | -------- | ----- |

<img width="571" height="639" alt="Image" src="https://github.com/user-attachments/assets/0f2555e4-00cb-4c86-b136-9e3e796b92b8" />

# Nodo Medidor de Aire (`medidor_aire`)

Este firmware convierte al SoC ESP32-C3 en un nodo inteligente de adquisición de datos ambientales (eCO2 y TVOC) integrado en una arquitectura multinivel Edge-to-Fog mediante CoAP y BLE.

## Índice de Contenidos
* [1. Objetivo del Nodo](#1-objetivo-del-nodo)
* [2. Arquitectura y Tareas en Ejecución](#2-arquitectura-y-tareas-en-ejecución)
* [3. Estructura del Directorio del Proyecto](#3-estructura-del-directorio-del-proyecto)
* [4. Máquina de Estados Finitos (FSM)](#4-máquina-de-estados-finitos-fsm)
* [5. Hardware Requerido y Cableado](#5-hardware-requerido-y-cableado)
* [6. Configuración del Proyecto (Menuconfig)](#6-configuración-del-proyecto-menuconfig)
* [7. Construcción, Flasheo y Monitorización](#7-construcción-flasheo-y-monitorización)
* [8. Ejemplo de Salida en Consola](#8-ejemplo-de-salida-en-consola)
* [9. Diccionario de Errores por Componente](#9-diccionario-de-errores-por-componente)

---

## 1. Objetivo del Nodo

Comportarse como un nodo que realiza lectura de eCO2 y TVOC utilizando el SGP30 Air Quality Sensor Component para ESP-IDF.

---

## 2. Arquitectura y Tareas en Ejecución
El diseño del firmware es completamente reactivo y agnóstico, basándose en tres pilares para optimizar el uso de energía y RAM:

1. **`esp_event_loop`**: Es el cerebro. El sistema permanece en bajo consumo y solo se "despierta" cuando un evento específico llega a este bucle principal.  
2. **Temporizadores por Software (`esp_timer`)**: Usamos timers nativos de Espressif en lugar de retardos bloqueantes (`vTaskDelay`), evitando la creación y el consumo de RAM de tareas adicionales.  
3. **FSM y Manejador de Eventos**: Un motor encargado de evaluar el estado actual y el evento entrante para decidir la acción a tomar y realizar la transición de estado.

---

## 3. Estructura del Directorio del Proyecto

A continuación se muestra una explicación de los archivos en la carpeta del proyecto `gatts_touch`.

```
medidor_aire/
├── CMakeLists.txt              (El CMake global del proyecto)
├── components/
│   ├── sensor_sgp30/           (El Productor)
│   │   ├── CMakeLists.txt
│   │   ├── include/sensor_sgp30.h
│   │   └── sensor_sgp30.c
│   ├── red_wifi/           (El Consumidor Fijo)
│   │   ├── CMakeLists.txt
│   │   ├── include/red_wifi.h
│   │   └── red_wifi.c
│   └── red_ble/            (El Consumidor Portátil)
│   │   ├── CMakeLists.txt
│   │   ├── idf_component.yml      
│   │   ├── Kconfig.projbuild      
│   │   ├── bleprph.h              
│   │   ├── gatt_svr.c             
│   │   ├── include/red_ble.h
│   │   └── red_ble.c
│   ├── boton_boot/           (El Consumidor Fijo)
│   │   ├── CMakeLists.txt
│   │   ├── include/boton_boot.h
│   │   └── boton_boot.c
├── main/                       (El Director de Orquesta)
│   ├── CMakeLists.txt
│   └── medidor_aire_main.c     (Lee botón BOOT, lee NVS, y enciende el modo correcto)
└── sdkconfig
```

---

## 4. Máquina de Estados Finitos (FSM)

### Los Estados (States)
1. **S0: INICIALIZACIÓN (BOOT)**: El ESP32 recibe energía. Se inicializan NVS y el Event Loop.
2. **S1: EVALUACIÓN DE RED**: Se lee la variable `modo_red` desde la NVS y se configura el botón BOOT.
3. **S2: WI-FI & CoAP**: Se conecta al punto de acceso local y levanta la sesión cliente CoAP UDP.
4. **S3: BLUETOOTH (BLE)**: Se inicializa el stack NimBLE y el ESP32 comienza a emitir *Advertising*.
5. **S4: BUCLE PRINCIPAL SENSOR**: Levanta el bus I2C, realiza el *warmup* de 15s del SGP30 y arranca la transmisión a 1Hz.
6. **S5: TRANSICIÓN Y REINICIO**: Invierte el valor del modo en NVS y fuerza un `esp_restart()`.

### Las Transiciones y Eventos

```
S0: BOOT ➔ S1: EVALUAR ➔ S2: WI-FI (Si NVS=1) ➔ S4: SENSOR ACTIVO
➔ S3: BLE   (Si NVS=0) ➔ S4: SENSOR ACTIVO

[Cualquier Estado Activo] ➔ (Pulsación Botón BOOT) ➔ S5: SWAP NVS & RESTART ➔ S0

```

---

## 5. Hardware Requerido y Cableado
* Placa de desarrollo basada en **ESP32-C3 SoC**.
* Sensor de calidad de aire **Sensirion SGP30**.
* Cable de programación USB-C / Micro-USB.

### Mapeo de Pines (I2C)
| Pin SGP30 | Color del Cable (Recomendado) | Pin ESP32-C3 | Descripción |
| :--- | :--- | :--- | :--- |
| **VIN** | 🔴 Rojo | **3V3** | Alimentación principal (3.3V) |
| **GND** | ⚫ Negro | **GND** | Referencia de Tierra Común |
| **SDA** | 🔵 Azul | **GPIO 4** | Línea de Datos I2C |
| **SCL** | 🟡 Amarillo | **GPIO 5** | Línea de Reloj I2C |

> **Nota sobre el Pin 1V8**: En los módulos comerciales del SGP30, este pin es una **salida regulada interna**, no una entrada. No debe conectarse a ninguna fuente externa.

---

## 6. Configuración del Proyecto (Menuconfig)
Antes de compilar, es obligatorio configurar los parámetros del sistema interactivo ejecutando:
```bash
idf.py menuconfig
```

Ajustes Críticos Obligatorios:
1. Redirección de Consola a USB Nativo:
* `Component config` ➔ `ESP System Settings` ➔ `Channel for console output` ➔ `Seleccionar USB Serial/JTAG Controller`.

2. Activación de la Pila Bluetooth:
* `Component config` ➔ `Bluetooth` ➔ `Habilitar casilla Bluetooth`.
* `Bluetooth Host` ➔ `Seleccionar NimBLE` - `BLE only`.

3. Configuración de Red Local (Wi-Fi y Gateway CoAP):
* `Wifi Configuration` ➔ Configurar el SSID y Password de tu router local.
* `CoAP Server Configuration` ➔ Configurar la IP estática real de la Raspberry Pi (Gateway) y el puerto (5683).

## 7. Construcción, Flasheo y Monitorización
Para una puesta en marcha limpia desde la terminal, ejecuta la siguiente secuencia de comandos:
```
# 1. Cargar las variables de entorno de ESP-IDF
. ~/esp/esp-idf/export.sh

# 2. Posicionarse en el directorio del firmware
cd ~/espressif/medidor_aire

# 3. Definir el chip e inicializar configuraciones de memoria
idf.py set-target esp32c3

# 4. Compilar, flashear y abrir el monitor serial en un solo comando
idf.py -p /dev/ttyACM0 flash monitor
```
(Para salir del monitor de telemetría en tiempo real, presiona las teclas `Ctrl + ]`).

## 8. Ejemplo de Salida en Consola
Cuando el nodo arranca de forma exitosa en el bus local, verás logs interactivos similares a este:

```
...
I (2364) wifi_coap_client: ¡Conectado exitosamente al SSID: MOVISTAR_3CB0!
I (2364) wifi_coap_client: Cliente CoAP inicializado y Worker Task desplegada.
I (2364) SENSOR_SGP30: Inicializando sensor (Bloqueo de 15s por Warmup)...
I (17364) SENSOR_SGP30: Warmup completado. Arrancando el motor Productor-Consumidor...
I (18374) wifi_coap_client: [CoAP POST] Enviado (mid=1380) ➔ CO2: 400 ppm
I (19374) wifi_coap_client: [CoAP POST] Enviado (mid=1381) ➔ CO2: 405 ppm
I (20374) wifi_coap_client: [CoAP POST] Enviado (mid=1382) ➔ CO2: 412 ppm
...

```

## 9. Diccionario de Errores por Componente

Para mantener el código modular, cada subsistema cuenta con su propia documentación técnica y su registro de errores comunes resueltos en su directorio local:

* **[Componente Sensor SGP30](https://github.com/ariegd/miot-tfm/tree/esp-idf/src/espressif/medidor_aire/components/sensor_sgp30)**: Inicialización del bus I2C, tiempos de calentamiento (*warmup*) y hardware del sensor de gas.
* **[Componente Botón BOOT](https://github.com/ariegd/miot-tfm/tree/esp-idf/src/espressif/medidor_aire/components/boton_boot)**: Gestion del funcionamiento del botón BOOT.
* **[Componente Conectividad Wi-Fi y CoAP](https://github.com/ariegd/miot-tfm/tree/esp-idf/src/espressif/medidor_aire/components/red_wifi)**: Gestión del stack inalámbrico y cliente nativo de comunicación ligera hacia el Gateway/Fog Node.
* **[Componente Conectividad BLE](https://github.com/ariegd/miot-tfm/tree/esp-idf/src/espressif/medidor_aire/components/red_ble)**: Pila de telemetría local mediante notificaciones NimBLE.
	


    






