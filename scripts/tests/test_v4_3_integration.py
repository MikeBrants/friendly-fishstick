#!/usr/bin/env python3
"""
FINAL TRIGGER v4.3 - Integration Tests

End-to-end tests using mock data to validate the full pipeline.
"""

import pytest
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scripts.artifacts import get_artifact_path, Phases, ArtifactNames
from scripts.generate_mock_data import generate_all_mock_data

TEST_ASSET = "TEST_ETH"
TEST_RUN_ID = "integration_test"


@pytest.fixture(scope="module")
def mock_data():
    """Generate mock data once for all tests."""
    summary = generate_all_mock_data(
        asset=TEST_ASSET,
        run_id=TEST_RUN_ID,
        n_bars=5000,
        n_trades=400,
        regime_effect=True,
        seed=42,
    )
    return summary


@pytest.fixture(scope="module")
def trades_df(mock_data):
    """Load generated trades."""
    import pandas as pd

    path = get_artifact_path(TEST_ASSET, TEST_RUN_ID, Phases.BASELINE, ArtifactNames.TRADES_PARQUET)
    return pd.read_parquet(path)


@pytest.fixture(scope="module")
def baseline_results(mock_data):
    """Load baseline results."""
    path = get_artifact_path(TEST_ASSET, TEST_RUN_ID, Phases.BASELINE, ArtifactNames.BASELINE_BEST)
    with open(path, encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def cscv_folds(mock_data):
    """Load CSCV folds."""
    path = get_artifact_path(TEST_ASSET, TEST_RUN_ID, Phases.PBO, ArtifactNames.CSCV_FOLDS)
    with open(path, encoding="utf-8") as f:
        return json.load(f)


class TestArtifacts:
    """Test artifact generation and paths."""

    def test_artifacts_use_v4_3(self):
        path = get_artifact_path("ETH", "test", Phases.BASELINE, "test.json")
        assert "v4_3" in str(path)

    def test_all_required_artifacts_exist(self, mock_data):
        required = [
            (Phases.SCREENING, ArtifactNames.SCREEN_LONG),
            (Phases.SCREENING, ArtifactNames.SCREEN_SHORT),
            (Phases.COUPLING, ArtifactNames.COUPLED_CANDIDATES),
            (Phases.BASELINE, ArtifactNames.BASELINE_BEST),
            (Phases.BASELINE, ArtifactNames.TRADES_PARQUET),
            (Phases.PBO, ArtifactNames.CSCV_FOLDS),
            (Phases.GUARDS, ArtifactNames.GUARDS_RESULT),
        ]

        for phase, filename in required:
            path = get_artifact_path(TEST_ASSET, TEST_RUN_ID, phase, filename)
            assert path.exists(), f"Missing: {path}"


class TestRegimeStats:
    """Test regime statistics module."""

    def test_regime_stats_detects_signal(self, trades_df):
        from scripts.regime_stats import compute_regime_stats_side_aware

        config = {
            "policy": {
                "regime": {
                    "n_trades_min_per_bucket": 30,
                    "n_trades_min_per_window": 10,
                    "signal_z_min": 1.0,
                    "stability_windows": 4,
                    "stability_pass_ratio": 0.5,
                }
            }
        }

        result = compute_regime_stats_side_aware(trades_df, config)

        assert result.sufficient_data is True
        assert result.delta_long > 0
        assert result.delta_short > 0

    def test_regime_decision(self, trades_df):
        from scripts.regime_stats import get_regime_decision

        config = {
            "policy": {
                "regime": {
                    "n_trades_min_per_bucket": 30,
                    "n_trades_min_per_window": 10,
                    "signal_z_min": 1.0,
                    "stability_windows": 4,
                    "stability_pass_ratio": 0.5,
                }
            }
        }

        decision = get_regime_decision(trades_df, config)

        assert "regime_useful" in decision
        assert "stats" in decision
        assert "delta_long" in decision["stats"]


class TestPolishOOS:
    """Test Polish OOS comparison module."""

    def test_polish_oos_with_regime_effect(self, baseline_results, cscv_folds, trades_df):
        from scripts.polish_oos import run_polish_oos_comparison

        config = {
            "policy": {
                "regime": {
                    "n_trades_min_per_bucket": 20,
                    "polish_oos": {
                        "max_candidates": 5,
                        "min_candidates_agree": 2,
                        "min_wins": 5,
                        "min_median_delta_sharpe": 0.01,
                        "min_median_delta_maxdd": 1.0,
                        "require_both": False,
                    }
                }
            }
        }

        result = run_polish_oos_comparison(
            baseline_results=baseline_results,
            cscv_folds=cscv_folds,
            trades_df=trades_df,
            config=config,
        )

        assert result.decision in ["UPGRADE_TO_B", "STAY_A", "INSUFFICIENT_DATA"]
        assert len(result.candidates_results) > 0

    def test_polish_oos_result_structure(self, baseline_results, cscv_folds, trades_df):
        from scripts.polish_oos import run_polish_oos_comparison

        config = {
            "policy": {
                "regime": {
                    "n_trades_min_per_bucket": 20,
                    "polish_oos": {
                        "max_candidates": 3,
                        "min_candidates_agree": 2,
                        "min_wins": 5,
                        "min_median_delta_sharpe": 0.01,
                        "min_median_delta_maxdd": 1.0,
                    }
                }
            }
        }

        result = run_polish_oos_comparison(baseline_results, cscv_folds, trades_df, config)

        assert hasattr(result, "decision")
        assert hasattr(result, "candidates_results")
        assert hasattr(result, "n_candidates_agree")
        assert hasattr(result, "reason")


class TestStateMachine:
    """Test state machine runner."""

    def test_state_machine_loads_router(self):
        from scripts.state_machine import StateMachine

        sm = StateMachine()
        assert len(sm.router) > 0
        assert "INIT" in sm.router or any("INIT" in str(k) for k in sm.router.keys())

    def test_state_machine_dry_run(self):
        from scripts.state_machine import StateMachine

        sm = StateMachine()

        initial_state = {
            "asset": "TEST",
            "run_id": "test",
            "family_id": "A",
            "screen_long_success": True,
            "screen_short_success": True,
            "baseline_success": True,
            "hard_guards_pass": 7,
            "regime_signal_detected": False,
            "cscv_pass": True,
            "portfolio_pass": True,
            "holdout_enabled": False,
            "pbo_proxy_enabled": False,
            "portfolio_passed": True,
        }

        result = sm.run(initial_state="INIT", state=initial_state, dry_run=True, max_steps=50)

        assert "_final_state" in result
        assert "_total_steps" in result


class TestOrchestrator:
    """Test orchestrator."""

    def test_orchestrator_initializes(self):
        from scripts.orchestrator_v4_3 import OrchestratorV43

        orch = OrchestratorV43()
        assert orch.config is not None
        assert orch.state_machine is not None

    def test_orchestrator_dry_run(self):
        from scripts.orchestrator_v4_3 import OrchestratorV43

        orch = OrchestratorV43()
        result = orch.run(asset="TEST", run_id="dry_run_test", dry_run=True)

        assert "_final_state" in result


class TestGuards:
    """Test guards module."""

    def test_guard_regime_lookahead_exists(self):
        from scripts.guards import guard_regime_lookahead

        assert callable(guard_regime_lookahead)

    def test_guard_regime_lookahead_clean_data(self, trades_df, mock_data):
        from scripts.guards import guard_regime_lookahead
        import pandas as pd

        ohlcv_path = get_artifact_path(TEST_ASSET, TEST_RUN_ID, Phases.BASELINE, "ohlcv.parquet")
        ohlcv_df = pd.read_parquet(ohlcv_path)

        result = guard_regime_lookahead(trades_df, ohlcv_df)

        assert "passed" in result
        assert "violation_rate" in result
        if result["violation_rate"] > 0.05:
            print(f"\nDEBUG: violation_rate = {result['violation_rate']}")
            print(f"DEBUG: n_checked = {result['n_checked']}")
            print(f"DEBUG: n_violations = {result['n_violations']}")
            if result.get("violations"):
                print(f"DEBUG: first violation = {result['violations']}")

        assert result["violation_rate"] <= 0.05, (
            f"Lookahead violation rate too high: {result['violation_rate']}"
        )


# Run with: pytest scripts/tests/test_v4_3_integration.py -v
