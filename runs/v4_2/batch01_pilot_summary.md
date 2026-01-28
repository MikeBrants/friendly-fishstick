# V4.2 Batch Pilot Summary - Run ID: v4.2_batch01_k5
## Date: 2026-01-28 | Status: COMPLETE

---

## Executive Summary

- Orchestrator fixes verified: guards stop pipeline, summary.json created, logging working, family upgrades executed.
- BTC blocked on WFE guard; SHIB blocked on top10_concentration guard.
- DOT and ANKR reached PROD_READY using moderate preset (Family C).
- PBO CSCV remains elevated (0.58 - 0.63) for DOT/ANKR.

---

## Asset Results Summary

| Asset | Verdict | WFE | OOS Sharpe | Trades | PBO CSCV | Filter Preset | Issues |
|------|---------|-----|------------|--------|----------|---------------|--------|
| BTC | BLOCKED | 0.36 | 0.84 | 133 | N/A | baseline | WFE guard fail (0.36 < 0.60) |
| SHIB | BLOCKED | 2.00 | 2.05 | 166 | N/A | baseline | top10_concentration guard fail |
| DOT | PROD_READY | 1.71 | 2.46 | 139 | 0.58 | moderate | WFE > 1.0 suspect |
| ANKR | PROD_READY | 0.65 | 1.89 | 160 | 0.63 | moderate | PBO warning (> 0.60) |

---

## Fixes Verified

| Fix | Status | Evidence |
|-----|--------|----------|
| Guards stop pipeline | FIXED | BTC stopped after guards fail; summary.json created |
| summary.json creation | FIXED | Summary saved for all 4 assets |
| PBO proxy removed | FIXED | Only CSCV reported in summary.json |
| Logging | FIXED | logs/orchestrator_*_v4.2_batch01_k5_*.log present |
| Family upgrades | FIXED | DOT/ANKR upgraded; moderate preset used |

---

## Observations

- DOT WFE = 1.71 (moderate preset) remains statistically suspect.
- PBO CSCV > 0.60 for DOT/ANKR indicates elevated overfitting risk.

---

## Next

- Consider lowering search complexity further (k=3 or narrower search space).
- Decide policy for PBO > 0.60 (warn vs block).
