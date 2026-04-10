| Supported Targets | Raspberry-Pi4 | Linux |
| ----------------- | ------------- | ----- |

<img width="371" height="439" alt="Image" src="https://github.com/ariegd/miot-tfm/blob/geth/src/geth/img/20260410_094412.jpg" />


# Objetivo red privada go-ethereum
* Crear una red blockchain compartida entre las diferentes RPis y ejecutar un smart contract básico. Es decir, geth en cada RPi y en un ordenador, y un smart contract simple en Solidity para poder enviar transacciones con los valores de CO2.

* Una RPi envia la telemetría, recibida por el ESP32, a la red geth y el otro RPi lee el valor CO2.


## Tareas en ejecución
Se basa en tres pilares:

1. **Tres nodos**: Se encuentran minando en la red privada blockchain.
2. **Envio valor CO2**: Calcula según el umbral, intervalo de tiempo y promedia para el envio del valor CO2
3. **Lectura valor CO2**: Cada cierto tiempo lee el valor CO2 en la red go-ethereum

## Directorio del proyecto
A continuación se muestra directorio `red_co2` dentro de cada nodo .

```
red_co2
├── 10cuentas.txt
├── genesis.json
├── nodo
│   ├── geth
│   │   ├── blobpool
│   ...
│   │   └── transactions.rlp
│   └── keystore
│       └── UTC--2026-04-08T10-26-39
└── password.txt

```

## Visualizando la Máquina de Estados Finitos (FSM)
stateDiagram-v2 es una instrucción de código utilizada por Mermaid, una herramienta que permite generar diagramas y gráficos mediante texto simple.

```
stateDiagram-v2
    state "RPi Emisor (Nodo 1)" as RPi1
    state "Smart Contract (Blockchain)" as SC
    state "RPi Receptor (Nodo 2)" as RPi2
    state "Portátil Debian (Nodo 3)" as Debian

    [*] --> RPi1: Inicio Monitoreo
    
    state RPi1 {
        [*] --> Recopilando: Leer Sensores
        Recopilando --> Promediando: Fin Intervalo
        Promediando --> Evaluando: Calcular Media
        Evaluando --> Enviando: > Umbral
        Evaluando --> Recopilando: < Umbral
        Enviando --> Esperando: Confirmación Tx
        Esperando --> Recopilando
    }

    RPi1 --> SC: envia(valor_CO2)
    
    state SC {
        [*] --> Almacenando: Recibir Datos
        Almacenando --> Validando: Consenso Auditoría
        Validando --> Actualizado: Estado Guardado
    }

    SC --> RPi2: Evento / Actualización
    
    state RPi2 {
        [*] --> Escuchando: Red Blockchain
        Escuchando --> Leyendo: "Lee" datos SC
        Leyendo --> Procesando: Datos CO2
        Procesando --> Escuchando
    }

    state Debian {
        [*] --> Minando: Validar Bloques
        Minando --> Minando: Prueba de Auditoría
    }

```

## Hardware requerido
* Raspberry Pi 4 Modelo B.
* Raspberry Pi 4 Modelo B.
* Portátil o ordenador mesa
* Dongle WiFi (opcional)

<img width="371" height="439" alt="Image" src="https://github.com/ariegd/miot-tfm/blob/geth/src/geth/img/1775732450744.jpeg" />

## Configuración del proyecto antes de puesta en marcha.
Se asume que ya la instalación de geth 1.13.15 y archivos correspondientes como genesis.json. Se encuentran instalados en cada nodo de red privada blockchain. Entoces, para cada nodo de la red privada blockchain:

1. Si se está utilizando el Dongle WiFi (opcional)
```
# 1. Desconectar la tarjeta USB de la red actual
nmcli device disconnect wlxccbabd6179b5

# 2. Crear el Punto de Acceso (Hotspot)
nmcli device wifi hotspot ifname wlxccbabd6179b5 ssid "<NOMBRE-WIFI>" password "<CONTRASEÑA>"
# O mediante
sudo nmcli device wifi hotspot con-name <NOMBRE-CONEXIÓN> ssid <NOMBRE-WIFI> password <CONTRASEÑA>

# 3. Comprobar que está funcionando
nmcli connection show --active

# 4. Conectar las Raspberry Pi
ip neigh show dev wlxccbabd6179b5
```

