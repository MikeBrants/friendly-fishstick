# friendly-fishstick

## Optimization Workflow
1. Prepare OHLCV data (CSV/Parquet) with UTC timestamps.
2. Run the demo optimizer:
   - `python crypto_backtest/examples/optimize_final_trigger.py`
3. Customize the param space:
   - Edit `get_param_space()` in `crypto_backtest/examples/optimize_final_trigger.py`
   - Modes: `quick`, `full`, `toggles`
4. Validate signals vs Pine (when CSV export is available):
   - Place `data/ohlcv.csv` and `data/pine_signals.csv`, then run:
   - `python crypto_backtest/examples/compare_signals.py`
