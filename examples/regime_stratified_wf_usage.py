"""
Example usage of Regime-Stratified Walk-Forward Cross-Validation.

This example demonstrates how to use the regime-aware splits in backtesting
and optimization workflows.

Author: Alex (Lead Quant)
Date: 2026-01-26
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import pandas as pd
import numpy as np

from crypto_backtest.analysis.regime_v3 import CryptoRegimeAnalyzer
from crypto_backtest.optimization.walk_forward import (
    stratified_regime_split,
    validate_regime_balance,
    _standard_walk_forward_split,
)


# ============================================================================
# EXAMPLE 1: Basic Usage
# ============================================================================

def example_1_basic_usage():
    """Basic example: Create regime-stratified splits."""
    print("=" * 80)
    print("EXAMPLE 1: Basic Regime-Stratified Splits")
    print("=" * 80 + "\n")

    # 1. Load your OHLCV data
    data_path = project_root / "data" / "ETH_1H.parquet"
    if not data_path.exists():
        print("ERROR: ETH data not found. Run data download first.")
        return

    data = pd.read_parquet(data_path)
    if "timestamp" in data.columns:
        data["timestamp"] = pd.to_datetime(data["timestamp"])
        data = data.set_index("timestamp")

    print(f"Loaded {len(data)} bars of ETH data\n")

    # 2. Run regime classification
    print("Running regime classification...")
    analyzer = CryptoRegimeAnalyzer(use_hmm=False, lookback=200)
    regimes_df = analyzer.fit_and_classify(data)

    # Add regime to data
    data["crypto_regime"] = regimes_df["crypto_regime"]

    # Check regime distribution
    regime_dist = data["crypto_regime"].value_counts(normalize=True)
    print("\nRegime Distribution:")
    for regime, pct in regime_dist.items():
        print(f"  {regime:15s}: {pct*100:5.2f}%")

    # 3. Create regime-stratified splits
    print("\n" + "-" * 80)
    print("Creating regime-stratified splits...")
    print("-" * 80 + "\n")

    splits, distributions = stratified_regime_split(
        data,
        regime_col="crypto_regime",
        n_splits=3,
        min_regime_pct=0.15,
        required_regimes=["ACCUMULATION", "MARKDOWN"],
    )

    # 4. Inspect splits
    for fold_id, (train_idx, test_idx) in enumerate(splits):
        print(f"Fold {fold_id}:")
        print(f"  Train: {len(train_idx):5d} samples")
        print(f"  Test:  {len(test_idx):5d} samples")
        print(f"  Regime distribution in test set:")
        for regime, pct in distributions[fold_id].items():
            print(f"    {regime:15s}: {pct*100:5.2f}%")
        print()

    # 5. Validate regime balance
    validation = validate_regime_balance(
        distributions,
        min_regime_pct=0.15,
        required_regimes=["ACCUMULATION", "MARKDOWN"],
    )

    if validation["passed"]:
        print("[PASS] All folds meet minimum regime requirements ✓")
    else:
        print("[FAIL] Some folds do not meet requirements:")
        for violation in validation["violations"]:
            print(f"  - {violation}")


# ============================================================================
# EXAMPLE 2: Integration with Backtesting
# ============================================================================

def example_2_backtest_integration():
    """Example: Use regime-stratified splits in backtesting."""
    print("\n" + "=" * 80)
    print("EXAMPLE 2: Integration with Backtesting")
    print("=" * 80 + "\n")

    # Load data (same as Example 1)
    data_path = project_root / "data" / "ETH_1H.parquet"
    if not data_path.exists():
        print("ERROR: ETH data not found.")
        return

    data = pd.read_parquet(data_path)
    if "timestamp" in data.columns:
        data["timestamp"] = pd.to_datetime(data["timestamp"])
        data = data.set_index("timestamp")

    # Add regime classification
    analyzer = CryptoRegimeAnalyzer(use_hmm=False, lookback=200)
    regimes_df = analyzer.fit_and_classify(data)
    data["crypto_regime"] = regimes_df["crypto_regime"]

    # Create splits
    splits, distributions = stratified_regime_split(
        data,
        regime_col="crypto_regime",
        n_splits=3,
        min_regime_pct=0.15,
        required_regimes=["ACCUMULATION", "MARKDOWN"],
    )

    print("Running walk-forward backtests on regime-stratified splits...\n")

    # Simulate backtesting on each fold
    is_sharpes = []
    oos_sharpes = []

    for fold_id, (train_idx, test_idx) in enumerate(splits):
        train_data = data.iloc[train_idx]
        test_data = data.iloc[test_idx]

        # Simulate Sharpe calculation (replace with real backtest)
        # In practice, this would call your backtester:
        # from crypto_backtest.engine.backtest import VectorizedBacktester
        # result = backtester.run(train_data, strategy)

        is_sharpe = np.random.uniform(1.5, 2.5)  # Simulated IS Sharpe
        oos_sharpe = np.random.uniform(1.0, 2.0)  # Simulated OOS Sharpe

        is_sharpes.append(is_sharpe)
        oos_sharpes.append(oos_sharpe)

        print(f"Fold {fold_id}:")
        print(f"  IS Sharpe:  {is_sharpe:.2f}")
        print(f"  OOS Sharpe: {oos_sharpe:.2f}")
        print(f"  WFE:        {oos_sharpe / is_sharpe:.2f}")
        print()

    # Calculate overall WFE
    mean_is = np.mean(is_sharpes)
    mean_oos = np.mean(oos_sharpes)
    wfe = mean_oos / mean_is

    print("-" * 80)
    print("Overall Walk-Forward Results:")
    print(f"  Mean IS Sharpe:  {mean_is:.2f}")
    print(f"  Mean OOS Sharpe: {mean_oos:.2f}")
    print(f"  WFE (OOS/IS):    {wfe:.2f}")
    print()

    if wfe >= 0.6:
        print("[PASS] WFE >= 0.6 - Strategy is robust ✓")
    else:
        print("[FAIL] WFE < 0.6 - Strategy may be overfitting")


# ============================================================================
# EXAMPLE 3: Comparison with Standard WF
# ============================================================================

def example_3_comparison():
    """Example: Compare regime-stratified vs standard walk-forward."""
    print("\n" + "=" * 80)
    print("EXAMPLE 3: Comparison with Standard Walk-Forward")
    print("=" * 80 + "\n")

    # Load data
    data_path = project_root / "data" / "ETH_1H.parquet"
    if not data_path.exists():
        print("ERROR: ETH data not found.")
        return

    data = pd.read_parquet(data_path)
    if "timestamp" in data.columns:
        data["timestamp"] = pd.to_datetime(data["timestamp"])
        data = data.set_index("timestamp")

    # Add regime classification
    analyzer = CryptoRegimeAnalyzer(use_hmm=False, lookback=200)
    regimes_df = analyzer.fit_and_classify(data)
    data["crypto_regime"] = regimes_df["crypto_regime"]

    # Standard WF
    print("Standard Walk-Forward:")
    print("-" * 80)
    standard_splits = _standard_walk_forward_split(data, n_splits=3)

    for fold_id, (train_idx, test_idx) in enumerate(standard_splits):
        test_data = data.iloc[test_idx]
        test_dist = test_data["crypto_regime"].value_counts(normalize=True)

        print(f"\nFold {fold_id}:")
        print(f"  Test size: {len(test_idx)} bars")
        print(f"  Regime distribution:")
        for regime in ["ACCUMULATION", "MARKDOWN"]:
            pct = test_dist.get(regime, 0.0) * 100
            warning = " [< 15%]" if pct < 15 else ""
            print(f"    {regime:15s}: {pct:5.2f}%{warning}")

    # Regime-stratified WF
    print("\n" + "=" * 80)
    print("Regime-Stratified Walk-Forward:")
    print("-" * 80)

    stratified_splits, distributions = stratified_regime_split(
        data,
        regime_col="crypto_regime",
        n_splits=3,
        min_regime_pct=0.15,
        required_regimes=["ACCUMULATION", "MARKDOWN"],
    )

    for fold_id, dist in distributions.items():
        train_idx, test_idx = stratified_splits[fold_id]
        print(f"\nFold {fold_id}:")
        print(f"  Test size: {len(test_idx)} bars")
        print(f"  Regime distribution:")
        for regime in ["ACCUMULATION", "MARKDOWN"]:
            pct = dist.get(regime, 0.0) * 100
            check = " [OK]" if pct >= 15 else ""
            print(f"    {regime:15s}: {pct:5.2f}%{check}")

    print("\n" + "=" * 80)
    print("Conclusion:")
    print("Standard WF may show regime imbalance (< 15% for some regimes).")
    print("Regime-stratified WF guarantees balanced representation.")
    print("=" * 80)


# ============================================================================
# MAIN
# ============================================================================

def main():
    """Run all examples."""
    print("\n")
    print("*" * 80)
    print("REGIME-STRATIFIED WALK-FORWARD: USAGE EXAMPLES")
    print("*" * 80)

    try:
        example_1_basic_usage()
    except Exception as e:
        print(f"Example 1 failed: {e}")

    try:
        example_2_backtest_integration()
    except Exception as e:
        print(f"Example 2 failed: {e}")

    try:
        example_3_comparison()
    except Exception as e:
        print(f"Example 3 failed: {e}")

    print("\n" + "*" * 80)
    print("All examples complete!")
    print("*" * 80 + "\n")


if __name__ == "__main__":
    main()
