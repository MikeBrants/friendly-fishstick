"""
Export screening results — Filter assets from Phase 1 scan CSVs.

Reads multiasset_scan CSV files, applies threshold filters, and outputs
a space-separated list of qualifying asset names.

Usage:
    python scripts/export_screening_results.py --input "outputs/screening_*.csv"
    python scripts/export_screening_results.py --input "outputs/screening_*.csv" \
        --wfe 0.5 --sharpe 0.5 --trades 50 --short-min 25 --short-max 75
    python scripts/export_screening_results.py --input "outputs/screening_*.csv" \
        --output candidates.txt

Reference: Issue #24, .cursor/rules/MASTER_PLAN.mdc Phase 1 thresholds
"""

from __future__ import annotations

import argparse
import glob
import sys
from pathlib import Path

import pandas as pd


def load_scan_csvs(pattern: str) -> pd.DataFrame:
    """Load and concatenate scan CSVs matching a glob pattern."""
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


def apply_filters(
    df: pd.DataFrame,
    *,
    wfe: float = 0.5,
    sharpe: float = 0.5,
    trades: int = 50,
    short_min: float = 25.0,
    short_max: float = 75.0,
    status: str | None = "SUCCESS",
) -> pd.DataFrame:
    """Apply Phase 1 screening thresholds."""
    if status and "status" in df.columns:
        df = df[df["status"] == status]

    if "wfe_pardo" in df.columns:
        df = df[df["wfe_pardo"] >= wfe]
    if "oos_sharpe" in df.columns:
        df = df[df["oos_sharpe"] >= sharpe]
    if "oos_trades" in df.columns:
        df = df[df["oos_trades"] >= trades]

    # SHORT ratio filter (if column exists)
    if "short_pct" in df.columns:
        df = df[(df["short_pct"] >= short_min) & (df["short_pct"] <= short_max)]

    return df


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Export qualifying assets from Phase 1 screening CSVs",
    )
    parser.add_argument("--input", required=True,
                        help='Glob pattern for scan CSVs (e.g. "outputs/screening_*.csv")')
    parser.add_argument("--output", default=None,
                        help="Output file (default: stdout)")
    parser.add_argument("--status", default="SUCCESS",
                        help="Filter by status column (default: SUCCESS, use '' to disable)")
    parser.add_argument("--wfe", type=float, default=0.5,
                        help="Min WFE Pardo (default: 0.5)")
    parser.add_argument("--sharpe", type=float, default=0.5,
                        help="Min OOS Sharpe (default: 0.5)")
    parser.add_argument("--trades", type=int, default=50,
                        help="Min OOS trades (default: 50)")
    parser.add_argument("--short-min", type=float, default=25.0,
                        help="Min SHORT%% (default: 25)")
    parser.add_argument("--short-max", type=float, default=75.0,
                        help="Max SHORT%% (default: 75)")
    parser.add_argument("--verbose", action="store_true",
                        help="Print detailed results table")
    args = parser.parse_args()

    df = load_scan_csvs(args.input)
    status_filter = args.status if args.status else None
    filtered = apply_filters(
        df,
        wfe=args.wfe,
        sharpe=args.sharpe,
        trades=args.trades,
        short_min=args.short_min,
        short_max=args.short_max,
        status=status_filter,
    )

    if filtered.empty:
        print("[INFO] No assets pass all filters", file=sys.stderr)
        return 0

    # Sort by OOS Sharpe descending
    if "oos_sharpe" in filtered.columns:
        filtered = filtered.sort_values("oos_sharpe", ascending=False)

    assets = filtered["asset"].unique().tolist()
    result = " ".join(assets)

    if args.verbose:
        cols = ["asset", "oos_sharpe", "wfe_pardo", "oos_trades"]
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
