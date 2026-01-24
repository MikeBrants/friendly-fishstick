import pandas as pd
import pytest

from crypto_backtest.analysis.metrics import compute_metrics, compute_metrics_reference


def _make_equity_from_returns(returns: pd.Series, start: float = 10_000.0) -> pd.Series:
    equity = (1.0 + returns.fillna(0.0)).cumprod() * start
    equity.name = "equity"
    return equity


def test_metrics_reference_matches_empyrical_if_available():
    # Skip if optional dependency is not installed.
    try:
        import empyrical  # noqa: F401
    except Exception:
        pytest.skip("empyrical not installed (install empyrical-reloaded to enable)")

    idx = pd.date_range("2024-01-01", periods=500, freq="h", tz="UTC")
    # Deterministic synthetic returns with some variance and drawdowns.
    base = pd.Series(0.0002, index=idx)
    shock = pd.Series(0.0, index=idx)
    shock.iloc[50:60] = -0.01
    shock.iloc[200:210] = 0.008
    returns = (base + shock).astype(float)

    equity = _make_equity_from_returns(returns)

    ours = compute_metrics(equity, trades=pd.DataFrame())
    ref = compute_metrics_reference(equity)

    # We don't require bit-exact match because implementations may differ in
    # ddof / downside handling. We do require "close enough" sanity agreement.
    assert "sharpe_ratio" in ours and "sharpe_ratio" in ref
    assert "sortino_ratio" in ours and "sortino_ratio" in ref
    assert "max_drawdown" in ours and "max_drawdown" in ref

    assert abs(float(ours["sharpe_ratio"]) - float(ref["sharpe_ratio"])) < 0.25
    assert abs(float(ours["sortino_ratio"]) - float(ref["sortino_ratio"])) < 0.5
    assert abs(float(ours["max_drawdown"]) - float(ref["max_drawdown"])) < 1e-6

