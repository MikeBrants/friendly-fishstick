# Phase 1 Screening — Batch 1

**Date:** 25 janvier 2026, 17:45 UTC  
**Goal:** Expand portfolio from 11 → 20+ assets  
**Target:** Screen 15 high-priority candidates

---

## 🎯 BATCH 1 SELECTION (15 Assets)

### Tier 1 - Blue Chips (5 assets)
1. **XRP** - Ripple (payment network)
2. **BNB** - Binance Coin (exchange token)
3. **ADA** - Cardano (smart contract platform)
4. **AVAX** - Avalanche (DeFi ecosystem)
5. **TRX** - Tron (blockchain platform)

### Tier 2 - Large Caps (5 assets)
6. **MATIC** - Polygon (L2 scaling)
7. **UNI** - Uniswap (DEX leader)
8. **ICP** - Internet Computer (cloud blockchain)
9. **FIL** - Filecoin (storage network)
10. **OP** - Optimism (L2 optimistic rollup)

### Tier 2/3 - Mid Caps (5 assets)
11. **XLM** - Stellar (payment network)
12. **LTC** - Litecoin (payment coin)
13. **GRT** - The Graph (indexing protocol)
14. **IMX** - Immutable X (gaming L2)
15. **STX** - Stacks (Bitcoin L2)

---

## 📋 PHASE 1 CRITERIA

**Objective:** Identify promising candidates for Phase 2 validation

**Thresholds:**
- OOS Sharpe > 0.8 (target: > 1.5)
- WFE > 0.5 (target: > 0.6)
- OOS Trades > 50 (target: > 60)
- No guards testing (Phase 1 only)

**Pass Rate Expected:** ~25-30% (4-5 assets PASS from 15)

---

## 🔧 COMMAND

```bash
python scripts/run_full_pipeline.py \
  --assets XRP BNB ADA AVAX TRX MATIC UNI ICP FIL OP XLM LTC GRT IMX STX \
  --workers 10 \
  --trials-atr 150 \
  --trials-ichi 150 \
  --skip-guards \
  --output-prefix phase1_batch1_20260125
```

**Parameters:**
- workers=10 (parallel screening, safe with constant_liar)
- trials=150 (screening level, faster than validation 300)
- skip-guards (Phase 1 doesn't test guards)
- Expected duration: ~1-2h

---

## 📊 EXPECTED OUTCOMES

### Success Case (4-5 PASS)
**Scenario:** 4-5 assets exceed thresholds
- Next: Phase 2 validation (300 trials, guards ON, workers=1)
- Goal: +4-5 assets PROD → 15-16 total (75% of 20+ target)

### Moderate Case (2-3 PASS)
**Scenario:** 2-3 assets marginal PASS
- Next: Phase 2 validation on PASS assets
- Next: Batch 2 screening (15 more candidates)

### Low Case (0-1 PASS)
**Scenario:** Most assets FAIL screening
- Next: Batch 2 with different asset types (Tier 3/4)
- Consider: Adjust thresholds or displacement

---

## 📁 OUTPUT FILES

**Scan Results:**
- `outputs/phase1_batch1_20260125_multiasset_scan_*.csv`

**Expected Columns:**
- asset, oos_sharpe, wfe, oos_trades, displacement, optimization_mode
- sl_mult, tp1_mult, tp2_mult, tp3_mult
- tenkan, kijun, tenkan_5, kijun_5

---

## 🎯 NEXT STEPS AFTER COMPLETION

### If 4+ Assets PASS
1. **Phase 2 Validation** (workers=1, guards ON, 300 trials)
2. **Portfolio update** (11 → 15+ assets)
3. **Portfolio rebalancing** (Max Sharpe with new assets)

### If 2-3 Assets PASS
1. **Phase 2 on PASS assets**
2. **Batch 2 screening** (next 15 candidates)
3. **Parallel approach** (validate while screening)

### If 0-1 PASS
1. **Adjust strategy** (lower thresholds? different displacement?)
2. **Batch 2 with Tier 3/4** (more volatile assets)
3. **Review screening results** (identify patterns)

---

## 📊 PROGRESS TRACKING

**Current State:**
- Assets PROD: 11/20+ (55%)
- Assets screened: 11 (initial) + 15 (Batch 1) = 26
- Candidates remaining: 14 (Batch 2+)

**Target After Batch 1:**
- Best case: 16 assets PROD (80%)
- Moderate: 14 assets PROD (70%)
- Worst case: 11-12 assets (55-60%)

---

**Status:** ✅ READY TO LAUNCH  
**Estimated Duration:** 1-2 hours  
**Priority:** P1 (expansion)  
**Created:** 25 janvier 2026, 17:45 UTC  
**Author:** Jordan (Developer)
