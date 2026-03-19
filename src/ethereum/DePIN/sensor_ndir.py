from web3 import Web3
import time
import random
import hashlib

# 1. Conexión a Ganache
w3 = Web3(Web3.HTTPProvider('http://127.0.0.1:8545'))

# ⚠️ RELLENA CON TUS DATOS DE GANACHE (Como hicimos antes)
DIRECCION_CONTRATO = Web3.to_checksum_address("0xd45398a5EEA5691F78eF5c7B24b108b2809B4fc9")
CLAVE_PRIVADA_SENSOR = "0x24cfdbcdc11822aa56503e77c0dc3073e44785404aeab7d05e5de2a0e8ce4801" 
DIRECCION_SENSOR = Web3.to_checksum_address("0x294df5986cdb4dc9c2bbfc679229997b17c99ee8")

# ABI simplificado del nuevo contrato
abi_sensor = [
    {
        "inputs": [{"internalType": "uint256","name": "_promedio","type": "uint256"},
                   {"internalType": "bytes32","name": "_hashLote","type": "bytes32"}],
        "name": "publicarDatos",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [], "name": "ultimoPromedioCO2",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view", "type": "function"
    }
]

contrato = w3.eth.contract(address=DIRECCION_CONTRATO, abi=abi_sensor)

print("📡 Sensor NDIR (Oráculo) encendido y conectado.")

# Variable para el patrón Publish-Subscribe (solo publicar si hay cambio > 15 ppm)
UMBRAL_DE_CAMBIO = 15

while True:
    print("\n--- Recopilando datos físicos ---")
    
    # 1. Simulación de Hardware: Leer CO2 cada segundo durante 5 segundos
    lecturas_crudas = [random.randint(380, 450) for _ in range(5)]
    print(f"Lecturas crudas (ppm): {lecturas_crudas}")
    
    # 2. CÓMPUTO OFF-CHAIN: Hacemos la matemática en Python, no en Ethereum
    promedio_actual = int(sum(lecturas_crudas) / len(lecturas_crudas))
    
    # 3. OPTIMIZACIÓN DE GAS: Generar un Hash de los datos crudos
    datos_string = str(lecturas_crudas).encode('utf-8')
    hash_lote = Web3.keccak(text=str(lecturas_crudas)) # Hash keccak256 estándar de Ethereum
    
    print(f"🧮 Promedio calculado Off-chain: {promedio_actual} ppm")
    print(f"🔒 Hash de integridad: {w3.to_hex(hash_lote)}")

    # 4. PATRÓN PUBLISH-SUBSCRIBE: Decidir si enviamos la transacción
    ultimo_promedio_onchain = contrato.functions.ultimoPromedioCO2().call()
    
    diferencia = abs(promedio_actual - ultimo_promedio_onchain)
    
    if diferencia >= UMBRAL_DE_CAMBIO or ultimo_promedio_onchain == 0:
        print(f"⚠️ Cambio significativo detectado ({diferencia} ppm). Actualizando Blockchain...")
        
        # Enviar transacción (pagar Gas)
        nonce = w3.eth.get_transaction_count(DIRECCION_SENSOR)
        tx = contrato.functions.publicarDatos(promedio_actual, hash_lote).build_transaction({
            'chainId': w3.eth.chain_id,
            'gas': 300000,
            'gasPrice': w3.eth.gas_price,
            'nonce': nonce,
        })
        
        tx_firmada = w3.eth.account.sign_transaction(tx, CLAVE_PRIVADA_SENSOR)
        tx_hash = w3.eth.send_raw_transaction(tx_firmada.raw_transaction)
        
        # Esperamos a que la red procese la tx para ver si falló
        recibo = w3.eth.wait_for_transaction_receipt(tx_hash)
        print(f"⛽ Gas real consumido: {recibo.gasUsed} unidades de Gas")
        
        if recibo.status == 1:
            print("✅ Transacción guardada en la blockchain con éxito.")
        else:
            print("❌ LA TRANSACCIÓN FALLÓ (Revert de la EVM).")
        
        print(f"✅ Datos publicados en la red. Hash TX: {w3.to_hex(tx_hash)}")
    else:
        # Consultas Locales (Polling gratuito)
        print(f"💤 Sin cambios significativos (Dif: {diferencia} ppm). Ahorrando Gas. No se envía transacción.")

    # El sensor físico duerme 10 segundos antes del siguiente escaneo
    time.sleep(10)
