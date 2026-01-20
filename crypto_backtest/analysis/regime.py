"""Regime classification helpers (no look-ahead)."""

from __future__ import annotations

import pandas as pd

from crypto_backtest.indicators.atr import compute_atr

REGIMES_V2 = ("CRASH", "HIGH_VOL", "BEAR", "BULL", "SIDEWAYS", "RECOVERY", "OTHER")


def classify_regimes_v2(data: pd.DataFrame) -> pd.Series:
    """Classify regimes using shifted rolling data (no look-ahead)."""
    close = data["close"]

    sma_50 = close.rolling(50).mean().shift(1)
    sma_200 = close.rolling(200).mean().shift(1)

    atr_14 = compute_atr(data["high"], data["low"], close, 14)
    atr_current = atr_14.shift(1)
    atr_50 = atr_14.rolling(50).mean().shift(1)

    from_high_50 = (close / close.rolling(50).max().shift(1)) - 1
    from_low_50 = (close / close.rolling(50).min().shift(1)) - 1

    regimes = pd.Series(index=data.index, dtype=object)
    regimes[:] = "OTHER"

    valid = ~(
        sma_50.isna()
        | sma_200.isna()
        | atr_50.isna()
        | atr_current.isna()
        | from_high_50.isna()
        | from_low_50.isna()
    )

    crash = valid & (from_high_50 < -0.15)
    high_vol = valid & (atr_current > atr_50 * 1.5)
    bear = valid & (sma_50 < sma_200) & (from_high_50 < -0.05)
    bull = valid & (sma_50 > sma_200) & (from_low_50 > 0.05)
    sideways = valid & (from_high_50.abs() < 0.05) & (from_low_50.abs() < 0.05)
    recovery = valid & (sma_50 < sma_200) & (from_low_50 > 0.10)

    for name, condition in [
        ("CRASH", crash),
        ("HIGH_VOL", high_vol),
        ("BEAR", bear),
        ("BULL", bull),
        ("SIDEWAYS", sideways),
        ("RECOVERY", recovery),
    ]:
        assign_mask = (regimes == "OTHER") & condition
        regimes.loc[assign_mask] = name

    return regimes
