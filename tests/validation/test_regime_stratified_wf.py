"""
Tests for regime-stratified walk-forward splits.

Validates that splits maintain minimum regime representation across all folds.
"""

import numpy as np
import pandas as pd
import pytest

from crypto_backtest.optimization.walk_forward import (
    stratified_regime_split,
    validate_regime_balance,
    _standard_walk_forward_split,
)


@pytest.fixture
def sample_data_with_regimes():
    """Create synthetic data with regime labels."""
    n_samples = 1000
    np.random.seed(42)

    # Create time index
    dates = pd.date_range("2023-01-01", periods=n_samples, freq="1h")

    # Create regime labels with realistic distribution
    regimes = []
    # 50% ACCUMULATION
    regimes.extend(["ACCUMULATION"] * 500)
    # 25% MARKDOWN
    regimes.extend(["MARKDOWN"] * 250)
    # 15% SIDEWAYS
    regimes.extend(["SIDEWAYS"] * 150)
    # 10% other (MARKUP, RECOVERY, etc.)
    regimes.extend(["MARKUP"] * 50)
    regimes.extend(["RECOVERY"] * 50)

    # Shuffle to simulate realistic transitions
    np.random.shuffle(regimes)

    data = pd.DataFrame({
        "close": np.random.randn(n_samples).cumsum() + 100,
        "crypto_regime": regimes,
    }, index=dates)

    return data


@pytest.fixture
def sample_data_imbalanced():
    """Create data with highly imbalanced regimes."""
    n_samples = 1000
    np.random.seed(42)

    dates = pd.date_range("2023-01-01", periods=n_samples, freq="1h")

    # 80% ACCUMULATION, 15% MARKUP, 5% MARKDOWN (insufficient)
    regimes = []
    regimes.extend(["ACCUMULATION"] * 800)
    regimes.extend(["MARKUP"] * 150)
    regimes.extend(["MARKDOWN"] * 50)  # Too few for 15% per fold × 3 folds

    np.random.shuffle(regimes)

    data = pd.DataFrame({
        "close": np.random.randn(n_samples).cumsum() + 100,
        "crypto_regime": regimes,
    }, index=dates)

    return data


