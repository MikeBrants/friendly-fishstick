"""
Multi-Asset Scan Configuration
Updated: 2026-01-20
Top 50 Cryptos by Market Cap (excluding stablecoins)
"""

# =============================================================================
# TOP 50 CRYPTOS (by market cap, excluding stablecoins)
# =============================================================================

# Tier 1 - Top 10 (Blue chips)
TIER1_ASSETS = [
    "BTC",    # Bitcoin
    "ETH",    # Ethereum
    "XRP",    # Ripple
    "BNB",    # Binance Coin
    "SOL",    # Solana
    "ADA",    # Cardano
    "DOGE",   # Dogecoin
    "AVAX",   # Avalanche
    "TRX",    # Tron
    "DOT",    # Polkadot
]

# Tier 2 - Top 11-25 (Large caps)
TIER2_ASSETS = [
    "LINK",   # Chainlink - Oracle
    "MATIC",  # Polygon (POL)
    "TON",    # Toncoin
    "SHIB",   # Shiba Inu
    "LTC",    # Litecoin
    "BCH",    # Bitcoin Cash
    "ATOM",   # Cosmos
    "UNI",    # Uniswap
    "XLM",    # Stellar
    "NEAR",   # Near Protocol
    "APT",    # Aptos
    "ICP",    # Internet Computer
    "FIL",    # Filecoin
    "ARB",    # Arbitrum
    "OP",     # Optimism
]

# Tier 3 - Top 26-40 (Mid caps)
TIER3_ASSETS = [
    "HBAR",   # Hedera
    "VET",    # VeChain
    "MKR",    # Maker
    "AAVE",   # Aave
    "INJ",    # Injective
    "SUI",    # Sui
    "IMX",    # Immutable X
    "RUNE",   # THORChain
    "GRT",    # The Graph
    "TIA",    # Celestia
    "SEI",    # Sei
    "STX",    # Stacks
    "ALGO",   # Algorand
    "FTM",    # Fantom
    "EGLD",   # MultiversX
]

# Tier 4 - Top 41-50 (Mid-small caps)
TIER4_ASSETS = [
    "SAND",   # Sandbox
    "MANA",   # Decentraland
    "FLOW",   # Flow
    "XTZ",    # Tezos
    "AXS",    # Axie Infinity
    "GALA",   # Gala Games
    "THETA",  # Theta Network
    "EOS",    # EOS
    "KAVA",   # Kava
    "RENDER", # Render Network
]

# Bonus - High potential / Trending
BONUS_ASSETS = [
    "HYPE",   # Hyperliquid
    "WIF",    # Dogwifhat
    "PEPE",   # Pepe
    "BONK",   # Bonk
    "JUP",    # Jupiter
    "W",      # Wormhole
    "STRK",   # Starknet
    "PYTH",   # Pyth Network
    "JTO",    # Jito
    "WLD",    # Worldcoin
]

# =============================================================================
# ASSET GROUPS
# =============================================================================

# Already validated assets (production ready)
VALIDATED_ASSETS = ["BTC", "ETH", "XRP", "AVAX", "UNI", "SEI"]

# Assets excluded (failed guards or overfit)
EXCLUDED_ASSETS = ["SOL", "AAVE", "SUI", "HYPE", "ATOM", "ARB", "LINK", "INJ", "TIA"]

# New assets to scan (not yet tested)
SCAN_ASSETS = [
    # From Tier 1
    "BNB", "ADA", "DOGE", "TRX", "DOT",
    # From Tier 2
    "MATIC", "TON", "SHIB", "LTC", "BCH", "XLM", "NEAR", "APT", "ICP", "FIL", "OP",
    # From Tier 3
    "HBAR", "VET", "MKR", "IMX", "RUNE", "GRT", "STX", "ALGO", "FTM", "EGLD",
    # From Tier 4
    "SAND", "MANA", "FLOW", "XTZ", "AXS", "GALA", "THETA", "EOS", "KAVA", "RENDER",
    # Bonus
    "WIF", "PEPE", "BONK", "JUP", "W", "STRK", "PYTH", "JTO", "WLD",
]

