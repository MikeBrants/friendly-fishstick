"""
Auto-generated Cluster Configuration
Generated: 2026-01-23T22:43:09.185301
Clusters found via K-means on optimized parameters
"""

CLUSTER_PARAMS = {
    "cluster_0": {
        "assets": ['CRV', 'ONE'],
        "atr": {
            "sl_mult": 2.0,
            "tp1_mult": 4.5,
            "tp2_mult": 6.0,
            "tp3_mult": 9.5,
        },
        "ichimoku": {"tenkan": 14, "kijun": 33},
        "five_in_one": {"tenkan_5": 9, "kijun_5": 18},
        "displacement": 52,
        "avg_sharpe": 2.34,
        "avg_trades": 108,
    },
    "cluster_1": {
        "assets": ['ZIL'],
        "atr": {
            "sl_mult": 1.5,
            "tp1_mult": 5.0,
            "tp2_mult": 8.0,
            "tp3_mult": 10.0,
        },
        "ichimoku": {"tenkan": 13, "kijun": 26},
        "five_in_one": {"tenkan_5": 8, "kijun_5": 25},
        "displacement": 52,
        "avg_sharpe": 1.33,
        "avg_trades": 120,
    },
}

# Asset to cluster mapping
ASSET_CLUSTER = {
    "CRV": "cluster_0",
    "ONE": "cluster_0",
    "ZIL": "cluster_1",
}


def get_params_for_asset(asset: str) -> dict:
    """Get cluster parameters for a given asset."""
    cluster_name = ASSET_CLUSTER.get(asset)
    if cluster_name is None:
        raise ValueError(f"Unknown asset: {asset}")
    return CLUSTER_PARAMS[cluster_name]