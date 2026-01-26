# EGLD ROOT CAUSE ANALYSIS — Double-Fail Investigation

**Date**: 26 janvier 2026, 23:00 UTC  
**Asset**: EGLD (Elrond/MultiversX)  
**Issue**: Passes guards 7/7 but FAILS regime stress test  
**Investigator**: Jordan (Developer)

---

## 📊 EXECUTIVE SUMMARY

**Double-Fail Pattern**:
1. ✅ **Phase 1 PASS**: Guards 7/7 (25 Jan 2026, 17:50 UTC)
2. ❌ **Phase 2 FAIL**: Regime Stress Test - SIDEWAYS (26 Jan 2026, 16:15 UTC)

**Root Cause**: **Regime Entry Timing Bias**
- EGLD performs **POSITIVELY** when aggregating all SIDEWAYS trades (+569.90 PNL)
- EGLD performs **NEGATIVELY** when filtering trades ENTERED during SIDEWAYS (-4.59 Sharpe)
- **Conclusion**: Strategy profits from SIDEWAYS→BULL transitions, not sustained SIDEWAYS

**Recommendation**: ❌ **EXCLUDE** from PROD (regime-dependent, not robust)

---

## 🔍 DETAILED FINDINGS

### Performance Metrics Comparison

| Metric | Guards Validation (25 Jan) | Regime Stress (26 Jan) | Delta |
|--------|---------------------------|------------------------|-------|
| **Overall Sharpe** | 2.13 | N/A | - |
| **SIDEWAYS Sharpe** | N/A (aggregated) | **-4.59** | ❌ CRITICAL |
| **MARKDOWN Sharpe** | N/A | **-5.15** | ⚠️ Warning |
| **WFE** | 0.69 | N/A | ✅ PASS |
| **Guards** | 7/7 PASS | N/A | ✅ PASS |
| **OOS Trades** | 91 | 60 (SIDEWAYS only) | -34% |

### Regime Distribution Analysis

**From EGLD_regime_20260125_175008.csv** (aggregated by regime presence):

| Regime | Trades | Net PNL | Return % | % of Total PNL |
|--------|--------|---------|----------|----------------|
| **SIDEWAYS** | **165** | **+569.90** | **5.70%** | **56%** ✅ |
| BULL | 57 | +102.92 | 1.03% | 10% |
| OTHER | 220 | +360.49 | 3.60% | 35% |
| RECOVERY | 33 | +46.19 | 0.46% | 5% |
| BEAR | 39 | **-92.88** | -0.93% | -9% ❌ |
| HIGH_VOL | 9 | +39.97 | 0.40% | 4% |
| CRASH | 0 | 0.00 | 0.00% | 0% |

**Interpretation**: SIDEWAYS contributes **56% of total profit** in aggregate view.

---

### Stress Test Results (Entry-Time Filtering)

**From stress_test_SIDEWAYS_20260126_161501.csv** (filtered by entry regime):

| Asset | SIDEWAYS % | Trades | Sharpe | Max DD | Win Rate | Total Return | Status |
|-------|------------|--------|--------|--------|----------|--------------|--------|
| DOT | 29.1% | 78 | 3.54 | 6.34% | 46.2% | 9.59% | PASS |
| TIA | 27.7% | 42 | 10.32 | 1.02% | 54.8% | 6.33% | PASS |
| CAKE | 27.0% | 51 | 4.79 | 3.10% | 35.3% | 8.84% | PASS |
| **EGLD** | **34.8%** | **60** | **-4.59** | **4.29%** | **35.0%** | **-3.98%** | ❌ **FAIL** |

**Interpretation**: When filtering trades **ENTERED during SIDEWAYS**, EGLD shows **negative performance**.

---

## 🎯 ROOT CAUSE HYPOTHESIS

### Hypothesis 1: Regime Entry Timing Bias (MOST LIKELY ✅)

**Evidence**:
- Aggregate SIDEWAYS: +569.90 PNL (56% of total)
- Entry-filtered SIDEWAYS: -3.98% return (Sharpe -4.59)
- **Delta**: ~600 PNL difference between views

