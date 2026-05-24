import asyncio
import json
import logging
from aiocoap import Message, Code
from aiocoap.resource import Resource, Site
import aiocoap
from web3 import Web3
from web3.middleware import ExtraDataToPOAMiddleware

# 1. CONEXIÓN AL GETH LOCAL DE CADA RPI
w3 = Web3(Web3.HTTPProvider('http://127.0.0.1:8545'))
w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)

# 2. CONFIGURACIÓN DEL CONTRATO
# Pon la dirección que te dio el script de despliegue
DIRECCION_CONTRATO = "0xC8FDFf39Ccc2dBb8CE8075722742b4c3BE4182F0" 

# Cada RPi tomará automáticamente la cuenta que desbloqueaste en su comando de arranque
CUENTA_FOG = w3.eth.accounts[0] 
print(f"Vinculado al Geth local. Usando cuenta minera: {CUENTA_FOG}")

with open("abi.json", "r") as file:
    ABI = json.load(file)

contrato = w3.eth.contract(address=DIRECCION_CONTRATO, abi=ABI)

class RecolectorCO2(Resource):
    def __init__(self):
        super().__init__()
        self.buffer_lecturas = []
        self.umbral = 5

    def enviar_a_blockchain(self, promedio):
        print(f"[FOG LOCAL] Enviando lote promediado de {promedio} ppm a Geth...")
        try:
            # Enviamos la transacción al nodo local
            tx_hash = contrato.functions.reportarCO2(promedio).transact({'from': CUENTA_FOG})
            receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
            print(f"[BLOCKCHAIN] Transacción incluida en bloque {receipt.blockNumber}!")
        except Exception as e:
            print(f"[BLOCKCHAIN] Error: {e}")

    async def render_post(self, request):
        try:
            valor_co2 = int(request.payload.decode('utf-8'))
            self.buffer_lecturas.append(valor_co2)
            print(f"[CoAP] Lectura recibida: {valor_co2} ppm. Buffer: {len(self.buffer_lecturas)}/{self.umbral}")
            
            if len(self.buffer_lecturas) >= self.umbral:
                promedio = int(sum(self.buffer_lecturas) / self.umbral)
                await asyncio.to_thread(self.enviar_a_blockchain, promedio)
                self.buffer_lecturas.clear()

            return Message(code=Code.CREATED, payload=b"Dato Agregado")
        except ValueError:
            return Message(code=Code.BAD_REQUEST)

async def main():
    root = Site()
    root.add_resource(['co2'], RecolectorCO2())
    print("Servidor Fog CoAP iniciado en puerto 5683 (UDP)...")
    await aiocoap.Context.create_server_context(root, bind=('0.0.0.0', 5683))
    await asyncio.get_running_loop().create_future()

if __name__ == "__main__":
    logging.basicConfig(level=logging.ERROR)
    asyncio.run(main())
