import asyncio
import logging
import json
from aiocoap import Message, Code
from aiocoap.resource import Resource, Site
import aiocoap
from web3 import Web3
from web3.middleware import ExtraDataToPOAMiddleware

# --- 1. CONFIGURACIÓN WEB3 ---
w3 = Web3(Web3.HTTPProvider('http://127.0.0.1:8545'))
w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)

# ¡ATENCIÓN! Actualiza con tus datos reales
DIRECCION_CONTRATO = "0xA1Be5B5E6DaBfccA46B96457E03C1160725D3E41"
CUENTA_FOG = w3.eth.accounts[0]
ABI = [...] # Pega aquí tu ABI
# 2. MODIFICA ESTA PARTE: Lee el archivo físico abi.json automáticamente
with open("abi.json", "r") as file:
    ABI = json.load(file)

contrato = w3.eth.contract(address=DIRECCION_CONTRATO, abi=ABI)

# --- 2. LÓGICA DE AGREGACIÓN Y COAP ---
class RecolectorCO2(Resource):
    """
    Este recurso (endpoint) recibe las peticiones POST de los sensores.
    Actúa como tu capa de agregación Fog.
    """
    def __init__(self):
        super().__init__()
        self.buffer_lecturas = []
        self.umbral = 5

    def enviar_a_blockchain(self, promedio):
        print(f"🚀 [BLOCKCHAIN] Enviando promedio ({promedio} ppm) a Geth...")
        try:
            tx_hash = contrato.functions.registrarCO2(promedio).transact({'from': CUENTA_FOG})
            receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
            print(f"✅ [BLOCKCHAIN] Lote guardado. Bloque: {receipt.blockNumber} | TX: {w3.to_hex(tx_hash)}\n")
        except Exception as e:
            print(f"❌ [BLOCKCHAIN] Error: {e}")

    async def render_post(self, request):
        # Decodificar el mensaje UDP entrante (ej: "450")
        payload = request.payload.decode('utf-8')
        
        try:
            valor_co2 = int(payload)
            self.buffer_lecturas.append(valor_co2)
            print(f"📥 [FOG] Dato recibido vía CoAP: {valor_co2} ppm. Buffer: {len(self.buffer_lecturas)}/{self.umbral}")
            
            if len(self.buffer_lecturas) >= self.umbral:
                promedio = int(sum(self.buffer_lecturas) / self.umbral)
                print(f"📊 [FOG] Umbral alcanzado. Promedio calculado: {promedio}")
                
                # Al ejecutar la transacción en un hilo separado evitamos bloquear el servidor CoAP
                await asyncio.to_thread(self.enviar_a_blockchain, promedio)
                
                self.buffer_lecturas.clear()

            # Responder al ESP32 que todo fue un éxito (HTTP 201 Created -> CoAP 2.01)
            return Message(code=Code.CREATED, payload=b"Dato recibido")
            
        except ValueError:
            return Message(code=Code.BAD_REQUEST, payload=b"Formato invalido")

async def main():
    # Construir el árbol de recursos del servidor (Rutas)
    root = Site()
    # El sensor enviará datos a la ruta: coap://<IP_FOG>/co2
    root.add_resource(['co2'], RecolectorCO2())

    print("📡 Servidor Fog CoAP iniciado. Escuchando en el puerto 5683 (UDP)...")
    await aiocoap.Context.create_server_context(root)
    
    # Mantener el servidor corriendo eternamente
    await asyncio.get_running_loop().create_future()

if __name__ == "__main__":
    # Silenciar logs internos de aiocoap para ver limpia nuestra consola
    logging.basicConfig(level=logging.ERROR)
    asyncio.run(main())
