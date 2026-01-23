"""
Export screening results for validation phase.
Extracts SUCCESS/HIGH-POTENTIAL assets to pass to Phase 2 (strict validation).
"""

import argparse
import pandas as pd
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="Export screening results for validation")
    parser.add_argument("--input", required=True, help="Input CSV from Phase 1 screening")
    parser.add_argument("--status", choices=["SUCCESS", "FAIL", "HIGH-POTENTIAL"],
                       default="SUCCESS", help="Asset status to export")
    parser.add_argument("--output", default="candidates_for_validation.txt",
                       help="Output file with asset list")
    parser.add_argument("--min-sharpe", type=float, default=0.5,
                       help="Minimum OOS Sharpe to include")

    args = parser.parse_args()

    # Load scan results
    df = pd.read_csv(args.input)

    # Filter by status
    if args.status == "SUCCESS":
        filtered = df[df["status"] == "SUCCESS"]
    elif args.status == "HIGH-POTENTIAL":
        # FAIL but with decent metrics (for Phase 3A rescue)
        filtered = df[(df["status"] == "FAIL") &
                     (df["oos_sharpe"] >= args.min_sharpe)]
    else:
        filtered = df[df["status"] == args.status]

    assets = filtered["asset"].tolist()

    print(f"Found {len(assets)} assets with status='{args.status}'")
    print(f"Assets: {', '.join(assets)}")

    # Write to file
    Path(args.output).write_text(" ".join(assets))
    print(f"✅ Exported to: {args.output}")


if __name__ == "__main__":
    main()
