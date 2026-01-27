"""
Auto-generated Cluster Configuration
Generated: 2026-01-27T00:24:20.640403
Clusters found via K-means on optimized parameters
"""

CLUSTER_PARAMS = {
    "cluster_0": {
        "assets": ['DOGE', 'ANKR'],
        "atr": {
            "sl_mult": 2.5,
            "tp1_mult": 3.25,
            "tp2_mult": 7.0,
            "tp3_mult": 10.0,
        },
        "ichimoku": {"tenkan": 11, "kijun": 32},
        "five_in_one": {"tenkan_5": 9, "kijun_5": 16},
        "displacement": 52,
        "avg_sharpe": 3.20,
        "avg_trades": 87,
    },
    "cluster_1": {
        "assets": ['ETH'],
        "atr": {
            "sl_mult": 4.25,
            "tp1_mult": 2.25,
            "tp2_mult": 5.5,
            "tp3_mult": 10.0,
        },
        "ichimoku": {"tenkan": 6, "kijun": 34},
        "five_in_one": {"tenkan_5": 14, "kijun_5": 23},
        "displacement": 52,
        "avg_sharpe": 4.18,
        "avg_trades": 78,
    },
}

# Asset to cluster mapping
ASSET_CLUSTER = {
    "DOGE": "cluster_0",
    "ANKR": "cluster_0",
    "ETH": "cluster_1",
}


def get_params_for_asset(asset: str) -> dict:
    """Get cluster parameters for a given asset."""
    cluster_name = ASSET_CLUSTER.get(asset)
    if cluster_name is None:
        raise ValueError(f"Unknown asset: {asset}")
    return CLUSTER_PARAMS[cluster_name]