"""
Auto-generated Cluster Configuration
Generated: 2026-01-24T00:26:57.429017
Clusters found via K-means on optimized parameters
"""

CLUSTER_PARAMS = {
    "cluster_0": {
        "assets": ['PEPE', 'ILV'],
        "atr": {
            "sl_mult": 2.0,
            "tp1_mult": 3.5,
            "tp2_mult": 8.5,
            "tp3_mult": 10.0,
        },
        "ichimoku": {"tenkan": 8, "kijun": 29},
        "five_in_one": {"tenkan_5": 11, "kijun_5": 18},
        "displacement": 52,
        "avg_sharpe": 2.31,
        "avg_trades": 94,
    },
    "cluster_1": {
        "assets": ['SAND', 'ONE'],
        "atr": {
            "sl_mult": 2.0,
            "tp1_mult": 5.0,
            "tp2_mult": 6.0,
            "tp3_mult": 7.5,
        },
        "ichimoku": {"tenkan": 8, "kijun": 27},
        "five_in_one": {"tenkan_5": 14, "kijun_5": 21},
        "displacement": 52,
        "avg_sharpe": 2.44,
        "avg_trades": 102,
    },
}

# Asset to cluster mapping
ASSET_CLUSTER = {
    "SAND": "cluster_1",
    "PEPE": "cluster_0",
    "ILV": "cluster_0",
    "ONE": "cluster_1",
}


def get_params_for_asset(asset: str) -> dict:
    """Get cluster parameters for a given asset."""
    cluster_name = ASSET_CLUSTER.get(asset)
    if cluster_name is None:
        raise ValueError(f"Unknown asset: {asset}")
    return CLUSTER_PARAMS[cluster_name]