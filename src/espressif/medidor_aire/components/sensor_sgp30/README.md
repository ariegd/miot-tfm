## Problemas y soluciones

### La autopsia del Log (¿Qué pasó realmente?)
El ESP32-C3 y tu SGP30 comparten la misma línea de alimentación de 3.3V.

1. Durante los primeros 15 segundos, el Wi-Fi estaba apagado. El sensor hizo su "warmup" (calentamiento) perfectamente y empezó a medir. 
2. En el segundo 15.1, el Director mandó encender la antena Wi-Fi. 
3. En el segundo 16.6, el ESP32 empezó a transmitir ondas de radio a máxima potencia para negociar la contraseña con "Ariel's-Galaxy". Esto provoca un **pico de consumo de corriente brutal** (puede llegar a 300mA o 400mA en fracciones de segundo). 
4. Como los cables de la protoboard son finos y tienen resistencia, ese tirón de corriente provocó una caída de voltaje momentánea (Brownout). Al ESP32 no le afectó, pero **el SGP30 se quedó sin energía una fracción de segundo y se reinició**. 
5. Cuando el SGP30 se reinicia, olvida su calibración y necesita que le vuelvan a enviar el comando de inicialización (0x2003). Como tu tarea del SGP30 seguía pidiéndole datos a ciegas (0x2008), el sensor asustado respondía con un error (NACK), lo que se traduce en tu log como ESP\_FAIL cada 1 segundo.

### La Solución: El Director debe organizar mejor los tiempos

Para evitar que el pico de arranque del Wi-Fi mate al sensor, la regla de oro en IoT es: **Primero levanta las comunicaciones pesadas (Wi-Fi), deja que la energía se estabilice, y luego encendemos los sensores delicados.** 

---

### La cruda realidad (y cómo lo solucionan los profesionales)
La documentación que encontraste sobre usar *solo* Timers y Eventos es ideal para cosas que se calculan rápido (como leer un pin digital o una variable). **Pero para leer buses de comunicación lentos y propensos a bloqueos como el I2C, meterlo dentro del Event Loop es un suicidio de código.** Por eso tu código original con el while(1) funcionaba como una roca. ¡Porque el while(1) vivía en su propia tarea aislada\! Si el I2C fallaba, solo esa tarea se pausaba, pero el sistema seguía vivo.
Vamos a hacer lo que se llama el **Patrón Productor-Consumidor**. Es la arquitectura definitiva:

1. **El Productor:** Una tarea aislada con su while(1) (fuerte, robusta, aislada) que se encarga exclusivamente de pelearse con el SGP30 por I2C.
2. **El Consumidor:** El Bucle de Eventos. La tarea, una vez lee los datos limpios, se los "dispara" como un evento al resto de tu sistema.

Así tenemos la robustez de FreeRTOS y la elegancia del Event Loop.
Al final hemos dado un rodeo inmenso para darnos cuenta de que: la separación de recursos a nivel embebido requiere **híbridos**. Una tarea sucia (pero segura) que hable con el hardware, y un bucle de eventos limpio que mueva la información. 
Presionamos el botón de flashear (recordamos hacer el ciclo de energía quitando el USB un segundito)

---

### ¿Qué ha provocado la parálisis?
El Bucle de Eventos por defecto de ESP-IDF corre sobre un único hilo del sistema llamado sys\_evt. Su trabajo es ser rapidísimo repartiendo mensajes.
Cuando el Timer saltó, le dijo al Bucle de Eventos: *"Ejecuta la lectura del SGP30"*. La función sgp30\_read\_measurements() no es instantánea; envía una señal I2C y se queda "escuchando" el bus esperando a que el sensor haga sus cálculos internos (\~12 milisegundos).
Como el bus I2C venía de un estado inestable (o requería un reset físico tras tantas pruebas), la función de lectura se quedó esperando una respuesta que nunca llegó. Al estar dentro del sys\_evt, **colapsó el Bucle de Eventos entero**. El procesador se queda en un "deadlock" (abrazo mortal) infinito.

---

### La solución: Actualizar el CMakeLists.txt de la carpeta main
Añadir la palabra REQUIRES seguida de las librerías que estamos usando ahora (`esp_event` y `esp_timer`). Modifícalo para que quede exactamente así:
```
CMake

idf_component_register(SRCS "medidor_aire.c"
                    INCLUDE_DIRS "."
                    REQUIRES esp_event esp_timer)
```

---

### Por qué esto es "Buenas Prácticas" y superior al código anterior:
1. **NO hay while(1) con Delay()**: Fíjate que app\_main() termina por completo. El sistema operativo ya no está bloqueado por una pausa lineal. Se queda en un estado de bajo consumo y solo reacciona asíncronamente cuando los temporizadores de esp\_timer (que son muy ligeros) expiran y mandan un mensaje al bucle principal.
2. **Organización basada en Eventos y FSM**: El código está ordenado lógicamente. Tienes Estados discretos (enum), Mensajes/Eventos claros (enum), y un único Manejador central que decide qué hacer (fsm\_event\_handler). Esto es robusto, fault-tolerant y fácil de escalar (ej: si añades un botón para reiniciar la calibración, solo añades un evento EVENT\_BUTTON\_PRESSED y añades la transición en la FSM).
3. **Bajo Consumo de RAM y Energía**: Al no tener tareas adicionales dedicadas consumiendo bloques de RAM (Stack) solo para hacer pausas lineales, el sistema es mucho más eficiente a largo plazo.

