# Revalidation Plan PR#20 — Post-Short Signal Parity Fix

**Created**: 26 Jan 2026, 23:00 UTC  
**Agent**: Jordan (Dev)  
**Trigger**: PR#19 (SHORT signal parity fix) merged

---

## 📊 Current State

### PROD Assets (12) — Need Revalidation

| Asset | OOS Sharpe | WFE | Status | Last Validation |
|-------|------------|-----|--------|-----------------|
| SHIB | 5.67 | 2.27 | Pre-PR#19 | Pre-reset |
| DOT | 4.82 | 1.74 | Pre-PR#19 | Pre-reset |
| TIA | 5.16 | 1.36 | Pre-PR#19 | PR#8 reclassified |
| NEAR | 4.26 | 1.69 | Pre-PR#19 | Pre-reset |
| DOGE | 3.88 | 1.55 | Pre-PR#19 | Pre-reset |
| ANKR | 3.48 | 0.86 | Pre-PR#19 | Pre-reset |
| ETH | 3.22 | 1.22 | Pre-PR#19 | 25 Jan reset |
| JOE | 3.16 | 0.73 | Pre-PR#19 | Pre-reset |
| YGG | 3.11 | 0.78 | Pre-PR#19 | 25 Jan reset |
| MINA | 2.58 | 1.13 | Pre-PR#19 | 25 Jan reset |
| CAKE | 2.46 | 0.81 | Pre-PR#19 | PR#8 reclassified |
| RUNE | 2.42 | 0.61 | Pre-PR#19 | 25 Jan reset |

**CRITICAL**: None of these were validated with PR#19 fix (`build_params_for_asset()`)

### Pending Rescue (3) — From Previous Cycle

- OSMO: 0.68 Sharpe, 0.19 WFE (severe overfit, needs d26/d78)
- AR: 1.64 Sharpe, 0.39 WFE (WFE + low trades)
- METIS: 1.59 Sharpe, 0.48 WFE (WFE fail)

### Excluded (10) — From EXCLUDED_ASSETS

SOL, AAVE, SUI, HYPE, ATOM, ARB, LINK, INJ, EGLD, AVAX

---

## 🎯 Revalidation Strategy

### Option A: Conservative (Recommended)
**Focus**: Confirm 12 PROD assets still pass with PR#19 fix  
**Assets**: 12  
**Time**: 8-12h  
**Risk**: Low

### Option B: Comprehensive
**Focus**: PROD + Rescue + New candidates  
**Assets**: 12 PROD + 3 Rescue + 11 New = 26  
**Time**: 20-30h  
**Risk**: Medium

### Option C: Pragmatic (Selected)
**Focus**: PROD confirmation + HIGH-priority rescue  
**Assets**: 12 PROD + OSMO (1 rescue test)  
**Time**: 10-14h  
**Risk**: Low-Medium

---

## 📋 Phase Plan (Option C - Pragmatic)

### Phase 0: Data Download (30 min)

```bash
python scripts/download_data.py \
    --assets SHIB DOT TIA NEAR DOGE ANKR ETH JOE YGG MINA CAKE RUNE OSMO \
    --timeframe 1h \
    --output data/
```

**Validation**:
- [ ] 13 `.parquet` files created
- [ ] Each file ≥8000 bars
- [ ] No gaps >4h

### Phase 1: PROD Batch Revalidation (8-10h)

**Strategy**: 3 batches × 4 assets, workers=1 for reproducibility

#### Batch 1: Top Performers (High WFE)
```bash
python scripts/run_full_pipeline.py \
    --assets SHIB DOT TIA NEAR \
    --optimization-mode baseline \
    --trials-atr 300 \
    --trials-ichi 300 \
    --run-guards \
    --workers 1 \
    --output-prefix pr20_batch1
```

