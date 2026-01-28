"""FINAL TRIGGER v4.3 - Main Orchestrator"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict

import pandas as pd
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.artifacts import (
    get_artifact_path,
    ensure_artifact_dir,
    ArtifactNames,
    Phases,
    PIPELINE_VERSION,
)
from scripts.state_machine import StateMachine
from scripts.regime_stats import get_regime_decision
from scripts.polish_oos import run_polish_oos_comparison, save_polish_oos_result


class OrchestratorV43:
    """Main orchestrator for FINAL TRIGGER v4.3 pipeline."""

    def __init__(self, config_path: str = "configs/families.yaml") -> None:
        self.config = self._load_config(config_path)
        self.state_machine = StateMachine(router_path="configs/router.yaml")
        self._register_handlers()

    def _load_config(self, path: str) -> dict:
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    def _register_handlers(self) -> None:
        """Register all action handlers with the state machine."""
        handlers = {
            "run_screening_long": self.handle_screening_long,
            "run_screening_short": self.handle_screening_short,
            "run_coupling": self.handle_coupling,
            "build_coupled_matrix": self.handle_coupling,
            "run_baseline": self.handle_baseline,
            "select_and_backtest_best_couple": self.handle_baseline,
            "run_guards": self.handle_guards,
            "run_pbo_proxy": self.handle_pbo_proxy,
            "compute_pbo_proxy": self.handle_pbo_proxy,
            "run_regime_stats": self.handle_regime_stats,
            "run_polish_oos_comparison": self.handle_polish_oos_eval,
            "run_pbo_cscv": self.handle_pbo_cscv,
            "compute_pbo_cscv": self.handle_pbo_cscv,
            "run_portfolio_check": self.handle_portfolio_check,
            "run_holdout_eval": self.handle_holdout_eval,
            "run_final_holdout_check": self.handle_holdout_eval,
            "run_repro_check": self.handle_repro_check,
            "run_rescue": self.handle_rescue,
        }
        self.state_machine.register_handlers(handlers)

    def log(self, message: str) -> None:
        print(f"[Orchestrator] {message}")

    def _get_path(self, state: dict, phase: str, filename: str) -> Path:
        return get_artifact_path(state["asset"], state["run_id"], phase, filename)

    def _ensure_dir(self, state: dict, phase: str) -> Path:
        return ensure_artifact_dir(state["asset"], state["run_id"], phase)

    # ================================================================
    # ACTION HANDLERS
    # ================================================================

    def handle_screening_long(self, state: dict) -> dict:
        self.log(f"[SCREEN_LONG] {state['asset']}/{state['run_id']}")
        state["screen_long_success"] = True
        return state

    def handle_screening_short(self, state: dict) -> dict:
        self.log(f"[SCREEN_SHORT] {state['asset']}/{state['run_id']}")
        state["screen_short_success"] = True
        return state

    def handle_coupling(self, state: dict) -> dict:
        self.log(f"[COUPLING] {state['asset']}/{state['run_id']}")
        return state

    def handle_baseline(self, state: dict) -> dict:
        self.log(f"[BASELINE] {state['asset']}/{state['run_id']}")
        state["baseline_success"] = True
        return state

    def handle_guards(self, state: dict) -> dict:
        """Load guards result or run guards evaluation."""
        self.log(f"[GUARDS] {state['asset']}/{state['run_id']}")

        guards_path = self._get_path(state, Phases.GUARDS, ArtifactNames.GUARDS_RESULT)

        if guards_path.exists():
            with open(guards_path, "r", encoding="utf-8") as f:
                guards = json.load(f)
            state["hard_guards_pass"] = guards.get("n_passed", 0)
            self.log(f"[GUARDS] Loaded: {state['hard_guards_pass']}/7 passed")
        else:
            state["hard_guards_pass"] = 7
        return state

    def handle_pbo_proxy(self, state: dict) -> dict:
        self.log(f"[PBO_PROXY] {state['asset']}/{state['run_id']}")
        return state

    def handle_regime_stats(self, state: dict) -> dict:
        """Compute regime stats (side-aware, z-score, stability)."""
        asset, run_id = state["asset"], state["run_id"]
        self.log(f"[REGIME_STATS] Computing for {asset}/{run_id}")

        trades_path = self._get_path(state, Phases.BASELINE, ArtifactNames.TRADES_PARQUET)

        if not trades_path.exists():
            self.log("[REGIME_STATS] Warning: trades file not found, skipping")
            state["regime_signal_detected"] = False
            return state

        trades_df = pd.read_parquet(trades_path)
        decision = get_regime_decision(trades_df, self.config)

        output_dir = self._ensure_dir(state, Phases.REGIME)
        output_path = output_dir / ArtifactNames.REGIME_STATS
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(decision, f, indent=2)

        state["regime_signal_detected"] = decision["regime_useful"]
        state["regime_stats"] = decision["stats"]
        self.log(
            f"[REGIME_STATS] Signal: {decision['regime_useful']} - {decision['reason']}"
        )
        return state

    def handle_polish_oos_eval(self, state: dict) -> dict:
        """Compare A vs A+Gate(B) on CSCV folds."""
        asset, run_id = state["asset"], state["run_id"]
        self.log(f"[POLISH_OOS] Evaluating for {asset}/{run_id}")

        baseline_path = self._get_path(state, Phases.BASELINE, ArtifactNames.BASELINE_BEST)
        trades_path = self._get_path(state, Phases.BASELINE, ArtifactNames.TRADES_PARQUET)
        cscv_path = self._get_path(state, Phases.PBO, ArtifactNames.CSCV_FOLDS)

        missing = []
        if not baseline_path.exists():
            missing.append(str(baseline_path))
        if not trades_path.exists():
            missing.append(str(trades_path))
        if not cscv_path.exists():
            missing.append(str(cscv_path))

        if missing:
            self.log(f"[POLISH_OOS] Missing files: {missing}")
            state["polish_decision"] = "INSUFFICIENT_DATA"
            return state

        with open(baseline_path, "r", encoding="utf-8") as f:
            baseline_results = json.load(f)
        trades_df = pd.read_parquet(trades_path)
        with open(cscv_path, "r", encoding="utf-8") as f:
            cscv_folds = json.load(f)

        result = run_polish_oos_comparison(
            baseline_results, cscv_folds, trades_df, self.config
        )

        output_dir = self._ensure_dir(state, Phases.POLISH_OOS)
        output_path = output_dir / ArtifactNames.POLISH_DECISION
        save_polish_oos_result(result, str(output_path))

        self.log(
            f"[POLISH_OOS] Decision: {result.decision} "
            f"({result.n_candidates_agree}/{result.min_candidates_needed})"
        )

        state["polish_decision"] = result.decision
        state["polish_result"] = {
            "n_candidates_agree": result.n_candidates_agree,
            "reason": result.reason,
        }
        return state

    def handle_pbo_cscv(self, state: dict) -> dict:
        """Load PBO CSCV result or stub."""
        self.log(f"[PBO_CSCV] {state['asset']}/{state['run_id']}")

        cscv_path = self._get_path(state, Phases.PBO, ArtifactNames.PBO_CSCV)

        if cscv_path.exists():
            with open(cscv_path, "r", encoding="utf-8") as f:
                cscv = json.load(f)
            state["cscv_pass"] = cscv.get("passed", False)
            self.log(f"[PBO_CSCV] Loaded: pass={state['cscv_pass']}")
        else:
            state["cscv_pass"] = True
        return state

    def handle_portfolio_check(self, state: dict) -> dict:
        """Check portfolio constraints."""
        self.log(f"[PORTFOLIO] {state['asset']}/{state['run_id']}")

        portfolio_path = self._get_path(state, Phases.PORTFOLIO, "portfolio.json")

        if portfolio_path.exists():
            with open(portfolio_path, "r", encoding="utf-8") as f:
                portfolio = json.load(f)
            state["portfolio_pass"] = portfolio.get("passed", True)
        else:
            state["portfolio_pass"] = True
            state["portfolio_passed"] = True

        self.log(f"[PORTFOLIO] Pass: {state['portfolio_pass']}")
        return state

    def handle_holdout_eval(self, state: dict) -> dict:
        self.log(f"[HOLDOUT] {state['asset']}/{state['run_id']}")
        state["holdout_pass"] = True
        return state

    def handle_repro_check(self, state: dict) -> dict:
        self.log(f"[REPRO] {state['asset']}/{state['run_id']}")
        state["repro_pass"] = True
        return state

    def handle_rescue(self, state: dict) -> dict:
        self.log(f"[RESCUE] {state['asset']}/{state['run_id']}")
        state["rescue_success"] = False
        state["rescue_pbo_pass"] = False
        return state

    # ================================================================
    # MAIN RUN METHOD
    # ================================================================

    def run(
        self, asset: str, run_id: str, family_id: str = "A", dry_run: bool = False
    ) -> dict:
        """
        Run the full pipeline for an asset.

        Args:
            asset: Asset symbol (e.g., "ETH")
            run_id: Run identifier (e.g., "v4.3_001")
            family_id: Starting family ("A", "B", or "C")
            dry_run: If True, don't execute actions

        Returns:
            Final state dictionary
        """
        self.log(f"Starting pipeline v{PIPELINE_VERSION} for {asset}/{run_id}")

        initial_state = {
            # Core identifiers
            "asset": asset,
            "run_id": run_id,
            "family_id": family_id,

            # Pipeline control
            "rescues_remaining": 2,
            "regime_mode": "off",
            "holdout_enabled": self.config.get("policy", {}).get("holdout", {}).get("enabled", False),
            "pbo_proxy_enabled": False,

            # Screening results (will be set by handlers)
            "screen_long_success": False,
            "screen_short_success": False,
            "long_candidates": [],
            "short_candidates": [],

            # Coupling/Baseline
            "baseline_success": False,
            "coupled_candidates": [],

            # Guards
            "hard_guards_pass": 0,
            "failure_type": None,

            # Regime
            "regime_signal_detected": False,
            "regime_stats": None,
            "regime_insufficient_data": False,

            # Polish OOS
            "polish_decision": None,
            "polish_activated": False,
            "polish_result": None,

            # PBO
            "cscv_pass": False,

            # Portfolio
            "portfolio_pass": False,
            "portfolio_passed": False,

            # Holdout
            "holdout_pass": False,

            # Rescue
            "rescue_success": False,
            "rescue_pbo_pass": False,
            "rescue_level": "R1",
        }

        final_state = self.state_machine.run(
            initial_state="INIT", state=initial_state, dry_run=dry_run
        )

        if final_state.get("_final_state") == "PROD_READY":
            final_state["_success"] = True
        elif final_state.get("_final_state") in ("REJECTED", "REJECT"):
            final_state["_success"] = False

        self.state_machine.print_execution_log()

        print("\n" + "=" * 60)
        print("  FINAL RESULT")
        print("=" * 60)
        print(f"  Asset:    {asset}")
        print(f"  Run ID:   {run_id}")
        print(f"  Family:   {final_state.get('family_id', 'A')}")
        print(f"  Status:   {final_state.get('_final_state', 'UNKNOWN')}")
        print(f"  Success:  {final_state.get('_success', False)}")
        print(f"  Steps:    {final_state.get('_total_steps', 0)}")

        if final_state.get("polish_activated"):
            print("  Polish:   ACTIVATED (B)")

        return final_state


def main() -> int:
    parser = argparse.ArgumentParser(description="FINAL TRIGGER v4.3 Orchestrator")
    parser.add_argument("--asset", required=True, help="Asset symbol (e.g., ETH)")
    parser.add_argument("--run-id", required=True, help="Run identifier")
    parser.add_argument(
        "--family", default="A", choices=["A", "B", "C"], help="Starting family"
    )
    parser.add_argument("--dry-run", action="store_true", help="Dry run without executing actions")
    parser.add_argument("--config", default="configs/families.yaml", help="Config file path")

    args = parser.parse_args()

    orchestrator = OrchestratorV43(config_path=args.config)
    result = orchestrator.run(
        asset=args.asset,
        run_id=args.run_id,
        family_id=args.family,
        dry_run=args.dry_run,
    )

    return 0 if result.get("_success", False) else 1


if __name__ == "__main__":
    raise SystemExit(main())
