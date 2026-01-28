"""
Auto-generated Cluster Configuration
Generated: 2026-01-27T20:35:14.301238
Clusters found via K-means on optimized parameters
"""

CLUSTER_PARAMS = {
    "cluster_0": {
        "assets": ['EGLD', 'TON', 'SUSHI', 'MINA', 'YGG', 'CAKE'],
        "atr": {
            "sl_mult": 4.0,
            "tp1_mult": 3.0,
            "tp2_mult": 7.0,
            "tp3_mult": 8.5,
        },
        "ichimoku": {"tenkan": 8, "kijun": 32},
        "five_in_one": {"tenkan_5": 8, "kijun_5": 22},
        "displacement": 52,
        "avg_sharpe": 2.35,
        "avg_trades": 78,
    },
    "cluster_1": {
        "assets": ['ETH', 'HBAR', 'CRV'],
        "atr": {
            "sl_mult": 2.5,
            "tp1_mult": 2.5,
            "tp2_mult": 6.0,
            "tp3_mult": 9.5,
        },
        "ichimoku": {"tenkan": 14, "kijun": 25},
        "five_in_one": {"tenkan_5": 13, "kijun_5": 19},
        "displacement": 52,
        "avg_sharpe": 2.62,
        "avg_trades": 93,
    },
}

# Asset to cluster mapping
ASSET_CLUSTER = {
    "ETH": "cluster_1",
    "EGLD": "cluster_0",
    "TON": "cluster_0",
    "HBAR": "cluster_1",
    "SUSHI": "cluster_0",
    "CRV": "cluster_1",
    "MINA": "cluster_0",
    "YGG": "cluster_0",
    "CAKE": "cluster_0",
}


def get_params_for_asset(asset: str) -> dict:
    """Get cluster parameters for a given asset."""
    cluster_name = ASSET_CLUSTER.get(asset)
    if cluster_name is None:
        raise ValueError(f"Unknown asset: {asset}")
    return CLUSTER_PARAMS[cluster_name]