
# Manual de Errores y Mantenimiento: Go-Ethereum

Este documento recopila las soluciones técnicas aplicadas para resolver fallos de comunicación en red, bloqueos de seguridad y problemas de divergencia en la sincronización del libro de bloques (*ledger*) en los nodos Raspberry Pi 4.

## Índice de Problemas
* [1. Error de Autenticación SSH (Known Hosts)](#1-error-de-autenticación-ssh-known-hosts)
* [2. Bloqueo de Puertos P2P por Cortafuegos](#2-bloqueo-de-puertos-p2p-por-cortafuegos)
* [3. Divergencia Crítica de Historiales (Blockchain Fork)](#3-divergencia-crítica-de-historiales-blockchain-fork)

---

## 1. Error de Autenticación SSH (Known Hosts)
### Síntoma
Al intentar acceder a una Raspberry Pi por terminal mediante su alias local (`ssh usuario@rpi-nodo1.local`), el sistema bloquea el acceso mostrando una alerta de seguridad por cambio de huella digital criptográfica.
### Causa
Ocurre frecuentemente en el laboratorio cuando se formatea una tarjeta MicroSD o se intercambian las placas físicas de las Raspberry Pi compartiendo el mismo nombre en la red local. Tu ordenador detecta que la firma del hardware cambió y bloquea la conexión para prevenir un ataque de suplantación.
### Solución
Forzar la limpieza de la caché de hosts conocidos en tu máquina de desarrollo antes de reintentar el acceso:
```bash
ssh-keygen -f "/home/zodd/.ssh/known_hosts" -R "rpi-nodo1.local"
```

---

## 2. Bloqueo de Puertos P2P por Cortafuegos
### Síntoma
Los nodos inician el servicio local de Geth correctamente pero no logran descubrirse entre sí ni sincronizar bloques a través de la red privada.

### Causa
Sistemas operativos Linux con firewalls activos por defecto (como CentOS, RHEL o Fedora) bloquean los puertos de comunicación síncronos no estándar del protocolo Discovery P2P de Ethereum.

### Solución
Habilitar de manera permanente los puertos nativos de descubrimiento y tráfico de datos de Geth (30303) tanto para transporte fiable (TCP) como para datagramas rápidos (UDP) y recargar el cortafuegos:
```
sudo firewall-cmd --zone=public --add-port=30303/tcp --permanent
sudo firewall-cmd --zone=public --add-port=30303/udp --permanent
sudo firewall-cmd --reload
```
---

## 3. Divergencia Crítica de Historiales (Blockchain Fork)
### Síntoma
Dos máquinas de la red privada se conectan por una fracción de segundo, pero se desconectan instantáneamente de forma infinita sin llegar a minar en conjunto.

### Causa
Bifurcación de la Blockchain. Si los nodos guardan historiales de bloques diferentes en su almacenamiento local (por pruebas previas o arranques aislados), el protocolo de consenso detecta que las firmas criptográficas divergen desde el bloque génesis y detiene la red de forma segura para evitar corrupción.

### Solución
"Formatear" por completo la base de datos de bloques locales en frío y re-inicializar la cadena desde el bloque cero unificado (`genesis.json`):

```
# Paso 1: Forzar la matanza de cualquier demonio o proceso fantasma de Geth en segundo plano
killall -9 geth

# Paso 2: Borrar la base de datos de bloques antigua corrupta de forma segura
geth --datadir ./nodo removedb

# Paso 3: Eliminar de raíz rastros accidentales de la Mainnet pública de Ethereum
rm -rf ./nodo/geth/chaindata
rm -rf ./nodo/geth/lightchaindata

# Paso 4: Re-inicializar el estado global del nodo con el plano estructural del proyecto
geth --datadir ./nodo init genesis.json

# Paso 5: Reiniciar el arranque coordinado inyectando el ID de red asignado en el laboratorio
geth --datadir ./nodo --networkid 12345 --nodiscover --allow-insecure-unlock console
```

