# Phase 1 Screening Batch 1 — RESULTS

**Date:** 25 janvier 2026, 18:05 UTC  
**Duration:** 16 minutes (rapid parallel execution)  
**Assets Screened:** 15  
**Status:** ✅ **COMPLETE**

---

## 🎯 EXECUTIVE SUMMARY

**PASS:** 2 assets ✅ (ADA, FIL)  
**FAIL:** 13 assets ❌  
**Notable:** MATIC (6.84 Sharpe but data insufficient)

**Pass Rate:** 13.3% (lower than expected 25-30%)

---

## ✅ SUCCESS ASSETS (2) — Ready for Phase 2

### 1. ADA (Cardano)
- **OOS Sharpe:** 1.92
- **WFE:** 0.61 ✅
- **Status:** SUCCESS → Phase 2 validation
- **Displacement:** TBD
- **Notes:** Smart contract platform, Tier 1 blue chip

### 2. FIL (Filecoin)
- **OOS Sharpe:** 1.98
- **WFE:** 0.90 ✅ (excellent)
- **Status:** SUCCESS → Phase 2 validation
- **Displacement:** TBD
- **Notes:** Storage network, strong WFE

---

## 🟡 NOTABLE FAIL — MATIC (Data Issue)

### MATIC (Polygon)
- **OOS Sharpe:** **6.84** 🔥 (exceptional!)
- **WFE:** 0.74 ✅ (good)
- **Total Bars:** **5,459** ❌ (insufficient)
- **Period:** 2024-01-26 → 2024-09-10 (7.5 months only)
- **Status:** FAIL (data insufficient < 8000 bars)

**Issue:** Données manquantes après Sept 2024 (delisting temporaire? API issue?)

**Recommendation:**
- **Check data source** (Binance API issue?)
- **Try alternative exchange** (Bybit, OKX)
- **Redownload** if data available
- **If fixed:** Likely strong PROD candidate (Sharpe 6.84!)

---

## 🟡 MARGINAL FAIL — AVAX

### AVAX (Avalanche)
- **OOS Sharpe:** 2.22 (good)
- **WFE:** 0.52 (marginal, threshold: 0.6)
- **Status:** FAIL (WFE slightly below)

**Recommendation:**
- **Phase 3A Displacement Rescue** (test d26, d78)
- **Likely recoverable** (Sharpe good, WFE close to threshold)

---

## ❌ CLEAR FAIL (11 assets)

| Asset | OOS Sharpe | WFE | Reason |
|:------|:-----------|:----|:-------|
| IMX | 1.26 | 0.57 | Close but below thresholds |
| ICP | 0.87 | 0.63 | Sharpe < 1.0 |
| STX | 0.80 | 0.18 | Low WFE (overfit) |
| XRP | 0.65 | 0.20 | Below thresholds |
| OP | 0.12 | 0.03 | Very weak |
| UNI | -0.40 | -0.17 | Negative performance |
| GRT | -0.65 | -0.20 | Negative |
| TRX | -0.91 | -0.37 | Negative |
| XLM | -1.17 | -0.62 | Negative |
| LTC | -1.74 | -0.52 | Negative |
| BNB | -2.13 | -0.99 | Negative |

---

## 📊 STATISTICAL ANALYSIS

**Pass Rate:** 2/15 (13.3%) vs expected 25-30%

**Why Lower?**
1. **Data quality issues** (MATIC missing data)
2. **Blue chips don't always perform** (BNB, LTC, XRP negative)
3. **Strategy may favor specific asset types** (mid-caps over mega-caps?)

**Positive Finding:**
- FIL has excellent WFE (0.90) → robust candidate

---

## 🎯 IMMEDIATE NEXT STEPS

### Priority 1: Phase 2 Validation (ADA, FIL)

**Command:**
```bash
python scripts/run_full_pipeline.py \
  --assets ADA FIL \
  --workers 1 \
  --trials-atr 300 \
  --trials-ichi 300 \
  --enforce-tp-progression \
  --run-guards \
  --output-prefix phase2_validation_batch1_20260125
```

**Expected:**
- Duration: ~30-45 minutes (2 assets, sequential)
- Outcome: 1-2 assets 7/7 guards PASS
- Portfolio: 11 → 12-13 assets (60-65%)

---

### Priority 2: Investigate MATIC Data

**Actions:**
1. Check alternative exchanges (Bybit, OKX)
2. Redownload with different source
3. If data available → rerun screening

**Potential:**
- MATIC Sharpe 6.84 would be **#1 performer** (beat SHIB 5.67!)
- WFE 0.74 is good (no overfit)
- HIGH PRIORITY if data fixable

---

### Priority 3: AVAX Displacement Rescue

**If time permits:**
```bash
python scripts/run_full_pipeline.py \
  --assets AVAX \
  --fixed-displacement 26 \
  --workers 1 \
  --trials-atr 300 \
  --trials-ichi 300 \
  --enforce-tp-progression \
  --run-guards
```

**Rationale:** Sharpe 2.22 good, WFE 0.52 close to threshold (0.6)

---

## 📋 BATCH 2 PLANNING

**Candidates Remaining:** 14 assets

**Priority Assets (next batch):**
- VET, MKR, ALGO, FTM (Tier 3)
- SAND, MANA, FLOW, THETA (Tier 4)

**Strategy Adjustment:**
- Maybe mid-caps (Tier 3/4) perform better than mega-caps?
- Consider: More volatile = better for trend-following?

---

## 📈 PORTFOLIO PROJECTION

**Current:** 11 assets PROD  
**After Phase 2 (ADA, FIL):** 12-13 assets (60-65% of goal)  
**After MATIC fix (if possible):** 13-14 assets (65-70%)  
**After Batch 2:** 15-18 assets (75-90% of goal)

**Timeline:**
- Phase 2 (ADA, FIL): ~45 min
- MATIC investigation: ~15 min
- Batch 2 screening: ~20 min (if needed)
- Total: ~1-2h to reach 12-14 assets

---

## 📁 OUTPUT FILES

**Scan Results:**
- `outputs/phase1_batch1_20260125_multiasset_scan_20260125_194144.csv`

**Key Findings:**
- 2 SUCCESS (ADA, FIL)
- 1 Data Issue (MATIC - 5,459 bars only)
- 12 Clear FAIL

---

## 💡 LESSONS LEARNED

### Finding 1: Blue Chips ≠ Better Performance
- BNB, LTC, XRP all FAIL (negative Sharpe)
- Mid-caps (ADA, FIL) more suitable for trend-following
- Strategy may favor specific volatility profiles

### Finding 2: Data Quality Critical
- MATIC has best potential (6.84 Sharpe) but insufficient data
- Always check total_bars before optimization
- Alternative exchanges may have better data coverage

### Finding 3: Parallel Screening is FAST
- 15 assets in 16 minutes (workers=10)
- Enables rapid iteration on candidate pools
- Can test large universes quickly

---

## 🎯 DECISION

**Proceed with:** Phase 2 Validation (ADA, FIL)

**Investigate:** MATIC data issue (high priority)

**Consider:** Batch 2 with Tier 3/4 assets (different volatility profile)

---

**Created:** 25 janvier 2026, 18:05 UTC  
**Author:** Jordan (Developer)  
**Status:** ✅ ANALYSIS COMPLETE
