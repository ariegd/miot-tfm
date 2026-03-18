# Levantar el servidor de Ethereum
Pero en este caso pasando el flujo de consola a un archivo
```
docker run --rm -p 8545:8545 trufflesuite/ganache:latest --defaultBalanceEther 1000  > /home/zodd/Documentos/python3/miot-tfm/src/ethereum/DePIN/doc/log_1803.txt
```

# Levantar la red local Ethereum
Esto iniciará tu red y te mostrará en la pantalla una lista de 10 cuentas (direcciones) y sus "Private Keys" (Claves Privadas), cada una con 1000 ETH falsos. ¡No cierres esa ventana!
```
docker run --rm -p 8545:8545 trufflesuite/ganache:latest --defaultBalanceEther 1000
```

----------
# 1. Crea el entorno (puedes llamarlo 'env' o '.venv')
python3 -m venv .venv

# 2. Actívalo
source .venv/bin/activate

# 3. Instala lo que necesites
pip install flask pillow


## Activar la variable de entorno

cd ~/Documentos/python3/cnn/back-end/
source ../.venv/bin/activate
python3 app.py

