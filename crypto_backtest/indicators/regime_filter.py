"""
Regime-Based Trade Filter

NEW FILE - Part of Alex's Quant R&D Plan (Track 2: EXPAND)

Key Finding from SHIB Investigation:
- RECOVERY regime loses money for meme coins (-11% SHIB, -0.7% DOGE)
- SIDEWAYS regime dominates profits (58.3% SHIB, 74.5% DOGE)

This filter optionally removes trades during underperforming regimes.

Usage:
    from crypto_backtest.indicators.regime_filter import filter_recovery_regime
    
    # Filter out RECOVERY regime trades
    filtered_signals = filter_recovery_regime(data, signals)
    
    # Or filter specific regimes
    filtered_signals = filter_regimes(data, signals, exclude=["RECOVERY", "CRASH"])
"""

from __future__ import annotations

import pandas as pd
import numpy as np
from typing import List, Optional

from crypto_backtest.analysis.regime import classify_regimes_v2, REGIMES_V2


def filter_recovery_regime(
    data: pd.DataFrame,
    entry_signals: pd.Series,
) -> pd.Series:
    """
    Filter out trades during RECOVERY regime.
    
    RECOVERY regime characteristics:
    - SMA50 < SMA200 (still in bearish structure)
    - But bouncing from lows (>10% from 50-bar low)
    - Often produces false reversals / dead cat bounces
    
    The shift(1) ensures no look-ahead bias - we use the regime
    from the PREVIOUS bar to filter the current signal.
    
    Args:
        data: OHLCV DataFrame with close, high, low columns
        entry_signals: Series of signals (1=long, -1=short, 0=none)
    
    Returns:
        Filtered signals with RECOVERY regime trades removed
    """
    regimes = classify_regimes_v2(data)
    is_recovery = (regimes == "RECOVERY").shift(1)  # Shift to avoid look-ahead
    
    filtered = entry_signals.copy()
    # Handle NaN values explicitly to avoid FutureWarning
    is_recovery_mask = is_recovery.copy()
    is_recovery_mask = is_recovery_mask.where(~pd.isna(is_recovery_mask), False).astype(bool)
    filtered = filtered.where(~is_recovery_mask, 0)
    
    return filtered


def filter_regimes(
    data: pd.DataFrame,
    entry_signals: pd.Series,
    exclude: List[str] = None,
    include_only: List[str] = None,
) -> pd.Series:
    """
    Filter trades based on market regime.
    
    Can either EXCLUDE specific regimes (blacklist) or 
    INCLUDE ONLY specific regimes (whitelist).
    
    Args:
        data: OHLCV DataFrame
        entry_signals: Series of signals (1=long, -1=short, 0=none)
        exclude: List of regimes to exclude (e.g., ["RECOVERY", "CRASH"])
        include_only: List of regimes to allow (e.g., ["BULL", "SIDEWAYS"])
                      If provided, exclude is ignored.
    
    Returns:
        Filtered signals
    """
    regimes = classify_regimes_v2(data)
    regimes_shifted = regimes.shift(1)  # Avoid look-ahead
    
    if include_only is not None:
        # Whitelist mode - only allow specified regimes
        valid_regimes = set(include_only)
        is_allowed = regimes_shifted.isin(valid_regimes)
    elif exclude is not None:
        # Blacklist mode - exclude specified regimes
        excluded_regimes = set(exclude)
        is_allowed = ~regimes_shifted.isin(excluded_regimes)
    else:
        # No filter
        return entry_signals
    
    filtered = entry_signals.copy()
    is_allowed_filled = is_allowed.fillna(False).infer_objects(copy=False)
    filtered = filtered.where(is_allowed_filled, 0)
    
    return filtered


def filter_by_volatility_regime(
    data: pd.DataFrame,
    entry_signals: pd.Series,
    exclude_high_vol: bool = False,
    exclude_low_vol: bool = False,
) -> pd.Series:
    """
    Filter trades based on volatility regime.
    
    Uses ATR percentile to classify volatility:
    - HIGH_VOL: ATR > 150% of 50-bar average
    - LOW_VOL: Not directly a regime, but can compute
    
    Args:
        data: OHLCV DataFrame
        entry_signals: Series of signals
        exclude_high_vol: If True, filter out HIGH_VOL regime
        exclude_low_vol: If True, filter out when ATR < 50% of average
    
    Returns:
        Filtered signals
    """
    from crypto_backtest.indicators.atr import compute_atr
    
    atr_14 = compute_atr(data["high"], data["low"], data["close"], 14)
    atr_50_mean = atr_14.rolling(50).mean()
    
    # Shift to avoid look-ahead
    atr_shifted = atr_14.shift(1)
    atr_50_shifted = atr_50_mean.shift(1)
    
    is_allowed = pd.Series(True, index=data.index)
    
    if exclude_high_vol:
        is_high_vol = atr_shifted > (atr_50_shifted * 1.5)
        is_allowed = is_allowed & ~is_high_vol
    
    if exclude_low_vol:
        is_low_vol = atr_shifted < (atr_50_shifted * 0.5)
        is_allowed = is_allowed & ~is_low_vol
    
    filtered = entry_signals.copy()
    is_allowed_filled = is_allowed.fillna(False).infer_objects(copy=False)
    filtered = filtered.where(is_allowed_filled, 0)
    
    return filtered


