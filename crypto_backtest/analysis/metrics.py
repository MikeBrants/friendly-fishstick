"""Performance metrics computation."""

from __future__ import annotations

import numpy as np
import pandas as pd
from typing import Any


def _safe_float(value, default: float = 0.0) -> float:
    """Convert any value to safe float, handling complex numbers."""
    if value is None:
        return default
    try:
        # Handle complex numbers explicitly
        if isinstance(value, (complex, np.complexfloating)):
            return float(np.real(value))
        # Handle numpy arrays/scalars
        if hasattr(value, 'item'):
            value = value.item()
        if isinstance(value, (complex, np.complexfloating)):
            return float(np.real(value))
        result = float(value)
        if not np.isfinite(result):
            return default
        return result
    except (TypeError, ValueError, OverflowError):
        return default


def _force_real_series(s: pd.Series) -> pd.Series:
    """Force a pandas Series to contain only real values."""
    if s.empty:
        return s
    if s.apply(lambda x: isinstance(x, (complex, np.complexfloating))).any():
        return s.apply(lambda x: np.real(x) if isinstance(x, (complex, np.complexfloating)) else x).astype(float)
    return s.astype(float)


def _safe_std(series: pd.Series, ddof: int = 0) -> float:
    """Calculate std with protection against complex results."""
    if series.empty or len(series) < 2:
        return 0.0
    try:
        # Force real values first
        series = _force_real_series(series)
        result = series.std(ddof=ddof)
        # Handle complex result from pandas bug
        if isinstance(result, (complex, np.complexfloating)):
            result = np.real(result)
        result = float(result)
        if not np.isfinite(result) or result < 0:
            return 0.0
        return result
    except Exception:
        return 0.0


def compute_metrics(equity_curve: pd.Series, trades: pd.DataFrame) -> dict[str, float]:
    """Compute performance metrics from equity and trades."""
    if equity_curve.empty:
        return {}

    equity = equity_curve.dropna()
    
    # FIX V6: Force equity to real values at the start
    equity = _force_real_series(equity)
    
    start = _safe_float(equity.iloc[0], default=1.0)
    end = _safe_float(equity.iloc[-1], default=1.0)
    
    # Protect against division by zero
    if start == 0:
        start = 1.0
    total_return = (end / start) - 1.0

    years = _years_between(equity.index)
    if years > 0 and start > 0:
        cagr = (end / start) ** (1 / years) - 1.0
    else:
        cagr = 0.0
    cagr = _safe_float(cagr)

    returns = equity.pct_change().dropna()
    
    # FIX V6: Force returns to real values
    returns = _force_real_series(returns)
    
    periods_per_year = _periods_per_year(equity.index)
    periods_per_year = _safe_float(periods_per_year, default=252.0)
    if periods_per_year <= 0:
        periods_per_year = 252.0
    
    # FIX V6: Use safe std calculation
    std_returns = _safe_std(returns, ddof=0)
    mean_returns = _safe_float(returns.mean())
    
    # Calculate Sharpe with full protection
    if std_returns > 0:
        sharpe = _safe_float(mean_returns / std_returns) * np.sqrt(periods_per_year)
    else:
        sharpe = 0.0
    sharpe = _safe_float(sharpe)
    
    # Sortino calculation with protection
    downside = returns[returns < 0]
    std_downside = _safe_std(downside, ddof=0)
    
    if std_downside > 0:
        sortino = _safe_float(mean_returns / std_downside) * np.sqrt(periods_per_year)
    else:
        sortino = 0.0
    sortino = _safe_float(sortino)

    drawdown, max_drawdown, max_drawdown_duration = _max_drawdown(equity)
    max_drawdown = _safe_float(max_drawdown)
    
    if max_drawdown != 0:
        calmar = _ratio(cagr, abs(max_drawdown))
    else:
        calmar = 0.0
    calmar = _safe_float(calmar)

    pnl_series = _trade_pnl(trades)
    win_rate = _safe_float(_win_rate(pnl_series))
    profit_factor = _safe_float(_profit_factor(pnl_series))
    expectancy = _safe_float(pnl_series.mean()) if not pnl_series.empty else 0.0

    var_95 = _safe_float(returns.quantile(0.05)) if not returns.empty else 0.0
    cvar_95 = _safe_float(returns[returns <= var_95].mean()) if not returns.empty else 0.0

    hour_blocks = _hour_block_stats(returns)
    weekday_stats = _weekday_stats(returns)

    return {
        "total_return": _safe_float(total_return),
        "cagr": _safe_float(cagr),
        "sharpe_ratio": sharpe,
        "sortino_ratio": sortino,
        "calmar_ratio": calmar,
        "max_drawdown": max_drawdown,
        "max_drawdown_duration": _safe_float(max_drawdown_duration),
        "win_rate": win_rate,
        "profit_factor": profit_factor,
        "expectancy": expectancy,
        "var_95": var_95,
        "cvar_95": cvar_95,
        "hour_block_avg_return": hour_blocks,
        "weekday_avg_return": weekday_stats,
    }


# =============================================================================
# Optional reference implementation (empyrical-reloaded)
# =============================================================================

def _import_empyrical():
    """
    Import empyrical (optionally provided by the package 'empyrical-reloaded').

    We keep this optional so the core backtesting stack does not hard-depend
    on empyrical. Tests should skip if missing.
    """
    try:
        import empyrical as emp  # type: ignore
    except Exception as exc:  # pragma: no cover
        raise ImportError(
            "empyrical not installed. Install 'empyrical-reloaded' to enable "
            "metrics reference cross-check."
        ) from exc
    return emp


