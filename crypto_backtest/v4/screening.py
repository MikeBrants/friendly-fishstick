"""Screening for v4.2 long/short candidate generation."""
from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Any

from crypto_backtest.v4.artifacts import get_run_root, ensure_run_dirs


TRIALS = 100
TOP_K = 20
DEFAULT_SEED = 42


def _sample_float(rng: random.Random, low: float, high: float, step: float) -> float:
    steps = int(round((high - low) / step))
    return round(low + step * rng.randint(0, steps), 4)


def _sample_int(rng: random.Random, low: int, high: int) -> int:
    return int(rng.randint(low, high))


def _sample_params(rng: random.Random, family_cfg: dict[str, Any]) -> dict[str, Any]:
    from crypto_backtest.config.scan_assets import ATR_SEARCH_SPACE, ICHI_SEARCH_SPACE

    for _ in range(1000):
        sl = _sample_float(rng, *ATR_SEARCH_SPACE["sl_mult"], step=0.25)
        tp1 = _sample_float(rng, *ATR_SEARCH_SPACE["tp1_mult"], step=0.25)
        tp2 = _sample_float(rng, *ATR_SEARCH_SPACE["tp2_mult"], step=0.5)
        tp3 = _sample_float(rng, *ATR_SEARCH_SPACE["tp3_mult"], step=0.5)
        if tp1 < tp2 < tp3:
            break
    else:
        tp1, tp2, tp3 = sorted([tp1, tp2, tp3])

    tenkan = _sample_int(rng, *ICHI_SEARCH_SPACE["tenkan"])
    kijun = _sample_int(rng, *ICHI_SEARCH_SPACE["kijun"])
    tenkan_5 = _sample_int(rng, *ICHI_SEARCH_SPACE["tenkan_5"])
    kijun_5 = _sample_int(rng, *ICHI_SEARCH_SPACE["kijun_5"])

    displacement = 52
    displacement_cfg = family_cfg.get("displacement", {})
    if displacement_cfg.get("enabled") and displacement_cfg.get("values"):
        displacement = rng.choice(displacement_cfg["values"])

    params = {
        "sl_mult": sl,
        "tp1_mult": tp1,
        "tp2_mult": tp2,
        "tp3_mult": tp3,
        "tenkan": tenkan,
        "kijun": kijun,
        "tenkan_5": tenkan_5,
        "kijun_5": kijun_5,
        "displacement": displacement,
    }

    preset = family_cfg.get("filters", {}).get("preset")
    if preset:
        params["filter_preset"] = preset

    return params


def _run_trial(
    asset: str,
    params: dict[str, Any],
    mode: str,
    start_ts: str | None,
    end_ts: str | None,
) -> dict[str, Any]:
    try:
        from crypto_backtest.v4.backtest_adapter import run_coupled_backtest
    except ModuleNotFoundError as exc:
        raise ImportError(
            "backtest_adapter.run_coupled_backtest not available (see PROMPT 13C)"
        ) from exc

    result = run_coupled_backtest(
        asset=asset,
        recipe_config=params,
        mode=mode,
        start_ts=start_ts,
        end_ts=end_ts,
    )
    metrics = result.get("metrics", result)
    score = result.get("score")
    if score is None:
        score = metrics.get("sharpe")
        if score is None:
            score = metrics.get("sharpe_ratio", 0.0)
    return {
        "params": params,
        "metrics": metrics,
        "score": float(score) if score is not None else 0.0,
    }


def _run_screening(
    asset: str,
    run_id: str,
    family_cfg: dict[str, Any],
    mode: str,
    data_end_ts: str | None,
    seed: int = DEFAULT_SEED,
) -> dict[str, Any]:
    rng = random.Random(seed)
    candidates = []
    for _ in range(TRIALS):
        params = _sample_params(rng, family_cfg)
        candidate = _run_trial(asset, params, mode, None, data_end_ts)
        candidates.append(candidate)

    top_candidates = sorted(candidates, key=lambda c: c.get("score", 0.0), reverse=True)[:TOP_K]
    return {
        "trials": TRIALS,
        "seed": seed,
        "top_candidates": top_candidates,
    }


def run_screening_long(
    asset: str,
    run_id: str,
    family_cfg: dict[str, Any],
    policy_cfg: dict[str, Any],
    data_end_ts: str | None,
) -> Path:
    run_root = get_run_root(asset, run_id)
    ensure_run_dirs(run_root)
    payload = _run_screening(
        asset,
        run_id,
        family_cfg,
        mode="long_only",
        data_end_ts=data_end_ts,
        seed=policy_cfg.get("random_seed", DEFAULT_SEED),
    )
    out_path = run_root / "screening" / "screen_long.json"
    out_path.write_text(json.dumps(payload, indent=2, default=str))
    return out_path


def run_screening_short(
    asset: str,
    run_id: str,
    family_cfg: dict[str, Any],
    policy_cfg: dict[str, Any],
    data_end_ts: str | None,
) -> Path:
    run_root = get_run_root(asset, run_id)
    ensure_run_dirs(run_root)
    payload = _run_screening(
        asset,
        run_id,
        family_cfg,
        mode="short_only",
        data_end_ts=data_end_ts,
        seed=policy_cfg.get("random_seed", DEFAULT_SEED),
    )
    out_path = run_root / "screening" / "screen_short.json"
    out_path.write_text(json.dumps(payload, indent=2, default=str))
    return out_path