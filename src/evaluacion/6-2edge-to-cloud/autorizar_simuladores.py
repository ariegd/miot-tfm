import json
from web3 import Web3
from web3.middleware import ExtraDataToPOAMiddleware

# 1. Conexión al nodo de Geth local del portátil administrador
w3 = Web3(Web3.HTTPProvider('http://127.0.0.1:8545'))
w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)

DIRECCION_CONTRATO = "0xDd6AdbD324d45238020C19Cce5ea42469F19B940"
admin = w3.eth.accounts[0]  # Cuenta 0xa1be... del portátil

with open("abi.json", "r") as file:
    ABI = json.load(file)

contrato = w3.eth.contract(address=DIRECCION_CONTRATO, abi=ABI)

# Lista exacta de las 11 direcciones generadas en la rpi-nodo1
cuentas_rpi = [
    "0x125dE73500FaB486F908F39b09d9D323eb982FFD",
    "0x686A64A687ca36aB514b899Fe7341fc242232e5f",
    "0x2e95C4AE8110c83bAee568Ded4aBce2340C72792",
    "0x18222f72C5Db1983b4E3ED21413D9795eEc37415",
    "0xe7F22A72A3E5360DE00e900783839C11Ba617EB1",
    "0x207F2dC92bcA3071C7Fca3F8d2d5Ad044B8b9a51",
    "0xca8D558dE0271cbf0890bA117B42C49c37D50F05",
    "0x9097807A4C513572155De0228b0F525e33F5B99D",
    "0x7fe2fa8d4c1425b7f7e5E6d38CB83a5E65E3A747",
    "0x0b22D43b663d7186Adb7CeAe5Fe91201dF0820C2",
    "0x6Df43412e524f4a922d959877aB387DA3bD610c2"
]

print(" Iniciando proceso de federación desde el Nodo Administrador...")

for idx, addr in enumerate(cuentas_rpi, start=1):
    checksum_addr = Web3.to_checksum_address(addr)
    
    # A. Transmisión del registro formal hacia el Smart Contract
    print(f"[{idx}/11] Registrando en SC: {checksum_addr}")
    tx_reg = contrato.functions.registrarEntidad(
        checksum_addr, "Clasico_HTTP", f"Sensor_Directo_{idx}"
    ).transact({'from': admin})
    w3.eth.wait_for_transaction_receipt(tx_reg)
    
    # B. Transferencia líquida de 5 ETH para la gestión local de Gas
    tx_gas = w3.eth.send_transaction({
        'from': admin,
        'to': checksum_addr,
        'value': w3.to_wei(5, 'ether')
    })
    w3.eth.wait_for_transaction_receipt(tx_gas)
    print(f"       -> Estatus: Autorizado y Fondeado con éxito.")

print("\n ¡Entorno preparado! Las cuentas ya son válidas ante la EVM y poseen balance propio.")
