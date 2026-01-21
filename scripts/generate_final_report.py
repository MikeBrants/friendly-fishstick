"""
Generate final validation report from guards, portfolio, and stress outputs.
"""
from __future__ import annotations

import argparse
from glob import glob
from pathlib import Path

import pandas as pd


def _load_guard_results(pattern: str) -> pd.DataFrame:
    files = sorted(glob(pattern))
    if not files:
        return pd.DataFrame()
    frames = [pd.read_csv(path) for path in files]
    df = pd.concat(frames, ignore_index=True)
    if "asset" in df.columns:
        df = df.drop_duplicates(subset=["asset"], keep="last")
    return df


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate final validation report.")
    parser.add_argument("--guards-results", required=True, help="Glob for guard summary CSVs")
    parser.add_argument("--portfolio-metrics", required=True)
    parser.add_argument("--stress-results", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    guards_df = _load_guard_results(args.guards_results)
    portfolio_df = pd.read_csv(args.portfolio_metrics)
    stress_df = pd.read_csv(args.stress_results)

    lines = []
    lines.append("# FINAL VALIDATION REPORT")
    lines.append("")

    lines.append("## Per-Asset Guard Results")
    if guards_df.empty:
        lines.append("No guard results found.")
    else:
        cols = [
            "asset",
            "guard001_p_value",
            "guard002_variance_pct",
            "guard003_sharpe_ci_lower",
            "guard006_stress1_sharpe",
            "guard007_mismatch_pct",
            "guard005_top10_pct",
            "guard_wfe",
            "all_pass",
        ]
        existing_cols = [c for c in cols if c in guards_df.columns]
        lines.append(guards_df[existing_cols].to_markdown(index=False))

    lines.append("")
    lines.append("## Portfolio Summary")
    lines.append(portfolio_df.to_markdown(index=False))

    lines.append("")
    lines.append("## Portfolio Stress Tests")
    lines.append(stress_df.to_markdown(index=False))

    output_path = Path(args.output)
    output_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Exported: {output_path}")


if __name__ == "__main__":
    main()
