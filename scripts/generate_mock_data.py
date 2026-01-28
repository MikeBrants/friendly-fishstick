#!/usr/bin/env python3
"""
FINAL TRIGGER v4.3 - Mock Data Generator

Generates realistic mock data for end-to-end pipeline testing.
Creates all required artifacts in runs/v4_3/<asset>/<run_id>/
"""

import argparse
import json
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.artifacts import (
    ensure_artifact_dir,
    get_artifact_path,
    ArtifactNames,
    Phases,
    PIPELINE_VERSION,
)


def generate_ohlcv(n_bars: int = 17520, seed: int = 42) -> pd.DataFrame:
    """Generate realistic OHLCV data."""
    np.random.seed(seed)

    start_price = 2000.0
    returns = np.random.normal(0.0001, 0.02, n_bars)

    trend = np.sin(np.linspace(0, 4 * np.pi, n_bars)) * 0.001
    returns = returns + trend

    prices = start_price * np.exp(np.cumsum(returns))

    timestamps = pd.date_range(
        start="2023-01-01",
        periods=n_bars,
        freq="h",
    )

    data = {
        "timestamp": timestamps,
        "open": prices,
        "high": prices * (1 + np.abs(np.random.normal(0, 0.005, n_bars))),
        "low": prices * (1 - np.abs(np.random.normal(0, 0.005, n_bars))),
        "close": prices * (1 + np.random.normal(0, 0.002, n_bars)),
        "volume": np.random.exponential(1000, n_bars),
    }

    df = pd.DataFrame(data)

    df["high"] = df[["open", "high", "close"]].max(axis=1)
    df["low"] = df[["open", "low", "close"]].min(axis=1)

    return df


def generate_trades(
    ohlcv_df: pd.DataFrame,
    n_trades: int = 800,
    regime_effect: bool = True,
    seed: int = 42,
) -> pd.DataFrame:
    """
    Generate mock trades with optional regime effect.

    IMPORTANT: Regime is calculated using ONLY data available BEFORE entry time
    to avoid lookahead bias.

    If regime_effect=True:
    - Long trades perform better in bull regime
    - Short trades perform better in bear regime
    """
    np.random.seed(seed)

    regimes = _precompute_regimes(ohlcv_df)

    valid_indices = range(100, len(ohlcv_df) - 10)
    entry_indices = np.random.choice(valid_indices, n_trades, replace=True)
    entry_indices = np.sort(entry_indices)

    trades = []

    for i, entry_idx in enumerate(entry_indices):
        entry_time = ohlcv_df.iloc[entry_idx]["timestamp"]
        entry_price = ohlcv_df.iloc[entry_idx]["close"]

        side = "long" if np.random.random() < 0.5 else "short"

        regime = regimes[entry_idx]

        if regime_effect:
            if side == "long" and regime == "bull":
                base_wr = 0.58
                base_pnl = 0.015
            elif side == "long" and regime == "bear":
                base_wr = 0.42
                base_pnl = -0.008
            elif side == "short" and regime == "bear":
                base_wr = 0.58
                base_pnl = 0.015
            elif side == "short" and regime == "bull":
                base_wr = 0.42
                base_pnl = -0.008
            else:
                base_wr = 0.50
                base_pnl = 0.003
        else:
            base_wr = 0.52
            base_pnl = 0.005

        win = np.random.random() < base_wr

        if win:
            pnl = abs(np.random.normal(base_pnl + 0.01, 0.008))
        else:
            pnl = -abs(np.random.normal(abs(base_pnl) + 0.008, 0.006))

        hold_hours = np.random.randint(1, 25)
        exit_idx = min(entry_idx + hold_hours, len(ohlcv_df) - 1)
        exit_time = ohlcv_df.iloc[exit_idx]["timestamp"]
        exit_price = entry_price * (1 + pnl)

        trades.append({
            "trade_id": i,
            "entry_time": entry_time,
            "exit_time": exit_time,
            "side": side,
            "regime": regime,
            "entry_price": round(entry_price, 2),
            "exit_price": round(exit_price, 2),
            "pnl": round(pnl, 6),
            "pnl_pct": round(pnl * 100, 4),
            "win": win,
            "hold_hours": hold_hours,
        })

    return pd.DataFrame(trades)


