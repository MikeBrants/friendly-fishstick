#!/usr/bin/env python3
"""
Phase 5 Portfolio Construction — Check Correlations
Validates correlation < 0.5 criterion for TIER 1 PROD assets
"""

import pandas as pd
import numpy as np
from pathlib import Path

# TIER 1 PROD assets from PR#21
PROD_ASSETS = ["SOL", "AVAX", "ETH", "BTC", "AXS"]

def load_returns(asset: str, data_dir: Path = Path("data")) -> pd.Series:
    """Load hourly returns for an asset."""
    file_path = data_dir / f"{asset}_1H.parquet"
    if not file_path.exists():
        raise FileNotFoundError(f"Data file not found: {file_path}")
    
    df = pd.read_csv(file_path) if file_path.suffix == ".csv" else pd.read_parquet(file_path)
    df['returns'] = df['close'].pct_change()
    return df['returns'].dropna()

def compute_correlation_matrix(assets: list[str]) -> pd.DataFrame:
    """Compute correlation matrix for list of assets."""
    returns_dict = {}
    
    for asset in assets:
        try:
            returns_dict[asset] = load_returns(asset)
            print(f"✅ Loaded {asset}: {len(returns_dict[asset])} bars")
        except FileNotFoundError as e:
            print(f"❌ {asset}: {e}")
            continue
    
    # Align all series to common datetime index
    returns_df = pd.DataFrame(returns_dict)
    
    # Compute correlation matrix
    corr_matrix = returns_df.corr()
    
    return corr_matrix

def check_portfolio_criterion(corr_matrix: pd.DataFrame, threshold: float = 0.5) -> dict:
    """Check if portfolio meets correlation < threshold criterion."""
    n_assets = len(corr_matrix)
    n_pairs = (n_assets * (n_assets - 1)) // 2
    
    # Extract upper triangle (exclude diagonal)
    upper_tri = np.triu(corr_matrix.values, k=1)
    correlations = upper_tri[upper_tri != 0]
    
    # Check violations
    violations = correlations[correlations >= threshold]
    
    result = {
        "n_assets": n_assets,
        "n_pairs": n_pairs,
        "mean_corr": correlations.mean(),
        "max_corr": correlations.max(),
        "threshold": threshold,
        "n_violations": len(violations),
        "pass": len(violations) == 0
    }
    
    return result

def main():
    print("=" * 60)
    print("Phase 5: Portfolio Correlation Check")
    print("=" * 60)
    print(f"Assets: {', '.join(PROD_ASSETS)}")
    print(f"Criterion: Correlation < 0.5")
    print()
    
    # Compute correlation matrix
    corr_matrix = compute_correlation_matrix(PROD_ASSETS)
    
    print("\n📊 Correlation Matrix:")
    print(corr_matrix.round(3))
    print()
    
    # Check criterion
    result = check_portfolio_criterion(corr_matrix)
    
    print("📋 Portfolio Analysis:")
    print(f"  - Assets: {result['n_assets']}")
    print(f"  - Pairs: {result['n_pairs']}")
    print(f"  - Mean correlation: {result['mean_corr']:.3f}")
    print(f"  - Max correlation: {result['max_corr']:.3f}")
    print(f"  - Violations (≥{result['threshold']}): {result['n_violations']}")
    print()
    
    if result['pass']:
        print("✅ PASS: Portfolio meets correlation criterion (<0.5)")
    else:
        print(f"❌ FAIL: {result['n_violations']} pairs exceed threshold")
        print("\nHigh correlation pairs:")
        for i in range(len(corr_matrix)):
            for j in range(i+1, len(corr_matrix)):
                corr = corr_matrix.iloc[i, j]
                if corr >= result['threshold']:
                    print(f"  - {corr_matrix.index[i]} ↔ {corr_matrix.columns[j]}: {corr:.3f}")
    
    # Save results
    output_file = Path("outputs/portfolio_correlations_tier1.csv")
    corr_matrix.to_csv(output_file)
    print(f"\n💾 Saved: {output_file}")

if __name__ == "__main__":
    main()
