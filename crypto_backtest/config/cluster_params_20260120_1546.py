"""
Auto-generated Cluster Configuration
Generated: 2026-01-20T15:46:30.757073
Clusters found via K-means on optimized parameters
"""

CLUSTER_PARAMS = {
    "cluster_0": {
        "assets": ['BTC', 'UNI', 'SUI', 'SEI'],
        "atr": {
            "sl_mult": 3.5,
            "tp1_mult": 4.5,
            "tp2_mult": 6.5,
            "tp3_mult": 9.0,
        },
        "ichimoku": {"tenkan": 10, "kijun": 29},
        "five_in_one": {"tenkan_5": 8, "kijun_5": 29},
        "displacement": 52,
        "avg_sharpe": 3.07,
        "avg_trades": 74,
    },
    "cluster_1": {
        "assets": ['ETH', 'AVAX'],
        "atr": {
            "sl_mult": 3.5,
            "tp1_mult": 3.0,
            "tp2_mult": 7.0,
            "tp3_mult": 6.0,
        },
        "ichimoku": {"tenkan": 18, "kijun": 27},
        "five_in_one": {"tenkan_5": 12, "kijun_5": 18},
        "displacement": 52,
        "avg_sharpe": 4.09,
        "avg_trades": 96,
    },
}

# Asset to cluster mapping
ASSET_CLUSTER = {
    "BTC": "cluster_0",
    "ETH": "cluster_1",
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