---

### La falta de una Máquina de Estados (FSM)
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

---

### El problema del `while(1)` con `Delay()`
En la programación tradicional (como en Arduino básico o scripts simples), un bucle infinito con pausas es lo habitual (el famoso loop()). Pero en ESP-IDF trabajamos sobre **FreeRTOS** (un Sistema Operativo en Tiempo Real), donde esta práctica rompe toda la filosofía de eficiencia por estas razones:

* **Ceguera asíncrona (Sordera del sistema):** Cuando haces vTaskDelay(1000), estás bloqueando esa tarea de forma estática. Si en ese segundo ocurre un evento crítico (el usuario presiona un botón, el WiFi se desconecta, o entra un mensaje MQTT), tu programa no puede reaccionar hasta que termine el *delay*.  
* **Desperdicio de RAM:** Cada tarea en FreeRTOS requiere su propio bloque de memoria reservada (Stack). Tener una tarea entera (que consume valiosos kilobytes de RAM) solo para ejecutar tres líneas y luego mandarla a dormir con un *delay* es un desperdicio de recursos.  
* **Mala sincronización:** Si tienes múltiples sensores o tareas con diferentes frecuencias (ej. leer I2C cada 1s, parpadear un LED cada 500ms, enviar datos por WiFi cada 10s), un while(1) lineal se vuelve un infierno matemático y de espagueti condicional (if (contador % 10 \== 0)...).

**La práctica correcta en Espressif:** En lugar de bucles infinitos y delays, la programación debe ser **Reactiva / Orientada a Eventos**. Si quieres leer un sensor cada 1 segundo, debes crear un **Temporizador por Software (FreeRTOS Software Timer)**. El temporizador "despierta" a una función de *callback* o lanza un evento exactamente cada segundo, hace la lectura, y el sistema queda libre y escuchando otros eventos. No hay bucles, no hay esperas.

---

### ¿Por qué los valores son 400 y 0?
El SGP30 es un sensor de línea base (baseline). El aire puro de la atmósfera terrestre tiene aproximadamente 400 ppm (Partes Por Millón) de CO2. El sensor asume que el ambiente donde se enciende es "aire limpio" y establece su mínimo ahí. El valor 0 de TVOC (Compuestos Orgánicos Volátiles Totales) también indica aire sin contaminantes.

---

### Nota importante sobre la salida
**El calentamiento (Warm-up):** El sensor SGP30 tiene una pequeña placa calefactora interna. Durante los primeros 15 segundos después de encenderlo, las lecturas estarán fijas en `CO2: 400 ppm` y `TVOC: 0 ppb`. No te asustes, es totalmente normal; el sensor se está calibrando térmicamente.

---

### Añadir la dependencia
Ahora ejecutamos el comando exacto. Esto descargará el driver del SGP30 y actualizará los archivos CMakeLists.txt automáticamente.
```
idf.py add-dependency "chiehmin/sgp30^1.0.0"
```

---

### ¿Qué quiere decir esto?
1. **Hardware perfecto:** Tu ESP32-C3 ha enviado una señal por el cable de datos (SDA) al ritmo del reloj (SCL) preguntando: "¿Hay alguien conectado a este bus?".
2.  **Sensor detectado:** Un dispositivo electrónico ha respondido: "Sí, yo estoy aquí, y mi dirección es la 0x58".
3. **Es indudablemente tu SGP30:** En el mundo de la electrónica, los fabricantes asignan direcciones fijas a sus chips. La dirección I2C universal y de fábrica del sensor de gas SGP30 es, precisamente, 0x58.

<img width="574" height="345" alt="Image" src="https://github.com/user-attachments/assets/68df3ff1-9948-4c5a-ab4b-d406578779d8" />

---

### El componente para el sensor SGP30
El más destacado en el ESP Component Registry es:
* Nombre: `chiehmin/sgp30`
* Descripción: SGP30 Air Quality Sensor Component for ESP-IDF. Maneja la lectura de eCO2 y TVOC, así como el ID de serie del chip.

---

### El misterio del pin "1V8"
En tu módulo hay un pin marcado como 1V8. Mucha gente se confunde y piensa que hay que meterle 1.8V por ahí. En realidad, en estos módulos comerciales, ese pin es una salida. Es el voltaje de 1.8V que el regulador interno de la placa está generando. Se deja ahí por si el usuario necesita alimentar otro pequeño componente a 1.8V, pero tú puedes ignorarlo por completo.

La conversión de 3.3V a 1.8V se hace automáticamente de forma invisible para ti. Así que puedes conectar VIN al 3V3 de tu ESP32-C3 y los pines SDA/SCL de forma directa con total tranquilidad.

