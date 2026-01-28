#!/usr/bin/env python3
"""
Challenger ETH/YGG — Test with True CSCV PBO
Post PR#31: Combinatorial Split Cross-Validation for robust PBO
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from crypto_backtest.validation.cpcv import CombinatorialPurgedKFold
from crypto_backtest.validation.pbo import probability_of_backtest_overfitting

CHALLENGER_ASSETS = ["ETH", "YGG"]

def load_returns_matrix(asset: str, returns_dir: Path = Path("outputs")) -> np.ndarray:
    """Load per-trial returns matrix for PBO calculation."""
    pattern = f"returns_matrix_{asset}_*.npy"
    files = list(returns_dir.glob(pattern))
    
    if not files:
        raise FileNotFoundError(f"No returns matrix found for {asset} in {returns_dir}")
    
    # Use most recent file
    latest_file = max(files, key=lambda p: p.stat().st_mtime)
    returns = np.load(latest_file)
    
    print(f"  Loaded: {latest_file.name}")
    print(f"  Shape: {returns.shape} (n_trials × n_observations)")
    
    return returns

def compute_cscv_pbo(returns_matrix: np.ndarray, n_splits: int = 6, n_test_splits: int = 2) -> dict:
    """
    Compute PBO using CSCV (Combinatorial Split Cross-Validation).
    
    Uses C(n_splits, n_test_splits) combinations for robust validation.
    """
    n_trials, n_obs = returns_matrix.shape
    
    # Create CSCV splitter
    cpcv = CombinatorialPurgedKFold(
        n_splits=n_splits,
        n_test_splits=n_test_splits,
        purge_gap=0,  # No purging for OHLCV data
        embargo_pct=0.01
    )
    
    n_combinations = cpcv.get_n_splits()
    print(f"  CSCV combinations: {n_combinations} (C({n_splits},{n_test_splits}))")
    
    # Compute PBO
    result = probability_of_backtest_overfitting(
        returns_matrix,
        n_splits=n_splits
    )
    
    return {
        "pbo": result.pbo,
        "n_combinations": n_combinations,
        "n_trials": n_trials,
        "n_obs": n_obs,
        "interpretation": result.interpretation,
        "pass": result.pbo < 0.50
    }

def main():
    print("=" * 70)
    print("CHALLENGER — ETH/YGG with True CSCV PBO")
    print("=" * 70)
    print("Post PR#31: Combinatorial Split Cross-Validation")
    print()
    
    results = []
    
    for asset in CHALLENGER_ASSETS:
        print(f"🔬 Testing {asset}...")
        
        try:
            # Load returns matrix
            returns_matrix = load_returns_matrix(asset)
            
            # Compute CSCV PBO
            result = compute_cscv_pbo(returns_matrix)
            
            print(f"  PBO (CSCV): {result['pbo']:.4f}")
            print(f"  Verdict: {'✅ PASS' if result['pass'] else '❌ FAIL'}")
            print(f"  Interpretation: {result['interpretation']}")
            print()
            
            results.append({
                "asset": asset,
                **result
            })
            
        except FileNotFoundError as e:
            print(f"  ❌ Error: {e}")
            print()
            continue
    
    # Summary
    if results:
        print("\n📊 CSCV PBO Summary:")
        df = pd.DataFrame(results)
        print(df.to_string(index=False))
        
        # Save
        output_file = Path("outputs/cscv_pbo_challenger_eth_ygg.csv")
        df.to_csv(output_file, index=False)
        print(f"\n💾 Saved: {output_file}")
        
        # Verdict
        n_pass = df['pass'].sum()
        n_total = len(df)
        print(f"\n✅ Pass rate: {n_pass}/{n_total} ({100*n_pass/n_total:.1f}%)")
    else:
        print("❌ No results computed (missing returns matrices)")
        print("\n💡 Tip: Run optimization with --save-returns-matrix flag")

if __name__ == "__main__":
    main()