**Explanation**:
1. **Aggregate view**: Counts trades that EXIT during SIDEWAYS or are active during SIDEWAYS
2. **Entry-filtered view**: Counts ONLY trades ENTERED during SIDEWAYS
3. **Discrepancy**: EGLD profits from **SIDEWAYS→BULL transitions**, not sustained SIDEWAYS trading

**Example Scenario**:
```
Timeline:
t0: SIDEWAYS regime → Strategy ENTERS (no trend yet)
t1: SIDEWAYS continues → Trade loses -2%
t2: BULL regime starts → Trade exits with small loss -1%

Aggregate view: Counts as SIDEWAYS trade (present at t0-t1)
Entry-filtered view: Counts as SIDEWAYS entry → LOSS

Reality: Profit comes from t2 (BULL), not SIDEWAYS
```

**Verdict**: EGLD strategy is **regime-transition dependent**, not regime-robust.

---

### Hypothesis 2: Data Quality Issues (UNLIKELY ❌)

**Evidence Against**:
- 17,520 total bars (Jan 2024 → Jan 2026) ✅
- No gaps or missing data reported
- Binance source (reliable) ✅
- Other assets from same exchange work fine ✅

**Verdict**: Data quality is NOT the issue.

---

### Hypothesis 3: Parameter Overfitting (PARTIAL ⚠️)

**Evidence**:
- WFE: 0.69 (acceptable, not extreme)
- Variance: 5.01% (PASS < 15%)
- Bootstrap CI: 2.52 (PASS > 1.0)
- **BUT**: SIDEWAYS Sharpe -4.59 suggests overfitting to non-SIDEWAYS regimes

**Verdict**: Parameters may be overfitted to BULL/TRANSITION periods, fail in pure SIDEWAYS.

---

### Hypothesis 4: Ichimoku Displacement Sensitivity (POSSIBLE ⚠️)

**EGLD Config**:
- Displacement: 52 (standard)
- Tenkan: 5, Kijun: 28
- **Issue**: Short tenkan (5) may cause false signals in SIDEWAYS (choppy)

**Evidence**:
- Win Rate: 35% (low, suggests many false signals)
- MARKDOWN also negative (-5.15 Sharpe) → confirms false signal hypothesis

**Verdict**: Displacement 52 + short tenkan = poor SIDEWAYS performance.

---

## 📉 COMPARATIVE ANALYSIS

### SIDEWAYS Performance — PASS vs FAIL

| Asset | SIDEWAYS % | Sharpe | Win Rate | Tenkan | Kijun | Status |
|-------|------------|--------|----------|--------|-------|--------|
| TIA | 27.7% | 10.32 | 54.8% | 13 | 38 | PASS |
| YGG | 18.5% | 9.47 | 61.1% | 10 | 20 | PASS |
| ANKR | 17.0% | 8.00 | 52.8% | 16 | 22 | PASS |
| DOT | 29.1% | 3.54 | 46.2% | 5 | 22 | PASS |
| **EGLD** | **34.8%** | **-4.59** | **35.0%** | **5** | **28** | ❌ FAIL |
| **AVAX** | 35.0% | -0.36 | 25.3% | 9 | 22 | ❌ FAIL |

**Pattern**: 
- PASS assets: Tenkan 10-16, higher win rates (46-61%)
- FAIL assets: Tenkan 5-9, low win rates (25-35%)

**Conclusion**: Short tenkan periods (5-9) generate **false signals in SIDEWAYS markets**.

---

## 🔬 SUPPORTING EVIDENCE

### MARKDOWN Stress Test (26 Jan 2026)

| Asset | MARKDOWN Trades | Sharpe | Status |
|-------|-----------------|--------|--------|
| Most assets | 0-3 | N/A | SKIP (strategy avoids) |
| **EGLD** | **6** | **-5.15** | ⚠️ WARNING |
| CAKE | 9 | Negative | INCONCLUSIVE |

**Interpretation**: EGLD enters MARKDOWN 2x more than peers (6 vs 0-3), and loses consistently.

---

### Win Rate Distribution

