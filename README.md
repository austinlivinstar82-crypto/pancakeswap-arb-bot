# PancakeSwap V2/V3 Arbitrage Bot

A Python bot that watches PancakeSwap V2 and V3 pools on BNB Chain for
price gaps between them, and simulates flash-loan arbitrage trades to
capture the difference.

> **Disclaimer:** Built for research and educational purposes. This is
> not financial advice. Cryptocurrency trading carries substantial risk,
> flash-loan arbitrage in particular can fail or lose money to slippage,
> gas costs, and failed transactions. Use at your own risk.

## Features
- **Dual-Pool Monitoring:** Tracks PancakeSwap V2 (Sync events) and V3
  (price polling) simultaneously to spot gaps between them.
- **Slippage Prediction:** Estimates real slippage before executing,
  rather than relying on the quoted price alone.
- **Liquidity Checks:** Requires both pools to hold a minimum liquidity
  before considering a trade, to avoid pools too thin to trade safely.
- **Profitability Analysis:** Nets out V2/V3 fees, flash-loan fees,
  predicted slippage, and gas cost before deciding a trade is worth it.
- **MEV-Protected Execution:** Sends transactions through a protected RPC
  endpoint to reduce sandwich-attack risk.

## Tech Stack
- Python 3.x (`asyncio`)
- `web3.py`, `termcolor`

## Project Structure
```text
pancakeswap-arb-bot/
├── Arb.py          # Main bot: pool monitoring, arbitrage logic, execution
└── .gitignore
```

## Getting Started

### Prerequisites
Python 3.8 or higher

### Installation
```bash
pip install web3 termcolor
```

### Configuration
This bot reads its secrets from environment variables, never from the
code. Set the following before running:
```bash
BSC_WSS_URL=your_bsc_rpc_wss_url
GAS_WALLET_ADDRESS=your_wallet_address
PRIVATE_KEY=your_wallet_private_key
```
**Never share your private key or commit a `.env` file containing it.**

### Usage
```bash
python Arb.py
```
