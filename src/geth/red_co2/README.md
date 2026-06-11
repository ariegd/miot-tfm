# Puesta en Marcha: Red P2P y Consenso Blockchain

Este documento detalla los pasos críticos para configurar el entorno de red, instalar las dependencias de Geth y sincronizar el mallado P2P entre los nodos de la infraestructura Fog.

## Índice de Configuración
1. [Configuración de Red (Hotspot & IPs)](#1-configuración-de-red)
2. [Instalación de Geth y Cuentas](#2-instalación-de-geth-y-cuentas)
3. [Configuración de Nodos Estáticos](#3-nodos-estáticos-p2p)
4. [Entorno de Ejecución Python](#4-entorno-python-y-scripts)
5. [Levantamiento de la Red y Minería](#5-levantamiento-de-la-red-y-minería)

---

## 1. Configuración de Red

Se requiere que los nodos estén en la misma subred para el descubrimiento P2P.

### Uso de Dongle WiFi (Opcional - Modo Hotspot)

Si una Dougle USB actúa como punto de acceso para las demás:

```bash
# 1. Desconectar de la red actual
nmcli device disconnect wlxccbabd6179b5

# 2. Crear el Punto de Acceso (Hotspot)
sudo nmcli device wifi hotspot ifname wlxccbabd6179b5 ssid "<NOMBRE-WIFI>" password "<CONTRASEÑA>"

# 3. Verificar estado activo
nmcli connection show --active

# 4. Listar dispositivos conectados
ip neigh show dev wlxccbabd6179b5
```

* **[Solución 2](https://github.com/ariegd/miot-tfm/tree/geth/src/geth/img)**

###  Auditoría de IPs en la Red

```Bash
# Escaneo rápido desde Debian
sudo nmap -sn 192.168.1.0/24

# Conexión SSH a nodos
ssh usuario@rpi-nodo1.local

# Configuración manual de WiFi en RPi
sudo nmcli device wifi connect "<NOMBRE-WIFI>" password "<CONTRASEÑA>"
```

---

## 2. Instalación de Geth y Cuentas
Procedimiento para instalar Geth 1.13.15 en arquitectura ARM64 (Raspberry Pi).

```
# 1. Descarga e instalación
wget [https://gethstore.blob.core.windows.net/builds/geth-linux-arm64-1.13.15-c5ba367e.tar.gz](https://gethstore.blob.core.windows.net/builds/geth-linux-arm64-1.13.15-c5ba367e.tar.gz)
tar -xvf geth-linux-arm64-*.tar.gz
sudo mv geth-linux-arm64-*/geth /usr/local/bin/

# 2. Preparación del proyecto
mkdir ~/red_co2 && cd ~/red_co2

# 3. Generar identidad del nodo
geth account new --datadir ./nodo
echo "<CONTRASEÑA_DE_LA_CUENTA>" > password.txt
```

---

## 3. Nodos Estáticos (P2P)
Para asegurar que los nodos se encuentren tras un reinicio, configuramos sus enodes de forma persistente.

Archivo: `~/red_co2/nodo/geth/static-nodes.json`
```
[
  "enode://<ID_DEBIAN>@<IP_DEBIAN>:30303",
  "enode://<ID_RPI1>@<IP_RPi_1>:30303",
  "enode://<ID_RPI2>@<IP_RPi_2>:30303"
]
```

---

## 4. Entorno Python y Scripts
Preparación del entorno para los servicios CoAP y la interacción Web3.

```
# 1. Crear entorno virtual
sudo apt install python3-venv
python3 -m venv venv
source venv/bin/activate

# 2. Dependencias
pip install web3 py-solc-x aiocoap
```

### Orden de Ejecución de Scripts
1. Servidor CoAP (RPi): python3 `nodo_fog_coap.py`

2. Simulador/Sensor (ESP32/PC): `python3 simular_sensor.py`

---

## 5. Levantamiento de la Red y Minería

### Step 1: Inicialización (Bloque Génesis)
Ejecutar en cada nodo antes del primer arranque:
```
geth --datadir ./nodo init genesis.json
```

### Step 2: Arranque de Minería (PoA)
Ejecutar el comando correspondiente según la IP y Dirección de cada nodo:
```
# Ejemplo genérico para RPi
geth --datadir ./nodo --networkid 12345 --port 30303 --nat extip:<IP_NODO> \
--allow-insecure-unlock --password password.txt --mine \
--miner.etherbase "<DIRECCION_ETH>" --unlock "<DIRECCION_ETH>" \
--http --http.addr "0.0.0.0" --http.api "eth,net,web3,personal,miner" \
--http.corsdomain "*" --nodiscover --bootnodes ""
```

### Step 3: Verificación de Conexión P2P
Desde la consola de Geth:
```
// Adjuntar a la instancia en ejecución
geth attach ./nodo/geth.ipc

// Verificar pares conectados
> net.peerCount
> admin.peers

// Forzar conexión manual si es necesario
> admin.addPeer("enode://<ID>@<IP>:30303")
```

### Ejemplo de Salida (Log Exitoso)
Cuando la red está sincronizada y minando en modo Clique (PoA), deberías observar:
```
Successfully sealed new block ➔ Bloque minado con éxito.Block sealing failed | err="signed recently..." ➔ Comportamiento normal en PoA (esperando turno de otro minero).
```


