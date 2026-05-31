| Supported Targets | ESP32 | ESP32-C2 | ESP32-C3 | ESP32-C5 | ESP32-C6 | ESP32-C61 | ESP32-H2 | ESP32-H21 | ESP32-H4 | ESP32-P4 | ESP32-S2 | ESP32-S3 | Linux |
| ----------------- | ----- | -------- | -------- | -------- | -------- | --------- | -------- | --------- | -------- | -------- | -------- | -------- | ----- |

<img width="571" height="639" alt="Image" src="https://github.com/user-attachments/assets/0f2555e4-00cb-4c86-b136-9e3e796b92b8" />

# Objetivo del nodo `medidor_aire`
```
Comportarse como un nodo que realiza lectura de eCO2 y TVOC. SGP30 Air Quality Sensor Component para ESP-IDF.
```

## Tareas en ejecución
Se basa en tres pilares:

1. **esp\_event\_loop**: Es el cerebro. El sistema se queda dormido y solo se "despierta" cuando un evento (un timer que expira) llega a este bucle principal.  
2. **Temporizadores por Software (esp\_timer)**: Usamos timers nativos de Espressif en lugar de delays. No consumen RAM de tareas adicionales.  
3. **FSM y Manejador de Eventos**: Un "motor" que mira el estado actual, el evento que acaba de llegar, y decide qué acción tomar y a qué estado cambiar.

## Directorio del proyecto
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

## Visualizando la Máquina de Estados Finitos (FSM)
**📍 Los Estados (States)**

1. **S0: INICIALIZACIÓN (BOOT)**  
   * El ESP32 recibe energía o se reinicia.  
   * Se inicializa la memoria no volátil (NVS).  
2. **S1: EVALUACIÓN DE RED**  
   * Se lee la variable modo\_red desde la memoria NVS.  
   * Se configura la interrupción/tarea del boton\_boot en segundo plano.  
3. **S2: ARRANQUE DE COMUNICACIONES \- WI-FI**  
   * Se inicializa el stack TCP/IP.  
   * El dispositivo se conecta al router y obtiene una IP.  
4. **S3: ARRANQUE DE COMUNICACIONES \- BLUETOOTH (BLE)**  
   * Se inicializa el stack NimBLE y el servidor GATT.  
   * El ESP32 comienza a anunciarse (Advertising).  
5. **S4: ARRANQUE SENSOR (SGP30) Y BUCLE PRINCIPAL**  
   * *A este estado se llega solo tras haber completado S2 o S3.*  
   * Se levanta el bus I2C.  
   * Comienza el *warmup* estricto de 15 segundos.  
   * Arranca el motor Productor-Consumidor (FreeRTOS) con el timer perfectamente sincronizado a 1Hz.  
6. **S5: TRANSICIÓN Y REINICIO**  
   * Se invierte el valor de la red en la memoria NVS.  
   * Se ejecuta esp\_restart() (reinicio por software).

**🔀 Las Transiciones (Transitions) y Eventos**

* **\[ Power ON / Reset \]** ➔ Entra a **S0**  
* **S0** ➔ (Automático al terminar NVS) ➔ **S1**  
* **S1** ➔ (Si NVS \== 1\) ➔ **S2** (Modo Wi-Fi)  
* **S1** ➔ (Si NVS \== 0\) ➔ **S3** (Modo Bluetooth)  
* **S2** o **S3** ➔ (Automático al estabilizar la red) ➔ **S4** (Arranca el sensor)  
* **Desde cualquier estado activo (S2, S3, o S4)** ➔ (Evento: Tarea boton\_boot detecta pulsación) ➔ **S5**  
* **S5** ➔ (Reinicio por software) ➔ Vuelve a **S0**

```
S0: INICIALIZACIÓN (BOOT) → S1: EVALUACIÓN DE RED → S2: ARRANQUE DE COMUNICACIONES \- WI-FI → S3: ARRANQUE DE COMUNICACIONES \- BLUETOOTH (BLE) 
 → S4: ARRANQUE SENSOR (SGP30) Y BUCLE PRINCIPAL → S5: TRANSICIÓN Y REINICIO

```

### Hardware requerido
* Una placa de desarrollo con ESP32/ESP32-C3 SoC (e.g., ESP32-DevKitC, ESP-WROVER-KIT, etc.).
* Un cable USB para alimentación y programación.
* Sensor SGP30 Air Quality Sensor Component
* Cuatro cables macho-hembra

