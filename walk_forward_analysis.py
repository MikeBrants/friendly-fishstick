"""Walk-Forward Analysis to validate strategy robustness."""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import timedelta
import argparse

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

def _build_optimized_params() -> FinalTriggerParams:
    """Return FinalTriggerParams using the current optimized Ichimoku + SL/TP."""
    five_in_one = FiveInOneConfig(
        fast_period=7,
        slow_period=19,
        er_period=8,
        norm_period=50,
        use_norm=True,
        ad_norm_period=50,
        use_ad_line=True,
        ichi5in1_strict=False,
        use_transition_mode=False,
        use_distance_filter=False,
        use_volume_filter=False,
        use_regression_cloud=False,
        use_kama_oscillator=False,
        use_ichimoku_filter=True,
        tenkan_5=12,
        kijun_5=21,
        displacement_5=52,
    )

    ichimoku = IchimokuConfig(
        tenkan=13,
        kijun=34,
        displacement=52,
    )

    return FinalTriggerParams(
        grace_bars=1,
        use_mama_kama_filter=False,
        require_fama_between=False,
        strict_lock_5in1_last=False,
        mama_fast_limit=0.5,
        mama_slow_limit=0.05,
        kama_length=20,
        atr_length=14,
        sl_mult=3.75,
        tp1_mult=3.75,
        tp2_mult=9.0,
        tp3_mult=7.0,
        ichimoku=ichimoku,
        five_in_one=five_in_one,
    )

def _run_backtest_segment(data: pd.DataFrame, params: FinalTriggerParams, config: BacktestConfig) -> dict:
    """Run a backtest on a segment and return enriched metrics."""
    backtester = VectorizedBacktester(config)
    result = backtester.run(data, FinalTriggerStrategy(params))

    metrics = compute_metrics(result.equity_curve, result.trades)
    final_equity = float(result.equity_curve.iloc[-1]) if len(result.equity_curve) else config.initial_capital
    total_return = (final_equity / config.initial_capital - 1) * 100 if config.initial_capital else 0.0

    pnl_col = None
    for col in ("pnl", "net_pnl", "gross_pnl"):
        if col in result.trades.columns:
            pnl_col = col
            break
    pnl = result.trades[pnl_col] if pnl_col else pd.Series(dtype=float)
    winners = pnl[pnl > 0]
    losers = pnl[pnl < 0]

    return {
        "total_return_pct": total_return,
        "max_drawdown_pct": metrics.get("max_drawdown", 0.0) * 100,
        "win_rate_pct": metrics.get("win_rate", 0.0) * 100,
        "profit_factor": metrics.get("profit_factor", 0.0),
        "trades": int(len(result.trades)),
        "avg_win": float(winners.mean()) if len(winners) else 0.0,
        "avg_loss": float(losers.mean()) if len(losers) else 0.0,
        "sharpe": metrics.get("sharpe_ratio", 0.0),
        "sortino": metrics.get("sortino_ratio", 0.0),
    }

