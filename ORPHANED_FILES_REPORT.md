# Orphaned Files Report

**Generated:** 2026-01-24  
**Context:** Post-Optuna fix, all results before 2026-01-24 are INVALID per `project-state.md`

---

## Summary

| Category | Count | Action |
|----------|-------|--------|
| Invalid Outputs (pre-cutoff) | ~1413 | DELETE |
| Root Log Files | 35 | DELETE |
| Root One-off Scripts | ~15 | REVIEW/DELETE |
| Orphaned Folders | 2 | DELETE |
| Obsolete Docs | ~15 | DELETE/ARCHIVE |
| Stray Data Files | 3 | DELETE |
| Obsolete Markdown Reports | ~30 | DELETE |

---

## 1. Invalid Outputs (HIGH PRIORITY)

### Location: `/workspace/outputs/`

All files with timestamps `20260121`, `20260122`, `20260123` in filename (~1413 files) are **INVALID** due to the Optuna reproducibility bug. Only files dated `20260124` and later should be kept.

**Files to delete:**
- `outputs/*_20260121_*.csv`
- `outputs/*_20260122_*.csv`
- `outputs/*_20260123_*.csv`
- `outputs/*_20260121_*.txt`
- `outputs/*_20260122_*.txt`
- `outputs/*_20260123_*.txt`
- `outputs/*_20260121_*.json`
- `outputs/*_20260122_*.json`
- `outputs/*_20260123_*.json`

**Command to delete:**
```bash
find outputs -name "*20260121*" -o -name "*20260122*" -o -name "*20260123*" | xargs rm -f
```

---

## 2. Root Log Files (DELETE ALL)

### Location: `/workspace/*.log`

35 log files from old runs that are no longer relevant:

```
optim_batch1.log
optim_batch2.log
optim_100alts.log
optim_fullrun_disp65_group.log
optim_fullrun_JOE_disp26.log
optim_DOGE_disp26.log
optim_LINK_disp39.log
optim_OP_disp78.log
displacement_grid_batch3.log
guards_OP_disp78.log
guards_new13.log
download_large_universe.log
download_top50.log
full_fix_test_round1.log
full_fix_test_round2.log
stability_test.log
stability_test_reopt.log
stability_test_full_fix.log
stability_test_final_run1.log
test_gala.log
gala_test.log
prod_validation_run1.log
repro_test_run3.log
repro_test_run4.log
phase1_batch3_rerun.log
```

Also in `/workspace/outputs/`:
```
outputs/doge_run.log
outputs/avax_run.log
outputs/ygg_test_run.log
outputs/winners_batch_run.log
outputs/uni_moderate_run.log
outputs/uni_run.log
outputs/pipeline_egld_imx.log
outputs/second_tier_run.log
outputs/p3_batch_run.log
outputs/phase1_batch3_run.log
outputs/op_run.log
```

**Command to delete:**
```bash
rm -f *.log outputs/*.log
```

---

## 3. Orphaned Root-Level Python Scripts

### Location: `/workspace/*.py` (excluding `app.py`)

These appear to be one-off development/test scripts NOT part of the main pipeline:

| File | Status | Reason |
|------|--------|--------|
| `backtest_optimized.py` | ORPHANED | One-off script, not imported |
| `backtest_sltp_optimized.py` | ORPHANED | One-off script, not imported |
| `fetch_binance_data.py` | ORPHANED | Replaced by `scripts/download_data.py` |
| `optimize_binance.py` | ORPHANED | One-off script |
| `optimize_ichimoku.py` | ORPHANED | One-off script |
| `optimize_focused.py` | ORPHANED | One-off script |
| `optimize_sltp_only.py` | ORPHANED | One-off script |
| `monte_carlo_permutation.py` | ORPHANED | One-off script, logic in `crypto_backtest/analysis/` |
| `multi_asset_optimization.py` | ORPHANED | Replaced by `scripts/run_full_pipeline.py` |
| `multi_asset_validation.py` | ORPHANED | Replaced by `scripts/run_guards_multiasset.py` |
| `regime_analysis.py` | ORPHANED | One-off analysis |
| `regime_analysis_v2.py` | ORPHANED | One-off analysis |
| `regime_reconciliation.py` | ORPHANED | One-off analysis |
| `sensitivity_analysis.py` | ORPHANED | Logic in guards |
| `sideways_filter_test.py` | ORPHANED | One-off test |
| `stress_test_fees.py` | ORPHANED | Logic in guards |
| `walk_forward_analysis.py` | ORPHANED | Logic in `crypto_backtest/optimization/walk_forward.py` |
| `guard_batch_analysis.py` | ORPHANED | One-off analysis |
| `test_doge_diagnostic.py` | ORPHANED | Debug script |
| `test_doge_kama_final.py` | ORPHANED | Debug script |
| `test_doge_kama_quick.py` | ORPHANED | Debug script |
| `test_doge_kama_simple.py` | ORPHANED | Debug script |
| `test_doge_reopt_kama.py` | ORPHANED | Debug script |

