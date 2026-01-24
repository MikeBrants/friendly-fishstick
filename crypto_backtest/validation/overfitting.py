"""
Overfitting diagnostics (report-only).

Implements Probabilistic Sharpe Ratio (PSR) and an approximate Deflated Sharpe
Ratio (DSR) following Bailey & López de Prado style adjustments.

This module is designed to be:
- deterministic (no RNG)
- safe (no NaN/inf/complex propagation)
- lightweight (used as an informational guard; not enforced by default)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import math
import numpy as np
import pandas as pd


def _safe_float(value: Any, default: float = 0.0) -> float:
    if value is None:
        return default
    try:
        if isinstance(value, (complex, np.complexfloating)):
            value = np.real(value)
        if hasattr(value, "item"):
            value = value.item()
        result = float(value)
        if not np.isfinite(result):
            return default
        return result
    except Exception:
        return default


def _force_real_series(s: pd.Series) -> pd.Series:
    if s is None:
        return pd.Series(dtype=float)
    if s.empty:
        return s.astype(float)
    if np.iscomplexobj(s.to_numpy()):
        return pd.Series(np.real(s.to_numpy()), index=s.index, name=s.name).astype(float)
    return s.astype(float)


def _periods_per_year(index: pd.Index) -> float:
    if not isinstance(index, pd.DatetimeIndex) or len(index) < 2:
        return 252.0
    freq = pd.infer_freq(index)
    if freq:
        offset = pd.tseries.frequencies.to_offset(freq)
        try:
            delta = offset.as_timedelta()
        except AttributeError:
            delta = pd.Timedelta(offset.nanos, unit="ns")
        denom = _safe_float(pd.Timedelta(days=365.25) / delta, 252.0)
        return denom if denom > 0 else 252.0
    delta = (index[1:] - index[:-1]).median()
    if delta <= pd.Timedelta(0):
        return 252.0
    denom = _safe_float(pd.Timedelta(days=365.25) / delta, 252.0)
    return denom if denom > 0 else 252.0


def _norm_cdf(x: float) -> float:
    """Normal CDF without scipy dependency."""
    # Abramowitz-Stegun approximation via erf.
    return 0.5 * (1.0 + float(math.erf(x / np.sqrt(2.0))))


def _norm_ppf(p: float) -> float:
    """Normal inverse CDF; uses scipy if available, else approximation."""
    try:
        from scipy.stats import norm  # type: ignore

        return _safe_float(norm.ppf(p), 0.0)
    except Exception:
        # Acklam approximation (good enough for our report-only usage).
        # Source: Peter J. Acklam, 2003
        if p <= 0.0:
            return -np.inf
        if p >= 1.0:
            return np.inf
        a = [
            -3.969683028665376e01,
            2.209460984245205e02,
            -2.759285104469687e02,
            1.383577518672690e02,
            -3.066479806614716e01,
            2.506628277459239e00,
        ]
        b = [
            -5.447609879822406e01,
            1.615858368580409e02,
            -1.556989798598866e02,
            6.680131188771972e01,
            -1.328068155288572e01,
        ]
        c = [
            -7.784894002430293e-03,
            -3.223964580411365e-01,
            -2.400758277161838e00,
            -2.549732539343734e00,
            4.374664141464968e00,
            2.938163982698783e00,
        ]
        d = [
            7.784695709041462e-03,
            3.224671290700398e-01,
            2.445134137142996e00,
            3.754408661907416e00,
        ]
        plow = 0.02425
        phigh = 1 - plow
        if p < plow:
            q = np.sqrt(-2 * np.log(p))
            num = (((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5])
            den = ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1)
            return float(num / den)
        if p > phigh:
            q = np.sqrt(-2 * np.log(1 - p))
            num = (((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5])
            den = ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1)
            return float(-(num / den))
        q = p - 0.5
        r = q * q
        num = (((((a[0] * r + a[1]) * r + a[2]) * r + a[3]) * r + a[4]) * r + a[5]) * q
        den = (((((b[0] * r + b[1]) * r + b[2]) * r + b[3]) * r + b[4]) * r + 1)
        return float(num / den)


def _skew_kurtosis(x: np.ndarray) -> tuple[float, float]:
    """Return (skewness, kurtosis) with kurtosis as non-excess (normal=3)."""
    x = x[np.isfinite(x)]
    if len(x) < 4:
        return 0.0, 3.0
    try:
        from scipy.stats import skew as sp_skew, kurtosis as sp_kurtosis  # type: ignore

        s = _safe_float(sp_skew(x, bias=False), 0.0)
        k = _safe_float(sp_kurtosis(x, fisher=False, bias=False), 3.0)
        if k <= 0:
            k = 3.0
        return s, k
    except Exception:
        # Moment-based fallback (bias not corrected).
        mu = float(np.mean(x))
        sigma = float(np.std(x, ddof=0))
        if sigma <= 0:
            return 0.0, 3.0
        z = (x - mu) / sigma
        s = float(np.mean(z**3))
        k = float(np.mean(z**4))
        return _safe_float(s, 0.0), _safe_float(k, 3.0)


def sharpe_ratio(returns: pd.Series, risk_free: float = 0.0) -> float:
    """Non-annualized Sharpe ratio (per period)."""
    r = _force_real_series(returns).dropna()
    if len(r) < 2:
        return 0.0
    x = r.to_numpy(dtype=float)
    mu = float(np.mean(x) - risk_free)
    sigma = float(np.std(x, ddof=1))
    if sigma <= 0 or not np.isfinite(sigma):
        return 0.0
    return _safe_float(mu / sigma, 0.0)


def probabilistic_sharpe_ratio(
    returns: pd.Series,
    sr_benchmark: float = 0.0,
    risk_free: float = 0.0,
) -> float:
    """
    Probabilistic Sharpe Ratio (PSR): P(SR > SR*) given sampling uncertainty.

    Returns a probability in [0, 1].
    """
    r = _force_real_series(returns).dropna()
    n = len(r)
    if n < 5:
        return 0.5
    sr_hat = sharpe_ratio(r, risk_free=risk_free)
    x = r.to_numpy(dtype=float)
    s, k = _skew_kurtosis(x)

    # Bailey & López de Prado denominator term.
    denom = 1.0 - s * sr_hat + ((k - 1.0) / 4.0) * (sr_hat**2)
    denom = float(denom)
    if denom <= 0 or not np.isfinite(denom):
        return 0.5

    z = ((sr_hat - sr_benchmark) * np.sqrt(n - 1.0)) / np.sqrt(denom)
    psr = _norm_cdf(_safe_float(z, 0.0))
    # Guard for numerical spill.
    if psr < 0.0:
        psr = 0.0
    if psr > 1.0:
        psr = 1.0
    return float(psr)


@dataclass(frozen=True)
class OverfittingReport:
    n: int
    periods_per_year: float
    sr_period: float
    sr_annualized: float
    psr: float
    dsr: float | None
    sr_star: float | None


def deflated_sharpe_ratio(
    returns: pd.Series,
    sr_benchmark: float = 0.0,
    risk_free: float = 0.0,
    n_trials: int | None = None,
) -> tuple[float | None, float | None]:
    """
    Approximate Deflated Sharpe Ratio (DSR).

    - Computes an adjusted threshold SR* based on number of trials.
    - Returns (dsr, sr_star). If n_trials is None or < 2, returns (None, None).
    """
    if n_trials is None or n_trials < 2:
        return None, None

    r = _force_real_series(returns).dropna()
    n = len(r)
    if n < 5:
        return None, None

    sr_hat = sharpe_ratio(r, risk_free=risk_free)
    x = r.to_numpy(dtype=float)
    s, k = _skew_kurtosis(x)

    denom = 1.0 - s * sr_hat + ((k - 1.0) / 4.0) * (sr_hat**2)
    denom = float(denom)
    if denom <= 0 or not np.isfinite(denom):
        return None, None

    sigma_sr = np.sqrt(denom / (n - 1.0))

    # Expected max Sharpe under multiple testing (approx via extreme quantile).
    p = 1.0 - (1.0 / float(n_trials))
    z = _norm_ppf(p)
    if not np.isfinite(z):
        return None, None
    sr_star = sr_benchmark + _safe_float(sigma_sr) * _safe_float(z)

    dsr = probabilistic_sharpe_ratio(r, sr_benchmark=sr_star, risk_free=risk_free)
    return float(dsr), float(sr_star)


def compute_overfitting_report(
    equity_curve: pd.Series,
    sr_benchmark: float = 0.0,
    risk_free: float = 0.0,
    n_trials: int | None = None,
) -> OverfittingReport:
    """
    Convenience wrapper used by guards runner: derive returns from equity curve.
    """
    equity = _force_real_series(pd.Series(equity_curve).dropna())
    returns = equity.pct_change().dropna()
    returns = _force_real_series(returns)

    ppy = _periods_per_year(equity.index)
    sr_p = sharpe_ratio(returns, risk_free=risk_free)
    sr_a = _safe_float(sr_p) * float(np.sqrt(ppy))
    psr = probabilistic_sharpe_ratio(returns, sr_benchmark=sr_benchmark, risk_free=risk_free)
    dsr, sr_star = deflated_sharpe_ratio(
        returns, sr_benchmark=sr_benchmark, risk_free=risk_free, n_trials=n_trials
    )
    return OverfittingReport(
        n=int(len(returns)),
        periods_per_year=float(ppy),
        sr_period=float(_safe_float(sr_p)),
        sr_annualized=float(_safe_float(sr_a)),
        psr=float(_safe_float(psr)),
        dsr=float(dsr) if dsr is not None else None,
        sr_star=float(sr_star) if sr_star is not None else None,
    )

