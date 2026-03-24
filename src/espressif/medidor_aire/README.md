| Supported Targets | ESP32 | ESP32-C2 | ESP32-C3 | ESP32-C5 | ESP32-C6 | ESP32-C61 | ESP32-H2 | ESP32-H21 | ESP32-H4 | ESP32-P4 | ESP32-S2 | ESP32-S3 | Linux |
| ----------------- | ----- | -------- | -------- | -------- | -------- | --------- | -------- | --------- | -------- | -------- | -------- | -------- | ----- |

# Objetivo del nodo `medidor_aire`
```
Comportarse como un nodo que realiza lectura de eCO2 y TVOC. SGP30 Air Quality Sensor Component for ESP-IDF.
```

##  Tareas en ejecución
Se basa en tres pilares:

1. **esp\_event\_loop**: Es el cerebro. El sistema se queda dormido y solo se "despierta" cuando un evento (un timer que expira) llega a este bucle principal.  
2. **Temporizadores por Software (esp\_timer)**: Usamos timers nativos de Espressif en lugar de delays. No consumen RAM de tareas adicionales.  
3. **FSM y Manejador de Eventos**: Un "motor" que mira el estado actual, el evento que acaba de llegar, y decide qué acción tomar y a qué estado cambiar.

## Directorio del proyecto
A continuación se muestra una explicación de los archivos en la carpeta del proyecto `gatts_touch`.

```
├── CMakeLists.txt
├── main
│   ├── CMakeLists.txt
│   └── medidor_aire.c
├── pytest_hello_world.py
├── README.md
├── sdkconfig
├── sdkconfig.ci
├── sdkconfig.defaults
└── sdkconfig.old
```

## Visualizando la Máquina de Estados Finitos (FSM)
```
INICIALIZACIÓN → CALENTAMIENTO (espera de 15s) → LECTURA_ACTIVA (loop reactivo de 1s). 
```
Si en cualquier punto algo falla catastróficamente, el sistema pasa a **ERROR\_CRÍTICO** y decide cómo reaccionar

### Hardware requerido
* Una placa de desarrollo con ESP32/ESP32-C3 SoC (e.g., ESP32-DevKitC, ESP-WROVER-KIT, etc.).
* Un cable USB para alimentación y programación.

### Configuración del proyecto antes de puesta en marcha
Abrir el menu de configuración del proyecto (`idf.py menuconfig`).

1. En el menu `TOUCH-PAD Configuration  --->`:
* Establecer la configuración de ejemplo.
```
(2) Numero de Touch Pad (GPIO)
(80) Factor de Umbral (%)
(1500) Tiempo de activacion requerido (ms)
```

### Construir y flashear
Construya el proyecto y fórmelo en la placa, luego ejecute la herramienta de monitorización para ver la salida en serie:
Ejecute `idf.py -p PORT flash monitor` para compilar, actualizar y monitorear el proyecto.
(Para salir del monitor serial, escriba ``Ctrl-]``.)

## Ejemplo de Salida

```
...
CO2: 406 ppm    TVOC: 3 ppb
CO2: 400 ppm    TVOC: 0 ppb
CO2: 411 ppm    TVOC: 0 ppb
CO2: 403 ppm    TVOC: 0 ppb
CO2: 404 ppm    TVOC: 0 ppb
CO2: 400 ppm    TVOC: 0 ppb
CO2: 418 ppm    TVOC: 7 ppb
CO2: 406 ppm    TVOC: 0 ppb
CO2: 413 ppm    TVOC: 2 ppb
CO2: 414 ppm    TVOC: 2 ppb
CO2: 405 ppm    TVOC: 0 ppb
CO2: 412 ppm    TVOC: 3 ppb
CO2: 405 ppm    TVOC: 0 ppb
CO2: 400 ppm    TVOC: 0 ppb
CO2: 411 ppm    TVOC: 0 ppb
CO2: 405 ppm    TVOC: 0 ppb
CO2: 400 ppm    TVOC: 0 ppb
CO2: 400 ppm    TVOC: 0 ppb
CO2: 400 ppm    TVOC: 0 ppb
CO2: 400 ppm    TVOC: 0 ppb
CO2: 408 ppm    TVOC: 0 ppb
...

```

## Problemas y soluciones
### Cambiar el puerto de la consola
Se abrirá un menú azul estilo MS-DOS. Navega usando las flechas de tu teclado de la siguiente manera:
1. Ve a Component `config` y presiona Enter.
2. Baja hasta `ESP System Settings` y presiona Enter.
3. Busca la opción que dice `Channel for console output` (probablemente esté puesta en `Default: UART0`). Presiona Enter.
4. En la lista que aparece, selecciona `USB Serial/JTAG Controller` y presiona Enter.


<img width="571" height="639" alt="Image" src="https://github.com/user-attachments/assets/0f2555e4-00cb-4c86-b136-9e3e796b92b8" />

### El cableado ideal quedaría así:
| Pin SGP30 | Color del Cable (Recomendado) | Pin ESP32-C3 |
| :---- | :---- | :---- |
| **VIN** | 🔴 **Rojo** | **3V3** |
| **GND** | ⚫ **Negro** | **GND** |
| **SDA** | 🔵 **Azul** (o Verde) | **GPIO 4** |
| **SCL** | 🟡 **Amarillo** (o Blanco) | **GPIO 5** |


### ¿Qué quiere decir esto?
1. **Hardware perfecto:** Tu ESP32-C3 ha enviado una señal por el cable de datos (SDA) al ritmo del reloj (SCL) preguntando: "¿Hay alguien conectado a este bus?".
2.  **Sensor detectado:** Un dispositivo electrónico ha respondido: "Sí, yo estoy aquí, y mi dirección es la 0x58".
3. **Es indudablemente tu SGP30:** En el mundo de la electrónica, los fabricantes asignan direcciones fijas a sus chips. La dirección I2C universal y de fábrica del sensor de gas SGP30 es, precisamente, 0x58.

<img width="574" height="345" alt="Image" src="https://github.com/user-attachments/assets/68df3ff1-9948-4c5a-ab4b-d406578779d8" />
