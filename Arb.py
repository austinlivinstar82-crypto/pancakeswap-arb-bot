# =========================================================================
# PANCAKESWAP V2/V3 ARBITRAGE BOT - FINAL PRODUCTION v2.1
# =========================================================================
# Built by: [UZORCHUKWU LIVINUS]
# Status: PRODUCTION READY WITH ALL UPGRADES
# Last Updated: December 28, 2024
# UPGRADES: Two V3 pools, updated fees, fixed slippage
# =========================================================================

import asyncio
import time
import statistics
import os
from web3 import AsyncWeb3, Web3
from web3.providers.persistent import WebSocketProvider
from datetime import datetime
from decimal import Decimal, getcontext
from termcolor import cprint, colored
# Set precision for financial calculations
getcontext().prec = 50

# =========================================================================
# 1. CONFIGURATION (OPTIMIZED + UPGRADED)
# =========================================================================
# Network
WSS_URL = os.environ.get("BSC_WSS_URL", "")
MEV_PROTECTED_RPC = "https://bscrpc.pancakeswap.finance"  # 🔥 NEW - MEV Guard

# Token Addresses (BSC Mainnet)
WBNB_ADDRESS = Web3.to_checksum_address("0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c")
USDT_ADDRESS = Web3.to_checksum_address("0x55d398326f99059fF775485246999027B3197955")

# Pool Addresses
V2_PAIR_ADDRESS = Web3.to_checksum_address("0x16b9a82891338f9bA80E2D6970FddA79D1eb0daE")
V3_SWAP_POOL = Web3.to_checksum_address('0x172fcD41E0913e95784454622d1c3724f546f849')  # $30M - For swaps
V3_FLASH_POOL = Web3.to_checksum_address('0x36696169C63e42cd08ce11f5deeBbCeBae652050') # $5M - For flash loan
V3_FACTORY_ADDRESS = '0x0BFbCF9fa4f9C56B0F40a671Ad40E0805A091865'
V2_FACTORY_ADDRESS = '0xcA143Ce32Fe78f1f7019d7d551a6402fC5350c73'

# Wallet Configuration
GAS_WALLET_ADDRESS = Web3.to_checksum_address(os.environ.get("GAS_WALLET_ADDRESS", ""))
PRIVATE_KEY = os.environ.get("PRIVATE_KEY", "")
FLASH_LOAN_CONTRACT_ADDRESS = Web3.to_checksum_address("0x01A03D70c7E5e4dFC9d79B65E193b379d5738b93")

# Trading Parameters (🔥 UPGRADED)
TARGET_FLASH_USD = 25_000       # Maximum capital
MAX_SLIPPAGE_PERCENT = 1     # Max allowed slippage
MIN_PROFIT_USD = 10.0           # Minimum profit after ALL costs
MIN_GAP_PERCENT = 0.6       # Minimum gap to consider
MIN_LIQUIDITY_USD = 3_000_000   # 🔥 NEW: Minimum pool liquidity
PROFIT_SAFETY_MARGIN = 1.0      # 🔥 NEW: Skip if profit < margin * min_profit

# Token Decimals
WBNB_DECIMALS = 18
USDT_DECIMALS = 18
WBNB_POWER_DEC = Decimal(10 ** WBNB_DECIMALS)
USDT_POWER_DEC = Decimal(10 ** USDT_DECIMALS)

# V3 Fee Tier
FEE_TIERS = [100]  # 0.01% pool
        
# Global variables
V2_PRICE = 0.0
last_v3_price = None
last_printed_gap = None
last_gap_timestamp = None
V3_POOL_ADDRESS_DYNAMIC = None
FLASH_LOAN_FEE = 0.0005  # 🔥 UPDATED: 0.05% flash fee from $5M pool

# Duplicate Prevention
last_printed_gap = None
last_gap_timestamp = None

