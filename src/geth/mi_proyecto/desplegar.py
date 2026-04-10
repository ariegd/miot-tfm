import json
from web3 import Web3
from web3.middleware import ExtraDataToPOAMiddleware
import solcx

# 1. Descargamos e instalamos el compilador (versión 0.8.19 de tu contrato)
print("Instalando compilador Solidity...")
solcx.install_solc('0.8.19')

# 2. Leemos el archivo físico de tu Smart Contract
with open("RegistroCO2.sol", "r") as file:
    contrato_solidity = file.read()

# 3. Compilamos el código humano a lenguaje máquina (Bytecode y ABI)
print("Compilando el contrato...")
compiled_sol = solcx.compile_standard(
    {
        "language": "Solidity",
        "sources": {"RegistroCO2.sol": {"content": contrato_solidity}},
        "settings": {
            "outputSelection": {
                "*": {"*": ["abi", "metadata", "evm.bytecode", "evm.sourceMap"]}
            }
        },
    },
    solc_version="0.8.19",
)

# Extraemos los datos útiles de la compilación
bytecode = compiled_sol["contracts"]["RegistroCO2.sol"]["RegistroCO2"]["evm"]["bytecode"]["object"]
abi = compiled_sol["contracts"]["RegistroCO2.sol"]["RegistroCO2"]["abi"]

# 4. Nos conectamos a tu nodo Geth en Debian
print("Conectando al nodo Geth...")
w3 = Web3(Web3.HTTPProvider('http://127.0.0.1:8545'))

# Añade esta línea para que acepte los 97 bytes
w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)

if not w3.is_connected():
    print("Error: No se pudo conectar a Geth. Revisa la IP y el nodo.")
    exit()
print("¡Conexión exitosa a Geth!")

# 5. Preparamos la transacción
# Como arrancaste Geth con tu cuenta desbloqueada, usamos la primera disponible
cuenta_minera = w3.eth.accounts[0]
print(f"Usando la cuenta minera: {cuenta_minera}")

# Le decimos a Web3 cómo es el contrato
Registro = w3.eth.contract(abi=abi, bytecode=bytecode)

# 6. ¡Desplegamos!
print("Enviando contrato a la red... (Asegúrate de que Geth está minando)")
tx_hash = Registro.constructor().transact({'from': cuenta_minera})

# Esperamos a que tu nodo Geth mine el bloque y confirme la transacción
tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

print("\n" + "="*50)
print(f"¡ÉXITO! Contrato guardado para siempre en tu blockchain.")
print(f"Guarda esta dirección del contrato: {tx_receipt.contractAddress}")
print("="*50 + "\n")

# Extra: Guardamos el ABI en un archivo para usarlo en el futuro
with open("abi.json", "w") as f:
    json.dump(abi, f)
print("Archivo 'abi.json' guardado. Lo necesitarás para interactuar con el contrato luego.")
