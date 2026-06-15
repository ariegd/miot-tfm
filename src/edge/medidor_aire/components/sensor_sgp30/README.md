# Componente: Sensor SGP30 (`sensor_sgp30`)

Este componente se encarga de la capa de abstracción de hardware (HAL) para gestionar el sensor de calidad del aire **Sensirion SGP30**, realizando lecturas de eCO2 (CO2 equivalente) y TVOC (Compuestos Orgánicos Volátiles Totales) a través del bus I2C del ESP32-C3.

## Índice de Contenidos
* [1. Descripción General y Hardware](#1-descripción-general-y-hardware)
* [2. Mapeo de Pines e Integración I2C](#2-mapeo-de-pines-e-integración-i2c)
* [3. Arquitectura de Software (Event Loop Nativo)](#3-arquitectura-of-software-event-loop-nativo)
* [4. Registro de Errores y Soluciones Técnicas](#4-registro-de-errores-y-soluciones-técnicas)

---

## 1. Descripción General y Hardware
El SGP30 es un sensor de gas digital basado en tecnología de óxido metálico (*MOx*) con múltiples elementos de detección en un solo chip. El componente utiliza el registro público oficial de Espressif (`chiehmin/sgp30`) como dependencia base para inicializar el dispositivo, leer los números de serie únicos del silicio y gestionar los algoritmos internos de calibración.

### El Ciclo de Calentamiento (*Warmup Phase*)
Al arrancar, el sensor requiere un bloqueo síncrono y estricto de **15 segundos** para que su placa calefactora interna de óxido metálico alcance la temperatura operativa nominal. Durante este período, el sensor estabiliza su química interna y no es capaz de emitir mediciones válidas.

---

## 2. Mapeo de Pines e Integración I2C
El sensor se conecta al controlador maestro I2C interno del ESP32-C3 (Puerto `0`). Tras realizar pruebas de escaneo en caliente, se ha verificado su direccionamiento físico.

* **Dirección I2C de Fábrica**: `0x58` (Fija e inmutable a nivel de hardware).
* **Frecuencia del Bus**: `100 kHz` (I2C Standard Mode).

### Conexión Física (Pinout)
| Pin SGP30 | Pin ESP32-C3 | Descripción |
| :--- | :--- | :--- |
| **VIN** | **3V3** | Alimentación principal (3.3V) compartida con el SoC |
| **GND** | **GND** | Referencia de masa común |
| **SDA** | **GPIO 4** | Línea de datos del bus I2C |
| **SCL** | **GPIO 5** | Línea de reloj del bus I2C |

> ⚠️ **El misterio del pin "1V8"**: En los módulos comerciales del SGP30, este pin es una **salida de voltaje regulada interna** (1.8V) generada por la propia placa de circuito. **No es una entrada de alimentación**. No debe conectarse a ninguna fuente externa o pin del ESP32, ya que podría dañar los pines lógicos del sensor.

---

## 3. Arquitectura de Software (Event Loop Nativo)
Para lograr un desacoplamiento absoluto de componentes (siguiendo la filosofía de diseño modular de Espressif), el sensor se comporta como un **Productor de datos agnóstico**.

El código ejecuta una tarea cíclica de FreeRTOS que realiza la lectura matemática estricta a **1Hz (una vez por segundo)**, tal y como exige el fabricante para evitar que los algoritmos de línea base (*baseline*) diverjan. Al obtener con éxito los datos, en lugar de invocar funciones de red, el componente empaqueta los datos en la estructura `sgp30_data_t` y publica un evento global:

```c
// Envío asíncrono al bus común del sistema
esp_event_post(SENSOR_EVENT_BASE, SENSOR_EVENT_DATA_READY, &sensor_data, sizeof(sgp30_data_t), portMAX_DELAY);
```

Gracias a este enfoque, los componentes consumidores (red\_wifi o red\_ble) se suscriben al bus de forma independiente. Si se cambia de Wi-Fi a Bluetooth mediante el botón físico, la lógica del sensor permanece intacta, garantizando la escalabilidad del sistema.

## 4. Registro de Errores y Soluciones Técnicas**

### Problema 1: Caída del Sensor y Error ESP\_FAIL en Bucle tras encender el Wi-Fi

* **Síntoma**: El sensor inicia y mide bien durante los primeros 15 segundos (fase de calentamiento). En cuanto el firmware activa la antena Wi-Fi, la consola se inunda instantáneamente de errores ESP\_FAIL (NACK en el bus I2C) cada segundo.  
* **Autopsia del Log (¿Qué pasó realmente?)**: El ESP32-C3 y el módulo SGP30 comparten la misma línea de alimentación de 3.3V en la protoboard. Al encender la antena Wi-Fi y comenzar la negociación de contraseñas con el Router, el módem del ESP32 demanda un **pico de corriente brutal** de entre 300mA y 400mA en microsegundos.  
  Debido a que los cables de prototipado son finos y tienen resistencia inductiva, se produce una caída de voltaje momentánea (*Brownout*). El ESP32 la soporta, pero el SGP30 sufre un micro-reinicio por falta de energía. Al reiniciarse, pierde su inicialización y espera el comando de arranque (0x2003); como el firmware le sigue pidiendo datos a ciegas (0x2008), el sensor asustado responde con un NACK, rompiendo el bus.  
* **Solución**: El módulo principal (medidor\_aire\_main.c) actúa como director de orquesta organizando los tiempos. Se inicializan primero las interfaces de red inalámbricas y, una vez que el consumo de corriente base de la antena se estabiliza, se arranca el bus I2C y el sensor, evitando cruzar el pico crítico de corriente con la calibración del MOx.

### Problema 2: Desfase temporal en el muestreo (*Interval Jitter*)

* **Causa**: El uso de la función estándar vTaskDelay(pdMS\_TO\_TICKS(1000)) dentro del bucle del sensor no garantiza un muestreo exacto de 1 segundo. Si el planificador de FreeRTOS decide dar prioridad a tareas pesadas de la pila Wi-Fi o CoAP, la lectura puede retrasarse a 1.1s o 1.2s, corrompiendo el cálculo interno de partes por millón (ppm).  
* **Solución**: El componente implementa la ejecución de la lectura mediante un temporizador por hardware dedicado utilizando la API **esp\_timer**, aislando el reloj del sensor de la carga de procesamiento computacional de las interfaces de red.

