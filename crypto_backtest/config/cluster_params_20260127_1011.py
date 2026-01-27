"""
Auto-generated Cluster Configuration
Generated: 2026-01-27T10:11:07.750436
Clusters found via K-means on optimized parameters
"""

CLUSTER_PARAMS = {
    "cluster_0": {
        "assets": ['YGG', 'EGLD', 'SOL'],
        "atr": {
            "sl_mult": 4.5,
            "tp1_mult": 2.25,
            "tp2_mult": 4.5,
            "tp3_mult": 7.0,
        },
        "ichimoku": {"tenkan": 8, "kijun": 22},
        "five_in_one": {"tenkan_5": 8, "kijun_5": 20},
        "displacement": 52,
        "avg_sharpe": 2.91,
        "avg_trades": 87,
    },
    "cluster_1": {
        "assets": ['CAKE', 'TON'],
        "atr": {
            "sl_mult": 3.5,
            "tp1_mult": 3.0,
            "tp2_mult": 8.5,
            "tp3_mult": 10.0,
        },
        "ichimoku": {"tenkan": 19, "kijun": 38},
        "five_in_one": {"tenkan_5": 9, "kijun_5": 23},
        "displacement": 52,
        "avg_sharpe": 1.78,
        "avg_trades": 76,
    },
    "cluster_2": {
        "assets": ['MINA', 'CRV'],
        "atr": {
            "sl_mult": 3.0,
            "tp1_mult": 3.5,
            "tp2_mult": 7.0,
            "tp3_mult": 9.0,
        },
        "ichimoku": {"tenkan": 14, "kijun": 24},
        "five_in_one": {"tenkan_5": 14, "kijun_5": 27},
        "displacement": 52,
        "avg_sharpe": 1.87,
        "avg_trades": 78,
    },
    "cluster_3": {
        "assets": ['HBAR', 'ONE'],
        "atr": {
            "sl_mult": 1.5,
            "tp1_mult": 3.75,
            "tp2_mult": 5.5,
            "tp3_mult": 9.0,
        },
        "ichimoku": {"tenkan": 7, "kijun": 24},
        "five_in_one": {"tenkan_5": 11, "kijun_5": 16},
        "displacement": 52,
        "avg_sharpe": 2.47,
        "avg_trades": 114,
    },
}

# Asset to cluster mapping
ASSET_CLUSTER = {
    "YGG": "cluster_0",
    "MINA": "cluster_2",
    "CAKE": "cluster_1",
    "EGLD": "cluster_0",
    "HBAR": "cluster_3",
    "TON": "cluster_1",
    "CRV": "cluster_2",
    "ONE": "cluster_3",
    "SOL": "cluster_0",
}


def get_params_for_asset(asset: str) -> dict:
    """Get cluster parameters for a given asset."""
    cluster_name = ASSET_CLUSTER.get(asset)
    if cluster_name is None:
        raise ValueError(f"Unknown asset: {asset}")
    return CLUSTER_PARAMS[cluster_name]