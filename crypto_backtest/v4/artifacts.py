"""Artifacts utilities for v4.2 runs."""
from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SUBDIRS = [
    "config_snapshot",
    "screening",
    "coupling",
    "baseline",
    "guards",
    "pbo",
    "regime",
    "portfolio",
    "holdout",
    "archive",
]


def get_run_root(asset: str, run_id: str) -> Path:
    return Path("runs") / "v4_2" / asset / run_id


def ensure_run_dirs(run_root: Path) -> dict[str, Path]:
    run_root.mkdir(parents=True, exist_ok=True)
    subpaths = {name: run_root / name for name in SUBDIRS}
    for path in subpaths.values():
        path.mkdir(parents=True, exist_ok=True)
    return subpaths


def write_run_metadata(run_root: Path, metadata_dict: dict[str, Any]) -> Path:
    run_root.mkdir(parents=True, exist_ok=True)
    path = run_root / "run_metadata.json"
    payload = dict(metadata_dict)
    if "created_utc" not in payload:
        payload["created_utc"] = datetime.now(timezone.utc).isoformat()
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, default=str)
    return path


def snapshot_configs(run_root: Path, families_path: str | Path, router_path: str | Path) -> Path:
    snapshot_dir = run_root / "config_snapshot"
    snapshot_dir.mkdir(parents=True, exist_ok=True)

    for src in (Path(families_path), Path(router_path)):
        if src.exists():
            shutil.copy2(src, snapshot_dir / src.name)
    return snapshot_dir