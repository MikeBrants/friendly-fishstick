"""
ADX (Average Directional Index) Trend Strength Filter

NEW FILE - Part of Alex's Quant R&D Plan (Track 2: EXPAND)

Rationale: Ichimoku gives direction, but not trend STRENGTH. 
ADX > 25 indicates a trending market where momentum strategies work better.

This filter is OPT-IN and does NOT modify existing code.

Usage:
    from crypto_backtest.indicators.adx_filter import compute_adx, adx_filter
    
    # Get ADX values
    adx = compute_adx(high, low, close, period=14)
    
    # Apply filter to signals
    filtered_signals = adx_filter(high, low, close, signals, period=14, threshold=25)
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def compute_true_range(
    high: pd.Series, 
    low: pd.Series, 
    close: pd.Series
) -> pd.Series:
    """Compute True Range (TR)."""
    prev_close = close.shift(1)
    
    tr1 = high - low
    tr2 = (high - prev_close).abs()
    tr3 = (low - prev_close).abs()
    
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    return tr


def compute_directional_movement(
    high: pd.Series, 
    low: pd.Series
) -> tuple[pd.Series, pd.Series]:
    """Compute +DM and -DM (Directional Movement)."""
    up_move = high.diff()
    down_move = -low.diff()
    
    plus_dm = pd.Series(index=high.index, dtype=float)
    minus_dm = pd.Series(index=high.index, dtype=float)
    
    # +DM: up_move > down_move and up_move > 0
    plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0)
    plus_dm = pd.Series(plus_dm, index=high.index)
    
    # -DM: down_move > up_move and down_move > 0
    minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0)
    minus_dm = pd.Series(minus_dm, index=high.index)
    
    return plus_dm, minus_dm


def wilder_smooth(series: pd.Series, period: int) -> pd.Series:
    """Apply Wilder's smoothing (EMA with alpha=1/period)."""
    return series.ewm(alpha=1/period, adjust=False).mean()


def compute_adx(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    period: int = 14
) -> pd.Series:
    """
    Compute Average Directional Index (ADX).
    
    The ADX measures trend strength regardless of direction.
    - ADX < 20: Weak/no trend (range-bound)
    - ADX 20-25: Developing trend
    - ADX 25-50: Strong trend
    - ADX > 50: Very strong trend
    
    Args:
        high: High prices
        low: Low prices
        close: Close prices
        period: ADX period (default: 14, Wilder's standard)
    
    Returns:
        ADX values as pandas Series
    """
    if period < 1:
        raise ValueError("period must be >= 1")
    
    # 1. Calculate True Range
    tr = compute_true_range(high, low, close)
    
    # 2. Calculate Directional Movement
    plus_dm, minus_dm = compute_directional_movement(high, low)
    
    # 3. Smooth TR, +DM, -DM using Wilder's method
    atr = wilder_smooth(tr, period)
    smooth_plus_dm = wilder_smooth(plus_dm, period)
    smooth_minus_dm = wilder_smooth(minus_dm, period)
    
    # 4. Calculate +DI and -DI
    plus_di = 100 * smooth_plus_dm / atr
    minus_di = 100 * smooth_minus_dm / atr
    
    # Handle division by zero
    plus_di = plus_di.replace([np.inf, -np.inf], 0)
    minus_di = minus_di.replace([np.inf, -np.inf], 0)
    
    # 5. Calculate DX (Directional Index)
    dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di)
    dx = dx.replace([np.inf, -np.inf], 0)
    
    # 6. Smooth DX to get ADX
    adx = wilder_smooth(dx, period)
    
    return adx


def compute_di(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    period: int = 14
) -> tuple[pd.Series, pd.Series]:
    """
    Compute +DI and -DI (Directional Indicators).
    
    Returns:
        Tuple of (+DI, -DI)
    """
    tr = compute_true_range(high, low, close)
    plus_dm, minus_dm = compute_directional_movement(high, low)
    
    atr = wilder_smooth(tr, period)
    smooth_plus_dm = wilder_smooth(plus_dm, period)
    smooth_minus_dm = wilder_smooth(minus_dm, period)
    
    plus_di = 100 * smooth_plus_dm / atr
    minus_di = 100 * smooth_minus_dm / atr
    
    plus_di = plus_di.replace([np.inf, -np.inf], 0)
    minus_di = minus_di.replace([np.inf, -np.inf], 0)
    
    return plus_di, minus_di


def adx_filter(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    signals: pd.Series,
    period: int = 14,
    threshold: float = 25.0
) -> pd.Series:
    """
    Filter signals based on ADX trend strength.
    
    Only allows signals when ADX > threshold (trending market).
    This helps avoid false signals in range-bound conditions.
    
    Args:
        high: High prices
        low: Low prices
        close: Close prices
        signals: Entry signals (1 for long, -1 for short, 0 for none)
        period: ADX period (default: 14)
        threshold: ADX threshold for allowing signals (default: 25)
    
    Returns:
        Filtered signals (signals where ADX > threshold)
    """
    adx = compute_adx(high, low, close, period)
    
    # Shift ADX by 1 to avoid look-ahead bias
    adx_shifted = adx.shift(1)
    
    # Only allow signals when trend is strong
    is_trending = adx_shifted > threshold
    
    filtered = signals.copy()
    filtered = filtered.where(is_trending, 0)
    
    return filtered


def adx_directional_filter(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    signals: pd.Series,
    period: int = 14,
    threshold: float = 25.0
) -> pd.Series:
    """
    Advanced filter: considers both ADX strength AND DI direction.
    
    - Long signals: ADX > threshold AND +DI > -DI
    - Short signals: ADX > threshold AND -DI > +DI
    
    This provides additional confirmation that trend strength
    aligns with signal direction.
    
    Args:
        high: High prices
        low: Low prices
        close: Close prices
        signals: Entry signals (1 for long, -1 for short, 0 for none)
        period: ADX period (default: 14)
        threshold: ADX threshold for allowing signals (default: 25)
    
    Returns:
        Filtered signals with directional confirmation
    """
    adx = compute_adx(high, low, close, period)
    plus_di, minus_di = compute_di(high, low, close, period)
    
    # Shift to avoid look-ahead
    adx_shifted = adx.shift(1)
    plus_di_shifted = plus_di.shift(1)
    minus_di_shifted = minus_di.shift(1)
    
    is_trending = adx_shifted > threshold
    
    filtered = signals.copy()
    
    # Long signals: need +DI > -DI (bullish momentum)
    long_mask = (signals == 1) & is_trending & (plus_di_shifted > minus_di_shifted)
    
    # Short signals: need -DI > +DI (bearish momentum)
    short_mask = (signals == -1) & is_trending & (minus_di_shifted > plus_di_shifted)
    
    # Apply filter
    filtered = pd.Series(0, index=signals.index)
    filtered = filtered.where(~long_mask, 1)
    filtered = filtered.where(~short_mask, -1)
    
    return filtered


# Optuna search space for ADX parameters
ADX_SEARCH_SPACE = {
    "adx_period": (10, 20),
    "adx_threshold": (20, 35),
}


def get_adx_optuna_params(trial) -> dict:
    """
    Get ADX parameters from Optuna trial.
    
    Usage in optimization:
        adx_params = get_adx_optuna_params(trial)
        # Apply ADX filter with these params
    """
    return {
        "adx_period": trial.suggest_int("adx_period", *ADX_SEARCH_SPACE["adx_period"]),
        "adx_threshold": trial.suggest_float("adx_threshold", *ADX_SEARCH_SPACE["adx_threshold"]),
    }
