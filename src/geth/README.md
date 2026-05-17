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

## Ejemplo de Salida de un nodo
```
...
alhash=f2d479..bc303f txs=0 gas=0       fees=0           elapsed="910.928µs"
INFO [05-17|19:05:07.570] Imported new chain segment               number=161 hash=1341b6..db4f4b blocks=1 txs=0 mgas=0.000 elapsed=96.474ms    mgasps=0.000 snapdiffs=279.00B triedirty=779.00B
INFO [05-17|19:05:07.571] Commit new sealing work                  number=162 sealhash=262cb3..92e02f txs=0 gas=0       fees=0           elapsed="526.852µs"
INFO [05-17|19:05:12.093] Successfully sealed new block            number=162 sealhash=262cb3..92e02f hash=e710ee..634728 elapsed=4.522s
INFO [05-17|19:05:12.095] Commit new sealing work                  number=163 sealhash=12f0bc..7b71ea txs=0 gas=0       fees=0           elapsed=1.562ms
WARN [05-17|19:05:12.095] Block sealing failed                     err="signed recently, must wait for others"
INFO [05-17|19:05:12.201] Looking for peers                        peercount=2 tried=21 static=2
INFO [05-17|19:05:17.127] Imported new chain segment               number=163 hash=3717b3..689a14 blocks=1 txs=0 mgas=0.000 elapsed=96.895ms    mgasps=0.000 snapdiffs=279.00B triedirty=779.00B
INFO [05-17|19:05:17.128] Commit new sealing work                  number=164 sealhash=deb0ea..588ce6 txs=0 gas=0       fees=0           elapsed=1.055ms
...
```

## Problemas y soluciones
### ⚠️ Error al lanzar el `simular_sensor.py`
**Solución**
```
1. Modifica la línea 4 (el import):
Antes: from web3.middleware import geth_poa_middleware
Ahora: from web3.middleware import ExtraDataToPOAMiddleware

2. Modifica la línea 13 (donde se aplica):
Antes: w3.middleware_onion.inject(geth_poa_middleware, layer=0)
Ahora: w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)
```
**Error**
```
(venv) zodd@debian:~/mi_proyecto$ python3 simular_sensor.py

Traceback (most recent call last):

  File "/home/zodd/mi_proyecto/simular_sensor.py", line 4, in <module>

    from web3.middleware import geth_poa_middleware

ImportError: cannot import name 'geth_poa_middleware' from 'web3.middleware' (/home/zodd/mi_proyecto/venv/lib/python3.13/site-packages/web3/middleware/__init__.py)
```

### ⚠️ Configuración y arranque desde WiFi Móvil
```
# Debian (Bootnode) 
geth --datadir ./nodo --networkid 12345 --port 30303 --nat extip:10.114.27.116 --allow-insecure-unlock --password password.txt --mine --miner.etherbase "0xA1Be5B5E6DaBfccA46B96457E03C1160725D3E41" --unlock "0xA1Be5B5E6DaBfccA46B96457E03C1160725D3E41" --http --http.addr "0.0.0.0" --http.port 8545 --http.api "eth,net,web3,personal,miner" --http.corsdomain "*" --nodiscover --bootnodes ""

# rpi-node1
geth --datadir ./nodo --networkid 12345 --port 30303 --nat extip:10.114.27.143 --allow-insecure-unlock --password password.txt --mine --miner.etherbase "0xEcCb21cFdC06b8777642d83904D49c96e4E929Cc" --unlock "0xEcCb21cFdC06b8777642d83904D49c96e4E929Cc" --http --http.addr "0.0.0.0" --http.port 8545 --http.api "eth,net,web3,personal,miner" --http.corsdomain "*" --nodiscover --bootnodes ""

# rpi-node2
geth --datadir ./nodo --networkid 12345 --port 30303 --nat extip:10.114.27.199 --allow-insecure-unlock --password password.txt --mine --miner.etherbase "0xB7523Cb4d56A13F9919b7B582070A73d9e8c92C2" --unlock "0xB7523Cb4d56A13F9919b7B582070A73d9e8c92C2" --http --http.addr "0.0.0.0" --http.port 8545 --http.api "eth,net,web3,personal,miner" --http.corsdomain "*" --nodiscover --bootnodes ""

# arrancar
geth attach ./nodo/geth.ipc

# Debian
admin.addPeer("enode://6445315e57f87383bdd2158bcf5642886e2bd39df07a5b8db2055f163bcc7224be7a2219c0b6abdf3624cea31070d6b9aa1a03a956db7c9e7b90026c3781f48e@10.114.27.116:30303")

# Rpi-1
admin.addPeer("enode://b1cb946980472e067f3e5e971814a65453a1749219caf21277b885c62e987f4a08e26674a116e3b093eb1834f4dedc7980e0d9ab9f95d1cad66d3c8f1eba73e0@10.114.27.143:30303")

# Rpi-2
admin.addPeer("enode://83ef2a7151b66881751e78f75c4462778baff9b39d9a6fed037a3f19d37427d658c79800c88ef3b6bdd46de2b05e7d1cc5bbb8322aa8ced0c0d486deca045689@10.114.27.199:30303")
```

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