2. Revisar las IPs de la wifi, para cambiar
```
# En la red wifi
sudo nmap -sn 192.168.1.0/24

# Para RPi
ssh usuario@rpi-nodo1.local

# Opción1 Usa la herramienta oficial 
sudo raspi-config
Introduce el SSID (Nombre de tu red): <NOMBRE-WIFI>
Introduce la Contraseña: <CONTRASEÑA>

# Opcion 2
sudo nmcli device wifi connect "<NOMBRE-WIFI>" password "<CONTRASEÑA>"
```

3. Instalación de Geth (En los 3 nodos)
Entrar en la página oficial de descargas: https://geth.ethereum.org/downloads/
```
# 0. Descagar el binario
wget https://gethstore.blob.core.windows.net/builds/geth-linux-arm64-1.13.15-c5ba367e.tar.gz

# 1. Descompactar el archivo
tar -xvf geth-linux-amd64-*.tar.gz

# 2. Mover el ejecutable a la carpeta del sistema
cd geth-linux-amd64-*
sudo mv geth /usr/local/bin/

# 3. Comprobar que todo funciona
geth version

# 4. Crea la carpeta del proyecto y entra en ella:
mkdir ~/red_co2
cd ~/red_co2

# 5. Generar una nueva cuenta de Ethereum para el nodo:
geth account new --datadir ./nodo

# 6. Guardar la contraseña:
echo "<CONTRASEÑA>" > password.txt
```

4. Crea el archivo `static-nodes.json`
La forma correcta y profesional de configurar una red privada en Geth
```
red_co2$ nano nodo/geth/static-nodes.json
[
  "enode://b1 ... @<IP_DEBIAN>:30303",
  "enode://83 ... @<IP_RPi_1>:30303",
  "enode://8f ... @<IP_RPi_2>:30303"
]
```

5. Trabajar con env en Python
```
# 1. Instalar el soporte de entornos virtuales
sudo apt update
sudo apt install python3-venv

# 2. Crear y activar nuestro entorno virtual
mkdir mi_proyecto && cd mi_proyecto
python3 -m venv venv

source venv/bin/activate

# 3. Instalar nuestros paquetes sin errores
pip install web3 py-solc-x

```

## Levantar la red privada blockchain P2P
1. Conectar mediante SSH a los nodos RPis
```
ssh usuario@rpi-nodo1.local
```

2. Inicializar la Blockchain en cada nodo
```
cd ~/red_co2
geth --datadir ./nodo init genesis.json
```

3. Puesta en marcha de los nodos para minar
```
# Debian (Bootnode) 
geth --datadir ./nodo --networkid 12345 --port 30303 --nat extip:<IP_DEBIAN> --allow-insecure-unlock --password password.txt --mine --miner.etherbase "<DIRECCION_DEBIAN>" --unlock "<DIRECCION_DEBIAN>" --http --http.addr "0.0.0.0" --http.port 8545 --http.api "eth,net,web3,personal,miner" --http.corsdomain "*"


# rpi-node1
geth --datadir ./nodo --networkid 12345 --port 30303 --nat extip:<IP_RPi_1> --allow-insecure-unlock --password password.txt --mine --miner.etherbase "<DIRECCION_RPi_1>" --unlock "<DIRECCION_RPi_1>" --http --http.addr "0.0.0.0" --http.port 8545 --http.api "eth,net,web3,personal,miner" --http.corsdomain "*"


# rpi-node2
geth --datadir ./nodo --networkid 12345 --port 30303 --nat extip:<IP_RPi_2> --allow-insecure-unlock --password password.txt --mine --miner.etherbase "<DIRECCION_RPi_2>" --unlock "<DIRECCION_RPi_2>" --http --http.addr "0.0.0.0" --http.port 8545 --http.api "eth,net,web3,personal,miner" --http.corsdomain "*"
```

