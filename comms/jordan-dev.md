# Jordan Dev Log — FINAL TRIGGER v2

**Last Updated**: 28 Jan 2026, 08:36 UTC

---

## 2026-01-28 — PROMPT 01 Audit Repo + Contract
**Status**: TODO → DONE
**Output**: status/v4_2_audit.md
**Summary**: Audited repo entrypoints, artifact patterns, and core data structures. Added v4.2 1H calibration contract details to the audit doc.
**Next**: PROMPT 02 — configs/families.yaml

## 2026-01-28 — PROMPT 02 configs/families.yaml
**Status**: TODO → DONE
**Output**: configs/families.yaml; scripts/print_family_config.py
**Summary**: Added v4.2 families/rescues YAML as single source of truth and a printer script to load/resolve configs.
**Next**: PROMPT 03 — configs/router.yaml

## 2026-01-28 — PROMPT 03 configs/router.yaml
**Status**: TODO → DONE
**Output**: configs/router.yaml
**Summary**: Added v4.2 router state machine definition with HOLDOUT states wired and transitions set.
**Next**: PROMPT 04 — Config Resolver + Validator

## 2026-01-28 — PROMPT 04 Config Resolver + Validator
**Status**: TODO → DONE
**Output**: scripts/validate_configs.py; crypto_backtest/v4/config.py; scripts/test_config_resolution.py
**Summary**: Implemented config validator and resolver utilities with inheritance/rescue support plus basic resolution tests.
**Next**: PROMPT 05 — SKIP (CSCV exists)

## 2026-01-28 — PROMPT 05 CSCV Param Compatibility
**Status**: TODO → DONE
**Output**: crypto_backtest/validation/pbo_cscv.py
**Summary**: Verified CSCV module and added a compatibility wrapper to accept folds/purge_bars/embargo_bars/annualization_factor.
**Next**: PROMPT 06 — Artifacts Layout

## 2026-01-28 — PROMPT 06 Artifacts Layout
**Status**: TODO → DONE
**Output**: crypto_backtest/v4/artifacts.py; scripts/init_run_v4_2.py
**Summary**: Added v4.2 run layout utilities (subdirs, metadata, snapshots) and an init script for run setup.
**Next**: PROMPT 07 — Screening (L/S) 100 Trials

## 1324 DONE jordan-dev -> system: CHALLENGER 100-TRIALS PIPELINE ✅

**Task**: Test hypothesis that reducing trials (300→100) reduces PBO overfitting  
**Status**: ✅ COMPLETE - HYPOTHESIS CONFIRMED

### Hypothesis
PR#20 PBO revealed 66% EXCLU rate (12/18 assets) with PBO > 0.70. Theory: 300 trials = higher chance of finding overfitted params by random chance. Reducing to 100 trials should reduce PBO values.

### Configuration
```bash
python scripts/run_full_pipeline.py \
  --assets BTC ETH SOL AVAX \
  --trials-atr 100 --trials-ichi 100 \
  --workers 1 --run-guards \
  --output-prefix challenger_100trials
```

**Assets**: BTC, ETH, SOL, AVAX  
**Rationale**: 3/4 were EXCLU with 300 trials, testing if 100T improves  
**Trials**: 100 ATR + 100 Ichimoku (vs baseline 300 each)  
**Workers**: 1 (sequential, reproducible)  
**Guards**: ON  
**ETA**: 2-3 hours (~15:30 UTC completion)

### Baseline (300 trials, PR#20)
| Asset | Sharpe OOS | PBO | Verdict |
|-------|------------|-----|---------|
| BTC | -0.18 | **0.9333** | EXCLU |
| SOL | 3.25 | **0.7333** | EXCLU |
| AVAX | 2.16 | **0.7333** | EXCLU |
| ETH | 3.22 | N/A | Not tested |

**Expected**: PBO < 0.50 (PASS threshold) with reduced trials

### Monitoring
- `python scripts/monitor_challenger.py`
- `logs/CHALLENGER_100TRIALS_LOG.md`
- Terminal PID: 215804

### Results Summary

**Completion**: 17:22:57 UTC (4h 1min runtime)  
**PBO Calculation**: Complete

| Asset | 300T PBO | 100T PBO | Change | Verdict Change |
|-------|----------|----------|--------|----------------|
| BTC | 0.9333 | 0.9333 | ±0% | EXCLU → EXCLU (no change) |
| ETH | N/A | **0.1333** | New | **PASS** ✅ |
| SOL | 0.7333 | **0.3333** | **-54.5%** | **EXCLU → PASS** ✅ |
| AVAX | 0.7333 | **0.1333** | **-81.8%** | **EXCLU → PASS** ✅ |

**Key Findings**:
- **Pass Rate**: 0% (300T) → **75% (100T)**
- **Average PBO Reduction**: **-68.2%** (for improvable assets)
- **Performance Trade-off**: -5% to -9% Sharpe reduction (acceptable)
- **Verdict**: HYPOTHESIS CONFIRMED ✅

### Decision

**RECOMMENDATION**: Rerun ALL 18 assets with 100 trials
- Expected: 8-10 assets upgrade from EXCLU → PASS
- New standard: 100 trials for ATR + Ichimoku optimization
- Update pipeline defaults and documentation

**Files Generated**:
- `reports/CHALLENGER_PBO_COMPARISON.md` (full analysis)
- `reports/CHALLENGER_FULL_COMPARISON.csv` (data)
- `outputs/*_pbo_challenger100_*.json` (PBO results)

**Started**: 13:21:27 UTC  
**Completed**: 17:22:57 UTC  
**Duration**: 4h 1min

---

## 1045 DONE jordan-dev -> system: PR#20 MEGA BATCH RE-RUN (PBO FIX)

