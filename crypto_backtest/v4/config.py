"""Config utilities for v4 pipeline."""
from __future__ import annotations

import copy
from pathlib import Path
from typing import Any

import yaml


def load_yaml(path: str | Path) -> dict[str, Any]:
    data = yaml.safe_load(Path(path).read_text())
    return data or {}


def deep_merge(base: Any, overlay: Any) -> Any:
    if isinstance(base, dict) and isinstance(overlay, dict):
        merged: dict[str, Any] = {k: deep_merge(base.get(k), v) for k, v in overlay.items()}
        for key, value in base.items():
            if key not in merged:
                merged[key] = copy.deepcopy(value)
        return merged
    if overlay is not None:
        return copy.deepcopy(overlay)
    return copy.deepcopy(base)


def resolve_family(
    families_cfg: dict[str, Any],
    family_id: str,
    rescue_id: str | None = None,
) -> dict[str, Any]:
    families = families_cfg.get("families", families_cfg)
    rescues = families_cfg.get("rescues", {})

    if family_id not in families:
        raise KeyError(f"Unknown family_id: {family_id}")

    def _resolve(fid: str) -> dict[str, Any]:
        family = copy.deepcopy(families[fid])
        parent_id = family.pop("inherits", None)
        if parent_id:
            base = _resolve(parent_id)
            return deep_merge(base, family)
        return family

    resolved = _resolve(family_id)

    if rescue_id:
        rescue_cfg = rescues.get(rescue_id)
        if rescue_cfg is None:
            raise KeyError(f"Unknown rescue_id: {rescue_id}")
        if rescue_cfg.get("type") == "filter_preset" and rescue_cfg.get("preset"):
            filters = deep_merge(resolved.get("filters", {}), {"preset": rescue_cfg["preset"]})
            resolved = deep_merge(resolved, {"filters": filters})
        resolved = deep_merge(resolved, {"rescue": copy.deepcopy(rescue_cfg)})

    return resolved


def get_policy(cfg: dict[str, Any]) -> dict[str, Any]:
    return copy.deepcopy(cfg.get("policy", {}))


def get_thresholds(cfg: dict[str, Any]) -> dict[str, Any]:
    return copy.deepcopy(cfg.get("policy", {}).get("thresholds", {}))
