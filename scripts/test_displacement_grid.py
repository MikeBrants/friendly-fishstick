"""
Test displacement grid for multiple assets.

Tests different Ichimoku displacements (26, 52, 78) to find optimal setting.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import argparse
import json
from datetime import datetime

import pandas as pd

from crypto_backtest.optimization.parallel_optimizer import (
    optimize_single_asset,
    load_data,
)


def test_displacement_grid(
    assets: list[str],
    displacements: list[int],
    data_dir: str = "data",
    trials: int = 60,
) -> dict:
    """
    Test multiple displacements for each asset.
    
    Returns dict with results per asset per displacement.
    """
    results = {}
    
    for asset in assets:
        print(f"\n{'='*70}")
        print(f"Testing {asset} with displacements: {displacements}")
        print(f"{'='*70}")
        
        asset_results = {}
        
        for disp in displacements:
            print(f"\n--- {asset} displacement={disp} ---")
            
            try:
                result = optimize_single_asset(
                    asset=asset,
                    data_dir=data_dir,
                    n_trials_atr=trials,
                    n_trials_ichi=trials,
                    fixed_displacement=disp,
                    enforce_tp_progression=True,
                )
                
                asset_results[f"d{disp}"] = {
                    "status": result.status,
                    "oos_sharpe": result.oos_sharpe,
                    "wfe": result.wfe,
                    "oos_trades": result.oos_trades,
                    "displacement": disp,
                }
                
                print(f"  OOS Sharpe: {result.oos_sharpe:.2f}")
                print(f"  WFE: {result.wfe:.2f}")
                print(f"  OOS Trades: {result.oos_trades}")
                
            except Exception as e:
                print(f"  ERROR: {e}")
                asset_results[f"d{disp}"] = {
                    "status": "ERROR",
                    "error": str(e),
                }
        
        results[asset] = asset_results
        
        # Print summary for this asset
        print(f"\n--- {asset} SUMMARY ---")
        best_disp = None
        best_wfe = -999
        
        for disp_key, res in asset_results.items():
            if res.get("wfe", -999) > best_wfe:
                best_wfe = res["wfe"]
                best_disp = disp_key
        
        if best_disp:
            print(f"Best displacement: {best_disp} (WFE={best_wfe:.2f})")
    
    return results


def main():
    parser = argparse.ArgumentParser(description="Test Displacement Grid")
    parser.add_argument("--assets", nargs="+", required=True, help="Assets to test")
    parser.add_argument("--displacements", nargs="+", type=int, default=[26, 52, 78], help="Displacements to test")
    parser.add_argument("--trials", type=int, default=60, help="Trials per displacement")
    parser.add_argument("--data-dir", type=str, default="data", help="Data directory")
    args = parser.parse_args()
    
    results = test_displacement_grid(
        assets=args.assets,
        displacements=args.displacements,
        data_dir=args.data_dir,
        trials=args.trials,
    )
    
    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    Path("outputs").mkdir(exist_ok=True)
    
    output_path = f"outputs/displacement_grid_test_{timestamp}.json"
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n{'='*70}")
    print(f"Results saved to: {output_path}")
    print(f"{'='*70}")


if __name__ == "__main__":
    main()
