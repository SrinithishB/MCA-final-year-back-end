from web3 import Web3
import json
import os

RPC_URL = "http://127.0.0.1:8545"

w3 = Web3(Web3.HTTPProvider(RPC_URL))

account = w3.eth.accounts[0]
# account = w3.to_checksum_address("0xF464fcE315591fDE6a79d3E460B35044E6287788")

BASE_DIR = os.path.dirname(__file__)

# ------------------ DrugRegistry ------------------

LOWER_DRUG_ADDRESS = "0x0B93409f07d2de83E429dCd2073CEd8b304bD371"
DRUG_ADDRESS = Web3.to_checksum_address(LOWER_DRUG_ADDRESS)

with open(os.path.join(BASE_DIR, "DrugRegistryABI.json")) as f:
    drug_abi = json.load(f)

drug_contract = w3.eth.contract(
    address=DRUG_ADDRESS,
    abi=drug_abi
)

# ------------------ ReaderRegistry ------------------

LOWER_READER_ADDRESS = "0x1978504F492aC54b5456Daf7F1818F064024B4c9"
READER_ADDRESS = Web3.to_checksum_address(LOWER_READER_ADDRESS)

with open(os.path.join(BASE_DIR, "ReaderRegistryABI.json")) as f:
    reader_abi = json.load(f)

reader_contract = w3.eth.contract(
    address=READER_ADDRESS,
    abi=reader_abi
)

# ------------------ TraceLogRegistry ------------------

LOWER_TRACE_ADDRESS = "0x4a3B8552a9a78FcF592Fd38749d2e05a04934585"
TRACE_CONTRACT_ADDRESS = Web3.to_checksum_address(LOWER_TRACE_ADDRESS)

with open(os.path.join(BASE_DIR, "TraceLogRegistryABI.json")) as f:
    trace_abi = json.load(f)

trace_contract = w3.eth.contract(
    address=TRACE_CONTRACT_ADDRESS,
    abi=trace_abi
)