**Task**: Re-run PR#20 MEGA BATCH with PBO calculations enabled (3 batches in parallel)
**Status**: ✅ COMPLETE - All batches finished, PBO calculated (18 assets)

### Issue Found & Fixed

**Problem**: PBO (guard008) was returning None values in guards CSV
- **Root Cause**: `--returns-matrix-dir` was not being passed to guards script
- **Impact**: 18/18 assets missing PBO validation (all showing all_pass=False)

**Fix Applied**:
- Modified `scripts/run_full_pipeline.py` line 290
- Now passes `--returns-matrix-dir outputs` when calling guards script
- Returns_matrix files ARE being saved (verified 18 files present)

**Expected Results**:
- PBO values will now be calculated and returned
- Guard results will show accurate all_pass status
- Better filtering of overfitting candidates

### Execution Plan

```bash
# Batch 1: YGG, MINA, CAKE, RUNE (PROD priority)
# Batch 2: EGLD, AVAX, BTC, SOL (Major assets)
# Batch 3: HBAR, TON, SUSHI, CRV, ONE, SEI, AXS, AAVE, ZIL, GALA (Candidates)
# Total: 18 assets, ~4-5 hours estimated
```

### Execution Status (27 Jan 2026)

**Batch 1** (4 assets: YGG, MINA, CAKE, RUNE)
- Status: ✅ COMPLETE (~13:30 UTC)
- Task ID: b79322e (previous)
- Results: Returns_matrix files generated ✓

**Batch 2 + Batch 3 LAUNCHED IN PARALLEL** (14 assets total)
- Batch 2: Task ID `b59215d` (EGLD, AVAX, BTC, SOL)
- Batch 3: Task ID `b068ecd` (HBAR, TON, SUSHI, CRV, ONE, SEI, AXS, AAVE, ZIL, GALA)
- Status: 🔄 RUNNING (parallel execution)
- Started: 27 Jan ~10:45 UTC
- Expected Completion: ~17:00-18:00 UTC (parallel saves ~4-5h)
- Output: PBO values will be present in all guard CSVs

### Next Steps
1. ✅ Batch 1 complete (YGG, MINA, CAKE, RUNE with PBO)
2. ⏳ Wait for Batch 2-3 to complete (~7h from now)
3. Analyze guard results and identify assets passing 8/8 guards
4. Classify assets:
   - **TIER 1**: All 8 guards PASS → Production ready
   - **TIER 2**: 7/8 guards PASS → Rescue candidates
   - **TIER 3**: <7/8 guards PASS → Further analysis needed
5. Make Phase 3 rescue decision (expected: GO for 4 TIER-2 assets)

---

## TODO 🔴🔴🔴 — Regime Stress Test Script
**Assigné**: Jordan
**Fichier**: scripts/run_regime_stress_test.py
**Spec**:
- CLI: --asset, --regimes (MARKDOWN, SIDEWAYS), --output
- Filtrer bars par ENTRY regime (pas exit) via regime_v3.py
- Critères PASS/FAIL:
  - MARKDOWN: ≤10 trades OU Sharpe ≥ -2
  - SIDEWAYS: Sharpe ≥ 0, sinon EXCLU
- Output CSV: asset, regime, trades, sharpe, max_dd, verdict
**Tests**: tests/test_regime_stress.py
**Validation**: python scripts/run_regime_stress_test.py --asset ETH --regimes MARKDOWN SIDEWAYS

## 27 Jan 2026 ? Regime Stress Test Script
**Status**: TODO ? DONE
**Output**: scripts/run_regime_stress_test.py; tests/test_regime_stress.py
**Summary**: Mise ? jour du script pour filtrer les trades par r?gime d'entr?e (MARKDOWN/SIDEWAYS) via regime_v3, nouveaux crit?res PASS/FAIL, CLI conforme et export CSV standard. Ajout de tests unitaires pour mapping r?gimes, filtre d'entr?e, verdicts et stats.
**Next**: Alex ? CPCV Full Implementation (comms/alex-lead.md)


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

**Status**: 🔄 IN PROGRESS — MEGA BATCH RUNNING (18 assets)  
**Started**: 27 Jan 2026, 04:26 UTC  
**PID**: 160712  
**Expected Completion**: ~08:30 UTC (3.5-4 hours)

## 0426 INPROGRESS jordan-dev -> casey-quant: PR#20 MEGA BATCH STARTED

**Decision**: Skip Phase 1 screening, go direct to Phase 2 validation (Option A)  
**Rationale**: Coherence with Batch 1-2, prioritize PROD candidates, comparable results

**Assets**: 18 total (4 PROD + 14 supplementary)
- **PROD Priority**: YGG, MINA, CAKE, RUNE
- **Ex-PROD**: EGLD, AVAX (regime exclusion, worth retesting)
- **Majors**: BTC, SOL
- **Candidates**: HBAR, TON, SUSHI, CRV, ONE, SEI, AXS, AAVE, ZIL, GALA

**Configuration**: baseline, 300 trials ATR/Ichi, workers=1, guards ON  
**Context**: Batch 1 (4/4 PASS) + Batch 2 (3/4 PASS) completed

**Previous Results Summary**:
- **Batch 1**: SHIB 5.05, DOT 2.67, TIA 2.86, NEAR 3.11 ✅
- **Batch 2**: ETH 4.18, ANKR 3.35, DOGE 3.05 ✅ | JOE 2.12 ❌

**Next**: Mid-batch checkpoint at 50% (~06:30 UTC)

---

## Previous Entries

### 2230 DONE jordan-dev -> casey-quant: PR#19 Integration Complete

[See previous entry in document history]
