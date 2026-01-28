"""Compute regime stats (stats-only) for v4.2."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from crypto_backtest.analysis.regime import classify_regimes_v2
from crypto_backtest.engine.backtest import BacktestConfig, VectorizedBacktester
from crypto_backtest.optimization.bayesian import _instantiate_strategy
from crypto_backtest.optimization.parallel_optimizer import load_data
from crypto_backtest.strategies.final_trigger import FinalTriggerStrategy
from crypto_backtest.v4.artifacts import get_run_root, ensure_run_dirs
from crypto_backtest.v4.config import load_yaml, get_policy


def _compute_research_end(cfg: dict, policy: dict, override_end: str | None) -> str | None:
    if override_end:
        return override_end
    dataset_end = cfg.get("dataset", {}).get("end_utc")
    if not dataset_end:
        return None
    end_ts = pd.to_datetime(dataset_end)
    holdout = policy.get("data", {}).get("holdout", {})
    if holdout.get("enabled"):
        months = int(holdout.get("months", 0))
        if months > 0:
            end_ts = end_ts - pd.DateOffset(months=months)
    return end_ts.isoformat()


def _select_params(baseline_best: dict) -> dict:
    if baseline_best.get("long_params"):
        return baseline_best["long_params"]
    if baseline_best.get("params"):
        return baseline_best["params"]
    if baseline_best.get("short_params"):
        return baseline_best["short_params"]
    return {}


def _normalize_params(params: dict) -> dict:
    if "ichimoku" in params or "five_in_one" in params:
        return params
    displacement = params.get("displacement", 52)
    return {
        "sl_mult": params.get("sl_mult", 3.0),
        "tp1_mult": params.get("tp1_mult", 2.0),
        "tp2_mult": params.get("tp2_mult", 6.0),
        "tp3_mult": params.get("tp3_mult", 10.0),
        "ichimoku": {
            "tenkan": params.get("tenkan", 9),
            "kijun": params.get("kijun", 26),
            "displacement": displacement,
        },
        "five_in_one": {
            "tenkan_5": params.get("tenkan_5", 9),
            "kijun_5": params.get("kijun_5", 26),
            "displacement_5": params.get("displacement_5", displacement),
        },
    }


def _win_rate(trades: pd.DataFrame) -> float:
    if trades.empty:
        return 0.0
    for col in ("pnl", "net_pnl", "gross_pnl"):
        if col in trades.columns:
            pnl = trades[col].astype(float)
            return float((pnl > 0).mean())
    return 0.0


def main() -> None:
    parser = argparse.ArgumentParser(description="v4.2 regime stats")
    parser.add_argument("--asset", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--end-ts", default=None, help="Override research window end timestamp")
    args = parser.parse_args()

    cfg = load_yaml("configs/families.yaml")
    policy = get_policy(cfg)
    regime_cfg = policy.get("thresholds", {}).get("regime", {})
    n_trades_min = int(regime_cfg.get("n_trades_min", 30))
    signal_delta = float(regime_cfg.get("signal_threshold_wr_delta", 0.15))

    data_end_ts = _compute_research_end(cfg, policy, args.end_ts)

    run_root = get_run_root(args.asset, args.run_id)
    ensure_run_dirs(run_root)
    baseline_path = run_root / "baseline" / "baseline_best.json"
    baseline_best = json.loads(baseline_path.read_text())

    params = _normalize_params(_select_params(baseline_best))

    data = load_data(args.asset, data_dir="data")
    if data_end_ts:
        data = data.loc[:pd.to_datetime(data_end_ts)]

    strategy = _instantiate_strategy(FinalTriggerStrategy, params)
    backtester = VectorizedBacktester(BacktestConfig())
    result = backtester.run(data, strategy)
    trades = result.trades

    regimes = classify_regimes_v2(data)
    if not trades.empty and "entry_time" in trades.columns:
        entry_times = pd.to_datetime(trades["entry_time"], utc=True)
        regime_at_entry = regimes.reindex(entry_times).fillna("OTHER")
        trades = trades.copy()
        trades["regime"] = regime_at_entry.to_numpy()
    else:
        trades = trades.copy()
        trades["regime"] = "OTHER"

    wr_by_regime = {}
    counts = {}
    for label in ("BULL", "BEAR", "SIDEWAYS"):
        subset = trades[trades["regime"] == label]
        wr_by_regime[label.lower()] = _win_rate(subset)
        counts[label.lower()] = int(len(subset))

    eligible = [wr_by_regime[k] for k in ("bull", "bear", "sideways") if counts[k] >= n_trades_min]
    if len(eligible) >= 2:
        delta_wr = max(eligible) - min(eligible)
        regime_signal_detected = delta_wr >= signal_delta
    else:
        delta_wr = 0.0
        regime_signal_detected = False

    payload = {
        "wr_by_regime": wr_by_regime,
        "delta_wr": float(delta_wr),
        "regime_signal_detected": bool(regime_signal_detected),
    }

    out_path = run_root / "regime" / "regime.json"
    out_path.write_text(json.dumps(payload, indent=2, default=str))


if __name__ == "__main__":
    main()