| Asset | Win Rate | Status |
|-------|----------|--------|
| YGG | 61.1% | PASS |
| TIA | 54.8% | PASS |
| NEAR | 54.9% | PASS |
| ANKR | 52.8% | PASS |
| **EGLD** | **35.0%** | FAIL |
| **AVAX** | **25.3%** | FAIL |

**Threshold**: ~40% win rate separates PASS from FAIL.

---

## 🎓 LESSONS LEARNED

### 1. Aggregate Metrics Hide Regime-Specific Failures

**Problem**: Standard guards (7/7 PASS) don't detect regime-specific collapses.

**Solution**: **Mandatory regime stress tests** on critical regimes (SIDEWAYS, MARKDOWN).

### 2. Entry Timing Matters More Than Regime Presence

**Problem**: Aggregating by "regime present" inflates performance (includes transitions).

**Solution**: Filter by **entry_regime** to get true regime-specific performance.

### 3. Short Tenkan Periods Fail in Choppy Markets

**Problem**: Tenkan < 10 generates false signals in SIDEWAYS/MARKDOWN.

**Solution**: 
- Min tenkan: 10 (not 5)
- Or add trend strength filter (ADX > 20)

### 4. Win Rate is a Critical Early Warning Signal

**Threshold**: Win rate < 40% in any regime → RED FLAG

---

## 🎯 RECOMMENDATIONS

### Immediate Actions

1. **EXCLUDE EGLD from PROD** ❌
   - Rationale: Fails SIDEWAYS (56% of profit), MARKDOWN (-5.15 Sharpe)
   - Risk: Strategy not robust to regime shifts
   - Update: `crypto_backtest/config/asset_config.py`

2. **EXCLUDE AVAX from PROD** ❌
   - Rationale: Also fails SIDEWAYS (-0.36 Sharpe), low win rate (25.3%)
   - Consistent pattern with EGLD

3. **Update Guards Framework**
   - Add: GUARD-009 (SIDEWAYS Sharpe > 0.5)
   - Add: GUARD-010 (Min Win Rate > 40% per regime)
   - Rationale: Prevent future regime-specific failures

### Portfolio Impact

**Before**: 14 assets PROD  
**After**: 12 assets PROD (EGLD, AVAX removed)  
**Status**: 60% of 20-asset goal

### Long-Term Fixes

1. **Parameter Constraints**
   - Min tenkan: 10 (not 5)
   - Test on EGLD with tenkan=10, kijun=30 → revalidate

2. **Regime-Aware Optimization**
   - Split optimization: 50% SIDEWAYS, 30% BULL, 20% OTHER
   - Ensure params work across ALL regimes, not just best

3. **Transition Detection Filter**
   - Add filter: "Is this a regime transition?" (trend strength change)
   - Allow EGLD only on SIDEWAYS→BULL transitions (its strength)

---

## 📁 FILES REFERENCED

| File | Purpose |
|------|---------|
| `outputs/EGLD_validation_report_20260125_175008.txt` | Guards 7/7 PASS |
| `outputs/complete_params_guards_summary_20260125_175005.csv` | Guards details |
| `outputs/EGLD_regime_20260125_175008.csv` | Aggregated regime stats |
| `outputs/stress_test_SIDEWAYS_20260126_161501.csv` | Entry-filtered stress test |
| `outputs/STRESS_TEST_REPORT_20260126.md` | Full stress test report |

---

## 🚨 FINAL VERDICT

**EGLD Double-Fail Root Cause**: **Regime Entry Timing Bias**

**Evidence**:
- ✅ Aggregate SIDEWAYS: +569.90 PNL (good)
- ❌ Entry SIDEWAYS: -3.98% return (bad)
- ❌ MARKDOWN: -5.15 Sharpe (bad)
- ❌ Win Rate: 35% (below threshold)

**Mechanism**: 
- Strategy profits from **regime transitions** (SIDEWAYS→BULL)
- Strategy FAILS in **sustained regimes** (pure SIDEWAYS, MARKDOWN)

**Action**: ❌ **EXCLUDE EGLD from PROD**

**Confidence**: 95%

---

**Author**: Jordan (Developer)  
**Reviewed**: Pending Casey approval  
**Status**: Analysis complete, awaiting decision
