"""Validate v4.2 YAML configs."""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import yaml


REQUIRED_FILES = [
    Path("configs/families.yaml"),
    Path("configs/router.yaml"),
]


def load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text())
    return data or {}


def require_keys(node: dict[str, Any], keys: list[str], context: str, errors: list[str]) -> None:
    for key in keys:
        if key not in node:
            errors.append(f"Missing key '{key}' in {context}")


def validate_families(cfg: dict[str, Any], errors: list[str]) -> None:
    meta = cfg.get("meta", {})
    if meta.get("version") != "4.2":
        errors.append("families.yaml meta.version must be '4.2'")

    policy = cfg.get("policy", {})
    thresholds = policy.get("thresholds", {})
    require_keys(
        thresholds,
        [
            "screening",
            "baseline_by_filter_preset",
            "guards",
            "pbo",
            "regime",
            "portfolio",
            "holdout",
        ],
        "policy.thresholds",
        errors,
    )

    pbo = policy.get("pbo", {})
    require_keys(pbo, ["proxy", "cscv"], "policy.pbo", errors)
    proxy = pbo.get("proxy", {})
    cscv = pbo.get("cscv", {})
    require_keys(proxy, ["folds", "purge_bars", "embargo_bars"], "policy.pbo.proxy", errors)
    require_keys(cscv, ["folds", "purge_bars", "embargo_bars"], "policy.pbo.cscv", errors)

    portfolio = thresholds.get("portfolio", {})
    require_keys(
        portfolio,
        ["corr_policy", "corr_scope", "ret_eps", "active_bars_min"],
        "policy.thresholds.portfolio",
        errors,
    )

    holdout = policy.get("data", {}).get("holdout", {})
    require_keys(holdout, ["enabled", "months", "mode"], "policy.data.holdout", errors)


def validate_router(cfg: dict[str, Any], errors: list[str]) -> None:
    meta = cfg.get("meta", {})
    if meta.get("version") != "4.2":
        errors.append("router.yaml meta.version must be '4.2'")

    states = cfg.get("states")
    if not isinstance(states, list) or not states:
        errors.append("router.yaml states must be a non-empty list")
        return

    state_set = set(states)
    transitions = cfg.get("transitions", {})
    if not isinstance(transitions, dict):
        errors.append("router.yaml transitions must be a mapping")
        return

    for from_state, edges in transitions.items():
        if from_state not in state_set:
            errors.append(f"transition from unknown state '{from_state}'")
        if not isinstance(edges, list):
            errors.append(f"transitions for '{from_state}' must be a list")
            continue
        for edge in edges:
            if not isinstance(edge, dict):
                errors.append(f"transition edge in '{from_state}' must be a mapping")
                continue
            target = edge.get("then")
            if target is not None and target not in state_set:
                errors.append(f"transition from '{from_state}' to unknown state '{target}'")


def main() -> int:
    errors: list[str] = []

    for path in REQUIRED_FILES:
        if not path.exists():
            errors.append(f"Missing required config file: {path.as_posix()}")

    if errors:
        print("FAIL")
        for err in errors:
            print(f"- {err}")
        return 1

    families_cfg = load_yaml(REQUIRED_FILES[0])
    router_cfg = load_yaml(REQUIRED_FILES[1])

    validate_families(families_cfg, errors)
    validate_router(router_cfg, errors)

    if errors:
        print("FAIL")
        for err in errors:
            print(f"- {err}")
        return 1

    print("PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())