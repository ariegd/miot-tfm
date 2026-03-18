from web3 import Web3
import json

# 1. Conexión al Ganache de Docker
w3 = Web3(Web3.HTTPProvider('http://localhost:8545'))

# 2. Configuración del contrato
# Copia la dirección que te dio Forge (la del status: success)
#contract_address = "0x8137cea3a1996ffd6f1ee40b2b8a1b2a93301f5d"
# Cambia esta línea:
contract_address = Web3.to_checksum_address("0x8137cea3a1996ffd6f1ee40b2b8a1b2a93301f5d")


# El ABI es la "traducción" para que Python sepa qué funciones existen
# Lo sacamos de la salida que te dio Forge antes
abi = json.loads('[{"type":"function","name":"escribir","inputs":[{"name":"_nuevaNota","type":"string","internalType":"string"}],"outputs":[],"stateMutability":"nonpayable"},{"type":"function","name":"nota","inputs":[],"outputs":[{"name":"","type":"string","internalType":"string"}],"stateMutability":"view"}]')

# Crear el objeto del contrato
contrato = w3.eth.contract(address=contract_address, abi=abi)

def leer_nota():
    # .call() es para lectura (gratis)
    mensaje = contrato.functions.nota().call()
    print(f"--- Nota actual en la Blockchain: {mensaje} ---")

def escribir_nota(nuevo_texto):
    print(f"Enviando transacción para escribir: {nuevo_texto}...")
    # .transact() es para escritura (cuesta Gas)
    # Usamos la cuenta 0 de Ganache
    cuenta = w3.eth.accounts[0]
    
    tx_hash = contrato.functions.escribir(nuevo_texto).transact({
        'from': cuenta,
        'gas': 100000 # El límite de gas que vimos que funcionaba
    })
    
    # Esperar a que se mine el bloque
    recibo = w3.eth.wait_for_transaction_receipt(tx_hash)
    print(f"Éxito! Bloque: {recibo.blockNumber}")

# --- PRUEBA PRÁCTICA ---
if w3.is_connected():
    leer_nota() # Debería decir "Funciona perfectamente"
    escribir_nota("Mensaje desde Python 3!")
    leer_nota() # Debería mostrar el nuevo mensaje
else:
    print("No se pudo conectar a Ganache")
