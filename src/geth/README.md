| Supported Targets | Raspberry-Pi4 | Linux |
| ----------------- | ------------- | ----- |

<img width="371" height="439" alt="Image" src="https://github.com/ariegd/miot-tfm/blob/geth/src/geth/img/20260410_094412.jpg" />


# Infraestructura Fog: Red Privada Go-Ethereum (`red_co2`)

Este directorio contiene la configuración, el bloque génesis y los scripts necesarios para desplegar una red Blockchain privada descentralizada basada en **Go-Ethereum (Geth)** distribuida entre múltiples nodos Raspberry Pi 4 (Fog Nodes) y una estación central.

## Índice de Contenidos
* [1. Objetivo de la Red Blockchain Perimetral](#1-objetivo-de-la-red-blockchain-perimetral)
* [2. Arquitectura de Ejecución (Pilares)](#2-arquitectura-de-ejecución-pilares)
* [3. Estructura del Directorio del Proyecto](#3-estructura-del-directorio-del-proyecto)
* [4. Despliegue del P2P Ethereum](#4-despliegue-del-p2p-ethereum)
* [5. Despliegue del Smart Contract](#5-despliegue-del-smart-contract)
* [6. Conectividad y Orquestación (Tailscale)](#6-conectividad-y-orquestación-tailscale)
* [7. Registro de Errores y Sincronización (Enlace Interno)](#7-registro-de-errores-y-sincronización-enlace-interno)

---

## 1. Objetivo de la Red Blockchain Perimetral

Crear una capa segura de persistencia y auditoría inmutable distribuida entre las diferentes Raspberry Pi 4. Cada nodo ejecuta una instancia local de Geth que aloja un contrato inteligente en Solidity para registrar y validar de manera incorruptible las transacciones con los valores de eCO2 procesados.

* **Flujo Fog-to-Chain:** Una Raspberry Pi actúa como pasarela CoAP (Gateway), recibe la telemetría del ESP32-C3, promedia los datos según los umbrales configurados e inyecta la transacción en el contrato inteligente de la Blockchain. Los otros nodos de la red leen estos valores validados directamente desde el ledger de la red distribuida.

---

## 2. Arquitectura de Ejecución (Pilares)
La red opera bajo un mecanismo de consenso eficiente para sistemas embebidos, estructurándose sobre tres pilares operativos:

1. **Validación de Consenso Clique (PoA - Proof of Authority)**: Los tres nodos autorizados cooperan para firmar y validar bloques continuamente en la red privada, reduciendo a cero el coste computacional y de energía (a diferencia de PoW).
2. **Ingesta Orientada a Umbrales (Productor / Post-Filtro)**: El recolector evalúa el flujo continuo, almacena las lecturas de gas en un buffer y calcula el promedio matemático real solo al alcanzar el límite fijado (`umbral = 5`), optimizando las comisiones de gas virtuales de la red.
3. **Lectura y Consumo Distribuido**: Procesos asíncronos paralelos leen la información almacenada en el Smart Contract mediante consultas constantes a las funciones globales de `go-ethereum`.

---

## 3. Estructura del Directorio del Proyecto

A continuación, se detalla la topología de archivos requerida en el directorio de cada nodo Fog:

´´´
red_co2/
├── 10cuentas.txt              (Registro de direcciones y credenciales del laboratorio)
├── genesis.json                (Configuración del bloque cero y consenso Clique PoA)
├── abi.json                    (Interfaz binaria de la aplicación del contrato inteligente)
├── RegistroCO2.sol            (Smart Contract nativo en Solidity)
├── desplegar.py                (Script de automatización web3.py para subir el contrato)
├── nodo_fog_coap.py            (Servidor CoAP y puente integrador con Web3 Blockchain)
├── simular_sensor.py           (Inyector local de pruebas para depuración de buffers)
├── venv/                       (Entorno virtual de Python con aiocoap y web3 instalado)
└── nodo/                       (Base de datos local y almacenamiento de bloques de Geth)
├── geth/
│   ├── blobpool/
│   ├── chaindata/          (Estructura del libro contable de la red)
│   └── lightchaindata/
└── keystore/               (Llaves criptográficas de las cuentas locales del nodo)
´´´

---

## 4. Despliegue del P2P Ethereum
La red privada requiere una configuración precisa de los nodos estáticos, el entorno de Python para los puentes CoAP-Web3 y el inicio de los motores de minería bajo el protocolo Clique.

* **[Guía de Configuración y Puesta en Marcha P2P](https://github.com/ariegd/miot-tfm/tree/geth/src/geth/red_co2)**

---

## 5. Despliegue del Smart Contract

Para subir el contrato inteligente a la red privada y actualizar los identificadores criptográficos, se debe ejecutar el orquestador:
```bash
python3 desplegar.py
```
Al finalizar, actualizará automáticamente la macro global `DIRECCION_CONTRATO` dentro del backend del servidor CoAP en el archivo `nodo_fog_coap.py`.

## 6. Conectividad y Orquestación (Tailscale)

Dado que los nodos operan en entornos de laboratorio que pueden cambiar de subred física, se implementa una red superpuesta segura (SDN) mediante Tailscale para asegurar el tunelamiento directo entre nodos sin lidiar con redireccionamiento de puertos en enrutadores comerciales.

Para verificar el estado del mallado P2P en el Gateway, ejecuta:
```bash
tailscale status
```

## 7. Registro de Errores y Sincronización (Enlace Interno)
Para evitar saturar la documentación de diseño y arquitectura, todas las guías de resolución de problemas de red, limpieza de demonios fantasmas y procedimientos ante bifurcaciones de la blockchain (blockchain forks) se han migrado a su propia bitácora dedicada local:

* **[Manual de Resolución de Errores y Mantenimiento de Geth](https://github.com/ariegd/miot-tfm/tree/geth/src/geth/mi_proyecto)**

