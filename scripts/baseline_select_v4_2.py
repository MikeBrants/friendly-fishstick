"""Select best coupled candidate for v4.2 baseline."""
from __future__ import annotations

import argparse
import json
import statistics
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from crypto_backtest.optimization.parallel_optimizer import load_data
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


def _extract_sharpe(metrics: dict) -> float:
    if metrics.get("sharpe") is not None:
        return float(metrics["sharpe"])
    if metrics.get("sharpe_ratio") is not None:
        return float(metrics["sharpe_ratio"])
    return 0.0


def _trade_count_from_result(result: dict) -> int:
    if result.get("trade_count") is not None:
        return int(result["trade_count"])
    trades = result.get("trades")
    if trades is None:
        return 0
    try:
        return int(len(trades))
    except TypeError:
        return 0


def _walk_forward_stats(
    asset: str,
    recipe_config: dict,
    data_index: pd.Index,
    n_splits: int,
    train_ratio: float,
    run_coupled_backtest,
) -> dict:
    n = len(data_index)
    if n < 4 or n_splits <= 0:
        return {
            "wfe": 0.0,
            "wfe_mean_split": 0.0,
            "wfe_median": 0.0,
            "wfe_trimmed": 0.0,
            "wfe_splits": [],
            "wfe_skew_ratio": None,
            "wfe_warnings": [],
            "oos_sharpe": 0.0,
            "oos_trades": 0,
            "is_trades": 0,
            "splits": 0,
        }

    train_size = int(n * train_ratio)
    remaining = n - train_size
    if train_size < 2 or remaining < 2:
        return {
            "wfe": 0.0,
            "wfe_mean_split": 0.0,
            "wfe_median": 0.0,
            "wfe_trimmed": 0.0,
            "wfe_splits": [],
            "wfe_skew_ratio": None,
            "wfe_warnings": [],
            "oos_sharpe": 0.0,
            "oos_trades": 0,
            "is_trades": 0,
            "splits": 0,
        }

    split_size = remaining // n_splits
    if split_size < 2:
        return {
            "wfe": 0.0,
            "wfe_mean_split": 0.0,
            "wfe_median": 0.0,
            "wfe_trimmed": 0.0,
            "wfe_splits": [],
            "wfe_skew_ratio": None,
            "wfe_warnings": [],
            "oos_sharpe": 0.0,
            "oos_trades": 0,
            "is_trades": 0,
            "splits": 0,
        }

    is_sharpes: list[float] = []
    oos_sharpes: list[float] = []
    wfe_splits: list[float] = []
    is_trades = 0
    oos_trades = 0
    splits_run = 0

    for split_id in range(n_splits):
        train_end_idx = train_size + split_id * split_size
        test_end_idx = train_end_idx + split_size
        if test_end_idx > n:
            break

        train_end_ts = data_index[train_end_idx - 1]
        test_start_ts = data_index[train_end_idx]
        test_end_ts = data_index[test_end_idx - 1]

        is_result = run_coupled_backtest(
            asset=asset,
            recipe_config=recipe_config,
            mode="combined",
            start_ts=None,
            end_ts=pd.Timestamp(train_end_ts).isoformat(),
        )
        oos_result = run_coupled_backtest(
            asset=asset,
            recipe_config=recipe_config,
            mode="combined",
            start_ts=pd.Timestamp(test_start_ts).isoformat(),
            end_ts=pd.Timestamp(test_end_ts).isoformat(),
        )

        is_metrics = is_result.get("metrics", {})
        oos_metrics = oos_result.get("metrics", {})

        is_sharpe = _extract_sharpe(is_metrics)
        oos_sharpe = _extract_sharpe(oos_metrics)
        is_sharpes.append(is_sharpe)
        oos_sharpes.append(oos_sharpe)
        wfe_split = oos_sharpe / is_sharpe if is_sharpe > 0 else 0.0
        wfe_splits.append(float(wfe_split))
        is_trades += _trade_count_from_result(is_result)
        oos_trades += _trade_count_from_result(oos_result)
        splits_run += 1

    mean_is = float(np.mean(is_sharpes)) if is_sharpes else 0.0
    mean_oos = float(np.mean(oos_sharpes)) if oos_sharpes else 0.0
    wfe = mean_oos / mean_is if mean_is > 0 else 0.0
    wfe_mean_split = statistics.mean(wfe_splits) if wfe_splits else 0.0
    wfe_median = statistics.median(wfe_splits) if wfe_splits else 0.0
    if len(wfe_splits) > 2:
        trimmed = sorted(wfe_splits)[1:-1]
        wfe_trimmed = statistics.mean(trimmed) if trimmed else wfe_mean_split
    else:
        wfe_trimmed = wfe_mean_split

    wfe_skew_ratio = None
    wfe_warnings: list[str] = []
    if wfe_median not in (0.0, 0):
        wfe_skew_ratio = abs(wfe_mean_split - wfe_median) / abs(wfe_median)
        if wfe_skew_ratio > 0.5:
            wfe_warnings.append("WFE_SKEWED")

    return {
        "wfe": wfe,
        "wfe_mean_split": wfe_mean_split,
        "wfe_median": wfe_median,
        "wfe_trimmed": wfe_trimmed,
        "wfe_splits": wfe_splits,
        "wfe_skew_ratio": wfe_skew_ratio,
        "wfe_warnings": wfe_warnings,
        "oos_sharpe": mean_oos,
        "oos_trades": int(oos_trades),
        "is_trades": int(is_trades),
        "splits": splits_run,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="v4.2 baseline select")
    parser.add_argument("--asset", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--end-ts", default=None, help="Override research window end timestamp")
    args = parser.parse_args()

    cfg = load_yaml("configs/families.yaml")
    policy = get_policy(cfg)
    data_end_ts = _compute_research_end(cfg, policy, args.end_ts)

    data = load_data(args.asset, data_dir="data")
    if data_end_ts:
        data = data.loc[: pd.to_datetime(data_end_ts)]
    data_index = data.index

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
    best_result = None
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
            best_result = result

    if best is None:
        raise ValueError("No coupled candidates found for baseline selection")

    wf_stats = _walk_forward_stats(
        asset=args.asset,
        recipe_config={
            "long_params": best["long_params"],
            "short_params": best["short_params"],
        },
        data_index=data_index,
        n_splits=5,
        train_ratio=0.6,
        run_coupled_backtest=run_coupled_backtest,
    )

    bars_total = cfg.get("dataset", {}).get("bars_total")
    if bars_total is None:
        bars_total = int(len(data_index))

    best.update(
        {
            "wfe": wf_stats.get("wfe"),
            "wfe_mean_split": wf_stats.get("wfe_mean_split"),
            "wfe_median": wf_stats.get("wfe_median"),
            "wfe_trimmed": wf_stats.get("wfe_trimmed"),
            "wfe_splits": wf_stats.get("wfe_splits"),
            "wfe_skew_ratio": wf_stats.get("wfe_skew_ratio"),
            "wfe_warnings": wf_stats.get("wfe_warnings"),
            "oos_sharpe": wf_stats.get("oos_sharpe"),
            "oos_trades": wf_stats.get("oos_trades"),
            "is_trades": wf_stats.get("is_trades"),
            "trade_count": _trade_count_from_result(best_result or {}),
            "bars": int(bars_total),
            "top10_concentration": (best_result or {}).get("top10_concentration", 0.0),
        }
    )

    out_path = run_root / "baseline" / "baseline_best.json"
    out_path.write_text(json.dumps(best, indent=2, default=str))


if __name__ == "__main__":
    main()
