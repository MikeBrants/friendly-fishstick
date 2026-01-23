"""
Auto-generated Cluster Configuration
Generated: 2026-01-24T01:39:53.461259
Clusters found via K-means on optimized parameters
"""

CLUSTER_PARAMS = {
    "cluster_0": {
        "assets": ['ILV', 'ONE'],
        "atr": {
            "sl_mult": 2.0,
            "tp1_mult": 3.5,
            "tp2_mult": 7.5,
            "tp3_mult": 9.0,
        },
        "ichimoku": {"tenkan": 8, "kijun": 35},
        "five_in_one": {"tenkan_5": 12, "kijun_5": 28},
        "displacement": 52,
        "avg_sharpe": 3.16,
        "avg_trades": 96,
    },
    "cluster_1": {
        "assets": ['PEPE'],
        "atr": {
            "sl_mult": 2.5,
            "tp1_mult": 3.25,
            "tp2_mult": 5.5,
            "tp3_mult": 10.0,
        },
        "ichimoku": {"tenkan": 9, "kijun": 21},
        "five_in_one": {"tenkan_5": 14, "kijun_5": 21},
        "displacement": 52,
        "avg_sharpe": 2.95,
        "avg_trades": 93,
    },
}

# Asset to cluster mapping
ASSET_CLUSTER = {
    "PEPE": "cluster_1",
    "ILV": "cluster_0",
    "ONE": "cluster_0",
}


def get_params_for_asset(asset: str) -> dict:
    """Get cluster parameters for a given asset."""
    cluster_name = ASSET_CLUSTER.get(asset)
    if cluster_name is None:
        raise ValueError(f"Unknown asset: {asset}")
    return CLUSTER_PARAMS[cluster_name]