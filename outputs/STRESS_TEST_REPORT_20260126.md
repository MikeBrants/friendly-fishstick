# Regime Stress Test Report - FINAL TRIGGER v2

**Date:** 26 janvier 2026, 16:15 UTC  
**Issue:** #17 (Regime-Robust Validation Framework)  
**TASK:** 3 - Isolated Regime Stress Tests  
**Owner:** Jordan

---

## Executive Summary

Tested 14 PROD assets on two critical regimes:
- **MARKDOWN** (bear market): Strategy naturally avoids entries
- **SIDEWAYS** (range-bound, variable %): 12 PASS, 2 FAIL

**Critical Finding:** EGLD and AVAX FAIL on SIDEWAYS regime.

---

## MARKDOWN Stress Test Results

**Finding:** The Ichimoku strategy has a **built-in bear filter** that prevents entries during MARKDOWN.

| Asset | MARKDOWN % | Total Trades | MARKDOWN Trades | Status |
|-------|------------|--------------|-----------------|--------|
| SHIB | 9.1% | 558 | 0 | SKIP |
| DOT | 9.0% | 558 | 3 | SKIP |
| TIA | 14.3% | 399 | 6 | INCONCLUSIVE |
| NEAR | 11.0% | 393 | 3 | SKIP |
| DOGE | 9.1% | 552 | 0 | SKIP |
| ANKR | 10.2% | 423 | 3 | SKIP |
| ETH | 6.1% | 459 | 0 | SKIP |
| JOE | 11.3% | 408 | 0 | SKIP |
| YGG | 12.3% | 414 | 3 | SKIP |
| MINA | 11.6% | 381 | 3 | SKIP |
| CAKE | 9.4% | 459 | 9 | INCONCLUSIVE |
| RUNE | 10.6% | 516 | 3 | SKIP |
| EGLD | 10.2% | 523 | 6 | INCONCLUSIVE |
| AVAX | 9.9% | 465 | 3 | SKIP |

**Interpretation:**
- 0-3 trades per asset during MARKDOWN = strategy avoids bear markets
- This is a POSITIVE finding for robustness
- EGLD showed negative Sharpe (-5.15) on 6 trades (warning signal)

---

## SIDEWAYS Stress Test Results

**Finding:** 12/14 assets perform well in SIDEWAYS; EGLD and AVAX FAIL.

| Asset | SIDEWAYS % | Trades | Sharpe | Max DD | Win Rate | Status |
|-------|------------|--------|--------|--------|----------|--------|
| SHIB | 16.9% | 57 | 3.29 | 6.37% | 33.3% | PASS |
| DOT | 29.1% | 78 | 3.54 | 6.34% | 46.2% | PASS |
| TIA | 27.7% | 42 | 10.32 | 1.02% | 54.8% | PASS |
| NEAR | 27.0% | 51 | 3.39 | 3.60% | 54.9% | PASS |
| DOGE | 17.7% | 81 | 1.38 | 3.49% | 40.7% | PASS |
| ANKR | 17.0% | 36 | 8.00 | 1.06% | 52.8% | PASS |
| ETH | 39.0% | 81 | 1.78 | 2.43% | 38.3% | PASS |
| JOE | 18.5% | 54 | 6.15 | 3.07% | 48.1% | PASS |
| YGG | 18.5% | 36 | 9.47 | 1.53% | 61.1% | PASS |
| MINA | 18.8% | 39 | 4.66 | 2.04% | 46.2% | PASS |
| CAKE | 27.0% | 51 | 4.79 | 3.10% | 35.3% | PASS |
| RUNE | 26.6% | 45 | 2.39 | 6.45% | 22.2% | PASS |
| **EGLD** | 34.8% | 60 | **-4.59** | 4.29% | 35.0% | **FAIL** |
| **AVAX** | 35.0% | 75 | **-0.36** | 6.55% | 25.3% | **FAIL** |

**Statistics:**
- PASS: 12 assets (85.7%)
- FAIL: 2 assets (14.3%)
- Mean Sharpe (all): 3.87
- Mean SIDEWAYS %: 25.3%

---

## Critical Alerts

### EGLD - FAIL
- **SIDEWAYS Sharpe:** -4.59
- **Trades:** 60
- **Win Rate:** 35%
- **MARKDOWN signal:** Also showed -5.15 Sharpe on 6 trades

**Recommendation:** REVIEW for EXCLU - asset underperforms in key regimes.

### AVAX - FAIL
- **SIDEWAYS Sharpe:** -0.36
- **Trades:** 75
- **Win Rate:** 25.3%
- **Note:** Already flagged for WFE issues in prior validation

**Recommendation:** REVIEW for EXCLU - strategy not profitable on this asset.

---

## Recommendations

### Immediate Actions
1. **EGLD**: Move to PENDING or EXCLU (fails SIDEWAYS + MARKDOWN signals)
2. **AVAX**: Move to PENDING or EXCLU (fails SIDEWAYS, prior WFE issues)
3. Update `asset_config.py` with regime notes

### Portfolio Impact
- Current PROD: 14 assets
- After exclusion: 12 assets (EGLD, AVAX removed)
- No new assets from today's screening (0/17)

### Live Trading Rules
```
IF regime == MARKDOWN:
    # Strategy naturally avoids - no action needed
    
IF regime == SIDEWAYS AND asset IN [EGLD, AVAX]:
    # Reduce position or FLAT
    position_size *= 0.5  # or skip entirely
```

---

## Files Generated

| File | Description |
|------|-------------|
| `outputs/stress_test_MARKDOWN_20260126_161422.csv` | MARKDOWN test results |
| `outputs/stress_test_SIDEWAYS_20260126_161501.csv` | SIDEWAYS test results |
| `scripts/run_regime_stress_test.py` | Stress test script (TASK 3 deliverable) |

---

## Validation Checklist (TASK 3)

- [x] Script `run_regime_stress_test.py` fonctionnel
- [x] Supporte `--asset`, `--all-assets`, `--regime`
- [x] Filtre par `entry_regime` (pas exit) - CRITICAL
- [x] Output CSV avec Sharpe, MaxDD, Trades, WinRate par asset
- [x] Alerte si Sharpe < 0 sur MARKDOWN
- [x] Test sur les 14 assets PROD pour MARKDOWN
- [x] Test supplementaire sur SIDEWAYS (79% profit source)

---

**Status:** TASK 3 COMPLETE  
**Next:** Casey review for EGLD/AVAX decisions  
**Author:** Jordan
