# Desarrollo de plataforma IoT descentralizada para la recopilación y compartición abierta de datos sensoriales

### Director: 
* Carlos Nuñez (carlnu03@ucm.es)

### Autor:
* Ariel Gámez (arielg01@ucm.es)

### Resumen:  

Diseño e implementación de una plataforma descentralizada de compartición de datos IoT en la que dispositivos finales basados en ESP32 recopilan información de sensores (por ejemplo, niveles de CO2 en entornos urbanos) y la transmiten mediante Bluetooth Low Energy (BLE) a nodos edge intermedios que actúan como agregadores y gateways hacia la infraestructura cloud. Estos nodos intermedios, basados en Raspberry Pi, procesarán los datos y los registrarán en una blockchain compartida entre los diferentes nodos edge y uno o varios nodos desplegados en el cloud. El objetivo final del sistema es garantizar la trazabilidad, integridad y disponibilidad de los datos IoT en un entorno público y abierto a la participación. Este TFM ofrece potencial para publicación científica y realización de doctorado.

## Ramas del Proyecto e Infraestructura

Este repositorio está organizado en ramas específicas para aislar los entornos de desarrollo antes de su consolidación final. Puedes explorar la documentación técnica completa de cada sección navegando directamente a sus respectivas ramas:

* **[Documentación del Firmware (Rama `esp-idf`)](https://github.com/ariegd/miot-tfm/tree/esp-idf/src/espressif/medidor_aire/README.md)**: Contiene el código fuente en C para el ESP32-C3, la configuración de controladores, tareas de FreeRTOS y los clientes nativos CoAP y NimBLE.
* **[Documentación de la Blockchain (Rama `geth`)](https://github.com/ariegd/miot-tfm/tree/geth/src/geth/README.md)**: Contiene la configuración del bloque génesis, contratos inteligentes en Solidity (`.sol`), scripts de orquestación en Python (`web3.py`) y manuales de despliegue P2P para las Raspberry Pi 4.

 
