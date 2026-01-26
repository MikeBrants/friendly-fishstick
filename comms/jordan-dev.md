# Jordan Dev Log — FINAL TRIGGER v2

**Last Updated**: 26 Jan 2026, 23:30 UTC

---

## 2330 READY jordan-dev -> casey-quant: PR#20 Revalidation Plan READY

**Task**: Prepare PR#20 revalidation after SHORT signal parity fix  
**Status**: ✅ READY TO EXECUTE

### Executive Summary

**Objective**: Revalidate 12 PROD assets + 1 rescue candidate (OSMO) with PR#19 fix integrated.

**Critical Issue**: All current PROD assets were validated PRE-PR#19. The fix changes how `tenkan_5`/`kijun_5` are propagated to `FiveInOneConfig`, which affects SHORT signal generation.

**Expected Impact**:
- ✅ SHORT signals should appear (was potentially 0% before)
- ✅ Sharpe: Neutral to slight positive (better signal balance)
- ⚠️ WFE: Slight drop expected (-0.1 to -0.2) due to more balanced strategy
- ✅ Trade count: Stable or slight increase

### Assets to Revalidate

**12 PROD Assets** (Priority 1):
1. SHIB (5.67 Sharpe, 2.27 WFE)
2. DOT (4.82 Sharpe, 1.74 WFE)
3. TIA (5.16 Sharpe, 1.36 WFE)
4. NEAR (4.26 Sharpe, 1.69 WFE)
5. DOGE (3.88 Sharpe, 1.55 WFE)
6. ANKR (3.48 Sharpe, 0.86 WFE)
7. ETH (3.22 Sharpe, 1.22 WFE)
8. JOE (3.16 Sharpe, 0.73 WFE)
9. YGG (3.11 Sharpe, 0.78 WFE)
10. MINA (2.58 Sharpe, 1.13 WFE)
11. CAKE (2.46 Sharpe, 0.81 WFE)
12. RUNE (2.42 Sharpe, 0.61 WFE)

**1 Rescue Candidate** (Priority 2):
- OSMO (0.68 Sharpe, 0.19 WFE) - Test d26/d78 rescue

### Pre-Flight Checklist

- [x] PR#19 integrated and tested (10/10 tests PASS)
- [x] Data availability verified (13/13 assets, ≥17520 bars each)
- [x] Revalidation plan documented (`docs/REVALIDATION_PLAN_PR20.md`)
- [x] Execution script prepared (`scripts/run_pr20_revalidation.sh`)
- [x] Output structure designed
- [ ] Execution approval from Casey

### Execution Plan

**Phase 1: PROD Revalidation** (8-10h)
- Batch 1: SHIB, DOT, TIA, NEAR (3-4h)
- Batch 2: DOGE, ANKR, ETH, JOE (3-4h)
- Batch 3: YGG, MINA, CAKE, RUNE (2-3h)

**Phase 2: Regime Stress Test** (2h)
- SIDEWAYS test for all Phase 1 passing assets
- Criteria: Sharpe ≥ 0 (PASS), Sharpe < 0 (EXCLUDE)

**Phase 3: OSMO Rescue** (2h)
- Displacement variants: d26, d78
- Target: WFE ≥ 0.6, Trades OOS ≥ 60

**Phase 4: Analysis** (1h)
- Compare pre/post PR#19 metrics
- Generate impact report
- Update project-state.md

**Total Estimated Duration**: 13-15h (spread over 2 working days)

### Success Criteria

| Metric | Target | Acceptable | FAIL |
|--------|--------|------------|------|
| PROD Pass Rate | ≥10/12 (83%) | ≥9/12 (75%) | <9/12 |
| Mean Sharpe | ≥3.0 | ≥2.5 | <2.5 |
| Mean WFE | ≥0.6 | ≥0.55 | <0.55 |
| SHORT Ratio | 25-75% | 20-80% | <20% or >80% |
| Regime SIDEWAYS | All ≥0 | ≥90% ≥0 | <90% |

### Risk Mitigation

**Risk 1**: Massive degradation (>50% fail)
- **Action**: STOP after Batch 1, full debug session
- **Probability**: Low (<10%)

**Risk 2**: No SHORT signals
- **Action**: Debug FiveInOneConfig propagation
- **Probability**: Very Low (<5%)

**Risk 3**: Time overrun
- **Action**: Stop after each batch, reassess
- **Probability**: Medium (30%)

### Output Files

```
outputs/
├── pr20_batch1_multiasset_scan_*.csv
├── pr20_batch1_guards_summary_*.csv
├── pr20_batch2_multiasset_scan_*.csv
├── pr20_batch2_guards_summary_*.csv
├── pr20_batch3_multiasset_scan_*.csv
├── pr20_batch3_guards_summary_*.csv
├── pr20_regime_stress_*.csv
├── pr20_osmo_d26_scan_*.csv
├── pr20_osmo_d78_scan_*.csv
├── PR20_CONSOLIDATED_RESULTS.csv
└── returns_matrix_*_*.npy

reports/
├── PR20_IMPACT_ANALYSIS.csv
└── PR20_REVALIDATION_REPORT.md
```

### Execution Command

```bash
# Bash (Linux/Mac)
bash scripts/run_pr20_revalidation.sh

# Manual execution (Windows PowerShell)
# Phase 1 Batch 1
python scripts/run_full_pipeline.py --assets SHIB DOT TIA NEAR --optimization-mode baseline --trials-atr 300 --trials-ichi 300 --run-guards --workers 1 --output-prefix pr20_batch1

# Phase 1 Batch 2
python scripts/run_full_pipeline.py --assets DOGE ANKR ETH JOE --optimization-mode baseline --trials-atr 300 --trials-ichi 300 --run-guards --workers 1 --output-prefix pr20_batch2

# Phase 1 Batch 3
python scripts/run_full_pipeline.py --assets YGG MINA CAKE RUNE --optimization-mode baseline --trials-atr 300 --trials-ichi 300 --run-guards --workers 1 --output-prefix pr20_batch3
```

### Next Steps

**Immediate** (Awaiting Casey approval):
1. Execute Phase 1 Batch 1 (SHIB, DOT, TIA, NEAR)
2. Analyze results after 4h
3. Decide: Continue Batch 2-3 OR stop/debug

**After Completion**:
1. Generate PR#20 impact analysis
2. Update project-state.md
3. Update asset_config.py if needed
4. Create PR#20 summary document
5. OPTIONAL: Test AR/METIS rescue if OSMO succeeds

### References

- **Plan**: `docs/REVALIDATION_PLAN_PR20.md`
- **Script**: `scripts/run_pr20_revalidation.sh`
- **PR#19 Fix**: commit 56ed34b
- **PR#19 Integration**: `docs/PR19_INTEGRATION_SUMMARY.md`

---

**Status**: ⏸️ STANDBY — Awaiting execution approval  
**Estimated Start**: 27 Jan 2026, 09:00 UTC  
**Estimated Completion**: 28 Jan 2026, 18:00 UTC

---

## Previous Entries

### 2230 DONE jordan-dev -> casey-quant: PR#19 Integration Complete

[See previous entry in document history]