#### Batch 2: Mid Performers
```bash
python scripts/run_full_pipeline.py \
    --assets DOGE ANKR ETH JOE \
    --optimization-mode baseline \
    --trials-atr 300 \
    --trials-ichi 300 \
    --run-guards \
    --workers 1 \
    --output-prefix pr20_batch2
```

#### Batch 3: Lower Performers
```bash
python scripts/run_full_pipeline.py \
    --assets YGG MINA CAKE RUNE \
    --optimization-mode baseline \
    --trials-atr 300 \
    --trials-ichi 300 \
    --run-guards \
    --workers 1 \
    --output-prefix pr20_batch3
```

**Success Criteria Phase 1**:
- [ ] ≥10/12 assets pass 7 hard guards
- [ ] Mean WFE ≥ 0.6 (expect slight drop from PR#19 fix)
- [ ] All assets have SHORT signals (25-75% ratio)

### Phase 2: Regime Stress Test (2h)

**Only for assets passing Phase 1**:

```bash
PHASE1_PASS=$(python -c "
import pandas as pd
import glob
files = glob.glob('outputs/pr20_*_guards_summary_*.csv')
df = pd.concat([pd.read_csv(f) for f in files])
passing = df[df['all_hard_pass'] == True]['asset'].tolist()
print(' '.join(passing))
")

python scripts/run_regime_stress_test.py \
    --assets $PHASE1_PASS \
    --regimes SIDEWAYS \
    --output outputs/pr20_regime_stress.csv
```

**Success Criteria Phase 2**:
- [ ] All assets have SIDEWAYS Sharpe ≥ 0
- [ ] MARKDOWN naturally skipped (strategy design)

### Phase 3: Rescue Test (OSMO only) (2h)

```bash
# Test OSMO with d26 and d78
for disp in 26 78; do
    python scripts/run_full_pipeline.py \
        --assets OSMO \
        --displacement $disp \
        --trials-atr 300 \
        --trials-ichi 300 \
        --run-guards \
        --workers 1 \
        --output-prefix pr20_osmo_d${disp}
done
```

**Success Criteria Phase 3**:
- [ ] 1+ displacement passes 7 hard guards
- [ ] WFE ≥ 0.6, Trades OOS ≥ 60

### Phase 4: Analysis & Documentation (1h)

**Generate comprehensive report**:

```python
import pandas as pd
import glob

# Load all results
scan_files = glob.glob("outputs/pr20_*_scan_*.csv")
guards_files = glob.glob("outputs/pr20_*_guards_*.csv")
stress_file = "outputs/pr20_regime_stress.csv"

scan_df = pd.concat([pd.read_csv(f) for f in scan_files])
guards_df = pd.concat([pd.read_csv(f) for f in guards_files])
stress_df = pd.read_csv(stress_file)

# Create report
report = scan_df.merge(guards_df, on='asset').merge(stress_df, on='asset')

# Compare with pre-PR#19
pre_pr19 = pd.read_csv("outputs/phase2_results.csv")  # From previous cycle
comparison = report.merge(pre_pr19, on='asset', suffixes=('_post', '_pre'))

comparison['sharpe_delta'] = comparison['sharpe_oos_post'] - comparison['sharpe_oos_pre']
comparison['wfe_delta'] = comparison['wfe_pardo_post'] - comparison['wfe_pardo_pre']

print("\n=== PR#19 IMPACT ANALYSIS ===")
print(f"Assets tested: {len(comparison)}")
print(f"Mean Sharpe delta: {comparison['sharpe_delta'].mean():.2f}")
print(f"Mean WFE delta: {comparison['wfe_delta'].mean():.2f}")
print(f"\nAssets with improved Sharpe: {(comparison['sharpe_delta'] > 0).sum()}")
print(f"Assets with degraded Sharpe: {(comparison['sharpe_delta'] < 0).sum()}")

comparison.to_csv("reports/PR20_IMPACT_ANALYSIS.csv", index=False)
```

**Expected Outcomes**:

1. **SHORT Signal Ratio**: All assets should have 25-75% SHORT trades (was potentially 0% pre-PR#19)
2. **Sharpe Impact**: Neutral to slight positive (better signal balance)
3. **WFE Impact**: Slight drop expected (0.0-0.2) due to more balanced strategy
4. **Trade Count**: Should remain stable or increase slightly

---

## ⚠️ Risk Mitigation

### Risk 1: Massive Degradation
**Symptom**: >50% of assets fail guards after PR#19  
**Action**: Rollback PR#19, investigate Pine parity deeply  
**Probability**: Low (<10%)

### Risk 2: No SHORT Signals Generated
**Symptom**: Assets still show 0% SHORT ratio  
**Action**: Debug `FiveInOneConfig` propagation, verify TS5/KS5 params  
**Probability**: Very Low (<5%) - PR#19 fix addresses this

### Risk 3: Time Overrun
**Symptom**: Phase 1 takes >12h  
**Action**: Stop after Batch 1, analyze, decide on Batch 2-3  
**Probability**: Medium (30%)

---

## 📊 Success Metrics

| Metric | Target | Acceptable | FAIL |
|--------|--------|------------|------|
| PROD Pass Rate | ≥10/12 (83%) | ≥9/12 (75%) | <9/12 |
| Mean Sharpe | ≥3.0 | ≥2.5 | <2.5 |
| Mean WFE | ≥0.6 | ≥0.55 | <0.55 |
| SHORT Ratio | 25-75% | 20-80% | <20% or >80% |
| Regime SIDEWAYS | All ≥0 | ≥90% ≥0 | <90% |

---

## 📅 Timeline

| Phase | Duration | Start | End |
|-------|----------|-------|-----|
| 0: Download | 30min | T+0h | T+0.5h |
| 1: Batch 1 | 3-4h | T+0.5h | T+4.5h |
| 1: Batch 2 | 3-4h | T+4.5h | T+8.5h |
| 1: Batch 3 | 2-3h | T+8.5h | T+11.5h |
| 2: Regime Stress | 2h | T+11.5h | T+13.5h |
| 3: OSMO Rescue | 2h | T+13.5h | T+15.5h |
| 4: Analysis | 1h | T+15.5h | T+16.5h |

**Total: ~16.5h (2 working days)**

---

## 🔄 Next Steps After PR#20

### If SUCCESS (≥10/12 PASS)
1. Update `project-state.md` with new metrics
2. Update `asset_config.py` with validated params
3. Create PR#20 summary document
4. OPTIONAL: Phase 2 - Test AR/METIS rescue

### If MIXED (9/12 PASS)
1. Analyze failed assets deeply
2. Attempt filter rescue (baseline → moderate → conservative)
3. Document reasons for exclusion
4. Update EXCLUDED_ASSETS list

### If FAIL (<9/12 PASS)
1. STOP - Critical issue detected
2. Full debug session on 1 failed asset
3. Compare pre/post PR#19 parameters
4. Potentially rollback PR#19 if systemic issue

---

## 📁 Output Files

```
outputs/
├── pr20_batch1_multiasset_scan_*.csv
├── pr20_batch1_guards_summary_*.csv
├── pr20_batch2_multiasset_scan_*.csv
├── pr20_batch2_guards_summary_*.csv
├── pr20_batch3_multiasset_scan_*.csv
├── pr20_batch3_guards_summary_*.csv
├── pr20_regime_stress.csv
├── pr20_osmo_d26_scan_*.csv
├── pr20_osmo_d78_scan_*.csv
└── returns_matrix_*_*.npy

reports/
├── PR20_IMPACT_ANALYSIS.csv
├── PR20_REVALIDATION_REPORT.md
└── PR20_SHORT_SIGNAL_ANALYSIS.md
```

---

**Status**: READY TO EXECUTE  
**Estimated Start**: 27 Jan 2026, 00:00 UTC  
**Estimated Completion**: 28 Jan 2026, 16:00 UTC