def get_regime_performance(
    data: pd.DataFrame,
    trades: pd.DataFrame,
) -> pd.DataFrame:
    """
    Analyze performance by regime (for diagnostics).
    
    Returns a summary of PnL, trade count, and win rate by regime.
    
    Args:
        data: OHLCV DataFrame with DatetimeIndex
        trades: DataFrame of trades with entry_time, pnl columns
    
    Returns:
        DataFrame with regime performance metrics
    """
    if trades.empty:
        return pd.DataFrame()
    
    regimes = classify_regimes_v2(data)
    
    # Map entry times to regimes
    results = []
    for regime in REGIMES_V2:
        # Find trades that entered during this regime
        regime_mask = regimes == regime
        
        # Match trades to regimes by entry_time
        regime_trades = []
        for _, trade in trades.iterrows():
            entry_time = trade.get("entry_time")
            if entry_time is not None and entry_time in regimes.index:
                if regimes.loc[entry_time] == regime:
                    regime_trades.append(trade)
        
        if not regime_trades:
            results.append({
                "regime": regime,
                "n_trades": 0,
                "total_pnl": 0,
                "pnl_pct": 0,
                "win_rate": 0,
                "avg_pnl": 0,
            })
            continue
        
        regime_df = pd.DataFrame(regime_trades)
        total_pnl = regime_df["pnl"].sum() if "pnl" in regime_df.columns else 0
        n_trades = len(regime_df)
        wins = (regime_df["pnl"] > 0).sum() if "pnl" in regime_df.columns else 0
        
        results.append({
            "regime": regime,
            "n_trades": n_trades,
            "total_pnl": total_pnl,
            "pnl_pct": 0,  # Will calculate after getting total
            "win_rate": wins / n_trades if n_trades > 0 else 0,
            "avg_pnl": total_pnl / n_trades if n_trades > 0 else 0,
        })
    
    result_df = pd.DataFrame(results)
    
    # Calculate PnL percentage
    total_pnl = result_df["total_pnl"].sum()
    if total_pnl != 0:
        result_df["pnl_pct"] = (result_df["total_pnl"] / abs(total_pnl)) * 100
    
    return result_df


# Predefined filter configurations based on research
REGIME_FILTER_CONFIGS = {
    "none": {
        "exclude": [],
        "description": "No regime filtering (baseline)",
    },
    "no_recovery": {
        "exclude": ["RECOVERY"],
        "description": "Filter out RECOVERY regime (recommended for meme coins)",
    },
    "no_crash": {
        "exclude": ["CRASH"],
        "description": "Filter out CRASH regime (extreme volatility)",
    },
    "no_recovery_crash": {
        "exclude": ["RECOVERY", "CRASH"],
        "description": "Filter out both RECOVERY and CRASH",
    },
    "trending_only": {
        "include_only": ["BULL", "BEAR"],
        "description": "Only trade in clear trend regimes",
    },
    "momentum_friendly": {
        "include_only": ["BULL", "SIDEWAYS", "HIGH_VOL"],
        "description": "Regimes favorable for momentum strategies",
    },
}


def apply_regime_filter_config(
    data: pd.DataFrame,
    entry_signals: pd.Series,
    config_name: str = "none",
) -> pd.Series:
    """
    Apply a predefined regime filter configuration.
    
    Args:
        data: OHLCV DataFrame
        entry_signals: Entry signals
        config_name: One of the predefined configs
    
    Returns:
        Filtered signals
    """
    if config_name not in REGIME_FILTER_CONFIGS:
        raise ValueError(
            f"Unknown config: {config_name}. "
            f"Available: {list(REGIME_FILTER_CONFIGS.keys())}"
        )
    
    config = REGIME_FILTER_CONFIGS[config_name]
    
    return filter_regimes(
        data,
        entry_signals,
        exclude=config.get("exclude"),
        include_only=config.get("include_only"),
    )
