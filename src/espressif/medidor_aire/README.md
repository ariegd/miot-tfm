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
    a. Ve a Component `config` y presiona Enter.
    b. Baja hasta `ESP System Settings` y presiona Enter.
    c. Busca la opción que dice `Channel for console output` (probablemente esté puesta en `Default: UART0`). Presiona Enter.
    d. En la lista que aparece, selecciona `USB Serial/JTAG Controller` y presiona Enter.
    
3. Como este ejemplo usa NimBLE, debemos asegurarnos de que el Bluetooth está activado en el sistema base de Espressif. Antes de compilar, ejecuta:
idf.py menuconfig
    a. Ve a `Component config -> Bluetooth`
    b. Habilita `Bluetooth`.
    c. En `Bluetooth Host`, asegúrate de que esté seleccionado `NimBLE - BLE only`.

### Construir y flashear
Construya el proyecto y fórmelo en la placa, luego ejecute la herramienta de monitorización para ver la salida en serie:
Ejecute `idf.py -p PORT flash monitor` para compilar, actualizar y monitorear el proyecto.
(Para salir del monitor serial, escriba ``Ctrl-]``.)

## Ejemplo de Salida
```
...
EVENTO RECIBIDO -> CO2: 400 ppm          TVOC: 0 ppb
EVENTO RECIBIDO -> CO2: 418 ppm          TVOC: 4 ppb
EVENTO RECIBIDO -> CO2: 420 ppm          TVOC: 6 ppb
EVENTO RECIBIDO -> CO2: 418 ppm          TVOC: 7 ppb
EVENTO RECIBIDO -> CO2: 411 ppm          TVOC: 7 ppb
EVENTO RECIBIDO -> CO2: 429 ppm          TVOC: 12 ppb
EVENTO RECIBIDO -> CO2: 418 ppm          TVOC: 12 ppb
EVENTO RECIBIDO -> CO2: 412 ppm          TVOC: 3 ppb
EVENTO RECIBIDO -> CO2: 415 ppm          TVOC: 7 ppb
...

```

## Problemas y soluciones
### ⚠️ Opción 3 (Event Loop). 
Nuestro archivo `sensor_sgp30.c` ya tiene implementado el Event Loop de forma nativa (Option 3). El Event Loop es más adecuado cuando múltiples consumidores necesitan reaccionar al mismo dato. Aunque solo se active una red a la vez, aprovechar la infraestructura de eventos que ya tenemos es el camino de menor resistencia, más escalable, y evita que tengamos que reescribir la lógica de nuestro sensor.

Con estos cambios, el SGP30 publicará el dato al Event Loop global. Como el ESP32 solo habrá arrancado una red (según el valor en la NVS), solo esa red registrará su handler y escuchará los datos, manteniendo la separación de responsabilidades intacta y sin desperdiciar CPU.

### ⚠️ Cómo se diseñan los dispositivos IoT comerciales? 
Un solo firmware, un botón físico para configurar, y la memoria no volátil (NVS) recordando la última configuración. Hay un secreto de la industria muy importante sobre cómo hacer esto en el ESP32: No intentes apagar el Wi-Fi y encender el Bluetooth "en caliente" (sin reiniciar).

Liberar toda la memoria de la pila Wi-Fi para arrancar la de Bluetooth sobre la marcha suele dar problemas de fragmentación de RAM y colapsos en la antena de radio. Lo que hacen el 99% de los dispositivos comerciales es:

1. Detectar el botón.
2. Cambiar una variable en la NVS.
3. Lanzar un reinicio por software (`esp_restart()`).
4. Al arrancar de nuevo (tarda 1 segundo), el `if (modo_wifi)` lee el nuevo estado e inicia la red correcta con la memoria 100% limpia.

Si arrancamos el SGP30 al principio, los segundos que tarde el Wi-Fi en negociar la IP con el router o el BLE en levantar su stack de radio van a consumir tiempo del *warmup* del sensor. Como el SGP30 exige una lectura estricta a 1Hz (una vez por segundo) para calcular bien sus algoritmos internos de línea base (baseline), cualquier bloqueo de red desfasaría el timer y corrompería las medidas iniciales.

### ⚠️ ¿Cómo se soluciona esto en el mundo real del IoT?

En la industria comercial, cuando un dispositivo no tiene pantalla, se utilizan estas alternativas:

* **PIN Estático Único (Impreso en pegatina):** En la fábrica se graba un PIN único y aleatorio en la memoria no volátil (NVS) de cada ESP32 y se imprime en una pegatina debajo del sensor. El código lee ese PIN de la memoria, no de un número fijo en el .c.

* **Derivar el PIN de la MAC:** Se programa una función para que el PIN sea, por ejemplo, los últimos 6 dígitos en base 10 de la dirección MAC única del chip de Espressif. Así, cada dispositivo tiene un PIN distinto que no viaja por el aire.

* **Modo "Just Works" (Sin PIN):** Se configura el Bluetooth para que no pida PIN. La comunicación sigue yendo encriptada por el aire, pero sacrificas la autenticación (cualquiera que esté cerca en el modo emparejamiento podría conectarse). Es lo que usan la mayoría de altavoces o auriculares Bluetooth.

* **Out of Band (OOB):** Se pone un código QR o un chip NFC en el dispositivo. El móvil lee el QR con la cámara y obtiene la clave criptográfica sin tener que teclear nada.
    
### ⚠️ La autopsia del Log (¿Qué pasó realmente?)
El ESP32-C3 y tu SGP30 comparten la misma línea de alimentación de 3.3V.

1. Durante los primeros 15 segundos, el Wi-Fi estaba apagado. El sensor hizo su "warmup" (calentamiento) perfectamente y empezó a medir.  
2. En el segundo 15.1, el Director mandó encender la antena Wi-Fi.  
3. En el segundo 16.6, el ESP32 empezó a transmitir ondas de radio a máxima potencia para negociar la contraseña con "Ariel's-Galaxy". Esto provoca un **pico de consumo de corriente brutal** (puede llegar a 300mA o 400mA en fracciones de segundo).  
4. Como los cables de la protoboard son finos y tienen resistencia, ese tirón de corriente provocó una caída de voltaje momentánea (Brownout). Al ESP32 no le afectó, pero **el SGP30 se quedó sin energía una fracción de segundo y se reinició**.  
5. Cuando el SGP30 se reinicia, olvida su calibración y necesita que le vuelvan a enviar el comando de inicialización (0x2003). Como tu tarea del SGP30 seguía pidiéndole datos a ciegas (0x2008), el sensor asustado respondía con un error (NACK), lo que se traduce en tu log como ESP\_FAIL cada 1 segundo.

### La Solución: El Director debe organizar mejor los tiempos

Para evitar que el pico de arranque del Wi-Fi mate al sensor, la regla de oro en IoT es: **Primero levanta las comunicaciones pesadas (Wi-Fi), deja que la energía se estabilice, y luego encendemos los sensores delicados.**  


### ⚠️ La cruda realidad (y cómo lo solucionan los profesionales)
La documentación que encontraste sobre usar *solo* Timers y Eventos es ideal para cosas que se calculan rápido (como leer un pin digital o una variable). **Pero para leer buses de comunicación lentos y propensos a bloqueos como el I2C, meterlo dentro del Event Loop es un suicidio de código.** Por eso tu código original con el while(1) funcionaba como una roca. ¡Porque el while(1) vivía en su propia tarea aislada\! Si el I2C fallaba, solo esa tarea se pausaba, pero el sistema seguía vivo.  
Vamos a hacer lo que se llama el **Patrón Productor-Consumidor**. Es la arquitectura definitiva:

1. **El Productor:** Una tarea aislada con su while(1) (fuerte, robusta, aislada) que se encarga exclusivamente de pelearse con el SGP30 por I2C.  
2. **El Consumidor:** El Bucle de Eventos. La tarea, una vez lee los datos limpios, se los "dispara" como un evento al resto de tu sistema.

Así tenemos la robustez de FreeRTOS y la elegancia del Event Loop.
Al final hemos dado un rodeo inmenso para darnos cuenta de que: la separación de recursos a nivel embebido requiere **híbridos**. Una tarea sucia (pero segura) que hable con el hardware, y un bucle de eventos limpio que mueva la información.  
Presionamos el botón de flashear (recordamos hacer el ciclo de energía quitando el USB un segundito)

