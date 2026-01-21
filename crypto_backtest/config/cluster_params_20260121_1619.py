"""
Auto-generated Cluster Configuration
Generated: 2026-01-21T16:19:59.123789
Clusters found via K-means on optimized parameters
"""

CLUSTER_PARAMS = {
    "cluster_0": {
        "assets": ['DOT', 'SHIB'],
        "atr": {
            "sl_mult": 2.5,
            "tp1_mult": 4.25,
            "tp2_mult": 7.5,
            "tp3_mult": 9.0,
        },
        "ichimoku": {"tenkan": 14, "kijun": 32},
        "five_in_one": {"tenkan_5": 15, "kijun_5": 23},
        "displacement": 52,
        "avg_sharpe": 4.13,
        "avg_trades": 93,
    },
    "cluster_1": {
        "assets": ['NEAR'],
        "atr": {
            "sl_mult": 4.5,
            "tp1_mult": 2.75,
            "tp2_mult": 5.5,
            "tp3_mult": 6.5,
        },
        "ichimoku": {"tenkan": 8, "kijun": 38},
        "five_in_one": {"tenkan_5": 8, "kijun_5": 27},
        "displacement": 52,
        "avg_sharpe": 3.25,
        "avg_trades": 99,
    },
}

# Asset to cluster mapping
ASSET_CLUSTER = {
    "DOT": "cluster_0",
    "SHIB": "cluster_0",
    "NEAR": "cluster_1",
}


def get_params_for_asset(asset: str) -> dict:
    """Get cluster parameters for a given asset."""
    cluster_name = ASSET_CLUSTER.get(asset)
    if cluster_name is None:
        raise ValueError(f"Unknown asset: {asset}")
    return CLUSTER_PARAMS[cluster_name]