import os
import argparse
import requests
from web3 import Web3
from dotenv import load_dotenv

# === Wczytaj dane z pliku .env ===
load_dotenv()
INFURA_KEY = os.getenv("INFURA_API_KEY")
INFURA_URL = f"https://mainnet.infura.io/v3/{INFURA_KEY}"

# === Parsowanie argumentów CLI ===
parser = argparse.ArgumentParser(description="DEX Pool Analyzer")
parser.add_argument("--pair", required=True, help="Adres puli (pair address)")
args = parser.parse_args()

w3 = Web3(Web3.HTTPProvider(INFURA_URL))
pool_address = w3.to_checksum_address(args.pair)

# === ABI i FACTORY ===
ERC20_ABI = [
    {"constant": True, "inputs": [], "name": "decimals", "outputs": [{"name": "", "type": "uint8"}], "type": "function"},
    {"constant": True, "inputs": [], "name": "symbol", "outputs": [{"name": "", "type": "string"}], "type": "function"}
]

PAIR_ABI_V2 = [
    {"name": "getReserves", "outputs": [{"type": "uint112", "name": "reserve0"}, {"type": "uint112", "name": "reserve1"}, {"type": "uint32", "name": "blockTimestampLast"}], "inputs": [], "stateMutability": "view", "type": "function"},
    {"name": "token0", "outputs": [{"type": "address", "name": ""}], "inputs": [], "stateMutability": "view", "type": "function"},
    {"name": "token1", "outputs": [{"type": "address", "name": ""}], "inputs": [], "stateMutability": "view", "type": "function"},
    {"name": "factory", "outputs": [{"type": "address", "name": ""}], "inputs": [], "stateMutability": "view", "type": "function"},
]

PAIR_ABI_V3 = [
    {"name": "slot0", "outputs": [
        {"name": "sqrtPriceX96", "type": "uint160"},
        {"name": "tick", "type": "int24"},
        {"name": "", "type": "uint16"},
        {"name": "", "type": "uint16"},
        {"name": "", "type": "uint16"},
        {"name": "", "type": "uint128"},
        {"name": "", "type": "uint128"}
    ], "inputs": [], "stateMutability": "view", "type": "function"},
    {"name": "token0", "outputs": [{"type": "address", "name": ""}], "inputs": [], "stateMutability": "view", "type": "function"},
    {"name": "token1", "outputs": [{"type": "address", "name": ""}], "inputs": [], "stateMutability": "view", "type": "function"},
    {"name": "factory", "outputs": [{"type": "address", "name": ""}], "inputs": [], "stateMutability": "view", "type": "function"},
]

FACTORIES = {
    "0x5C69bEe701ef814a2B6a3EDD4B1652CB9cc5aA6f": "Uniswap V2",
    "0x1F98431c8aD98523631AE4a59f267346ea31F984": "Uniswap V3",
    "0xC0AEe478e3658e2610c5F7A4A2E1777Ce9e4f2Ac": "SushiSwap V2",
    "0xBCfCcbde45cE874adCB698cC183deBcF17952812": "PancakeSwap (BSC)",
}

def get_token_info(addr):
    token = w3.eth.contract(address=addr, abi=ERC20_ABI)
    try:
        return token.functions.symbol().call(), token.functions.decimals().call()
    except:
        return "???", 18

# === Próba jako V2 ===
try:
    contract = w3.eth.contract(address=pool_address, abi=PAIR_ABI_V2)
    factory_addr = contract.functions.factory().call()
    token0_addr = contract.functions.token0().call()
    token1_addr = contract.functions.token1().call()
    reserve0, reserve1, _ = contract.functions.getReserves().call()
    version = "V2"
    print("✅ Wykryto kontrakt V2")
except:
    # Próba jako V3
    contract = w3.eth.contract(address=pool_address, abi=PAIR_ABI_V3)
    factory_addr = contract.functions.factory().call()
    token0_addr = contract.functions.token0().call()
    token1_addr = contract.functions.token1().call()
    sqrtPriceX96 = contract.functions.slot0().call()[0]
    version = "V3"
    print("✅ Wykryto kontrakt V3")

dex = FACTORIES.get(factory_addr, "❓ Nieznana giełda")
print(f"🔎 Factory: {factory_addr} → {dex}")

sym0, dec0 = get_token_info(token0_addr)
sym1, dec1 = get_token_info(token1_addr)
print(f"🔗 Token0: {sym0}, Token1: {sym1}")

if version == "V2":
    price = (reserve1 / 10**dec1) / (reserve0 / 10**dec0)
    print(f"💰 Cena: 1 {sym0} ≈ {price:.6f} {sym1}")
elif version == "V3":
    import math
    price = (sqrtPriceX96 / (2**96))**2
    price = price * (10**(dec0 - dec1))
    print(f"💰 Cena (V3): 1 {sym0} ≈ {price:.6f} {sym1}")
