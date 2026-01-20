"""Walk-Forward Analysis to validate strategy robustness."""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import timedelta

from crypto_backtest.strategies.final_trigger import FinalTriggerStrategy, FinalTriggerParams
from crypto_backtest.indicators.five_in_one import FiveInOneConfig
from crypto_backtest.indicators.ichimoku import IchimokuConfig
from crypto_backtest.engine.backtest import VectorizedBacktester, BacktestConfig
from crypto_backtest.analysis.metrics import compute_metrics
from crypto_backtest.optimization.bayesian import BayesianOptimizer

def load_binance_data(warmup: int = 200) -> pd.DataFrame:
    """Load Binance data with warmup."""
    df = pd.read_csv("data/Binance_BTCUSDT_1h.csv")
    df.columns = [col.strip() for col in df.columns]
    data = df[["open", "high", "low", "close"]].copy()

    if "volume" in df.columns:
        data["volume"] = df["volume"].fillna(0.0)
    else:
        data["volume"] = 0.0

    if "timestamp" in df.columns:
        data.index = pd.to_datetime(df["timestamp"], utc=True)

    return data.iloc[warmup:]

def run_backtest_with_params(data: pd.DataFrame, sl: float, tp1: float, tp2: float, tp3: float) -> dict:
    """Run backtest with given parameters."""
    five_in_one = FiveInOneConfig(
        use_distance_filter=False,
        use_volume_filter=False,
        use_regression_cloud=False,
        use_kama_oscillator=False,
        use_ichimoku_filter=True,
        ichi5in1_strict=False,
        use_transition_mode=False,
    )

    params = FinalTriggerParams(
        grace_bars=1,
        use_mama_kama_filter=False,
        sl_mult=sl,
        tp1_mult=tp1,
        tp2_mult=tp2,
        tp3_mult=tp3,
        five_in_one=five_in_one,
    )

    strategy = FinalTriggerStrategy(params)
    config = BacktestConfig(
        initial_capital=10000.0,
        fees_bps=5.0,
        slippage_bps=2.0,
        sizing_mode="fixed",
    )

    backtester = VectorizedBacktester(config)
    result = backtester.run(data, strategy)

    if len(result.trades) > 0:
        metrics = compute_metrics(result.equity_curve, result.trades)
        final_equity = result.equity_curve.iloc[-1]
        return {
            "sharpe": metrics.get('sharpe_ratio', 0),
            "sortino": metrics.get('sortino_ratio', 0),
            "return": (final_equity / config.initial_capital - 1) * 100,
            "max_dd": metrics.get('max_drawdown', 0),
            "win_rate": metrics.get('win_rate', 0),
            "trades": len(result.trades),
        }
    return None

