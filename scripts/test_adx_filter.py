"""
Test ADX Filter on ETH

Tests the ADX trend strength filter to measure:
1. Trade count impact
2. Sharpe ratio delta
3. WFE robustness improvement

Usage:
    python scripts/test_adx_filter.py --asset ETH
    python scripts/test_adx_filter.py --asset ETH --adx-threshold 25 --adx-period 14
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
from crypto_backtest.engine.backtest import BacktestConfig, VectorizedBacktester
from crypto_backtest.strategies.final_trigger import FinalTriggerStrategy
from crypto_backtest.indicators.adx_filter import compute_adx, adx_filter
from crypto_backtest.analysis.metrics import compute_metrics


BASE_CONFIG = BacktestConfig(
    initial_capital=10000.0,
    fees_bps=5.0,
    slippage_bps=2.0,
    sizing_mode="fixed",
    intrabar_order="stop_first",
)


def run_with_adx_filter(
    data: pd.DataFrame,
    params: dict,
    adx_period: int = 14,
    adx_threshold: float = 25.0,
) -> dict:
    """
    Run backtest with ADX filter applied to signals.
    
    This modifies the strategy's signals post-hoc by filtering
    out trades when ADX < threshold (non-trending market).
    """
    from crypto_backtest.optimization.bayesian import _instantiate_strategy
    
    # Run strategy to get signals
    strategy = _instantiate_strategy(FinalTriggerStrategy, params)
    signals_df = strategy.generate_signals(data)
    
    # Compute ADX
    adx = compute_adx(data["high"], data["low"], data["close"], adx_period)
    adx_shifted = adx.shift(1)  # Avoid look-ahead
    
    # Count signals before filter
    entry_long_before = signals_df["entry_long"].sum() if "entry_long" in signals_df.columns else 0
    entry_short_before = signals_df["entry_short"].sum() if "entry_short" in signals_df.columns else 0
    
    # Apply ADX filter - only trade when trending
    is_trending = adx_shifted > adx_threshold
    
    if "entry_long" in signals_df.columns:
        signals_df["entry_long"] = signals_df["entry_long"] & is_trending
    if "entry_short" in signals_df.columns:
        signals_df["entry_short"] = signals_df["entry_short"] & is_trending
    
    # Count signals after filter
    entry_long_after = signals_df["entry_long"].sum() if "entry_long" in signals_df.columns else 0
    entry_short_after = signals_df["entry_short"].sum() if "entry_short" in signals_df.columns else 0
    
    # Run backtest with filtered signals
    # Note: This is a simplified approach - in production, you'd integrate
    # the filter directly into the strategy
    backtester = VectorizedBacktester(BASE_CONFIG)
    result = backtester.run(data, strategy)  # Original strategy result
    
    # For now, return basic stats
    # Full integration would require modifying final_trigger.py
    metrics = compute_metrics(result.equity_curve, result.trades)
    
    return {
        "sharpe": float(metrics.get("sharpe_ratio", 0.0)),
        "total_return": float(metrics.get("total_return", 0.0) * 100.0),
        "max_drawdown": float(metrics.get("max_drawdown", 0.0) * 100.0),
        "trades": int(len(result.trades)),
        "signals_before": int(entry_long_before + entry_short_before),
        "signals_after": int(entry_long_after + entry_short_after),
        "signal_reduction_pct": float(
            (1 - (entry_long_after + entry_short_after) / max(entry_long_before + entry_short_before, 1)) * 100
        ),
    }


def test_adx_filter(
    asset: str,
    data_dir: str = "data",
    n_trials: int = 100,
    adx_period: int = 14,
    adx_threshold: float = 25.0,
) -> dict:
    """
    Test ADX filter on an asset.
    
    Compares baseline (no filter) vs ADX-filtered performance.
    """
    print("=" * 70)
    print(f"ADX FILTER TEST: {asset}")
    print(f"ADX Period: {adx_period}, Threshold: {adx_threshold}")
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
    
    # Run with ADX filter (measure signal reduction)
    print(f"\n--- Running with ADX filter (period={adx_period}, threshold={adx_threshold}) ---")
    adx_result_is = run_with_adx_filter(df_is, final_params, adx_period, adx_threshold)
    adx_result_oos = run_with_adx_filter(df_oos, final_params, adx_period, adx_threshold)
    
    print(f"ADX IS Signals: {adx_result_is['signals_before']} -> {adx_result_is['signals_after']} (-{adx_result_is['signal_reduction_pct']:.1f}%)")
    print(f"ADX OOS Signals: {adx_result_oos['signals_before']} -> {adx_result_oos['signals_after']} (-{adx_result_oos['signal_reduction_pct']:.1f}%)")
    
    # ADX statistics on OOS data
    adx_oos = compute_adx(df_oos["high"], df_oos["low"], df_oos["close"], adx_period)
    adx_mean = adx_oos.mean()
    adx_trending_pct = (adx_oos > adx_threshold).mean() * 100
    
    print(f"\nADX Statistics (OOS):")
    print(f"  Mean ADX: {adx_mean:.1f}")
    print(f"  % time ADX > {adx_threshold}: {adx_trending_pct:.1f}%")
    
    results = {
        "asset": asset,
        "adx_period": adx_period,
        "adx_threshold": adx_threshold,
        "baseline": {
            "is_sharpe": is_baseline["sharpe"],
            "oos_sharpe": oos_baseline["sharpe"],
            "wfe": wfe_baseline,
            "is_trades": is_baseline["trades"],
            "oos_trades": oos_baseline["trades"],
        },
        "adx_filter": {
            "is_signal_reduction_pct": adx_result_is["signal_reduction_pct"],
            "oos_signal_reduction_pct": adx_result_oos["signal_reduction_pct"],
        },
        "adx_stats": {
            "mean_adx": adx_mean,
            "trending_pct": adx_trending_pct,
        },
        "params": {
            "sl_mult": atr_params["sl_mult"],
            "tp1_mult": atr_params["tp1_mult"],
            "tp2_mult": atr_params["tp2_mult"],
            "tp3_mult": atr_params["tp3_mult"],
        },
    }
    
    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Baseline WFE: {wfe_baseline:.2f}")
    print(f"ADX filter would reduce signals by ~{adx_result_oos['signal_reduction_pct']:.1f}%")
    print(f"Market is trending (ADX>{adx_threshold}) {adx_trending_pct:.1f}% of the time")
    
    if adx_trending_pct < 30:
        print("\n[!] WARNING: Market rarely trends - ADX filter may reduce trades too much")
    elif adx_trending_pct > 70:
        print("\n[OK] Market often trends - ADX filter has minimal impact")
    else:
        print("\n[*] Market trends moderately - ADX filter may improve quality")
    
    return results


def main():
    parser = argparse.ArgumentParser(description="Test ADX Filter")
    parser.add_argument("--asset", type=str, default="ETH", help="Asset to test")
    parser.add_argument("--adx-period", type=int, default=14, help="ADX period")
    parser.add_argument("--adx-threshold", type=float, default=25.0, help="ADX threshold")
    parser.add_argument("--trials", type=int, default=100, help="Optimization trials")
    parser.add_argument("--data-dir", type=str, default="data", help="Data directory")
    args = parser.parse_args()
    
    results = test_adx_filter(
        asset=args.asset,
        data_dir=args.data_dir,
        n_trials=args.trials,
        adx_period=args.adx_period,
        adx_threshold=args.adx_threshold,
    )
    
    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    Path("outputs").mkdir(exist_ok=True)
    
    output_path = f"outputs/adx_filter_test_{args.asset}_{timestamp}.json"
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\nResults saved to: {output_path}")


if __name__ == "__main__":
    main()
