"""v4.2 definition-of-done checklist."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from crypto_backtest.v4.artifacts import get_run_root
from crypto_backtest.v4.config import load_yaml, get_policy


def _check(path: Path) -> tuple[bool, str]:
    return (path.exists(), path.as_posix())


def main() -> None:
    parser = argparse.ArgumentParser(description="v4.2 checklist")
    parser.add_argument("--asset", required=True)
    parser.add_argument("--run-id", required=True)
    args = parser.parse_args()

    families_cfg = load_yaml("configs/families.yaml")
    policy = get_policy(families_cfg)
    holdout_enabled = bool(policy.get("data", {}).get("holdout", {}).get("enabled", False))

    run_root = get_run_root(args.asset, args.run_id)

    required = [
        run_root / "screening" / "screen_long.json",
        run_root / "screening" / "screen_short.json",
        run_root / "coupling" / "coupled_candidates.json",
        run_root / "baseline" / "baseline_best.json",
        run_root / "guards" / "guards.json",
        run_root / "pbo" / "pbo_proxy.json",
        run_root / "pbo" / "pbo_cscv.json",
        run_root / "regime" / "regime.json",
        run_root / "portfolio" / "portfolio.json",
        run_root / "archive" / "repro_check.json",
        run_root / "archive" / "summary.json",
        run_root / "archive" / "summary.md",
    ]

    if holdout_enabled:
        required.append(run_root / "holdout" / "holdout.json")

    all_passed = True
    for path in required:
        ok, label = _check(path)
        status = "PASS" if ok else "FAIL"
        print(f"{status}: {label}")
        if not ok:
            all_passed = False

    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()