"""Print resolved family configuration from configs/families.yaml."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import yaml


def deep_merge(base: Any, overlay: Any) -> Any:
    if isinstance(base, dict) and isinstance(overlay, dict):
        merged = {k: deep_merge(base.get(k), v) for k, v in overlay.items()}
        for key, value in base.items():
            if key not in merged:
                merged[key] = value
        return merged
    return overlay if overlay is not None else base


def resolve_family(families_cfg: dict[str, Any], family_id: str) -> dict[str, Any]:
    if family_id not in families_cfg:
        raise KeyError(f"Unknown family_id: {family_id}")
    family = dict(families_cfg[family_id])
    parent_id = family.pop("inherits", None)
    if parent_id:
        base = resolve_family(families_cfg, parent_id)
        return deep_merge(base, family)
    return family


def apply_rescue(resolved: dict[str, Any], rescue_cfg: dict[str, Any]) -> dict[str, Any]:
    result = deep_merge(resolved, {})
    if rescue_cfg.get("type") == "filter_preset" and rescue_cfg.get("preset"):
        filters = dict(result.get("filters", {}))
        filters["preset"] = rescue_cfg["preset"]
        result["filters"] = filters
    result["rescue"] = rescue_cfg
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Print resolved family config")
    parser.add_argument(
        "--config",
        default="configs/families.yaml",
        help="Path to families.yaml",
    )
    parser.add_argument("--family", default=None, help="Family id (e.g., A/B/C)")
    parser.add_argument("--rescue", default=None, help="Rescue id (e.g., R1/R2)")
    args = parser.parse_args()

    path = Path(args.config)
    cfg = yaml.safe_load(path.read_text())

    if args.family:
        resolved = resolve_family(cfg.get("families", {}), args.family)
        if args.rescue:
            rescue_cfg = cfg.get("rescues", {}).get(args.rescue)
            if rescue_cfg is None:
                raise KeyError(f"Unknown rescue_id: {args.rescue}")
            resolved = apply_rescue(resolved, rescue_cfg)
        print(json.dumps(resolved, indent=2, sort_keys=True))
    else:
        print(json.dumps(cfg, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