def _precompute_regimes(ohlcv_df: pd.DataFrame) -> list:
    """
    Pre-compute regime for each bar using ONLY past data.

    Uses Ichimoku cloud with:
    - tenkan: 13 periods
    - kijun: 34 periods
    - senkou_b: 52 periods
    - displacement: 26 periods (cloud is projected 26 periods ahead)

    For bar i, we use data [0:i] only (no future data).
    """
    n = len(ohlcv_df)
    regimes = ["sideways"] * n

    high = ohlcv_df["high"].values
    low = ohlcv_df["low"].values
    close = ohlcv_df["close"].values

    tenkan_period = 13
    kijun_period = 34
    senkou_b_period = 52
    displacement = 26

    min_bars = senkou_b_period + displacement

    for i in range(min_bars, n):
        idx = i - 1

        cloud_calc_idx = idx - displacement

        if cloud_calc_idx >= senkou_b_period:
            t_high = np.max(high[max(0, cloud_calc_idx - tenkan_period + 1):cloud_calc_idx + 1])
            t_low = np.min(low[max(0, cloud_calc_idx - tenkan_period + 1):cloud_calc_idx + 1])
            t_sen = (t_high + t_low) / 2

            k_high = np.max(high[max(0, cloud_calc_idx - kijun_period + 1):cloud_calc_idx + 1])
            k_low = np.min(low[max(0, cloud_calc_idx - kijun_period + 1):cloud_calc_idx + 1])
            k_sen = (k_high + k_low) / 2

            s_a = (t_sen + k_sen) / 2

            s_b_high = np.max(high[max(0, cloud_calc_idx - senkou_b_period + 1):cloud_calc_idx + 1])
            s_b_low = np.min(low[max(0, cloud_calc_idx - senkou_b_period + 1):cloud_calc_idx + 1])
            s_b = (s_b_high + s_b_low) / 2

            cloud_top = max(s_a, s_b)
            cloud_bottom = min(s_a, s_b)

            current_close = close[idx]

            if current_close > cloud_top * 1.001:
                regimes[i] = "bull"
            elif current_close < cloud_bottom * 0.999:
                regimes[i] = "bear"
            else:
                regimes[i] = "sideways"
        else:
            regimes[i] = "sideways"

    return regimes


def generate_screening_results(trades_df: pd.DataFrame, seed: int = 42) -> dict:
    """Generate mock screening results."""
    np.random.seed(seed)

    long_configs = []
    short_configs = []

    for i in range(20):
        long_configs.append({
            "config_id": f"L{i + 1:02d}",
            "params": {"tp1": 1.5 + i * 0.1, "tp2": 2.5 + i * 0.1, "sl": 1.0},
            "wfe": round(0.5 + np.random.random() * 0.5, 3),
            "sharpe": round(0.8 + np.random.random() * 1.5, 3),
            "trades": 50 + np.random.randint(0, 100),
            "win_rate": round(0.45 + np.random.random() * 0.15, 3),
        })

        short_configs.append({
            "config_id": f"S{i + 1:02d}",
            "params": {"tp1": 1.5 + i * 0.1, "tp2": 2.5 + i * 0.1, "sl": 1.0},
            "wfe": round(0.5 + np.random.random() * 0.5, 3),
            "sharpe": round(0.8 + np.random.random() * 1.5, 3),
            "trades": 50 + np.random.randint(0, 100),
            "win_rate": round(0.45 + np.random.random() * 0.15, 3),
        })

    long_configs = sorted(long_configs, key=lambda x: x["sharpe"], reverse=True)
    short_configs = sorted(short_configs, key=lambda x: x["sharpe"], reverse=True)

    return {
        "long": long_configs,
        "short": short_configs,
    }


