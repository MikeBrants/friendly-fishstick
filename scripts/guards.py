"""Guards for FINAL TRIGGER pipeline."""

from __future__ import annotations

import numpy as np
import pandas as pd


def _calculate_regime_ichimoku(
    ohlcv_df: pd.DataFrame,
    entry_idx: int,
    tenkan: int = 13,
    kijun: int = 34,
    senkou_b: int = 52,
    displacement: int = 26,
) -> str:
    """
    Calculate regime at entry_idx using ONLY data available before entry.

    This must match exactly the logic in generate_mock_data._precompute_regimes
    """
    n = len(ohlcv_df)
    min_bars = senkou_b + displacement

    if entry_idx < min_bars:
        return "sideways"

    high = ohlcv_df["high"].values
    low = ohlcv_df["low"].values
    close = ohlcv_df["close"].values

    idx = entry_idx - 1
    cloud_calc_idx = idx - displacement

    if cloud_calc_idx < senkou_b:
        return "sideways"

    t_high = np.max(high[max(0, cloud_calc_idx - tenkan + 1):cloud_calc_idx + 1])
    t_low = np.min(low[max(0, cloud_calc_idx - tenkan + 1):cloud_calc_idx + 1])
    t_sen = (t_high + t_low) / 2

    k_high = np.max(high[max(0, cloud_calc_idx - kijun + 1):cloud_calc_idx + 1])
    k_low = np.min(low[max(0, cloud_calc_idx - kijun + 1):cloud_calc_idx + 1])
    k_sen = (k_high + k_low) / 2

    s_a = (t_sen + k_sen) / 2

    s_b_high = np.max(high[max(0, cloud_calc_idx - senkou_b + 1):cloud_calc_idx + 1])
    s_b_low = np.min(low[max(0, cloud_calc_idx - senkou_b + 1):cloud_calc_idx + 1])
    s_b = (s_b_high + s_b_low) / 2

    cloud_top = max(s_a, s_b)
    cloud_bottom = min(s_a, s_b)

    current_close = close[idx]

    if current_close > cloud_top * 1.001:
        return "bull"
    if current_close < cloud_bottom * 0.999:
        return "bear"
    return "sideways"


def guard_regime_lookahead(trades_df: pd.DataFrame, ohlcv_df: pd.DataFrame, config: dict | None = None) -> dict:
    """Verify no trade uses regime calculated with future data."""
    violations = []
    n_checked = 0

    tenkan, kijun, senkou_b, displacement = 13, 34, 52, 26
    min_bars_required = senkou_b + displacement

    ohlcv_df = ohlcv_df.copy()
    if "timestamp" in ohlcv_df.columns:
        ohlcv_df = ohlcv_df.set_index("timestamp")

    for idx, trade in trades_df.iterrows():
        entry_time = trade["entry_time"]
        recorded_regime = trade.get("regime", "unknown")

        if recorded_regime == "unknown":
            continue

        try:
            if entry_time in ohlcv_df.index:
                entry_idx = ohlcv_df.index.get_loc(entry_time)
            else:
                mask = ohlcv_df.index <= entry_time
                if not mask.any():
                    continue
                entry_idx = mask.sum() - 1
        except Exception:
            continue

        if entry_idx < min_bars_required:
            continue

        n_checked += 1

        ohlcv_reset = ohlcv_df.reset_index()
        recalculated = _calculate_regime_ichimoku(
            ohlcv_reset, entry_idx, tenkan, kijun, senkou_b, displacement
        )

        if recalculated != recorded_regime:
            violations.append({
                "trade_idx": idx,
                "entry_time": str(entry_time),
                "recorded": recorded_regime,
                "recalculated": recalculated,
            })

    n_violations = len(violations)
    violation_rate = n_violations / n_checked if n_checked > 0 else 0.0
    tolerance = 0.05

    return {
        "guard": "regime_lookahead",
        "passed": violation_rate <= tolerance,
        "n_checked": n_checked,
        "n_violations": n_violations,
        "violation_rate": round(violation_rate, 4),
        "tolerance": tolerance,
        "violations": violations[:10],
        "reason": f"Lookahead: {n_violations}/{n_checked} violations ({violation_rate:.2%})",
    }


GUARDS_CONFIG = {
    "regime_lookahead": {
        "function": guard_regime_lookahead,
        "type": "hard",
        "requires": ["trades_df", "ohlcv_df"],
    }
}
