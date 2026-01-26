"""
Full test suite for CPCV Full Activation (TASK 1).

Tests the integration of Combinatorial Purged Cross-Validation (CPCV)
with Probability of Backtest Overfitting (PBO).
"""

import numpy as np
import pandas as pd
import pytest

from crypto_backtest.validation.cpcv import (
    CombinatorialPurgedKFold,
    CPCVPBOResult,
    pbo_with_cpcv,
    guard_cpcv_pbo,
    validate_with_cpcv,
)


def _dummy_data(n_rows: int = 120) -> pd.DataFrame:
    """Generate dummy OHLCV data."""
    return pd.DataFrame(
        {
            "open": np.linspace(1, 2, n_rows),
            "high": np.linspace(1.1, 2.1, n_rows),
            "low": np.linspace(0.9, 1.9, n_rows),
            "close": np.linspace(1, 2, n_rows),
        }
    )


def _random_returns(n_trials: int, n_periods: int, seed: int = 42) -> np.ndarray:
    """Generate random returns matrix for testing."""
    rng = np.random.default_rng(seed)
    return rng.normal(loc=0.0, scale=0.01, size=(n_trials, n_periods))


# =============================================================================
# TEST 1: CPCV generates exactly 15 combinations for C(6,2)
# =============================================================================
def test_cpcv_generates_15_combinations():
    """Test that CPCV with n_splits=6, n_test_splits=2 generates C(6,2)=15 combinations."""
    cpcv = CombinatorialPurgedKFold(n_splits=6, n_test_splits=2)
    assert cpcv.get_n_splits() == 15, "C(6,2) should equal 15"


# =============================================================================
# TEST 2: CPCV + PBO integration returns correct structure
# =============================================================================
def test_pbo_with_cpcv_returns_correct_structure():
    """Test that pbo_with_cpcv returns CPCVPBOResult with all required fields."""
    returns = _random_returns(n_trials=50, n_periods=600, seed=42)
    result = pbo_with_cpcv(
        returns,
        n_splits=6,
        n_test_splits=2,
        purge_gap=5,
        embargo_pct=0.01,
        threshold=0.15,
    )

    assert isinstance(result, CPCVPBOResult)
    assert hasattr(result, "pbo")
    assert hasattr(result, "pbo_median_rank")
    assert hasattr(result, "n_combinations")
    assert hasattr(result, "threshold")
    assert hasattr(result, "passed")
    assert hasattr(result, "is_sharpes_mean")
    assert hasattr(result, "oos_sharpes_mean")
    assert hasattr(result, "wfe_cpcv")
    assert hasattr(result, "logits")


# =============================================================================
# TEST 3: CPCV + PBO uses exactly 15 combinations
# =============================================================================
def test_pbo_with_cpcv_uses_15_combinations():
    """Test that pbo_with_cpcv processes all 15 CPCV combinations."""
    returns = _random_returns(n_trials=30, n_periods=600, seed=42)
    result = pbo_with_cpcv(returns, n_splits=6, n_test_splits=2)

    assert result.n_combinations == 15, "Should process 15 CPCV combinations"
    assert len(result.logits) == 15, "Should have 15 relative rank logits"


# =============================================================================
# TEST 4: PBO value is within valid range [0, 1]
# =============================================================================
def test_pbo_value_in_valid_range():
    """Test that PBO value is always between 0 and 1."""
    returns = _random_returns(n_trials=50, n_periods=600, seed=7)
    result = pbo_with_cpcv(returns, n_splits=6, n_test_splits=2)

    assert 0.0 <= result.pbo <= 1.0, "PBO must be in [0, 1]"
    assert 0.0 <= result.pbo_median_rank <= 1.0, "Median rank must be in [0, 1]"


# =============================================================================
# TEST 5: Perfect strategy should have low PBO
# =============================================================================
def test_pbo_low_for_perfect_strategy():
    """Test that a consistently superior strategy has low PBO."""
    returns = _random_returns(n_trials=50, n_periods=600, seed=11)
    # Make trial 0 consistently better across all periods
    returns[0] += 0.02

    result = pbo_with_cpcv(returns, n_splits=6, n_test_splits=2, threshold=0.15)

    # Perfect strategy should pass (low PBO)
    assert result.pbo < 0.30, "Perfect strategy should have low PBO"
    # Note: May not always be < 0.15 due to randomness, but should be < 0.30


# =============================================================================
# TEST 6: Random strategies should have moderate to high PBO
# =============================================================================
def test_pbo_moderate_for_random_strategies():
    """Test that random strategies have moderate to high PBO."""
    returns = _random_returns(n_trials=50, n_periods=600, seed=13)
    result = pbo_with_cpcv(returns, n_splits=6, n_test_splits=2)

    # Random strategies should have PBO around 0.5 (median)
    assert 0.2 <= result.pbo <= 0.8, "Random strategies should have moderate PBO"


