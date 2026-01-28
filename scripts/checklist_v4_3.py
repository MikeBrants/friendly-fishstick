#!/usr/bin/env python3
"""FINAL TRIGGER v4.3 - Checklist and Audit Tool."""

import argparse
import json
from pathlib import Path

RUNS_DIR = Path("runs/v4_3")

REQUIRED_ARTIFACTS = {
    "screening": ["screen_long.json", "screen_short.json"],
    "coupling": ["coupled_candidates.json"],
    "baseline": ["baseline_best.json"],
    "regime": ["regime_stats.json"],
    "polish_oos": ["decision.json"],
    "guards": ["guards.json"],
    "pbo": ["pbo_proxy.json", "pbo_cscv.json"],
}


def check_run(asset: str, run_id: str) -> dict:
    run_path = RUNS_DIR / asset / run_id
    results = {"asset": asset, "run_id": run_id, "artifacts": {}, "polish_decision": None}

    for phase, files in REQUIRED_ARTIFACTS.items():
        results["artifacts"][phase] = []
        for f in files:
            path = run_path / phase / f
            results["artifacts"][phase].append({"file": f, "exists": path.exists()})

    polish_path = run_path / "polish_oos" / "decision.json"
    if polish_path.exists():
        with open(polish_path, encoding="utf-8") as f:
            data = json.load(f)
            results["polish_decision"] = data.get("decision")
            results["polish_candidates_agree"] = data.get("n_candidates_agree")

    return results


def print_checklist(result: dict) -> None:
    print(f"\n{'=' * 60}")
    print(f"  {result['asset']} / {result['run_id']}")
    print(f"{'=' * 60}")

    for phase, files in result["artifacts"].items():
        for f in files:
            icon = "OK" if f["exists"] else "MISSING"
            print(f"  {icon} {phase}/{f['file']}")

    if result.get("polish_decision"):
        print(
            f"\n  Polish OOS: {result['polish_decision']} "
            f"({result.get('polish_candidates_agree', '?')}/3 agree)"
        )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--asset", required=True)
    parser.add_argument("--run-id", required=True)
    args = parser.parse_args()

    result = check_run(args.asset, args.run_id)
    print_checklist(result)


if __name__ == "__main__":
    main()
