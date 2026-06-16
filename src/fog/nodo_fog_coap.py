import asyncio
import json
import logging
import time
from aiocoap import Message, Code
from aiocoap.resource import Resource, Site
import aiocoap
from web3 import Web3
from web3.middleware import ExtraDataToPOAMiddleware

# 1. CONEXION AL GETH LOCAL DE CADA RPI
w3 = Web3(Web3.HTTPProvider('http://127.0.0.1:8545'))
w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)

# 2. CONFIGURACION DEL CONTRATO
DIRECCION_CONTRATO = "0xDd6AdbD324d45238020C19Cce5ea42469F19B940" 

# Fuerza la cuenta autorizada si la posición [0] de Geth difiere de tu registro de Cádiz
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

    def enviar_a_blockchain(self, promedio, latencia_red, latencia_fog, t_salida_fog):
        print(f"[FOG LOCAL] Enviando lote promediado de {promedio} ppm a Geth...")
        try:
            # Envío de la transacción firmada por el Nodo Fog autorizado
            tx_hash = contrato.functions.reportarCO2(promedio).transact({'from': CUENTA_FOG})
            
            # Espera síncrona dentro del hilo secundario hasta el minado (consenso Clique)
            receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
            
            # Momento 3: Bloque consolidado e indexado
            t_confirmacion_blockchain = int(time.time() * 1000)
            
            # CÁLCULO ETAPA 3: Latencia exclusiva del consenso de la Blockchain
            latencia_blockchain = t_confirmacion_blockchain - t_salida_fog
            
            print(f"[BLOCKCHAIN] Transaccion incluida en bloque {receipt.blockNumber}!")
            
            # REGISTRO AUTOMÁTICO EN EL CSV
            with open("resultados_latencia.csv", "a") as f:
                f.write(f"{latencia_red},{latencia_fog},{latencia_blockchain}\n")
            print("[CSV] Métricas grabadas de forma exitosa en 'resultados_latencia.csv'.")
            
        except Exception as e:
            print(f"[BLOCKCHAIN] Error: {e}")

    async def render_post(self, request):
        try:
            # Momento 1: El paquete UDP/CoAP entra al stack de red del Fog Node
            t_llegada_red = int(time.time() * 1000)
            
            # Decodificación del payload JSON estructurado
            data_json = json.loads(request.payload.decode('utf-8'))
            valor_co2 = int(data_json["co2"])
            t_origen = int(data_json["t_origen"])
            
            # CÁLCULO ETAPA 1: Latencia neta del canal inalámbrico/cableado (Edge a Fog)
            latencia_ms = t_llegada_red - t_origen
            
            # Almacenamos el dato junto con su trazabilidad de marcas de tiempo
            self.buffer_lecturas.append({
                "co2": valor_co2,
                "t_origen": t_origen,
                "t_llegada_red": t_llegada_red,
                "latencia_red": latencia_ms
            })
            
            print(f"[CoAP] Lectura: {valor_co2} ppm | Latencia red: {latencia_ms} ms | Buffer: {len(self.buffer_lecturas)}/{self.umbral}")
            
            if len(self.buffer_lecturas) >= self.umbral:
                # Extraemos el promedio aritmético del lote
                promedio = int(sum(x["co2"] for x in self.buffer_lecturas) / self.umbral)
                
                # Para la métrica E2E del lote, tomamos la referencia del último mensaje recibido
                ultimo_nodo = self.buffer_lecturas[-1]
                latencia_red_lote = ultimo_nodo["latencia_red"]
                t_llegada_red_lote = ultimo_nodo["t_llegada_red"]
                
                # Momento 2: Justo antes de delegar la carga al subproceso de la Web3 RPC
                t_salida_fog = int(time.time() * 1000)
                
                # CÁLCULO ETAPA 2: Retraso interno por procesamiento y buffers asíncronos en el Fog
                latencia_fog_lote = t_salida_fog - t_llegada_red_lote
                
                # Delegamos de forma asíncrona a un hilo dedicado para no congelar el socket de aiocoap
                await asyncio.to_thread(
                    self.enviar_a_blockchain, 
                    promedio, 
                    latencia_red_lote, 
                    latencia_fog_lote, 
                    t_salida_fog
                )
                self.buffer_lecturas.clear()

            return Message(code=Code.CREATED, payload=b"Dato Agregado")
        except (ValueError, KeyError, json.JSONDecodeError):
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
