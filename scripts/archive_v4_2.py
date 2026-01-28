"""Archive summarizer for v4.2 runs."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from crypto_backtest.v4.artifacts import get_run_root, ensure_run_dirs


def _load_json(path: Path):
    if not path.exists():
        return None
    return json.loads(path.read_text())


def main() -> None:
    parser = argparse.ArgumentParser(description="v4.2 archive summarizer")
    parser.add_argument("--asset", required=True)
    parser.add_argument("--run-id", required=True)
    args = parser.parse_args()

    run_root = get_run_root(args.asset, args.run_id)
    ensure_run_dirs(run_root)

    summary = {
        "baseline": _load_json(run_root / "baseline" / "baseline_best.json"),
        "guards": _load_json(run_root / "guards" / "guards.json"),
        "pbo_proxy": _load_json(run_root / "pbo" / "pbo_proxy.json"),
        "pbo_cscv": _load_json(run_root / "pbo" / "pbo_cscv.json"),
        "regime": _load_json(run_root / "regime" / "regime.json"),
        "portfolio": _load_json(run_root / "portfolio" / "portfolio.json"),
        "holdout": _load_json(run_root / "holdout" / "holdout.json"),
        "repro": _load_json(run_root / "archive" / "repro_check.json"),
    }

    guards_passed = bool(summary.get("guards", {}).get("passed"))
    portfolio_passed = bool(summary.get("portfolio", {}).get("passed"))
    holdout = summary.get("holdout")
    holdout_passed = True if holdout is None else bool(holdout.get("passed"))

    decision = "PROD_READY" if (guards_passed and portfolio_passed and holdout_passed) else "REJECT"
    summary["decision"] = decision

    json_path = run_root / "archive" / "summary.json"
    json_path.write_text(json.dumps(summary, indent=2, default=str))

    md_lines = [
        f"# v4.2 Run Summary: {args.asset} / {args.run_id}",
        "",
        f"Decision: {decision}",
        "",
        "## Baseline",
        f"- Present: {summary['baseline'] is not None}",
        "## Guards",
        f"- Passed: {summary.get('guards', {}).get('passed')}",
        "## PBO",
        f"- Proxy: {summary.get('pbo_proxy', {}).get('pbo')}",
        f"- CSCV: {summary.get('pbo_cscv', {}).get('pbo')}",
        "## Regime",
        f"- Signal detected: {summary.get('regime', {}).get('regime_signal_detected')}",
        "## Portfolio",
        f"- Passed: {summary.get('portfolio', {}).get('passed')}",
        "## Holdout",
        f"- Passed: {holdout_passed}",
        "## Repro",
        f"- Passed: {summary.get('repro', {}).get('passed')}",
    ]

    md_path = run_root / "archive" / "summary.md"
    md_path.write_text("\n".join(md_lines))


if __name__ == "__main__":
    main()