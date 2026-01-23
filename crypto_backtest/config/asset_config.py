"""Production asset configuration for the validated 5-asset portfolio.

Updated: 2026-01-22
All TP values are progressive: TP1 < TP2 < TP3 with min gap 0.5
"""

ASSET_CONFIG = {
    "BTC": {
        "pair": "BTC/USDT",
        "atr": {
            "sl_mult": 4.5,
            "tp1_mult": 4.25,
            "tp2_mult": 7.5,
            "tp3_mult": 9.5,
        },
        "ichimoku": {"tenkan": 6, "kijun": 37},
        "five_in_one": {"tenkan_5": 9, "kijun_5": 29},
        "displacement": 52,
        "filter_mode": "baseline",
    },
    "ETH": {
        "pair": "ETH/USDT",
        "atr": {
            "sl_mult": 4.5,
            "tp1_mult": 4.75,
            "tp2_mult": 7.0,
            "tp3_mult": 10.0,
        },
        "ichimoku": {"tenkan": 15, "kijun": 20},
        "five_in_one": {"tenkan_5": 13, "kijun_5": 22},
        "displacement": 52,
        "filter_mode": "medium_distance_volume",  # Winner from filter grid
    },
    "JOE": {
        "pair": "JOE/USDT",
        "atr": {
            "sl_mult": 3.75,
            "tp1_mult": 5.0,
            "tp2_mult": 8.0,
            "tp3_mult": 9.0,
        },
        "ichimoku": {"tenkan": 9, "kijun": 27},
        "five_in_one": {"tenkan_5": 8, "kijun_5": 30},
        "displacement": 26,
        "filter_mode": "baseline",
    },
    "OSMO": {
        "pair": "OSMO/USDT",
        "atr": {
            "sl_mult": 3.5,
            "tp1_mult": 2.75,
            "tp2_mult": 6.5,
            "tp3_mult": 10.0,
        },
        "ichimoku": {"tenkan": 10, "kijun": 31},
        "five_in_one": {"tenkan_5": 12, "kijun_5": 26},
        "displacement": 65,
        "filter_mode": "baseline",
    },
    "MINA": {
        "pair": "MINA/USDT",
        "atr": {
            "sl_mult": 2.75,
            "tp1_mult": 3.0,
            "tp2_mult": 8.5,
            "tp3_mult": 9.5,
        },
        "ichimoku": {"tenkan": 5, "kijun": 29},
        "five_in_one": {"tenkan_5": 14, "kijun_5": 29},
        "displacement": 78,
        "filter_mode": "baseline",
    },
}

EXEC_CONFIG = {
    "warmup_bars": 200,
    "fees_bps": 5,
    "slippage_bps": 2,
    "timeframe": "1H",
}
