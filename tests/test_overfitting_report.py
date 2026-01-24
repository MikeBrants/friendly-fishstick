import pandas as pd

from crypto_backtest.validation.overfitting import (
    compute_overfitting_report,
    probabilistic_sharpe_ratio,
)


def _equity_from_returns(idx: pd.DatetimeIndex, returns: pd.Series, start: float = 10_000.0) -> pd.Series:
    return (1.0 + returns.fillna(0.0)).cumprod() * start


def test_probabilistic_sharpe_ratio_basic_sanity():
    idx = pd.date_range("2024-01-01", periods=500, freq="h", tz="UTC")
    zero = pd.Series(0.0, index=idx)
    pos = pd.Series(0.0002, index=idx)
    neg = pd.Series(-0.0002, index=idx)

    assert 0.0 <= probabilistic_sharpe_ratio(zero) <= 1.0
    assert probabilistic_sharpe_ratio(pos) > probabilistic_sharpe_ratio(zero)
    assert probabilistic_sharpe_ratio(neg) < probabilistic_sharpe_ratio(zero)


def test_compute_overfitting_report_fields_are_finite():
    idx = pd.date_range("2024-01-01", periods=800, freq="h", tz="UTC")
    # Mildly positive returns with a drawdown block
    r = pd.Series(0.0001, index=idx)
    r.iloc[50:65] = -0.01

    equity = _equity_from_returns(idx, r)
    rep = compute_overfitting_report(equity_curve=equity, n_trials=200)

    assert rep.n > 0
    assert rep.periods_per_year > 0
    assert 0.0 <= rep.psr <= 1.0
    # DSR may be None if n_trials is None; here it must be present and bounded.
    assert rep.dsr is not None
    assert 0.0 <= rep.dsr <= 1.0
    assert rep.sr_star is not None

