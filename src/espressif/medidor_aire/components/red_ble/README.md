# Componente: Conectividad BLE (`red_ble`)

Este componente gestiona el subsistema de comunicación inalámbrica de corto alcance utilizando la pila nativa **NimBLE** de ESP-IDF, convirtiendo al ESP32-C3 en un servidor GATT capaz de notificar lecturas ambientales localmente en tiempo real.

## Índice de Contenidos
* [1. ¿Por qué NimBLE?](#1-por-qué-nimble)
* [2. Arquitectura del Servidor GATT](#2-arquitectura-del-servidor-gatt)
* [3. Filosofía de Seguridad en Bluetooth IoT Comercial](#3-filosofía-de-seguridad-en-bluetooth-iot-comercial)
* [4. Registro de Errores y Soluciones Técnicas](#4-registro-de-errores-y-soluciones-técnicas)

---

## 1. ¿Por qué NimBLE?
El ESP32-C3 incluye soporte para dos pilas Bluetooth en ESP-IDF: *Bluedroid* y *NimBLE*. Este componente implementa de forma estricta **NimBLE** debido a las siguientes ventajas críticas de ingeniería:
* **Bajo consumo de memoria RAM y Flash**: NimBLE requiere aproximadamente la mitad de espacio que Bluedroid, lo cual fue un factor determinante para solucionar los errores de desbordamiento de partición (`app partition is too small`).
* **Optimización para BLE**: Está diseñado exclusivamente para Bluetooth Low Energy (BLE), eliminando toda la sobrecarga de código de Bluetooth Clásico (BR/EDR).

---

## 2. Arquitectura del Servidor GATT
Al arrancar en modo Bluetooth (cuando la variable en NVS determina `modo_wifi = false`), el componente ejecuta de forma secuencial:

1. **Inicialización**: Levanta el puerto del host NimBLE (`nimble_port_init`) y su tarea en FreeRTOS.
2. **Configuración de GAP**: Define el nombre del dispositivo en la red (por defecto `nimble-bleprph`).
3. **Servidor GATT (`gatt_svr_init`)**: Registra los servicios y características personalizadas para exponer los datos del sensor.

### Formato de Notificación de Telemetría
El componente escucha de forma asíncrona el bucle de eventos global (`esp_event_loop`). Cuando el sensor SGP30 publica una lectura lista, el handler de BLE actualiza el valor de la característica GATT y dispara una **notificación asíncrona** al cliente conectado con el siguiente formato estructurado:

```text
NimBLE: [BLE] Dato listo para notificar -> CO2: 425 ppm | TVOC: 28 ppb
```

## 3. Filosofía de Seguridad en Bluetooth IoT Comercial

Una de las decisiones más críticas en el despliegue de nodos industriales o comerciales es cómo gestionar el emparejamiento seguro (*pairing*) sin añadir pantallas ni teclados al hardware. El código base soporta configuraciones de bonding (ble\_hs\_cfg.sm\_bonding \= 1\) y protección contra ataques Man-In-The-Middle (MITM), permitiendo evaluar diferentes alternativas arquitectónicas de la industria:

* **Opción A: Modo "Just Works" (Recomendado para el prototipo)**: Configura el Bluetooth para establecer un enlace cifrado por el aire de forma transparente, sin requerir la inserción de un PIN físico. Sacrifica la autenticación estricta del cliente a cambio de la máxima usabilidad y automatización.  
* **Opción B: PIN Único Estático vía NVS**: En lugar de quemar un PIN fijo en el código fuente (lo cual es una vulnerabilidad grave), se graba un código numérico aleatorio único de fábrica en la memoria no volátil (NVS) de cada chip. El firmware lee este valor dinámicamente al arrancar para validar el emparejamiento.  
* **Opción C: Derivación por Dirección MAC**: El código genera un algoritmo donde el PIN de emparejamiento se calcula a partir de los últimos bytes de la dirección MAC física y única del silicio de Espressif, evitando que viaje información sensible de configuración.  
* **Opción D: Vinculación Fuera de Banda (OOB)**: Uso de códigos QR impresos en el chasis del dispositivo que el usuario escanea con el móvil para intercambiar las claves criptográficas iniciales de manera 100% segura.

## 4. Registro de Errores y Soluciones Técnicas

### Problema 1: Latencia y Desfase en el Reloj del Sensor (1Hz Jitter)

* **Causa:** Si el stack de radio de Bluetooth se inicializa simultáneamente con el bucle de lectura del sensor SGP30, las ráfagas de consumo eléctrico y la asignación de memoria del controlador de radio pueden retrasar temporalmente la ejecución de los timers por software. El SGP30 requiere una consulta matemática estricta a **1Hz exacto** para que sus algoritmos internos de calibración (*baseline*) no se corrompan.  
* **Solución:** Priorizar el arranque en el hilo principal (medidor\_aire\_main.c). La pila inalámbrica BLE se inicializa primero, y una vez que el host de NimBLE reporta estabilidad, se arranca de manera aislada el temporizador del sensor, garantizando que su intervalo de muestreo sufra de cero latencias.

### Problema 2: El Cliente BLE pierde la conexión tras unos minutos de inactividad

* **Causa:** Los teléfonos móviles modernos (iOS/Android) desconectan agresivamente los periféricos BLE si el nodo IoT solicita parámetros de conexión (*Connection Parameters*) muy lentos o si no responde a los eventos de supervisión (*Supervision Timeout*) debido a bloqueos en otras tareas del sistema.  
* **Solución:** Configurar adecuadamente los intervalos de conexión mínimos y máximos en el host de NimBLE a través de menuconfig (Component config \-\> Bluetooth \-\> NimBLE Options), asegurando rangos de entre 20ms y 40ms, ideales para transmisiones continuas de sensores cada segundo.

---

### ¿Por qué esta estructura es ideal para tu componente BLE?
1. **Justificación del diseño**: Deja claro por qué elegiste NimBLE sobre Bluedroid (un punto excelente para defender en cualquier evaluación técnica o memoria).
2. **Claridad del formato**: Documenta el String exacto de telemetría que expone el nodo, facilitando la integración a cualquiera que desarrolle la aplicación móvil cliente.
3. **Visión industrial**: La sección de seguridad demuestra que el proyecto no es un simple juguete de Arduino, sino que contempla metodologías de despliegue IoT reales y profesionales.
