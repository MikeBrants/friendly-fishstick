"""
Orchestrator — Single entry point for FINAL TRIGGER v2 pipeline.

Usage:
    python scripts/orchestrator.py --phase 1 --assets ETH BTC DOGE
    python scripts/orchestrator.py --phase 2 --assets ETH
    python scripts/orchestrator.py --phase 3 --assets ETH --rescue displacement
    python scripts/orchestrator.py --phase 3 --assets ETH --rescue filter
    python scripts/orchestrator.py --phase 4 --assets ETH
    python scripts/orchestrator.py --status
    python scripts/orchestrator.py --portfolio

Reference: Issue #24, .cursor/rules/MASTER_PLAN.mdc
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Configuration — mirrors MASTER_PLAN.mdc (single source of truth)
# ---------------------------------------------------------------------------

PHASE_CONFIG = {
    1: {
        "name": "Screening",
        "workers": 10,
        "trials_atr": 200,
        "trials_ichi": 200,
        "guards": False,
        "thresholds": {"wfe": 0.5, "sharpe": 0.5, "trades": 50, "short_min": 25, "short_max": 75},
    },
    2: {
        "name": "Validation",
        "workers": 1,
        "trials_atr": 300,
        "trials_ichi": 300,
        "guards": True,
        "thresholds": {"wfe": 0.6, "sharpe": 1.0, "trades": 60},
    },
    3: {
        "name": "Rescue",
        "workers": 1,
        "trials_atr": 300,
        "trials_ichi": 300,
        "guards": True,
        "thresholds": {"wfe": 0.6, "sharpe": 1.0, "trades": 40},
    },
    4: {
        "name": "Regime Stress Test",
        "workers": 1,
        "trials_atr": 0,
        "trials_ichi": 0,
        "guards": False,
        "thresholds": {"sideways_sharpe": 0.0, "markdown_sharpe": -2.0},
    },
    5: {
        "name": "Portfolio Construction",
        "workers": 1,
        "trials_atr": 0,
        "trials_ichi": 0,
        "guards": False,
        "thresholds": {"max_correlation": 0.5},
    },
    6: {
        "name": "Production",
        "workers": 1,
        "trials_atr": 0,
        "trials_ichi": 0,
        "guards": False,
        "thresholds": {},
    },
}

HARD_GUARDS = {
    "guard001_wfe_pardo": {"op": ">=", "value": 0.6},
    "guard002_sensitivity": {"op": "<", "value": 15},
    "guard003_bootstrap_ci": {"op": ">", "value": 1.0},
    "guard004_montecarlo_p": {"op": "<", "value": 0.05},
    "guard005_top10": {"op": "<", "value": 40},
    "guard006_trades_oos": {"op": ">=", "value": 60},
    "guard007_bars_is": {"op": ">=", "value": 8000},
}

SOFT_GUARDS = {
    "guard008_pbo": {"op": "<", "value": 0.50},
    "guard009_dsr": {"op": ">", "value": 85},
    "guard010_cpcv": {"op": ">", "value": 0.8},
    "guard011_psr": {"op": ">", "value": 95},
}

DISPLACEMENTS = [26, 52, 78]
FILTER_CASCADE = ["baseline", "moderate", "conservative"]

SCRIPTS_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPTS_DIR.parent


# ---------------------------------------------------------------------------
# Phase runners
# ---------------------------------------------------------------------------

def _run(cmd: list[str]) -> int:
    """Run a subprocess, print the command, return exit code."""
    print(f"\n>>> {' '.join(cmd)}\n")
    result = subprocess.run(cmd, cwd=str(PROJECT_ROOT))
    return result.returncode


def run_phase_1(assets: list[str], prefix: str) -> int:
    """Phase 1 — Screening (multi-worker, no guards)."""
    cfg = PHASE_CONFIG[1]
    cmd = [
        sys.executable,
        str(SCRIPTS_DIR / "run_full_pipeline.py"),
        "--assets", *assets,
        "--trials-atr", str(cfg["trials_atr"]),
        "--trials-ichi", str(cfg["trials_ichi"]),
        "--enforce-tp-progression",
        "--workers", str(cfg["workers"]),
        "--skip-guards",
        "--output-prefix", prefix,
    ]
    return _run(cmd)


def run_phase_2(assets: list[str], prefix: str) -> int:
    """Phase 2 — Validation (workers=1, guards ON)."""
    cfg = PHASE_CONFIG[2]
    cmd = [
        sys.executable,
        str(SCRIPTS_DIR / "run_full_pipeline.py"),
        "--assets", *assets,
        "--optimization-mode", "baseline",
        "--trials-atr", str(cfg["trials_atr"]),
        "--trials-ichi", str(cfg["trials_ichi"]),
        "--enforce-tp-progression",
        "--run-guards",
        "--workers", str(cfg["workers"]),
        "--output-prefix", prefix,
    ]
    return _run(cmd)


def run_phase_3_displacement(assets: list[str], prefix: str) -> int:
    """Phase 3A — Displacement rescue: test d26, d52, d78."""
    cfg = PHASE_CONFIG[3]
    for disp in DISPLACEMENTS:
        tag = f"{prefix}_d{disp}"
        cmd = [
            sys.executable,
            str(SCRIPTS_DIR / "run_full_pipeline.py"),
            "--assets", *assets,
            "--fixed-displacement", str(disp),
            "--trials-atr", str(cfg["trials_atr"]),
            "--trials-ichi", str(cfg["trials_ichi"]),
            "--enforce-tp-progression",
            "--run-guards",
            "--workers", str(cfg["workers"]),
            "--output-prefix", tag,
        ]
        rc = _run(cmd)
        if rc != 0:
            print(f"[WARN] Displacement d{disp} returned exit code {rc}")
    return 0


def run_phase_3_filter(assets: list[str], prefix: str) -> int:
    """Phase 3B — Filter rescue: baseline -> moderate -> conservative."""
    cfg = PHASE_CONFIG[3]
    for mode in FILTER_CASCADE:
        tag = f"{prefix}_{mode}"
        cmd = [
            sys.executable,
            str(SCRIPTS_DIR / "run_full_pipeline.py"),
            "--assets", *assets,
            "--optimization-mode", mode,
            "--trials-atr", str(cfg["trials_atr"]),
            "--trials-ichi", str(cfg["trials_ichi"]),
            "--enforce-tp-progression",
            "--run-guards",
            "--workers", str(cfg["workers"]),
            "--output-prefix", tag,
        ]
        rc = _run(cmd)
        if rc != 0:
            print(f"[WARN] Filter mode {mode} returned exit code {rc}")
    return 0


def run_phase_4(assets: list[str]) -> int:
    """Phase 4 — Regime stress test."""
    script = SCRIPTS_DIR / "run_regime_stress_test.py"
    if not script.exists():
        print(f"[ERROR] {script} not found")
        return 1
    for asset in assets:
        for regime in ("MARKDOWN", "SIDEWAYS"):
            cmd = [
                sys.executable,
                str(script),
                "--asset", asset,
                "--regimes", regime,
            ]
            _run(cmd)
    return 0


def run_phase_5(prefix: str) -> int:
    """Phase 5 — Portfolio construction."""
    script = SCRIPTS_DIR / "portfolio_construction.py"
    if not script.exists():
        print(f"[ERROR] {script} not found")
        return 1
    cmd = [
        sys.executable,
        str(script),
        "--output-prefix", prefix,
    ]
    return _run(cmd)


def show_status() -> int:
    """Print current project state from status/project-state.md."""
    state_file = PROJECT_ROOT / "status" / "project-state.md"
    if not state_file.exists():
        print("[ERROR] status/project-state.md not found")
        return 1
    sys.stdout.buffer.write(state_file.read_text(encoding="utf-8").encode("utf-8"))
    return 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        description="FINAL TRIGGER v2 — Pipeline Orchestrator (Issue #24)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --phase 1 --assets ETH BTC DOGE
  %(prog)s --phase 2 --assets ETH
  %(prog)s --phase 3 --assets ETH --rescue displacement
  %(prog)s --phase 3 --assets ETH --rescue filter
  %(prog)s --phase 4 --assets ETH
  %(prog)s --status
  %(prog)s --portfolio
""",
    )
    parser.add_argument("--phase", type=int, choices=[1, 2, 3, 4, 5, 6],
                        help="Pipeline phase to execute")
    parser.add_argument("--assets", nargs="+", help="Asset list (e.g. ETH BTC)")
    parser.add_argument("--rescue", choices=["displacement", "filter"],
                        help="Rescue type for Phase 3")
    parser.add_argument("--prefix", default=None,
                        help="Output prefix (auto-generated if omitted)")
    parser.add_argument("--status", action="store_true",
                        help="Show current project state")
    parser.add_argument("--portfolio", action="store_true",
                        help="Run portfolio construction (Phase 5)")
    args = parser.parse_args()

    # --status shortcut
    if args.status:
        return show_status()

    # --portfolio shortcut
    if args.portfolio:
        prefix = args.prefix or "portfolio"
        return run_phase_5(prefix)

    # Phase execution
    if args.phase is None:
        parser.print_help()
        return 1

    if args.phase in (1, 2, 3, 4) and not args.assets:
        parser.error(f"--assets required for Phase {args.phase}")

    from datetime import datetime
    ts = datetime.now().strftime("%Y%m%d_%H%M")
    prefix = args.prefix or f"phase{args.phase}_{ts}"

    if args.phase == 1:
        return run_phase_1(args.assets, prefix)
    elif args.phase == 2:
        return run_phase_2(args.assets, prefix)
    elif args.phase == 3:
        rescue = args.rescue or "displacement"
        if rescue == "displacement":
            return run_phase_3_displacement(args.assets, prefix)
        else:
            return run_phase_3_filter(args.assets, prefix)
    elif args.phase == 4:
        return run_phase_4(args.assets)
    elif args.phase == 5:
        return run_phase_5(prefix)
    elif args.phase == 6:
        print("[Phase 6] Production — Manual steps required:")
        print("  1. Update crypto_backtest/config/asset_config.py")
        print("  2. Update status/project-state.md")
        print("  3. Verify reproducibility (2 identical runs)")
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
