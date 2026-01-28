"""Production asset configuration for the validated portfolio.

Updated: 2026-01-28 12:00 UTC
All TP values are progressive: TP1 < TP2 < TP3 with min gap 0.5

🎉 PR#21 COMPLETE — 100 Trials Standard (28 Jan 2026):
✅ ETH: 100% VALIDATED (8/8 guards, PBO 0.24, SIDEWAYS 1.98, Phase 4/5/6 PASS)
✅ SOL: 7/7 guards PASS (100T), Sharpe 2.96, WFE 1.27 — PENDING Phase 4

❌ PR#21 FAIL (100T, 28 Jan 2026):
- BTC: WFE 0.54 < 0.6 (overfit)
- AVAX: WFE 0.48 < 0.6 (overfit)

❌ EXCLUDED (26 Jan 2026) — Regime Stress Test FAIL:
- EGLD: SIDEWAYS Sharpe -4.59
- AVAX (old params): SIDEWAYS Sharpe -0.36

❌ FAILED RE-VALIDATION (need Phase 3A rescue or EXCLU):
- OSMO, AR, OP, METIS

VALID FILTER MODES:
- baseline: Ichimoku only (default)
- moderate: 5 filters
- conservative: 7 filters
"""

ASSET_CONFIG = {
    "BTC": {
        # ❌ FAIL PR#21 (28 Jan 2026, 100 trials)
        # WFE 0.54 < 0.6 (overfit), OOS Sharpe 1.65, Degradation 45.7%
        # Status: PENDING rescue (Phase 3A displacement or Phase 4 filters)
        "pair": "BTC/USDT",
        "atr": {
            "sl_mult": 4.25,
            "tp1_mult": 4.5,
            "tp2_mult": 8.0,
            "tp3_mult": 9.0,
        },
        "ichimoku": {"tenkan": 10, "kijun": 20},
        "five_in_one": {"tenkan_5": 13, "kijun_5": 29},
        "displacement": 52,
        "filter_mode": "baseline",
    },
    "ETH": {
        # 🎉 100% VALIDATED (28 Jan 2026, 100 trials + Phase 4/5/6)
        # 8/8 Guards PASS (Monte Carlo 0.002, Sensitivity 13.81%, Bootstrap 1.12,
        #                  Top10 25.31%, Stress1 1.11, Regime 0.00%, PBO 0.24, WFE 1.81)
        # Phase 4: SIDEWAYS Sharpe 1.98 (27 trades) ✅
        # Phase 5: Correlation 0.32 with SOL ✅
        # Phase 6: PBO (CSCV) 0.2416, PSR 98.4% ✅
        # OOS: Sharpe 3.21, Return +314.6%, MaxDD -1.04%, Trades 69
        # Status: PRODUCTION READY 🚀
        "pair": "ETH/USDT",
        "atr": {
            "sl_mult": 4.25,
            "tp1_mult": 2.25,
            "tp2_mult": 6.0,
            "tp3_mult": 10.0,
        },
        "ichimoku": {"tenkan": 13, "kijun": 20},
        "five_in_one": {"tenkan_5": 13, "kijun_5": 19},
        "displacement": 52,
        "filter_mode": "baseline",
    },
    "SOL": {
        # ✅ PR#21 SUCCESS (28 Jan 2026, 100 trials)
        # 7/7 Hard Guards PASS, WFE 1.27, OOS Sharpe 2.96
        # OOS: Return +291.9%, MaxDD -1.03%, Trades 96, PF 1.94
        # Status: PENDING Phase 4 (SIDEWAYS test) + Phase 5 (correlations)
        "pair": "SOL/USDT",
        "atr": {
            "sl_mult": 4.5,
            "tp1_mult": 2.5,
            "tp2_mult": 5.0,
            "tp3_mult": 8.5,
        },
        "ichimoku": {"tenkan": 11, "kijun": 25},
        "five_in_one": {"tenkan_5": 10, "kijun_5": 17},
        "displacement": 52,
        "filter_mode": "baseline",
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
        # ❌ FAIL PR#21 (28 Jan 2026, 100 trials)
        # WFE 0.48 < 0.6 (overfit), OOS Sharpe 2.05, Degradation 52.1%
        # Old params (26 Jan): EXCLUDED for Regime SIDEWAYS -0.36
        # New params (28 Jan 100T): Still FAIL WFE, needs rescue
        # Status: PENDING rescue (Phase 3A displacement or Phase 4 filters)
        "pair": "AVAX/USDT",
        "atr": {
            "sl_mult": 3.0,
            "tp1_mult": 1.5,
            "tp2_mult": 7.5,
            "tp3_mult": 10.0,
        },
        "ichimoku": {"tenkan": 20, "kijun": 32},
        "five_in_one": {"tenkan_5": 12, "kijun_5": 16},
        "displacement": 52,
        "filter_mode": "baseline",
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