4. En caso que no se reconozcan los nodos hay que forzarlos.
Para confirmar visualmente que todos están hablando entre sí, abrimos la consola interactiva de Geth en cualquiera de los nodos que estén corriendo.
```
# Entramos a una consola con un prompt que dice >:
geth attach /home/usuario/red_co2/nodo/geth.ipc
geth attach ./nodo/geth.ipc

# Debería devolvernos un número mayor que 0 (mv conectadas)
net.peerCount

# Para ver la lista detallada de las IPs a las que está conectado.
admin.peers

# Si son timidos y aún no se conectan, entonces hay que forzar. Mencionar que aunque nos devuelva un `true` lo único que dice es que su ejecución fue exitosa.
admin.addPeer("enode://e96a...@<IP_NODO>:30303")

```

## Ejemplo de Salida
```
...
I (134290) NimBLE: [BLE] Dato listo para notificar -> CO2: 402 ppm | TVOC: 20 ppb
I (135290) NimBLE: [BLE] Dato listo para notificar -> CO2: 413 ppm | TVOC: 26 ppb
I (136290) NimBLE: [BLE] Dato listo para notificar -> CO2: 406 ppm | TVOC: 28 ppb
I (137290) NimBLE: [BLE] Dato listo para notificar -> CO2: 400 ppm | TVOC: 20 ppb
I (138290) NimBLE: [BLE] Dato listo para notificar -> CO2: 405 ppm | TVOC: 21 ppb
I (139290) NimBLE: [BLE] Dato listo para notificar -> CO2: 416 ppm | TVOC: 24 ppb
I (140290) NimBLE: [BLE] Dato listo para notificar -> CO2: 402 ppm | TVOC: 23 ppb
...

```

## Problemas y soluciones
### ⚠️ Ayuda en la terminal
```
# Reiniciar o apaga linux
sudo reboot
sudo shutdown -r now

# Problema si el DHCP no envia la ip4. Hay que forzar
sudo dhclient enp0s3

# Darle vida a la red empezando a generar bloques.
# Identificar las cuentas (Etherbase)
geth --datadir ./nodo account list
```

### ⚠️ Problema de conexión de nodos por estar en diferentes redes WiFi
**La Solución: Tailscale VPN**
```
# 1. Instalar Tailscale
curl -fsSL https://tailscale.com/install.sh | sh

# 2. Conectar la RPi a tu red
sudo tailscale up

3. Verificar la conexión
tailscale status
```

### ⚠️ Paso importante, modificar los cortafuegos de los tres (resuelve problemas)
```
sudo firewall-cmd --zone=public --add-port=30303/tcp --permanent
sudo firewall-cmd --zone=public --add-port=30303/udp --permanent
sudo firewall-cmd --reload
```

### ⚠️ Conectarse a RPi mediante ssh 
```
# 1. 
ssh usuario@rpi-nodo1.local

# Si no accede, limpiar la memoria por cambio de RPi
ssh-keygen -f "/home/zodd/.ssh/known_hosts" -R "rpi-nodo1.local"

```

### ⚠️ Problemas de historicos distintos
 Si las dos máquinas tienen historiales distintos guardados en su disco duro, se conectarán, verán que sus bloques no coinciden, y se desconectarán al instante.

**La Solución: "Formatear" la blockchain y empezar de cero**
```
# Paso 1: Borrar la base de datos de bloques antigua
geth --datadir ./nodo removedb

# Paso 2: Borramos la base de datos de la Mainnet que se creó por error
rm -rf ./nodo/geth/chaindata
rm -rf ./nodo/geth/lightchaindata

# Paso 3: Matar el proceso fantasma de Geth
killall -9 geth

# Paso 4: Re-inicializar Geth con el plano correcto
geth --datadir ./nodo init genesis.json

# Paso 5: Arrancar los tres nodos (aislados del mundo exterior)
geth --datadir ./nodo --networkid 12345 --port 30303 --nat extip:<IP_NODO> --allow-insecure-unlock --password password.txt --mine --miner.etherbase "<DIRECCION_NODO>" --unlock "<DIRECCION_NODO>" --http --http.addr "0.0.0.0" --http.port 8545 --http.api "eth,net,web3,personal,miner" --http.corsdomain "*"
```
