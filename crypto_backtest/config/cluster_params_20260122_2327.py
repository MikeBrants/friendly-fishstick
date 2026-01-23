"""
Auto-generated Cluster Configuration
Generated: 2026-01-22T23:27:08.982234
Clusters found via K-means on optimized parameters
"""

CLUSTER_PARAMS = {
    "cluster_0": {
        "assets": ['STRK', 'METIS'],
        "atr": {
            "sl_mult": 1.75,
            "tp1_mult": 4.0,
            "tp2_mult": 7.0,
            "tp3_mult": 9.0,
        },
        "ichimoku": {"tenkan": 18, "kijun": 25},
        "five_in_one": {"tenkan_5": 10, "kijun_5": 18},
        "displacement": 52,
        "avg_sharpe": 2.08,
        "avg_trades": 94,
    },
    "cluster_1": {
        "assets": ['AEVO'],
        "atr": {
            "sl_mult": 4.5,
            "tp1_mult": 2.75,
            "tp2_mult": 5.5,
            "tp3_mult": 9.0,
        },
        "ichimoku": {"tenkan": 7, "kijun": 23},
        "five_in_one": {"tenkan_5": 8, "kijun_5": 28},
        "displacement": 52,
        "avg_sharpe": 1.23,
        "avg_trades": 81,
    },
}

# Asset to cluster mapping
ASSET_CLUSTER = {
    "STRK": "cluster_0",
    "METIS": "cluster_0",
    "AEVO": "cluster_1",
}


def get_params_for_asset(asset: str) -> dict:
    """Get cluster parameters for a given asset."""
    cluster_name = ASSET_CLUSTER.get(asset)
    if cluster_name is None:
        raise ValueError(f"Unknown asset: {asset}")
    return CLUSTER_PARAMS[cluster_name]