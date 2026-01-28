"""Orchestrator for v4.2 state machine execution.

CHANGELOG (2026-01-28):
- FIX: Guards bypass bug - pipeline now stops if guards fail
- FIX: Removed PBO proxy (keep only CSCV)
- FIX: Added save_summary() - creates archive/summary.json
- FIX: Added explicit stage logging
- FIX: Added proper file logging to logs/
"""
from __future__ import annotations

import argparse
import json
import logging
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from crypto_backtest.v4.config import load_yaml, resolve_family, get_policy
from crypto_backtest.v4.screening import run_screening_long, run_screening_short
from crypto_backtest.v4.coupling import build_coupled_matrix
from crypto_backtest.v4.artifacts import get_run_root, ensure_run_dirs


# =============================================================================
# LOGGING SETUP
# =============================================================================
def setup_logging(asset: str, run_id: str) -> logging.Logger:
    """Setup logging to both file and console."""
    logs_dir = Path("logs")
    logs_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = logs_dir / f"orchestrator_{asset}_{run_id}_{timestamp}.log"

    # Create logger
    logger = logging.getLogger(f"orchestrator.{asset}")
    logger.setLevel(logging.DEBUG)

    # Clear any existing handlers
    logger.handlers.clear()

    # File handler
    fh = logging.FileHandler(log_file, encoding='utf-8')
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(logging.Formatter(
        '%(asctime)s [%(levelname)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    ))
    logger.addHandler(fh)

    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(logging.Formatter('[%(levelname)s] %(message)s'))
    logger.addHandler(ch)

    logger.info(f"Logging initialized: {log_file}")
    return logger


# =============================================================================
# SUMMARY FUNCTIONS
# =============================================================================
def save_summary(
    run_root: Path,
    asset: str,
    run_id: str,
    verdict: str,
    reason: str = "",
    logger: logging.Logger = None
) -> dict:
    """Save final summary.json with all metrics collected during the run."""
    summary = {
        "asset": asset,
        "run_id": run_id,
        "verdict": verdict,
        "reason": reason,
        "timestamp": datetime.now().isoformat(),
        "metrics": {}
    }

    # Files to aggregate into summary
    files_to_load = [
        ('baseline', 'baseline/baseline_best.json',
         ['wfe', 'oos_sharpe', 'oos_trades', 'is_trades', 'bars', 'top10_concentration']),
        ('guards', 'guards/guards.json', ['passed', 'failed', 'catastrophic']),
        ('pbo_cscv', 'pbo/pbo_cscv.json', ['pbo', 'folds']),
        ('regime', 'regime/regime.json', ['regime_signal_detected']),
        ('portfolio', 'portfolio/portfolio.json', ['passed', 'reason', 'corr_union']),
        ('repro', 'archive/repro_check.json', ['passed', 'diff_count']),
    ]

    for section, filepath, keys in files_to_load:
        full_path = run_root / filepath
        if full_path.exists():
            try:
                data = json.loads(full_path.read_text())
                summary['metrics'][section] = {k: data.get(k) for k in keys if k in data}
            except Exception as e:
                if logger:
                    logger.warning(f"Could not load {filepath}: {e}")

    # Save summary
    archive_dir = run_root / 'archive'
    archive_dir.mkdir(parents=True, exist_ok=True)
    summary_path = archive_dir / 'summary.json'

    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)

    if logger:
        logger.info(f"Summary saved: verdict={verdict}, reason={reason}")
        logger.info(f"Summary path: {summary_path}")

    return summary


# =============================================================================
# HELPERS
# =============================================================================
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


def _run_script(path: str, args: list[str], logger: logging.Logger = None) -> None:
    """Run a script subprocess with logging."""
    cmd = [sys.executable, path] + args
    if logger:
        logger.debug(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        if logger:
            logger.error(f"Script failed: {path}")
            logger.error(f"stderr: {result.stderr}")
        raise subprocess.CalledProcessError(result.returncode, cmd)
    if logger:
        logger.debug(f"Completed: {path}")


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


# =============================================================================
# MAIN ORCHESTRATOR
# =============================================================================
def main() -> None:
    parser = argparse.ArgumentParser(description="v4.2 orchestrator")
    parser.add_argument("--asset", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--family", default="A")
    parser.add_argument("--rescue", default=None)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    # Setup logging
    logger = setup_logging(args.asset, args.run_id)
    logger.info("=" * 60)
    logger.info(f"ORCHESTRATOR v4.2 START: {args.asset} / {args.run_id}")
    logger.info("=" * 60)

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
    # FIX: Disable PBO proxy by default - only use CSCV
    ctx["pbo_proxy_enabled"] = False
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
        logger.info(f"[{state}] Running action: {action}")

        if action == "run_screening_long":
            path = run_screening_long(
                ctx["asset"],
                ctx["run_id"],
                ctx["family_cfg"],
                policy,
                ctx.get("train_end_ts"),
            )
            ctx["long_candidates"] = len(_load_json(path).get("top_candidates", []))
            logger.info(f"Screening long: {ctx['long_candidates']} candidates")

        elif action == "run_screening_short":
            path = run_screening_short(
                ctx["asset"],
                ctx["run_id"],
                ctx["family_cfg"],
                policy,
                ctx.get("train_end_ts"),
            )
            ctx["short_candidates"] = len(_load_json(path).get("top_candidates", []))
            logger.info(f"Screening short: {ctx['short_candidates']} candidates")

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
            logger.info(f"Coupled matrix: {ctx['coupled_candidates']} couples")

        elif action == "select_and_backtest_best_couple":
            _run_script(
                "scripts/baseline_select_v4_2.py",
                ["--asset", ctx["asset"], "--run-id", ctx["run_id"]],
                logger
            )
            # Load baseline results for logging
            baseline_path = run_root / "baseline" / "baseline_best.json"
            if baseline_path.exists():
                baseline = _load_json(baseline_path)
                wfe = baseline.get('wfe', 'N/A')
                oos_sharpe = baseline.get('oos_sharpe', 'N/A')
                oos_trades = baseline.get('oos_trades', 'N/A')
                wfe_str = f"{wfe:.3f}" if isinstance(wfe, (int, float)) else str(wfe)
                sharpe_str = f"{oos_sharpe:.3f}" if isinstance(oos_sharpe, (int, float)) else str(oos_sharpe)
                logger.info(f"Baseline: WFE={wfe_str}, OOS_Sharpe={sharpe_str}, OOS_Trades={oos_trades}")

        elif action == "run_guards":
            _run_script(
                "scripts/run_guards_v4_2.py",
                ["--asset", ctx["asset"], "--run-id", ctx["run_id"]],
                logger
            )
            # FIX: Load guards result and set context variable
            guards_path = run_root / "guards" / "guards.json"
            if guards_path.exists():
                guards_result = _load_json(guards_path)
                ctx["guards_passed"] = guards_result.get("passed", False)
                ctx["guards_failed_count"] = guards_result.get("failed", 0)
                ctx["guards_catastrophic"] = guards_result.get("catastrophic", False)

                if ctx["guards_passed"]:
                    logger.info("Guards: PASS (7/7)")
                else:
                    failed_guards = [g["name"] for g in guards_result.get("guards", [])
                                    if not g.get("passed", True)]
                    logger.warning(f"Guards: FAIL ({7 - ctx['guards_failed_count']}/7) - "
                                  f"Failed: {', '.join(failed_guards)}")
            else:
                ctx["guards_passed"] = False
                logger.error("Guards file not found!")

        elif action == "compute_pbo_proxy":
            # FIX: Skip PBO proxy - only compute if explicitly enabled (which it won't be)
            logger.info("PBO proxy SKIPPED (disabled in v4.2)")

        elif action == "compute_pbo_cscv":
            _run_script(
                "scripts/pbo_v4_2.py",
                ["--asset", ctx["asset"], "--run-id", ctx["run_id"]],
                logger
            )
            # Load PBO result for logging and soft gate
            pbo_path = run_root / "pbo" / "pbo_cscv.json"
            if pbo_path.exists():
                pbo_result = _load_json(pbo_path)
                pbo_value = pbo_result.get("pbo", 1.0)
                ctx["pbo_cscv_value"] = pbo_value

                # Soft gate: warn but don't block
                pbo_thresholds = policy.get("thresholds", {}).get("pbo", {})
                if pbo_value > pbo_thresholds.get("proxy_kill", 0.70):
                    logger.warning(f"PBO CSCV: {pbo_value:.2f} - HIGH OVERFITTING RISK (> 0.70)")
                elif pbo_value > pbo_thresholds.get("proxy_warning", 0.60):
                    logger.warning(f"PBO CSCV: {pbo_value:.2f} - Elevated overfitting risk (> 0.60)")
                else:
                    logger.info(f"PBO CSCV: {pbo_value:.2f} - OK")

        elif action == "compute_regime_stats":
            _run_script(
                "scripts/regime_stats_v4_2.py",
                ["--asset", ctx["asset"], "--run-id", ctx["run_id"]],
                logger
            )
            regime_path = run_root / "regime" / "regime.json"
            if regime_path.exists():
                regime_data = _load_json(regime_path)
                ctx["regime_signal_detected"] = regime_data.get("regime_signal_detected", False)
                logger.info(f"Regime signal detected: {ctx['regime_signal_detected']}")

        elif action == "run_repro_check":
            _run_script(
                "scripts/repro_check_v4_2.py",
                ["--asset", ctx["asset"], "--run-id", ctx["run_id"]],
                logger
            )
            repro_path = run_root / "archive" / "repro_check.json"
            if repro_path.exists():
                repro_result = _load_json(repro_path)
                logger.info(f"Repro check: {'PASS' if repro_result.get('passed') else 'FAIL'}")

        elif action == "run_portfolio_check":
            _run_script(
                "scripts/portfolio_check_v4_2.py",
                ["--asset", ctx["asset"], "--run-id", ctx["run_id"]],
                logger
            )
            portfolio_path = run_root / "portfolio" / "portfolio.json"
            if portfolio_path.exists():
                portfolio_result = _load_json(portfolio_path)
                ctx["portfolio_passed"] = portfolio_result.get("passed", False)
                corr = portfolio_result.get('corr_union', 'N/A')
                corr_str = f"{corr:.3f}" if isinstance(corr, (int, float)) else str(corr)
                logger.info(f"Portfolio check: {'PASS' if ctx['portfolio_passed'] else 'FAIL'} "
                           f"(corr={corr_str})")
            else:
                ctx["portfolio_passed"] = False
                logger.error("Portfolio file not found!")

        elif action == "run_final_holdout_check":
            if not ctx.get("holdout_enabled"):
                ctx["holdout_passed"] = True
                logger.info("Holdout: SKIPPED (disabled)")
                return
            holdout_script = Path("scripts/holdout_check_v4_2.py")
            if holdout_script.exists():
                _run_script(
                    str(holdout_script),
                    ["--asset", ctx["asset"], "--run-id", ctx["run_id"]],
                    logger
                )
            else:
                raise RuntimeError("Holdout enabled but no holdout checker implemented")
        else:
            raise ValueError(f"Unknown action: {action}")

    # Main state machine loop
    try:
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

                    # FIX: Check guards result immediately after running guards
                    if action == "run_guards" and not ctx.get("guards_passed", True):
                        run_root = get_run_root(ctx["asset"], ctx["run_id"])
                        logger.error("GUARDS FAILED - stopping pipeline")
                        save_summary(
                            run_root, ctx["asset"], ctx["run_id"],
                            verdict="BLOCKED",
                            reason=f"Guards failed: {ctx.get('guards_failed_count', '?')}/7",
                            logger=logger
                        )
                        state = "REJECT"
                        logger.info(f"Final state: {state}")
                        logger.info("=" * 60)
                        logger.info(f"ORCHESTRATOR v4.2 END: {ctx['asset']} -> {state}")
                        logger.info("=" * 60)
                        return

                if "set" in edge:
                    ctx.update(edge["set"])
                    if "family_id" in edge["set"] or "rescue_id" in edge["set"]:
                        refresh_family()
                        # FIX: Clear visited set when changing families to allow state revisit
                        logger.info(f"Family changed to {ctx['family_id']} - resetting state machine")
                        visited.clear()

                state = edge.get("then", state)
                logger.debug(f"Transition -> {state}")
                moved = True
                break

            if not moved:
                raise RuntimeError(f"No valid transition for state {state}")

            # Terminal states
            if state in ("PROD_READY", "REJECT"):
                break

        # FIX: Save summary at terminal state
        run_root = get_run_root(ctx["asset"], ctx["run_id"])
        if state == "PROD_READY":
            save_summary(
                run_root, ctx["asset"], ctx["run_id"],
                verdict="PROD_READY",
                reason="All checks passed",
                logger=logger
            )
        elif state == "REJECT":
            # Find the reason from the last transition
            reason = "Pipeline rejected"
            for edge in transitions.get(state, []):
                if edge.get("reason"):
                    reason = edge["reason"]
                    break
            save_summary(
                run_root, ctx["asset"], ctx["run_id"],
                verdict="REJECT",
                reason=reason,
                logger=logger
            )

        if args.dry_run:
            logger.info(f"Dry run complete. Final state: {state}")
        else:
            logger.info(f"Completed. Final state: {state}")

    except Exception as e:
        logger.exception(f"Pipeline failed with error: {e}")
        try:
            run_root = get_run_root(ctx["asset"], ctx["run_id"])
            save_summary(
                run_root, ctx["asset"], ctx["run_id"],
                verdict="ERROR",
                reason=str(e),
                logger=logger
            )
        except Exception:
            pass
        raise

    logger.info("=" * 60)
    logger.info(f"ORCHESTRATOR v4.2 END: {ctx['asset']} -> {state}")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
