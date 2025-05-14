# dex-pool-analyzer

Skrypt analizujący pule DEX (Uniswap V2/V3, SushiSwap, PancakeSwap) na podstawie adresu puli.

## Wymagania

- Python 3.7+
- Zainstalowane biblioteki z `requirements.txt`
- Plik `.env` z kluczem INFURA

## Instalacja

```bash
git clone https://github.com/tymczasowe/dex-pool-analyzer.git
cd dex-pool-analyzer
pip install -r requirements.txt
cp .env.example .env
# Edytuj .env i dodaj swój klucz INFURA