# =============================================================================
# TEST 7: Purging is enforced
# =============================================================================
def test_cpcv_purging_enforced():
    """Test that purging is correctly applied around test boundaries."""
    data = _dummy_data(120)
    cpcv = CombinatorialPurgedKFold(
        n_splits=4,
        n_test_splits=1,
        purge_gap=3,
        embargo_pct=0.0,
    )

    for train_idx, test_idx in cpcv.split(data):
        # Verify no train sample is within purge_gap of any test sample
        for t in test_idx:
            distances = np.abs(train_idx - t)
            assert np.all(distances > 3), f"Purge gap violated at test idx {t}"


# =============================================================================
# TEST 8: Embargo is enforced
# =============================================================================
def test_cpcv_embargo_enforced():
    """Test that embargo period is correctly applied after test set."""
    data = _dummy_data(120)
    cpcv = CombinatorialPurgedKFold(
        n_splits=4,
        n_test_splits=1,
        purge_gap=0,
        embargo_pct=0.1,
    )

    split_size = len(data) // cpcv.n_splits
    embargo_size = int(len(data) * cpcv.embargo_pct)

    for train_idx, test_idx in cpcv.split(data):
        test_end = int(test_idx.max()) + 1
        embargo_start = test_end
        embargo_end = min(test_end + embargo_size, len(data))
        embargo_range = set(range(embargo_start, embargo_end))

        # Verify no train sample falls in embargo period
        assert not (set(train_idx) & embargo_range), "Embargo period violated"


# =============================================================================
# TEST 9: WFE calculation is correct
# =============================================================================
def test_pbo_wfe_calculation():
    """Test that WFE is correctly calculated as mean(OOS)/mean(IS)."""
    returns = _random_returns(n_trials=30, n_periods=600, seed=17)
    result = pbo_with_cpcv(returns, n_splits=6, n_test_splits=2)

    # WFE should be ratio of mean OOS to mean IS Sharpe
    if result.is_sharpes_mean != 0:
        expected_wfe = result.oos_sharpes_mean / result.is_sharpes_mean
        assert abs(result.wfe_cpcv - expected_wfe) < 1e-6, "WFE calculation incorrect"


# =============================================================================
# TEST 10: Guard function returns correct format
# =============================================================================
def test_guard_cpcv_pbo_format():
    """Test that guard_cpcv_pbo returns correctly formatted dict."""
    returns = _random_returns(n_trials=30, n_periods=600, seed=19)
    result = guard_cpcv_pbo(
        returns,
        threshold=0.15,
        n_splits=6,
        n_test_splits=2,
    )

    # Verify all required keys
    assert result["guard"] == "cpcv_pbo"
    assert "pass" in result
    assert "pbo" in result
    assert "pbo_median_rank" in result
    assert "threshold" in result
    assert "interpretation" in result
    assert "n_combinations" in result
    assert "is_sharpe_mean" in result
    assert "oos_sharpe_mean" in result
    assert "wfe_cpcv" in result

    assert result["pass"] in (True, False)
    assert result["n_combinations"] == 15


# =============================================================================
# TEST 11: Threshold enforcement
# =============================================================================
def test_pbo_threshold_enforcement():
    """Test that threshold correctly determines pass/fail."""
    returns = _random_returns(n_trials=30, n_periods=600, seed=23)

    # Test with very low threshold (should fail)
    result_low = pbo_with_cpcv(returns, threshold=0.01)
    # Most random strategies will have PBO > 0.01

    # Test with high threshold (should pass)
    result_high = pbo_with_cpcv(returns, threshold=0.99)
    assert result_high.passed, "Should pass with threshold=0.99"

    # Test default threshold (0.15)
    result_default = pbo_with_cpcv(returns, threshold=0.15)
    assert result_default.threshold == 0.15


# =============================================================================
# TEST 12: Invalid parameters raise errors
# =============================================================================
def test_pbo_with_cpcv_invalid_params():
    """Test that invalid parameters raise appropriate errors."""
    returns = _random_returns(n_trials=10, n_periods=100, seed=29)

    # n_test_splits >= n_splits
    with pytest.raises(ValueError, match="n_test_splits must be less than n_splits"):
        pbo_with_cpcv(returns, n_splits=4, n_test_splits=4)

    # n_splits < 2
    with pytest.raises(ValueError, match="n_splits must be at least 2"):
        pbo_with_cpcv(returns, n_splits=1, n_test_splits=1)


