"""
Auto-generated Cluster Configuration
Generated: 2026-01-24T04:16:11.280098
Clusters found via K-means on optimized parameters
"""

CLUSTER_PARAMS = {
    "cluster_0": {
        "assets": ['TIA', 'CAKE', 'TON'],
        "atr": {
            "sl_mult": 3.25,
            "tp1_mult": 2.75,
            "tp2_mult": 8.5,
            "tp3_mult": 9.5,
        },
        "ichimoku": {"tenkan": 17, "kijun": 38},
        "five_in_one": {"tenkan_5": 10, "kijun_5": 21},
        "displacement": 52,
        "avg_sharpe": 3.39,
        "avg_trades": 78,
    },
    "cluster_1": {
        "assets": ['CRV', 'SUSHI', 'RUNE'],
        "atr": {
            "sl_mult": 2.5,
            "tp1_mult": 4.0,
            "tp2_mult": 6.5,
            "tp3_mult": 8.0,
        },
        "ichimoku": {"tenkan": 8, "kijun": 36},
        "five_in_one": {"tenkan_5": 12, "kijun_5": 17},
        "displacement": 52,
        "avg_sharpe": 1.78,
        "avg_trades": 106,
    },
}

# Asset to cluster mapping
ASSET_CLUSTER = {
    "CRV": "cluster_1",
    "SUSHI": "cluster_1",
    "RUNE": "cluster_1",
    "TIA": "cluster_0",
    "CAKE": "cluster_0",
    "TON": "cluster_0",
}


def get_params_for_asset(asset: str) -> dict:
    """Get cluster parameters for a given asset."""
    cluster_name = ASSET_CLUSTER.get(asset)
    if cluster_name is None:
        raise ValueError(f"Unknown asset: {asset}")
    return CLUSTER_PARAMS[cluster_name]