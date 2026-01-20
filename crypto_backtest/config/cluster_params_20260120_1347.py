"""
Auto-generated Cluster Configuration
Generated: 2026-01-20T13:47:33.918642
Clusters found via K-means on optimized parameters
"""

CLUSTER_PARAMS = {
    "cluster_0": {
        "assets": ['UNI', 'SUI', 'SEI'],
        "atr": {
            "sl_mult": 3.25,
            "tp1_mult": 4.75,
            "tp2_mult": 6.0,
            "tp3_mult": 9.0,
        },
        "ichimoku": {"tenkan": 11, "kijun": 26},
        "five_in_one": {"tenkan_5": 8, "kijun_5": 29},
        "displacement": 52,
        "avg_sharpe": 3.42,
        "avg_trades": 79,
    },
    "cluster_1": {
        "assets": ['AVAX'],
        "atr": {
            "sl_mult": 2.75,
            "tp1_mult": 1.5,
            "tp2_mult": 10.5,
            "tp3_mult": 8.0,
        },
        "ichimoku": {"tenkan": 20, "kijun": 23},
        "five_in_one": {"tenkan_5": 12, "kijun_5": 16},
        "displacement": 52,
        "avg_sharpe": 4.22,
        "avg_trades": 102,
    },
}

# Asset to cluster mapping
ASSET_CLUSTER = {
    "AVAX": "cluster_1",
    "UNI": "cluster_0",
    "SUI": "cluster_0",
    "SEI": "cluster_0",
}


def get_params_for_asset(asset: str) -> dict:
    """Get cluster parameters for a given asset."""
    cluster_name = ASSET_CLUSTER.get(asset)
    if cluster_name is None:
        raise ValueError(f"Unknown asset: {asset}")
    return CLUSTER_PARAMS[cluster_name]