# Componente: Red Wi-Fi & Cliente CoAP (`red_wifi`)

Este componente se encarga de gestionar el ciclo de vida de la interfaz de red inalámbrica en modo Estación (STA) y encapsular la telemetría del sensor para transmitirla mediante el protocolo ligero **CoAP (Constrained Application Protocol)** hacia el Nodo Fog (Gateway).

## Índice de Contenidos
* [1. Descripción General](#1-descripción-general)
* [2. Mapeo y Formato del Recurso CoAP](#2-mapeo-y-formato-del-recurso-coap)
* [3. Arquitectura Interna y Manejo de Buffers](#3-arquitectura-interna-y-manejo-de-buffers)
* [4. Registro de Errores y Soluciones Técnicas](#4-registro-de-errores-y-soluciones-técnicas)

---

## 1. Descripción General
En arquitecturas de Internet de las Cosas (IoT) orientadas a la computación perimetral (*Edge/Fog Computing*), la eficiencia en los mensajes de red es crucial. Aunque inicialmente el nodo contemplaba el uso de MQTT, la infraestructura se migró por completo a **CoAP sobre UDP**. 

Al eliminar la sobrecarga de mantener una conexión TCP persistente y las pesadas cabeceras de MQTT, este componente reduce drásticamente el consumo de energía de la antena de radio del ESP32-C3 y libera valiosa memoria RAM en el microcontrolador.

---

## 2. Mapeo y Formato del Recurso CoAP
El componente implementa el stack nativo **`libcoap`** de ESP-IDF. Está diseñado de forma reactiva y agnóstica: permanece inactivo hasta que el bus de eventos global (`esp_event_loop`) notifica que hay una nueva lectura del sensor (`SENSOR_EVENT_DATA_READY`).

### Especificaciones del Datagrama
* **Método de Petición**: `COAP_REQUEST_POST`
* **Ruta del Recurso (URI-Path)**: `/co2`
* **Tipo de Contenido (Content-Format)**: `text/plain` (ID: 0 según la IANA).
* **Confirmación de Entrega**: Mensaje No Confirmable (`COAP_MESSAGE_NON`). Se transmite en ráfagas de 1Hz (cada 1 segundo); al ser telemetría continua de alta frecuencia, se prioriza la velocidad de red evitando la espera de paquetes ACK.
* **Carga Útil (*Payload*)**: Envía estrictamente el número entero en texto plano de la medición de eCO2 (ej. `"415"`), acoplándose perfectamente al descompresor y analizador sintáctico del script `aiocoap` corriendo en la Raspberry Pi.

---

## 3. Arquitectura Interna y Manejo de Buffers
A diferencia de otros protocolos basados en sockets síncronos, `libcoap` funciona como una máquina de estados abstracta que requiere procesar activamente las colas de entrada y salida de red.

### El Worker de FreeRTOS (`coap_client_worker_task`)
Para evitar retrasos y saturación de memoria, el componente delega el mantenimiento del protocolo a una tarea dedicada en segundo plano dentro del sistema operativo de tiempo real (FreeRTOS):

```
                   ┌──────────────────────────────┐
                   │  esp_event_loop (Lectura)    │
                   └──────────────┬───────────────┘
                                  │ (Dispara Evento 1Hz)
                                  ▼
                   ┌──────────────────────────────┐
                   │    wifi_telemetry_handler    │
                   └──────────────┬───────────────┘
                                  │ (coap_send)
                                  ▼
                ┌──────────────────────────────────────┐
                │ Memory Heap / Sockets UDP de libcoap │
                └──────────────────┬───────────────────┘
                                   │ (Bombea y libera buffers cada 50ms)
                                   ▼
                    ┌──────────────┴───────────────┐
                    │  coap_client_worker_task     │
                    └──────────────────────────────┘
```
Esta tarea en segundo plano ejecuta el método `coap_io_process(coap_ctx, 50);` en un bucle infinito cada 50 milisegundos. Esto garantiza que:
1. Los datagramas UDP expulsados se limpien inmediatamente de la memoria intermedia del chip.
2. El hilo principal del sensor no sufra bloqueos por latencias de red Wi-Fi.

---

## 4. Registro de Errores y Soluciones Técnicas

### Problema 1: El ESP32 reporta éxito en el envío pero el Gateway no recibe nada
* **Sintoma**: La consola imprime `[CoAP POST] Enviado con éxito (mid=XXXX)` pero el servidor en la Raspberry Pi no muestra logs de entrada.
* **Causa**: Al usar mensajes no confirmables (`COAP_MESSAGE_NON`), la función `coap_send()` devuelve éxito si el paquete logró salir físicamente por la antena de radio. Al correr sobre UDP (protocolo no orientado a la conexión), el ESP32 transmite "a ciegas". Si la IP destino configurada es errónea (ej. apuntar a la IP estática `.100` cuando el router reasignó la Pi a la `.43`), los datos se descartan silenciosamente en la red.
* **Solución**: Verificar la IP real del servidor en la Raspberry Pi mediante `hostname -I` e introducirla dinámicamente en el firmware usando el menú interactivo de `idf.py menuconfig` dentro de la sección *CoAP Server Configuration*.

### Problema 2: Fallos intermitentes en la transmisión (`COAP_INVALID_MID`)
```text
E (21374) wifi_coap_client: Fallo en la transmisión del paquete CoAP
```
* Causa: Saturación de los buffers internos de transacciones de libcoap. En las primeras versiones del código, coap_io_process se ejecutaba únicamente dentro del manejador del sensor (una vez por segundo). Al no tener un ciclo de reloj continuo, la cola de memoria se llenaba al tercer envío, provocando pérdidas intermitentes de datos.

* Solución: Creación de la tarea de fondo de FreeRTOS (coap_client_worker_task) configurada con un tamaño de stack de 4096 bytes para bombear el stack de red de forma asíncrona y constante.

### Advertencia de Seguridad DTLS
```
Jan 01 00:03:50.229 EMRG libcoap not compiled for DTLS with Mbed TLS - update Mbed TLS to include DTLS
```
* Causa: libcoap emite una alerta de nivel Emergency indicando que el componente no ha sido compilado con capas de seguridad criptográfica para datagramas (CoAPS).

* Impacto: Ninguno para el prototipo de laboratorio actual. Al tratarse de una red local privada y controlada, prescindir de la sobrecarga computacional de DTLS permite mantener el firmware del ESP32-C3 ligero, rápido y estable.

---

### Beneficios de esta estructura:
1. **Justificación de Diseño Clara**: Explica de manera científica y estructurada por qué se migró de MQTT a CoAP, lo cual es de gran valor para la memoria técnica de tu proyecto.
2. **Documentación del Formato**: Al especificar que el payload es texto plano (`text/plain`) y que la URI-Path es `/co2`, cualquier desarrollador puede entender la integración con la Raspberry Pi sin necesidad de descifrar líneas de código en C.
3. **Explicación del Flujo Libre de Errores**: Deja documentado el porqué de la solución con la tarea *Worker* de FreeRTOS, demostrando un control avanzado de los recursos de tiempo real del chip.
