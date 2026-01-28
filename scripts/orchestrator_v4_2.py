"""Orchestrator for v4.2 state machine execution."""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from crypto_backtest.v4.config import load_yaml, resolve_family, get_policy
from crypto_backtest.v4.screening import run_screening_long, run_screening_short
from crypto_backtest.v4.coupling import build_coupled_matrix
from crypto_backtest.v4.artifacts import get_run_root, ensure_run_dirs


def _compute_research_end(cfg: dict, policy: dict) -> str | None:
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


def _run_script(path: str, args: list[str]) -> None:
    cmd = [sys.executable, path] + args
    subprocess.run(cmd, check=True)


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def main() -> None:
    parser = argparse.ArgumentParser(description="v4.2 orchestrator")
    parser.add_argument("--asset", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--family", default="A")
    parser.add_argument("--rescue", default=None)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    families_cfg = load_yaml("configs/families.yaml")
    router_cfg = load_yaml("configs/router.yaml")
    policy = get_policy(families_cfg)

    ctx: dict[str, Any] = {
        "asset": args.asset,
        "run_id": args.run_id,
        "family_id": args.family,
        "rescue_id": args.rescue,
        "families_cfg": families_cfg,
        "policy": policy,
        "holdout_enabled": bool(policy.get("data", {}).get("holdout", {}).get("enabled", False)),
    }
    ctx["train_end_ts"] = _compute_research_end(families_cfg, policy)
    ctx["pbo_proxy_enabled"] = bool(policy.get("pbo", {}).get("proxy", {}).get("enabled", True))
    ctx["family_cfg"] = resolve_family(families_cfg, ctx["family_id"], ctx.get("rescue_id"))

    states = set(router_cfg.get("states", []))
    transitions = router_cfg.get("transitions", {})

    state = "INIT"
    visited = set()

    def refresh_family() -> None:
        ctx["family_cfg"] = resolve_family(families_cfg, ctx["family_id"], ctx.get("rescue_id"))

    def run_action(action: str) -> None:
        run_root = get_run_root(ctx["asset"], ctx["run_id"])
        ensure_run_dirs(run_root)

        if action == "run_screening_long":
            path = run_screening_long(
                ctx["asset"],
                ctx["run_id"],
                ctx["family_cfg"],
                policy,
                ctx.get("train_end_ts"),
            )
            ctx["long_candidates"] = len(_load_json(path).get("top_candidates", []))
        elif action == "run_screening_short":
            path = run_screening_short(
                ctx["asset"],
                ctx["run_id"],
                ctx["family_cfg"],
                policy,
                ctx.get("train_end_ts"),
            )
            ctx["short_candidates"] = len(_load_json(path).get("top_candidates", []))
        elif action == "build_coupled_matrix":
            coupling = policy.get("coupling", {})
            path = build_coupled_matrix(
                ctx["asset"],
                ctx["run_id"],
                int(coupling.get("k_long", 10)),
                int(coupling.get("k_short", 10)),
                int(coupling.get("max_couples", 100)),
            )
            ctx["coupled_candidates"] = len(_load_json(path).get("candidates", []))
        elif action == "select_and_backtest_best_couple":
            _run_script(
                "scripts/baseline_select_v4_2.py",
                ["--asset", ctx["asset"], "--run-id", ctx["run_id"]],
            )
        elif action == "run_guards":
            _run_script(
                "scripts/run_guards_v4_2.py",
                ["--asset", ctx["asset"], "--run-id", ctx["run_id"]],
            )
        elif action == "compute_pbo_proxy":
            _run_script(
                "scripts/pbo_v4_2.py",
                ["--asset", ctx["asset"], "--run-id", ctx["run_id"]],
            )
        elif action == "compute_pbo_cscv":
            # pbo_v4_2 writes both proxy and cscv; ensure file exists
            _run_script(
                "scripts/pbo_v4_2.py",
                ["--asset", ctx["asset"], "--run-id", ctx["run_id"]],
            )
        elif action == "compute_regime_stats":
            _run_script(
                "scripts/regime_stats_v4_2.py",
                ["--asset", ctx["asset"], "--run-id", ctx["run_id"]],
            )
            regime_path = run_root / "regime" / "regime.json"
            if regime_path.exists():
                ctx["regime_signal_detected"] = _load_json(regime_path).get(
                    "regime_signal_detected", False
                )
        elif action == "run_repro_check":
            _run_script(
                "scripts/repro_check_v4_2.py",
                ["--asset", ctx["asset"], "--run-id", ctx["run_id"]],
            )
        elif action == "run_portfolio_check":
            _run_script(
                "scripts/portfolio_check_v4_2.py",
                ["--asset", ctx["asset"], "--run-id", ctx["run_id"]],
            )
            portfolio_path = run_root / "portfolio" / "portfolio.json"
            if portfolio_path.exists():
                ctx["portfolio_passed"] = _load_json(portfolio_path).get("passed", False)
        elif action == "run_final_holdout_check":
            if not ctx.get("holdout_enabled"):
                ctx["holdout_passed"] = True
                return
            holdout_script = Path("scripts/holdout_check_v4_2.py")
            if holdout_script.exists():
                _run_script(
                    str(holdout_script),
                    ["--asset", ctx["asset"], "--run-id", ctx["run_id"]],
                )
            else:
                raise RuntimeError("Holdout enabled but no holdout checker implemented")
        else:
            raise ValueError(f"Unknown action: {action}")

    while True:
        if state in visited:
            raise RuntimeError(f"Detected loop at state {state}")
        visited.add(state)

        state_transitions = transitions.get(state, [])
        if not state_transitions:
            raise RuntimeError(f"No transitions defined for state {state}")

        moved = False
        for edge in state_transitions:
            condition = edge.get("if")
            if condition:
                try:
                    cond_value = bool(eval(condition, {"__builtins__": {}}, ctx))
                except Exception:
                    cond_value = False
                if not cond_value:
                    continue
            action = edge.get("action")
            if action and not args.dry_run:
                run_action(action)
            if "set" in edge:
                ctx.update(edge["set"])
                if "family_id" in edge["set"] or "rescue_id" in edge["set"]:
                    refresh_family()
            state = edge.get("then", state)
            moved = True
            break

        if not moved:
            raise RuntimeError(f"No valid transition for state {state}")

        if state in ("PROD_READY", "REJECT"):
            break

    if args.dry_run:
        print(f"Dry run complete. Final state: {state}")
    else:
        print(f"Completed. Final state: {state}")


if __name__ == "__main__":
    main()