"""Performance metrics computation."""

from __future__ import annotations

import pandas as pd


def compute_metrics(equity_curve: pd.Series, trades: pd.DataFrame) -> dict[str, float]:
    """Compute performance metrics from equity and trades."""
    if equity_curve.empty:
        return {}

    equity = equity_curve.dropna()
    start = float(equity.iloc[0])
    end = float(equity.iloc[-1])
    total_return = 0.0 if start == 0 else (end / start) - 1.0

    years = _years_between(equity.index)
    cagr = (end / start) ** (1 / years) - 1.0 if years > 0 and start > 0 else 0.0

    returns = equity.pct_change().dropna()
    periods_per_year = _periods_per_year(equity.index)
    sharpe = _ratio(returns.mean(), returns.std(ddof=0)) * (periods_per_year**0.5)
    downside = returns[returns < 0]
    sortino = _ratio(returns.mean(), downside.std(ddof=0)) * (periods_per_year**0.5)

    drawdown, max_drawdown, max_drawdown_duration = _max_drawdown(equity)
    calmar = _ratio(cagr, abs(max_drawdown)) if max_drawdown != 0 else 0.0

    pnl_series = _trade_pnl(trades)
    win_rate = _win_rate(pnl_series)
    profit_factor = _profit_factor(pnl_series)
    expectancy = float(pnl_series.mean()) if not pnl_series.empty else 0.0

    var_95 = returns.quantile(0.05) if not returns.empty else 0.0
    cvar_95 = returns[returns <= var_95].mean() if not returns.empty else 0.0

    hour_blocks = _hour_block_stats(returns)
    weekday_stats = _weekday_stats(returns)

    return {
        "total_return": total_return,
        "cagr": cagr,
        "sharpe_ratio": sharpe,
        "sortino_ratio": sortino,
        "calmar_ratio": calmar,
        "max_drawdown": max_drawdown,
        "max_drawdown_duration": float(max_drawdown_duration),
        "win_rate": win_rate,
        "profit_factor": profit_factor,
        "expectancy": expectancy,
        "var_95": float(var_95) if pd.notna(var_95) else 0.0,
        "cvar_95": float(cvar_95) if pd.notna(cvar_95) else 0.0,
        "hour_block_avg_return": hour_blocks,
        "weekday_avg_return": weekday_stats,
    }


def _trade_pnl(trades: pd.DataFrame) -> pd.Series:
    if trades is None or trades.empty:
        return pd.Series(dtype=float)
    if "pnl" in trades.columns:
        return trades["pnl"].astype(float)
    if "net_pnl" in trades.columns:
        return trades["net_pnl"].astype(float)
    return trades.get("gross_pnl", pd.Series(dtype=float)).astype(float)


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
    return pd.Timedelta(days=365.25) / delta


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
