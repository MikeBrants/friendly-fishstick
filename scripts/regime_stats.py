"""FINAL TRIGGER v4.3 - Regime Statistics (side-aware, z-score, stability)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional, Tuple

import numpy as np
import pandas as pd


def _to_native(obj):
    """Convert numpy types to native Python types for JSON serialization."""
    import numpy as np

    if isinstance(obj, dict):
        return {k: _to_native(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_to_native(v) for v in obj]
    np_bool = getattr(np, "bool_", None)
    if np_bool is not None and isinstance(obj, np_bool):
        return bool(obj)
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        return float(obj)
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    return obj


@dataclass
class BucketStats:
    side: str
    regime: str
    n_trades: int
    n_wins: int
    win_rate: float
    avg_pnl: float
    total_pnl: float


@dataclass
class RegimeStatsResult:
    bucket_stats: Dict[str, BucketStats]
    delta_long: float
    delta_short: float
    z_long: float
    z_short: float
    side_aware_pass: bool
    sufficient_data: bool
    stability_result: Optional[dict]
    signal_detected: bool
    reason: str


def compute_regime_stats_side_aware(trades_df: pd.DataFrame, config: dict) -> RegimeStatsResult:
    regime_cfg = config.get("policy", {}).get("regime", {})
    n_min_bucket = regime_cfg.get("n_trades_min_per_bucket", 80)
    z_min = regime_cfg.get("signal_z_min", 1.65)

    bucket_stats = _compute_bucket_stats(trades_df)
    sufficient_data = _check_data_sufficiency(bucket_stats, n_min_bucket)

    if not sufficient_data:
        return RegimeStatsResult(
            bucket_stats=bucket_stats,
            delta_long=0.0,
            delta_short=0.0,
            z_long=0.0,
            z_short=0.0,
            side_aware_pass=False,
            sufficient_data=False,
            stability_result=None,
            signal_detected=False,
            reason=f"Insufficient data: buckets < {n_min_bucket} trades",
        )

    delta_long, z_long = _compute_delta_z(bucket_stats, "long", "bull", "bear")
    delta_short, z_short = _compute_delta_z(bucket_stats, "short", "bear", "bull")

    side_aware_pass = (
        delta_long > 0 and z_long >= z_min and delta_short > 0 and z_short >= z_min
    )
    stability_result = check_stability_windows(trades_df, config)
    signal_detected = side_aware_pass and stability_result.get("stability_pass", False)

    if signal_detected:
        reason = (
            "Regime signal: "
            f"delta_long={delta_long:.3f}(z={z_long:.2f}), "
            f"delta_short={delta_short:.3f}(z={z_short:.2f})"
        )
    elif not side_aware_pass:
        reason = (
            "Side-aware fail: "
            f"delta_long={delta_long:.3f}(z={z_long:.2f}), "
            f"delta_short={delta_short:.3f}(z={z_short:.2f})"
        )
    else:
        reason = (
            "Stability fail: "
            f"{stability_result['n_windows_pass']}/{stability_result['n_valid_windows']} windows"
        )

    return RegimeStatsResult(
        bucket_stats=bucket_stats,
        delta_long=delta_long,
        delta_short=delta_short,
        z_long=z_long,
        z_short=z_short,
        side_aware_pass=side_aware_pass,
        sufficient_data=sufficient_data,
        stability_result=stability_result,
        signal_detected=signal_detected,
        reason=reason,
    )


def _compute_bucket_stats(trades_df: pd.DataFrame) -> Dict[str, BucketStats]:
    bucket_stats: Dict[str, BucketStats] = {}
    for side in ["long", "short"]:
        for regime in ["bull", "bear", "sideways"]:
            key = f"{side}_{regime}"
            mask = (trades_df["side"] == side) & (trades_df["regime"] == regime)
            subset = trades_df[mask]
            n_trades = len(subset)
            if n_trades > 0:
                n_wins = int(subset["win"].sum())
                win_rate = n_wins / n_trades
                avg_pnl = float(subset["pnl"].mean())
                total_pnl = float(subset["pnl"].sum())
            else:
                n_wins, win_rate, avg_pnl, total_pnl = 0, 0.0, 0.0, 0.0
            bucket_stats[key] = BucketStats(
                side, regime, n_trades, n_wins, win_rate, avg_pnl, total_pnl
            )
    return bucket_stats


def _check_data_sufficiency(bucket_stats: Dict[str, BucketStats], n_min: int) -> bool:
    required = ["long_bull", "long_bear", "short_bull", "short_bear"]
    return all(
        key in bucket_stats and bucket_stats[key].n_trades >= n_min for key in required
    )


def _compute_delta_z(
    bucket_stats: Dict[str, BucketStats],
    side: str,
    regime_good: str,
    regime_bad: str,
) -> Tuple[float, float]:
    stats_good = bucket_stats[f"{side}_{regime_good}"]
    stats_bad = bucket_stats[f"{side}_{regime_bad}"]
    p1, p2 = stats_good.win_rate, stats_bad.win_rate
    n1, n2 = stats_good.n_trades, stats_bad.n_trades
    delta = p1 - p2
    if n1 > 0 and n2 > 0:
        se = np.sqrt((p1 * (1 - p1) / n1) + (p2 * (1 - p2) / n2))
        z = delta / se if se > 0 else 0.0
    else:
        z = 0.0
    return delta, z


def check_stability_windows(trades_df: pd.DataFrame, config: dict) -> dict:
    regime_cfg = config.get("policy", {}).get("regime", {})
    n_windows = regime_cfg.get("stability_windows", 4)
    pass_ratio = regime_cfg.get("stability_pass_ratio", 0.75)
    n_min_per_window = regime_cfg.get("n_trades_min_per_window", 20)

    trades_sorted = trades_df.sort_values("entry_time")
    window_size = len(trades_sorted) // n_windows
    if window_size < 10:
        return {
            "windows": [],
            "n_windows_pass": 0,
            "n_valid_windows": 0,
            "stability_pass": False,
        }

    n_pass, n_valid = 0, 0
    for i in range(n_windows):
        start_idx = i * window_size
        end_idx = (i + 1) * window_size if i < n_windows - 1 else len(trades_sorted)
        window_trades = trades_sorted.iloc[start_idx:end_idx]

        bucket_counts = {}
        for side in ["long", "short"]:
            for regime in ["bull", "bear"]:
                mask = (window_trades["side"] == side) & (
                    window_trades["regime"] == regime
                )
                bucket_counts[f"{side}_{regime}"] = int(mask.sum())

        if min(bucket_counts.values()) >= n_min_per_window:
            n_valid += 1
            bucket_stats = _compute_bucket_stats(window_trades)
            delta_long, _ = _compute_delta_z(bucket_stats, "long", "bull", "bear")
            delta_short, _ = _compute_delta_z(bucket_stats, "short", "bear", "bull")
            if delta_long > 0 and delta_short > 0:
                n_pass += 1

    stability_pass = (n_pass / n_valid) >= pass_ratio if n_valid >= 2 else False
    return {
        "n_windows_pass": n_pass,
        "n_valid_windows": n_valid,
        "stability_pass": stability_pass,
    }


def get_regime_decision(trades_df: pd.DataFrame, config: dict) -> dict:
    stats = compute_regime_stats_side_aware(trades_df, config)
    result = {
        "regime_useful": stats.signal_detected,
        "reason": stats.reason,
        "stats": {
            "delta_long": stats.delta_long,
            "delta_short": stats.delta_short,
            "z_long": stats.z_long,
            "z_short": stats.z_short,
            "side_aware_pass": stats.side_aware_pass,
            "sufficient_data": stats.sufficient_data,
            "stability_pass": (
                stats.stability_result.get("stability_pass", False)
                if stats.stability_result
                else False
            ),
            "bucket_stats": {k: vars(v) for k, v in stats.bucket_stats.items()},
        },
    }
    return _to_native(result)