def oos_validation(
    data: pd.DataFrame,
    split: tuple[float, float, float] = (0.6, 0.2, 0.2),
    baseline_is_sharpe: float = 2.13,
    output_csv: str = "outputs/oos_validation_results.csv",
    output_report: str = "outputs/oos_validation_report.txt",
) -> pd.DataFrame:
    """Run 60/20/20 OOS validation with fixed optimized params."""
    if not np.isclose(sum(split), 1.0):
        raise ValueError("Split must sum to 1.0 (e.g., 0.6, 0.2, 0.2).")

    print("=" * 70)
    print("OOS VALIDATION (60/20/20 SPLIT)")
    print("=" * 70)

    n = len(data)
    is_end = int(n * split[0])
    val_end = int(n * (split[0] + split[1]))

    train_data = data.iloc[:is_end]
    val_data = data.iloc[is_end:val_end]
    oos_data = data.iloc[val_end:]

    print(f"Total bars: {n}")
    print(f"IS:  {train_data.index[0]} to {train_data.index[-1]} ({len(train_data)} bars)")
    print(f"VAL: {val_data.index[0]} to {val_data.index[-1]} ({len(val_data)} bars)")
    print(f"OOS: {oos_data.index[0]} to {oos_data.index[-1]} ({len(oos_data)} bars)")

    params = _build_optimized_params()
    config = BacktestConfig(
        initial_capital=10000.0,
        fees_bps=5.0,
        slippage_bps=2.0,
        sizing_mode="fixed",
        intrabar_order="stop_first",
    )

    rows = []
    for label, segment in (("IS", train_data), ("VAL", val_data), ("OOS", oos_data)):
        metrics = _run_backtest_segment(segment, params, config)
        metrics["segment"] = label
        metrics["bars"] = len(segment)
        metrics["start"] = str(segment.index[0])
        metrics["end"] = str(segment.index[-1])
        rows.append(metrics)

    df = pd.DataFrame(rows)
    oos_sharpe = float(df.loc[df["segment"] == "OOS", "sharpe"].iloc[0])
    wfe = oos_sharpe / baseline_is_sharpe if baseline_is_sharpe else 0.0
    overfit_risk = wfe < 0.6

    df["wfe_vs_baseline"] = np.where(df["segment"] == "OOS", wfe, np.nan)
    df["wfe_target_pass"] = np.where(df["segment"] == "OOS", not overfit_risk, np.nan)

    Path("outputs").mkdir(exist_ok=True)
    df.to_csv(output_csv, index=False)

    with open(output_report, "w") as f:
        f.write("OOS VALIDATION REPORT (60/20/20 SPLIT)\n")
        f.write("=" * 70 + "\n")
        f.write(f"Baseline IS Sharpe: {baseline_is_sharpe:.2f}\n")
        f.write(f"OOS Sharpe: {oos_sharpe:.2f}\n")
        f.write(f"WFE (OOS/IS): {wfe:.2f}\n")
        f.write(f"Overfitting risk: {'YES' if overfit_risk else 'NO'}\n\n")

        def _fmt_row(row: pd.Series) -> str:
            return (
                f"{row['segment']}: return={row['total_return_pct']:+.2f}%, "
                f"sharpe={row['sharpe']:.2f}, sortino={row['sortino']:.2f}, "
                f"max_dd={row['max_drawdown_pct']:.2f}%, win_rate={row['win_rate_pct']:.2f}%, "
                f"pf={row['profit_factor']:.2f}, trades={int(row['trades'])}, "
                f"avg_win={row['avg_win']:.2f}, avg_loss={row['avg_loss']:.2f}"
            )

        for _, row in df.iterrows():
            f.write(_fmt_row(row) + "\n")

    print("\nComparison report (IS vs OOS):")
    print(f"  Baseline IS Sharpe: {baseline_is_sharpe:.2f}")
    print(f"  OOS Sharpe: {oos_sharpe:.2f}")
    print(f"  WFE (OOS/IS): {wfe:.2f}")
    print(f"  Overfitting risk: {'YES' if overfit_risk else 'NO'}")
    print(f"\nSaved CSV: {output_csv}")
    print(f"Saved report: {output_report}")

    return df

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
    parser = argparse.ArgumentParser(description="Walk-forward or OOS validation.")
    parser.add_argument(
        "--mode",
        choices=["walk_forward", "oos"],
        default="oos",
        help="Run standard walk-forward or 60/20/20 OOS validation.",
    )
    args = parser.parse_args()

    print("\nLoading data...")
    data = load_binance_data(warmup=200)
    print(f"Data loaded: {len(data)} bars")
    print(f"Date range: {data.index[0]} to {data.index[-1]}")

    if args.mode == "walk_forward":
        walk_forward_analysis(data, in_sample_months=6, out_sample_months=1)
    else:
        oos_validation(data)

if __name__ == "__main__":
    main()
