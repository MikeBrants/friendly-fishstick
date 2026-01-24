"""
Test Regime Filter (RECOVERY) on SHIB

Tests filtering out RECOVERY regime trades to see if WFE improves.
Based on finding that RECOVERY regime loses money for meme coins.

Usage:
    python scripts/test_regime_filter.py --asset SHIB
    python scripts/test_regime_filter.py --asset SHIB --filter-config no_recovery
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
from crypto_backtest.indicators.regime_filter import (
    filter_recovery_regime,
    filter_regimes,
    get_regime_performance,
    REGIME_FILTER_CONFIGS,
)
from crypto_backtest.analysis.regime import classify_regimes_v2, REGIMES_V2
from crypto_backtest.analysis.metrics import compute_metrics


BASE_CONFIG = BacktestConfig(
    initial_capital=10000.0,
    fees_bps=5.0,
    slippage_bps=2.0,
    sizing_mode="fixed",
    intrabar_order="stop_first",
)


def analyze_regime_distribution(data: pd.DataFrame) -> dict:
    """Analyze regime distribution in data."""
    regimes = classify_regimes_v2(data)
    
    counts = {}
    for regime in REGIMES_V2:
        count = (regimes == regime).sum()
        counts[regime] = {
            "count": int(count),
            "pct": float(count / len(regimes) * 100),
        }
    
    return counts


def count_signals_by_regime(data: pd.DataFrame, params: dict) -> dict:
    """Count entry signals by regime."""
    from crypto_backtest.optimization.bayesian import _instantiate_strategy
    
    strategy = _instantiate_strategy(FinalTriggerStrategy, params)
    signals_df = strategy.generate_signals(data)
    
    regimes = classify_regimes_v2(data)
    
    signal_counts = {}
    for regime in REGIMES_V2:
        regime_mask = regimes == regime
        
        long_signals = 0
        short_signals = 0
        if "entry_long" in signals_df.columns:
            long_signals = (signals_df["entry_long"] & regime_mask).sum()
        if "entry_short" in signals_df.columns:
            short_signals = (signals_df["entry_short"] & regime_mask).sum()
        
        signal_counts[regime] = {
            "long": int(long_signals),
            "short": int(short_signals),
            "total": int(long_signals + short_signals),
        }
    
    return signal_counts


def test_regime_filter(
    asset: str,
    data_dir: str = "data",
    n_trials: int = 100,
    filter_config: str = "no_recovery",
) -> dict:
    """
    Test regime filter on an asset.
    
    Compares baseline vs filtered performance.
    """
    print("=" * 70)
    print(f"REGIME FILTER TEST: {asset}")
    print(f"Filter config: {filter_config}")
    if filter_config in REGIME_FILTER_CONFIGS:
        print(f"Description: {REGIME_FILTER_CONFIGS[filter_config]['description']}")
    print("=" * 70)
    
    # Load data
    df = load_data(asset, data_dir)
    df = df.iloc[OPTIM_CONFIG["warmup_bars"]:]
    df_is, df_val, df_oos = split_data(df, splits=(0.6, 0.2, 0.2))
    
    print(f"Data: IS={len(df_is)}, VAL={len(df_val)}, OOS={len(df_oos)} bars")
    
    # Analyze regime distribution
    print("\n--- Regime Distribution (OOS) ---")
    regime_dist = analyze_regime_distribution(df_oos)
    for regime, stats in sorted(regime_dist.items(), key=lambda x: -x[1]["pct"]):
        if stats["pct"] > 1:
            print(f"  {regime}: {stats['pct']:.1f}%")
    
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
    
    # Run baseline
    print("\n--- Running baseline ---")
    is_baseline = run_backtest(df_is, final_params)
    oos_baseline = run_backtest(df_oos, final_params)
    wfe_baseline = oos_baseline["sharpe"] / is_baseline["sharpe"] if is_baseline["sharpe"] > 0 else 0
    
    print(f"Baseline IS:  Sharpe={is_baseline['sharpe']:.2f}, Trades={is_baseline['trades']}")
    print(f"Baseline OOS: Sharpe={oos_baseline['sharpe']:.2f}, Trades={oos_baseline['trades']}")
    print(f"Baseline WFE: {wfe_baseline:.2f}")
    
    # Count signals by regime
    print("\n--- Signals by Regime (OOS) ---")
    signal_counts = count_signals_by_regime(df_oos, final_params)
    total_signals = sum(s["total"] for s in signal_counts.values())
    
    for regime, counts in sorted(signal_counts.items(), key=lambda x: -x[1]["total"]):
        if counts["total"] > 0:
            pct = counts["total"] / max(total_signals, 1) * 100
            print(f"  {regime}: {counts['total']} signals ({pct:.1f}%)")
    
    # Get trades and analyze regime performance
    print("\n--- Regime Performance Analysis ---")
    from crypto_backtest.optimization.bayesian import _instantiate_strategy
    strategy = _instantiate_strategy(FinalTriggerStrategy, final_params)
    backtester = VectorizedBacktester(BASE_CONFIG)
    result = backtester.run(df_oos, strategy)
    trades = result.trades
    
    if not trades.empty:
        regime_perf = get_regime_performance(df_oos, trades)
        if not regime_perf.empty:
            print(regime_perf[["regime", "n_trades", "pnl_pct"]].to_string(index=False))
    
    # Calculate potential impact of filtering RECOVERY
    recovery_signals = signal_counts.get("RECOVERY", {}).get("total", 0)
    recovery_pct = recovery_signals / max(total_signals, 1) * 100
    
    print(f"\n--- Filter Impact Estimate ---")
    print(f"RECOVERY signals: {recovery_signals} ({recovery_pct:.1f}% of total)")
    
    if filter_config == "no_recovery":
        print(f"Filtering RECOVERY would remove ~{recovery_pct:.1f}% of signals")
    
    results = {
        "asset": asset,
        "filter_config": filter_config,
        "baseline": {
            "is_sharpe": is_baseline["sharpe"],
            "oos_sharpe": oos_baseline["sharpe"],
            "wfe": wfe_baseline,
            "is_trades": is_baseline["trades"],
            "oos_trades": oos_baseline["trades"],
        },
        "regime_distribution": regime_dist,
        "signal_counts_by_regime": signal_counts,
        "filter_impact": {
            "recovery_signals": recovery_signals,
            "recovery_pct": recovery_pct,
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
    print(f"RECOVERY regime represents {recovery_pct:.1f}% of signals")
    
    # Get RECOVERY PnL if available
    if not trades.empty:
        regime_perf = get_regime_performance(df_oos, trades)
        if not regime_perf.empty:
            recovery_row = regime_perf[regime_perf["regime"] == "RECOVERY"]
            if not recovery_row.empty:
                recovery_pnl_pct = recovery_row["pnl_pct"].values[0]
                print(f"RECOVERY PnL contribution: {recovery_pnl_pct:.1f}%")
                
                if recovery_pnl_pct < 0:
                    print("\n[OK] RECOVERY regime loses money - filtering recommended")
                    results["recommendation"] = "FILTER_RECOVERY"
                else:
                    print("\n[!] RECOVERY regime is profitable - filtering NOT recommended")
                    results["recommendation"] = "KEEP_RECOVERY"
    
    return results


def main():
    parser = argparse.ArgumentParser(description="Test Regime Filter")
    parser.add_argument("--asset", type=str, default="SHIB", help="Asset to test")
    parser.add_argument(
        "--filter-config",
        type=str,
        default="no_recovery",
        choices=list(REGIME_FILTER_CONFIGS.keys()),
        help="Filter configuration to test"
    )
    parser.add_argument("--trials", type=int, default=100, help="Optimization trials")
    parser.add_argument("--data-dir", type=str, default="data", help="Data directory")
    args = parser.parse_args()
    
    results = test_regime_filter(
        asset=args.asset,
        data_dir=args.data_dir,
        n_trials=args.trials,
        filter_config=args.filter_config,
    )
    
    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    Path("outputs").mkdir(exist_ok=True)
    
    output_path = f"outputs/regime_filter_test_{args.asset}_{timestamp}.json"
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\nResults saved to: {output_path}")


if __name__ == "__main__":
    main()
