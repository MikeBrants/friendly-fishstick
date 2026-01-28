"""Run calibrated PBO proxy + CSCV for v4.2."""
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


def _stack_returns_matrix(series_list: list[np.ndarray]) -> np.ndarray:
    if not series_list:
        return np.empty((0, 0), dtype=np.float32)
    lengths = {len(series) for series in series_list}
    min_len = min(lengths)
    stacked = np.stack([series[:min_len] for series in series_list], axis=0)
    return stacked.astype(np.float32, copy=False)


def _extract_bar_returns(result: dict[str, Any]) -> np.ndarray | None:
    if "bar_returns" in result and result["bar_returns"] is not None:
        return np.asarray(result["bar_returns"], dtype=float)
    if "returns" in result and result["returns"] is not None:
        return np.asarray(result["returns"], dtype=float)
    equity = result.get("equity_curve")
    if equity is not None:
        equity = np.asarray(equity, dtype=float)
        if equity.size < 2:
            return None
        prev = equity[:-1]
        diff = np.diff(equity)
        with np.errstate(divide="ignore", invalid="ignore"):
            returns = np.where(prev != 0, diff / prev, 0.0)
        return returns
    return None


def main() -> None:
    parser = argparse.ArgumentParser(description="v4.2 calibrated PBO runners")
    parser.add_argument("--asset", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--end-ts", default=None, help="Override research window end timestamp")
    args = parser.parse_args()

    cfg = load_yaml("configs/families.yaml")
    policy = get_policy(cfg)
    pbo_cfg = policy.get("pbo", {})
    proxy_cfg = pbo_cfg.get("proxy", {})
    cscv_cfg = pbo_cfg.get("cscv", {})

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

    returns_list: list[np.ndarray] = []
    warnings_list: list[str] = []

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
        returns = _extract_bar_returns(result)
        if returns is None:
            warnings_list.append("Missing bar_returns for candidate")
            continue
        returns_list.append(returns)

    returns_matrix = _stack_returns_matrix(returns_list)
    K = int(returns_matrix.shape[0])
    T = int(returns_matrix.shape[1])

    pbo_proxy_value = None
    pbo_cscv_value = None

    if K == 0 or T == 0:
        warnings_list.append("Empty returns matrix; PBO skipped")
    else:
        from crypto_backtest.validation.pbo_legacy import probability_of_backtest_overfitting
        from crypto_backtest.validation.pbo_cscv import cscv_pbo_compat

        try:
            proxy_result = probability_of_backtest_overfitting(
                returns_matrix,
                n_splits=int(proxy_cfg.get("folds", 8)),
                threshold=float(policy.get("thresholds", {}).get("pbo", {}).get("cscv_pass", 0.50)),
            )
            pbo_proxy_value = float(proxy_result.pbo)
            warnings_list.append("proxy_pbo ignores purge/embargo")
        except Exception as exc:  # pragma: no cover - defensive
            warnings_list.append(f"proxy_pbo failed: {exc}")

        try:
            cscv_result = cscv_pbo_compat(
                returns_matrix,
                folds=int(cscv_cfg.get("folds", 10)),
                purge_bars=int(cscv_cfg.get("purge_bars", 120)),
                embargo_bars=int(cscv_cfg.get("embargo_bars", 240)),
                annualization_factor=float(pbo_cfg.get("annualization_factor", 8760)),
            )
            pbo_cscv_value = float(cscv_result.get("pbo"))
        except Exception as exc:  # pragma: no cover - defensive
            warnings_list.append(f"cscv_pbo failed: {exc}")

    proxy_payload = {
        "K": K,
        "T": T,
        "folds": int(proxy_cfg.get("folds", 8)),
        "purge_bars": int(proxy_cfg.get("purge_bars", 120)),
        "embargo_bars": int(proxy_cfg.get("embargo_bars", 240)),
        "pbo": pbo_proxy_value,
        "warnings": warnings_list,
    }

    cscv_payload = {
        "K": K,
        "T": T,
        "folds": int(cscv_cfg.get("folds", 10)),
        "purge_bars": int(cscv_cfg.get("purge_bars", 120)),
        "embargo_bars": int(cscv_cfg.get("embargo_bars", 240)),
        "pbo": pbo_cscv_value,
        "warnings": warnings_list,
    }

    (run_root / "pbo" / "pbo_proxy.json").write_text(json.dumps(proxy_payload, indent=2, default=str))
    (run_root / "pbo" / "pbo_cscv.json").write_text(json.dumps(cscv_payload, indent=2, default=str))


if __name__ == "__main__":
    main()