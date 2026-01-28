"""Select best coupled candidate for v4.2 baseline."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

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


def _score_from_metrics(metrics: dict) -> float:
    if "score" in metrics and metrics["score"] is not None:
        return float(metrics["score"])
    if "sharpe" in metrics and metrics["sharpe"] is not None:
        return float(metrics["sharpe"])
    if "sharpe_ratio" in metrics and metrics["sharpe_ratio"] is not None:
        return float(metrics["sharpe_ratio"])
    return 0.0


def main() -> None:
    parser = argparse.ArgumentParser(description="v4.2 baseline select")
    parser.add_argument("--asset", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--end-ts", default=None, help="Override research window end timestamp")
    args = parser.parse_args()

    cfg = load_yaml("configs/families.yaml")
    policy = get_policy(cfg)
    data_end_ts = _compute_research_end(cfg, policy, args.end_ts)

    run_root = get_run_root(args.asset, args.run_id)
    ensure_run_dirs(run_root)
    coupled_path = run_root / "coupling" / "coupled_candidates.json"
    coupled = json.loads(coupled_path.read_text())
    candidates = coupled.get("candidates", [])

    try:
        from crypto_backtest.v4.backtest_adapter import run_coupled_backtest
    except ModuleNotFoundError as exc:
        raise ImportError(
            "backtest_adapter.run_coupled_backtest not available (see PROMPT 13C)"
        ) from exc

    best = None
    best_score = float("-inf")
    for candidate in candidates:
        recipe_config = {
            "long_params": candidate["long"].get("params", {}),
            "short_params": candidate["short"].get("params", {}),
        }
        result = run_coupled_backtest(
            asset=args.asset,
            recipe_config=recipe_config,
            mode="combined",
            start_ts=None,
            end_ts=data_end_ts,
        )
        metrics = result.get("metrics", result)
        score = _score_from_metrics(metrics)
        if score > best_score:
            best_score = score
            best = {
                "best_couple_id": candidate.get("couple_id"),
                "long_params": recipe_config["long_params"],
                "short_params": recipe_config["short_params"],
                "metrics": metrics,
                "train_end_ts": data_end_ts,
            }

    if best is None:
        raise ValueError("No coupled candidates found for baseline selection")

    out_path = run_root / "baseline" / "baseline_best.json"
    out_path.write_text(json.dumps(best, indent=2, default=str))


if __name__ == "__main__":
    main()