**Keep:**
- `app.py` - Streamlit dashboard (active)

---

## 4. Orphaned Folders

### `/workspace/indicators/` (ORPHANED)

This folder contains duplicate/old implementations:
- `__init__.py`
- `ichimoku.py`
- `signals.py`

**Not imported anywhere** - the main code uses `crypto_backtest.indicators`.

### `/workspace/config/` (PARTIALLY ORPHANED)

Contains:
- `__init__.py` - Keep (may be needed)
- `filter_modes.py` - Keep (used)
- `diagnostic_history.json` - DELETE (debug artifact)
- `machine_profile.json` - DELETE (debug artifact)

---

## 5. Stray Data Files

| File | Location | Action |
|------|----------|--------|
| `BYBIT_BTCUSDT, 60 (1).csv` | `/workspace/crypto_backtest/` | DELETE |
| `btc_for_compare_signals.csv` | `/workspace/` | DELETE |
| `compare_report.csv` | `/workspace/` | DELETE |
| `kama.csv` | `/workspace/` (empty file) | DELETE |

---

## 6. Obsolete Markdown Reports at Root

Many of these are historical and contain **INVALID** information:

| File | Status |
|------|--------|
| `BUG_FIX_REPORT.md` | OBSOLETE - historical |
| `DEPLOYMENT_SUMMARY.txt` | OBSOLETE - pre-fix |
| `EXECUTIVE_SUMMARY.md` | OBSOLETE - pre-fix |
| `FINAL_VERIFICATION.txt` | OBSOLETE - pre-fix |
| `IMPLEMENTATION_CHECKLIST.md` | OBSOLETE - pre-fix |
| `LAUNCH_READY.md` | OBSOLETE - pre-fix, invalid claims |
| `NEXT_STEPS.md` | OBSOLETE - pre-fix |
| `NEXT_STEPS_POST_OVERNIGHT.md` | OBSOLETE - pre-fix |
| `NEXT_STEPS_SUMMARY.md` | OBSOLETE - pre-fix |
| `OPTUNA_CONFIGURATION_FIX.md` | KEEP - documents the fix |
| `OVERNIGHT_PLAN.md` | OBSOLETE - executed |
| `OVERNIGHT_PROGRESS_REPORT.md` | OBSOLETE - pre-fix |
| `RECOMMENDED_ASSETS_PHASE1.md` | OBSOLETE - assets need re-screening |
| `REPRODUCIBILITY_FIX_COMPLETE.md` | KEEP - documents the fix |
| `REPRODUCIBILITY_FIX_VERIFICATION.md` | KEEP - documents verification |
| `REPRODUCIBILITY_STRATEGY.md` | OBSOLETE - strategy executed |
| `RESET_SUMMARY.md` | KEEP - explains reset |
| `SAM_VALIDATION_PREP_REPORT.md` | OBSOLETE - pre-fix |
| `SCRIPT_VERIFICATION.md` | OBSOLETE - pre-fix |
| `memo.md` | REVIEW - may contain useful notes |
| `instructions.md` | REVIEW - may contain useful instructions |

---

## 7. Obsolete Markdown in `/workspace/outputs/`

All 28 `.md` files in outputs are investigation/status reports from **before the fix**:

```
COMPLEX_NUMBER_BUG_INVESTIGATION.md
COMPLEX_NUMBER_FIX_APPLIED.md
BUG_COMPLEX_INVESTIGATION_V4.md
CODEX_MULTI_ASSET_005.md
ALEX_RD_RESEARCH_FINDINGS.md
ANALYSIS_FILTER_GRID_ETH_20260122.md
FILTER_GRID_ETH_SUMMARY.md
HBAR_VARIANTS_PROPOSAL.md
STATUS_*.md (multiple)
RESUME_*.md
P0_*.md
PHASE3B_*.md
```

**Action:** DELETE all (historical investigation artifacts)

---

## 8. Obsolete Docs

### `/workspace/docs/HANDOFF.md` (MARKED OBSOLETE)

