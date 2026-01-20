"""
Multi-Asset Scan Configuration
Generated: 2026-01-20
"""

# Assets to scan (new alts)
SCAN_ASSETS = [
    "HYPE",   # Hyperliquid - DEX Perp
    "AVAX",   # Avalanche - L1
    "ATOM",   # Cosmos - IBC
    "ARB",    # Arbitrum - L2
    "LINK",   # Chainlink - Oracle
    "UNI",    # Uniswap - DeFi
    "SUI",    # Sui - L1 Move
    "INJ",    # Injective - DeFi/Perp
    "TIA",    # Celestia - Modular
    "SEI",    # Sei - L1 Fast
]

# Already validated assets (for clustering comparison)
VALIDATED_ASSETS = ["BTC", "ETH", "XRP"]

# All assets
ALL_ASSETS = VALIDATED_ASSETS + SCAN_ASSETS

# Exchange mapping per asset
EXCHANGE_MAP = {
    "BTC": "binance", "ETH": "binance", "XRP": "binance",
    "HYPE": "bybit",
    "AVAX": "binance", "ATOM": "binance", "ARB": "binance",
    "LINK": "binance", "UNI": "binance", "SUI": "binance",
    "INJ": "binance", "TIA": "binance", "SEI": "binance",
}

# Optimization parameters
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
