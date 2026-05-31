## Problemas y soluciones
### Problema 2
**¿Por qué el ESP32 dice "Enviado con éxito" pero la RPi no ve nada?**
CoAP corre sobre UDP, que es un protocolo no orientado a la conexión. Cuando el código del ESP32 ejecuta `coap_send()`, el chip empaqueta el mensaje y lo expulsa por la antena Wi-Fi hacia la IP de destino. Si la función devuelve un identificador de mensaje (mid=1380), significa únicamente que el paquete salió con éxito de la tarjeta de red del ESP32.

Al estar configurado como mensaje No Confirmable (COAP_MESSAGE_NON), el ESP32 no espera un acuse de recibo (ACK). Si la IP de la Raspberry Pi es incorrecta, o si hay un firewall bloqueándolo, el ESP32 seguirá diciendo "Enviado con éxito" hacia la nada.
### Solucion
1. Verifica la IP real de la Raspberry Pi: Entra en la terminal de tu RPi y ejecuta `hostname -I`. Asegúrate de que coincida exactamente con la macro #define `COAP_SERVER_IP` que pusiste en el código del ESP32 (en el ejemplo anterior dejamos "192.168.1.100" por defecto).
2. Abre el archivo red_wifi.c en tu entorno de desarrollo del ESP32.
```
// Cambia la .100 por la .43 que te dio el comando hostname -I
#define COAP_SERVER_IP             "192.168.1.43"  
#define COAP_SERVER_PORT           "5683"
```
3. Guarda los cambios, compila el firmware de nuevo y flashea el chip:
```
idf.py build flash monitor
```
---
### Problema 1
El nuevo error ocurre porque estás utilizando ESP-IDF v5.5. A partir de la versión 5.0, Espressif eliminó la librería CoAP del núcleo de ESP-IDF y la trasladó a su repositorio externo de paquetes (el ESP Component Registry).
### Solucion
Ejecuta el siguiente comando para descargar e instalar de forma automática la dependencia de CoAP en tu proyecto:
```
idf.py add-dependency "espressif/coap"
```
