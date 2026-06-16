import sys
import time
import json
import random
from web3 import Web3
from web3.middleware import ExtraDataToPOAMiddleware

if len(sys.argv) < 3:
    print("Uso: python3 simular_sensor_directo.py <IP_PORTATIL_VALIDADOR> <INDICE_CUENTA>")
    sys.exit(1)

IP_VALIDADOR = sys.argv[1]
ACCOUNT_INDEX = int(sys.argv[2])

# 1. CONEXIÓN DIRECTA A LA BLOCKCHAIN VÍA RPC HTTP
w3 = Web3(Web3.HTTPProvider(f'http://{IP_VALIDADOR}:8545'))
w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)

# 2. DIRECCIÓN DEL CONTRATO DESPLEGADO EN CÁDIZ
DIRECCION_CONTRATO = "0xDd6AdbD324d45238020C19Cce5ea42469F19B940" 

with open("abi.json", "r") as file:
    ABI = json.load(file)

contrato = w3.eth.contract(address=DIRECCION_CONTRATO, abi=ABI)

# Asignar una cuenta unlocked del nodo a este sensor virtual para evitar colisiones de Nonce
try:
    CUENTA_EMISORA = w3.eth.accounts[ACCOUNT_INDEX]
    print(f"Sensor Virtual listo. Usando cuenta asignada: {CUENTA_EMISORA}")
except IndexError:
    CUENTA_EMISORA = w3.eth.accounts[0]
    print(f"[ALERTA] Índice no encontrado. Usando cuenta por defecto: {CUENTA_EMISORA}")

print(" Iniciando modo comparativo: Edge-to-Blockchain directo (Sin Capa Fog)...")

# Inicializar el archivo CSV con su cabecera si no existe
with open("latencia_directo_base.csv", "w") as f:
    f.write("latencia_e2e_base\n")

while True:
    try:
        valor_co2 = random.randint(390, 440)
        
        # MOMENTO DE ORIGEN: Generación del dato telemétrico (ms)
        t_origen = int(time.time() * 1000)
        
        print(f"[{time.strftime('%H:%M:%S')}] Enviando {valor_co2} ppm directamente a la EVM...")
        
        # Envío síncrono individual e inmediato a la Blockchain (1 dato = 1 Transacción)
        tx_hash = contrato.functions.reportarCO2(valor_co2).transact({'from': CUENTA_EMISORA})
        
        # El hilo se bloquea activamente esperando el recibo del bloque (consenso Clique)
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
        
        # MOMENTO DE CONFIRMACIÓN: Bloque minado con éxito (ms)
        t_confirmacion = int(time.time() * 1000)
        
        # Cálculo de la Latencia E2E Absoluta del escenario sin optimizar
        latencia_e2e = t_confirmacion - t_origen
        print(f" Indexado en bloque {receipt.blockNumber}. Latencia E2E Base: {latencia_e2e} ms")
        
        # Escritura persistente e inmediata en el CSV comparativo
        with open("latencia_directo_base.csv", "a") as f:
            f.write(f"{latencia_e2e}\n")
            
        # Frecuencia fija de envío estipulada en la metodología (Cada 2 segundos)
        time.sleep(2)
        
    except KeyboardInterrupt:
        print("\nSimulación finalizada.")
        break
    except Exception as e:
        print(f" Error por congestión o rechazo en la EVM: {e}")
        time.sleep(2)
