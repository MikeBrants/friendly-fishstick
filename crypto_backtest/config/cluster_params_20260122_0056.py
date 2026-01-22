"""
Auto-generated Cluster Configuration
Generated: 2026-01-22T00:56:10.256399
Clusters found via K-means on optimized parameters
"""

CLUSTER_PARAMS = {
    "cluster_0": {
        "assets": ['HBAR', 'YGG', 'CELO', 'AR', 'ANKR', 'STRK', 'METIS', 'AEVO'],
        "atr": {
            "sl_mult": 2.5,
            "tp1_mult": 3.25,
            "tp2_mult": 7.0,
            "tp3_mult": 9.0,
        },
        "ichimoku": {"tenkan": 13, "kijun": 28},
        "five_in_one": {"tenkan_5": 12, "kijun_5": 22},
        "displacement": 52,
        "avg_sharpe": 2.61,
        "avg_trades": 95,
    },
    "cluster_1": {
        "assets": ['EGLD', 'IMX', 'W'],
        "atr": {
            "sl_mult": 4.75,
            "tp1_mult": 2.25,
            "tp2_mult": 4.0,
            "tp3_mult": 8.0,
        },
        "ichimoku": {"tenkan": 6, "kijun": 22},
        "five_in_one": {"tenkan_5": 8, "kijun_5": 26},
        "displacement": 52,
        "avg_sharpe": 1.62,
        "avg_trades": 92,
    },
}

# Asset to cluster mapping
ASSET_CLUSTER = {
    "HBAR": "cluster_0",
    "EGLD": "cluster_1",
    "IMX": "cluster_1",
    "YGG": "cluster_0",
    "CELO": "cluster_0",
    "AR": "cluster_0",
    "ANKR": "cluster_0",
    "W": "cluster_1",
    "STRK": "cluster_0",
    "METIS": "cluster_0",
    "AEVO": "cluster_0",
}


def get_params_for_asset(asset: str) -> dict:
    """Get cluster parameters for a given asset."""
    cluster_name = ASSET_CLUSTER.get(asset)
    if cluster_name is None:
        raise ValueError(f"Unknown asset: {asset}")
    return CLUSTER_PARAMS[cluster_name]