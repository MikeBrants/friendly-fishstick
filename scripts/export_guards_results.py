"""
Export guards results — Filter assets by guard PASS/FAIL status.

Reads guards_summary CSV files and filters by hard guard pass status.

Usage:
    python scripts/export_guards_results.py --input "outputs/*_guards_summary_*.csv"
    python scripts/export_guards_results.py --input "outputs/*_guards_summary_*.csv" \
        --status PASS --output validated.txt
    python scripts/export_guards_results.py --input "outputs/*_guards_summary_*.csv" \
        --status FAIL --output rescue_candidates.txt

Reference: Issue #24, .cursor/rules/MASTER_PLAN.mdc 11 Guards
"""

from __future__ import annotations

import argparse
import glob
import sys
from pathlib import Path

import pandas as pd


# 7 hard guard columns (must all be True for PASS)
HARD_GUARD_COLS = [
    "guard001_pass",   # WFE Pardo >= 0.6
    "guard002_pass",   # Sensitivity < 15%
    "guard003_pass",   # Bootstrap CI > 1.0
    "guard005_pass",   # Top10 Concentration < 40%
    "guard006_pass",   # Stress1 Sharpe > 1.0
    "guard007_pass",   # Regime mismatch < 1%
    "guard_wfe_pass",  # WFE threshold
]


def load_guards_csvs(pattern: str) -> pd.DataFrame:
    """Load and concatenate guards summary CSVs matching a glob pattern."""
    files = sorted(glob.glob(pattern))
    if not files:
        print(f"[ERROR] No files matching pattern: {pattern}", file=sys.stderr)
        sys.exit(1)

    frames = []
    for f in files:
        try:
            df = pd.read_csv(f)
            df["_source"] = Path(f).name
            frames.append(df)
        except Exception as e:
            print(f"[WARN] Skipping {f}: {e}", file=sys.stderr)

    if not frames:
        print("[ERROR] No valid CSV files loaded", file=sys.stderr)
        sys.exit(1)

    return pd.concat(frames, ignore_index=True)


def classify_guards(df: pd.DataFrame) -> pd.DataFrame:
    """Add hard_guards_pass count and all_hard_pass boolean."""
    available = [c for c in HARD_GUARD_COLS if c in df.columns]

    if not available:
        print("[WARN] No hard guard columns found in CSV", file=sys.stderr)
        df["hard_guards_pass"] = 0
        df["all_hard_pass"] = False
        return df

    df["hard_guards_pass"] = df[available].sum(axis=1).astype(int)
    df["all_hard_pass"] = df[available].all(axis=1)
    return df


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Export assets filtered by guard PASS/FAIL status",
    )
    parser.add_argument("--input", required=True,
                        help='Glob pattern for guards CSVs (e.g. "outputs/*_guards_*.csv")')
    parser.add_argument("--output", default=None,
                        help="Output file (default: stdout)")
    parser.add_argument("--status", choices=["PASS", "FAIL", "ALL"], default="PASS",
                        help="Filter: PASS (all 7 hard guards), FAIL, or ALL (default: PASS)")
    parser.add_argument("--min-guards", type=int, default=None,
                        help="Min number of hard guards passing (overrides --status)")
    parser.add_argument("--verbose", action="store_true",
                        help="Print detailed results table")
    args = parser.parse_args()

    df = load_guards_csvs(args.input)
    df = classify_guards(df)

    if args.min_guards is not None:
        filtered = df[df["hard_guards_pass"] >= args.min_guards]
    elif args.status == "PASS":
        filtered = df[df["all_hard_pass"]]
    elif args.status == "FAIL":
        filtered = df[~df["all_hard_pass"]]
    else:
        filtered = df

    if filtered.empty:
        print(f"[INFO] No assets with status={args.status}", file=sys.stderr)
        return 0

    # Sort by guard pass count descending, then base_sharpe
    sort_cols = ["hard_guards_pass"]
    if "base_sharpe" in filtered.columns:
        sort_cols.append("base_sharpe")
    filtered = filtered.sort_values(sort_cols, ascending=False)

    assets = filtered["asset"].unique().tolist()
    result = " ".join(assets)

    if args.verbose:
        cols = ["asset", "hard_guards_pass", "all_hard_pass", "base_sharpe"]
        # Add individual guard columns
        for c in HARD_GUARD_COLS:
            if c in filtered.columns:
                cols.append(c)
        cols = [c for c in cols if c in filtered.columns]
        print(filtered[cols].to_string(index=False), file=sys.stderr)
        print(file=sys.stderr)

    if args.output:
        Path(args.output).write_text(result + "\n", encoding="utf-8")
        print(f"[OK] {len(assets)} assets written to {args.output}", file=sys.stderr)
    else:
        print(result)

    return 0


if __name__ == "__main__":
    sys.exit(main())