El cableado ideal quedaría así:
| Pin SGP30 | Color del Cable (Recomendado) | Pin ESP32-C3 |
| :---- | :---- | :---- |
| **VIN** | 🔴 **Rojo** | **3V3** |
| **GND** | ⚫ **Negro** | **GND** |
| **SDA** | 🔵 **Azul** (o Verde) | **GPIO 4** |
| **SCL** | 🟡 **Amarillo** (o Blanco) | **GPIO 5** |

### Configuración del proyecto antes de puesta en marcha
1. Ver todos los dispositivos conectados 
```
ls /dev/ttyACM* /dev/ttyUSB*
```
y arrancar idf.py
```
# 1. Cargar el entorno
. ~/esp/esp-idf/export.sh

# 2. Ir al proyecto
cd ~/espressif/medidor_aire

# 3. Flashear y monitorizar
idf.py fullclean            //Si ya habías configurado el target antes, limpia y recompila
idf.py set-target esp32c3
idf.py menuconfig
idf.py build
idf.py -p /dev/ttyACM0 flash
idf.py -p /dev/ttyACM0 monitor

```

2. Abrir el menu de configuración del proyecto (`idf.py menuconfig`).
* a. Ve a Component `config` y presiona Enter.
* b. Baja hasta `ESP System Settings` y presiona Enter.
* c. Busca la opción que dice `Channel for console output` (probablemente esté puesta en `Default: UART0`). Presiona Enter.
* d. En la lista que aparece, selecciona `USB Serial/JTAG Controller` y presiona Enter.
    
3. Como este ejemplo usa NimBLE, debemos asegurarnos de que el Bluetooth está activado en el sistema base de Espressif. Antes de compilar, ejecuta: `idf.py menuconfig`
* a. Ve a `Component config -> Bluetooth`
* b. Habilita `Bluetooth`.
* c. En `Bluetooth Host`, asegúrate de que esté seleccionado `NimBLE - BLE only`.

### Construir y flashear
Construya el proyecto y fórmelo en la placa, luego ejecute la herramienta de monitorización para ver la salida en serie:
* Ejecute `idf.py -p PORT flash monitor` para compilar, actualizar y monitorear el proyecto.
(Para salir del monitor serial, escriba ``Ctrl-]``.)

## Ejemplo de Salida
```
...
I (134290) NimBLE: [BLE] Dato listo para notificar -> CO2: 402 ppm | TVOC: 20 ppb
I (135290) NimBLE: [BLE] Dato listo para notificar -> CO2: 413 ppm | TVOC: 26 ppb
I (136290) NimBLE: [BLE] Dato listo para notificar -> CO2: 406 ppm | TVOC: 28 ppb
I (137290) NimBLE: [BLE] Dato listo para notificar -> CO2: 400 ppm | TVOC: 20 ppb
I (138290) NimBLE: [BLE] Dato listo para notificar -> CO2: 405 ppm | TVOC: 21 ppb
I (139290) NimBLE: [BLE] Dato listo para notificar -> CO2: 416 ppm | TVOC: 24 ppb
I (140290) NimBLE: [BLE] Dato listo para notificar -> CO2: 402 ppm | TVOC: 23 ppb
...

```

## Guías de Errores

Para mantener el código modular, cada subsistema cuenta con su propia documentación técnica y su registro de errores comunes resueltos en su directorio local:

* **[Componente Sensor SGP30](https://github.com/ariegd/miot-tfm/tree/esp-idf/src/espressif/medidor_aire/components/sensor_sgp30)**: Inicialización del bus I2C, tiempos de calentamiento (*warmup*) y hardware del sensor de gas.
* **[Componente Botón BOOT](https://github.com/ariegd/miot-tfm/tree/esp-idf/src/espressif/medidor_aire/components/boton_boot)**: Gestion del funcionamiento del botón BOOT.
* **[Componente Conectividad Wi-Fi y CoAP](https://github.com/ariegd/miot-tfm/tree/esp-idf/src/espressif/medidor_aire/components/red_wifi)**: Gestión del stack inalámbrico y cliente nativo de comunicación ligera hacia el Gateway/Fog Node.
* **[Componente Conectividad BLE](https://github.com/ariegd/miot-tfm/tree/esp-idf/src/espressif/medidor_aire/components/red_ble)**: Pila de telemetría local mediante notificaciones NimBLE.
	


    






