import numpy as np
import pytest

from crypto_backtest.validation.pbo_cscv import CSCVConfig, cscv_pbo, guard_pbo_cscv


def _random_returns(n_trials: int, n_periods: int, seed: int = 42) -> np.ndarray:
    rng = np.random.default_rng(seed)
    return rng.normal(loc=0.0, scale=0.01, size=(n_trials, n_periods))


def test_cscv_pbo_random_returns_probability_range():
    returns = _random_returns(n_trials=20, n_periods=400, seed=7)
    config = CSCVConfig(n_folds=4, min_bars_per_fold=50, purge_gap=0)
    result = cscv_pbo(returns, config=config)
    assert 0.0 <= result["pbo"] <= 1.0


def test_cscv_pbo_with_strong_winner_has_valid_output():
    returns = _random_returns(n_trials=20, n_periods=400, seed=11)
    returns[0] += 0.02  # Make trial 0 consistently better.
    config = CSCVConfig(n_folds=4, min_bars_per_fold=50, purge_gap=0)
    result = cscv_pbo(returns, config=config)
    assert 0.0 <= result["pbo"] <= 1.0


def test_cscv_pbo_invalid_folds():
    returns = _random_returns(n_trials=2, n_periods=40, seed=1)
    config = CSCVConfig(n_folds=3, min_bars_per_fold=5, purge_gap=0)
    with pytest.raises(ValueError, match="n_folds must be even"):
        cscv_pbo(returns, config=config)


def test_guard_pbo_cscv_shape():
    returns = _random_returns(n_trials=10, n_periods=2000, seed=3)
    result = guard_pbo_cscv(returns, threshold=0.4, n_splits=4)
    assert "pbo" in result
    assert "pass" in result
    assert "n_paths" in result
    assert "method" in result


def test_cscv_pbo_empty_returns_matrix():
    empty_returns = np.empty((0, 0))
    config = CSCVConfig(n_folds=4, min_bars_per_fold=5, purge_gap=0)
    with pytest.raises(ValueError, match="Need at least 2 trials"):
        cscv_pbo(empty_returns, config=config)


def test_cscv_pbo_insufficient_bars():
    returns = _random_returns(n_trials=10, n_periods=100, seed=9)
    config = CSCVConfig(n_folds=4, min_bars_per_fold=50, purge_gap=0)
    with pytest.raises(ValueError, match="Insufficient data"):
        cscv_pbo(returns, config=config)
