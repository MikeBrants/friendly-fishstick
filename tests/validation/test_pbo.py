import numpy as np
import pytest

from crypto_backtest.validation.pbo import (
    guard_pbo,
    probability_of_backtest_overfitting,
)


def _random_returns(n_trials: int, n_periods: int, seed: int = 42) -> np.ndarray:
    rng = np.random.default_rng(seed)
    return rng.normal(loc=0.0, scale=0.01, size=(n_trials, n_periods))


def test_pbo_random_returns_reasonable_range():
    returns = _random_returns(n_trials=50, n_periods=320, seed=7)
    result = probability_of_backtest_overfitting(returns, n_splits=8)
    assert 0.2 < result.pbo < 0.8


def test_pbo_perfect_strategy_low_overfit():
    returns = _random_returns(n_trials=50, n_periods=320, seed=11)
    returns[0] += 0.02  # Make trial 0 consistently better.
    result = probability_of_backtest_overfitting(returns, n_splits=8)
    assert result.pbo < 0.3


def test_pbo_invalid_splits():
    returns = _random_returns(n_trials=10, n_periods=32, seed=1)
    try:
        probability_of_backtest_overfitting(returns, n_splits=1)
        assert False, "Expected ValueError for n_splits < 2"
    except ValueError:
        pass
    try:
        probability_of_backtest_overfitting(returns, n_splits=3)
        assert False, "Expected ValueError for odd n_splits"
    except ValueError:
        pass


def test_guard_pbo_shape():
    returns = _random_returns(n_trials=20, n_periods=160, seed=3)
    result = guard_pbo(returns, threshold=0.4, n_splits=8)
    assert result["guard"] == "pbo"
    assert "pbo" in result
    assert "passed" not in result  # guard_pbo uses 'pass'
    assert result["pass"] in (True, False)


def test_pbo_empty_returns_matrix():
    empty_returns = np.empty((0, 0))
    with pytest.raises(ValueError, match="Not enough periods"):
        probability_of_backtest_overfitting(empty_returns, n_splits=4)


def test_pbo_zero_or_negative_splits():
    returns = _random_returns(n_trials=10, n_periods=32, seed=5)
    for n_splits in (0, -4):
        with pytest.raises(ValueError, match="n_splits must be at least 2"):
            probability_of_backtest_overfitting(returns, n_splits=n_splits)


def test_pbo_insufficient_periods():
    returns = _random_returns(n_trials=10, n_periods=8, seed=9)
    with pytest.raises(ValueError, match="Not enough periods"):
        probability_of_backtest_overfitting(returns, n_splits=16)
