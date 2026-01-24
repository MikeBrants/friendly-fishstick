"""
Portfolio weight optimizers (bounded simplex).

Kept independent from the backtest engine: consumes only a returns DataFrame.
"""

from __future__ import annotations

from typing import Callable

import numpy as np
import pandas as pd
from scipy.optimize import minimize


def _check_bounds(n: int, min_w: float, max_w: float) -> None:
    if n <= 0:
        raise ValueError("n must be > 0")
    if min_w < 0 or max_w < 0 or max_w < min_w:
        raise ValueError("Invalid bounds")
    if n * min_w - 1.0 > 1e-12:
        raise ValueError("Infeasible bounds: n*min_w > 1")
    if n * max_w + 1e-12 < 1.0:
        raise ValueError("Infeasible bounds: n*max_w < 1")


def project_to_bounded_simplex(w: np.ndarray, min_w: float, max_w: float, tol: float = 1e-10) -> np.ndarray:
    """
    Project weights onto simplex with bounds:
    - sum(w) = 1
    - min_w <= w_i <= max_w

    Uses a simple iterative redistribution (sufficient for small N portfolios).
    """
    w = np.asarray(w, dtype=float)
    n = len(w)
    _check_bounds(n, min_w, max_w)

    w = np.clip(w, min_w, max_w)
    for _ in range(10_000):
        s = float(w.sum())
        diff = s - 1.0
        if abs(diff) <= tol:
            break
        if diff > 0:
            # Need to remove weight from those above min.
            idx = np.where(w > min_w + 1e-15)[0]
            if len(idx) == 0:
                break
            room = w[idx] - min_w
            room_sum = float(room.sum())
            if room_sum <= 0:
                break
            w[idx] -= diff * (room / room_sum)
            w = np.clip(w, min_w, max_w)
        else:
            # Need to add weight to those below max.
            idx = np.where(w < max_w - 1e-15)[0]
            if len(idx) == 0:
                break
            room = max_w - w[idx]
            room_sum = float(room.sum())
            if room_sum <= 0:
                break
            w[idx] += (-diff) * (room / room_sum)
            w = np.clip(w, min_w, max_w)

    # Final normalize (small drift).
    w = np.clip(w, min_w, max_w)
    s = float(w.sum())
    if s == 0:
        return np.full(n, 1.0 / n)
    w = w / s
    # Ensure within bounds after normalize (may slightly violate due to division).
    w = np.clip(w, min_w, max_w)
    w = w / float(w.sum())
    return w


def compute_equal_weights(n: int, min_w: float = 0.0, max_w: float = 1.0) -> np.ndarray:
    _check_bounds(n, min_w, max_w)
    w0 = np.full(n, 1.0 / n)
    return project_to_bounded_simplex(w0, min_w=min_w, max_w=max_w)


def _optimize(
    returns_df: pd.DataFrame,
    objective: Callable[[np.ndarray], float],
    min_w: float,
    max_w: float,
) -> np.ndarray:
    if returns_df.empty or returns_df.shape[1] == 0:
        return np.array([])
    n = returns_df.shape[1]
    _check_bounds(n, min_w, max_w)

    bounds = [(min_w, max_w)] * n
    constraints = [{"type": "eq", "fun": lambda w: float(np.sum(w) - 1.0)}]
    x0 = compute_equal_weights(n, min_w=min_w, max_w=max_w)

    res = minimize(objective, x0, method="SLSQP", bounds=bounds, constraints=constraints)
    if not res.success or res.x is None:
        return x0
    return project_to_bounded_simplex(res.x, min_w=min_w, max_w=max_w)


def optimize_max_sharpe(returns_df: pd.DataFrame, min_w: float = 0.0, max_w: float = 1.0) -> np.ndarray:
    r = returns_df.to_numpy(dtype=float)

    def neg_sharpe(w: np.ndarray) -> float:
        pr = r @ w
        vol = float(np.std(pr, ddof=0))
        if vol <= 0:
            return 0.0
        return -float(np.mean(pr) / vol)

    return _optimize(returns_df, neg_sharpe, min_w=min_w, max_w=max_w)


def optimize_risk_parity(returns_df: pd.DataFrame, min_w: float = 0.0, max_w: float = 1.0) -> np.ndarray:
    r = returns_df.to_numpy(dtype=float)
    cov = np.cov(r, rowvar=False, ddof=0)
    cov = np.asarray(cov, dtype=float)
    n = cov.shape[0]
    if n == 0:
        return np.array([])
    target_rc = np.full(n, 1.0 / n)

    def rp_objective(w: np.ndarray) -> float:
        w = np.asarray(w, dtype=float)
        port_var = float(w.T @ cov @ w)
        if port_var <= 0:
            return 1e6
        mrc = cov @ w  # marginal risk contribution (unnormalized)
        rc = (w * mrc) / port_var
        return float(np.sum((rc - target_rc) ** 2))

    return _optimize(returns_df, rp_objective, min_w=min_w, max_w=max_w)


def optimize_min_cvar(
    returns_df: pd.DataFrame,
    alpha: float = 0.05,
    min_w: float = 0.0,
    max_w: float = 1.0,
) -> np.ndarray:
    """
    Minimize historical CVaR (expected shortfall) of portfolio *losses*.
    """
    r = returns_df.to_numpy(dtype=float)

    def cvar_objective(w: np.ndarray) -> float:
        pr = r @ w
        losses = -pr
        var = float(np.quantile(losses, 1.0 - alpha))
        tail = losses[losses >= var]
        if len(tail) == 0:
            return 0.0
        return float(np.mean(tail))

    return _optimize(returns_df, cvar_objective, min_w=min_w, max_w=max_w)