### ⚠️ ¿Qué ha provocado la parálisis?
El Bucle de Eventos por defecto de ESP-IDF corre sobre un único hilo del sistema llamado sys\_evt. Su trabajo es ser rapidísimo repartiendo mensajes.  
Cuando el Timer saltó, le dijo al Bucle de Eventos: *"Ejecuta la lectura del SGP30"*. La función sgp30\_read\_measurements() no es instantánea; envía una señal I2C y se queda "escuchando" el bus esperando a que el sensor haga sus cálculos internos (\~12 milisegundos).  
Como el bus I2C venía de un estado inestable (o requería un reset físico tras tantas pruebas), la función de lectura se quedó esperando una respuesta que nunca llegó. Al estar dentro del sys\_evt, **colapsó el Bucle de Eventos entero**. El procesador se queda en un "deadlock" (abrazo mortal) infinito.

### ⚠️ La solución: Actualizar el CMakeLists.txt de la carpeta main
Añadir la palabra REQUIRES seguida de las librerías que estamos usando ahora (`esp_event` y `esp_timer`). Modifícalo para que quede exactamente así:
```
CMake

idf_component_register(SRCS "medidor_aire.c"
                    INCLUDE_DIRS "."
                    REQUIRES esp_event esp_timer)
```
### ⚠️ Por qué esto es "Buenas Prácticas" y superior al código anterior:
1. **NO hay while(1) con Delay()**: Fíjate que app\_main() termina por completo. El sistema operativo ya no está bloqueado por una pausa lineal. Se queda en un estado de bajo consumo y solo reacciona asíncronamente cuando los temporizadores de esp\_timer (que son muy ligeros) expiran y mandan un mensaje al bucle principal.  
2. **Organización basada en Eventos y FSM**: El código está ordenado lógicamente. Tienes Estados discretos (enum), Mensajes/Eventos claros (enum), y un único Manejador central que decide qué hacer (fsm\_event\_handler). Esto es robusto, fault-tolerant y fácil de escalar (ej: si añades un botón para reiniciar la calibración, solo añades un evento EVENT\_BUTTON\_PRESSED y añades la transición en la FSM).  
3. **Bajo Consumo de RAM y Energía**: Al no tener tareas adicionales dedicadas consumiendo bloques de RAM (Stack) solo para hacer pausas lineales, el sistema es mucho más eficiente a largo plazo.

### ⚠️ La falta de una Máquina de Estados (FSM)
La programación lineal asume que todo va a salir bien siempre: inicias el sensor, esperas, y lees datos por siempre. En el mundo real (y más en IoT), **los sistemas fallan**. El cable del sensor puede soltarse, el bus I2C puede colgarse por ruido electromagnético, o el chip puede necesitar reiniciarse.  
Si no tienes una FSM (Finite State Machine / Máquina de Estados Finitos) o una arquitectura similar:

* **El código se vuelve frágil y anidado:** Terminas usando docenas de variables *booleanas* (is\_sensor\_ready, has\_error, is\_wifi\_connected) y tu código se llena de sentencias if / else ilegibles para intentar adivinar qué está pasando.  
* **Recuperación de errores ineficaz:** En el código anterior, si el I2C falla, simplemente imprimíamos un Warning y seguíamos intentando leer en el siguiente ciclo, chocando contra la pared infinitamente.

**La práctica correcta en Espressif (FSM):**  
El comportamiento del dispositivo debe dividirse en **Estados discretos y mutuamente excluyentes**. Por ejemplo:

1. ESTADO\_INICIALIZACION: Configura el bus I2C. Si tiene éxito, pasa al estado CALENTAMIENTO. Si falla, pasa a ERROR.  
2. ESTADO\_CALENTAMIENTO: Activa un timer de 15 segundos. Al expirar, pasa al estado LECTURA\_ACTIVA.  
3. ESTADO\_LECTURA\_ACTIVA: Lee el I2C cada 1 segundo. Si falla 3 veces seguidas, asume que el sensor se desconectó y pasa a ESTADO\_RECUPERACION.  
4. ESTADO\_RECUPERACION: Resetea el hardware I2C e intenta volver a INICIALIZACION.

### ⚠️ El problema del `while(1)` con `Delay()`
En la programación tradicional (como en Arduino básico o scripts simples), un bucle infinito con pausas es lo habitual (el famoso loop()). Pero en ESP-IDF trabajamos sobre **FreeRTOS** (un Sistema Operativo en Tiempo Real), donde esta práctica rompe toda la filosofía de eficiencia por estas razones:

* **Ceguera asíncrona (Sordera del sistema):** Cuando haces vTaskDelay(1000), estás bloqueando esa tarea de forma estática. Si en ese segundo ocurre un evento crítico (el usuario presiona un botón, el WiFi se desconecta, o entra un mensaje MQTT), tu programa no puede reaccionar hasta que termine el *delay*.  
* **Desperdicio de RAM:** Cada tarea en FreeRTOS requiere su propio bloque de memoria reservada (Stack). Tener una tarea entera (que consume valiosos kilobytes de RAM) solo para ejecutar tres líneas y luego mandarla a dormir con un *delay* es un desperdicio de recursos.  
* **Mala sincronización:** Si tienes múltiples sensores o tareas con diferentes frecuencias (ej. leer I2C cada 1s, parpadear un LED cada 500ms, enviar datos por WiFi cada 10s), un while(1) lineal se vuelve un infierno matemático y de espagueti condicional (if (contador % 10 \== 0)...).

**La práctica correcta en Espressif:** En lugar de bucles infinitos y delays, la programación debe ser **Reactiva / Orientada a Eventos**. Si quieres leer un sensor cada 1 segundo, debes crear un **Temporizador por Software (FreeRTOS Software Timer)**. El temporizador "despierta" a una función de *callback* o lanza un evento exactamente cada segundo, hace la lectura, y el sistema queda libre y escuchando otros eventos. No hay bucles, no hay esperas.

### ⚠️ ¿Por qué los valores son 400 y 0?
El SGP30 es un sensor de línea base (baseline). El aire puro de la atmósfera terrestre tiene aproximadamente 400 ppm (Partes Por Millón) de CO2. El sensor asume que el ambiente donde se enciende es "aire limpio" y establece su mínimo ahí. El valor 0 de TVOC (Compuestos Orgánicos Volátiles Totales) también indica aire sin contaminantes.

### ⚠️ Nota importante sobre la salida
**El calentamiento (Warm-up):** El sensor SGP30 tiene una pequeña placa calefactora interna. Durante los primeros 15 segundos después de encenderlo, las lecturas estarán fijas en `CO2: 400 ppm` y `TVOC: 0 ppb`. No te asustes, es totalmente normal; el sensor se está calibrando térmicamente.

### ⚠️ Añadir la dependencia
Ahora ejecutamos el comando exacto. Esto descargará el driver del SGP30 y actualizará los archivos CMakeLists.txt automáticamente.
```
idf.py add-dependency "chiehmin/sgp30^1.0.0"
```

### ⚠️ ¿Qué quiere decir esto?
1. **Hardware perfecto:** Tu ESP32-C3 ha enviado una señal por el cable de datos (SDA) al ritmo del reloj (SCL) preguntando: "¿Hay alguien conectado a este bus?".
2.  **Sensor detectado:** Un dispositivo electrónico ha respondido: "Sí, yo estoy aquí, y mi dirección es la 0x58".
3. **Es indudablemente tu SGP30:** En el mundo de la electrónica, los fabricantes asignan direcciones fijas a sus chips. La dirección I2C universal y de fábrica del sensor de gas SGP30 es, precisamente, 0x58.

<img width="574" height="345" alt="Image" src="https://github.com/user-attachments/assets/68df3ff1-9948-4c5a-ab4b-d406578779d8" />

### ⚠️ El componente para el sensor SGP30
El más destacado en el ESP Component Registry es:
* Nombre: `chiehmin/sgp30`
* Descripción: SGP30 Air Quality Sensor Component for ESP-IDF. Maneja la lectura de eCO2 y TVOC, así como el ID de serie del chip.

### ⚠️ El misterio del pin "1V8"
En tu módulo hay un pin marcado como 1V8. Mucha gente se confunde y piensa que hay que meterle 1.8V por ahí. En realidad, en estos módulos comerciales, ese pin es una salida. Es el voltaje de 1.8V que el regulador interno de la placa está generando. Se deja ahí por si el usuario necesita alimentar otro pequeño componente a 1.8V, pero tú puedes ignorarlo por completo.

La conversión de 3.3V a 1.8V se hace automáticamente de forma invisible para ti. Así que puedes conectar VIN al 3V3 de tu ESP32-C3 y los pines SDA/SCL de forma directa con total tranquilidad.
