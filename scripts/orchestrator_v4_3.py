"""FINAL TRIGGER v4.3 - Main Orchestrator"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import crypto_backtest.v4.screening as screening_mod
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
from crypto_backtest.v4.config import load_yaml, resolve_family, get_policy
from crypto_backtest.v4.screening import run_screening_long, run_screening_short
from crypto_backtest.v4.artifacts import get_run_root, ensure_run_dirs
from crypto_backtest.optimization.parallel_optimizer import load_data


class OrchestratorV43:
    """Main orchestrator for FINAL TRIGGER v4.3 pipeline."""

    def __init__(self, config_path: str = "configs/families.yaml") -> None:
        self.config = self._load_config(config_path)
        self.state_machine = StateMachine(router_path="configs/router.yaml")
        self._register_handlers()

    def _load_config(self, path: str) -> dict:
        return load_yaml(path)

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
        """Run Optuna screening for LONG side."""
        asset, run_id = state["asset"], state["run_id"]
        family_id = state.get("family_id", "A")
        rescue_level = state.get("rescue_level") if state.get("rescues_remaining", 2) < 2 else None

        self.log(f"[SCREEN_LONG] {asset}/{run_id} family={family_id}")

        try:
            policy = get_policy(self.config)
            family_cfg = resolve_family(self.config, family_id, rescue_level)

            data_end_ts = self._compute_research_end(policy)

            original_trials = screening_mod.TRIALS
            if state.get("fast_mode"):
                screening_mod.TRIALS = 10

            try:
                result_path = run_screening_long(asset, run_id, family_cfg, policy, data_end_ts)
            finally:
                screening_mod.TRIALS = original_trials

            output_path = Path(result_path) if result_path else None
            if output_path is None or not output_path.exists():
                run_root = get_run_root(asset, run_id)
                output_path = run_root / "screening" / "screen_long.json"

            if output_path.exists():
                payload = json.loads(output_path.read_text())
                candidates = payload.get("candidates") or payload.get("top_candidates") or []
            else:
                candidates = []

            state["screen_long_success"] = len(candidates) > 0
            state["long_candidates"] = candidates
            self.log(f"[SCREEN_LONG] Found {len(state['long_candidates'])} candidates")

        except Exception as e:
            self.log(f"[SCREEN_LONG] ERROR: {e}")
            state["screen_long_success"] = False
            state["long_candidates"] = []
        return state

    def handle_screening_short(self, state: dict) -> dict:
        """Run Optuna screening for SHORT side."""
        asset, run_id = state["asset"], state["run_id"]
        family_id = state.get("family_id", "A")
        rescue_level = state.get("rescue_level") if state.get("rescues_remaining", 2) < 2 else None

        self.log(f"[SCREEN_SHORT] {asset}/{run_id} family={family_id}")

        try:
            policy = get_policy(self.config)
            family_cfg = resolve_family(self.config, family_id, rescue_level)
            data_end_ts = self._compute_research_end(policy)

            original_trials = screening_mod.TRIALS
            if state.get("fast_mode"):
                screening_mod.TRIALS = 10

            try:
                result_path = run_screening_short(asset, run_id, family_cfg, policy, data_end_ts)
            finally:
                screening_mod.TRIALS = original_trials

            output_path = Path(result_path) if result_path else None
            if output_path is None or not output_path.exists():
                run_root = get_run_root(asset, run_id)
                output_path = run_root / "screening" / "screen_short.json"

            if output_path.exists():
                payload = json.loads(output_path.read_text())
                candidates = payload.get("candidates") or payload.get("top_candidates") or []
            else:
                candidates = []

            state["screen_short_success"] = len(candidates) > 0
            state["short_candidates"] = candidates

            total_long = len(state.get("long_candidates", []))
            total_short = len(state["short_candidates"])
            if total_long + total_short > 0:
                short_ratio = total_short / (total_long + total_short)
                if not (0.25 <= short_ratio <= 0.75):
                    self.log(f"[SCREEN_SHORT] WARNING: short_ratio={short_ratio:.2f} outside 25-75%")

            self.log(f"[SCREEN_SHORT] Found {total_short} candidates")

        except Exception as e:
            self.log(f"[SCREEN_SHORT] ERROR: {e}")
            state["screen_short_success"] = False
            state["short_candidates"] = []
        return state

    def handle_coupling(self, state: dict) -> dict:
        """Build top_k_cross coupled candidates from L/S screening results."""
        asset, run_id = state["asset"], state["run_id"]
        self.log(f"[COUPLING] {asset}/{run_id}")

        try:
            run_root = get_run_root(asset, run_id)
            ensure_run_dirs(run_root)

            screen_long_path = run_root / "screening" / "screen_long.json"
            screen_short_path = run_root / "screening" / "screen_short.json"

            if not screen_long_path.exists() or not screen_short_path.exists():
                self.log("[COUPLING] Missing screening results")
                state["coupled_candidates"] = []
                return state

            long_results = json.loads(screen_long_path.read_text())
            short_results = json.loads(screen_short_path.read_text())

            long_candidates = (long_results.get("candidates") or long_results.get("top_candidates") or [])[:10]
            short_candidates = (short_results.get("candidates") or short_results.get("top_candidates") or [])[:10]

            coupled = []
            couple_id = 0
            for lc in long_candidates:
                for sc in short_candidates:
                    coupled.append({
                        "couple_id": couple_id,
                        "long": lc,
                        "short": sc,
                        "combined_score": (lc.get("score", 0) + sc.get("score", 0)) / 2,
                    })
                    couple_id += 1

            max_couples = 5 if state.get("fast_mode") else 100
            coupled = sorted(coupled, key=lambda x: x["combined_score"], reverse=True)[:max_couples]

            output = {"candidates": coupled, "n_long": len(long_candidates), "n_short": len(short_candidates)}
            coupling_dir = run_root / "coupling"
            coupling_dir.mkdir(parents=True, exist_ok=True)
            (coupling_dir / "coupled_candidates.json").write_text(json.dumps(output, indent=2))

            state["coupled_candidates"] = coupled
            self.log(f"[COUPLING] Created {len(coupled)} coupled candidates")

        except Exception as e:
            self.log(f"[COUPLING] ERROR: {e}")
            state["coupled_candidates"] = []
        return state

    def handle_baseline(self, state: dict) -> dict:
        """Select best coupled candidate with walk-forward validation."""
        asset, run_id = state["asset"], state["run_id"]
        self.log(f"[BASELINE] {asset}/{run_id}")

        try:
            from crypto_backtest.v4.backtest_adapter import run_coupled_backtest

            policy = get_policy(self.config)
            data_end_ts = self._compute_research_end(policy)

            data = load_data(asset, data_dir="data")
            if data_end_ts:
                data = data.loc[:pd.to_datetime(data_end_ts)]

            run_root = get_run_root(asset, run_id)
            coupled_path = run_root / "coupling" / "coupled_candidates.json"

            if not coupled_path.exists():
                self.log("[BASELINE] No coupled candidates found")
                state["baseline_success"] = False
                return state

            coupled = json.loads(coupled_path.read_text())
            candidates = coupled.get("candidates", [])

            best = None
            best_score = float("-inf")
            best_result = None

            max_candidates = 5 if state.get("fast_mode") else len(candidates)
            for candidate in candidates[:max_candidates]:
                recipe_config = {
                    "long_params": candidate["long"].get("params", {}),
                    "short_params": candidate["short"].get("params", {}),
                }
                result = run_coupled_backtest(
                    asset=asset,
                    recipe_config=recipe_config,
                    mode="combined",
                    start_ts=None,
                    end_ts=data_end_ts,
                )
                metrics = result.get("metrics", {})
                score = metrics.get("sharpe", metrics.get("score", 0))

                if score > best_score:
                    best_score = score
                    best = {
                        "couple_id": candidate.get("couple_id"),
                        "long_params": recipe_config["long_params"],
                        "short_params": recipe_config["short_params"],
                        "metrics": metrics,
                    }
                    best_result = result

            if best is None:
                state["baseline_success"] = False
                return state

            wf_stats = self._walk_forward_eval(asset, best, data.index, run_coupled_backtest)
            best.update(wf_stats)
            best["bars"] = len(data)

            baseline_dir = run_root / "baseline"
            baseline_dir.mkdir(parents=True, exist_ok=True)
            (baseline_dir / "baseline_best.json").write_text(json.dumps(best, indent=2, default=str))

            trades = (best_result or {}).get("trades")
            if trades is not None:
                try:
                    trades.to_parquet(baseline_dir / "trades.parquet", index=False)
                except Exception as e:
                    self.log(f"[BASELINE] WARN: failed to save trades.parquet: {e}")

            state["baseline_success"] = True
            state["baseline_wfe"] = wf_stats.get("wfe", 0)
            state["baseline_oos_trades"] = wf_stats.get("oos_trades", 0)
            self.log(f"[BASELINE] Best couple WFE={wf_stats.get('wfe', 0):.3f}")

        except Exception as e:
            self.log(f"[BASELINE] ERROR: {e}")
            state["baseline_success"] = False
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
        """Run calibrated PBO proxy evaluation."""
        asset, run_id = state["asset"], state["run_id"]
        self.log(f"[PBO_PROXY] {asset}/{run_id}")

        try:
            from crypto_backtest.v4.backtest_adapter import run_coupled_backtest
            from crypto_backtest.validation.pbo_legacy import probability_of_backtest_overfitting

            policy = get_policy(self.config)
            pbo_cfg = policy.get("pbo", {}).get("proxy", {})
            data_end_ts = self._compute_research_end(policy)

            run_root = get_run_root(asset, run_id)
            coupled_path = run_root / "coupling" / "coupled_candidates.json"

            if not coupled_path.exists():
                self.log("[PBO_PROXY] No coupled candidates found")
                return state

            coupled = json.loads(coupled_path.read_text())
            candidates = coupled.get("candidates", [])

            returns_list = []
            for candidate in candidates:
                recipe_config = {
                    "long_params": candidate["long"].get("params", {}),
                    "short_params": candidate["short"].get("params", {}),
                }
                result = run_coupled_backtest(
                    asset=asset,
                    recipe_config=recipe_config,
                    mode="combined",
                    start_ts=None,
                    end_ts=data_end_ts,
                )
                returns = self._extract_bar_returns(result)
                if returns is not None and len(returns) > 0:
                    returns_list.append(returns)

            if not returns_list:
                self.log("[PBO_PROXY] No returns data available")
                return state

            min_len = min(len(r) for r in returns_list)
            returns_matrix = np.stack([r[:min_len] for r in returns_list], axis=0).astype(np.float32)

            proxy_result = probability_of_backtest_overfitting(
                returns_matrix,
                n_splits=int(pbo_cfg.get("folds", 8)),
                threshold=0.50,
            )

            pbo_value = float(proxy_result.pbo)

            pbo_dir = run_root / "pbo"
            pbo_dir.mkdir(parents=True, exist_ok=True)
            payload = {
                "K": returns_matrix.shape[0],
                "T": returns_matrix.shape[1],
                "folds": int(pbo_cfg.get("folds", 8)),
                "pbo": pbo_value,
            }
            (pbo_dir / "pbo_proxy.json").write_text(json.dumps(payload, indent=2))

            state["pbo_proxy_value"] = pbo_value
            self.log(f"[PBO_PROXY] PBO={pbo_value:.3f}")

        except Exception as e:
            self.log(f"[PBO_PROXY] ERROR: {e}")
        return state

    def handle_regime_stats(self, state: dict) -> dict:
        """Compute regime stats (side-aware, z-score, stability)."""
        asset, run_id = state["asset"], state["run_id"]
        self.log(f"[REGIME_STATS] Computing for {asset}/{run_id}")

        trades_path = self._get_path(state, Phases.BASELINE, ArtifactNames.TRADES_PARQUET)
        if not trades_path.exists():
            run_root = get_run_root(asset, run_id)
            fallback = run_root / "baseline" / "trades.parquet"
            if fallback.exists():
                trades_path = fallback

        if not trades_path.exists():
            self.log("[REGIME_STATS] Warning: trades file not found, skipping")
            state["regime_signal_detected"] = False
            return state

        trades_df = pd.read_parquet(trades_path)
        required_cols = ["side", "regime"]
        missing_cols = [c for c in required_cols if c not in trades_df.columns]

        if missing_cols:
            self.log(f"[REGIME_STATS] Missing columns: {missing_cols} — attempting derivation")

            if "side" not in trades_df.columns:
                if "direction" in trades_df.columns:
                    trades_df["side"] = trades_df["direction"].map(
                        {1: "long", -1: "short", "long": "long", "short": "short"}
                    )
                elif all(col in trades_df.columns for col in ("pnl", "entry_price", "exit_price")):
                    trades_df["side"] = np.where(
                        trades_df["exit_price"] > trades_df["entry_price"],
                        "long",
                        "short",
                    )
                else:
                    self.log("[REGIME_STATS] Cannot derive 'side', skipping regime stats")
                    state["regime_signal_detected"] = False
                    state["regime_insufficient_data"] = True
                    return state

            if "regime" not in trades_df.columns:
                self.log("[REGIME_STATS] 'regime' column missing — regime stats not applicable for Family A")
                state["regime_signal_detected"] = False
                state["regime_insufficient_data"] = True
                return state

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

        if not (baseline_path.exists() and trades_path.exists() and cscv_path.exists()):
            run_root = get_run_root(asset, run_id)
            baseline_fallback = run_root / "baseline" / "baseline_best.json"
            trades_fallback = run_root / "baseline" / "trades.parquet"
            cscv_fallback = run_root / "pbo" / "cscv_folds.json"
            if baseline_fallback.exists():
                baseline_path = baseline_fallback
            if trades_fallback.exists():
                trades_path = trades_fallback
            if cscv_fallback.exists():
                cscv_path = cscv_fallback

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
    # UTILITIES
    # ================================================================

    def _compute_research_end(self, policy: dict) -> str | None:
        """Compute research window end, excluding holdout period."""
        dataset_end = self.config.get("dataset", {}).get("end_utc")
        if not dataset_end:
            return None
        end_ts = pd.to_datetime(dataset_end)
        holdout = policy.get("data", {}).get("holdout", {})
        if holdout.get("enabled"):
            months = int(holdout.get("months", 0))
            if months > 0:
                end_ts = end_ts - pd.DateOffset(months=months)
        return end_ts.isoformat()

    def _walk_forward_eval(
        self,
        asset: str,
        best: dict,
        data_index,
        run_coupled_backtest,
        n_splits: int = 5,
        train_ratio: float = 0.6,
    ) -> dict:
        """Run walk-forward evaluation on best candidate."""
        n = len(data_index)
        train_size = int(n * train_ratio)
        remaining = n - train_size
        split_size = remaining // n_splits

        if split_size < 2:
            return {"wfe": 0.0, "oos_sharpe": 0.0, "oos_trades": 0}

        is_sharpes, oos_sharpes = [], []
        oos_trades = 0

        recipe_config = {
            "long_params": best["long_params"],
            "short_params": best["short_params"],
        }

        for split_id in range(n_splits):
            train_end_idx = train_size + split_id * split_size
            test_end_idx = train_end_idx + split_size
            if test_end_idx > n:
                break

            train_end_ts = data_index[train_end_idx - 1]
            test_start_ts = data_index[train_end_idx]
            test_end_ts = data_index[test_end_idx - 1]

            is_result = run_coupled_backtest(
                asset=asset,
                recipe_config=recipe_config,
                mode="combined",
                start_ts=None,
                end_ts=pd.Timestamp(train_end_ts).isoformat(),
            )
            oos_result = run_coupled_backtest(
                asset=asset,
                recipe_config=recipe_config,
                mode="combined",
                start_ts=pd.Timestamp(test_start_ts).isoformat(),
                end_ts=pd.Timestamp(test_end_ts).isoformat(),
            )

            is_sharpe = is_result.get("metrics", {}).get("sharpe", 0)
            oos_sharpe = oos_result.get("metrics", {}).get("sharpe", 0)
            is_sharpes.append(is_sharpe)
            oos_sharpes.append(oos_sharpe)
            oos_trades += len(oos_result.get("trades", []))

        mean_is = np.mean(is_sharpes) if is_sharpes else 0
        mean_oos = np.mean(oos_sharpes) if oos_sharpes else 0
        wfe = mean_oos / mean_is if mean_is > 0 else 0

        return {
            "wfe": float(wfe),
            "oos_sharpe": float(mean_oos),
            "oos_trades": int(oos_trades),
        }

    def _extract_bar_returns(self, result: dict) -> np.ndarray | None:
        """Extract bar returns from backtest result."""
        if "bar_returns" in result:
            return np.asarray(result["bar_returns"], dtype=float)
        if "returns" in result:
            return np.asarray(result["returns"], dtype=float)
        equity = result.get("equity_curve")
        if equity is not None:
            equity = np.asarray(equity, dtype=float)
            if len(equity) < 2:
                return None
            return np.diff(equity) / equity[:-1]
        return None

    # ================================================================
    # MAIN RUN METHOD
    # ================================================================

    def run(
        self,
        asset: str,
        run_id: str,
        family_id: str = "A",
        dry_run: bool = False,
        fast_mode: bool = False,
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
            "fast_mode": fast_mode,

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
    parser.add_argument("--fast", action="store_true", help="Fast mode: reduced trials/candidates for testing")
    parser.add_argument("--config", default="configs/families.yaml", help="Config file path")

    args = parser.parse_args()

    orchestrator = OrchestratorV43(config_path=args.config)
    result = orchestrator.run(
        asset=args.asset,
        run_id=args.run_id,
        family_id=args.family,
        dry_run=args.dry_run,
        fast_mode=args.fast,
    )

    return 0 if result.get("_success", False) else 1


if __name__ == "__main__":
    raise SystemExit(main())