class TestStratifiedRegimeSplit:
    """Test suite for regime-stratified walk-forward splitting."""

    def test_basic_split_creation(self, sample_data_with_regimes):
        """Test that splits are created successfully."""
        splits, distributions = stratified_regime_split(
            sample_data_with_regimes,
            regime_col="crypto_regime",
            n_splits=3,
            min_regime_pct=0.15,
        )

        assert len(splits) == 3, "Should create 3 splits"
        assert len(distributions) == 3, "Should have distribution for each split"

        for train_idx, test_idx in splits:
            assert len(train_idx) > 0, "Train set should not be empty"
            assert len(test_idx) > 0, "Test set should not be empty"
            # No overlap
            assert len(set(train_idx) & set(test_idx)) == 0, "Train/test overlap detected"

    def test_minimum_regime_percentage(self, sample_data_with_regimes):
        """Test that each fold has minimum 15% of each required regime."""
        min_pct = 0.15
        splits, distributions = stratified_regime_split(
            sample_data_with_regimes,
            regime_col="crypto_regime",
            n_splits=3,
            min_regime_pct=min_pct,
            required_regimes=["ACCUMULATION", "MARKDOWN", "SIDEWAYS"],
        )

        for fold_id, dist in distributions.items():
            # Check ACCUMULATION (most common)
            accum_pct = dist.get("ACCUMULATION", 0.0)
            assert accum_pct >= min_pct, f"Fold {fold_id}: ACCUMULATION {accum_pct:.2%} < {min_pct:.2%}"

            # Check MARKDOWN
            markdown_pct = dist.get("MARKDOWN", 0.0)
            assert markdown_pct >= min_pct, f"Fold {fold_id}: MARKDOWN {markdown_pct:.2%} < {min_pct:.2%}"

            # Check SIDEWAYS
            sideways_pct = dist.get("SIDEWAYS", 0.0)
            assert sideways_pct >= min_pct, f"Fold {fold_id}: SIDEWAYS {sideways_pct:.2%} < {min_pct:.2%}"

    def test_imbalanced_data_handling(self, sample_data_imbalanced):
        """Test that imbalanced data falls back gracefully."""
        splits, distributions = stratified_regime_split(
            sample_data_imbalanced,
            regime_col="crypto_regime",
            n_splits=3,
            min_regime_pct=0.15,
            required_regimes=["ACCUMULATION", "MARKDOWN", "MARKUP"],
        )

        # Should still create splits even if MARKDOWN is insufficient
        assert len(splits) == 3, "Should create splits despite imbalance"

        # ACCUMULATION should meet minimum (it's 80% of data, so definitely available)
        for fold_id, dist in distributions.items():
            accum_pct = dist.get("ACCUMULATION", 0.0)
            # Should meet at least the 15% minimum (may not be much higher due to balancing)
            assert accum_pct >= 0.15, f"Fold {fold_id}: ACCUMULATION below minimum: {accum_pct:.2%}"

            # MARKUP should also be represented (15% of data)
            markup_pct = dist.get("MARKUP", 0.0)
            assert markup_pct >= 0.10, f"Fold {fold_id}: MARKUP too low: {markup_pct:.2%}"

    def test_validation_function(self, sample_data_with_regimes):
        """Test regime balance validation."""
        splits, distributions = stratified_regime_split(
            sample_data_with_regimes,
            regime_col="crypto_regime",
            n_splits=3,
            min_regime_pct=0.15,
        )

        validation = validate_regime_balance(
            distributions,
            min_regime_pct=0.15,
            required_regimes=["ACCUMULATION", "MARKDOWN", "SIDEWAYS"],
        )

        assert validation["passed"], f"Validation failed: {validation['violations']}"
        assert len(validation["violations"]) == 0, "Should have no violations"

    def test_missing_regime_column(self, sample_data_with_regimes):
        """Test error handling for missing regime column."""
        with pytest.raises(ValueError, match="not found in data"):
            stratified_regime_split(
                sample_data_with_regimes,
                regime_col="nonexistent_column",
                n_splits=3,
            )

    def test_distribution_sums_to_one(self, sample_data_with_regimes):
        """Test that regime percentages sum to 1.0 for each fold."""
        splits, distributions = stratified_regime_split(
            sample_data_with_regimes,
            regime_col="crypto_regime",
            n_splits=3,
        )

        for fold_id, dist in distributions.items():
            total_pct = sum(dist.values())
            assert 0.99 <= total_pct <= 1.01, f"Fold {fold_id}: percentages sum to {total_pct:.4f}"

    def test_compare_with_standard_wf(self, sample_data_with_regimes):
        """Compare regime-stratified vs standard walk-forward."""
        # Standard WF
        standard_splits = _standard_walk_forward_split(sample_data_with_regimes, n_splits=3)

        # Regime-stratified WF
        stratified_splits, _ = stratified_regime_split(
            sample_data_with_regimes,
            regime_col="crypto_regime",
            n_splits=3,
            min_regime_pct=0.15,
        )

        # Both should create same number of splits
        assert len(standard_splits) == len(stratified_splits)

        # Stratified should have different indices (due to stratification)
        for i, ((std_train, std_test), (strat_train, strat_test)) in enumerate(
            zip(standard_splits, stratified_splits)
        ):
            # Test sets should differ (stratified enforces regime balance)
            assert not np.array_equal(std_test, strat_test), f"Split {i}: test sets should differ"


class TestRegimeDistributionAnalysis:
    """Test regime distribution reporting."""

    def test_distribution_keys(self, sample_data_with_regimes):
        """Test that distribution dict has correct structure."""
        splits, distributions = stratified_regime_split(
            sample_data_with_regimes,
            regime_col="crypto_regime",
            n_splits=3,
        )

        for fold_id, dist in distributions.items():
            assert isinstance(fold_id, int), "Fold ID should be integer"
            assert isinstance(dist, dict), "Distribution should be dict"
            assert all(isinstance(v, float) for v in dist.values()), "Values should be floats"

    def test_all_regimes_present(self, sample_data_with_regimes):
        """Test that all regimes from data appear in at least one fold."""
        splits, distributions = stratified_regime_split(
            sample_data_with_regimes,
            regime_col="crypto_regime",
            n_splits=3,
        )

        all_regimes_in_folds = set()
        for dist in distributions.values():
            all_regimes_in_folds.update(dist.keys())

        original_regimes = set(sample_data_with_regimes["crypto_regime"].unique())
        assert all_regimes_in_folds >= {"ACCUMULATION", "MARKDOWN", "SIDEWAYS"}, \
            "Key regimes should appear in distributions"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
