# TODO PLAN — 26 January 2026

**Generated**: 26 Jan 2026, 14:30 UTC  
**Status**: 🟢 PRODUCTION-READY with 14 assets  
**Next Phase**: Live Deployment Preparation

---

## 📊 CURRENT STATE SUMMARY

| Metric | Value | Status |
|--------|-------|--------|
| **PROD Assets** | 14 | ✅ All 7/7 guards PASS |
| **Mean OOS Sharpe** | 3.54 | ✅ Excellent |
| **Mean WFE** | 1.23 | ⚠️ Period-sensitive |
| **Portfolio Method** | Max Sharpe | ✅ Selected (Sharpe 4.96) |
| **Regime Analysis v3** | Deployed | 🟡 Needs PROD validation |
| **WFE Audit** | Complete | ✅ Period effect confirmed |

---

## 🎯 4-PHASE ROADMAP

### PHASE 1: Regime v3 Validation (Priority: HIGH) ⏱️ 2-3h
**Goal**: Validate regime analysis on all 14 PROD assets with new v3 system

| Task | Script | Status | ETA |
|------|--------|--------|-----|
| 1.1 Run regime analysis on 14 PROD | `run_regime_prod_analysis.py` | 🔴 TODO | 1h |
| 1.2 Verify SIDEWAYS profit ratio | Manual analysis | 🔴 TODO | 30m |
| 1.3 Update guard007 if needed | Code change | 🔴 TODO | 30m |
| 1.4 Document regime distribution | Report | 🔴 TODO | 30m |

**Command**:
```bash
python scripts/run_regime_prod_analysis.py --all-prod --export-report
```

**Success Criteria**:
- ✅ All 14 assets analyzed without errors
- ✅ SIDEWAYS profit ratio documented (was 79.5%)
- ✅ Regime stability > 10 bars average
- ✅ No regime mismatch > 20%

---

### PHASE 2: Asset Rescue (Priority: MEDIUM) ⏱️ 4-6h
**Goal**: Recover OSMO, AR, METIS via Phase 3A displacement optimization

| Asset | Current Issue | Rescue Action | Status |
|-------|--------------|---------------|--------|
| **OSMO** | Sharpe 0.68, WFE 0.19 | Displacement d26/d52/d78 | 🔴 TODO |
| **AR** | WFE 0.39, Trades 41 | Displacement + more data | 🔴 TODO |
| **METIS** | WFE 0.48 | Displacement rescue | 🔴 TODO |

**Command**:
```bash
python scripts/run_phase3a_rescue.py --assets OSMO AR METIS --displacements 26 52 78
```

**Success Criteria**:
- ✅ At least 1 asset rescued to PROD
- ✅ All pass 7/7 guards OR documented exclusion reason
- ✅ Portfolio updated if new assets added

---

### PHASE 3: Production Export (Priority: HIGH) ⏱️ 2-3h
**Goal**: Prepare Pine Script configurations for TradingView deployment

| Task | Script | Status | ETA |
|------|--------|--------|-----|
| 3.1 Export frozen params to JSON | `export_pine_config.py` | 🔴 TODO | 30m |
| 3.2 Generate Pine Script template | `generate_pine_template.py` | 🔴 TODO | 1h |
| 3.3 Create deployment checklist | Manual | 🔴 TODO | 30m |
| 3.4 Validate params consistency | Cross-check | 🔴 TODO | 30m |

**Command**:
```bash
python scripts/export_pine_config.py --all-prod --output pine_configs/
```

**Deliverables**:
- `pine_configs/asset_params.json` — All 14 asset parameters
- `pine_configs/PINE_DEPLOYMENT_CHECKLIST.md` — Step-by-step deployment
- `pine_configs/template_ichimoku_atr.pine` — Base Pine Script template

---

### PHASE 4: Live Monitoring Setup (Priority: MEDIUM) ⏱️ 3-4h
**Goal**: Prepare monitoring infrastructure for live deployment

| Task | Status | Notes |
|------|--------|-------|
| 4.1 Define performance degradation alerts | 🔴 TODO | Sharpe < 0.5 = alert |
| 4.2 Setup regime shift detection | 🔴 TODO | Auto-pause on BEAR |
| 4.3 Create position sizing tiers | 🔴 TODO | Based on WFE sensitivity |
| 4.4 Document rollback procedure | 🔴 TODO | Emergency stop protocol |

---

## 📋 DETAILED TASK BREAKDOWN

### 1.1 Regime v3 PROD Validation

**Script**: `scripts/run_regime_prod_analysis.py`

