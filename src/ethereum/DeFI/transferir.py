from web3 import Web3

# Conectar al Ganache de Docker
w3 = Web3(Web3.HTTPProvider('http://localhost:8545'))

if w3.is_connected():
    accounts = w3.eth.accounts
    # Enviar 5 ETH de la cuenta 0 a la 1
    tx_hash = w3.eth.send_transaction({
        'from': accounts[0],
        'to': accounts[1],
        'value': w3.to_wei(5, 'ether')
    })
    print(f"Transferencia realizada! Hash: {tx_hash.hex()}")
    print(f"Nuevo saldo cuenta 1: {w3.from_wei(w3.eth.get_balance(accounts[1]), 'ether')} ETH")
