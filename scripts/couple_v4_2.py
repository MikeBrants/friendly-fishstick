"""Build coupled candidates from screening results."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from crypto_backtest.v4.config import load_yaml, get_policy
from crypto_backtest.v4.coupling import build_coupled_matrix


def main() -> None:
    parser = argparse.ArgumentParser(description="v4.2 coupling step")
    parser.add_argument("--asset", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--k-long", type=int, default=None)
    parser.add_argument("--k-short", type=int, default=None)
    parser.add_argument("--max-couples", type=int, default=None)
    args = parser.parse_args()

    cfg = load_yaml("configs/families.yaml")
    policy = get_policy(cfg)
    coupling = policy.get("coupling", {})

    k_long = args.k_long if args.k_long is not None else int(coupling.get("k_long", 10))
    k_short = args.k_short if args.k_short is not None else int(coupling.get("k_short", 10))
    max_couples = (
        args.max_couples if args.max_couples is not None else int(coupling.get("max_couples", 100))
    )

    build_coupled_matrix(args.asset, args.run_id, k_long, k_short, max_couples)


if __name__ == "__main__":
    main()