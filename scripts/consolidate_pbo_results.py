#!/usr/bin/env python3
"""
PBO Consolidation Script
========================
Scans outputs/ for *_pbo_*.json files and generates a consolidated report.

Usage:
    python scripts/consolidate_pbo_results.py
    python scripts/consolidate_pbo_results.py --outputs-dir outputs --threshold-pass 0.50 --threshold-exclu 0.70

Output:
    - Console summary with verdicts
    - CSV file: outputs/pbo_consolidated_<timestamp>.csv
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd


# Default thresholds (aligned with MASTER_PLAN)
DEFAULT_THRESHOLD_PASS = 0.50
DEFAULT_THRESHOLD_EXCLU = 0.70


def load_pbo_json(filepath: Path) -> dict[str, Any] | None:
    """Load a single PBO JSON file."""
    try:
        with open(filepath, "r") as f:
            data = json.load(f)
        return data
    except (json.JSONDecodeError, IOError) as e:
        print(f"⚠️  Error loading {filepath}: {e}")
        return None


def extract_asset_from_filename(filename: str) -> str:
    """Extract asset name from filename like 'BTC_pbo_20260127_131138.json'."""
    parts = filename.split("_pbo_")
    if parts:
        return parts[0]
    return filename


def classify_pbo(
    pbo_value: float | None,
    threshold_pass: float,
    threshold_exclu: float,
) -> tuple[str, str]:
    """Classify PBO value into verdict and emoji."""
    if pbo_value is None:
        return "ERROR", "❓"
    if pbo_value < threshold_pass:
        return "PASS", "✅"
    elif pbo_value < threshold_exclu:
        return "QUARANTINE", "⚠️"
    else:
        return "EXCLU", "🔴"


def scan_pbo_files(outputs_dir: Path) -> list[Path]:
    """Find all PBO JSON files in outputs directory."""
    pattern = "*_pbo_*.json"
    files = sorted(outputs_dir.glob(pattern))
    return files


def consolidate_pbo_results(
    outputs_dir: str = "outputs",
    threshold_pass: float = DEFAULT_THRESHOLD_PASS,
    threshold_exclu: float = DEFAULT_THRESHOLD_EXCLU,
) -> pd.DataFrame:
    """Main consolidation logic."""
    outputs_path = Path(outputs_dir)
    
    if not outputs_path.exists():
        print(f"❌ Directory not found: {outputs_dir}")
        sys.exit(1)
    
    pbo_files = scan_pbo_files(outputs_path)
    
    if not pbo_files:
        print(f"❌ No PBO files found in {outputs_dir}")
        print(f"   Expected pattern: *_pbo_*.json")
        sys.exit(1)
    
    print(f"📁 Found {len(pbo_files)} PBO files")
    print(f"📊 Thresholds: PASS < {threshold_pass}, EXCLU > {threshold_exclu}")
    print("=" * 60)
    
    rows = []
    for filepath in pbo_files:
        asset = extract_asset_from_filename(filepath.name)
        data = load_pbo_json(filepath)
        
        if data is None:
            rows.append({
                "asset": asset,
                "pbo": None,
                "pass_guard": False,
                "n_combinations": None,
                "interpretation": "ERROR",
                "verdict": "ERROR",
                "file": filepath.name,
            })
            continue
        
        pbo_value = data.get("pbo")
        pass_guard = data.get("pass", False)
        n_combinations = data.get("n_combinations")
        interpretation = data.get("interpretation", "")
        
        verdict, emoji = classify_pbo(pbo_value, threshold_pass, threshold_exclu)
        
        rows.append({
            "asset": asset,
            "pbo": pbo_value,
            "pass_guard": pass_guard,
            "n_combinations": n_combinations,
            "interpretation": interpretation,
            "verdict": verdict,
            "file": filepath.name,
        })
        
        # Console output
        pbo_str = f"{pbo_value:.4f}" if pbo_value is not None else "N/A"
        print(f"{emoji} {asset:8s} | PBO: {pbo_str:8s} | {verdict:12s} | {interpretation}")
    
    df = pd.DataFrame(rows)
    return df


def print_summary(df: pd.DataFrame) -> None:
    """Print categorized summary."""
    print("\n" + "=" * 60)
    print("📊 SUMMARY BY VERDICT")
    print("=" * 60)
    
    for verdict in ["PASS", "QUARANTINE", "EXCLU", "ERROR"]:
        subset = df[df["verdict"] == verdict]
        if len(subset) > 0:
            assets = ", ".join(subset["asset"].tolist())
            emoji = {"PASS": "✅", "QUARANTINE": "⚠️", "EXCLU": "🔴", "ERROR": "❓"}[verdict]
            print(f"{emoji} {verdict:12s} ({len(subset):2d}): {assets}")
    
    # Stats
    print("\n" + "-" * 60)
    total = len(df)
    pass_count = len(df[df["verdict"] == "PASS"])
    quarantine_count = len(df[df["verdict"] == "QUARANTINE"])
    exclu_count = len(df[df["verdict"] == "EXCLU"])
    
    print(f"Total: {total} assets")
    print(f"  PASS:       {pass_count:3d} ({pass_count/total*100:.1f}%)")
    print(f"  QUARANTINE: {quarantine_count:3d} ({quarantine_count/total*100:.1f}%)")
    print(f"  EXCLU:      {exclu_count:3d} ({exclu_count/total*100:.1f}%)")
    
    if pass_count > 0:
        print(f"\n🎯 Candidats PROD: {', '.join(df[df['verdict'] == 'PASS']['asset'].tolist())}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Consolidate PBO results from batch validation runs."
    )
    parser.add_argument(
        "--outputs-dir",
        default="outputs",
        help="Directory containing *_pbo_*.json files (default: outputs)",
    )
    parser.add_argument(
        "--threshold-pass",
        type=float,
        default=DEFAULT_THRESHOLD_PASS,
        help=f"PBO threshold for PASS verdict (default: {DEFAULT_THRESHOLD_PASS})",
    )
    parser.add_argument(
        "--threshold-exclu",
        type=float,
        default=DEFAULT_THRESHOLD_EXCLU,
        help=f"PBO threshold for EXCLU verdict (default: {DEFAULT_THRESHOLD_EXCLU})",
    )
    parser.add_argument(
        "--output-csv",
        default=None,
        help="Output CSV path (default: outputs/pbo_consolidated_<timestamp>.csv)",
    )
    parser.add_argument(
        "--no-save",
        action="store_true",
        help="Don't save CSV, only print to console",
    )
    
    args = parser.parse_args()
    
    print("\n" + "=" * 60)
    print("🔍 PBO CONSOLIDATION REPORT")
    print("=" * 60 + "\n")
    
    df = consolidate_pbo_results(
        outputs_dir=args.outputs_dir,
        threshold_pass=args.threshold_pass,
        threshold_exclu=args.threshold_exclu,
    )
    
    print_summary(df)
    
    # Save CSV
    if not args.no_save:
        if args.output_csv:
            output_path = Path(args.output_csv)
        else:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = Path(args.outputs_dir) / f"pbo_consolidated_{timestamp}.csv"
        
        df.to_csv(output_path, index=False)
        print(f"\n💾 Saved: {output_path}")
    
    print("\n" + "=" * 60)
    print("✅ Consolidation complete")
    print("=" * 60)


if __name__ == "__main__":
    main()