def walk_forward_analysis(data: pd.DataFrame, in_sample_months: int = 6, out_sample_months: int = 1):
    """
    Perform walk-forward analysis.

    Args:
        data: Full dataset
        in_sample_months: Training window in months
        out_sample_months: Test window in months
    """
    print("=" * 70)
    print("WALK-FORWARD ANALYSIS")
    print("=" * 70)

    print(f"\nConfiguration:")
    print(f"  In-Sample (train): {in_sample_months} months")
    print(f"  Out-of-Sample (test): {out_sample_months} months")
    print(f"  Total data: {len(data)} bars ({len(data)//24:.0f} days)")

    # Calculate window sizes in hours
    in_sample_hours = in_sample_months * 30 * 24
    out_sample_hours = out_sample_months * 30 * 24

    # Setup param space for optimization
    BASE_PARAMS = {
        "grace_bars": 1,
        "use_mama_kama_filter": False,
        "require_fama_between": False,
        "strict_lock_5in1_last": False,
        "mama_fast_limit": 0.5,
        "mama_slow_limit": 0.05,
        "kama_length": 20,
        "atr_length": 14,
        "sl_mult": 3.0,
        "tp1_mult": 2.0,
        "tp2_mult": 6.0,
        "tp3_mult": 10.0,
        "ichimoku": {"tenkan": 9, "kijun": 26, "displacement": 52},
        "five_in_one": {
            "fast_period": 7, "slow_period": 19, "er_period": 8,
            "norm_period": 50, "use_norm": True, "ad_norm_period": 50,
            "use_ad_line": True, "ichi5in1_strict": False,
            "use_transition_mode": False, "use_distance_filter": False,
            "use_volume_filter": False, "use_regression_cloud": False,
            "use_kama_oscillator": False, "use_ichimoku_filter": True,
            "tenkan_5": 9, "kijun_5": 26, "displacement_5": 52,
        },
    }

    SEARCH_SPACE = {
        "sl_mult": {"type": "float", "low": 1.5, "high": 5.0, "step": 0.25},
        "tp1_mult": {"type": "float", "low": 1.0, "high": 4.0, "step": 0.25},
        "tp2_mult": {"type": "float", "low": 4.0, "high": 10.0, "step": 0.5},
        "tp3_mult": {"type": "float", "low": 6.0, "high": 15.0, "step": 0.5},
    }

    param_space = {
        "base_params": BASE_PARAMS,
        "search_space": SEARCH_SPACE,
        "objective": "sharpe_ratio",
        "direction": "maximize",
        "backtest_config": BacktestConfig(
            initial_capital=10000.0, fees_bps=5.0, slippage_bps=2.0,
            sizing_mode="fixed", intrabar_order="stop_first",
        ),
    }

    results = []
    optimizer = BayesianOptimizer()

    # Walk forward through data
    start_idx = 0
    window_num = 0

    while start_idx + in_sample_hours + out_sample_hours <= len(data):
        window_num += 1

        # Split data
        is_end = start_idx + in_sample_hours
        oos_end = is_end + out_sample_hours

        train_data = data.iloc[start_idx:is_end]
        test_data = data.iloc[is_end:oos_end]

        print(f"\n{'='*70}")
        print(f"Window {window_num}")
        print(f"{'='*70}")
        print(f"Train: {train_data.index[0]} to {train_data.index[-1]} ({len(train_data)} bars)")
        print(f"Test:  {test_data.index[0]} to {test_data.index[-1]} ({len(test_data)} bars)")

        # Optimize on in-sample
        print(f"\nOptimizing on in-sample data (20 trials)...")
        opt_result = optimizer.optimize(
            data=train_data,
            strategy_class=FinalTriggerStrategy,
            param_space=param_space,
            n_trials=20,
        )

        best_params = opt_result.best_params
        is_sharpe = opt_result.best_score

        print(f"  IS Sharpe: {is_sharpe:.2f}")
        print(f"  Best SL/TP: {best_params['sl_mult']:.2f}/{best_params['tp1_mult']:.2f}/{best_params['tp2_mult']:.1f}/{best_params['tp3_mult']:.1f}")

        # Test on out-of-sample
        oos_metrics = run_backtest_with_params(
            test_data,
            best_params['sl_mult'],
            best_params['tp1_mult'],
            best_params['tp2_mult'],
            best_params['tp3_mult'],
        )

        if oos_metrics:
            oos_sharpe = oos_metrics['sharpe']
            degradation = (oos_sharpe / is_sharpe) if is_sharpe != 0 else 0

            print(f"  OOS Sharpe: {oos_sharpe:.2f}")
            print(f"  Degradation: {degradation:.1%}")
            print(f"  OOS Return: {oos_metrics['return']:+.2f}%")
            print(f"  OOS Trades: {oos_metrics['trades']}")

            results.append({
                "window": window_num,
                "is_sharpe": is_sharpe,
                "oos_sharpe": oos_sharpe,
                "degradation": degradation,
                "oos_return": oos_metrics['return'],
                "oos_trades": oos_metrics['trades'],
                **best_params
            })

        # Move window forward
        start_idx += out_sample_hours

    # Summary statistics
    print("\n" + "=" * 70)
    print("WALK-FORWARD SUMMARY")
    print("=" * 70)

    if results:
        df_results = pd.DataFrame(results)

        print(f"\nTotal windows: {len(df_results)}")
        print(f"\nIn-Sample Performance:")
        print(f"  Avg Sharpe: {df_results['is_sharpe'].mean():.2f}")
        print(f"  Std Sharpe: {df_results['is_sharpe'].std():.2f}")

        print(f"\nOut-of-Sample Performance:")
        print(f"  Avg Sharpe: {df_results['oos_sharpe'].mean():.2f}")
        print(f"  Std Sharpe: {df_results['oos_sharpe'].std():.2f}")
        print(f"  Avg Return: {df_results['oos_return'].mean():+.2f}%")
        print(f"  Win Rate: {(df_results['oos_sharpe'] > 0).mean():.1%}")

        print(f"\nDegradation Ratio:")
        print(f"  Mean: {df_results['degradation'].mean():.1%}")
        print(f"  Median: {df_results['degradation'].median():.1%}")

        print(f"\nParameter Stability:")
        for param in ['sl_mult', 'tp1_mult', 'tp2_mult', 'tp3_mult']:
            print(f"  {param}: {df_results[param].mean():.2f} ± {df_results[param].std():.2f}")

        # Save results
        output_file = "outputs/walk_forward_results.csv"
        Path("outputs").mkdir(exist_ok=True)
        df_results.to_csv(output_file, index=False)
        print(f"\nDetailed results saved to: {output_file}")

        return df_results
    else:
        print("\nNo valid results generated.")
        return None

def main():
    # Load data
    print("\nLoading data...")
    data = load_binance_data(warmup=200)
    print(f"Data loaded: {len(data)} bars")
    print(f"Date range: {data.index[0]} to {data.index[-1]}")

    # Run walk-forward analysis
    results = walk_forward_analysis(data, in_sample_months=6, out_sample_months=1)

if __name__ == "__main__":
    main()
