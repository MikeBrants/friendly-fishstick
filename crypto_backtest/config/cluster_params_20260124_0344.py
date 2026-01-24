"""
Auto-generated Cluster Configuration
Generated: 2026-01-24T03:44:31.337433
Clusters found via K-means on optimized parameters
"""

CLUSTER_PARAMS = {
    "cluster_0": {
        "assets": ['JOE', 'DOGE', 'SHIB'],
        "atr": {
            "sl_mult": 2.5,
            "tp1_mult": 4.5,
            "tp2_mult": 6.0,
            "tp3_mult": 9.0,
        },
        "ichimoku": {"tenkan": 14, "kijun": 24},
        "five_in_one": {"tenkan_5": 14, "kijun_5": 21},
        "displacement": 52,
        "avg_sharpe": 3.99,
        "avg_trades": 90,
    },
    "cluster_1": {
        "assets": ['ETH', 'ANKR', 'DOT'],
        "atr": {
            "sl_mult": 2.75,
            "tp1_mult": 4.5,
            "tp2_mult": 7.0,
            "tp3_mult": 10.0,
        },
        "ichimoku": {"tenkan": 9, "kijun": 37},
        "five_in_one": {"tenkan_5": 8, "kijun_5": 17},
        "displacement": 52,
        "avg_sharpe": 3.54,
        "avg_trades": 79,
    },
    "cluster_2": {
        "assets": ['NEAR'],
        "atr": {
            "sl_mult": 4.75,
            "tp1_mult": 1.5,
            "tp2_mult": 9.5,
            "tp3_mult": 10.0,
        },
        "ichimoku": {"tenkan": 5, "kijun": 39},
        "five_in_one": {"tenkan_5": 8, "kijun_5": 25},
        "displacement": 52,
        "avg_sharpe": 2.33,
        "avg_trades": 96,
    },
}

# Asset to cluster mapping
ASSET_CLUSTER = {
    "ETH": "cluster_1",
    "JOE": "cluster_0",
    "ANKR": "cluster_1",
    "DOGE": "cluster_0",
    "DOT": "cluster_1",
    "NEAR": "cluster_2",
    "SHIB": "cluster_0",
}


def get_params_for_asset(asset: str) -> dict:
    """Get cluster parameters for a given asset."""
    cluster_name = ASSET_CLUSTER.get(asset)
    if cluster_name is None:
        raise ValueError(f"Unknown asset: {asset}")
    return CLUSTER_PARAMS[cluster_name]