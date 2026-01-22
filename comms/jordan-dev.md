## [22:04] [RUN] @Jordan -> @Sam

**Assets:** ICP, HBAR

**Mode:** medium_distance_volume

**Displacement:** auto (Optuna)

**Command:** 
```bash
python scripts/run_full_pipeline.py \
  --assets ICP HBAR \
  --workers 6 \
  --trials-atr 150 \
  --trials-ichi 150 \
  --enforce-tp-progression \
  --optimization-mode medium_distance_volume \
  --run-guards
```

**Status:** Scan Complete ✅ | Guards In Progress ⏳

**Outputs:**
- Scan: `outputs/multiasset_scan_20260122_221225.csv`
- Guards: In progress (Monte Carlo files generated at 22:13)

**Scan Results:**

| Asset | Status | OOS Sharpe | WFE | OOS Trades | TP Progression | Fail Reason |
|-------|--------|------------|-----|------------|----------------|-------------|
| ICP | ❌ FAIL | -1.04 | -0.13 | 75 | ✅ Valid (3.0 < 5.0 < 8.0 < 9.5) | OOS_SHARPE<1.0; WFE<0.6; OVERFIT |
| HBAR | ✅ SUCCESS | 1.28 | 0.63 | 107 | ✅ Valid (1.5 < 2.5 < 6.5 < 10.0) | - |

**Detailed Metrics:**

### ICP (FAIL)
- **IS Sharpe:** 1.89
- **Val Sharpe:** -1.04
- **OOS Sharpe:** -1.04 ❌
- **OOS Return:** -1.67%
- **OOS Max DD:** -0.25%
- **OOS PF:** 0.93
- **WFE:** -0.13 ❌ (target >0.6)
- **MC p-value:** 0.622
- **Params:** sl=3.0, tp1=5.0, tp2=8.0, tp3=9.5, tenkan=8, kijun=26, displacement=52

**Analysis:** ICP shows severe overfitting with negative OOS Sharpe and negative WFE. IS performance (1.89 Sharpe) completely fails to generalize to OOS (-1.04 Sharpe). The strategy is not viable for this asset.

### HBAR (SUCCESS - Pending Guards)
- **IS Sharpe:** 2.04
- **Val Sharpe:** -1.93
- **OOS Sharpe:** 1.28 ✅ (target >1.0)
- **OOS Return:** 3.07%
- **OOS Max DD:** -3.81%
- **OOS PF:** 1.26
- **WFE:** 0.63 ✅ (target >0.6)
- **MC p-value:** 0.024
- **Params:** sl=1.5, tp1=2.5, tp2=6.5, tp3=10.0, tenkan=7, kijun=20, displacement=52

**Analysis:** HBAR passes scan criteria with OOS Sharpe 1.28 and WFE 0.63. However, validation Sharpe is negative (-1.93), which is concerning. Awaiting guard results to confirm robustness.

**TP Progression Check:**
- ✅ ICP: TP1=5.0, TP2=8.0, TP3=9.5 (gaps: 3.0, 1.5)
- ✅ HBAR: TP1=2.5, TP2=6.5, TP3=10.0 (gaps: 4.0, 3.5)

**Next Steps:**
- ⏳ Awaiting guard results for HBAR (Monte Carlo files generated, guards still running)
- ❌ ICP excluded - severe overfitting, no further action needed

---

## [21:33] [RUN] @Jordan -> @Sam

**Assets:** AVAX, UNI

**Mode:** medium_distance_volume

**Displacement:** auto (Optuna)

**Command:** python scripts/run_full_pipeline.py --assets AVAX UNI --workers 6 --trials-atr 150 --trials-ichi 150 --enforce-tp-progression --optimization-mode medium_distance_volume --skip-download --run-guards

**Status:** Failed ❌

**Outputs:**
- Scan: outputs/multiasset_scan_20260122_213336.csv
- Guards: outputs/multiasset_guards_summary_20260122_213339.csv

**Quick Results:**

| Asset | OOS Sharpe | WFE | Trades | TP Valid |
|-------|------------|-----|--------|----------|
| AVAX | 0.00 | 0.00 | 0 | ❌ |
| UNI | 0.00 | 0.00 | 0 | ❌ |

**Error:** Both assets failed with "No data found for AVAX/UNI in data". The pipeline ran with `--skip-download` but the data files are missing from the data directory.

**Next:** @Sam - Data files for AVAX and UNI need to be downloaded before running the pipeline. Should I run without `--skip-download` to fetch the data first?

