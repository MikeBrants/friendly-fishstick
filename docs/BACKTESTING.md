# Backtesting Dossier - FINAL TRIGGER v2

This file is the single source of truth for all backtesting results, issues, and next steps.
`docs/HANDOFF.md` stays short and links here.

## Scope
- Multi-asset scans, displacement grids, and full pipeline runs
- Guard results and anomaly investigations
- Issues, challenges, and analysis notes
- Next steps and recommended reruns

## Current status snapshot (2026-01-21)
- Production validated (scan): BTC, ETH, XRP, AVAX, UNI, SUI, SEI
- Production validated (full guards): BTC, ETH, AVAX, UNI, SEI (SUI excluded by guards)
- New 13 assets guards (run_id `20260121_201821`): PASS = AR, EGLD, CELO, ANKR
- Anomaly check for HOOK/ALICE/HMSTR: trades < 60 and/or data < 10000 bars, no guards rerun

Key outputs:
- `outputs/multiasset_guards_summary_20260121_201821.csv`
- `outputs/anomaly_investigation_20260121_205300.csv`

## Recent runs and outputs

### Top 50 (two batches, excluding BTC/ETH/AVAX/UNI/SEI)
- PASS: DOT, SHIB, NEAR, SUI, APT
- FAIL: SOL, XRP, BNB, ADA, DOGE, LINK, MATIC, LTC, ATOM, XLM, FIL, ARB, OP, INJ, RENDER, FET, TAO, PEPE, WIF, BONK, AAVE, MKR, CRV, SNX, SAND
Outputs:
- `outputs/multiasset_scan_20260121_1619.csv`
- `outputs/multiasset_scan_20260121_1626.csv`

### OP displacement
- Full run disp=78: OOS Sharpe 2.48, WFE 1.66, trades 90
- Guards: all pass (p=0.0000, sens var=5.34%, CI lower=2.01, stress1 sharpe=1.73)
Outputs:
- `outputs/displacement_grid_OP_20260121_173045.csv`
- `outputs/op_fullrun_disp78_20260121_174550.csv`
- `outputs/multiasset_guards_summary_20260121_175759.csv`

### Displacement grid (near-threshold FAIL set)
Results summary:
- SOL best=52 (no gain)
- DOGE best=26 (+2.18 Sharpe vs 52)
- LINK best=39 (+1.36 Sharpe vs 52)
Output: `outputs/displacement_grid_summary_20260121_175713.csv`

### Displacement grid batch3 (run 20260121_210728)
Best displacement by asset:
- AXS=39, CAKE=26, JOE=26, KSM=26, MINA=78, OSMO=65, RUNE=78, TON=78
Output:
- `outputs/displacement_grid_batch3_20260121_210728.csv`
- `outputs/displacement_grid_batch3_summary_20260121_210728.csv`

### Full runs with fixed displacement (latest)
- `outputs/multiasset_scan_20260121_2111.csv` (disp=26): CAKE PASS, JOE PASS, KSM FAIL (WFE 0.57)
- `outputs/multiasset_scan_20260121_2130.csv` (disp=39): AXS PASS
- Guards:
  - `outputs/multiasset_guards_summary_20260121_211152.csv` (CAKE/JOE/KSM)
  - `outputs/multiasset_guards_summary_20260121_213038.csv` (AXS)

## TP progression audit and enforcement
- Audit run across CSV outputs found 519 TP progression errors
  - Summary: `outputs/tp_progression_errors_summary_20260121_215436.csv`
  - Full list: `outputs/tp_progression_errors_20260121_215436.csv`
- Enforcement is now default-on in:
  - `crypto_backtest/optimization/parallel_optimizer.py`
  - `scripts/run_full_pipeline.py`
  - `scripts/run_displacement_grid.py`
- Override: `--no-enforce-tp-progression`
- Note: Older outputs (ex: `outputs/multiasset_scan_20260121_2111.csv`, `outputs/multiasset_scan_20260121_2130.csv`) include non-progressive TP ladders and should be rerun.

## Issues and challenges
- Guard errors (complex numbers): YGG, ARKM, STRK, METIS, AEVO in `outputs/multiasset_guards_summary_20260121_201821.csv`.
  Likely from metrics or data anomalies; needs targeted debug.
- Console encoding: `parallel_optimizer.py` prints unicode arrows/checks; when console is cp1252, it can crash.
  Workaround: run with `chcp 65001` and `PYTHONIOENCODING=utf-8`.
- Output overwrites: Some scans share the same timestamp (ex: `multiasset_scan_20260121_1759.csv` overwritten).
  Use `RunManager` or add higher-resolution timestamps to avoid collisions.
- Data length / trade count issues:
  - LOOM and HMSTR have short history
  - HOOK/ALICE/HMSTR often fail due to trades < 60

## Next steps (recommended)
1. Rerun assets with non-progressive TP outputs using default enforcement:
   - AXS (disp=39), CAKE/KSM (disp=26), any other winners you plan to keep
2. Run full pipelines for displacement winners not yet validated:
   - MINA disp=78, OSMO disp=65, RUNE disp=78, TON disp=78
3. Re-run guards for new winners after updated full runs.
4. Build `outputs/all_validated_assets.csv`, then run portfolio construction + stress test + final report.
5. Investigate guard errors for YGG/ARKM/STRK/METIS/AEVO (data quality or metric bug).

## Reference outputs
- Guard summaries: `outputs/multiasset_guards_summary_*.csv`
- Scan outputs: `outputs/multiasset_scan_*.csv`, `outputs/multi_asset_scan_*.csv`
- Displacement grids: `outputs/displacement_grid_*`
- Portfolio artifacts: `outputs/portfolio_*.csv`
