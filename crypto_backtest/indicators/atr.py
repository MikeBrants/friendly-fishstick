"""ATR indicator implementation."""

from __future__ import annotations

import pandas as pd


def compute_atr(high: pd.Series, low: pd.Series, close: pd.Series, length: int = 14) -> pd.Series:
    """Compute ATR using Wilder's smoothing."""
    if length < 1:
        raise ValueError("length must be >= 1")
    prev_close = close.shift(1)
    true_range = pd.concat(
        [
            high - low,
            (high - prev_close).abs(),
            (low - prev_close).abs(),
        ],
        axis=1,
    ).max(axis=1)
    return true_range.ewm(alpha=1 / length, adjust=False).mean()
