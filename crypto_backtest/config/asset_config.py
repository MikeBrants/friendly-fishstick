"""Production asset configuration for the validated portfolio.

Updated: 2026-01-26 16:30 UTC
All TP values are progressive: TP1 < TP2 < TP3 with min gap 0.5

NOTE: TIA and CAKE reclassified from Phase 4 to Phase 2 post-PR#8 (guard002 threshold 15%)

✅ RESET COMPLETE (25 Jan 2026, 15:30 UTC):
- ETH: baseline PASS (Sharpe 3.22, WFE 1.22)
- MINA: baseline PASS (Sharpe 2.58, WFE 1.13) — NEW params
- YGG: baseline PASS (Sharpe 3.11, WFE 0.78) — NEW params
- RUNE: baseline PASS (Sharpe 2.42, WFE 0.61) — params completed

❌ EXCLUDED (26 Jan 2026, 16:30 UTC) — Regime Stress Test FAIL:
- EGLD: SIDEWAYS Sharpe -4.59 (Issue #17 TASK 3)
- AVAX: SIDEWAYS Sharpe -0.36 (Issue #17 TASK 3)

❌ FAILED RE-VALIDATION (need Phase 3A rescue or EXCLU):
- OSMO: Sharpe 0.68, WFE 0.19 — SEVERE OVERFIT
- AR: WFE 0.39, Trades 41 — WFE + low trades
- OP: Sharpe 0.03, WFE 0.01 — SEVERE FAIL (likely EXCLU)
- METIS: WFE 0.48 — overfit

VALID FILTER MODES (NEW SYSTEM):
- baseline: Ichimoku only (default)
- moderate: 5 filters (distance, volume, regression, kama, ichimoku)
- conservative: 7 filters (all + strict ichimoku)

OBSOLETE MODES (DO NOT USE):
- medium_distance_volume, light_kama, light_distance, light_volume,
- light_regression, medium_kama_distance, medium_kama_volume, medium_kama_regression
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
        # ✅ RESET COMPLETE (25 Jan 2026, 14:40 UTC)
        # Migrated from OBSOLETE 'medium_distance_volume' to 'baseline'
        # Results: OOS Sharpe 3.22, WFE 1.22, Trades 72, MC p=0.006
        "pair": "ETH/USDT",
        "atr": {
            "sl_mult": 3.0,
            "tp1_mult": 5.0,
            "tp2_mult": 6.0,
            "tp3_mult": 7.5,
        },
        "ichimoku": {"tenkan": 12, "kijun": 36},
        "five_in_one": {"tenkan_5": 8, "kijun_5": 17},
        "displacement": 52,
        "filter_mode": "baseline",  # Valid mode (was medium_distance_volume)
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
        # ❌ FAILED RE-VALIDATION (25 Jan 2026) — NEEDS RESCUE
        # Sharpe 0.68 (< 1.0), WFE 0.19 (< 0.6) — SEVERE OVERFIT
        # Old params kept for reference, Phase 3A rescue required
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
        # "status": "PENDING_RESCUE",
    },
    "MINA": {
        # ✅ RE-VALIDATED (25 Jan 2026, 15:20 UTC)
        # OOS Sharpe 2.58, WFE 1.13, Trades 60, 7/7 guards PASS
        "pair": "MINA/USDT",
        "atr": {
            "sl_mult": 4.25,
            "tp1_mult": 3.0,
            "tp2_mult": 7.5,
            "tp3_mult": 9.0,
        },
        "ichimoku": {"tenkan": 9, "kijun": 26},
        "five_in_one": {"tenkan_5": 14, "kijun_5": 25},
        "displacement": 52,
        "filter_mode": "baseline",
    },
    "AVAX": {
        # ❌ EXCLUDED (26 Jan 2026, 16:30 UTC) — Regime Stress Test FAIL
        # Baseline FAILED (WFE 0.51), MODERATE PASSED (25 Jan 2026)
        # Results: OOS Sharpe 2.00, WFE 0.66, Trades 81, Sensitivity 2.77%
        # ⚠️ REGIME STRESS TEST FAIL: SIDEWAYS Sharpe -0.36 (75 trades, 25.3% win rate)
        # Decision: EXCLUDED from PROD portfolio (Issue #17 TASK 3)
        "pair": "AVAX/USDT",
        "atr": {
            "sl_mult": 3.0,
            "tp1_mult": 4.75,
            "tp2_mult": 8.5,
            "tp3_mult": 9.0,
        },
        "ichimoku": {"tenkan": 9, "kijun": 22},
        "five_in_one": {"tenkan_5": 8, "kijun_5": 17},
        "displacement": 52,
        "filter_mode": "moderate",  # Baseline failed WFE, moderate PASS
    },
    "AR": {
        # ❌ FAILED RE-VALIDATION (25 Jan 2026) — NEEDS RESCUE
        # WFE 0.39 (< 0.6), Trades 41 (< 50) — overfit + low sample
        # Old params kept for reference, Phase 3A rescue required
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
        # "status": "PENDING_RESCUE",
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
        # ❌ SEVERE FAIL RE-VALIDATION (25 Jan 2026) — LIKELY EXCLU
        # Sharpe 0.03, WFE 0.01 — ALL CRITERIA FAIL
        # Candidate for EXCLUSION, rescue unlikely to help
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
        # "status": "LIKELY_EXCLU",
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
        # ✅ RESET COMPLETE (25 Jan 2026, 14:10 UTC)
        # Phase 2 validation: 7/7 guards PASS
        # Variance: 3.23% < 15% → PASS
        # OOS Sharpe: 2.42, WFE: 0.61, Trades: 102, MC p=0.0
        "pair": "RUNE/USDT",
        "atr": {
            "sl_mult": 1.5,
            "tp1_mult": 4.75,
            "tp2_mult": 8.0,
            "tp3_mult": 10.0,
        },
        "ichimoku": {"tenkan": 5, "kijun": 38},
        "five_in_one": {"tenkan_5": 14, "kijun_5": 15},
        "displacement": 52,
        "filter_mode": "baseline",
    },
    "EGLD": {
        # ❌ EXCLUDED (26 Jan 2026, 16:30 UTC) — Regime Stress Test FAIL
        # Phase 2 validation: 7/7 guards PASS (baseline)
        # Variance: 5.01% < 15% → PASS
        # OOS Sharpe: 2.13, WFE: 0.69, Trades: 91, MC p=0.01
        # ⚠️ REGIME STRESS TEST FAIL: SIDEWAYS Sharpe -4.59 (60 trades, 35% win rate)
        # ⚠️ MARKDOWN also negative: -5.15 Sharpe (6 trades)
        # Decision: EXCLUDED from PROD portfolio (Issue #17 TASK 3)
        "pair": "EGLD/USDT",
        "atr": {
            "sl_mult": 5.0,
            "tp1_mult": 1.75,
            "tp2_mult": 4.0,
            "tp3_mult": 5.5,
        },
        "ichimoku": {"tenkan": 5, "kijun": 28},
        "five_in_one": {"tenkan_5": 8, "kijun_5": 19},
        "displacement": 52,
        "filter_mode": "baseline",
    },
    "METIS": {
        # ❌ FAILED RE-VALIDATION (25 Jan 2026) — NEEDS RESCUE
        # WFE 0.48 (< 0.6), Sharpe 1.59 — overfit detected
        # Old params kept for reference, Phase 3A rescue required
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
        # "status": "PENDING_RESCUE",
    },
    "YGG": {
        # ✅ RE-VALIDATED (25 Jan 2026, 15:20 UTC)
        # OOS Sharpe 3.11, WFE 0.78, Trades 78, 7/7 guards PASS
        "pair": "YGG/USDT",
        "atr": {
            "sl_mult": 4.25,
            "tp1_mult": 2.75,
            "tp2_mult": 7.5,
            "tp3_mult": 9.5,
        },
        "ichimoku": {"tenkan": 10, "kijun": 20},
        "five_in_one": {"tenkan_5": 8, "kijun_5": 17},
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
