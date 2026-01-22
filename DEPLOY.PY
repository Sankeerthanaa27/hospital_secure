from solcx import compile_source, install_solc
from web3 import Web3
import os

install_solc("0.8.0")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONTRACT_PATH = os.path.join(BASE_DIR, "..", "contracts", "AccessControl.sol")

with open(CONTRACT_PATH, "r") as f:
    source = f.read()

compiled = compile_source(source, solc_version="0.8.0")
contract_id, contract_interface = compiled.popitem()

abi = contract_interface["abi"]
bytecode = contract_interface["bin"]

w3 = Web3(Web3.HTTPProvider("http://127.0.0.1:7545"))
acct = w3.eth.accounts[0]

Access = w3.eth.contract(abi=abi, bytecode=bytecode)
tx_hash = Access.constructor().transact({"from": acct})
tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

print("\n✅ Contract deployed successfully!")
print("📌 Contract Address:", tx_receipt.contractAddress)
print("\n📌 ABI:")
print(abi)