def generate_coupled_candidates(screening: dict, k: int = 10) -> list:
    """Generate top_k_cross coupled candidates."""
    candidates = []

    for long_cfg in screening["long"][:k]:
        for short_cfg in screening["short"][:k]:
            couple_id = f"{long_cfg['config_id']}_{short_cfg['config_id']}"
            combined_sharpe = (long_cfg["sharpe"] + short_cfg["sharpe"]) / 2

            candidates.append({
                "couple_id": couple_id,
                "long_config": long_cfg,
                "short_config": short_cfg,
                "combined_sharpe": round(combined_sharpe, 3),
                "combined_wfe": round((long_cfg["wfe"] + short_cfg["wfe"]) / 2, 3),
            })

    candidates = sorted(candidates, key=lambda x: x["combined_sharpe"], reverse=True)

    return candidates


def generate_baseline_best(candidates: list) -> dict:
    """Generate baseline_best.json from top candidate."""
    best = candidates[0] if candidates else {}

    return {
        "couple_id": best.get("couple_id", "L01_S01"),
        "long_config": best.get("long_config", {}),
        "short_config": best.get("short_config", {}),
        "wfe": best.get("combined_wfe", 0.65),
        "sharpe": best.get("combined_sharpe", 1.2),
        "oos_trades": 120,
        "bars": 17520,
        "max_dd": 18.5,
        "pf": 1.35,
        "coupled_candidates": candidates[:10],
    }


def generate_cscv_folds(n_trades: int, n_folds: int = 10) -> list:
    """Generate CSCV fold indices."""
    indices = list(range(n_trades))
    fold_size = n_trades // n_folds
    folds = []

    for i in range(n_folds):
        test_start = i * fold_size
        test_end = (i + 1) * fold_size if i < n_folds - 1 else n_trades
        test_idx = indices[test_start:test_end]
        train_idx = indices[:test_start] + indices[test_end:]

        folds.append({
            "fold_id": i,
            "train_idx": train_idx,
            "test_idx": test_idx,
        })

    return folds


def generate_guards_result() -> dict:
    """Generate passing guards result."""
    return {
        "all_hard_passed": True,
        "n_passed": 7,
        "n_total": 7,
        "guards": {
            "wfe": {"passed": True, "value": 0.68, "threshold": 0.60},
            "trades_oos": {"passed": True, "value": 85, "threshold": 60},
            "bars": {"passed": True, "value": 17520, "threshold": 12000},
            "sharpe": {"passed": True, "value": 1.25, "threshold": 0.80},
            "max_dd": {"passed": True, "value": 18.5, "threshold": 35.0},
            "pf": {"passed": True, "value": 1.35, "threshold": 1.05},
            "top10_concentration": {"passed": True, "value": 28.0, "threshold": 40.0},
        },
    }


def generate_pbo_results() -> tuple:
    """Generate PBO proxy and CSCV results."""
    proxy = {
        "pbo": 0.35,
        "passed": True,
        "n_folds": 8,
    }

    cscv = {
        "pbo": 0.38,
        "passed": True,
        "cscv_pass": 0.62,
        "threshold": 0.50,
        "n_folds": 10,
    }

    return proxy, cscv


