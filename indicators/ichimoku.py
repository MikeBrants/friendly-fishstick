"""
Ichimoku Light filter for 5in1 strategy.
Mode: ichi5in1Strict = OFF (Light version).
"""

from __future__ import annotations

import numpy as np
from numba import njit


@njit
def _period_high(values: np.ndarray, end: int, period: int) -> float:
    start = end - period + 1
    if start < 0:
        start = 0
    max_val = values[start]
    for idx in range(start + 1, end + 1):
        if values[idx] > max_val:
            max_val = values[idx]
    return max_val


@njit
def _period_low(values: np.ndarray, end: int, period: int) -> float:
    start = end - period + 1
    if start < 0:
        start = 0
    min_val = values[start]
    for idx in range(start + 1, end + 1):
        if values[idx] < min_val:
            min_val = values[idx]
    return min_val


@njit
def compute_ichimoku_components(
    high: np.ndarray,
    low: np.ndarray,
    close: np.ndarray,
    tenkan_p: int = 9,
    kijun_p: int = 26,
    senkou_b_p: int = 52,
    displacement: int = 26,
) -> tuple:
    """
    Returns: tenkan, kijun, senkou_a, senkou_b, chikou arrays.
    """
    n = len(close)
    tenkan = np.full(n, np.nan)
    kijun = np.full(n, np.nan)
    senkou_a = np.full(n, np.nan)
    senkou_b = np.full(n, np.nan)
    chikou = np.full(n, np.nan)

    for i in range(n):
        if i >= tenkan_p - 1:
            tenkan[i] = (_period_high(high, i, tenkan_p) + _period_low(low, i, tenkan_p)) / 2.0

        if i >= kijun_p - 1:
            kijun[i] = (_period_high(high, i, kijun_p) + _period_low(low, i, kijun_p)) / 2.0

        if i >= kijun_p - 1:
            senkou_a[i] = (tenkan[i] + kijun[i]) / 2.0

        if i >= senkou_b_p - 1:
            senkou_b[i] = (_period_high(high, i, senkou_b_p) + _period_low(low, i, senkou_b_p)) / 2.0

        if i >= displacement:
            chikou[i] = close[i]

    return tenkan, kijun, senkou_a, senkou_b, chikou


@njit
def compute_ichimoku_light_state(
    high: np.ndarray,
    low: np.ndarray,
    close: np.ndarray,
    tenkan_p: int = 9,
    kijun_p: int = 26,
    senkou_b_p: int = 52,
    displacement: int = 26,
) -> tuple:
    """
    Compute Ichimoku Light bullish/bearish state for each bar.

    Returns:
        is_bullish: array of bool (at least 1 condition true)
        is_bearish: array of bool (all 3 conditions true)
    """
    tenkan, kijun, senkou_a, senkou_b, _ = compute_ichimoku_components(
        high,
        low,
        close,
        tenkan_p=tenkan_p,
        kijun_p=kijun_p,
        senkou_b_p=senkou_b_p,
        displacement=displacement,
    )

    n = len(close)
    is_bullish = np.zeros(n, dtype=np.bool_)
    is_bearish = np.zeros(n, dtype=np.bool_)
    warmup = senkou_b_p

    for i in range(n):
        if i < warmup or i - displacement < 0:
            continue

        cloud_idx = i - displacement
        kumo_top = senkou_a[cloud_idx]
        kumo_bottom = senkou_b[cloud_idx]
        if kumo_top != kumo_top or kumo_bottom != kumo_bottom:
            continue
        if kumo_bottom > kumo_top:
            temp = kumo_top
            kumo_top = kumo_bottom
            kumo_bottom = temp

        price_above_kumo = close[i] > kumo_top
        price_below_kumo = close[i] < kumo_bottom
        tenkan_above_kijun = tenkan[i] > kijun[i]
        tenkan_below_kijun = tenkan[i] < kijun[i]
        chikou_above = close[i] > close[i - displacement]
        chikou_below = close[i] < close[i - displacement]

        is_bullish[i] = price_above_kumo or tenkan_above_kijun or chikou_above
        is_bearish[i] = price_below_kumo and tenkan_below_kijun and chikou_below

    return is_bullish, is_bearish
