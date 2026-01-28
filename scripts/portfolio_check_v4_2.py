"""Portfolio correlation check for v4.2."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from crypto_backtest.v4.artifacts import get_run_root, ensure_run_dirs
from crypto_backtest.v4.backtest_adapter import run_two_pass_backtest
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


def main() -> None:
    parser = argparse.ArgumentParser(description="v4.2 portfolio correlation check")
    parser.add_argument("--asset", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--end-ts", default=None, help="Override research window end timestamp")
    parser.add_argument("--debug", action="store_true", help="Print active bar counts for debugging")
    args = parser.parse_args()

    cfg = load_yaml("configs/families.yaml")
    policy = get_policy(cfg)
    port_cfg = policy.get("thresholds", {}).get("portfolio", {})

    corr_policy = port_cfg.get("corr_policy", "max_positive")
    threshold = float(port_cfg.get("corr_long_short_max", 0.50))
    ret_eps = float(port_cfg.get("ret_eps", 1e-12))
    active_bars_min = int(port_cfg.get("active_bars_min", 500))
    min_leg_active = int(port_cfg.get("min_leg_active_bars", 150))

    data_end_ts = _compute_research_end(cfg, policy, args.end_ts)

    run_root = get_run_root(args.asset, args.run_id)
    ensure_run_dirs(run_root)
    baseline_path = run_root / "baseline" / "baseline_best.json"
    baseline_best = json.loads(baseline_path.read_text())
    recipe_config = {
        "long_params": baseline_best.get("long_params", {}),
        "short_params": baseline_best.get("short_params", {}),
    }

    results = run_two_pass_backtest(
        asset=args.asset,
        recipe_config=recipe_config,
        start_ts=None,
        end_ts=data_end_ts,
    )

    long_returns = np.asarray(results["long"].get("bar_returns", []), dtype=float)
    short_returns = np.asarray(results["short"].get("bar_returns", []), dtype=float)

    min_len = min(len(long_returns), len(short_returns))
    if min_len == 0:
        payload = {
            "corr_policy": corr_policy,
            "active_union_bars": 0,
            "active_long_bars": int(np.sum(np.abs(long_returns) > ret_eps)),
            "active_short_bars": int(np.sum(np.abs(short_returns) > ret_eps)),
            "corr_union": None,
            "threshold": threshold,
            "passed": False,
            "reason": "NO_RETURNS",
        }
        (run_root / "portfolio" / "portfolio.json").write_text(json.dumps(payload, indent=2))
        return

    long_returns = long_returns[:min_len]
    short_returns = short_returns[:min_len]

    active_long = np.abs(long_returns) > ret_eps
    active_short = np.abs(short_returns) > ret_eps
    active_union = active_long | active_short

    active_union_bars = int(active_union.sum())
    active_long_bars = int(active_long.sum())
    active_short_bars = int(active_short.sum())
    if args.debug:
        print(
            f"[portfolio_check] active_long={active_long_bars} "
            f"active_short={active_short_bars} active_union={active_union_bars}"
        )
    if int(active_long.sum()) < min_leg_active or int(active_short.sum()) < min_leg_active:
        payload = {
            "corr_policy": corr_policy,
            "active_union_bars": active_union_bars,
            "active_long_bars": active_long_bars,
            "active_short_bars": active_short_bars,
            "corr_union": None,
            "threshold": threshold,
            "passed": False,
            "reason": "INSUFFICIENT_ACTIVE_BARS",
        }
        (run_root / "portfolio" / "portfolio.json").write_text(json.dumps(payload, indent=2))
        return

    if active_union_bars < active_bars_min:
        payload = {
            "corr_policy": corr_policy,
            "active_union_bars": active_union_bars,
            "active_long_bars": active_long_bars,
            "active_short_bars": active_short_bars,
            "corr_union": None,
            "threshold": threshold,
            "passed": False,
            "reason": "ACTIVE_UNION_TOO_SMALL",
        }
        (run_root / "portfolio" / "portfolio.json").write_text(json.dumps(payload, indent=2))
        return

    lr = long_returns[active_union]
    sr = short_returns[active_union]

    if np.std(lr) == 0 or np.std(sr) == 0:
        payload = {
            "corr_policy": corr_policy,
            "active_union_bars": active_union_bars,
            "active_long_bars": active_long_bars,
            "active_short_bars": active_short_bars,
            "corr_union": 0.0,
            "threshold": threshold,
            "passed": False,
            "reason": "ZERO_VARIANCE",
        }
        (run_root / "portfolio" / "portfolio.json").write_text(json.dumps(payload, indent=2))
        return

    corr_union = float(np.corrcoef(lr, sr)[0, 1])

    corr_for_pass = max(corr_union, 0.0) if corr_policy == "max_positive" else corr_union
    passed = corr_for_pass <= threshold
    reason = "PASS" if passed else "CORR_TOO_HIGH"

    payload = {
        "corr_policy": corr_policy,
        "active_union_bars": active_union_bars,
        "active_long_bars": active_long_bars,
        "active_short_bars": active_short_bars,
        "corr_union": corr_union,
        "threshold": threshold,
        "passed": passed,
        "reason": reason,
    }

    (run_root / "portfolio" / "portfolio.json").write_text(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
