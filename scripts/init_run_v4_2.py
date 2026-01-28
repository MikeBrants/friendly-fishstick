"""Initialize v4.2 run directory layout and metadata."""
from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from crypto_backtest.v4.artifacts import get_run_root, ensure_run_dirs, write_run_metadata


def main() -> None:
    parser = argparse.ArgumentParser(description="Initialize v4.2 run layout")
    parser.add_argument("--asset", required=True, help="Asset symbol (e.g., ETH)")
    parser.add_argument("--run-id", required=True, help="Run identifier")
    args = parser.parse_args()

    run_root = get_run_root(args.asset, args.run_id)
    ensure_run_dirs(run_root)
    metadata = {
        "asset": args.asset,
        "run_id": args.run_id,
        "version": "4.2",
        "created_utc": datetime.now(timezone.utc).isoformat(),
    }
    write_run_metadata(run_root, metadata)
    print(f"Initialized run at {run_root}")


if __name__ == "__main__":
    main()