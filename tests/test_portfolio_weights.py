import numpy as np
import pandas as pd

from crypto_backtest.portfolio.weights import (
    compute_equal_weights,
    optimize_max_sharpe,
    optimize_risk_parity,
    optimize_min_cvar,
)


def _make_returns_df(n_days: int = 250, n_assets: int = 5) -> pd.DataFrame:
    rng = np.random.default_rng(123)
    idx = pd.date_range("2024-01-01", periods=n_days, freq="D", tz="UTC")
    # Create slightly different drifts/vols per asset
    cols = {}
    for i in range(n_assets):
        drift = 0.0002 + i * 0.00002
        vol = 0.01 + i * 0.002
        cols[f"A{i}"] = drift + rng.normal(0, vol, size=n_days)
    return pd.DataFrame(cols, index=idx)


def _assert_weights_ok(w: np.ndarray, n: int, min_w: float, max_w: float):
    assert len(w) == n
    assert np.isfinite(w).all()
    assert abs(float(np.sum(w)) - 1.0) < 1e-8
    assert (w >= min_w - 1e-10).all()
    assert (w <= max_w + 1e-10).all()


def test_equal_weights_with_bounds():
    w = compute_equal_weights(5, min_w=0.05, max_w=0.5)
    _assert_weights_ok(w, 5, 0.05, 0.5)


def test_optimize_max_sharpe_bounds():
    df = _make_returns_df()
    w = optimize_max_sharpe(df, min_w=0.05, max_w=0.5)
    _assert_weights_ok(w, df.shape[1], 0.05, 0.5)


def test_optimize_risk_parity_bounds():
    df = _make_returns_df()
    w = optimize_risk_parity(df, min_w=0.05, max_w=0.5)
    _assert_weights_ok(w, df.shape[1], 0.05, 0.5)


def test_optimize_min_cvar_bounds():
    df = _make_returns_df()
    w = optimize_min_cvar(df, alpha=0.05, min_w=0.05, max_w=0.5)
    _assert_weights_ok(w, df.shape[1], 0.05, 0.5)

