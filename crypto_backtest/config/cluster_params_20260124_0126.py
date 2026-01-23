"""
Auto-generated Cluster Configuration
Generated: 2026-01-24T01:26:19.652038
Clusters found via K-means on optimized parameters
"""

CLUSTER_PARAMS = {
    "cluster_0": {
        "assets": ['ILV', 'CHZ', 'ROSE'],
        "atr": {
            "sl_mult": 3.25,
            "tp1_mult": 3.5,
            "tp2_mult": 7.0,
            "tp3_mult": 10.0,
        },
        "ichimoku": {"tenkan": 12, "kijun": 39},
        "five_in_one": {"tenkan_5": 10, "kijun_5": 22},
        "displacement": 52,
        "avg_sharpe": 1.85,
        "avg_trades": 83,
    },
    "cluster_1": {
        "assets": ['GALA', 'ONE'],
        "atr": {
            "sl_mult": 1.75,
            "tp1_mult": 5.0,
            "tp2_mult": 6.0,
            "tp3_mult": 9.5,
        },
        "ichimoku": {"tenkan": 5, "kijun": 25},
        "five_in_one": {"tenkan_5": 12, "kijun_5": 20},
        "displacement": 52,
        "avg_sharpe": 3.06,
        "avg_trades": 105,
    },
}

# Asset to cluster mapping
ASSET_CLUSTER = {
    "GALA": "cluster_1",
    "ILV": "cluster_0",
    "CHZ": "cluster_0",
    "ONE": "cluster_1",
    "ROSE": "cluster_0",
}


def get_params_for_asset(asset: str) -> dict:
    """Get cluster parameters for a given asset."""
    cluster_name = ASSET_CLUSTER.get(asset)
    if cluster_name is None:
        raise ValueError(f"Unknown asset: {asset}")
    return CLUSTER_PARAMS[cluster_name]