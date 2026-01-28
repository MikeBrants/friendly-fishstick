"""Run v4.2 hard guards for baseline selection."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from crypto_backtest.v4.artifacts import get_run_root, ensure_run_dirs
from crypto_backtest.v4.config import load_yaml, get_policy


def _get_metric(metrics: dict, keys: list[str]) -> float | None:
    for key in keys:
        value = metrics.get(key)
        if value is not None:
            return float(value)
    return None


def main() -> None:
    parser = argparse.ArgumentParser(description="v4.2 guards runner")
    parser.add_argument("--asset", required=True)
    parser.add_argument("--run-id", required=True)
    args = parser.parse_args()

    cfg = load_yaml("configs/families.yaml")
    policy = get_policy(cfg)
    thresholds = policy.get("thresholds", {})
    baseline = thresholds.get("baseline_by_filter_preset", {}).get("baseline", {})
    guards_cfg = thresholds.get("guards", {})

    bars_min = float(baseline.get("bars_min", 12000))
    trades_min = float(baseline.get("trades_min", 60))
    wfe_min = float(baseline.get("wfe_min", 0.60))

    sharpe_min = float(guards_cfg.get("sharpe_min", 0.80))
    max_dd_max = float(guards_cfg.get("max_drawdown_max", 0.35))
    pf_min = float(guards_cfg.get("profit_factor_min", 1.05))
    top10_max = 40.0

    run_root = get_run_root(args.asset, args.run_id)
    ensure_run_dirs(run_root)
    baseline_path = run_root / "baseline" / "baseline_best.json"
    baseline_best = json.loads(baseline_path.read_text())
    metrics = baseline_best.get("metrics", {})

    bars = _get_metric(metrics, ["bars", "n_bars", "total_bars"])
    trades = _get_metric(metrics, ["trades", "n_trades", "total_trades"])
    sharpe = _get_metric(metrics, ["sharpe", "sharpe_ratio"])
    max_dd = _get_metric(metrics, ["max_drawdown", "max_dd"])
    pf = _get_metric(metrics, ["profit_factor", "pf"])
    wfe = _get_metric(metrics, ["wfe", "wfe_pardo"])
    top10 = _get_metric(metrics, ["top10_concentration", "top10_pct", "guard005_top10_pct"])

    guards = [
        {"name": "bars", "passed": bars is not None and bars >= bars_min, "value": bars, "threshold": bars_min},
        {
            "name": "trades",
            "passed": trades is not None and trades >= trades_min,
            "value": trades,
            "threshold": trades_min,
        },
        {
            "name": "sharpe",
            "passed": sharpe is not None and sharpe >= sharpe_min,
            "value": sharpe,
            "threshold": sharpe_min,
        },
        {
            "name": "max_drawdown",
            "passed": max_dd is not None and max_dd <= max_dd_max,
            "value": max_dd,
            "threshold": max_dd_max,
        },
        {
            "name": "profit_factor",
            "passed": pf is not None and pf >= pf_min,
            "value": pf,
            "threshold": pf_min,
        },
        {
            "name": "wfe",
            "passed": wfe is not None and wfe >= wfe_min,
            "value": wfe,
            "threshold": wfe_min,
        },
        {
            "name": "top10_concentration",
            "passed": top10 is not None and top10 < top10_max,
            "value": top10,
            "threshold": top10_max,
        },
    ]

    failed = sum(1 for guard in guards if not guard["passed"])
    catastrophic = failed >= 3
    payload = {
        "passed": failed == 0,
        "failed": failed,
        "catastrophic": catastrophic,
        "guards": guards,
    }

    out_path = run_root / "guards" / "guards.json"
    out_path.write_text(json.dumps(payload, indent=2, default=str))


if __name__ == "__main__":
    main()