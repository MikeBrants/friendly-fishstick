"""
Run Manager - Centralized management of backtest run outputs.

Implements structured folder organization:
    outputs/
    ├── run_20260121_120000/
    │   ├── manifest.json
    │   ├── scan.csv
    │   ├── guards.csv
    │   └── params/
    │       ├── BTC.json
    │       └── ETH.json
    └── run_20260121_150000/
        └── ...

Usage:
    # Create new run
    run = RunManager.create_run(description="Initial scan BTC/ETH")
    run.save_scan_results(df)
    run.save_params("BTC", params_dict)

    # List existing runs
    runs = RunManager.list_runs()

    # Load specific run
    run = RunManager.load_run("run_20260121_120000")
    scan_df = run.load_scan_results()
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

import pandas as pd


class Run:
    """Represents a single backtest run with all its outputs."""

    def __init__(self, run_id: str, base_dir: Path = Path("outputs")):
        """
        Initialize a Run instance.

        Args:
            run_id: Run identifier (e.g., "run_20260121_120000")
            base_dir: Base outputs directory
        """
        self.run_id = run_id
        self.base_dir = base_dir
        self.run_dir = base_dir / run_id
        self.params_dir = self.run_dir / "params"
        self.manifest_path = self.run_dir / "manifest.json"

    def ensure_dirs(self) -> None:
        """Create run directories if they don't exist."""
        self.run_dir.mkdir(parents=True, exist_ok=True)
        self.params_dir.mkdir(exist_ok=True)

    def save_manifest(
        self,
        description: str = "",
        assets: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """
        Save run metadata to manifest.json.

        Args:
            description: Human-readable description of the run
            assets: List of assets included in this run
            metadata: Additional metadata (e.g., config, hyperparams)
        """
        self.ensure_dirs()
        manifest = {
            "run_id": self.run_id,
            "timestamp": datetime.now().isoformat(),
            "description": description,
            "assets": assets or [],
            "metadata": metadata or {},
        }
        with open(self.manifest_path, "w") as f:
            json.dump(manifest, f, indent=2)

    def load_manifest(self) -> dict[str, Any]:
        """Load manifest.json metadata."""
        if not self.manifest_path.exists():
            return {}
        with open(self.manifest_path) as f:
            return json.load(f)

    def save_scan_results(self, df: pd.DataFrame) -> Path:
        """Save scan results CSV."""
        self.ensure_dirs()
        path = self.run_dir / "scan.csv"
        df.to_csv(path, index=False)
        return path

    def load_scan_results(self) -> pd.DataFrame | None:
        """Load scan results CSV."""
        path = self.run_dir / "scan.csv"
        if not path.exists():
            return None
        return pd.read_csv(path)

    def save_guards_summary(self, df: pd.DataFrame) -> Path:
        """Save guards summary CSV."""
        self.ensure_dirs()
        path = self.run_dir / "guards.csv"
        df.to_csv(path, index=False)
        return path

    def load_guards_summary(self) -> pd.DataFrame | None:
        """Load guards summary CSV."""
        path = self.run_dir / "guards.csv"
        if not path.exists():
            return None
        return pd.read_csv(path)

    def save_params(self, asset: str, params: dict[str, Any]) -> Path:
        """Save optimal parameters for an asset."""
        self.ensure_dirs()
        path = self.params_dir / f"{asset}.json"
        with open(path, "w") as f:
            json.dump(params, f, indent=2)
        return path

    def load_params(self, asset: str) -> dict[str, Any] | None:
        """Load optimal parameters for an asset."""
        path = self.params_dir / f"{asset}.json"
        if not path.exists():
            return None
        with open(path) as f:
            return json.load(f)

    def list_params(self) -> list[str]:
        """List all assets with saved parameters."""
        if not self.params_dir.exists():
            return []
        return sorted([p.stem for p in self.params_dir.glob("*.json")])

    def save_file(self, filename: str, df: pd.DataFrame) -> Path:
        """Save arbitrary CSV file to run directory."""
        self.ensure_dirs()
        path = self.run_dir / filename
        df.to_csv(path, index=False)
        return path

    def load_file(self, filename: str) -> pd.DataFrame | None:
        """Load arbitrary CSV file from run directory."""
        path = self.run_dir / filename
        if not path.exists():
            return None
        return pd.read_csv(path)

    def exists(self) -> bool:
        """Check if run directory exists."""
        return self.run_dir.exists()

    def get_summary(self) -> dict[str, Any]:
        """Get summary of run contents."""
        manifest = self.load_manifest()
        scan_df = self.load_scan_results()
        guards_df = self.load_guards_summary()

        return {
            "run_id": self.run_id,
            "description": manifest.get("description", ""),
            "timestamp": manifest.get("timestamp", ""),
            "assets": manifest.get("assets", []),
            "has_scan": scan_df is not None,
            "has_guards": guards_df is not None,
            "params_count": len(self.list_params()),
            "scan_assets_count": len(scan_df) if scan_df is not None else 0,
            "guards_assets_count": len(guards_df) if guards_df is not None else 0,
        }


class RunManager:
    """Factory and utilities for managing runs."""

    @staticmethod
    def generate_run_id() -> str:
        """Generate a timestamped run ID."""
        return f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    @staticmethod
    def create_run(
        description: str = "",
        assets: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
        base_dir: Path = Path("outputs"),
    ) -> Run:
        """
        Create a new run with manifest.

        Args:
            description: Human-readable description
            assets: List of assets to be processed
            metadata: Additional metadata
            base_dir: Base outputs directory

        Returns:
            Run instance
        """
        run_id = RunManager.generate_run_id()
        run = Run(run_id, base_dir)
        run.save_manifest(description, assets, metadata)
        return run

    @staticmethod
    def list_runs(base_dir: Path = Path("outputs")) -> list[Run]:
        """
        List all runs in reverse chronological order.

        Args:
            base_dir: Base outputs directory

        Returns:
            List of Run instances, newest first
        """
        if not base_dir.exists():
            return []

        run_dirs = sorted(
            [d for d in base_dir.iterdir() if d.is_dir() and d.name.startswith("run_")],
            reverse=True,
        )
        return [Run(d.name, base_dir) for d in run_dirs]

    @staticmethod
    def load_run(run_id: str, base_dir: Path = Path("outputs")) -> Run:
        """
        Load an existing run.

        Args:
            run_id: Run identifier
            base_dir: Base outputs directory

        Returns:
            Run instance

        Raises:
            FileNotFoundError: If run doesn't exist
        """
        run = Run(run_id, base_dir)
        if not run.exists():
            raise FileNotFoundError(f"Run '{run_id}' not found in {base_dir}")
        return run

    @staticmethod
    def get_latest_run(base_dir: Path = Path("outputs")) -> Run | None:
        """Get the most recent run."""
        runs = RunManager.list_runs(base_dir)
        return runs[0] if runs else None

    @staticmethod
    def find_runs_with_asset(asset: str, base_dir: Path = Path("outputs")) -> list[Run]:
        """Find all runs that include a specific asset."""
        runs = RunManager.list_runs(base_dir)
        matching_runs = []
        for run in runs:
            manifest = run.load_manifest()
            if asset in manifest.get("assets", []):
                matching_runs.append(run)
        return matching_runs
