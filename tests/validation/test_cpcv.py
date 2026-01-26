import numpy as np
import pandas as pd

from crypto_backtest.validation.cpcv import CombinatorialPurgedKFold, validate_with_cpcv


def _dummy_data(n_rows: int = 120) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "open": np.linspace(1, 2, n_rows),
            "high": np.linspace(1.1, 2.1, n_rows),
            "low": np.linspace(0.9, 1.9, n_rows),
            "close": np.linspace(1, 2, n_rows),
        }
    )


def test_cpcv_split_count():
    cpcv = CombinatorialPurgedKFold(n_splits=6, n_test_splits=2)
    assert cpcv.get_n_splits() == 15


def test_cpcv_no_overlap():
    data = _dummy_data(120)
    cpcv = CombinatorialPurgedKFold(n_splits=6, n_test_splits=2)
    for train_idx, test_idx in cpcv.split(data):
        assert len(set(train_idx) & set(test_idx)) == 0


def test_cpcv_purge_gap_enforced():
    data = _dummy_data(120)
    cpcv = CombinatorialPurgedKFold(n_splits=4, n_test_splits=1, purge_gap=2, embargo_pct=0.0)
    for train_idx, test_idx in cpcv.split(data):
        for t in test_idx:
            assert not np.any(np.abs(train_idx - t) <= 2)


def test_cpcv_embargo_enforced():
    data = _dummy_data(120)
    cpcv = CombinatorialPurgedKFold(n_splits=4, n_test_splits=1, purge_gap=0, embargo_pct=0.1)
    split_size = len(data) // cpcv.n_splits
    embargo_size = int(len(data) * cpcv.embargo_pct)
    for train_idx, test_idx in cpcv.split(data):
        test_start = int(test_idx.min())
        test_end = int(test_idx.max()) + 1
        embargo_start = test_end
        embargo_end = min(test_end + embargo_size, len(data))
        embargo_range = set(range(embargo_start, embargo_end))
        assert not (set(train_idx) & embargo_range)
        assert test_end - test_start == split_size


def test_validate_with_cpcv_returns_keys():
    data = _dummy_data(120)

    def strategy_func(df: pd.DataFrame) -> dict:
        # Minimal metrics for validation
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
