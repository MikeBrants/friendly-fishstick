"""Production asset configuration for the validated 3-asset portfolio."""

ASSET_CONFIG = {
    "BTC": {
        "pair": "BTC/USDT",
        "atr": {
            "sl_mult": 3.75,
            "tp1_mult": 3.75,
            "tp2_mult": 9.0,
            "tp3_mult": 7.0,
        },
        "ichimoku": {"tenkan": 13, "kijun": 34},
        "five_in_one": {"tenkan_5": 12, "kijun_5": 21},
        "displacement": 52,
    },
    "ETH": {
        "pair": "ETH/USDT",
        "atr": {
            "sl_mult": 5.0,
            "tp1_mult": 5.0,
            "tp2_mult": 3.0,
            "tp3_mult": 8.0,
        },
        "ichimoku": {"tenkan": 7, "kijun": 26},
        "five_in_one": {"tenkan_5": 13, "kijun_5": 25},
        "displacement": 52,
    },
    "XRP": {
        "pair": "XRP/USDT",
        "atr": {
            "sl_mult": 4.0,
            "tp1_mult": 5.0,
            "tp2_mult": 3.0,
            "tp3_mult": 5.0,
        },
        "ichimoku": {"tenkan": 10, "kijun": 32},
        "five_in_one": {"tenkan_5": 9, "kijun_5": 20},
        "displacement": 52,
    },
}

EXEC_CONFIG = {
    "warmup_bars": 200,
    "fees_bps": 5,
    "slippage_bps": 2,
    "timeframe": "1H",
}
