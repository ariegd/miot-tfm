from web3 import Web3
import time

# 1. Conexión a tu blockchain local (Ganache)
w3 = Web3(Web3.HTTPProvider('http://127.0.0.1:8545'))

# ==========================================
# ⚠️ RELLENA ESTOS DATOS CON LOS DE TU GANACHE
# ==========================================
DIRECCION_MERCADO = Web3.to_checksum_address("0x9BD7dcd1c25A778E9b274B6047698d832ad9268e")
CLAVE_PRIVADA_BOT = "0xfc2ff063ced42aadda62a0885de5aa0017a64e319a535aeae56188bd16dcfb3b"
DIRECCION_BOT = Web3.to_checksum_address("0x3b44e1c4751ae273435233841e8b5b3522ead4cd")

# Este es el "mapa" mínimo para que Python encuentre las dos funciones que necesitamos
abi_mercado = [
    {
        "inputs": [],
        "name": "ejecutarIntercambio",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "tiempoRestante",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    }
]

# 2. Cargar el contrato en Python
contrato = w3.eth.contract(address=DIRECCION_MERCADO, abi=abi_mercado)

print("🤖 Bot iniciado. Conectado a Ganache:", w3.is_connected())
print("Buscando el mercado en:", DIRECCION_MERCADO)
print("-" * 40)

# 3. El Bucle Infinito (El Despertador)
while True:
    # Leemos el contrato (esto es gratis, no gasta Gas)
    segundos_faltantes = contrato.functions.tiempoRestante().call()

    if segundos_faltantes > 0:
        print(f"⏳ El mercado sigue cerrado. Faltan {segundos_faltantes} segundos. Esperando...")
        time.sleep(5) # Pausa el bot 5 segundos para no saturar tu computadora
    else:
        print("🚀 ¡ES LA HORA! El mercado está abierto. Preparando la transacción...")

        # Como vamos a ESCRIBIR en la blockchain, necesitamos armar y firmar una transacción
        nonce = w3.eth.get_transaction_count(DIRECCION_BOT)

        # Construimos la transacción
        tx = contrato.functions.ejecutarIntercambio().build_transaction({
            'chainId': w3.eth.chain_id,
            'gas': 500000, # Límite de gas
            'gasPrice': w3.eth.gas_price,
            'nonce': nonce,
        })

        # Firmamos la transacción con la clave privada secreta
        tx_firmada = w3.eth.account.sign_transaction(tx, CLAVE_PRIVADA_BOT)

        # ¡Disparamos la transacción a la red!
        tx_hash = w3.eth.send_raw_transaction(tx_firmada.raw_transaction)

        print(f"✅ ¡Transacción enviada con éxito!")
        print(f"🔍 Hash de la operación: {w3.to_hex(tx_hash)}")
        print("🎉 ¡Intercambio completado! El comprador tiene la casa y el vendedor el dinero.")

        break # Rompemos el bucle para que el bot se apague
