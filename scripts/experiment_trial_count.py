"""
Experiment: Trial Count vs WFE Curve

Alex R&D Plan - Track 1: RESCUE (1.3 Reduced Trial Count Paradox)

Hypothesis: Fewer trials = less overfitting (find robust vs optimal params).
Test: Run BTC with 50, 100, 200, 300 trials. Plot WFE vs trial count.
Expected: Inverse relationship — more trials = lower WFE for BTC.

Usage:
    python scripts/experiment_trial_count.py --asset BTC
    python scripts/experiment_trial_count.py --asset BTC --trial-counts 50 100 150 200 250 300
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import argparse
import json
from datetime import datetime
from typing import List

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
from crypto_backtest.config.scan_assets import ATR_SEARCH_SPACE, ICHI_SEARCH_SPACE


def run_trial_count_experiment(
    asset: str,
    trial_counts: List[int] = None,
    data_dir: str = "data",
    runs_per_count: int = 3,
    fixed_displacement: int = 52,
) -> pd.DataFrame:
    """
    Run optimization with different trial counts and measure WFE.
    
    Args:
        asset: Asset to test (e.g., "BTC")
        trial_counts: List of trial counts to test
        data_dir: Data directory
        runs_per_count: Number of runs per trial count (for variance estimation)
        fixed_displacement: Ichimoku displacement to use
    
    Returns:
        DataFrame with results
    """
    if trial_counts is None:
        trial_counts = [50, 100, 150, 200, 250, 300]
    
    print("=" * 70)
    print(f"TRIAL COUNT EXPERIMENT: {asset}")
    print(f"Trial counts: {trial_counts}")
    print(f"Runs per count: {runs_per_count}")
    print("=" * 70)
    
    # Load data
    df = load_data(asset, data_dir)
    df = df.iloc[OPTIM_CONFIG["warmup_bars"]:]
    df_is, df_val, df_oos = split_data(df, splits=(0.6, 0.2, 0.2))
    
    print(f"Data: IS={len(df_is)}, VAL={len(df_val)}, OOS={len(df_oos)} bars")
    
    results = []
    
    for trial_count in trial_counts:
        print(f"\n{'='*60}")
        print(f"Testing {trial_count} trials...")
        print("=" * 60)
        
        for run_idx in range(runs_per_count):
            print(f"  Run {run_idx + 1}/{runs_per_count}...")
            
            try:
                # Optimize ATR
                atr_params, atr_sharpe = optimize_atr(
                    df_is,
                    n_trials=trial_count,
                    min_trades=30,  # Lower threshold for experiment
                    enforce_tp_progression=True,
                    fixed_displacement=fixed_displacement,
                )
                
                # Optimize Ichimoku
                ichi_params, ichi_sharpe = optimize_ichimoku(
                    df_is,
                    atr_params,
                    n_trials=trial_count,
                    min_trades=30,
                    fixed_displacement=fixed_displacement,
                )
                
                # Build final params
                final_params = build_strategy_params(
                    sl_mult=atr_params["sl_mult"],
                    tp1_mult=atr_params["tp1_mult"],
                    tp2_mult=atr_params["tp2_mult"],
                    tp3_mult=atr_params["tp3_mult"],
                    tenkan=ichi_params["tenkan"],
                    kijun=ichi_params["kijun"],
                    tenkan_5=ichi_params["tenkan_5"],
                    kijun_5=ichi_params["kijun_5"],
                    displacement=fixed_displacement,
                )
                
                # Evaluate on all splits
                is_result = run_backtest(df_is, final_params)
                val_result = run_backtest(df_val, final_params)
                oos_result = run_backtest(df_oos, final_params)
                
                # Calculate WFE
                wfe = oos_result["sharpe"] / is_result["sharpe"] if is_result["sharpe"] > 0 else 0
                
                results.append({
                    "asset": asset,
                    "trial_count": trial_count,
                    "run_idx": run_idx,
                    "is_sharpe": is_result["sharpe"],
                    "val_sharpe": val_result["sharpe"],
                    "oos_sharpe": oos_result["sharpe"],
                    "wfe": wfe,
                    "is_trades": is_result["trades"],
                    "oos_trades": oos_result["trades"],
                    "sl_mult": atr_params["sl_mult"],
                    "tp1_mult": atr_params["tp1_mult"],
                    "tp2_mult": atr_params["tp2_mult"],
                    "tp3_mult": atr_params["tp3_mult"],
                    "tenkan": ichi_params["tenkan"],
                    "kijun": ichi_params["kijun"],
                })
                
                print(f"    IS Sharpe: {is_result['sharpe']:.2f}, OOS Sharpe: {oos_result['sharpe']:.2f}, WFE: {wfe:.2f}")
                
            except Exception as e:
                print(f"    ERROR: {e}")
                results.append({
                    "asset": asset,
                    "trial_count": trial_count,
                    "run_idx": run_idx,
                    "is_sharpe": 0,
                    "val_sharpe": 0,
                    "oos_sharpe": 0,
                    "wfe": 0,
                    "error": str(e),
                })
    
    return pd.DataFrame(results)


def analyze_results(df: pd.DataFrame) -> dict:
    """Analyze trial count experiment results."""
    
    # Group by trial count
    summary = df.groupby("trial_count").agg({
        "is_sharpe": ["mean", "std"],
        "oos_sharpe": ["mean", "std"],
        "wfe": ["mean", "std"],
        "oos_trades": "mean",
    }).round(3)
    
    # Flatten column names
    summary.columns = ["_".join(col) for col in summary.columns]
    summary = summary.reset_index()
    
    # Calculate correlation between trial count and WFE
    correlation = df["trial_count"].corr(df["wfe"])
    
    # Find optimal trial count (highest mean WFE)
    best_idx = summary["wfe_mean"].idxmax()
    optimal_trials = summary.loc[best_idx, "trial_count"]
    
    return {
        "summary": summary,
        "correlation_trial_wfe": correlation,
        "optimal_trial_count": optimal_trials,
        "hypothesis_confirmed": correlation < -0.1,  # Expect negative correlation
    }


def main():
    parser = argparse.ArgumentParser(description="Trial Count vs WFE Experiment")
    parser.add_argument("--asset", type=str, default="BTC", help="Asset to test")
    parser.add_argument(
        "--trial-counts",
        nargs="+",
        type=int,
        default=[50, 100, 150, 200, 250, 300],
        help="Trial counts to test"
    )
    parser.add_argument("--runs", type=int, default=3, help="Runs per trial count")
    parser.add_argument("--displacement", type=int, default=52, help="Fixed displacement")
    parser.add_argument("--data-dir", type=str, default="data", help="Data directory")
    args = parser.parse_args()
    
    # Run experiment
    results_df = run_trial_count_experiment(
        asset=args.asset,
        trial_counts=args.trial_counts,
        data_dir=args.data_dir,
        runs_per_count=args.runs,
        fixed_displacement=args.displacement,
    )
    
    # Analyze
    analysis = analyze_results(results_df)
    
    # Print summary
    print("\n" + "=" * 70)
    print("EXPERIMENT RESULTS")
    print("=" * 70)
    print("\nSummary by trial count:")
    print(analysis["summary"].to_string(index=False))
    print(f"\nCorrelation (trial_count vs WFE): {analysis['correlation_trial_wfe']:.3f}")
    print(f"Optimal trial count: {analysis['optimal_trial_count']}")
    print(f"Hypothesis confirmed (more trials = lower WFE): {analysis['hypothesis_confirmed']}")
    
    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    Path("outputs").mkdir(exist_ok=True)
    
    results_path = f"outputs/trial_count_experiment_{args.asset}_{timestamp}.csv"
    results_df.to_csv(results_path, index=False)
    print(f"\nRaw results saved to: {results_path}")
    
    summary_path = f"outputs/trial_count_summary_{args.asset}_{timestamp}.csv"
    analysis["summary"].to_csv(summary_path, index=False)
    print(f"Summary saved to: {summary_path}")
    
    # Save analysis as JSON
    analysis_path = f"outputs/trial_count_analysis_{args.asset}_{timestamp}.json"
    with open(analysis_path, "w") as f:
        json.dump({
            "asset": args.asset,
            "trial_counts": args.trial_counts,
            "correlation_trial_wfe": float(analysis["correlation_trial_wfe"]),
            "optimal_trial_count": int(analysis["optimal_trial_count"]),
            "hypothesis_confirmed": bool(analysis["hypothesis_confirmed"]),
        }, f, indent=2)
    print(f"Analysis saved to: {analysis_path}")


if __name__ == "__main__":
    main()