def generate_all_mock_data(
    asset: str,
    run_id: str,
    n_bars: int = 17520,
    n_trades: int = 800,
    regime_effect: bool = True,
    seed: int = 42,
) -> dict:
    """Generate all mock data for a complete pipeline run."""
    print(f"Generating mock data for {asset}/{run_id}...")

    print("  [1/8] Generating OHLCV data...")
    ohlcv_df = generate_ohlcv(n_bars, seed)

    print("  [2/8] Generating trades...")
    trades_df = generate_trades(ohlcv_df, n_trades, regime_effect, seed)

    print("  [3/8] Generating screening results...")
    screening = generate_screening_results(trades_df, seed)

    print("  [4/8] Generating coupled candidates...")
    candidates = generate_coupled_candidates(screening)

    print("  [5/8] Generating baseline results...")
    baseline = generate_baseline_best(candidates)

    print("  [6/8] Generating CSCV folds...")
    cscv_folds = generate_cscv_folds(len(trades_df))

    print("  [7/8] Generating guards & PBO results...")
    guards = generate_guards_result()
    pbo_proxy, pbo_cscv = generate_pbo_results()

    print("  [8/8] Saving artifacts...")

    screening_dir = ensure_artifact_dir(asset, run_id, Phases.SCREENING)
    with open(screening_dir / ArtifactNames.SCREEN_LONG, "w", encoding="utf-8") as f:
        json.dump(screening["long"], f, indent=2)
    with open(screening_dir / ArtifactNames.SCREEN_SHORT, "w", encoding="utf-8") as f:
        json.dump(screening["short"], f, indent=2)

    coupling_dir = ensure_artifact_dir(asset, run_id, Phases.COUPLING)
    with open(coupling_dir / ArtifactNames.COUPLED_CANDIDATES, "w", encoding="utf-8") as f:
        json.dump(candidates, f, indent=2)

    baseline_dir = ensure_artifact_dir(asset, run_id, Phases.BASELINE)
    with open(baseline_dir / ArtifactNames.BASELINE_BEST, "w", encoding="utf-8") as f:
        json.dump(baseline, f, indent=2)
    trades_df.to_parquet(baseline_dir / ArtifactNames.TRADES_PARQUET, index=False)

    ohlcv_df.to_parquet(baseline_dir / "ohlcv.parquet", index=False)

    pbo_dir = ensure_artifact_dir(asset, run_id, Phases.PBO)
    with open(pbo_dir / ArtifactNames.PBO_PROXY, "w", encoding="utf-8") as f:
        json.dump(pbo_proxy, f, indent=2)
    with open(pbo_dir / ArtifactNames.PBO_CSCV, "w", encoding="utf-8") as f:
        json.dump(pbo_cscv, f, indent=2)
    with open(pbo_dir / ArtifactNames.CSCV_FOLDS, "w", encoding="utf-8") as f:
        json.dump(cscv_folds, f, indent=2)

    guards_dir = ensure_artifact_dir(asset, run_id, Phases.GUARDS)
    with open(guards_dir / ArtifactNames.GUARDS_RESULT, "w", encoding="utf-8") as f:
        json.dump(guards, f, indent=2)

    summary = {
        "asset": asset,
        "run_id": run_id,
        "generated_at": datetime.now().isoformat(),
        "n_bars": n_bars,
        "n_trades": len(trades_df),
        "regime_effect": regime_effect,
        "seed": seed,
        "trades_by_regime": trades_df.groupby("regime").size().to_dict(),
        "trades_by_side": trades_df.groupby("side").size().to_dict(),
        "win_rate": round(trades_df["win"].mean(), 4),
        "mean_pnl": round(trades_df["pnl"].mean(), 6),
    }

    archive_dir = ensure_artifact_dir(asset, run_id, Phases.ARCHIVE)
    with open(archive_dir / "mock_data_summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print("\n? Mock data generated successfully!")
    print(f"   Location: runs/{PIPELINE_VERSION}/{asset}/{run_id}/")
    print(f"   Trades: {len(trades_df)} ({trades_df['win'].mean() * 100:.1f}% win rate)")
    print(f"   Regime effect: {regime_effect}")

    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate mock data for v4.3 pipeline testing")
    parser.add_argument("--asset", default="ETH", help="Asset symbol")
    parser.add_argument("--run-id", default="mock_001", help="Run identifier")
    parser.add_argument("--n-bars", type=int, default=17520, help="Number of OHLCV bars")
    parser.add_argument("--n-trades", type=int, default=800, help="Number of trades")
    parser.add_argument("--no-regime-effect", action="store_true", help="Disable regime effect in trades")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")

    args = parser.parse_args()

    generate_all_mock_data(
        asset=args.asset,
        run_id=args.run_id,
        n_bars=args.n_bars,
        n_trades=args.n_trades,
        regime_effect=not args.no_regime_effect,
        seed=args.seed,
    )


if __name__ == "__main__":
    main()
