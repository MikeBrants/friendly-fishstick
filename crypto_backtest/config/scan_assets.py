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
EXCLUDED_ASSETS = ["SOL", "AAVE", "SUI", "HYPE", "ATOM", "ARB", "LINK", "INJ", "EGLD", "AVAX"]  # EGLD, AVAX: Regime stress FAIL (SIDEWAYS, 26 Jan 2026)

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

# Optimization config
# NOTE: Trial count reduced from 100 to 60 based on R&D findings
# More trials -> more overfitting (BTC: 50 trials WFE=0.45 vs 100 trials WFE=0.18)
# See: outputs/trial_count_experiment_BTC_*.csv
OPTIM_CONFIG = {
    "n_trials_atr": 60,      # Reduced from 100 to avoid overfitting
    "n_trials_ichi": 60,     # Reduced from 100 to avoid overfitting
    "validation_split": (0.6, 0.2, 0.2),  # IS/VAL/OOS
    "warmup_bars": 200,
    "min_trades": 50,
}

# Legacy high-trial config (use for final validation only)
OPTIM_CONFIG_HIGH_TRIALS = {
    "n_trials_atr": 150,
    "n_trials_ichi": 150,
    "validation_split": (0.6, 0.2, 0.2),
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

# =============================================================================
# VOLATILITY-BASED PARAMETER RANGES (Alex R&D Plan - Track 1: RESCUE)
# =============================================================================
# 
# Hypothesis: Tighter, asset-specific ranges reduce overfitting.
# Assets are clustered by volatility profile into 3 categories.
#
# HIGH_VOL: Meme coins, small caps (high ATR, fast moves)
#   -> Tighter stops (lower sl_mult), quicker profits
# MED_VOL: Mid-cap alts (standard volatility)
#   -> Balanced ranges
# LOW_VOL: Majors like BTC, ETH (lower ATR relative to price)
#   -> Wider stops to avoid noise, larger profit targets

# Asset classification by volatility profile
VOLATILITY_PROFILES = {
    # HIGH_VOL - Meme coins and small caps
    "HIGH_VOL": [
        "SHIB", "DOGE", "PEPE", "BONK", "WIF", "FLOKI",  # Meme coins
        "GALA", "SAND", "MANA", "AXS", "IMX",  # Gaming/Metaverse
        "JOE", "OSMO",  # DeFi small caps
    ],
    # MED_VOL - Mid-cap altcoins
    "MED_VOL": [
        "SOL", "AVAX", "DOT", "ATOM", "NEAR", "FTM", "ALGO",  # L1s
        "LINK", "UNI", "AAVE", "MKR", "INJ",  # DeFi
        "ARB", "OP", "MATIC", "IMX", "STRK",  # L2s
        "APT", "SUI", "SEI", "TIA",  # New L1s
    ],
    # LOW_VOL - Major cryptocurrencies (blue chips)
    "LOW_VOL": [
        "BTC", "ETH", "BNB", "XRP",  # Top 4
        "ADA", "TRX", "LTC", "BCH",  # Established large caps
    ],
}

# ATR search spaces by volatility profile
ATR_SEARCH_SPACE_HIGH_VOL = {
    # Tighter stops for high volatility assets
    "sl_mult": (1.5, 3.5),      # Tighter SL (was 1.5-5.0)
    "tp1_mult": (1.5, 3.0),     # Quick first profit
    "tp2_mult": (2.5, 7.0),     # Moderate second target
    "tp3_mult": (4.0, 10.0),    # Runner target
}

ATR_SEARCH_SPACE_MED_VOL = {
    # Standard ranges for medium volatility
    "sl_mult": (2.0, 4.5),
    "tp1_mult": (2.0, 4.0),
    "tp2_mult": (3.5, 10.0),
    "tp3_mult": (5.0, 12.0),
}

ATR_SEARCH_SPACE_LOW_VOL = {
    # Wider stops for low volatility majors
    "sl_mult": (3.0, 5.5),      # Wider SL to avoid noise
    "tp1_mult": (3.0, 5.5),     # Larger first target
    "tp2_mult": (5.0, 12.0),    # Larger second target
    "tp3_mult": (7.0, 15.0),    # Extended runner
}

# Map of search spaces by profile
ATR_SEARCH_SPACES_BY_VOL = {
    "HIGH_VOL": ATR_SEARCH_SPACE_HIGH_VOL,
    "MED_VOL": ATR_SEARCH_SPACE_MED_VOL,
    "LOW_VOL": ATR_SEARCH_SPACE_LOW_VOL,
}


def get_volatility_profile(asset: str) -> str:
    """
    Get the volatility profile for an asset.
    
    Returns:
        One of "HIGH_VOL", "MED_VOL", "LOW_VOL"
        Defaults to "MED_VOL" if asset not classified.
    """
    for profile, assets in VOLATILITY_PROFILES.items():
        if asset.upper() in assets:
            return profile
    return "MED_VOL"  # Default to medium if not classified


def get_atr_search_space_for_asset(asset: str) -> dict:
    """
    Get the appropriate ATR search space based on asset's volatility profile.
    
    Args:
        asset: Asset ticker (e.g., "BTC", "SHIB")
    
    Returns:
        ATR search space dict suitable for the asset
    """
    profile = get_volatility_profile(asset)
    return ATR_SEARCH_SPACES_BY_VOL[profile]


# =============================================================================
# MEME COIN CLUSTER (from SHIB investigation)
# =============================================================================
# These assets showed similar patterns in validation:
# - High trade frequency (400+ trades)
# - SIDEWAYS dominance (>50% of PnL)
# - WFE > 1.0 (OOS better than IS)
# - Low sensitivity variance (<10%)

MEME_COINS = ["SHIB", "DOGE", "PEPE", "BONK", "WIF", "FLOKI"]

# Recommended displacement for meme coins (faster price action)
MEME_COIN_DISPLACEMENT = 26

# Recommended filter mode for meme coins
MEME_COIN_FILTER_MODE = "baseline"  # Minimal filters work best


def is_meme_coin(asset: str) -> bool:
    """Check if an asset is classified as a meme coin."""
    return asset.upper() in MEME_COINS
