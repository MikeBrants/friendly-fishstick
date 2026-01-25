"""Production asset configuration for the validated portfolio.

Updated: 2026-01-25 10:15
All TP values are progressive: TP1 < TP2 < TP3 with min gap 0.5

NOTE: TIA and CAKE reclassified from Phase 4 to Phase 2 post-PR#8 (guard002 threshold 15%)
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
    "AVAX": {
        "pair": "AVAX/USDT",
        "atr": {
            "sl_mult": 2.75,
            "tp1_mult": 1.5,
            "tp2_mult": 7.5,
            "tp3_mult": 9.5,
        },
        "ichimoku": {"tenkan": 7, "kijun": 32},
        "five_in_one": {"tenkan_5": 15, "kijun_5": 27},
        "displacement": 52,
        "filter_mode": "medium_distance_volume",  # Winner from filter grid
    },
    "AR": {
        "pair": "AR/USDT",
        "atr": {
            "sl_mult": 1.5,
            "tp1_mult": 4.0,
            "tp2_mult": 5.5,
            "tp3_mult": 8.0,
        },
        "ichimoku": {"tenkan": 8, "kijun": 31},
        "five_in_one": {"tenkan_5": 9, "kijun_5": 22},
        "displacement": 52,
        "filter_mode": "baseline",
    },
    "ANKR": {
        "pair": "ANKR/USDT",
        "atr": {
            "sl_mult": 5.0,
            "tp1_mult": 2.0,
            "tp2_mult": 8.0,
            "tp3_mult": 9.5,
        },
        "ichimoku": {"tenkan": 20, "kijun": 25},
        "five_in_one": {"tenkan_5": 16, "kijun_5": 25},
        "displacement": 52,
        "filter_mode": "baseline",
    },
    "DOGE": {
        "pair": "DOGE/USDT",
        "atr": {
            "sl_mult": 3.25,
            "tp1_mult": 1.5,
            "tp2_mult": 6.0,
            "tp3_mult": 9.0,
        },
        "ichimoku": {"tenkan": 15, "kijun": 39},
        "five_in_one": {"tenkan_5": 15, "kijun_5": 17},
        "displacement": 26,
        "filter_mode": "baseline",
    },
    "OP": {
        "pair": "OP/USDT",
        "atr": {
            "sl_mult": 4.5,
            "tp1_mult": 2.25,
            "tp2_mult": 3.0,
            "tp3_mult": 8.5,
        },
        "ichimoku": {"tenkan": 12, "kijun": 36},
        "five_in_one": {"tenkan_5": 9, "kijun_5": 23},
        "displacement": 78,
        "filter_mode": "baseline",
    },
    "DOT": {
        "pair": "DOT/USDT",
        "atr": {
            "sl_mult": 2.5,
            "tp1_mult": 5.0,
            "tp2_mult": 5.5,
            "tp3_mult": 10.0,
        },
        "ichimoku": {"tenkan": 12, "kijun": 21},
        "five_in_one": {"tenkan_5": 8, "kijun_5": 27},
        "displacement": 52,
        "filter_mode": "baseline",
    },
    "NEAR": {
        "pair": "NEAR/USDT",
        "atr": {
            "sl_mult": 5.0,
            "tp1_mult": 3.25,
            "tp2_mult": 9.0,
            "tp3_mult": 9.5,
        },
        "ichimoku": {"tenkan": 8, "kijun": 32},
        "five_in_one": {"tenkan_5": 9, "kijun_5": 28},
        "displacement": 52,
        "filter_mode": "baseline",
    },
    "SHIB": {
        "pair": "SHIB/USDT",
        "atr": {
            "sl_mult": 1.5,
            "tp1_mult": 4.75,
            "tp2_mult": 6.0,
            "tp3_mult": 8.0,
        },
        "ichimoku": {"tenkan": 19, "kijun": 25},
        "five_in_one": {"tenkan_5": 14, "kijun_5": 16},
        "displacement": 52,
        "filter_mode": "baseline",
    },
    "TIA": {
        # Reclassified from Phase 4 to Phase 2 baseline post-PR#8 (guard002 threshold 15%)
        # Phase 2 validation: 2026-01-24 14:33:37
        # Variance: 11.49% < 15% threshold → PASS
        # OOS Sharpe: 5.16, WFE: 1.36, Trades: 75
        "pair": "TIA/USDT",
        "atr": {
            "sl_mult": 5.0,
            "tp1_mult": 2.5,
            "tp2_mult": 9.0,
            "tp3_mult": 9.5,
        },
        "ichimoku": {"tenkan": 13, "kijun": 38},
        "five_in_one": {"tenkan_5": 12, "kijun_5": 18},
        "displacement": 52,
        "filter_mode": "baseline",
    },
    "CAKE": {
        # Reclassified from Phase 4 to Phase 2 baseline post-PR#8 (guard002 threshold 15%)
        # Phase 2 validation: 2026-01-24 14:46:04
        # Variance: 10.76% < 15% threshold → PASS
        # OOS Sharpe: 2.46, WFE: 0.81, Trades: 90
        "pair": "CAKE/USDT",
        "atr": {
            "sl_mult": 2.25,
            "tp1_mult": 3.75,
            "tp2_mult": 9.0,
            "tp3_mult": 10.0,
        },
        "ichimoku": {"tenkan": 19, "kijun": 40},
        "five_in_one": {"tenkan_5": 8, "kijun_5": 22},
        "displacement": 52,
        "filter_mode": "baseline",
    },
    "RUNE": {
        # Phase 2 validation: 2026-01-24
        # Variance: 3.23% < 15% → PASS
        # OOS Sharpe: TBD, WFE: 0.61, Trades: TBD
        "pair": "RUNE/USDT",
        "atr": {
            "sl_mult": 0.0,  # TBD from scan
            "tp1_mult": 0.0,
            "tp2_mult": 0.0,
            "tp3_mult": 0.0,
        },
        "ichimoku": {"tenkan": 0, "kijun": 0},
        "five_in_one": {"tenkan_5": 0, "kijun_5": 0},
        "displacement": 52,
        "filter_mode": "baseline",
    },
    "EGLD": {
        # Phase 2 validation: 2026-01-24
        # Variance: 5.04% < 15% → PASS
        # OOS Sharpe: TBD, WFE: 0.66, Trades: TBD
        "pair": "EGLD/USDT",
        "atr": {
            "sl_mult": 0.0,  # TBD from scan
            "tp1_mult": 0.0,
            "tp2_mult": 0.0,
            "tp3_mult": 0.0,
        },
        "ichimoku": {"tenkan": 0, "kijun": 0},
        "five_in_one": {"tenkan_5": 0, "kijun_5": 0},
        "displacement": 52,
        "filter_mode": "baseline",
    },
    "METIS": {
        "pair": "METIS/USDT",
        "atr": {
            "sl_mult": 1.5,
            "tp1_mult": 4.75,
            "tp2_mult": 7.5,
            "tp3_mult": 9.5,
        },
        "ichimoku": {"tenkan": 16, "kijun": 20},
        "five_in_one": {"tenkan_5": 8, "kijun_5": 17},
        "displacement": 52,
        "filter_mode": "baseline",
    },
    "YGG": {
        "pair": "YGG/USDT",
        "atr": {
            "sl_mult": 1.5,
            "tp1_mult": 5.0,
            "tp2_mult": 7.5,
            "tp3_mult": 9.0,
        },
        "ichimoku": {"tenkan": 11, "kijun": 39},
        "five_in_one": {"tenkan_5": 12, "kijun_5": 24},
        "displacement": 52,
        "filter_mode": "baseline",
    },
}

EXEC_CONFIG = {
    "warmup_bars": 200,
    "fees_bps": 5,
    "slippage_bps": 2,
    "timeframe": "1H",
}
