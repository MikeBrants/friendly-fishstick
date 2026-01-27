import numpy as np

from crypto_backtest.validation.worst_case import worst_case_path


def test_worst_case_produces_15_paths():
    returns = np.full((12, 240), 0.01)
    result = worst_case_path(returns, n_splits=6, n_test_splits=2, purge_gap=3, embargo_pct=0.01)

    assert len(result.oos_sharpes) == 15


def test_worst_case_robust_for_stable_positive():
    returns = np.full((12, 240), 0.01)
    result = worst_case_path(returns, n_splits=6, n_test_splits=2, purge_gap=3, embargo_pct=0.01)

    assert result.verdict == "ROBUST"


def test_worst_case_fragile_for_negative_mean():
    returns = np.full((12, 240), -0.01)
    result = worst_case_path(returns, n_splits=6, n_test_splits=2, purge_gap=3, embargo_pct=0.01)

    assert result.verdict == "FRAGILE"
