import numpy as np
import pandas as pd
import pytest

from crypto_backtest.validation.multi_period import (
    MultiPeriodResult,
    classify_consistency,
    evaluate_multi_period,
)


def _make_returns(n_windows: int, window_size: int, n_positive: int) -> pd.Series:
    rng = np.random.default_rng(123)
    series = []
    for i in range(n_windows):
        mean = 0.01 if i < n_positive else -0.01
        series.append(rng.normal(loc=mean, scale=0.005, size=window_size))
    return pd.Series(np.concatenate(series))


def test_evaluate_multi_period_robust():
    returns = _make_returns(n_windows=34, window_size=10, n_positive=30)
    result = evaluate_multi_period(returns, n_windows=34, is_ratio=0.7)

    assert isinstance(result, MultiPeriodResult)
    assert result.n_windows == 34
    assert result.consistency_ratio > 0.80
    assert result.verdict == "ROBUST"


def test_evaluate_multi_period_regime_dependent():
    returns = _make_returns(n_windows=34, window_size=10, n_positive=22)
    result = evaluate_multi_period(returns, n_windows=34, is_ratio=0.7)

    assert 0.60 <= result.consistency_ratio <= 0.80
    assert result.verdict == "REGIME-DEPENDENT"


def test_evaluate_multi_period_fragile():
    returns = _make_returns(n_windows=34, window_size=10, n_positive=10)
    result = evaluate_multi_period(returns, n_windows=34, is_ratio=0.7)

    assert result.consistency_ratio < 0.60
    assert result.verdict == "FRAGILE"


def test_evaluate_multi_period_requires_data():
    returns = pd.Series([0.01] * 20)
    with pytest.raises(ValueError):
        evaluate_multi_period(returns, n_windows=34, is_ratio=0.7)
