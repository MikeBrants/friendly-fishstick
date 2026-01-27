"""
Auto-generated Cluster Configuration
Generated: 2026-01-27T07:49:46.127816
Clusters found via K-means on optimized parameters
"""

CLUSTER_PARAMS = {
    "cluster_0": {
        "assets": ['DOT', 'TIA', 'NEAR'],
        "atr": {
            "sl_mult": 4.5,
            "tp1_mult": 3.0,
            "tp2_mult": 7.5,
            "tp3_mult": 8.5,
        },
        "ichimoku": {"tenkan": 7, "kijun": 34},
        "five_in_one": {"tenkan_5": 9, "kijun_5": 23},
        "displacement": 52,
        "avg_sharpe": 2.88,
        "avg_trades": 80,
    },
    "cluster_1": {
        "assets": ['SHIB'],
        "atr": {
            "sl_mult": 1.5,
            "tp1_mult": 4.75,
            "tp2_mult": 6.0,
            "tp3_mult": 8.0,
        },
        "ichimoku": {"tenkan": 19, "kijun": 26},
        "five_in_one": {"tenkan_5": 14, "kijun_5": 18},
        "displacement": 52,
        "avg_sharpe": 5.05,
        "avg_trades": 99,
    },
}

# Asset to cluster mapping
ASSET_CLUSTER = {
    "SHIB": "cluster_1",
    "DOT": "cluster_0",
    "TIA": "cluster_0",
    "NEAR": "cluster_0",
}


def get_params_for_asset(asset: str) -> dict:
    """Get cluster parameters for a given asset."""
    cluster_name = ASSET_CLUSTER.get(asset)
    if cluster_name is None:
        raise ValueError(f"Unknown asset: {asset}")
    return CLUSTER_PARAMS[cluster_name]