def compute_metrics_reference(
    equity_curve: pd.Series,
    risk_free: float = 0.0,
) -> dict[str, float]:
    """
    Compute a subset of metrics using a well-known reference library (empyrical).

    This is intended for *sanity checking* only (e.g. CI/test comparisons),
    not as the primary metrics source.

    Returns values in the same units as `compute_metrics()`:
    - total_return, cagr, max_drawdown are fractions (e.g. 0.10 = +10%)
    - sharpe_ratio and sortino_ratio are annualized
    """
    if equity_curve is None or equity_curve.empty:
        return {}

    emp = _import_empyrical()

    equity = equity_curve.dropna()
    equity = _force_real_series(equity)

    start = _safe_float(equity.iloc[0], default=1.0)
    end = _safe_float(equity.iloc[-1], default=1.0)
    if start == 0:
        start = 1.0

    total_return = (end / start) - 1.0
    years = _years_between(equity.index)
    if years > 0 and start > 0:
        cagr = (end / start) ** (1 / years) - 1.0
    else:
        cagr = 0.0

    returns = equity.pct_change().dropna()
    returns = _force_real_series(returns)

    periods_per_year = _periods_per_year(equity.index)
    periods_per_year = _safe_float(periods_per_year, default=252.0)
    if periods_per_year <= 0:
        periods_per_year = 252.0

    # Empyrical expects returns, not equity.
    sharpe = emp.sharpe_ratio(returns, risk_free=risk_free, annualization=periods_per_year)
    sortino = emp.sortino_ratio(returns, required_return=risk_free, annualization=periods_per_year)
    max_dd = emp.max_drawdown(returns)

    # empyrical may return numpy scalars; force safe floats.
    return {
        "total_return": _safe_float(total_return),
        "cagr": _safe_float(cagr),
        "sharpe_ratio": _safe_float(sharpe),
        "sortino_ratio": _safe_float(sortino),
        "max_drawdown": _safe_float(max_dd),
    }


def diff_metrics(
    ours: dict[str, Any],
    reference: dict[str, Any],
    keys: list[str] | None = None,
) -> dict[str, float]:
    """
    Convenience helper to compute per-metric deltas (ours - reference).
    Missing keys are ignored.
    """
    if keys is None:
        keys = sorted(set(ours.keys()) & set(reference.keys()))
    out: dict[str, float] = {}
    for k in keys:
        if k in ours and k in reference:
            out[k] = _safe_float(ours.get(k)) - _safe_float(reference.get(k))
    return out


def _trade_pnl(trades: pd.DataFrame) -> pd.Series:
    """Return PnL aggregated by signal (entry_time), not by leg."""
    if trades is None or trades.empty:
        return pd.Series(dtype=float)

    # Determine PnL column
    if "pnl" in trades.columns:
        pnl_col = "pnl"
    elif "net_pnl" in trades.columns:
        pnl_col = "net_pnl"
    elif "gross_pnl" in trades.columns:
        pnl_col = "gross_pnl"
    else:
        return pd.Series(dtype=float)

    # Group by entry_time to count by signal (not by leg)
    if "entry_time" in trades.columns:
        return trades.groupby("entry_time")[pnl_col].sum().astype(float)

    return trades[pnl_col].astype(float)


def _ratio(numerator: float, denominator: float) -> float:
    if denominator == 0 or pd.isna(denominator):
        return 0.0
    return float(numerator / denominator)


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
        return pd.Timedelta(days=365.25) / delta
    delta = (index[1:] - index[:-1]).median()
    if delta <= pd.Timedelta(0):
        return 252.0
    
    result = pd.Timedelta(days=365.25) / delta
    # FIX: Protection contre valeurs invalides
    if pd.isna(result) or result <= 0 or result == float('inf'):
        return 252.0
    return float(result)


def _years_between(index: pd.Index) -> float:
    if not isinstance(index, pd.DatetimeIndex) or len(index) < 2:
        return 0.0
    delta = index[-1] - index[0]
    return delta.total_seconds() / (365.25 * 24 * 3600)


def _max_drawdown(equity: pd.Series) -> tuple[pd.Series, float, int]:
    hwm = equity.cummax()
    drawdown = equity / hwm - 1.0
    max_drawdown = float(drawdown.min()) if not drawdown.empty else 0.0

    underwater = drawdown < 0
    max_duration = 0
    current = 0
    for is_under in underwater:
        if is_under:
            current += 1
            max_duration = max(max_duration, current)
        else:
            current = 0
    return drawdown, max_drawdown, max_duration


def _win_rate(pnl: pd.Series) -> float:
    if pnl.empty:
        return 0.0
    return float((pnl > 0).mean())


def _profit_factor(pnl: pd.Series) -> float:
    if pnl.empty:
        return 0.0
    gains = pnl[pnl > 0].sum()
    losses = pnl[pnl < 0].sum()
    if losses == 0:
        return float("inf") if gains > 0 else 0.0
    return float(gains / abs(losses))


def _hour_block_stats(returns: pd.Series) -> dict[str, float]:
    if returns.empty or not isinstance(returns.index, pd.DatetimeIndex):
        return {}
    blocks = (returns.index.hour // 4) * 4
    stats = returns.groupby(blocks).mean()
    return {f"{int(block):02d}-{int(block)+3:02d}": float(val) for block, val in stats.items()}


def _weekday_stats(returns: pd.Series) -> dict[str, float]:
    if returns.empty or not isinstance(returns.index, pd.DatetimeIndex):
        return {}
    stats = returns.groupby(returns.index.dayofweek).mean()
    return {str(int(day)): float(val) for day, val in stats.items()}