**Logic**:
```python
PROD_ASSETS = [
    "SHIB", "DOT", "TIA", "NEAR", "DOGE", "ANKR", "ETH",
    "JOE", "YGG", "MINA", "CAKE", "RUNE", "EGLD", "AVAX"
]

for asset in PROD_ASSETS:
    1. Load OHLCV data from data/{asset}_USDT_1h.parquet
    2. Run CryptoRegimeAnalyzer.fit_and_classify()
    3. Calculate profit distribution by regime
    4. Check SIDEWAYS ratio (target > 70%)
    5. Export to reports/regime_v3_{asset}.csv
```

**Expected Output**:
```
--- REGIME ANALYSIS: 14 PROD ASSETS ---

| Asset | SIDEWAYS % | BULL % | BEAR % | Stability |
|-------|------------|--------|--------|----------|
| SHIB  | 78.2%      | 15.3%  | 6.5%   | 14.2 bars |
| DOT   | 72.1%      | 18.9%  | 9.0%   | 11.8 bars |
...
```

---

### 2.1 Phase 3A Displacement Rescue

**Script**: `scripts/run_phase3a_rescue.py`

**Methodology**:
1. For each failed asset (OSMO, AR, METIS)
2. Test displacement values: d26, d52, d78 (Ichimoku standard)
3. Run full optimization with 300 trials
4. Apply 7 guards validation
5. If PASS → add to PROD, else → EXCLUDE

**Expected Results**:
| Asset | Best Disp | Sharpe | WFE | Verdict |
|-------|-----------|--------|-----|--------|
| OSMO | d52 | 1.85? | 0.62? | RESCUE? |
| AR | d78 | 1.72? | 0.58? | RESCUE? |
| METIS | d26 | 1.94? | 0.65? | RESCUE? |

---

### 3.1 Pine Script Export Configuration

**Format**:
```json
{
  "ETH": {
    "sl_mult": 3.0,
    "tp1_mult": 5.0,
    "tp2_mult": 6.0,
    "tp3_mult": 7.5,
    "tenkan": 12,
    "kijun": 36,
    "displacement": 26,
    "filter_mode": "baseline",
    "position_size_tier": "standard",
    "wfe_sensitivity": "moderate"
  },
  ...
}
```

---

## ⚠️ RISK MATRIX

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Regime v3 shows different distribution | 30% | MEDIUM | Re-calibrate if SIDEWAYS < 60% |
| No assets rescued in Phase 2 | 50% | LOW | Portfolio already has 14 assets |
| Pine Script discrepancy | 20% | HIGH | Manual validation before live |
| Live degradation > 60% | 40% | HIGH | Conservative position sizing |

---

## 📊 POSITION SIZING TIERS (Based on WFE)

| Tier | WFE Range | Assets | Position Size | Rationale |
|------|-----------|--------|---------------|----------|
| **Tier 1** (Normal) | < 1.0 | ANKR, JOE, YGG, CAKE, RUNE, EGLD, AVAX, NEAR, DOGE | 100% | Expected degradation |
| **Tier 2** (Moderate) | 1.0-1.5 | ETH, TIA, MINA | 75% | Period-sensitive |
| **Tier 3** (Extreme) | > 2.0 | DOT, SHIB | 50% | High period sensitivity |

---

## ✅ COMPLETION CHECKLIST

### Phase 1 Checklist
- [ ] Regime v3 analysis run on all 14 PROD assets
- [ ] SIDEWAYS profit ratio verified (target > 70%)
- [ ] Regime stability documented
- [ ] guard007 updated if needed
- [ ] Report generated: `reports/regime_v3_prod_analysis.md`

### Phase 2 Checklist
- [ ] OSMO displacement rescue attempted
- [ ] AR displacement rescue attempted
- [ ] METIS displacement rescue attempted
- [ ] Results documented in project-state.md
- [ ] asset_config.py updated if rescued

### Phase 3 Checklist
- [ ] Pine configs exported to JSON
- [ ] Pine Script template generated
- [ ] Deployment checklist created
- [ ] Cross-validation with Python backtest

### Phase 4 Checklist
- [ ] Performance alerts defined
- [ ] Regime shift detection setup
- [ ] Position sizing tiers implemented
- [ ] Rollback procedure documented

---

## 🚀 IMMEDIATE NEXT ACTION

**Run Phase 1.1**: Regime v3 PROD Validation

```bash
cd /path/to/friendly-fishstick
python scripts/run_regime_prod_analysis.py --all-prod --export-report
```

**Expected Duration**: 1 hour (14 assets × 4-5 min each)

---

**Author**: Casey (Orchestrator)  
**Reviewed**: Alex (Lead Quant)  
**Last Updated**: 26 Jan 2026, 14:30 UTC