# All top 50 assets
TOP50_ASSETS = TIER1_ASSETS + TIER2_ASSETS + TIER3_ASSETS + TIER4_ASSETS

# All assets (for full download)
ALL_ASSETS = list(set(TOP50_ASSETS + BONUS_ASSETS))

# =============================================================================
# EXCHANGE MAPPING
# =============================================================================

# Default exchange for each asset
# Most are on Binance, exceptions noted
EXCHANGE_MAP = {
    # Tier 1
    "BTC": "binance", "ETH": "binance", "XRP": "binance", "BNB": "binance",
    "SOL": "binance", "ADA": "binance", "DOGE": "binance", "AVAX": "binance",
    "TRX": "binance", "DOT": "binance",

    # Tier 2
    "LINK": "binance", "MATIC": "binance", "TON": "binance", "SHIB": "binance",
    "LTC": "binance", "BCH": "binance", "ATOM": "binance", "UNI": "binance",
    "XLM": "binance", "NEAR": "binance", "APT": "binance", "ICP": "binance",
    "FIL": "binance", "ARB": "binance", "OP": "binance",

    # Tier 3
    "HBAR": "binance", "VET": "binance", "MKR": "binance", "AAVE": "binance",
    "INJ": "binance", "SUI": "binance", "IMX": "binance", "RUNE": "binance",
    "GRT": "binance", "TIA": "binance", "SEI": "binance", "STX": "binance",
    "ALGO": "binance", "FTM": "binance", "EGLD": "binance",

    # Tier 4
    "SAND": "binance", "MANA": "binance", "FLOW": "binance", "XTZ": "binance",
    "AXS": "binance", "GALA": "binance", "THETA": "binance", "EOS": "binance",
    "KAVA": "binance", "RENDER": "binance",

    # Bonus (some on Bybit)
    "HYPE": "bybit",    # Hyperliquid - only on Bybit/own DEX
    "WIF": "binance", "PEPE": "binance", "BONK": "binance", "JUP": "binance",
    "W": "binance", "STRK": "binance", "PYTH": "binance", "JTO": "binance",
    "WLD": "binance",
}

# =============================================================================
# OPTIMIZATION PARAMETERS
# =============================================================================

OPTIM_CONFIG = {
    "n_trials_atr": 100,
    "n_trials_ichi": 100,
    "validation_split": (0.6, 0.2, 0.2),  # IS/VAL/OOS
    "warmup_bars": 200,
    "min_trades": 50,
}

# ATR search space
ATR_SEARCH_SPACE = {
    "sl_mult": (1.5, 5.0),
    "tp1_mult": (1.5, 5.0),
    "tp2_mult": (3.0, 12.0),
    "tp3_mult": (2.0, 10.0),
}

# ATR search space for moderate optimization
ATR_SEARCH_SPACE_MODERATE = {
    "sl_mult": (2.0, 4.75),
    "tp1_mult": (2.0, 4.75),
    "tp2_mult": (3.5, 10.0),
    "tp3_mult": (5.0, 11.0),
}

# Ichimoku search space
ICHI_SEARCH_SPACE = {
    "tenkan": (5, 20),
    "kijun": (20, 40),
    "tenkan_5": (8, 16),
    "kijun_5": (15, 30),
}

# Clustering parameters
CLUSTER_CONFIG = {
    "n_clusters_range": (2, 5),
    "max_param_loss": 0.15,
    "min_cluster_size": 3,
}

# Pass criteria for validation
PASS_CRITERIA = {
    "oos_sharpe_min": 1.0,
    "wfe_min": 0.6,
    "oos_trades_min": 50,
    "max_dd_max": 0.15,
}
