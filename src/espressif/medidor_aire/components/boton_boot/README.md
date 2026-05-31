# Componente: Botón BOOT (`boton_boot`)

Este componente gestiona la interacción física con el botón BOOT integrado en la placa del ESP32-C3, actuando como el interruptor físico de hardware para conmutar el modo de operación del nodo (Wi-Fi/CoAP ⇄ Bluetooth/NimBLE).

## Índice de Contenidos
* [1. Descripción General](#1-descripción-general)
* [2. Filosofía de Diseño Comercial (NVS + Restart)](#2-filosofía-de-diseño-comercial-nvs--restart)
* [3. Flujo de Ejecución del Cambio de Modo](#3-flujo-de-ejecución-del-cambio-de-modo)
* [4. Registro de Errores y Soluciones Técnicas](#4-registro-de-errores-y-soluciones-técnicas)

---

## 1. Descripción General
En dispositivos IoT del mundo real que carecen de pantallas o interfaces complejas, el uso de un botón físico multifunción es el estándar para permitir al usuario interactuar con el entorno de red. 

Este componente configura el pin del botón BOOT (usualmente `GPIO 9` en el ESP32-C3) como una entrada con resistencia de *pull-up* interna y asocia una interrupción por hardware (ISR) para detectar pulsaciones de forma asíncrona, evitando el uso de bucles de consulta (*polling*) que desperdicien ciclos de CPU.

---

## 2. Filosofía de Diseño Comercial (NVS + Restart)
Un error común al iniciar en el desarrollo de sistemas embebidos es intentar apagar la pila Wi-Fi y encender la pila Bluetooth "en caliente" (sobre la marcha en tiempo de ejecución) al presionar un botón. 

### El Secreto de la Industria
Liberar por completo la memoria dinámica (Heap RAM) utilizada por la pila Wi-Fi para inicializar inmediatamente el controlador de radio en modo BLE suele provocar **fragmentación severa de la memoria RAM** y colapsos catastróficos en el coprocesador de radio del chip.

Para solventar esto, este firmware imita el diseño del **99% de los dispositivos IoT comerciales**:
* El dispositivo cuenta con **un único firmware unificado**.
* Utiliza la **Memoria No Volátil (NVS)** para recordar de forma permanente cuál fue la última configuración seleccionada.
* En lugar de conmutar en caliente, el botón altera el estado en la NVS y **fuerza un reinicio limpio del sistema**.

---

## 3. Flujo de Ejecución del Cambio de Modo
Cuando el usuario presiona el botón físico para alternar la conectividad, el componente ejecuta de forma secuencial y segura el siguiente algoritmo de bajo nivel:
```
[Pulsación Física] ➔ 1. ISR detecta flanco de bajada ➔ 2. Cambia 'modo_red' en NVS ➔ 3. esp_restart()
                                                                                                    │
┌───────────────────────────────────────────────────────────────────────────────────────────────────┘
▼
[Reinicio Limpio (1 seg)] ➔ app_main() lee NVS ➔ Inicializa la red seleccionada con RAM 100% limpia
```

1. **Detección**: Se captura la interrupción del botón y se filtra el ruido eléctrico.
2. **Escritura en NVS**: Se invierte el valor de la variable booleana de control (ej. si era `1` [Wi-Fi] se pasa a `0` [BLE]) y se confirma el *commit* en la memoria flash de la NVS.
3. **Reinicio por Software**: Se invoca inmediatamente la función nativa **`esp_restart()`**.
4. **Ciclo de Inicialización**: Al arrancar de nuevo (un proceso limpio que toma apenas 1 segundo), la función principal `app_main()` evalúa la variable mediante un `if (modo_wifi)` e inicia la red correcta con la memoria caché y el direccionamiento físico completamente vacíos y estables.

---

## 4. Registro de Errores y Soluciones Técnicas

### Problema 1: El sensor arranca desfasado o con lecturas iniciales corruptas
* **Causa:** Si se inicializan las pilas de red inalámbricas antes o al mismo tiempo que el sensor de gas SGP30, la negociación de la dirección IP con el router (Wi-Fi) o el levantamiento del stack de radio (BLE) consumen valioso tiempo del procesador e introducen latencias. Como el SGP30 exige una lectura estricta y milimétrica a **1Hz (una vez por segundo)** para estabilizar sus algoritmos internos de línea base (*baseline*), cualquier bloqueo inicial corrompe su calibración interna.
* **Solución:** Modificar el orden de arranque en el `app_main.c`. El sensor SGP30 debe ser tratado con prioridad absoluta o bien su temporizador asíncrono debe correr de forma aislada para que las negociaciones inalámbricas de fondo consuman su tiempo en paralelo sin desfasar el reloj de muestreo de gases.

### Problema 2: Reinicios infinitos o "Efecto Rebote" (*Debouncing*)
* **Causa:** Al presionar un botón mecánico, las láminas metálicas internas rebotan físicamente durante unos pocos milisegundos antes de quedarse fijas. Para el microcontrolador (que corre a 160 MHz), estos rebotes se interpretan como decenas de pulsaciones consecutivas ultrarrápidas, lo que provoca escrituras masivas en la NVS y múltiples llamadas a `esp_restart()`.
* **Solución:** Implementar un filtro por software dentro del manejador del botón. Al detectar la interrupción, se guarda el tiempo actual usando `esp_timer_get_time()` y se descarta cualquier otra interrupción que ocurra dentro de una ventana de tolerancia de 200 a 250 milisegundos.

