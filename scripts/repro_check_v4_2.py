"""Reproducibility check for v4.2."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from crypto_backtest.v4.artifacts import get_run_root, ensure_run_dirs
from crypto_backtest.v4.config import load_yaml, get_policy
from crypto_backtest.v4.backtest_adapter import run_coupled_backtest


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


def _metrics_diff(m1: dict[str, Any], m2: dict[str, Any]) -> int:
    diff = 0
    keys = set(m1.keys()) | set(m2.keys())
    for key in keys:
        v1 = m1.get(key)
        v2 = m2.get(key)
        if v1 is None and v2 is None:
            continue
        try:
            if not np.isclose(float(v1), float(v2), equal_nan=True):
                diff += 1
        except Exception:
            if v1 != v2:
                diff += 1
    return diff


def main() -> None:
    parser = argparse.ArgumentParser(description="v4.2 reproducibility check")
    parser.add_argument("--asset", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--end-ts", default=None, help="Override research window end timestamp")
    args = parser.parse_args()

    cfg = load_yaml("configs/families.yaml")
    policy = get_policy(cfg)
    data_end_ts = _compute_research_end(cfg, policy, args.end_ts)

    run_root = get_run_root(args.asset, args.run_id)
    ensure_run_dirs(run_root)
    baseline_path = run_root / "baseline" / "baseline_best.json"
    baseline_best = json.loads(baseline_path.read_text())
    recipe_config = {
        "long_params": baseline_best.get("long_params", {}),
        "short_params": baseline_best.get("short_params", {}),
    }

    result1 = run_coupled_backtest(
        asset=args.asset,
        recipe_config=recipe_config,
        mode="combined",
        start_ts=None,
        end_ts=data_end_ts,
    )
    result2 = run_coupled_backtest(
        asset=args.asset,
        recipe_config=recipe_config,
        mode="combined",
        start_ts=None,
        end_ts=data_end_ts,
    )

    diff_count = 0

    br1 = np.asarray(result1.get("bar_returns", []), dtype=float)
    br2 = np.asarray(result2.get("bar_returns", []), dtype=float)
    if br1.shape != br2.shape or not np.allclose(br1, br2, equal_nan=True):
        diff_count += 1

    trades1 = result1.get("trades")
    trades2 = result2.get("trades")
    if trades1 is None or trades2 is None:
        diff_count += 1
    else:
        if not trades1.equals(trades2):
            diff_count += 1

    diff_count += _metrics_diff(result1.get("metrics", {}), result2.get("metrics", {}))

    payload = {"passed": diff_count == 0, "diff_count": diff_count}
    out_path = run_root / "archive" / "repro_check.json"
    out_path.write_text(json.dumps(payload, indent=2, default=str))


if __name__ == "__main__":
    main()