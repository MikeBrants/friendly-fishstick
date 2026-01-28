"""Production asset configuration for the validated portfolio.

Updated: 2026-01-28 13:00 UTC
All TP values are progressive: TP1 < TP2 < TP3 with min gap 0.5

🎉 PR#21 COMPLETE — 100 Trials Standard Validated (28 Jan 2026)

✅ TIER 1 PROD (5 assets) — All guards PASS + PBO < 0.50:
- ETH: PBO 0.13 (CSCV 0.24), Sharpe 3.21, Phase 4/5/6 ✅
- AVAX: PBO 0.13, Sharpe 2.05 (Challenger 100T)
- SOL: PBO 0.33, Sharpe 2.96 (Challenger 100T)
- YGG: PBO 0.40, Sharpe 3.40 (PR#21 100T, -52.5% vs 300T) ⭐
- AXS: PBO 0.33, Sharpe 1.21 (PR#20 300T)

🔴 TIER 2 EXCLUDED (28 Jan 2026, 13:15 UTC) — Elevated PBO risk:
- EGLD: PBO 0.53, Sharpe 2.08 (all guards PASS but PBO borderline)
- SUSHI: PBO 0.60, Sharpe 2.51 (all guards PASS but PBO borderline)
- MINA: PBO 0.53, Sharpe 2.12 (all guards PASS but PBO borderline)
Decision: EXCLUDED - Conservative approach, strict PBO < 0.50 threshold

🔴 TIER 3 EXCLU (4 assets) — PBO critical or guards FAIL:
- CAKE: PBO 0.93 (critical overfitting)
- CRV: PBO 0.87 + guards FAIL
- TON: PBO 0.60 + guards FAIL (4/7)
- HBAR: PBO 0.60 + guards FAIL (5/7)

FILTER MODES:
- baseline: Ichimoku only (default, all PROD use this)
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
        # 🔴 TIER 2 EXCLUDED (28 Jan 2026, 13:15 UTC)
        # PBO 0.53 (borderline, above 0.50 threshold)
        # All guards PASS, OOS Sharpe 2.12, improved -24% vs 300T
        # Decision: EXCLUDED - Conservative approach, elevated overfitting risk
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
        # 🔴 TIER 3 EXCLU (28 Jan 2026, PR#21 100T)
        # PBO 0.93 (CRITICAL overfitting), improved -5% vs 300T (0.98 → 0.93)
        # All guards PASS but PBO critical → EXCLUDED
        # OOS Sharpe: 2.56
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
        # 🔴 TIER 2 EXCLUDED (28 Jan 2026, 13:15 UTC)
        # PBO 0.53 (borderline, above 0.50 threshold)
        # All guards PASS, OOS Sharpe 2.08, improved -20% vs 300T
        # Decision: EXCLUDED - Conservative approach, elevated overfitting risk
        # Note: Old params (26 Jan) FAILED Regime SIDEWAYS -4.59
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
    "SUSHI": {
        # 🔴 TIER 2 EXCLUDED (28 Jan 2026, 13:15 UTC)
        # PBO 0.60 (elevated risk, above 0.50 threshold)
        # All guards PASS, OOS Sharpe 2.51, improved -18% vs 300T
        # Decision: EXCLUDED - Conservative approach, elevated overfitting risk
        "pair": "SUSHI/USDT",
        "atr": {
            "sl_mult": 3.5,
            "tp1_mult": 2.5,
            "tp2_mult": 6.0,
            "tp3_mult": 9.0,
        },
        "ichimoku": {"tenkan": 12, "kijun": 28},
        "five_in_one": {"tenkan_5": 10, "kijun_5": 18},
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
        # 🎉 TIER 1 PROD (28 Jan 2026, PR#21 100T)
        # PBO 0.40 (PASS), improved -52.5% vs 300T (0.84 → 0.40) ⭐
        # All guards PASS, OOS Sharpe 3.40, WFE 0.89, Trades 72
        # Status: PRODUCTION READY
        "pair": "YGG/USDT",
        "atr": {
            "sl_mult": 4.25,
            "tp1_mult": 2.75,
            "tp2_mult": 7.5,
            "tp3_mult": 8.5,  # Updated from 9.5 (PR#21 100T)
        },
        "ichimoku": {"tenkan": 7, "kijun": 23},  # Updated (PR#21 100T)
        "five_in_one": {"tenkan_5": 8, "kijun_5": 17},
        "displacement": 52,
        "filter_mode": "baseline",
    },
    "AXS": {
        # ✅ TIER 1 PROD (PR#20 300T, validated with PBO)
        # PBO 0.33 (PASS), OOS Sharpe 1.21
        # Status: PRODUCTION READY
        "pair": "AXS/USDT",
        "atr": {
            "sl_mult": 2.5,
            "tp1_mult": 2.0,
            "tp2_mult": 4.5,
            "tp3_mult": 7.5,
        },
        "ichimoku": {"tenkan": 7, "kijun": 20},
        "five_in_one": {"tenkan_5": 10, "kijun_5": 21},
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
