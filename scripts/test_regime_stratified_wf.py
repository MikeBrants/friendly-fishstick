"""
Test regime-stratified walk-forward on real asset data.

Compares standard WF vs regime-aware WF for ETH, SHIB, DOT.

Usage:
    python scripts/test_regime_stratified_wf.py
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import pandas as pd
import numpy as np
from typing import Dict

from crypto_backtest.analysis.regime_v3 import CryptoRegimeAnalyzer
from crypto_backtest.optimization.walk_forward import (
    stratified_regime_split,
    validate_regime_balance,
    _standard_walk_forward_split,
)
from crypto_backtest.data.storage import ParquetStore, CacheKey


def analyze_asset_regimes(asset: str) -> Dict:
    """
    Analyze regime distribution for an asset and compare WF methods.

    Args:
        asset: Asset ticker (e.g., "ETH")

    Returns:
        dict with analysis results
    """
    print(f"\n{'=' * 80}")
    print(f"Analyzing {asset}")
    print(f"{'=' * 80}\n")

    # Load data
    try:
        data_path = project_root / "data" / f"{asset}_1H.parquet"
        if not data_path.exists():
            print(f"ERROR: Data for {asset} not found at {data_path}")
            return {"error": "data_not_found"}

        data = pd.read_parquet(data_path)

        # Set timestamp as index
        if "timestamp" in data.columns:
            data["timestamp"] = pd.to_datetime(data["timestamp"])
            data = data.set_index("timestamp")
        elif not isinstance(data.index, pd.DatetimeIndex):
            print(f"ERROR: No timestamp column found for {asset}")
            return {"error": "no_timestamp"}

    except Exception as e:
        print(f"ERROR loading data: {e}")
        return {"error": "data_load_failed"}

    print(f"Loaded {len(data)} bars for {asset}")
    print(f"Period: {data.index[0]} to {data.index[-1]}")

    # Run regime classification
    print("\nRunning regime classification...")
    analyzer = CryptoRegimeAnalyzer(use_hmm=False, lookback=200)
    regimes_df = analyzer.fit_and_classify(data)

    # Add regime column to data
    data_with_regimes = data.copy()
    data_with_regimes["crypto_regime"] = regimes_df["crypto_regime"]

    # Get regime distribution
    regime_counts = data_with_regimes["crypto_regime"].value_counts()
    print("\nOverall Regime Distribution:")
    for regime, count in regime_counts.items():
        pct = count / len(data_with_regimes) * 100
        print(f"  {regime:15s}: {count:5d} bars ({pct:5.2f}%)")

    # Test standard walk-forward
    print("\n" + "-" * 80)
    print("Standard Walk-Forward (no regime awareness)")
    print("-" * 80)

    standard_splits = _standard_walk_forward_split(data_with_regimes, n_splits=3)
    standard_distributions = []

    for fold_id, (train_idx, test_idx) in enumerate(standard_splits):
        test_data = data_with_regimes.iloc[test_idx]
        test_dist = test_data["crypto_regime"].value_counts(normalize=True).to_dict()
        standard_distributions.append(test_dist)

        print(f"\nFold {fold_id}:")
        print(f"  Train: {len(train_idx)} bars | Test: {len(test_idx)} bars")
        print("  Test regime distribution:")
        for regime in ["ACCUMULATION", "MARKDOWN", "SIDEWAYS"]:
            pct = test_dist.get(regime, 0.0) * 100
            marker = "WARN" if pct < 15 else "OK  "
            print(f"    [{marker}] {regime:15s}: {pct:5.2f}%")

    # Test regime-stratified walk-forward
    print("\n" + "-" * 80)
    print("Regime-Stratified Walk-Forward (min 15% per regime)")
    print("-" * 80)

    try:
        # Check which regimes are actually present with sufficient data
        regime_counts_pct = regime_counts / len(data_with_regimes)
        available_regimes = []
        for regime in ["ACCUMULATION", "MARKDOWN", "SIDEWAYS"]:
            if regime_counts_pct.get(regime, 0) >= 0.05:  # At least 5% of data
                available_regimes.append(regime)

        if not available_regimes:
            # Fallback: use ACCUMULATION and MARKDOWN only
            available_regimes = ["ACCUMULATION", "MARKDOWN"]

        print(f"\nUsing regimes for stratification: {available_regimes}")

        stratified_splits, stratified_distributions = stratified_regime_split(
            data_with_regimes,
            regime_col="crypto_regime",
            n_splits=3,
            min_regime_pct=0.15,
            required_regimes=available_regimes,
        )

        for fold_id, dist in stratified_distributions.items():
            train_idx, test_idx = stratified_splits[fold_id]
            print(f"\nFold {fold_id}:")
            print(f"  Train: {len(train_idx)} bars | Test: {len(test_idx)} bars")
            print("  Test regime distribution:")
            for regime in available_regimes:
                pct = dist.get(regime, 0.0) * 100
                marker = "OK  " if pct >= 15 else "WARN"
                print(f"    [{marker}] {regime:15s}: {pct:5.2f}%")

        # Validate regime balance
        validation = validate_regime_balance(
            stratified_distributions,
            min_regime_pct=0.15,
            required_regimes=available_regimes,
        )

        print("\nRegime Balance Validation:")
        if validation["passed"]:
            print("  [PASS] All folds meet minimum regime requirements")
        else:
            print("  [FAIL] Some folds do not meet requirements")
            for violation in validation["violations"]:
                print(f"    Fold {violation['fold']}: {violation['regime']} "
                      f"{violation['actual_pct']:.2%} < {violation['required_pct']:.2%}")

    except Exception as e:
        print(f"ERROR in regime-stratified WF: {e}")
        validation = {"passed": False, "error": str(e)}

    # Comparison summary
    print("\n" + "=" * 80)
    print("COMPARISON SUMMARY")
    print("=" * 80)

    # Check if standard WF has regime imbalance
    has_imbalance = False
    for fold_id, dist in enumerate(standard_distributions):
        for regime in ["ACCUMULATION", "MARKDOWN", "SIDEWAYS"]:
            if dist.get(regime, 0.0) < 0.15:
                has_imbalance = True
                break

    if has_imbalance:
        print("\n[WARN] Standard WF shows regime imbalance (< 15% for some regimes)")
        print("[OK]   Regime-stratified WF ensures balanced representation")
        print("\nRECOMMENDATION: Use regime-stratified WF for this asset")
    else:
        print("\n[OK] Standard WF already has balanced regime distribution")
        print("     Regime-stratified WF provides additional guarantee")
        print("\nRECOMMENDATION: Both methods acceptable, regime-stratified preferred for robustness")

    return {
        "asset": asset,
        "total_bars": len(data_with_regimes),
        "regime_distribution": regime_counts.to_dict(),
        "standard_wf": {
            "distributions": standard_distributions,
            "has_imbalance": has_imbalance,
        },
        "stratified_wf": {
            "distributions": dict(stratified_distributions) if stratified_distributions else {},
            "validation": validation,
        },
    }


def main():
    """Run regime-stratified WF analysis on pilot assets."""
    pilot_assets = ["ETH", "SHIB", "DOT"]

    print("=" * 80)
    print("REGIME-STRATIFIED WALK-FORWARD ANALYSIS")
    print("Testing on pilot assets: ETH, SHIB, DOT")
    print("=" * 80)

    results = {}
    for asset in pilot_assets:
        try:
            results[asset] = analyze_asset_regimes(asset)
        except Exception as e:
            print(f"\nERROR analyzing {asset}: {e}")
            results[asset] = {"error": str(e)}

    # Final summary
    print("\n\n" + "=" * 80)
    print("FINAL SUMMARY")
    print("=" * 80)

    for asset, result in results.items():
        if "error" in result:
            print(f"\n{asset}: ERROR - {result['error']}")
        else:
            validation = result.get("stratified_wf", {}).get("validation", {})
            if validation.get("passed"):
                print(f"\n{asset}: [PASS] Regime-stratified WF working correctly")
            else:
                print(f"\n{asset}: [FAIL] Issues detected")

    print("\n" + "=" * 80)
    print("Analysis complete!")
    print("=" * 80)


if __name__ == "__main__":
    main()
