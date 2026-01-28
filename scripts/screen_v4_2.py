"""Run v4.2 screening for long and short modes."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from crypto_backtest.v4.config import load_yaml, resolve_family, get_policy
from crypto_backtest.v4.screening import run_screening_long, run_screening_short


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
    parser = argparse.ArgumentParser(description="v4.2 screening (long/short)")
    parser.add_argument("--asset", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--family", default="A")
    parser.add_argument("--rescue", default=None)
    parser.add_argument("--end-ts", default=None, help="Override research window end timestamp")
    args = parser.parse_args()

    cfg = load_yaml("configs/families.yaml")
    policy = get_policy(cfg)
    family_cfg = resolve_family(cfg, args.family, args.rescue)
    data_end_ts = _compute_research_end(cfg, policy, args.end_ts)

    run_screening_long(args.asset, args.run_id, family_cfg, policy, data_end_ts)
    run_screening_short(args.asset, args.run_id, family_cfg, policy, data_end_ts)


if __name__ == "__main__":
    main()