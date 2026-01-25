"""
Test OP with ADX filter integration.

Since OP has severe overfit (WFE=0.01), test if ADX filtering helps.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import argparse
import json
from datetime import datetime

import pandas as pd
import numpy as np

from crypto_backtest.optimization.parallel_optimizer import (
    load_data,
    split_data,
    optimize_atr,
    optimize_ichimoku,
    build_strategy_params,
    run_backtest,
    OPTIM_CONFIG,
)
from crypto_backtest.indicators.adx_filter import compute_adx
from crypto_backtest.engine.backtest import BacktestConfig, VectorizedBacktester
from crypto_backtest.strategies.final_trigger import FinalTriggerStrategy
from crypto_backtest.optimization.bayesian import _instantiate_strategy


BASE_CONFIG = BacktestConfig(
    initial_capital=10000.0,
    fees_bps=5.0,
    slippage_bps=2.0,
    sizing_mode="fixed",
    intrabar_order="stop_first",
)


def run_with_adx_filter_full(
    data: pd.DataFrame,
    params: dict,
    adx_period: int = 14,
    adx_threshold: float = 25.0,
) -> dict:
    """
    Run backtest with ADX filter by modifying strategy signals.
    
    This creates a modified version of signals filtered by ADX.
    """
    from crypto_backtest.optimization.bayesian import _instantiate_strategy
    
    # Compute ADX
    adx = compute_adx(data["high"], data["low"], data["close"], adx_period)
    adx_shifted = adx.shift(1)  # Avoid look-ahead
    is_trending = adx_shifted > adx_threshold
    
    # Run strategy with modified params that include ADX awareness
    # Note: This is a simplified approach for testing
    strategy = _instantiate_strategy(FinalTriggerStrategy, params)
    backtester = VectorizedBacktester(BASE_CONFIG)
    
    # Get base result
    result_base = backtester.run(data, strategy)
    
    # Filter trades by ADX
    if not result_base.trades.empty:
        trades_filtered = result_base.trades.copy()
        
        # Map entry_time to index
        entries = pd.to_datetime(trades_filtered["entry_time"], utc=True)
        entry_idx = data.index.get_indexer(entries, method="nearest")
        
        # Check ADX at entry time
        trades_filtered["adx_at_entry"] = [
            adx_shifted.iloc[idx] if 0 <= idx < len(adx_shifted) else np.nan
            for idx in entry_idx
        ]
        trades_filtered = trades_filtered[trades_filtered["adx_at_entry"] > adx_threshold]
        
        # Recalculate metrics with filtered trades
        if not trades_filtered.empty:
            from crypto_backtest.analysis.metrics import compute_metrics
            
            # Rebuild equity curve from filtered trades
            equity = pd.Series(BASE_CONFIG.initial_capital, index=data.index)
            exits = pd.to_datetime(trades_filtered["exit_time"], utc=True)
            exit_idx_arr = data.index.get_indexer(exits, method="nearest")
            
            for idx, (_, trade) in enumerate(trades_filtered.iterrows()):
                exit_idx = exit_idx_arr[idx]
                if 0 <= exit_idx < len(equity):
                    equity.iloc[exit_idx:] += trade["pnl"]
            
            metrics = compute_metrics(equity, trades_filtered)
            
            return {
                "sharpe": float(metrics.get("sharpe_ratio", 0.0)),
                "trades": int(len(trades_filtered)),
                "total_return": float(metrics.get("total_return", 0.0) * 100.0),
                "max_drawdown": float(metrics.get("max_drawdown", 0.0) * 100.0),
            }
        else:
            return {
                "sharpe": 0.0,
                "trades": 0,
                "total_return": 0.0,
                "max_drawdown": 0.0,
            }
    else:
        return {
            "sharpe": 0.0,
            "trades": 0,
            "total_return": 0.0,
            "max_drawdown": 0.0,
        }


def test_op_with_adx(
    data_dir: str = "data",
    n_trials: int = 60,
    adx_thresholds: list[float] = [20.0, 25.0, 30.0],
) -> dict:
    """
    Test OP with different ADX thresholds.
    """
    asset = "OP"
    
    print("=" * 70)
    print(f"OP + ADX FILTER TEST")
    print("=" * 70)
    
    # Load data
    df = load_data(asset, data_dir)
    df = df.iloc[OPTIM_CONFIG["warmup_bars"]:]
    df_is, df_val, df_oos = split_data(df, splits=(0.6, 0.2, 0.2))
    
    print(f"Data: IS={len(df_is)}, VAL={len(df_val)}, OOS={len(df_oos)} bars")
    
    # Optimize parameters (baseline)
    print("\n--- Optimizing parameters (baseline) ---")
    atr_params, _ = optimize_atr(df_is, n_trials=n_trials, min_trades=30, enforce_tp_progression=True)
    ichi_params, _ = optimize_ichimoku(df_is, atr_params, n_trials=n_trials, min_trades=30)
    
    final_params = build_strategy_params(
        sl_mult=atr_params["sl_mult"],
        tp1_mult=atr_params["tp1_mult"],
        tp2_mult=atr_params["tp2_mult"],
        tp3_mult=atr_params["tp3_mult"],
        tenkan=ichi_params["tenkan"],
        kijun=ichi_params["kijun"],
        tenkan_5=ichi_params["tenkan_5"],
        kijun_5=ichi_params["kijun_5"],
    )
    
    print(f"Optimized params: SL={atr_params['sl_mult']:.2f}, TP1={atr_params['tp1_mult']:.2f}")
    
    # Run baseline (no filter)
    print("\n--- Running baseline (no ADX filter) ---")
    is_baseline = run_backtest(df_is, final_params)
    oos_baseline = run_backtest(df_oos, final_params)
    wfe_baseline = oos_baseline["sharpe"] / is_baseline["sharpe"] if is_baseline["sharpe"] > 0 else 0
    
    print(f"Baseline IS:  Sharpe={is_baseline['sharpe']:.2f}, Trades={is_baseline['trades']}")
    print(f"Baseline OOS: Sharpe={oos_baseline['sharpe']:.2f}, Trades={oos_baseline['trades']}")
    print(f"Baseline WFE: {wfe_baseline:.2f}")
    
    # Test different ADX thresholds
    results = {
        "asset": asset,
        "baseline": {
            "is_sharpe": is_baseline["sharpe"],
            "oos_sharpe": oos_baseline["sharpe"],
            "wfe": wfe_baseline,
            "oos_trades": oos_baseline["trades"],
        },
        "adx_tests": {},
    }
    
    for threshold in adx_thresholds:
        print(f"\n--- Testing ADX threshold={threshold} ---")
        
        oos_adx = run_with_adx_filter_full(df_oos, final_params, adx_period=14, adx_threshold=threshold)
        
        if oos_adx["trades"] > 0:
            is_adx = run_with_adx_filter_full(df_is, final_params, adx_period=14, adx_threshold=threshold)
            wfe_adx = oos_adx["sharpe"] / is_adx["sharpe"] if is_adx["sharpe"] > 0 else 0
            
            print(f"  IS:  Sharpe={is_adx['sharpe']:.2f}, Trades={is_adx['trades']}")
            print(f"  OOS: Sharpe={oos_adx['sharpe']:.2f}, Trades={oos_adx['trades']}")
            print(f"  WFE: {wfe_adx:.2f}")
            
            results["adx_tests"][f"threshold_{threshold}"] = {
                "threshold": threshold,
                "is_sharpe": is_adx["sharpe"],
                "oos_sharpe": oos_adx["sharpe"],
                "wfe": wfe_adx,
                "oos_trades": oos_adx["trades"],
                "improvement_vs_baseline": wfe_adx - wfe_baseline,
            }
        else:
            print(f"  No trades with ADX>{threshold}")
            results["adx_tests"][f"threshold_{threshold}"] = {
                "threshold": threshold,
                "oos_trades": 0,
                "improvement_vs_baseline": None,
            }
    
    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Baseline WFE: {wfe_baseline:.2f}")
    
    best_threshold = None
    best_wfe = wfe_baseline
    
    for test_name, test_result in results["adx_tests"].items():
        if test_result.get("wfe", 0) > best_wfe:
            best_wfe = test_result["wfe"]
            best_threshold = test_result["threshold"]
    
    if best_threshold:
        print(f"\nBest ADX threshold: {best_threshold} (WFE={best_wfe:.2f})")
        print(f"WFE improvement: {best_wfe - wfe_baseline:.2f}")
    else:
        print("\nNo ADX threshold improves WFE")
    
    return results


def main():
    parser = argparse.ArgumentParser(description="Test OP with ADX Filter")
    parser.add_argument("--trials", type=int, default=60, help="Optimization trials")
    parser.add_argument("--data-dir", type=str, default="data", help="Data directory")
    parser.add_argument("--thresholds", nargs="+", type=float, default=[20.0, 25.0, 30.0], help="ADX thresholds")
    args = parser.parse_args()
    
    results = test_op_with_adx(
        data_dir=args.data_dir,
        n_trials=args.trials,
        adx_thresholds=args.thresholds,
    )
    
    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    Path("outputs").mkdir(exist_ok=True)
    
    output_path = f"outputs/op_adx_test_{timestamp}.json"
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\nResults saved to: {output_path}")


if __name__ == "__main__":
    main()
