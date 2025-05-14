import os
import math
import argparse
import requests
from web3 import Web3
from dotenv import load_dotenv

# === Load .env ===
load_dotenv()
INFURA_KEY = os.getenv("INFURA_API_KEY")
INFURA_URL = f"https://mainnet.infura.io/v3/{INFURA_KEY}"

# === CLI ===
parser = argparse.ArgumentParser(description="DEX Pool Analyzer")
parser.add_argument("--pair", required=True, help="Address of the pool contract")
args = parser.parse_args()
POOL_ADDRESS = Web3.to_checksum_address(args.pair)

w3 = Web3(Web3.HTTPProvider(INFURA_URL))

# === Known DEX factories ===
FACTORIES = {
    "0x5C69bEe701ef814a2B6a3EDD4B1652CB9cc5aA6f": "Uniswap V2",
    "0x1F98431c8aD98523631AE4a59f267346ea31F984": "Uniswap V3",
    "0xC0AEe478e3658e2610c5F7A4A2E1777Ce9e4f2Ac": "SushiSwap V2",
    "0xBCfCcbde45cE874adCB698cC183deBcF17952812": "PancakeSwap (BSC)",
}

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
    {"name": "slot0", "outputs": [{"name": "sqrtPriceX96", "type": "uint160"}, {"name": "tick", "type": "int24"}, {"type": "uint16"}, {"type": "uint16"}, {"type": "uint16"}, {"type": "uint128"}, {"type": "uint128"}], "inputs": [], "stateMutability": "view", "type": "function"},
    {"name": "token0", "outputs": [{"type": "address", "name": ""}], "inputs": [], "stateMutability": "view", "type": "function"},
    {"name": "token1", "outputs": [{"type": "address", "name": ""}], "inputs": [], "stateMutability": "view", "type": "function"},
    {"name": "factory", "outputs": [{"type": "address", "name": ""}], "inputs": [], "stateMutability": "view", "type": "function"},
]

# === Fallback przez DexScreener API ===
def get_symbol_from_dexscreener(pair_address, token_index):
    try:
        url = f"https://api.dexscreener.com/latest/dex/pairs/ethereum/{pair_address}"
        r = requests.get(url)
        data = r.json()
        if token_index == 0:
            return data["pair"]["baseToken"]["symbol"]
        else:
            return data["pair"]["quoteToken"]["symbol"]
    except:
        return "???"

# === Token info helper ===
def get_token_info(addr, index):
    token = w3.eth.contract(address=addr, abi=ERC20_ABI)
    try:
        symbol = token.functions.symbol().call()
    except:
        symbol = get_symbol_from_dexscreener(POOL_ADDRESS, index)
    try:
        decimals = token.functions.decimals().call()
    except:
        decimals = 18
    return symbol, decimals

# === Analiza kontraktu ===
try:
    contract = w3.eth.contract(address=POOL_ADDRESS, abi=PAIR_ABI_V2)
    factory_addr = contract.functions.factory().call()
    token0_addr = contract.functions.token0().call()
    token1_addr = contract.functions.token1().call()
    reserve0, reserve1, _ = contract.functions.getReserves().call()
    version = "V2"
    print("✅ Wykryto kontrakt V2")
except:
    contract = w3.eth.contract(address=POOL_ADDRESS, abi=PAIR_ABI_V3)
    factory_addr = contract.functions.factory().call()
    token0_addr = contract.functions.token0().call()
    token1_addr = contract.functions.token1().call()
    sqrtPriceX96 = contract.functions.slot0().call()[0]
    version = "V3"
    print("✅ Wykryto kontrakt V3")

dex = FACTORIES.get(factory_addr, "❓ Nieznana giełda")
print(f"🔎 Factory: {factory_addr} → {dex}")

sym0, dec0 = get_token_info(token0_addr, 0)
sym1, dec1 = get_token_info(token1_addr, 1)
print(f"🔗 Token0: {sym0}, Token1: {sym1}")

if version == "V2":
    price = (reserve1 / 10**dec1) / (reserve0 / 10**dec0)
    print(f"💰 Cena: 1 {sym0} ≈ {price:.6f} {sym1}")
elif version == "V3":
    price = (sqrtPriceX96 / (2**96))**2
    price = price * (10**(dec0 - dec1))
    print(f"💰 Cena (V3): 1 {sym0} ≈ {price:.6f} {sym1}")
