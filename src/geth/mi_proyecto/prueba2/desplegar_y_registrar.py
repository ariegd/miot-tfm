import json
import solcx
from web3 import Web3
from web3.middleware import ExtraDataToPOAMiddleware

# 1. Compilar
solcx.install_solc('0.8.19')
with open("RegistroCO2Distribuido.sol", "r") as file:
    contrato_solidity = file.read()

compiled_sol = solcx.compile_standard({
    "language": "Solidity",
    "sources": {"RegistroCO2Distribuido.sol": {"content": contrato_solidity}},
    "settings": {"outputSelection": {"*": {"*": ["abi", "evm.bytecode.object"]}}}
}, solc_version="0.8.19")

bytecode = compiled_sol["contracts"]["RegistroCO2Distribuido.sol"]["RegistroCO2Distribuido"]["evm"]["bytecode"]["object"]
abi = compiled_sol["contracts"]["RegistroCO2Distribuido.sol"]["RegistroCO2Distribuido"]["abi"]

# Guardar ABI para los Nodos Fog
with open("abi.json", "w") as f:
    json.dump(abi, f)

# 2. Conectar y Desplegar
w3 = Web3(Web3.HTTPProvider('http://127.0.0.1:8545'))
w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)
admin = w3.eth.accounts[0]

print("Desplegando contrato...")
Registro = w3.eth.contract(abi=abi, bytecode=bytecode)
tx_hash = Registro.constructor().transact({'from': admin})
tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
direccion = tx_receipt.contractAddress
print(f"Contrato desplegado en: {direccion}")

# 3. Registrar dos Entidades (SoC / Nodos Fog)
# Usaremos la cuenta 0 para la UCA y la cuenta 1 para el Ayuntamiento
cuenta_uca = w3.eth.accounts[0]
cuenta_ayto = w3.eth.accounts[1] # Asegúrate de que esta cuenta tenga saldo y esté desbloqueada en Geth

contrato = w3.eth.contract(address=direccion, abi=abi)

print("Registrando Nodo UCA...")
tx1 = contrato.functions.registrarEntidad(cuenta_uca, "La Viña", "Calle Palma").transact({'from': admin})
w3.eth.wait_for_transaction_receipt(tx1)

print("Registrando Nodo Ayuntamiento...")
tx2 = contrato.functions.registrarEntidad(cuenta_ayto, "La Viña", "Calle San Felix").transact({'from': admin})
w3.eth.wait_for_transaction_receipt(tx2)

print("Infraestructura de Cádiz configurada.")
