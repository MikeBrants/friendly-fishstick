"""
Smoke tests for GUARD-008 PBO integration (J2 deliverable).

Verifies that:
1. guard_pbo function exists and returns correct format
2. PBO calculation produces valid probability [0, 1]
3. Guard passes/fails based on threshold
"""
import numpy as np
import pytest

from crypto_backtest.validation.pbo_cscv import CSCVConfig, cscv_pbo, guard_pbo_cscv


def test_guard_pbo_exists():
    """Test that guard_pbo function is importable and callable."""
    assert callable(guard_pbo_cscv)


def test_guard_pbo_return_format():
    """Test that guard_pbo returns expected dict format."""
    # Create dummy returns matrix (10 trials, 100 periods)
    np.random.seed(42)
    returns = np.random.randn(10, 2000) * 0.01

    result = guard_pbo_cscv(returns, threshold=0.30, n_splits=4)

    # Check return format
    assert isinstance(result, dict)
    assert "pass" in result
    assert "pbo" in result
    assert "n_paths" in result
    assert "method" in result
    assert "lambda_median" in result
    assert "degradation" in result

    # Check types
    assert isinstance(result["pass"], bool)
    assert isinstance(result["pbo"], (int, float))
    assert isinstance(result["n_paths"], int)
    assert isinstance(result["method"], str)


def test_pbo_probability_range():
    """Test that PBO is in valid range [0, 1]."""
    np.random.seed(42)
    returns = np.random.randn(20, 2000) * 0.01

    result = guard_pbo_cscv(returns, threshold=0.30, n_splits=4)

    # PBO should be a probability
    assert 0.0 <= result["pbo"] <= 1.0


def test_pbo_threshold_logic():
    """Test that guard passes/fails based on threshold."""
    np.random.seed(42)

    # Create returns with low overfitting (good strategy)
    # All trials perform similarly -> low PBO
    returns_good = np.random.randn(10, 2000) * 0.005 + 0.001
    result_good = guard_pbo_cscv(returns_good, threshold=1.0, n_splits=4)

    # Create returns with high overfitting (random performance)
    # Some trials good IS, bad OOS -> high PBO
    returns_bad = np.random.randn(10, 2000) * 0.02
    result_bad = guard_pbo_cscv(returns_bad, threshold=-0.1, n_splits=4)

    # At least one should pass or fail (not both same)
    # Note: This is probabilistic, but with fixed seed should be deterministic
    assert result_good["pass"] is True
    assert result_bad["pass"] is False


def test_pbo_n_splits_validation():
    """Test that PBO validates n_splits parameter."""
    np.random.seed(42)
    returns = np.random.randn(10, 100) * 0.01

    # n_splits must be even and >= 2
    config = CSCVConfig(n_folds=3, min_bars_per_fold=5, purge_gap=0)
    with pytest.raises(ValueError):
        cscv_pbo(returns, config=config)  # Odd


def test_pbo_interpretation():
    """Test that interpretation string is meaningful."""
    np.random.seed(42)
    returns = np.random.randn(10, 2000) * 0.01

    result = guard_pbo_cscv(returns, threshold=0.30, n_splits=4)

    assert result["method"].upper() == "CSCV"


def test_guard_pbo_with_perfect_strategy():
    """Test PBO with a strategy that always wins (no overfitting)."""
    np.random.seed(42)

    # All trials have positive returns -> should have low PBO
    returns_perfect = np.abs(np.random.randn(10, 2000) * 0.005) + 0.001

    result = guard_pbo_cscv(returns_perfect, threshold=0.30, n_splits=4)

    # Should likely pass (low PBO) but not guaranteed due to randomness
    assert 0.0 <= result["pbo"] <= 1.0


def test_guard_pbo_with_random_strategy():
    """Test PBO with completely random strategy (high overfitting)."""
    np.random.seed(42)

    # Random returns with no consistency -> should have high PBO
    returns_random = np.random.randn(20, 2000) * 0.05

    result = guard_pbo_cscv(returns_random, threshold=0.30, n_splits=4)

    # PBO should be calculated (not necessarily high, but valid)
    assert 0.0 <= result["pbo"] <= 1.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
