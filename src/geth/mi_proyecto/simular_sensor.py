import time
import random
from web3 import Web3
from web3.middleware import ExtraDataToPOAMiddleware

# 1. Conexión al nodo Geth local
# Usamos localhost porque este script corre en la misma máquina que el nodo
w3 = Web3(Web3.HTTPProvider('http://127.0.0.1:8545'))

# Inyectar el middleware de PoA (Proof of Authority - Clique)
# Esto es OBLIGATORIO en redes privadas como la tuya, si no, fallarán las transacciones
w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)

if not w3.is_connected():
    print("❌ Error: No se pudo conectar a Geth. ¿Está el nodo arrancado con el puerto 8545 abierto?")
    exit()

print("✅ Conectado a la red Geth exitosamente.")

# 2. Configuración del Contrato y la Cuenta
# ¡ATENCIÓN! Pega aquí la dirección que te devolvió el script desplegar.py
DIRECCION_CONTRATO = "0xC8FDFf39Ccc2dBb8CE8075722742b4c3BE4182F0" 

# Usaremos la cuenta minera que ya tienes desbloqueada en tu nodo
CUENTA_SENSOR = w3.eth.accounts[0] 
print(f"📡 Usando la cuenta del sensor (ESP32 simulado): {CUENTA_SENSOR}")

# El ABI es el "manual de instrucciones" para que Python sepa qué funciones tiene el contrato
ABI = [
    {
        "inputs": [{"internalType": "uint256", "name": "_co2PPM", "type": "uint256"}],
        "name": "registrarCO2",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "obtenerUltimaLectura",
        "outputs": [
            {"internalType": "uint256", "name": "", "type": "uint256"},
            {"internalType": "uint256", "name": "", "type": "uint256"},
            {"internalType": "address", "name": "", "type": "address"}
        ],
        "stateMutability": "view",
        "type": "function"
    }
]

# Inicializamos el contrato en Python
contrato = w3.eth.contract(address=DIRECCION_CONTRATO, abi=ABI)

# 3. Bucle principal: Simulación del envío de datos
print("\n🚀 Iniciando simulación de envío de datos de CO2...")
print("Presiona Ctrl+C para detener el script.\n")

try:
    while True:
        # Generar un valor de CO2 simulado (PPM normal en exteriores es ~400, en interiores mal ventilados >800)
        co2_actual = random.randint(380, 1200)
        
        print(f"[{time.strftime('%H:%M:%S')}] Generada lectura: {co2_actual} ppm. Enviando a la blockchain...")
        
        # Construir y enviar la transacción llamando a registrarCO2
        tx_hash = contrato.functions.registrarCO2(co2_actual).transact({
            'from': CUENTA_SENSOR
        })
        
        # Esperar a que la red mine la transacción (como hicimos en el despliegue)
        # Le damos un timeout prudente para que no dé el error TimeExhausted
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
        
        print(f"✅ Dato guardado en el bloque {receipt.blockNumber}! Hash TX: {w3.to_hex(tx_hash)}")
        
        # Pausa antes de la siguiente lectura (ej. 15 segundos)
        time.sleep(15)

except KeyboardInterrupt:
    print("\n🛑 Simulación detenida por el usuario.")
except Exception as e:
    print(f"\n❌ Ocurrió un error: {e}")
