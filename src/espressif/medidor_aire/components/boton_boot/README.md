## Problemas y soluciones

### Opción 3 (Event Loop). 
Nuestro archivo `sensor_sgp30.c` ya tiene implementado el Event Loop de forma nativa (Option 3). El Event Loop es más adecuado cuando múltiples consumidores necesitan reaccionar al mismo dato. Aunque solo se active una red a la vez, aprovechar la infraestructura de eventos que ya tenemos es el camino de menor resistencia, más escalable, y evita que tengamos que reescribir la lógica de nuestro sensor.

Con estos cambios, el SGP30 publicará el dato al Event Loop global. Como el ESP32 solo habrá arrancado una red (según el valor en la NVS), solo esa red registrará su handler y escuchará los datos, manteniendo la separación de responsabilidades intacta y sin desperdiciar CPU.

---

### Cómo se diseñan los dispositivos IoT comerciales? 
Un solo firmware, un botón físico para configurar, y la memoria no volátil (NVS) recordando la última configuración. Hay un secreto de la industria muy importante sobre cómo hacer esto en el ESP32: No intentes apagar el Wi-Fi y encender el Bluetooth "en caliente" (sin reiniciar).

Liberar toda la memoria de la pila Wi-Fi para arrancar la de Bluetooth sobre la marcha suele dar problemas de fragmentación de RAM y colapsos en la antena de radio. Lo que hacen el 99% de los dispositivos comerciales es:

1. Detectar el botón.
2. Cambiar una variable en la NVS.
3. Lanzar un reinicio por software (`esp_restart()`).
4. Al arrancar de nuevo (tarda 1 segundo), el `if (modo_wifi)` lee el nuevo estado e inicia la red correcta con la memoria 100% limpia.

Si arrancamos el SGP30 al principio, los segundos que tarde el Wi-Fi en negociar la IP con el router o el BLE en levantar su stack de radio van a consumir tiempo del *warmup* del sensor. Como el SGP30 exige una lectura estricta a 1Hz (una vez por segundo) para calcular bien sus algoritmos internos de línea base (baseline), cualquier bloqueo de red desfasaría el timer y corrompería las medidas iniciales.

---

### ¿Cómo se soluciona esto en el mundo real del IoT?

En la industria comercial, cuando un dispositivo no tiene pantalla, se utilizan estas alternativas:

* **PIN Estático Único (Impreso en pegatina):** En la fábrica se graba un PIN único y aleatorio en la memoria no volátil (NVS) de cada ESP32 y se imprime en una pegatina debajo del sensor. El código lee ese PIN de la memoria, no de un número fijo en el .c.

* **Derivar el PIN de la MAC:** Se programa una función para que el PIN sea, por ejemplo, los últimos 6 dígitos en base 10 de la dirección MAC única del chip de Espressif. Así, cada dispositivo tiene un PIN distinto que no viaja por el aire.

* **Modo "Just Works" (Sin PIN):** Se configura el Bluetooth para que no pida PIN. La comunicación sigue yendo encriptada por el aire, pero sacrificas la autenticación (cualquiera que esté cerca en el modo emparejamiento podría conectarse). Es lo que usan la mayoría de altavoces o auriculares Bluetooth.

* **Out of Band (OOB):** Se pone un código QR o un chip NFC en el dispositivo. El móvil lee el QR con la cámara y obtiene la clave criptográfica sin tener que teclear nada.
