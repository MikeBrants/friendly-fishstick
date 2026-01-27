"""Multi-period validation using rolling IS→OOS windows."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class MultiPeriodResult:
    n_windows: int
    consistency_ratio: float
    verdict: str
    oos_sharpes: List[float]


def _sharpe(returns: pd.Series, periods_per_year: float = 252.0) -> float:
    if returns.empty:
        return 0.0
    mean_ret = float(returns.mean())
    std_ret = float(returns.std(ddof=0))
    if std_ret == 0.0:
        return 0.0
    return mean_ret / std_ret * np.sqrt(periods_per_year)


def _generate_windows(
    returns: pd.Series,
    n_windows: int = 34,
    is_ratio: float = 0.7,
) -> List[Tuple[pd.Series, pd.Series]]:
    if n_windows <= 0:
        raise ValueError("n_windows must be positive")
    if not 0.0 < is_ratio < 1.0:
        raise ValueError("is_ratio must be between 0 and 1")

    total_len = len(returns)
    window_size = total_len // n_windows
    if window_size < 2:
        raise ValueError("Not enough data to build requested windows")

    is_len = int(window_size * is_ratio)
    if is_len < 1:
        is_len = 1
    oos_len = window_size - is_len
    if oos_len < 1:
        oos_len = 1
        is_len = window_size - oos_len

    windows: List[Tuple[pd.Series, pd.Series]] = []
    for i in range(n_windows):
        start = i * window_size
        end = start + window_size
        if end > total_len:
            break
        is_slice = returns.iloc[start : start + is_len]
        oos_slice = returns.iloc[start + is_len : end]
        windows.append((is_slice, oos_slice))

    if len(windows) != n_windows:
        raise ValueError("Insufficient data to build all windows")

    return windows


def classify_consistency(consistency_ratio: float) -> str:
    if consistency_ratio > 0.80:
        return "ROBUST"
    if consistency_ratio >= 0.60:
        return "REGIME-DEPENDENT"
    return "FRAGILE"


def evaluate_multi_period(
    returns: pd.Series,
    n_windows: int = 34,
    is_ratio: float = 0.7,
) -> MultiPeriodResult:
    returns = returns.dropna()
    windows = _generate_windows(returns, n_windows=n_windows, is_ratio=is_ratio)

    oos_sharpes = []
    for _, oos_slice in windows:
        oos_sharpes.append(_sharpe(oos_slice))

    n_positive = sum(1 for s in oos_sharpes if s > 0.0)
    consistency_ratio = n_positive / n_windows if n_windows > 0 else 0.0
    verdict = classify_consistency(consistency_ratio)

    return MultiPeriodResult(
        n_windows=n_windows,
        consistency_ratio=consistency_ratio,
        verdict=verdict,
        oos_sharpes=oos_sharpes,
    )