Explicitly marked as **OBSOLETE** in `MASTER_PLAN.mdc`. Should be deleted.

### Other docs to review:
- `BACKTESTING.md` - Historical only per MASTER_PLAN
- `BRIEF_PARALLEL_GUARDS_V2.md` - Review
- `REOPT_DIAGNOSTICS.md` - Review
- `OVERNIGHT_PIPELINE_POSTMORTEM.md` - Historical

---

## 9. Pine Script Files

| File | Status |
|------|--------|
| `pinescript_strategy_match.pine` | REVIEW - may be reference |
| `FT_BTC.pine` | GENERATED - keep if valid |
| `FT_ETH.pine` | GENERATED - keep if valid |
| `FT_AVAX.pine` | GENERATED - may be invalid |
| `FT_UNI.pine` | GENERATED - may be invalid |
| `FT_SEI.pine` | GENERATED - may be invalid |

Also text versions:
- `pinescriptmodel.txt` - Reference model
- `pinescriptmodelMAJ.txt` - Updated model
- `pinescrpt1.txt` - Old version

---

## 10. Timestamped Config Files (Orphaned Snapshots)

### `/workspace/crypto_backtest/config/cluster_params_*.py`

15 timestamped snapshot files that are no longer needed:
```
cluster_params_20260120_1347.py
cluster_params_20260120_1546.py
cluster_params_20260120_1603.py
cluster_params_20260121_1619.py
cluster_params_20260121_1751.py
cluster_params_20260122_0056.py
cluster_params_20260122_2327.py
cluster_params_20260123_2243.py
cluster_params_20260123_2301.py
cluster_params_20260123_2302.py
cluster_params_20260124_0026.py
cluster_params_20260124_0126.py
cluster_params_20260124_0139.py
cluster_params_20260124_0344.py
cluster_params_20260124_0416.py
```

**Keep only:** `cluster_params.py` (current)

---

## Recommended Cleanup Commands

```bash
# 1. Delete invalid outputs (pre-cutoff dates)
find outputs -name "*20260121*" -delete
find outputs -name "*20260122*" -delete  
find outputs -name "*20260123*" -delete

# 2. Delete all log files
rm -f *.log outputs/*.log

# 3. Delete obsolete markdown in outputs
rm -f outputs/*.md

# 4. Delete orphaned root-level scripts (REVIEW FIRST)
# rm -f backtest_optimized.py backtest_sltp_optimized.py fetch_binance_data.py
# rm -f optimize_*.py monte_carlo_permutation.py multi_asset_*.py
# rm -f regime_*.py sensitivity_analysis.py sideways_filter_test.py
# rm -f stress_test_fees.py walk_forward_analysis.py guard_batch_analysis.py
# rm -f test_doge_*.py

# 5. Delete orphaned indicators folder
rm -rf indicators/

# 6. Delete stray data files
rm -f "crypto_backtest/BYBIT_BTCUSDT, 60 (1).csv"
rm -f btc_for_compare_signals.csv compare_report.csv kama.csv

# 7. Delete obsolete config snapshots
rm -f crypto_backtest/config/cluster_params_202601*.py

# 8. Delete obsolete docs
rm -f docs/HANDOFF.md

# 9. Delete obsolete root markdown (REVIEW FIRST)
# Keep: README.md, claude.md, OPTUNA_CONFIGURATION_FIX.md, 
#       REPRODUCIBILITY_FIX_*.md, RESET_SUMMARY.md
```

---

## Files to KEEP

| File/Folder | Reason |
|-------------|--------|
| `app.py` | Active Streamlit dashboard |
| `README.md` | Project documentation |
| `claude.md` | Agent instructions |
| `crypto_backtest/` | Main codebase |
| `scripts/` | Active pipeline scripts |
| `tests/` | Test suite |
| `tools/` | Utility tools |
| `data/` | Data folder |
| `.cursor/`, `.claude/` | Config |
| `.streamlit/` | Streamlit config |
| `status/` | Project state |
| `comms/` | Agent communication |
| `examples/` | Usage examples |
| `OPTUNA_CONFIGURATION_FIX.md` | Documents critical fix |
| `REPRODUCIBILITY_FIX_*.md` | Documents critical fixes |
| `RESET_SUMMARY.md` | Explains current reset state |
| `pytest.ini` | Test config |

---

## Estimated Space Savings

- Invalid outputs: ~150-200 MB
- Log files: ~10-20 MB
- Total: ~170-220 MB
