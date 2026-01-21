"""
Auto-generated Cluster Configuration
Generated: 2026-01-21T17:51:46.205556
Clusters found via K-means on optimized parameters
"""

CLUSTER_PARAMS = {
    "cluster_0": {
        "assets": ['ICP', 'HBAR', 'YGG', 'CELO', 'ARKM', 'AR', 'STRK', 'METIS', 'AEVO'],
        "atr": {
            "sl_mult": 2.0,
            "tp1_mult": 3.5,
            "tp2_mult": 7.0,
            "tp3_mult": 9.0,
        },
        "ichimoku": {"tenkan": 12, "kijun": 29},
        "five_in_one": {"tenkan_5": 10, "kijun_5": 23},
        "displacement": 52,
        "avg_sharpe": 2.30,
        "avg_trades": 101,
    },
    "cluster_1": {
        "assets": ['EGLD', 'IMX', 'ANKR', 'W'],
        "atr": {
            "sl_mult": 5.0,
            "tp1_mult": 2.25,
            "tp2_mult": 5.5,
            "tp3_mult": 8.0,
        },
        "ichimoku": {"tenkan": 6, "kijun": 26},
        "five_in_one": {"tenkan_5": 10, "kijun_5": 26},
        "displacement": 52,
        "avg_sharpe": 2.26,
        "avg_trades": 86,
    },
}

# Asset to cluster mapping
ASSET_CLUSTER = {
    "ICP": "cluster_0",
    "HBAR": "cluster_0",
    "EGLD": "cluster_1",
    "IMX": "cluster_1",
    "YGG": "cluster_0",
    "CELO": "cluster_0",
    "ARKM": "cluster_0",
    "AR": "cluster_0",
    "ANKR": "cluster_1",
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