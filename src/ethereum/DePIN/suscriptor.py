import time
from web3 import Web3

# 1. Conexión a tu nodo local (Ganache)
w3 = Web3(Web3.HTTPProvider('http://127.0.0.1:8545'))

# Dirección exacta de tu contrato actual
DIRECCION_CONTRATO = Web3.to_checksum_address("0xd45398a5EEA5691F78eF5c7B24b108b2809B4fc9")

# 2. El ABI CORREGIDO (Apuntando a las variables públicas reales de Solidity)
ABI = [
    {
        "inputs": [],
        "name": "ultimoPromedioCO2",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "hashLoteDatos",
        "outputs": [{"internalType": "bytes32", "name": "", "type": "bytes32"}], # Es bytes32, no string
        "stateMutability": "view",
        "type": "function"
    }
]

# 3. Conectar con el contrato
contrato = w3.eth.contract(address=DIRECCION_CONTRATO, abi=ABI)

print("🎧 Iniciando Centro de Monitoreo...")
print("Leyendo datos de la blockchain (Costo de Gas: 0)\n")

# Guardamos un estado inicial vacío para poder comparar después
ultimo_hash_visto = "0x0000000000000000000000000000000000000000000000000000000000000000"

# 4. El bucle infinito de escucha
while True:
    try:
        co2 = contrato.functions.ultimoPromedioCO2().call()
        hash_datos_raw = contrato.functions.hashLoteDatos().call()
        hash_datos = w3.to_hex(hash_datos_raw)

        # 👀 LÍNEA NUEVA: Imprimimos en crudo lo que leemos cada 3 segundos
        print(f"👀 [Rastreo] CO2: {co2} | Hash: {hash_datos}")

        # Si el hash cambia y no está vacío...
        if hash_datos != ultimo_hash_visto and hash_datos != "0x0000000000000000000000000000000000000000000000000000000000000000":
            print("🚨 ¡NUEVO REPORTE NOTARIZADO EN BLOCKCHAIN!")
            print(f"📊 Nivel de CO2: {co2} ppm")
            print(f"🔐 Hash de Integridad: {hash_datos}")
            print("-" * 40)
            
            ultimo_hash_visto = hash_datos

        time.sleep(3)

    except Exception as e:
        print(f"Error de conexión o lectura: {e}")
        time.sleep(3)
