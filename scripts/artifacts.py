"""FINAL TRIGGER v4.3 - Artifacts Path Management"""

from pathlib import Path
from typing import Optional

# Pipeline version - single source of truth
PIPELINE_VERSION = "v4_3"
RUNS_BASE_DIR = Path("runs")


def get_artifact_path(
    asset: str,
    run_id: str,
    phase: str,
    filename: str,
    version: str = PIPELINE_VERSION,
) -> Path:
    """
    Build artifact path for any phase.

    Args:
        asset: Asset symbol (e.g., "ETH", "BTC")
        run_id: Run identifier (e.g., "v4.3_001")
        phase: Pipeline phase (screening, coupling, baseline, regime, polish_oos, guards, pbo, portfolio, archive)
        filename: Artifact filename
        version: Pipeline version (default: v4_3)

    Returns:
        Path object for the artifact
    """
    return RUNS_BASE_DIR / version / asset / run_id / phase / filename


def get_run_dir(asset: str, run_id: str, version: str = PIPELINE_VERSION) -> Path:
    """Get the base directory for a run."""
    return RUNS_BASE_DIR / version / asset / run_id


def ensure_artifact_dir(
    asset: str, run_id: str, phase: str, version: str = PIPELINE_VERSION
) -> Path:
    """Create artifact directory if it doesn't exist and return path."""
    dir_path = RUNS_BASE_DIR / version / asset / run_id / phase
    dir_path.mkdir(parents=True, exist_ok=True)
    return dir_path


def list_runs(asset: Optional[str] = None, version: str = PIPELINE_VERSION) -> list:
    """List all runs, optionally filtered by asset."""
    version_dir = RUNS_BASE_DIR / version
    if not version_dir.exists():
        return []

    runs = []
    if asset:
        asset_dir = version_dir / asset
        if asset_dir.exists():
            for run_dir in asset_dir.iterdir():
                if run_dir.is_dir():
                    runs.append({"asset": asset, "run_id": run_dir.name})
    else:
        for asset_dir in version_dir.iterdir():
            if asset_dir.is_dir():
                for run_dir in asset_dir.iterdir():
                    if run_dir.is_dir():
                        runs.append({"asset": asset_dir.name, "run_id": run_dir.name})

    return sorted(runs, key=lambda x: (x["asset"], x["run_id"]))


# Artifact filename constants
class ArtifactNames:
    # Screening
    SCREEN_LONG = "screen_long.json"
    SCREEN_SHORT = "screen_short.json"

    # Coupling
    COUPLED_CANDIDATES = "coupled_candidates.json"

    # Baseline
    BASELINE_BEST = "baseline_best.json"
    TRADES_PARQUET = "trades.parquet"

    # Regime
    REGIME_STATS = "regime_stats.json"

    # Polish OOS
    POLISH_DECISION = "decision.json"

    # Guards
    GUARDS_RESULT = "guards.json"

    # PBO
    PBO_PROXY = "pbo_proxy.json"
    PBO_CSCV = "pbo_cscv.json"
    CSCV_FOLDS = "cscv_folds.json"

    # Portfolio
    PORTFOLIO = "portfolio.json"

    # Archive
    SUMMARY = "summary.json"


# Phase names
class Phases:
    SCREENING = "screening"
    COUPLING = "coupling"
    BASELINE = "baseline"
    REGIME = "regime"
    POLISH_OOS = "polish_oos"
    GUARDS = "guards"
    PBO = "pbo"
    PORTFOLIO = "portfolio"
    HOLDOUT = "holdout"
    ARCHIVE = "archive"