# =========================================================================
# 2. CONTRACT ABIS (PASTE YOUR ABIS HERE)
# =========================================================================
V2_PAIR_ABI = [{"inputs":[],"payable":False,"stateMutability":"nonpayable","type":"constructor"},{"anonymous":False,"inputs":[{"indexed":True,"internalType":"address","name":"owner","type":"address"},{"indexed":True,"internalType":"address","name":"spender","type":"address"},{"indexed":False,"internalType":"uint256","name":"value","type":"uint256"}],"name":"Approval","type":"event"},{"anonymous":False,"inputs":[{"indexed":True,"internalType":"address","name":"sender","type":"address"},{"indexed":False,"internalType":"uint256","name":"amount0","type":"uint256"},{"indexed":False,"internalType":"uint256","name":"amount1","type":"uint256"},{"indexed":True,"internalType":"address","name":"to","type":"address"}],"name":"Burn","type":"event"},{"anonymous":False,"inputs":[{"indexed":True,"internalType":"address","name":"sender","type":"address"},{"indexed":False,"internalType":"uint256","name":"amount0","type":"uint256"},{"indexed":False,"internalType":"uint256","name":"amount1","type":"uint256"}],"name":"Mint","type":"event"},{"anonymous":False,"inputs":[{"indexed":True,"internalType":"address","name":"sender","type":"address"},{"indexed":False,"internalType":"uint256","name":"amount0In","type":"uint256"},{"indexed":False,"internalType":"uint256","name":"amount1In","type":"uint256"},{"indexed":False,"internalType":"uint256","name":"amount0Out","type":"uint256"},{"indexed":False,"internalType":"uint256","name":"amount1Out","type":"uint256"},{"indexed":True,"internalType":"address","name":"to","type":"address"}],"name":"Swap","type":"event"},{"anonymous":False,"inputs":[{"indexed":False,"internalType":"uint112","name":"reserve0","type":"uint112"},{"indexed":False,"internalType":"uint112","name":"reserve1","type":"uint112"}],"name":"Sync","type":"event"},{"anonymous":False,"inputs":[{"indexed":True,"internalType":"address","name":"from","type":"address"},{"indexed":True,"internalType":"address","name":"to","type":"address"},{"indexed":False,"internalType":"uint256","name":"value","type":"uint256"}],"name":"Transfer","type":"event"},{"constant":True,"inputs":[],"name":"DOMAIN_SEPARATOR","outputs":[{"internalType":"bytes32","name":"","type":"bytes32"}],"payable":False,"stateMutability":"view","type":"function"},{"constant":True,"inputs":[],"name":"MINIMUM_LIQUIDITY","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"payable":False,"stateMutability":"view","type":"function"},{"constant":True,"inputs":[],"name":"PERMIT_TYPEHASH","outputs":[{"internalType":"bytes32","name":"","type":"bytes32"}],"payable":False,"stateMutability":"view","type":"function"},{"constant":True,"inputs":[{"internalType":"address","name":"","type":"address"},{"internalType":"address","name":"","type":"address"}],"name":"allowance","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"payable":False,"stateMutability":"view","type":"function"},{"constant":False,"inputs":[{"internalType":"address","name":"spender","type":"address"},{"internalType":"uint256","name":"value","type":"uint256"}],"name":"approve","outputs":[{"internalType":"bool","name":"","type":"bool"}],"payable":False,"stateMutability":"nonpayable","type":"function"},{"constant":True,"inputs":[{"internalType":"address","name":"","type":"address"}],"name":"balanceOf","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"payable":False,"stateMutability":"view","type":"function"},{"constant":False,"inputs":[{"internalType":"address","name":"to","type":"address"}],"name":"burn","outputs":[{"internalType":"uint256","name":"amount0","type":"uint256"},{"internalType":"uint256","name":"amount1","type":"uint256"}],"payable":False,"stateMutability":"nonpayable","type":"function"},{"constant":True,"inputs":[],"name":"decimals","outputs":[{"internalType":"uint8","name":"","type":"uint8"}],"payable":False,"stateMutability":"view","type":"function"},{"constant":True,"inputs":[],"name":"factory","outputs":[{"internalType":"address","name":"","type":"address"}],"payable":False,"stateMutability":"view","type":"function"},{"constant":True,"inputs":[],"name":"getReserves","outputs":[{"internalType":"uint112","name":"_reserve0","type":"uint112"},{"internalType":"uint112","name":"_reserve1","type":"uint112"},{"internalType":"uint32","name":"_blockTimestampLast","type":"uint32"}],"payable":False,"stateMutability":"view","type":"function"},{"constant":False,"inputs":[{"internalType":"address","name":"_token0","type":"address"},{"internalType":"address","name":"_token1","type":"address"}],"name":"initialize","outputs":[],"payable":False,"stateMutability":"nonpayable","type":"function"},{"constant":True,"inputs":[],"name":"kLast","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"payable":False,"stateMutability":"view","type":"function"},{"constant":False,"inputs":[{"internalType":"address","name":"to","type":"address"}],"name":"mint","outputs":[{"internalType":"uint256","name":"liquidity","type":"uint256"}],"payable":False,"stateMutability":"nonpayable","type":"function"},{"constant":True,"inputs":[],"name":"name","outputs":[{"internalType":"string","name":"","type":"string"}],"payable":False,"stateMutability":"view","type":"function"},{"constant":True,"inputs":[{"internalType":"address","name":"","type":"address"}],"name":"nonces","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"payable":False,"stateMutability":"view","type":"function"},{"constant":False,"inputs":[{"internalType":"address","name":"owner","type":"address"},{"internalType":"address","name":"spender","type":"address"},{"internalType":"uint256","name":"value","type":"uint256"},{"internalType":"uint256","name":"deadline","type":"uint256"},{"internalType":"uint8","name":"v","type":"uint8"},{"internalType":"bytes32","name":"r","type":"bytes32"},{"internalType":"bytes32","name":"s","type":"bytes32"}],"name":"permit","outputs":[],"payable":False,"stateMutability":"nonpayable","type":"function"},{"constant":True,"inputs":[],"name":"price0CumulativeLast","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"payable":False,"stateMutability":"view","type":"function"},{"constant":True,"inputs":[],"name":"price1CumulativeLast","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"payable":False,"stateMutability":"view","type":"function"},{"constant":False,"inputs":[{"internalType":"address","name":"to","type":"address"}],"name":"skim","outputs":[],"payable":False,"stateMutability":"nonpayable","type":"function"},{"constant":False,"inputs":[{"internalType":"uint256","name":"amount0Out","type":"uint256"},{"internalType":"uint256","name":"amount1Out","type":"uint256"},{"internalType":"address","name":"to","type":"address"},{"internalType":"bytes","name":"data","type":"bytes"}],"name":"swap","outputs":[],"payable":False,"stateMutability":"nonpayable","type":"function"},{"constant":True,"inputs":[],"name":"symbol","outputs":[{"internalType":"string","name":"","type":"string"}],"payable":False,"stateMutability":"view","type":"function"},{"constant":False,"inputs":[],"name":"sync","outputs":[],"payable":False,"stateMutability":"nonpayable","type":"function"},{"constant":True,"inputs":[],"name":"token0","outputs":[{"internalType":"address","name":"","type":"address"}],"payable":False,"stateMutability":"view","type":"function"},{"constant":True,"inputs":[],"name":"token1","outputs":[{"internalType":"address","name":"","type":"address"}],"payable":False,"stateMutability":"view","type":"function"},{"constant":True,"inputs":[],"name":"totalSupply","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"payable":False,"stateMutability":"view","type":"function"},{"constant":False,"inputs":[{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"value","type":"uint256"}],"name":"transfer","outputs":[{"internalType":"bool","name":"","type":"bool"}],"payable":False,"stateMutability":"nonpayable","type":"function"},{"constant":False,"inputs":[{"internalType":"address","name":"from","type":"address"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"value","type":"uint256"}],"name":"transferFrom","outputs":[{"internalType":"bool","name":"","type":"bool"}],"payable":False,"stateMutability":"nonpayable","type":"function"}]
V3_POOL_ABI = [{"inputs":[],"stateMutability":"nonpayable","type":"constructor"},{"anonymous":False,"inputs":[{"indexed":True,"internalType":"address","name":"owner","type":"address"},{"indexed":True,"internalType":"int24","name":"tickLower","type":"int24"},{"indexed":True,"internalType":"int24","name":"tickUpper","type":"int24"},{"indexed":False,"internalType":"uint128","name":"amount","type":"uint128"},{"indexed":False,"internalType":"uint256","name":"amount0","type":"uint256"},{"indexed":False,"internalType":"uint256","name":"amount1","type":"uint256"}],"name":"Burn","type":"event"},{"anonymous":False,"inputs":[{"indexed":True,"internalType":"address","name":"owner","type":"address"},{"indexed":False,"internalType":"address","name":"recipient","type":"address"},{"indexed":True,"internalType":"int24","name":"tickLower","type":"int24"},{"indexed":True,"internalType":"int24","name":"tickUpper","type":"int24"},{"indexed":False,"internalType":"uint128","name":"amount0","type":"uint128"},{"indexed":False,"internalType":"uint128","name":"amount1","type":"uint128"}],"name":"Collect","type":"event"},{"anonymous":False,"inputs":[{"indexed":True,"internalType":"address","name":"sender","type":"address"},{"indexed":True,"internalType":"address","name":"recipient","type":"address"},{"indexed":False,"internalType":"uint128","name":"amount0","type":"uint128"},{"indexed":False,"internalType":"uint128","name":"amount1","type":"uint128"}],"name":"CollectProtocol","type":"event"},{"anonymous":False,"inputs":[{"indexed":True,"internalType":"address","name":"sender","type":"address"},{"indexed":True,"internalType":"address","name":"recipient","type":"address"},{"indexed":False,"internalType":"uint256","name":"amount0","type":"uint256"},{"indexed":False,"internalType":"uint256","name":"amount1","type":"uint256"},{"indexed":False,"internalType":"uint256","name":"paid0","type":"uint256"},{"indexed":False,"internalType":"uint256","name":"paid1","type":"uint256"}],"name":"Flash","type":"event"},{"anonymous":False,"inputs":[{"indexed":False,"internalType":"uint16","name":"observationCardinalityNextOld","type":"uint16"},{"indexed":False,"internalType":"uint16","name":"observationCardinalityNextNew","type":"uint16"}],"name":"IncreaseObservationCardinalityNext","type":"event"},{"anonymous":False,"inputs":[{"indexed":False,"internalType":"uint160","name":"sqrtPriceX96","type":"uint160"},{"indexed":False,"internalType":"int24","name":"tick","type":"int24"}],"name":"Initialize","type":"event"},{"anonymous":False,"inputs":[{"indexed":False,"internalType":"address","name":"sender","type":"address"},{"indexed":True,"internalType":"address","name":"owner","type":"address"},{"indexed":True,"internalType":"int24","name":"tickLower","type":"int24"},{"indexed":True,"internalType":"int24","name":"tickUpper","type":"int24"},{"indexed":False,"internalType":"uint128","name":"amount","type":"uint128"},{"indexed":False,"internalType":"uint256","name":"amount0","type":"uint256"},{"indexed":False,"internalType":"uint256","name":"amount1","type":"uint256"}],"name":"Mint","type":"event"},{"anonymous":False,"inputs":[{"indexed":False,"internalType":"uint32","name":"feeProtocol0Old","type":"uint32"},{"indexed":False,"internalType":"uint32","name":"feeProtocol1Old","type":"uint32"},{"indexed":False,"internalType":"uint32","name":"feeProtocol0New","type":"uint32"},{"indexed":False,"internalType":"uint32","name":"feeProtocol1New","type":"uint32"}],"name":"SetFeeProtocol","type":"event"},{"anonymous":False,"inputs":[{"indexed":False,"internalType":"address","name":"addr","type":"address"}],"name":"SetLmPoolEvent","type":"event"},{"anonymous":False,"inputs":[{"indexed":True,"internalType":"address","name":"sender","type":"address"},{"indexed":True,"internalType":"address","name":"recipient","type":"address"},{"indexed":False,"internalType":"int256","name":"amount0","type":"int256"},{"indexed":False,"internalType":"int256","name":"amount1","type":"int256"},{"indexed":False,"internalType":"uint160","name":"sqrtPriceX96","type":"uint160"},{"indexed":False,"internalType":"uint128","name":"liquidity","type":"uint128"},{"indexed":False,"internalType":"int24","name":"tick","type":"int24"}],"name":"Swap","type":"event"},{"inputs":[{"internalType":"int24","name":"tickLower","type":"int24"},{"internalType":"int24","name":"tickUpper","type":"int24"},{"internalType":"uint128","name":"amount","type":"uint128"}],"name":"burn","outputs":[{"internalType":"uint256","name":"amount0","type":"uint256"},{"internalType":"uint256","name":"amount1","type":"uint256"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"recipient","type":"address"},{"internalType":"int24","name":"tickLower","type":"int24"},{"internalType":"int24","name":"tickUpper","type":"int24"},{"internalType":"uint128","name":"amount0Requested","type":"uint128"},{"internalType":"uint128","name":"amount1Requested","type":"uint128"}],"name":"collect","outputs":[{"internalType":"uint128","name":"amount0","type":"uint128"},{"internalType":"uint128","name":"amount1","type":"uint128"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"recipient","type":"address"},{"internalType":"uint128","name":"amount0Requested","type":"uint128"},{"internalType":"uint128","name":"amount1Requested","type":"uint128"}],"name":"collectProtocol","outputs":[{"internalType":"uint128","name":"amount0","type":"uint128"},{"internalType":"uint128","name":"amount1","type":"uint128"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[],"name":"factory","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"fee","outputs":[{"internalType":"uint24","name":"","type":"uint24"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"feeGrowthGlobal0X128","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"feeGrowthGlobal1X128","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"recipient","type":"address"},{"internalType":"uint256","name":"amount0","type":"uint256"},{"internalType":"uint256","name":"amount1","type":"uint256"},{"internalType":"bytes","name":"data","type":"bytes"}],"name":"flash","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint16","name":"observationCardinalityNext","type":"uint16"}],"name":"increaseObservationCardinalityNext","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint160","name":"sqrtPriceX96","type":"uint160"}],"name":"initialize","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[],"name":"liquidity","outputs":[{"internalType":"uint128","name":"","type":"uint128"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"lmPool","outputs":[{"internalType":"contract IPancakeV3LmPool","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"maxLiquidityPerTick","outputs":[{"internalType":"uint128","name":"","type":"uint128"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"recipient","type":"address"},{"internalType":"int24","name":"tickLower","type":"int24"},{"internalType":"int24","name":"tickUpper","type":"int24"},{"internalType":"uint128","name":"amount","type":"uint128"},{"internalType":"bytes","name":"data","type":"bytes"}],"name":"mint","outputs":[{"internalType":"uint256","name":"amount0","type":"uint256"},{"internalType":"uint256","name":"amount1","type":"uint256"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint256","name":"","type":"uint256"}],"name":"observations","outputs":[{"internalType":"uint32","name":"blockTimestamp","type":"uint32"},{"internalType":"int56","name":"tickCumulative","type":"int56"},{"internalType":"uint160","name":"secondsPerLiquidityCumulativeX128","type":"uint160"},{"internalType":"bool","name":"initialized","type":"bool"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"uint32[]","name":"secondsAgos","type":"uint32[]"}],"name":"observe","outputs":[{"internalType":"int56[]","name":"tickCumulatives","type":"int56[]"},{"internalType":"uint160[]","name":"secondsPerLiquidityCumulativeX128s","type":"uint160[]"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"bytes32","name":"","type":"bytes32"}],"name":"positions","outputs":[{"internalType":"uint128","name":"liquidity","type":"uint128"},{"internalType":"uint256","name":"feeGrowthInside0LastX128","type":"uint256"},{"internalType":"uint256","name":"feeGrowthInside1LastX128","type":"uint256"},{"internalType":"uint128","name":"tokensOwed0","type":"uint128"},{"internalType":"uint128","name":"tokensOwed1","type":"uint128"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"protocolFees","outputs":[{"internalType":"uint128","name":"token0","type":"uint128"},{"internalType":"uint128","name":"token1","type":"uint128"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"uint32","name":"feeProtocol0","type":"uint32"},{"internalType":"uint32","name":"feeProtocol1","type":"uint32"}],"name":"setFeeProtocol","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"_lmPool","type":"address"}],"name":"setLmPool","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[],"name":"slot0","outputs":[{"internalType":"uint160","name":"sqrtPriceX96","type":"uint160"},{"internalType":"int24","name":"tick","type":"int24"},{"internalType":"uint16","name":"observationIndex","type":"uint16"},{"internalType":"uint16","name":"observationCardinality","type":"uint16"},{"internalType":"uint16","name":"observationCardinalityNext","type":"uint16"},{"internalType":"uint32","name":"feeProtocol","type":"uint32"},{"internalType":"bool","name":"unlocked","type":"bool"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"int24","name":"tickLower","type":"int24"},{"internalType":"int24","name":"tickUpper","type":"int24"}],"name":"snapshotCumulativesInside","outputs":[{"internalType":"int56","name":"tickCumulativeInside","type":"int56"},{"internalType":"uint160","name":"secondsPerLiquidityInsideX128","type":"uint160"},{"internalType":"uint32","name":"secondsInside","type":"uint32"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"recipient","type":"address"},{"internalType":"bool","name":"zeroForOne","type":"bool"},{"internalType":"int256","name":"amountSpecified","type":"int256"},{"internalType":"uint160","name":"sqrtPriceLimitX96","type":"uint160"},{"internalType":"bytes","name":"data","type":"bytes"}],"name":"swap","outputs":[{"internalType":"int256","name":"amount0","type":"int256"},{"internalType":"int256","name":"amount1","type":"int256"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"int16","name":"","type":"int16"}],"name":"tickBitmap","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"tickSpacing","outputs":[{"internalType":"int24","name":"","type":"int24"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"int24","name":"","type":"int24"}],"name":"ticks","outputs":[{"internalType":"uint128","name":"liquidityGross","type":"uint128"},{"internalType":"int128","name":"liquidityNet","type":"int128"},{"internalType":"uint256","name":"feeGrowthOutside0X128","type":"uint256"},{"internalType":"uint256","name":"feeGrowthOutside1X128","type":"uint256"},{"internalType":"int56","name":"tickCumulativeOutside","type":"int56"},{"internalType":"uint160","name":"secondsPerLiquidityOutsideX128","type":"uint160"},{"internalType":"uint32","name":"secondsOutside","type":"uint32"},{"internalType":"bool","name":"initialized","type":"bool"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"token0","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"token1","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"}]
V2_FACTORY_ABI = [{"inputs":[{"internalType":"address","name":"_feeToSetter","type":"address"}],"payable":False,"stateMutability":"nonpayable","type":"constructor"},{"anonymous":False,"inputs":[{"indexed":True,"internalType":"address","name":"token0","type":"address"},{"indexed":True,"internalType":"address","name":"token1","type":"address"},{"indexed":False,"internalType":"address","name":"pair","type":"address"},{"indexed":False,"internalType":"uint256","name":"","type":"uint256"}],"name":"PairCreated","type":"event"},{"constant":True,"inputs":[],"name":"INIT_CODE_PAIR_HASH","outputs":[{"internalType":"bytes32","name":"","type":"bytes32"}],"payable":False,"stateMutability":"view","type":"function"},{"constant":True,"inputs":[{"internalType":"uint256","name":"","type":"uint256"}],"name":"allPairs","outputs":[{"internalType":"address","name":"","type":"address"}],"payable":False,"stateMutability":"view","type":"function"},{"constant":True,"inputs":[],"name":"allPairsLength","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"payable":False,"stateMutability":"view","type":"function"},{"constant":False,"inputs":[{"internalType":"address","name":"tokenA","type":"address"},{"internalType":"address","name":"tokenB","type":"address"}],"name":"createPair","outputs":[{"internalType":"address","name":"pair","type":"address"}],"payable":False,"stateMutability":"nonpayable","type":"function"},{"constant":True,"inputs":[],"name":"feeTo","outputs":[{"internalType":"address","name":"","type":"address"}],"payable":False,"stateMutability":"view","type":"function"},{"constant":True,"inputs":[],"name":"feeToSetter","outputs":[{"internalType":"address","name":"","type":"address"}],"payable":False,"stateMutability":"view","type":"function"},{"constant":True,"inputs":[{"internalType":"address","name":"","type":"address"},{"internalType":"address","name":"","type":"address"}],"name":"getPair","outputs":[{"internalType":"address","name":"","type":"address"}],"payable":False,"stateMutability":"view","type":"function"},{"constant":False,"inputs":[{"internalType":"address","name":"_feeTo","type":"address"}],"name":"setFeeTo","outputs":[],"payable":False,"stateMutability":"nonpayable","type":"function"},{"constant":False,"inputs":[{"internalType":"address","name":"_feeToSetter","type":"address"}],"name":"setFeeToSetter","outputs":[],"payable":False,"stateMutability":"nonpayable","type":"function"}]
V3_FACTORY_ABI = [{"inputs":[{"internalType":"address","name":"_poolDeployer","type":"address"}],"stateMutability":"nonpayable","type":"constructor"},{"anonymous":False,"inputs":[{"indexed":True,"internalType":"uint24","name":"fee","type":"uint24"},{"indexed":True,"internalType":"int24","name":"tickSpacing","type":"int24"}],"name":"FeeAmountEnabled","type":"event"},{"anonymous":False,"inputs":[{"indexed":True,"internalType":"uint24","name":"fee","type":"uint24"},{"indexed":False,"internalType":"bool","name":"whitelistRequested","type":"bool"},{"indexed":False,"internalType":"bool","name":"enabled","type":"bool"}],"name":"FeeAmountExtraInfoUpdated","type":"event"},{"anonymous":False,"inputs":[{"indexed":True,"internalType":"address","name":"oldOwner","type":"address"},{"indexed":True,"internalType":"address","name":"newOwner","type":"address"}],"name":"OwnerChanged","type":"event"},{"anonymous":False,"inputs":[{"indexed":True,"internalType":"address","name":"token0","type":"address"},{"indexed":True,"internalType":"address","name":"token1","type":"address"},{"indexed":True,"internalType":"uint24","name":"fee","type":"uint24"},{"indexed":False,"internalType":"int24","name":"tickSpacing","type":"int24"},{"indexed":False,"internalType":"address","name":"pool","type":"address"}],"name":"PoolCreated","type":"event"},{"anonymous":False,"inputs":[{"indexed":True,"internalType":"address","name":"lmPoolDeployer","type":"address"}],"name":"SetLmPoolDeployer","type":"event"},{"anonymous":False,"inputs":[{"indexed":True,"internalType":"address","name":"user","type":"address"},{"indexed":False,"internalType":"bool","name":"verified","type":"bool"}],"name":"WhiteListAdded","type":"event"},{"inputs":[{"internalType":"address","name":"pool","type":"address"},{"internalType":"address","name":"recipient","type":"address"},{"internalType":"uint128","name":"amount0Requested","type":"uint128"},{"internalType":"uint128","name":"amount1Requested","type":"uint128"}],"name":"collectProtocol","outputs":[{"internalType":"uint128","name":"amount0","type":"uint128"},{"internalType":"uint128","name":"amount1","type":"uint128"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"tokenA","type":"address"},{"internalType":"address","name":"tokenB","type":"address"},{"internalType":"uint24","name":"fee","type":"uint24"}],"name":"createPool","outputs":[{"internalType":"address","name":"pool","type":"address"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint24","name":"fee","type":"uint24"},{"internalType":"int24","name":"tickSpacing","type":"int24"}],"name":"enableFeeAmount","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint24","name":"","type":"uint24"}],"name":"feeAmountTickSpacing","outputs":[{"internalType":"int24","name":"","type":"int24"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"uint24","name":"","type":"uint24"}],"name":"feeAmountTickSpacingExtraInfo","outputs":[{"internalType":"bool","name":"whitelistRequested","type":"bool"},{"internalType":"bool","name":"enabled","type":"bool"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"","type":"address"},{"internalType":"address","name":"","type":"address"},{"internalType":"uint24","name":"","type":"uint24"}],"name":"getPool","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"lmPoolDeployer","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"owner","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"poolDeployer","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"uint24","name":"fee","type":"uint24"},{"internalType":"bool","name":"whitelistRequested","type":"bool"},{"internalType":"bool","name":"enabled","type":"bool"}],"name":"setFeeAmountExtraInfo","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"pool","type":"address"},{"internalType":"uint32","name":"feeProtocol0","type":"uint32"},{"internalType":"uint32","name":"feeProtocol1","type":"uint32"}],"name":"setFeeProtocol","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"pool","type":"address"},{"internalType":"address","name":"lmPool","type":"address"}],"name":"setLmPool","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"_lmPoolDeployer","type":"address"}],"name":"setLmPoolDeployer","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"_owner","type":"address"}],"name":"setOwner","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"user","type":"address"},{"internalType":"bool","name":"verified","type":"bool"}],"name":"setWhiteListAddress","outputs":[],"stateMutability":"nonpayable","type":"function"}]
FLASH_LOAN_ABI = [
	{
		"inputs": [
			{
				"internalType": "address",
				"name": "_wbnb",
				"type": "address"
			},
			{
				"internalType": "address",
				"name": "_usdt",
				"type": "address"
			}
		],
		"stateMutability": "nonpayable",
		"type": "constructor"
	},
	{
		"anonymous": False,
		"inputs": [
			{
				"indexed": False,
				"internalType": "uint256",
				"name": "profit",
				"type": "uint256"
			},
			{
				"indexed": False,
				"internalType": "uint256",
				"name": "timestamp",
				"type": "uint256"
			}
		],
		"name": "ArbitrageExecuted",
		"type": "event"
	},
	{
		"anonymous": False,
		"inputs": [
			{
				"indexed": False,
				"internalType": "string",
				"name": "message",
				"type": "string"
			},
			{
				"indexed": False,
				"internalType": "address",
				"name": "addr",
				"type": "address"
			}
		],
		"name": "DebugAddress",
		"type": "event"
	},
	{
		"anonymous": False,
		"inputs": [
			{
				"indexed": False,
				"internalType": "string",
				"name": "message",
				"type": "string"
			},
			{
				"indexed": False,
				"internalType": "uint256",
				"name": "value",
				"type": "uint256"
			}
		],
		"name": "DebugLog",
		"type": "event"
	},
	{
		"inputs": [
			{
				"internalType": "address",
				"name": "v2Pool",
				"type": "address"
			},
			{
				"internalType": "address",
				"name": "v3SwapPool",
				"type": "address"
			},
			{
				"internalType": "address",
				"name": "v3FlashPool",
				"type": "address"
			},
			{
				"internalType": "address",
				"name": "tokenToBorrow",
				"type": "address"
			},
			{
				"internalType": "uint256",
				"name": "amountToBorrow",
				"type": "uint256"
			},
			{
				"internalType": "uint256",
				"name": "minOutput",
				"type": "uint256"
			}
		],
		"name": "executeFlashLoan",
		"outputs": [],
		"stateMutability": "nonpayable",
		"type": "function"
	},
	{
		"inputs": [
			{
				"internalType": "uint256",
				"name": "fee0",
				"type": "uint256"
			},
			{
				"internalType": "uint256",
				"name": "fee1",
				"type": "uint256"
			},
			{
				"internalType": "bytes",
				"name": "data",
				"type": "bytes"
			}
		],
		"name": "pancakeV3FlashCallback",
		"outputs": [],
		"stateMutability": "nonpayable",
		"type": "function"
	},
	{
		"inputs": [
			{
				"internalType": "int256",
				"name": "amount0Delta",
				"type": "int256"
			},
			{
				"internalType": "int256",
				"name": "amount1Delta",
				"type": "int256"
			},
			{
				"internalType": "bytes",
				"name": "",
				"type": "bytes"
			}
		],
		"name": "pancakeV3SwapCallback",
		"outputs": [],
		"stateMutability": "nonpayable",
		"type": "function"
	},
	{
		"inputs": [
			{
				"internalType": "address",
				"name": "token",
				"type": "address"
			},
			{
				"internalType": "uint256",
				"name": "amount",
				"type": "uint256"
			}
		],
		"name": "recoverTokens",
		"outputs": [],
		"stateMutability": "nonpayable",
		"type": "function"
	},
	{
		"inputs": [],
		"name": "owner",
		"outputs": [
			{
				"internalType": "address",
				"name": "",
				"type": "address"
			}
		],
		"stateMutability": "view",
		"type": "function"
	},
	{
		"inputs": [],
		"name": "USDT",
		"outputs": [
			{
				"internalType": "address",
				"name": "",
				"type": "address"
			}
		],
		"stateMutability": "view",
		"type": "function"
	},
	{
		"inputs": [],
		"name": "WBNB",
		"outputs": [
			{
				"internalType": "address",
				"name": "",
				"type": "address"
			}
		],
		"stateMutability": "view",
		"type": "function"
	}
]  # 🔥 YOU WILL PASTE THE NEW ABI HERE WITH 6 PARAMETERS

# =========================================================================
# 3. HELPER FUNCTIONS (BACK TO BASICS - NO GRAPHQL)
# =========================================================================

def calculate_v3_price(sqrt_price_x96):
    """Calculate WBNB price in USDT from V3 sqrtPriceX96"""
    if sqrt_price_x96 is None:
        return 0.0
    
    price_x192 = Decimal(sqrt_price_x96) ** 2
    divisor = Decimal(2) ** Decimal(192)
    P_raw = price_x192 / divisor
    
    if P_raw == 0:
        return 0.0
    
    USDT_per_WBNB = Decimal('1') / P_raw
    return float(USDT_per_WBNB)

def calculate_v2_amount_out(amount_in_wei, reserve_in_wei, reserve_out_wei):
    """Calculate V2 swap output with 0.25% fee"""
    amount_in_with_fee = amount_in_wei * 9975
    numerator = amount_in_with_fee * reserve_out_wei
    denominator = reserve_in_wei * 10000 + amount_in_with_fee
    
    if denominator == 0:
        return 0
    
    return numerator // denominator

def check_pool_liquidity(usdt_reserve, wbnb_reserve, current_price, v3_liquidity_usd=None):
    """Check both V2 and V3 pool liquidity"""
    
    # V2 Liquidity check
    usdt_reserve_dec = Decimal(usdt_reserve) / USDT_POWER_DEC
    wbnb_reserve_usd = (Decimal(wbnb_reserve) / WBNB_POWER_DEC) * Decimal(current_price)
    v2_liquidity_usd = float(usdt_reserve_dec + wbnb_reserve_usd)
    
    # V3 Liquidity check
    v3_ok = True
    if v3_liquidity_usd is not None:
        v3_ok = v3_liquidity_usd >= MIN_LIQUIDITY_USD
    
    v2_ok = v2_liquidity_usd >= MIN_LIQUIDITY_USD
    
    # BOTH must pass
    both_ok = v2_ok and v3_ok
   
    return both_ok, v2_liquidity_usd, v3_liquidity_usd

def predict_hidden_slippage(trade_size_usd, usdt_reserve, wbnb_reserve, v2_price, is_path1=True):
    """Predict actual slippage BEFORE executing"""
    trade_size_dec = Decimal(trade_size_usd)
    usdt_reserve_dec = Decimal(usdt_reserve) / USDT_POWER_DEC
    wbnb_reserve_dec = Decimal(wbnb_reserve) / WBNB_POWER_DEC
    v2_price_dec = Decimal(v2_price)
    
    if is_path1:
        usdt_in_wei = int(trade_size_dec * USDT_POWER_DEC)
        wbnb_out_wei = calculate_v2_amount_out(usdt_in_wei, usdt_reserve, wbnb_reserve)
        
        if wbnb_out_wei == 0:
            return 0.0
        
        wbnb_out_norm = Decimal(wbnb_out_wei) / WBNB_POWER_DEC
        expected_wbnb = trade_size_dec / v2_price_dec
        slippage_wbnb = expected_wbnb - wbnb_out_norm
        slippage_usd = float(slippage_wbnb * v2_price_dec)
        
    else:
        wbnb_borrow_norm = trade_size_dec / v2_price_dec
        usdt_from_v3 = wbnb_borrow_norm * v2_price_dec * Decimal('0.9995')  # 🔥 UPDATED: 0.05% flash fee
        
        usdt_in_wei = int(usdt_from_v3 * USDT_POWER_DEC)
        wbnb_out_wei = calculate_v2_amount_out(usdt_in_wei, usdt_reserve, wbnb_reserve)
        
        if wbnb_out_wei == 0:
            return 0.0
        
        wbnb_out_norm = Decimal(wbnb_out_wei) / WBNB_POWER_DEC
        expected_wbnb = usdt_from_v3 / v2_price_dec
        slippage_wbnb = expected_wbnb - wbnb_out_norm
        slippage_usd = float(slippage_wbnb * v2_price_dec)
    
    return slippage_usd

def calculate_trade_size_for_target_slippage(usdt_reserve, wbnb_reserve, target_slippage_percent):
    """Calculate optimal trade size for target slippage"""
    usdt_reserve_dec = Decimal(usdt_reserve) / USDT_POWER_DEC
    wbnb_reserve_dec = Decimal(wbnb_reserve) / WBNB_POWER_DEC
    v2_price = usdt_reserve_dec / wbnb_reserve_dec
    target_slip_dec = Decimal(target_slippage_percent)
    
    test_sizes = [
        Decimal('25000'),
        Decimal('20000'),
        Decimal('15000'),
        Decimal('10000'),
        Decimal('5000'),
        Decimal('2500'),
        Decimal('1000'),
        Decimal('500')
    ]
    
    for test_size in test_sizes:
        usdt_in_wei = int(test_size * USDT_POWER_DEC)
        wbnb_out_wei = calculate_v2_amount_out(usdt_in_wei, usdt_reserve, wbnb_reserve)
        
        if wbnb_out_wei == 0:
            continue
            
        wbnb_out_norm = Decimal(wbnb_out_wei) / WBNB_POWER_DEC
        expected_wbnb = test_size / v2_price
        
        if expected_wbnb == 0:
            continue
            
        actual_slip = abs((expected_wbnb - wbnb_out_norm) / expected_wbnb) * Decimal('100')
        
        if actual_slip <= target_slip_dec:
            return float(test_size)
    
    return 500.0
    
def get_v3_pool_data(web3):
    """Find and validate V3 pool"""
    factory_contract = web3.eth.contract(
        address=V3_FACTORY_ADDRESS,
        abi=V3_FACTORY_ABI
    )
    
    for fee in FEE_TIERS:
        try:
            pool_address = factory_contract.functions.getPool(
                WBNB_ADDRESS, USDT_ADDRESS, fee
            ).call()
            
            if pool_address != '0x0000000000000000000000000000000000000000':
                fee_percent = fee / 1_000_000
                cprint(f"✅ V3 Pool: {pool_address} @ {fee_percent*100:.2f}% Fee", "green")
                return pool_address, fee_percent
        except:
            pass
    
    cprint("!! ERROR: No V3 pools found !!", "red", attrs=["bold"])
    return None, 0.0

def estimate_gas_cost(w3_sync, bnb_price_usd):
    """Estimate gas cost in USD"""
    try:
        gas_price_wei = w3_sync.eth.gas_price
        gas_limit = 4000000
        gas_cost_bnb = (gas_price_wei * gas_limit) / 1e18
        gas_cost_usd = gas_cost_bnb * bnb_price_usd
        return gas_cost_usd
    except:
        return 1.5
        
# =========================================================================
# 4. CORE ARBITRAGE LOGIC (SILENT MODE)
# =========================================================================

async def handle_event(event, event_type, w3_sync, flash_contract_sync):
    """
    Process V2 Sync events and execute profitable arbitrage
    SILENT MODE: Only prints when gap >= MIN_GAP_PERCENT
    """
    global V2_PRICE, last_v3_price, last_printed_gap, last_gap_timestamp
    
    FLASH_LOAN_FEE_RATE = Decimal('0.0005')  # 🔥 UPDATED: 0.05%
    V3_SWAP_RATE_DEC = Decimal('1') - Decimal(FLASH_LOAN_FEE)
    V2_SWAP_RATE_DEC = Decimal('0.9975')

    if last_v3_price is None or event_type != 'V2':
        return
    
    try:
        reserve0_raw = event['args']['reserve0']
        reserve1_raw = event['args']['reserve1']
        
        if reserve0_raw == 0 or reserve1_raw == 0:
            return
        
        v2_pool_contract = w3_sync.eth.contract(address=V2_PAIR_ADDRESS, abi=V2_PAIR_ABI)
        v2_token0 = v2_pool_contract.functions.token0().call()
        v3_liquidity_usd = None
        
        if v2_token0.lower() == WBNB_ADDRESS.lower():
            wbnb_reserve = reserve0_raw
            usdt_reserve = reserve1_raw
        else:
            wbnb_reserve = reserve1_raw
            usdt_reserve = reserve0_raw
            
        # Fetch real V3 pool liquidity
        try:
             v3_pool_contract = w3_sync.eth.contract(
                     address=V3_SWAP_POOL,
                     abi=V3_POOL_ABI
             )
             v3_liq_raw = v3_pool_contract.functions.liquidity().call()
             v3_liquidity_usd = float(
                     (Decimal(v3_liq_raw) / WBNB_POWER_DEC) * Decimal(str(V2_PRICE))
              )
        except:
              v3_liquidity_usd = None
        wbnb_reserve_norm = Decimal(wbnb_reserve) / WBNB_POWER_DEC
        usdt_reserve_norm = Decimal(usdt_reserve) / USDT_POWER_DEC
        
        if wbnb_reserve_norm == 0:
            return
        
        v2_price_dec = usdt_reserve_norm / wbnb_reserve_norm
        V2_PRICE = float(v2_price_dec)

        if V2_PRICE < 100 or V2_PRICE > 10000:
            return

        liquidity_ok, v2_liquidity, v3_liquidity = check_pool_liquidity(
              usdt_reserve, wbnb_reserve, V2_PRICE, v3_liquidity_usd
)
        
        if not liquidity_ok:
            return

        v3_price_dec = Decimal(last_v3_price)
        gap_percent_dec = (abs(v2_price_dec - v3_price_dec) / v3_price_dec) * Decimal('100')
        gap_percent = float(gap_percent_dec)
        
        if gap_percent < MIN_GAP_PERCENT:
            return
        
        current_time = datetime.now()
        
        if last_printed_gap is not None:
            gap_change = abs(gap_percent - last_printed_gap)
            time_diff = (current_time - last_gap_timestamp).total_seconds()
            
            if gap_change < 0.05 and time_diff < 30:
                return
        
        last_printed_gap = gap_percent
        last_gap_timestamp = current_time
        
        max_safe = calculate_trade_size_for_target_slippage(
            usdt_reserve, 
            wbnb_reserve, 
            MAX_SLIPPAGE_PERCENT
        )
        
       # Get V3 based safe size (V3 pool is smaller = more slippage)
        v3_safe_size = calculate_trade_size_for_target_slippage(
                int(v3_liquidity_usd * USDT_POWER_DEC) if        v3_liquidity_usd else int(1e26),
                int((v3_liquidity_usd / float(v2_price_dec)) * WBNB_POWER_DEC) if v3_liquidity_usd else int(1e26),
                MAX_SLIPPAGE_PERCENT
         )

        # ✅ Use the smaller - most conservative safe size
        max_safe = min(max_safe, v3_safe_size)
        trade_size_dec = Decimal(max_safe)
        trade_size = float(trade_size_dec)
        
        is_path1 = V2_PRICE > last_v3_price
        
        predicted_slippage_usd = predict_hidden_slippage(
            trade_size, 
            usdt_reserve, 
            wbnb_reserve, 
            V2_PRICE,
            is_path1
        )
        
        v2_fee_est = trade_size * 0.0025
        v3_fee_est = trade_size * 0.0001  # V3 swap fee
        flash_fee_est = trade_size * 0.0005  # 🔥 UPDATED: 0.05% flash fee
        total_fees = v2_fee_est + v3_fee_est + flash_fee_est
        
        gas_cost_usd = estimate_gas_cost(w3_sync, V2_PRICE)
        gap_revenue = trade_size * gap_percent / 100
        expected_profit = gap_revenue - total_fees - predicted_slippage_usd - gas_cost_usd
        
        if expected_profit < (MIN_PROFIT_USD * PROFIT_SAFETY_MARGIN):
            return
        
        if is_path1:
            direction = "📈 BUY V3 → SELL V2"

            usdt_borrow_wei = int(trade_size_dec * USDT_POWER_DEC)

            # ✅ CORRECT: V3 swap USDT → WBNB (buy cheap on V3)
            wbnb_from_v3 = (trade_size_dec / v3_price_dec) * Decimal('0.9999')  # After V3 0.01% fee
            wbnb_from_v3_wei = int(wbnb_from_v3 * WBNB_POWER_DEC)

            # ✅ CORRECT: V2 swap WBNB → USDT (sell expensive on V2)
            usdt_back_wei = calculate_v2_amount_out(wbnb_from_v3_wei, wbnb_reserve, usdt_reserve)
            usdt_back_norm = Decimal(usdt_back_wei) / USDT_POWER_DEC

            expected_usdt = wbnb_from_v3 * v2_price_dec
            actual_usdt = usdt_back_norm
            slippage_dec = ((expected_usdt - actual_usdt) / expected_usdt) * Decimal('100') if expected_usdt > 0 else Decimal('0')

            flash_fee_wei = int(trade_size_dec * USDT_POWER_DEC * FLASH_LOAN_FEE_RATE)
            amount_owed_wei = usdt_borrow_wei + flash_fee_wei
            profit_wei = usdt_back_wei - amount_owed_wei
            profit_usd = float(Decimal(profit_wei) / USDT_POWER_DEC)

            v2_fee_usd = float(wbnb_from_v3 * v2_price_dec * Decimal('0.0025'))  # ✅ FIXED
            v3_fee_usd = float(trade_size_dec * Decimal('0.0001'))  # ✅ FIXED
            flash_fee_usd = float(Decimal(flash_fee_wei) / USDT_POWER_DEC)
            slippage_cost_usd = float(abs(expected_usdt - actual_usdt))
    
            best_token = USDT_ADDRESS
            best_amount = usdt_borrow_wei
            path_name = "USDT→V3($30M)→WBNB→V2→USDT"
            
        else:
            direction = "📉 BUY V2 → SELL V3"

            wbnb_borrow_norm = trade_size_dec / v2_price_dec  # ✅ Based on V2 price
            wbnb_borrow_wei = int(wbnb_borrow_norm * WBNB_POWER_DEC)

            # ✅ CORRECT: V2 swap WBNB → USDT (sell on V2)
            usdt_from_v2_wei = calculate_v2_amount_out(wbnb_borrow_wei, wbnb_reserve, usdt_reserve)
            usdt_from_v2_norm = Decimal(usdt_from_v2_wei) / USDT_POWER_DEC

            # ✅ CORRECT: V3 swap USDT → WBNB (buy back on V3)
            wbnb_back_norm = (usdt_from_v2_norm / v3_price_dec) * Decimal('0.9999')  # After V3 0.01% fee
            wbnb_back_wei = int(wbnb_back_norm * WBNB_POWER_DEC)

            expected_wbnb = usdt_from_v2_norm / v3_price_dec
            actual_wbnb = wbnb_back_norm
            slippage_dec = ((expected_wbnb - actual_wbnb) / expected_wbnb) * Decimal('100') if expected_wbnb > 0 else Decimal('0')

            flash_fee_wei = int(wbnb_borrow_wei * FLASH_LOAN_FEE_RATE)
            amount_owed_wei = wbnb_borrow_wei + flash_fee_wei
            profit_wei = wbnb_back_wei - amount_owed_wei
            profit_wbnb_norm = Decimal(profit_wei) / WBNB_POWER_DEC
            profit_usd = float(profit_wbnb_norm * v2_price_dec)
    
            v3_fee_usd = float(usdt_from_v2_norm * Decimal('0.0001'))  # ✅ FIXED
            v2_fee_usd = float(wbnb_borrow_norm * v2_price_dec * Decimal('0.0025'))  # ✅ FIXED
            flash_fee_usd = float(Decimal(flash_fee_wei) / WBNB_POWER_DEC * v2_price_dec)
            slippage_cost_usd = float(abs(expected_wbnb - actual_wbnb) * v2_price_dec)
    
            best_token = WBNB_ADDRESS
            best_amount = wbnb_borrow_wei
            path_name = "WBNB→V2→USDT→V3($30M)→WBNB"
            
        gap_revenue = float(trade_size_dec * gap_percent_dec / Decimal('100'))
        total_fees_display = v2_fee_usd + v3_fee_usd + flash_fee_usd

        print()
        cprint("="*70, "yellow")
        cprint("🔥 ARBITRAGE OPPORTUNITY DETECTED! 🔥", "yellow", attrs=["bold"])
        cprint("="*70, "yellow")
        print(f"{colored('Direction:', 'white')} {direction}")
        print(f"{colored('Gap:', 'white')} {gap_percent:.4f}% | {colored('Trade Size:', 'white')} ${trade_size:,.0f}")
        print(f"{colored('V2 Price:', 'cyan')} ${V2_PRICE:.4f} | {colored('V3 Price:', 'cyan')} ${last_v3_price:.4f}")
        print(f"{colored('V2 Liquidity:', 'cyan')} ${v2_liquidity:,.0f}")
        print(f"{colored('V3 Liquidity:', 'cyan')} ${v3_liquidity:,.0f}" 
                  if v3_liquidity else "V3 Liquidity: Unknown")

        print(f"\n{colored('📊 PROFITABILITY ANALYSIS:', 'cyan', attrs=['bold'])}")
        print("┌─────────────────────────────────────────────────────────────┐")
        print("│ REVENUE:                                                    │")
        print(f"│   Gap ({gap_percent:.4f}%):                +${gap_revenue:>10,.2f}    │")
        print("│                                                             │")
        print("│ COSTS:                                                      │")
        print(f"│   V2 Fee (0.25%):             -${v2_fee_usd:>10,.2f}    │")
        print(f"│   V3 Fee (0.01%):             -${v3_fee_usd:>10,.2f}    │")
        print(f"│   Flash Fee (0.05%):          -${flash_fee_usd:>10,.2f}    │")
        print(f"│   Gas Cost:                   -${gas_cost_usd:>10,.2f}    │")
        print("│                                ─────────────────            │")
        print(f"│   Direct Fees + Gas:          -${total_fees_display + gas_cost_usd:>10,.2f}    │")
        print("│                                                             │")
        print(f"│   Hidden Slippage Loss:       -${slippage_cost_usd:>10,.2f}    │")
        
        final_profit = gap_revenue - total_fees_display - slippage_cost_usd - gas_cost_usd
        profit_color = "green" if final_profit >= MIN_PROFIT_USD else "red"
        print(f"│ {colored('NET PROFIT (after everything):', profit_color, attrs=['bold'])} ${final_profit:>10,.2f}    │")   
        print("└─────────────────────────────────────────────────────────────┘")
        
        if final_profit >= MIN_PROFIT_USD:
            cprint(f"\n✅ PROFITABLE! Executing trade...", "green", attrs=["bold"])
            cprint(f"Path: {path_name}", "green")
            cprint(f"Flash from: $5M pool | Swap on: $30M pool", "green")
            
    
            # Calculate realistic minOutput = amount to repay + $10 minimum profit
            MIN_PROFIT_USD_DECIMAL = Decimal('10')  # $10 minimum

            if is_path1:
                # PATH 1: USDT borrowed
                # Calculate total amount owed (principal + flash fee)
                flash_fee_wei = int(trade_size_dec * USDT_POWER_DEC * FLASH_LOAN_FEE_RATE)
                amount_owed_wei = usdt_borrow_wei + flash_fee_wei
    
                # Minimum acceptable output = amount owed + $10 profit
                min_profit_wei = int(MIN_PROFIT_USD_DECIMAL * USDT_POWER_DEC)
                best_min_out = min_profit_wei
    
                tolerance_pct = ((usdt_back_wei - best_min_out) / usdt_back_wei) * 100 if usdt_back_wei > 0 else 0
                cprint(f"🔍 Debug: Expected Out={usdt_back_wei/1e18:.2f} USDT", "yellow")
                cprint(f"🔍 Debug: Amount Owed={amount_owed_wei/1e18:.2f} USDT", "yellow")
                cprint(f"🔍 Debug: Min Profit=$10.00 USDT", "yellow")
                cprint(f"🔍 Debug: Min Out={best_min_out/1e18:.2f} USDT", "yellow")
    
            else:
                # PATH 2: WBNB borrowed
                # Calculate total amount owed (principal + flash fee)
                flash_fee_wei = int(wbnb_borrow_wei * FLASH_LOAN_FEE_RATE)
                amount_owed_wei = wbnb_borrow_wei + flash_fee_wei
    
                # Minimum acceptable output = amount owed + $10 profit (in WBNB)
                min_profit_usd = MIN_PROFIT_USD_DECIMAL
                min_profit_wbnb = min_profit_usd / v2_price_dec
                min_profit_wei = int(min_profit_wbnb * WBNB_POWER_DEC)
                best_min_out = min_profit_wei
    
                tolerance_pct = ((wbnb_back_wei - best_min_out) / wbnb_back_wei) * 100 if wbnb_back_wei > 0 else 0
                cprint(f"🔍 Debug: Expected Out={wbnb_back_wei/1e18:.4f} WBNB", "yellow")
                cprint(f"🔍 Debug: Amount Owed={amount_owed_wei/1e18:.4f} WBNB", "yellow")
                cprint(f"🔍 Debug: Min Profit=${min_profit_usd} (~{min_profit_wei/1e18:.4f} WBNB)", "yellow")
                cprint(f"🔍 Debug: Min Out={best_min_out/1e18:.4f} WBNB", "yellow")

            cprint(f"🔍 Debug: Safety Margin={tolerance_pct:.2f}%", "yellow")
            cprint("="*70, "green")
            print()
                  
            current_nonce = w3_sync.eth.get_transaction_count(GAS_WALLET_ADDRESS)
            
            try:
                cprint("🧪 Running deep simulation with revert detection...", "cyan")
                
                try:
                    simulation_result = flash_contract_sync.functions.executeFlashLoan(
                        V2_PAIR_ADDRESS,
                        V3_SWAP_POOL,      # 🔥 UPDATED: $30M pool for swaps
                        V3_FLASH_POOL,     # 🔥 UPDATED: $5M pool for flash
                        best_token,
                        best_amount,
                        best_min_out
                    ).call({'from': GAS_WALLET_ADDRESS, 'gas': 4000000})
                    
                    cprint(f"✅ Simulation PASSED! Result: {simulation_result}", "green", attrs=["bold"])
                    
                except Exception as sim_err:
                    cprint("\n🚨 SIMULATION REVERTED!", "red", attrs=["bold"])
                    cprint("="*70, "red")
                    cprint("📋 RAW ERROR:", "yellow", attrs=["bold"])
                    print(repr(sim_err))
                    
                    if hasattr(sim_err, "args") and len(sim_err.args) > 0:
                        cprint("\n📋 DECODED ARGS:", "yellow", attrs=["bold"])
                        print(sim_err.args)
                    
                    error_str = str(sim_err)
                    if "execution reverted:" in error_str.lower():
                        parts = error_str.split("execution reverted:")
                        if len(parts) > 1:
                            reason = parts[1].strip()
                            cprint(f"\n🎯 REVERT REASON: {reason}", "red", attrs=["bold"])
                    
                    cprint("="*70, "red")
                    raise
                
                try:
                    cprint("\n🔍 Running gas estimation probe...", "cyan")
                    estimated_gas = flash_contract_sync.functions.executeFlashLoan(
                        V2_PAIR_ADDRESS,
                        V3_SWAP_POOL,      # 🔥 UPDATED
                        V3_FLASH_POOL,     # 🔥 UPDATED
                        best_token,
                        best_amount,
                        best_min_out
                    ).estimate_gas({'from': GAS_WALLET_ADDRESS})
                    
                    cprint(f"✅ Gas estimation OK: {estimated_gas:,} gas", "green")
                    
                except Exception as gas_err:
                    cprint("\n🚨 GAS ESTIMATION FAILED!", "red", attrs=["bold"])
                    cprint("="*70, "red")
                    cprint("📋 RAW GAS ERROR:", "yellow", attrs=["bold"])
                    print(repr(gas_err))
                    
                    if hasattr(gas_err, "args") and len(gas_err.args) > 0:
                        cprint("\n📋 DECODED GAS ARGS:", "yellow", attrs=["bold"])
                        print(gas_err.args)
                    
                    error_str = str(gas_err)
                    if "execution reverted:" in error_str.lower():
                        parts = error_str.split("execution reverted:")
                        if len(parts) > 1:
                            reason = parts[1].strip()
                            cprint(f"\n🎯 REVERT REASON: {reason}", "red", attrs=["bold"])
                    
                    cprint("="*70, "red")
                    raise
                
                cprint("📤 Sending real transaction...", "cyan")
                
                transaction = flash_contract_sync.functions.executeFlashLoan(
                    V2_PAIR_ADDRESS,
                    V3_SWAP_POOL,      # 🔥 UPDATED
                    V3_FLASH_POOL,     # 🔥 UPDATED
                    best_token,
                    best_amount,
                    best_min_out
                ).build_transaction({
                    'from': GAS_WALLET_ADDRESS,
                    'gas': 4000000,
                    'gasPrice': w3_sync.eth.gas_price,
                    'nonce': current_nonce
                })
                
                signed_tx = w3_sync.eth.account.sign_transaction(transaction, PRIVATE_KEY)
                
                mev_w3 = Web3(Web3.HTTPProvider(MEV_PROTECTED_RPC))

                try:
                    tx_hash = mev_w3.eth.send_raw_transaction(signed_tx.raw_transaction)
                    cprint("✅ TRANSACTION SENT via MEV Guard!", "green", attrs=["bold"])
                    cprint(f"TX Hash: {tx_hash.hex()}", "cyan")
                    cprint(f"BSCScan: https://bscscan.com/tx/{tx_hash.hex()}", "cyan")
                    
                    cprint("\n⏳ Waiting for confirmation...", "yellow")
                    receipt = w3_sync.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
                    
                    if receipt['status'] == 1:
                        cprint(f"\n🎉 SUCCESS! Transaction confirmed!", "green", attrs=["bold"])
                        cprint(f"Block: {receipt['blockNumber']}", "cyan")
                        cprint(f"Gas Used: {receipt['gasUsed']:,}", "cyan")
                    else:
                        cprint(f"\n❌ Transaction failed on-chain!", "red", attrs=["bold"])
                        cprint(f"Receipt: {receipt}", "red")
                        
                except Exception as send_err:
                    cprint("\n🚨 TRANSACTION FAILED AT SEND!", "red", attrs=["bold"])
                    cprint("="*70, "red")
                    cprint("📋 RAW SEND ERROR:", "yellow", attrs=["bold"])
                    print(repr(send_err))
                    
                    if hasattr(send_err, "args") and len(send_err.args) > 0:
                        cprint("\n📋 DECODED SEND ARGS:", "yellow", attrs=["bold"])
                        print(send_err.args)
                    
                    cprint("="*70, "red")
                    
            except Exception as tx_e:
                error_msg = str(tx_e)
                cprint(f"🚨 TRANSACTION EXECUTION FAILED!", "red", attrs=["bold"])
                cprint(f"Error: {error_msg}\n", "red")
                       
        else:
            cprint(f"\n❌ NOT PROFITABLE (Min: ${MIN_PROFIT_USD:.2f})", "red", attrs=["bold"])
            cprint(f"Skipping trade.\n", "red")
        
    except Exception as e:
        cprint(f"🚨 Error in handle_event: {e}", "red", attrs=["bold"])
        
# =========================================================================
# 5. ASYNC LOOPS (RPC-BASED, NO GRAPHQL)
# =========================================================================

async def get_initial_v3_price(w3_async, v3_pool_contract_async):
    """Fetch initial V3 price on startup"""
    global last_v3_price
    try:
        slot0_data = await v3_pool_contract_async.functions.slot0().call()
        sqrt_price_x96 = slot0_data[0]
        last_v3_price = calculate_v3_price(sqrt_price_x96)
        cprint(
            f"✅ Initial V3 Price: ${last_v3_price:.4f} USDT/WBNB",
            "green"
        )
    except Exception as e:
        cprint(
            f"⚠️  Error fetching initial V3 price: {e}",
            "yellow"
        )


async def v3_price_poller(poll_interval):
    """
    🔥 V3 Price Poller using SYNC HTTP RPC
    Uses the $30M swap pool for price monitoring
    """
    global last_v3_price
    consecutive_failures = 0

    # Wait for V3 pool address to be ready
    while V3_POOL_ADDRESS_DYNAMIC is None:
        cprint("⏳ V3 Poller waiting for pool initialization...", "yellow")
        await asyncio.sleep(3)

    cprint("✅ V3 Price Poller Activated!", "green")

    http_url = WSS_URL.replace("wss://", "https://")
    w3_sync_v3 = Web3(Web3.HTTPProvider(http_url))

    v3_contract_sync = w3_sync_v3.eth.contract(
        address=V3_POOL_ADDRESS_DYNAMIC,
        abi=V3_POOL_ABI
    )

    while True:
        try:
            slot0 = v3_contract_sync.functions.slot0().call()
            sqrt_price_x96 = slot0[0]
            new_price = calculate_v3_price(sqrt_price_x96)

            if new_price > 0:
                last_v3_price = new_price
                consecutive_failures = 0

        except Exception as e:
            consecutive_failures += 1
            if consecutive_failures >= 5:
                cprint(
                    f"⚠️  V3 poller error ({consecutive_failures}): {e}",
                    "yellow"
                )
                consecutive_failures = 0

        await asyncio.sleep(poll_interval)


async def v2_price_backup_poller(poll_interval):
    """
    🔥 V2 Backup Price Poller
    Polls reserves directly if Sync events fail
    """
    global V2_PRICE
    consecutive_failures = 0

    http_url = WSS_URL.replace("wss://", "https://")
    w3_sync_v2 = Web3(Web3.HTTPProvider(http_url))

    v2_contract_sync = w3_sync_v2.eth.contract(
        address=V2_PAIR_ADDRESS,
        abi=V2_PAIR_ABI
    )

    await asyncio.sleep(15)  # Allow event system to start first

    while True:
        try:
            reserves = v2_contract_sync.functions.getReserves().call()
            reserve0, reserve1 = reserves[0], reserves[1]

            if reserve0 == 0 or reserve1 == 0:
                await asyncio.sleep(poll_interval)
                continue

            token0 = v2_contract_sync.functions.token0().call()

            if token0.lower() == WBNB_ADDRESS.lower():
                wbnb_reserve = reserve0
                usdt_reserve = reserve1
            else:
                wbnb_reserve = reserve1
                usdt_reserve = reserve0

            wbnb_norm = Decimal(wbnb_reserve) / WBNB_POWER_DEC
            usdt_norm = Decimal(usdt_reserve) / USDT_POWER_DEC

            if wbnb_norm > 0:
                price = usdt_norm / wbnb_norm
                price_f = float(price)

                if 100 < price_f < 10000:
                    V2_PRICE = price_f
                    consecutive_failures = 0

        except Exception as e:
            consecutive_failures += 1
            if consecutive_failures >= 5:
                cprint(
                    f"⚠️  V2 backup poller error ({consecutive_failures}): {e}",
                    "yellow"
                )
                consecutive_failures = 0

        await asyncio.sleep(poll_interval)


async def heartbeat_monitor():
    """Heartbeat - shows bot is alive every 60 seconds"""
    global V2_PRICE, last_v3_price

    await asyncio.sleep(60)

    while True:
        try:
            now = datetime.now().strftime("%H:%M:%S")

            if V2_PRICE and last_v3_price:
                gap = abs(V2_PRICE - last_v3_price) / last_v3_price * 100
                cprint(
                    f"💚 [{now}] Bot Active | V2: ${V2_PRICE:.2f} | "
                    f"V3: ${last_v3_price:.2f} | Gap: {gap:.3f}%",
                    "green"
                )
            else:
                cprint(
                    f"💛 [{now}] Bot Active | Waiting for price data...",
                    "yellow"
                )

        except Exception:
            now = datetime.now().strftime("%H:%M:%S")
            cprint(f"💙 [{now}] Bot Active", "cyan")

        await asyncio.sleep(60)


async def log_loop(event_filters, poll_interval, w3_sync, flash_contract_sync):
    """Event monitoring loop - checks V2 Sync events"""
    while True:
        try:
            for event in event_filters["v2"].get_new_entries():
                await handle_event(
                    event,
                    "V2",
                    w3_sync,
                    flash_contract_sync
                )

        except ValueError as e:
            if "filter not found" in str(e).lower():
                try:
                    current_block = w3_sync.eth.block_number
                    v2_contract = w3_sync.eth.contract(
                        address=V2_PAIR_ADDRESS,
                        abi=V2_PAIR_ABI
                    )
                    event_filters["v2"] = (
                        v2_contract.events.Sync.create_filter(
                            from_block=current_block
                        )
                    )
                    cprint("⚠️  V2 filter recreated", "yellow")
                except Exception:
                    pass

        except Exception:
            pass

        await asyncio.sleep(poll_interval)

# =========================================================================
# 6. MAIN EXECUTION
# =========================================================================

async def run_scanner():
    """Initialize and run the arbitrage bot"""
    global V3_POOL_ADDRESS_DYNAMIC, FLASH_LOAN_FEE, last_v3_price
    
    print()
    cprint("="*70, "cyan", attrs=["bold"])
    cprint("   PANCAKESWAP V2/V3 ARBITRAGE BOT v2.1 FINAL", "cyan", attrs=["bold"])
    cprint("="*70, "cyan", attrs=["bold"])
    
    print()
    
    try:
        # Setup HTTP connection (sync, stable!)
        http_url = WSS_URL.replace('wss://', 'https://')
        w3_sync = Web3(Web3.HTTPProvider(http_url))
        
        if not w3_sync.is_connected():
            cprint("❌ Connection failed", "red", attrs=["bold"])
            return
        
        w3_sync.eth.default_account = GAS_WALLET_ADDRESS
        cprint(f"✅ Wallet: {GAS_WALLET_ADDRESS}", "green")
        
        # Get V3 pool info (uses $30M swap pool)
        V3_POOL_ADDRESS_DYNAMIC, _ = get_v3_pool_data(w3_sync)
        if not V3_POOL_ADDRESS_DYNAMIC:
            return
        
        # Get current block
        current_block = w3_sync.eth.block_number
        cprint(f"✅ Connected to BSC! Block: {current_block}", "green")
        
        # Setup contracts (all using sync HTTP connection!)
        v2_pool_contract_sync = w3_sync.eth.contract(address=V2_PAIR_ADDRESS, abi=V2_PAIR_ABI)
        v3_pool_contract_sync = w3_sync.eth.contract(address=V3_POOL_ADDRESS_DYNAMIC, abi=V3_POOL_ABI)
        flash_contract_sync = w3_sync.eth.contract(address=FLASH_LOAN_CONTRACT_ADDRESS, abi=FLASH_LOAN_ABI)
        
        cprint(f"\n📊 TRADING PARAMETERS:", "cyan", attrs=["bold"])
        print(f"├─ V2 Pool: {V2_PAIR_ADDRESS}")
        print(f"├─ V3 Swap Pool ($30M): {V3_SWAP_POOL}")
        print(f"├─ V3 Flash Pool ($5M): {V3_FLASH_POOL}")
        print(f"├─ Flash Loan Contract: {FLASH_LOAN_CONTRACT_ADDRESS}")
        print(f"├─ Max Capital: ${TARGET_FLASH_USD:,.0f}")
        print(f"├─ Max Slippage: {MAX_SLIPPAGE_PERCENT}%")
        print(f"├─ Min Liquidity: ${MIN_LIQUIDITY_USD:,.0f}")
        print(f"├─ Min Gap: {MIN_GAP_PERCENT}%")
        print(f"├─ Min Profit: ${MIN_PROFIT_USD:.2f}")
        print(f"├─ Flash Fee: {FLASH_LOAN_FEE*100:.2f}%")
        print(f"└─ Profit Safety Margin: {PROFIT_SAFETY_MARGIN}x\n")
        
        cprint("🔧 NETWORK SETUP:", "cyan", attrs=["bold"])
        print(f"├─ V2 Price: Sync Events (Real-time) ✅")
        print(f"│  └─ Frontrunning/Sandwich Attack Protection ACTIVE")
        print(f"├─ V3 Price: HTTP RPC Polling (Every 5s - Reliable!) ✅")
        print(f"├─ V3 Flash: $5M Pool (0.05% fee) ✅")
        print(f"├─ V3 Swap: $30M Pool (Low slippage) ✅")
        print(f"└─ Execution: HTTPS RPC (Stable) ✅\n")
        
        # 🔥 Get initial V3 price using SYNC connection
        try:
            slot0 = v3_pool_contract_sync.functions.slot0().call()
            sqrt_price_x96 = slot0[0]
            last_v3_price = calculate_v3_price(sqrt_price_x96)
            cprint(f"✅ Initial V3 Price: ${last_v3_price:.4f} USDT/WBNB", "green")
        except Exception as e:
            cprint(f"⚠️  Error fetching initial V3 price: {e}", "yellow")
        
        # Setup V2 event filter
        v2_filter = v2_pool_contract_sync.events.Sync.create_filter(from_block=current_block)
        event_filters = {'v2': v2_filter}
        
        cprint("✅ V2 Sync event listener activated!", "green")
        
        # Silent mode banner
        print()
        cprint("="*70, "green", attrs=["bold"])
        cprint("🔇 SILENT MODE ACTIVE - Monitoring gaps quietly...", "green", attrs=["bold"])
        cprint(f"📊 Will alert when gap ≥ {MIN_GAP_PERCENT}%", "cyan")
        cprint("💚 Heartbeat every 60 seconds to confirm bot is alive", "cyan")
        cprint("⚡ V3 price updated every 5 seconds via HTTP RPC (Reliable!)", "cyan")
        cprint("="*70, "green", attrs=["bold"])
        print()
        
        # 🔥 Run all loops
        await asyncio.gather(
            log_loop(event_filters, 2, w3_sync, flash_contract_sync),  # V2 events (primary)
            v3_price_poller(5),              # V3 poller every 5s
            v2_price_backup_poller(10),      # V2 backup every 10s
            heartbeat_monitor()              # Heartbeat every 60s
        )
    
    except Exception as e:
        cprint(f"❌ FATAL ERROR: {e}", "red", attrs=["bold"])

if __name__ == "__main__":
    try:
        asyncio.run(run_scanner())
    except KeyboardInterrupt:
        cprint("\n\n👋 Bot stopped by user. Goodbye!", "yellow", attrs=["bold"])
    except Exception as e:
        cprint(f"❌ Error: {e}", "red", attrs=["bold"])
