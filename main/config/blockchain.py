from web3 import Web3
import json
import os

RPC_URL = "http://127.0.0.1:8545"

w3 = Web3(Web3.HTTPProvider(RPC_URL))

account = w3.eth.accounts[0]
# account = w3.to_checksum_address("0xF464fcE315591fDE6a79d3E460B35044E6287788")

BASE_DIR = os.path.dirname(__file__)

# ------------------ DrugRegistry ------------------

LOWER_DRUG_ADDRESS = "0x5c1928A82CbfD9f24BC9Ef68a2268a2fc9697A54"
DRUG_ADDRESS = Web3.to_checksum_address(LOWER_DRUG_ADDRESS)

with open(os.path.join(BASE_DIR, "DrugRegistryABI.json")) as f:
    drug_abi = json.load(f)

drug_contract = w3.eth.contract(
    address=DRUG_ADDRESS,
    abi=drug_abi
)

# ------------------ ReaderRegistry ------------------

LOWER_READER_ADDRESS = "0xB944eE444f0Ca83d4f48A24099A96E2f8CBcF93D"
READER_ADDRESS = Web3.to_checksum_address(LOWER_READER_ADDRESS)

with open(os.path.join(BASE_DIR, "ReaderRegistryABI.json")) as f:
    reader_abi = json.load(f)

reader_contract = w3.eth.contract(
    address=READER_ADDRESS,
    abi=reader_abi
)

# ------------------ TraceLogRegistry ------------------

LOWER_TRACE_ADDRESS = "0xD3f2Fc44Ef269deA8eb11597D8544455f9F7757d"
TRACE_CONTRACT_ADDRESS = Web3.to_checksum_address(LOWER_TRACE_ADDRESS)

with open(os.path.join(BASE_DIR, "TraceLogRegistryABI.json")) as f:
    trace_abi = json.load(f)

trace_contract = w3.eth.contract(
    address=TRACE_CONTRACT_ADDRESS,
    abi=trace_abi
)
