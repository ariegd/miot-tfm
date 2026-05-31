## Problemas y soluciones

### Problema de espacio
Al juntar Wi-Fi, Bluetooth (NimBLE), el Event Loop, NVS y ahora el cliente MQTT, tu código compilado (`medidor_aire.bin`) pesa 1.13 MB (`0x122100`). Sin embargo, la tabla de particiones por defecto de ESP-IDF solo reserva 1 MB (`0x100000`) para tu aplicación. Básicamente, estamos intentando meter un camión en la plaza de un coche.

Para solucionarlo, solo necesitamos decirle al ESP32 que reorganice su memoria flash usando una tabla de particiones más grande.

Cambiar la tabla de particiones
1. Navega usando las flechas de tu teclado hasta la sección `Partition Table` y entra con `Enter`.
2. Entra en la primera opción, que también se llama `Partition Table`.
3. Verás una lista de opciones. Selecciona `Single factory app (large), no OTA` (esto ampliará el espacio disponible para tu código a 1.5 MB).
4. Pulsa la tecla `S` para guardar (Save) y luego `Enter` para confirmar.
5. Pulsa la tecla `Q` para salir (Quit) del menú.

---

### Filosofía de Espressif y la arquitectura de eventos
Dado que en tu aplicación la red Wi-Fi y el MQTT van de la mano (si estás en modo Wi-Fi, quieres enviar por MQTT), la forma más limpia y cohesiva de implementarlo sin crear excesivos archivos es añadir el cliente MQTT dentro de tu componente red_wifi.c.

El flujo será el siguiente:
1. El ESP32 se conecta al Wi-Fi.
2. Arranca el cliente MQTT.
3. Se registra el handler del sensor.
4. Cada vez que el SGP30 publica un dato al Event Loop, el handler lo empaqueta en JSON y lo dispara por MQTT.

Si quieres ver los datos llegando en tiempo real desde tu ordenador, puedes abrir otra terminal y usar mosquitto_sub (si lo tienes instalado en Linux):
```
mosquitto_sub -h test.mosquitto.org -t "/sensor/sgp30/telemetria" -v
```
