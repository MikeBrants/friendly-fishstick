"""
Experiment: Ensemble Displacement

Alex R&D Plan - Track 1: RESCUE (1.2 Ensemble Displacement)

Hypothesis: Single displacement choice is fragile. 
Voting across d26/d52/d78 is more robust.

Implementation:
- Run optimization with each displacement separately
- Take majority vote (2/3) for signal direction
- Alternative: weighted average by IS Sharpe

Usage:
    python scripts/experiment_ensemble_displacement.py --asset OP
    python scripts/experiment_ensemble_displacement.py --assets BTC OP SOL
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import argparse
import json
from datetime import datetime
from typing import List, Dict, Any

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
from crypto_backtest.analysis.metrics import compute_metrics


BASE_CONFIG = BacktestConfig(
    initial_capital=10000.0,
    fees_bps=5.0,
    slippage_bps=2.0,
    sizing_mode="fixed",
    intrabar_order="stop_first",
)

DISPLACEMENTS = [26, 52, 78]


def optimize_for_displacement(
    df_is: pd.DataFrame,
    displacement: int,
    n_trials: int = 100,
    min_trades: int = 30,
) -> tuple[dict, float]:
    """Optimize parameters for a specific displacement."""
    
    # Optimize ATR
    atr_params, atr_sharpe = optimize_atr(
        df_is,
        n_trials=n_trials,
        min_trades=min_trades,
        enforce_tp_progression=True,
        fixed_displacement=displacement,
    )
    
    # Optimize Ichimoku
    ichi_params, ichi_sharpe = optimize_ichimoku(
        df_is,
        atr_params,
        n_trials=n_trials,
        min_trades=min_trades,
        fixed_displacement=displacement,
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
        displacement=displacement,
    )
    
    return final_params, ichi_sharpe


def generate_signals(data: pd.DataFrame, params: dict) -> pd.Series:
    """Generate signals from strategy parameters."""
    from crypto_backtest.optimization.bayesian import _instantiate_strategy
    
    strategy = _instantiate_strategy(FinalTriggerStrategy, params)
    signals_df = strategy.generate_signals(data)
    
    # Extract signal direction (1 = long, -1 = short, 0 = none)
    if "signal" in signals_df.columns:
        return signals_df["signal"]
    else:
        # Construct from entry columns
        signal = pd.Series(0, index=data.index)
        if "entry_long" in signals_df.columns:
            signal = signal.where(~signals_df["entry_long"], 1)
        if "entry_short" in signals_df.columns:
            signal = signal.where(~signals_df["entry_short"], -1)
        return signal


def ensemble_vote(
    signals_list: List[pd.Series],
    weights: List[float] = None,
    method: str = "majority",
) -> pd.Series:
    """
    Combine signals from multiple displacements.
    
    Args:
        signals_list: List of signal Series from different displacements
        weights: Optional weights for weighted voting
        method: "majority" (2/3 agreement) or "weighted" (weighted average)
    
    Returns:
        Combined signal Series
    """
    if not signals_list:
        raise ValueError("signals_list cannot be empty")
    
    # Align all signals to same index
    combined = pd.concat(signals_list, axis=1)
    combined.columns = [f"d{i}" for i in range(len(signals_list))]
    
    if method == "majority":
        # Majority vote - need 2/3 agreement
        long_count = (combined == 1).sum(axis=1)
        short_count = (combined == -1).sum(axis=1)
        
        result = pd.Series(0, index=combined.index)
        result = result.where(long_count < 2, 1)   # 2+ long signals -> long
        result = result.where(short_count < 2, -1)  # 2+ short signals -> short
        
        return result
    
    elif method == "weighted":
        # Weighted average
        if weights is None:
            weights = [1.0] * len(signals_list)
        
        weights = np.array(weights) / sum(weights)
        
        weighted_sum = sum(
            signals_list[i] * weights[i] 
            for i in range(len(signals_list))
        )
        
        # Threshold: > 0.33 = long, < -0.33 = short
        result = pd.Series(0, index=combined.index)
        result = result.where(weighted_sum <= 0.33, 1)
        result = result.where(weighted_sum >= -0.33, -1)
        
        return result
    
    else:
        raise ValueError(f"Unknown method: {method}")


def run_ensemble_experiment(
    asset: str,
    data_dir: str = "data",
    n_trials: int = 100,
) -> Dict[str, Any]:
    """
    Run ensemble displacement experiment on an asset.
    
    Compares:
    1. Single best displacement
    2. Ensemble (majority vote)
    3. Ensemble (weighted by IS Sharpe)
    """
    print("=" * 70)
    print(f"ENSEMBLE DISPLACEMENT EXPERIMENT: {asset}")
    print("=" * 70)
    
    # Load data
    df = load_data(asset, data_dir)
    df = df.iloc[OPTIM_CONFIG["warmup_bars"]:]
    df_is, df_val, df_oos = split_data(df, splits=(0.6, 0.2, 0.2))
    
    print(f"Data: IS={len(df_is)}, VAL={len(df_val)}, OOS={len(df_oos)} bars")
    
    # Optimize for each displacement
    displacement_results = {}
    
    for disp in DISPLACEMENTS:
        print(f"\nOptimizing for displacement={disp}...")
        
        try:
            params, is_sharpe = optimize_for_displacement(
                df_is, disp, n_trials=n_trials
            )
            
            # Evaluate
            is_result = run_backtest(df_is, params)
            oos_result = run_backtest(df_oos, params)
            wfe = oos_result["sharpe"] / is_result["sharpe"] if is_result["sharpe"] > 0 else 0
            
            displacement_results[disp] = {
                "params": params,
                "is_sharpe": is_result["sharpe"],
                "oos_sharpe": oos_result["sharpe"],
                "wfe": wfe,
                "is_trades": is_result["trades"],
                "oos_trades": oos_result["trades"],
            }
            
            print(f"  d{disp}: IS Sharpe={is_result['sharpe']:.2f}, OOS Sharpe={oos_result['sharpe']:.2f}, WFE={wfe:.2f}")
            
        except Exception as e:
            print(f"  d{disp}: ERROR - {e}")
            displacement_results[disp] = {"error": str(e)}
    
    # Find single best (by IS Sharpe)
    valid_disps = [d for d, r in displacement_results.items() if "is_sharpe" in r]
    if not valid_disps:
        return {"error": "All displacement optimizations failed"}
    
    best_disp = max(valid_disps, key=lambda d: displacement_results[d]["is_sharpe"])
    single_best = displacement_results[best_disp]
    
    print(f"\n--- Single Best: d{best_disp} ---")
    print(f"  IS Sharpe: {single_best['is_sharpe']:.2f}")
    print(f"  OOS Sharpe: {single_best['oos_sharpe']:.2f}")
    print(f"  WFE: {single_best['wfe']:.2f}")
    
    # Generate signals for ensemble
    signals_by_disp = {}
    for disp in valid_disps:
        params = displacement_results[disp]["params"]
        signals_by_disp[disp] = generate_signals(df_oos, params)
    
    # Ensemble: majority vote
    print("\n--- Ensemble (Majority Vote) ---")
    signals_list = [signals_by_disp[d] for d in sorted(valid_disps)]
    ensemble_signals_majority = ensemble_vote(signals_list, method="majority")
    
    # Count signals
    n_long_majority = (ensemble_signals_majority == 1).sum()
    n_short_majority = (ensemble_signals_majority == -1).sum()
    print(f"  Signals: {n_long_majority} long, {n_short_majority} short")
    
    # Ensemble: weighted by IS Sharpe
    print("\n--- Ensemble (IS Sharpe Weighted) ---")
    weights = [displacement_results[d]["is_sharpe"] for d in sorted(valid_disps)]
    ensemble_signals_weighted = ensemble_vote(signals_list, weights=weights, method="weighted")
    
    n_long_weighted = (ensemble_signals_weighted == 1).sum()
    n_short_weighted = (ensemble_signals_weighted == -1).sum()
    print(f"  Signals: {n_long_weighted} long, {n_short_weighted} short")
    
    # Note: Full backtesting of ensemble signals would require modifying
    # the backtest engine to accept pre-computed signals
    # For now, we report signal agreement metrics
    
    # Signal agreement analysis
    agreement_majority = (
        (ensemble_signals_majority == signals_by_disp[best_disp]).sum() / 
        len(ensemble_signals_majority)
    )
    agreement_weighted = (
        (ensemble_signals_weighted == signals_by_disp[best_disp]).sum() / 
        len(ensemble_signals_weighted)
    )
    
    return {
        "asset": asset,
        "displacements_tested": DISPLACEMENTS,
        "displacement_results": {
            d: {k: v for k, v in r.items() if k != "params"} 
            for d, r in displacement_results.items()
        },
        "single_best": {
            "displacement": best_disp,
            "is_sharpe": single_best["is_sharpe"],
            "oos_sharpe": single_best["oos_sharpe"],
            "wfe": single_best["wfe"],
        },
        "ensemble_majority": {
            "n_long": int(n_long_majority),
            "n_short": int(n_short_majority),
            "agreement_with_best": agreement_majority,
        },
        "ensemble_weighted": {
            "n_long": int(n_long_weighted),
            "n_short": int(n_short_weighted),
            "agreement_with_best": agreement_weighted,
        },
    }


def main():
    parser = argparse.ArgumentParser(description="Ensemble Displacement Experiment")
    parser.add_argument(
        "--assets",
        nargs="+",
        default=["OP"],
        help="Assets to test"
    )
    parser.add_argument("--trials", type=int, default=100, help="Trials per optimization")
    parser.add_argument("--data-dir", type=str, default="data", help="Data directory")
    args = parser.parse_args()
    
    all_results = []
    
    for asset in args.assets:
        print(f"\n{'='*70}")
        print(f"Processing {asset}...")
        print("=" * 70)
        
        try:
            result = run_ensemble_experiment(
                asset=asset,
                data_dir=args.data_dir,
                n_trials=args.trials,
            )
            all_results.append(result)
        except Exception as e:
            print(f"ERROR processing {asset}: {e}")
            all_results.append({"asset": asset, "error": str(e)})
    
    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    Path("outputs").mkdir(exist_ok=True)
    
    output_path = f"outputs/ensemble_displacement_experiment_{timestamp}.json"
    with open(output_path, "w") as f:
        json.dump(all_results, f, indent=2, default=str)
    
    print(f"\n{'='*70}")
    print("EXPERIMENT COMPLETE")
    print("=" * 70)
    print(f"Results saved to: {output_path}")
    
    # Summary
    print("\nSummary:")
    for result in all_results:
        asset = result.get("asset", "Unknown")
        if "error" in result:
            print(f"  {asset}: ERROR - {result['error']}")
        else:
            best = result["single_best"]
            print(f"  {asset}: Best d{best['displacement']}, WFE={best['wfe']:.2f}")


if __name__ == "__main__":
    main()
