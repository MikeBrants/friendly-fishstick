"""Coupling step for v4.2 pipeline."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from crypto_backtest.v4.artifacts import get_run_root, ensure_run_dirs


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def build_coupled_matrix(
    asset: str,
    run_id: str,
    k_long: int,
    k_short: int,
    max_couples: int,
) -> Path:
    run_root = get_run_root(asset, run_id)
    ensure_run_dirs(run_root)

    screen_long = run_root / "screening" / "screen_long.json"
    screen_short = run_root / "screening" / "screen_short.json"
    long_data = _load_json(screen_long)
    short_data = _load_json(screen_short)

    long_candidates = long_data.get("top_candidates", [])[:k_long]
    short_candidates = short_data.get("top_candidates", [])[:k_short]

    candidates = []
    couple_id = 0
    for li, long_item in enumerate(long_candidates):
        for si, short_item in enumerate(short_candidates):
            candidates.append(
                {
                    "couple_id": f"L{li}_S{si}",
                    "long": long_item,
                    "short": short_item,
                }
            )
            couple_id += 1
            if couple_id >= max_couples:
                break
        if couple_id >= max_couples:
            break

    payload = {
        "method": "top_k_cross",
        "candidates": candidates,
    }
    out_path = run_root / "coupling" / "coupled_candidates.json"
    out_path.write_text(json.dumps(payload, indent=2, default=str))
    return out_path