"""Run v4.2 hard guards for baseline selection."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from crypto_backtest.v4.artifacts import get_run_root, ensure_run_dirs
from crypto_backtest.v4.config import load_yaml, get_policy


def _safe_float(value: object) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _load_baseline_metrics(baseline_best: dict) -> dict:
    metrics = baseline_best.get("metrics", {}) or {}
    sharpe = _safe_float(metrics.get("sharpe_ratio") or metrics.get("sharpe"))
    max_dd = _safe_float(metrics.get("max_drawdown"))
    if max_dd is not None:
        max_dd = abs(max_dd)
    profit_factor = _safe_float(metrics.get("profit_factor"))

    return {
        "bars": _safe_float(
            baseline_best.get("bars")
            or metrics.get("bars")
            or metrics.get("n_bars")
            or metrics.get("total_bars")
        ),
        "trades": _safe_float(
            baseline_best.get("oos_trades")
            or baseline_best.get("trade_count")
            or metrics.get("trades")
            or metrics.get("n_trades")
            or metrics.get("total_trades")
        ),
        "sharpe": sharpe,
        "max_drawdown": max_dd,
        "profit_factor": profit_factor,
        "wfe": _safe_float(baseline_best.get("wfe") or metrics.get("wfe") or metrics.get("wfe_pardo")),
        "wfe_median": _safe_float(
            baseline_best.get("wfe_median")
            or metrics.get("wfe_median")
            or baseline_best.get("wfe_median_split")
            or metrics.get("wfe_median_split")
        ),
        "top10_concentration": _safe_float(
            baseline_best.get("top10_concentration")
            or metrics.get("top10_concentration")
            or metrics.get("top10_pct")
            or metrics.get("guard005_top10_pct")
        ),
    }


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
    
    # v4.3: Dual WFE threshold (mean AND median)
    wfe_cfg = guards_cfg.get("wfe", {})
    if isinstance(wfe_cfg, dict):
        wfe_mean_min = float(wfe_cfg.get("mean_min", 0.60))
        wfe_median_min = float(wfe_cfg.get("median_min", 0.50))
    else:
        # Fallback for old config
        wfe_mean_min = float(baseline.get("wfe_min", 0.60))
        wfe_median_min = 0.50

    sharpe_min = float(guards_cfg.get("sharpe_min", 0.80))
    max_dd_max = float(guards_cfg.get("max_drawdown_max", 0.35))
    pf_min = float(guards_cfg.get("profit_factor_min", 1.05))
    top10_max = 40.0

    run_root = get_run_root(args.asset, args.run_id)
    ensure_run_dirs(run_root)
    baseline_path = run_root / "baseline" / "baseline_best.json"
    baseline_best = json.loads(baseline_path.read_text())
    metrics = _load_baseline_metrics(baseline_best)

    bars = metrics.get("bars")
    trades = metrics.get("trades")
    sharpe = metrics.get("sharpe")
    max_dd = metrics.get("max_drawdown")
    pf = metrics.get("profit_factor")
    wfe_mean = metrics.get("wfe")
    wfe_median = metrics.get("wfe_median")
    top10 = metrics.get("top10_concentration")

    # v4.3: Dual WFE guard (mean AND median)
    wfe_mean_passed = wfe_mean is not None and wfe_mean >= wfe_mean_min
    wfe_median_passed = wfe_median is not None and wfe_median >= wfe_median_min
    wfe_passed = wfe_mean_passed and wfe_median_passed
    
    wfe_reason = f"mean={wfe_mean:.2f}" if wfe_mean is not None else "mean=N/A"
    if wfe_median is not None:
        wfe_reason += f", median={wfe_median:.2f}"
    else:
        wfe_reason += ", median=N/A"

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
            "name": "WFE",
            "passed": wfe_passed,
            "value": {"mean": wfe_mean, "median": wfe_median},
            "threshold": {"mean_min": wfe_mean_min, "median_min": wfe_median_min},
            "reason": wfe_reason,
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