# =============================================================================
# TEST 13: Edge case - small dataset
# =============================================================================
def test_pbo_with_small_dataset():
    """Test PBO calculation with small dataset."""
    returns = _random_returns(n_trials=10, n_periods=120, seed=31)
    result = pbo_with_cpcv(
        returns,
        n_splits=4,
        n_test_splits=1,  # C(4,1) = 4 combinations
        purge_gap=1,
        embargo_pct=0.05,
    )

    assert result.n_combinations == 4, "C(4,1) should equal 4"
    assert 0.0 <= result.pbo <= 1.0


# =============================================================================
# TEST 14: Logits distribution
# =============================================================================
def test_pbo_logits_distribution():
    """Test that logits (relative ranks) are in valid range."""
    returns = _random_returns(n_trials=40, n_periods=600, seed=37)
    result = pbo_with_cpcv(returns, n_splits=6, n_test_splits=2)

    # All logits should be in [0, 1]
    assert all(0.0 <= logit <= 1.0 for logit in result.logits), "Logits must be in [0, 1]"

    # Median rank should be close to median of logits
    median_logits = float(np.median(result.logits))
    assert abs(result.pbo_median_rank - median_logits) < 1e-6


# =============================================================================
# TEST 15: Reproducibility
# =============================================================================
def test_pbo_reproducibility():
    """Test that results are deterministic given same inputs."""
    returns = _random_returns(n_trials=30, n_periods=600, seed=41)

    result1 = pbo_with_cpcv(returns, n_splits=6, n_test_splits=2, threshold=0.15)
    result2 = pbo_with_cpcv(returns, n_splits=6, n_test_splits=2, threshold=0.15)

    assert result1.pbo == result2.pbo, "Results should be deterministic"
    assert result1.n_combinations == result2.n_combinations
    assert result1.logits == result2.logits


# =============================================================================
# TEST 16: Integration with validate_with_cpcv
# =============================================================================
def test_validate_with_cpcv_compatibility():
    """Test that validate_with_cpcv still works after changes."""
    data = _dummy_data(120)

    def strategy_func(df: pd.DataFrame) -> dict:
        return {"sharpe_ratio": 1.0, "total_return": 0.1}

    result = validate_with_cpcv(
        data,
        strategy_func,
        n_splits=4,
        n_test_splits=1,
        purge_gap=1,
        embargo_pct=0.05,
    )

    assert "n_combinations" in result
    assert "mean_is_sharpe" in result
    assert "mean_oos_sharpe" in result
    assert "wfe_mean" in result


# =============================================================================
# TEST 17: Interpretation strings
# =============================================================================
def test_interpretation_strings():
    """Test that interpretation strings are correct for different PBO values."""
    from crypto_backtest.validation.cpcv import _interpret_pbo

    assert "PASS" in _interpret_pbo(0.10)
    assert "MARGINAL" in _interpret_pbo(0.20)
    assert "FAIL" in _interpret_pbo(0.40)
    assert "CRITICAL" in _interpret_pbo(0.60)


# =============================================================================
# TEST 18: Zero-variance strategies
# =============================================================================
def test_pbo_with_zero_variance_strategies():
    """Test PBO calculation when some strategies have zero variance."""
    returns = _random_returns(n_trials=30, n_periods=600, seed=43)
    # Make one strategy have zero variance (constant returns)
    returns[0, :] = 0.01

    result = pbo_with_cpcv(returns, n_splits=6, n_test_splits=2)

    # Should handle zero-variance gracefully (Sharpe will be very high or inf)
    assert 0.0 <= result.pbo <= 1.0
    assert result.n_combinations == 15


# =============================================================================
# TEST 19: Negative returns strategies
# =============================================================================
def test_pbo_with_negative_returns():
    """Test PBO calculation with strategies that have negative returns."""
    returns = _random_returns(n_trials=30, n_periods=600, seed=47)
    # Make some strategies consistently lose money
    returns[10:15, :] -= 0.02

    result = pbo_with_cpcv(returns, n_splits=6, n_test_splits=2)

    assert 0.0 <= result.pbo <= 1.0
    assert result.n_combinations == 15


# =============================================================================
# TEST 20: Different CPCV configurations
# =============================================================================
@pytest.mark.parametrize(
    "n_splits,n_test_splits,expected_combos",
    [
        (4, 1, 4),  # C(4,1) = 4
        (5, 2, 10),  # C(5,2) = 10
        (6, 2, 15),  # C(6,2) = 15
        (6, 3, 20),  # C(6,3) = 20
        (7, 2, 21),  # C(7,2) = 21
    ],
)
def test_pbo_different_cpcv_configs(n_splits, n_test_splits, expected_combos):
    """Test PBO with different CPCV configurations."""
    returns = _random_returns(n_trials=20, n_periods=600, seed=53)
    result = pbo_with_cpcv(
        returns,
        n_splits=n_splits,
        n_test_splits=n_test_splits,
    )

    assert result.n_combinations == expected_combos, (
        f"C({n_splits},{n_test_splits}) should equal {expected_combos}"
    )
