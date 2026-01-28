# v4.2 Audit + Contract (1H Calibration)

Date: 2026-01-28
Branch: v4.2-pipeline-1h

## Discovered Entrypoints (paths + purpose)
- `scripts/run_full_pipeline.py`: multi-asset scan pipeline (download -> optimize -> cluster -> optional guards).
- `scripts/orchestrator.py`: phase orchestration wrapper (sets trials/workers and chains steps).
- `scripts/run_guards_multiasset.py`: guards runner + overfitting diagnostics; writes multiple guard outputs.
- `scripts/run_phase3b_optimization.py`: phase 3B optimization and consolidation.
- `scripts/run_phase3a_rescue.py`: rescue pipeline runs with selectable trial counts.
- `scripts/run_filter_rescue.py`: filter-preset rescue runner.
- `scripts/run_displacement_grid.py`: displacement grid search runner.
- `scripts/run_cscv_pbo_challenger.py`, `scripts/calc_pbo_*.py`: PBO/CSCV utilities on returns matrices.
- `scripts/portfolio_construction.py`, `scripts/portfolio_correlation.py`, `scripts/portfolio_stress_test.py`: portfolio analytics outputs.
- `crypto_backtest/optimization/parallel_optimizer.py`: core Optuna-based scan/optimization and `run_backtest` glue.
- `crypto_backtest/optimization/bayesian.py`: single-asset Bayesian optimization wrapper.
- `crypto_backtest/engine/backtest.py`: vectorized backtest engine + `BacktestResult`.
- `crypto_backtest/strategies/final_trigger.py`: primary strategy implementation.

## Existing Artifact Patterns
- Output root: `outputs/` with timestamped CSVs, e.g. `multiasset_scan_*.csv`, `*_guards_*.csv`, `*_summary_*.csv`.
- Run manager layout: `outputs/run_<timestamp>/` with `manifest.json`, `scan.csv`, `guards.csv`, `params/<ASSET>.json` (see `crypto_backtest/utils/run_manager.py`).
- Returns matrices: NumPy `.npy` files written by `crypto_backtest/optimization/parallel_optimizer.py` and consumed by PBO scripts.
- PBO/analysis artifacts: JSON files written by `scripts/calc_pbo_*.py` and `scripts/run_guards_multiasset.py`.
- Reports: text/CSV summaries in `reports/` and `outputs/*_validation_report_*.txt` (via analysis scripts).

## Data Structures Available
- `BacktestConfig`, `BacktestResult` (`crypto_backtest/engine/backtest.py`).
- Trades as `pd.DataFrame` with `entry_time`, `exit_time`, `pnl`/`net_pnl`/`gross_pnl`, `direction` (varies by module).
- Equity curve as `pd.Series` (aligned to OHLCV index).
- Returns matrices as `np.ndarray` shaped `(n_trials, n_bars)` for PBO/CSCV.
- Guards outputs as `pd.DataFrame` (multi-asset summaries) and JSON dicts for PBO guard outputs.
- Session/manifest metadata as JSON (see `crypto_backtest/config/session_manager.py` and `crypto_backtest/utils/run_manager.py`).

## Calibration 1H
- timeframe: 1H
- dataset_bars: 17520
- dataset_window: 2024-01-28 17:00 UTC -> 2026-01-27 16:00 UTC
- holding: P95=106, P99=230
- returns: bar-level sparse
