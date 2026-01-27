#!/usr/bin/env python3
"""
Post-Batch Analysis Pipeline
Runs after Phase 2 batch completes to identify final winners.

Usage:
    python scripts/analyze_batch_results.py --batch-dir outputs/pr20_batch_complete_*
    python scripts/analyze_batch_results.py --batch-dir outputs/pr20_batch_complete_* --skip-regime
"""

from __future__ import annotations

import argparse
import glob
import os
import platform
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Iterable, List, Optional, Tuple

import numpy as np
import pandas as pd

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Optional imports aligned to repo API
try:
    from crypto_backtest.validation.cpcv import calculate_pbo
except Exception as exc:
    calculate_pbo = None
    _CPCV_IMPORT_ERROR = str(exc)
else:
    _CPCV_IMPORT_ERROR = None

try:
    from crypto_backtest.validation.multi_period import evaluate_multi_period
except Exception as exc:
    evaluate_multi_period = None
    _MULTI_IMPORT_ERROR = str(exc)
else:
    _MULTI_IMPORT_ERROR = None

try:
    from crypto_backtest.validation.worst_case import worst_case_path
except Exception as exc:
    worst_case_path = None
    _WORST_IMPORT_ERROR = str(exc)
else:
    _WORST_IMPORT_ERROR = None


def _print_header(title: str) -> None:
    print("=" * 60)
    print(title)
    print("=" * 60)


def _is_windows() -> bool:
    return platform.system().lower().startswith("win")


def _process_running(pattern: str) -> Optional[bool]:
    """Best-effort process check. Returns True/False, or None if unknown."""
    if _is_windows():
        # Try tasklist /v first (may include command line in window title)
        try:
            result = subprocess.run(
                ["tasklist", "/v", "/fo", "csv"],
                capture_output=True,
                text=True,
                check=False,
            )
            if result.returncode == 0 and pattern.lower() in result.stdout.lower():
                return True
        except Exception:
            pass

        # Fallback to wmic if available
        try:
            result = subprocess.run(
                [
                    "wmic",
                    "process",
                    "where",
                    f"CommandLine like '%{pattern}%'",
                    "get",
                    "ProcessId",
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            if result.returncode == 0:
                digits = "".join(ch for ch in result.stdout if ch.isdigit())
                if digits:
                    return True
        except Exception:
            pass

        return None

    # Unix-like
    try:
        result = subprocess.run(
            ["pgrep", "-f", pattern],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode == 0:
            return True
        if result.returncode == 1:
            return False
    except Exception:
        return None

    return None


def check_batch_complete(batch_dir: str) -> bool:
    running = _process_running("run_full_pipeline")
    if running is True:
        print("WARNING: Batch appears to be running. Results may be incomplete.")
        return False
    if running is None:
        print("WARNING: Unable to verify batch status on this platform.")
        return False
    return True


def _expand_batch_dirs(pattern: str) -> List[Path]:
    path = Path(pattern)
    if path.exists() and path.is_dir():
        return [path]

    matches = [Path(p) for p in glob.glob(pattern)]
    dirs = [p for p in matches if p.is_dir()]
    if dirs:
        return dirs

    files = [p for p in matches if p.is_file()]
    if files:
        parents = sorted({p.parent for p in files})
        return parents

    # Fallback to outputs
    fallback = Path("outputs")
    return [fallback]


def _collect_files(patterns: Iterable[str]) -> List[str]:
    files: List[str] = []
    for pattern in patterns:
        files.extend(glob.glob(pattern))
    return sorted(set(files))


def load_phase2_results(batch_dirs: List[Path]) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Load guard summaries and scan results; return merged, guards, scan DataFrames."""
    guard_files: List[str] = []
    scan_files: List[str] = []

    for batch_dir in batch_dirs:
        guard_files.extend(_collect_files([
            str(batch_dir / "*guards_summary*.csv"),
            str(batch_dir / "*guards*summary*.csv"),
            str(batch_dir / "*guards*.csv"),
        ]))
        scan_files.extend(_collect_files([
            str(batch_dir / "*multiasset_scan*.csv"),
            str(batch_dir / "*multi_asset_scan*.csv"),
            str(batch_dir / "*scan*.csv"),
        ]))

    guard_files.extend(_collect_files([
        "outputs/pr20_*guards_summary*.csv",
        "outputs/*guards_summary*.csv",
    ]))
    scan_files.extend(_collect_files([
        "outputs/pr20_*multiasset_scan*.csv",
        "outputs/pr20_*multi_asset_scan*.csv",
        "outputs/*multiasset_scan*.csv",
        "outputs/*multi_asset_scan*.csv",
    ]))

    guard_df = pd.DataFrame()
    if guard_files:
        guard_df = pd.concat([pd.read_csv(f) for f in guard_files], ignore_index=True)
        guard_df = guard_df.drop_duplicates(subset=["asset"], keep="last")
        print(f"Loaded guards: {len(guard_df)} assets from {len(guard_files)} files")

    scan_df = pd.DataFrame()
    if scan_files:
        scan_df = pd.concat([pd.read_csv(f) for f in scan_files], ignore_index=True)
        scan_df = scan_df.drop_duplicates(subset=["asset"], keep="last")
        print(f"Loaded scans: {len(scan_df)} assets from {len(scan_files)} files")

    if guard_df.empty and scan_df.empty:
        raise FileNotFoundError("No guard or scan results found for batch")

    if not guard_df.empty and not scan_df.empty:
        merged = guard_df.merge(scan_df, on="asset", how="left", suffixes=("", "_scan"))
    else:
        merged = guard_df if not guard_df.empty else scan_df

    return merged, guard_df, scan_df


def analyze_hard_guards(guard_df: pd.DataFrame, scan_df: pd.DataFrame, merged_df: pd.DataFrame) -> Tuple[List[str], List[str]]:
    """Separate PASS and FAIL based on available guard columns."""
    if not guard_df.empty:
        if "all_pass" in guard_df.columns:
            pass_assets = guard_df[guard_df["all_pass"] == True]["asset"].tolist()
            fail_assets = guard_df[guard_df["all_pass"] == False]["asset"].tolist()
            return pass_assets, fail_assets

        # Build pass mask from guard columns if available
        guard_cols = [
            "guard001_pass",
            "guard002_pass",
            "guard003_pass",
            "guard005_pass",
            "guard006_pass",
            "guard007_pass",
            "guard_wfe_pass",
        ]
        available = [c for c in guard_cols if c in guard_df.columns]
        if available:
            mask = guard_df[available].all(axis=1)
            pass_assets = guard_df[mask]["asset"].tolist()
            fail_assets = guard_df[~mask]["asset"].tolist()
            return pass_assets, fail_assets

    # Fallback to scan thresholds
    source = scan_df if not scan_df.empty else merged_df
    mask = pd.Series(True, index=source.index)
    if "wfe_pardo" in source.columns:
        mask &= source["wfe_pardo"] >= 0.6
    if "oos_trades" in source.columns:
        mask &= source["oos_trades"] >= 60
    if "mc_p" in source.columns:
        mask &= source["mc_p"] <= 0.05
    if "oos_sharpe" in source.columns:
        mask &= source["oos_sharpe"] >= 0.0

    pass_assets = source[mask]["asset"].tolist()
    fail_assets = source[~mask]["asset"].tolist()
    return pass_assets, fail_assets


def _find_returns_matrix(asset: str, search_dirs: Iterable[Path]) -> Optional[str]:
    patterns = []
    for directory in search_dirs:
        patterns.extend([
            str(directory / f"returns_matrix_{asset}_*.npy"),
            str(directory / f"*returns_matrix_{asset}*.npy"),
            str(directory / f"*{asset}*returns*.npy"),
        ])
    patterns.append(f"outputs/returns_matrix_{asset}_*.npy")

    matches = _collect_files(patterns)
    if not matches:
        return None

    return max(matches, key=lambda p: Path(p).stat().st_mtime)


def run_cpcv_analysis(assets: List[str], search_dirs: Iterable[Path]) -> pd.DataFrame:
    """Run CPCV/PBO analysis on assets."""
    results = []

    if calculate_pbo is None:
        print(f"WARNING: calculate_pbo not available: {_CPCV_IMPORT_ERROR}")
        return pd.DataFrame([
            {"asset": asset, "pbo": None, "pbo_verdict": "NO_PBO"}
            for asset in assets
        ])

    for asset in assets:
        returns_file = _find_returns_matrix(asset, search_dirs)
        if returns_file and os.path.exists(returns_file):
            try:
                returns = np.load(returns_file)
                pbo = float(calculate_pbo(returns))
                if pbo < 0.30:
                    verdict = "PASS"
                elif pbo < 0.50:
                    verdict = "MARGINAL"
                else:
                    verdict = "FAIL"
            except Exception as exc:
                pbo = None
                verdict = f"ERROR: {exc}"
        else:
            pbo = None
            verdict = "NO_DATA"

        results.append({
            "asset": asset,
            "pbo": pbo,
            "pbo_verdict": verdict,
            "returns_file": returns_file or "",
        })

        pbo_display = f"{pbo:.3f}" if pbo is not None else "N/A"
        print(f"  {asset}: PBO={pbo_display} -> {verdict}")

    return pd.DataFrame(results)


def run_multi_period_analysis(assets: List[str], search_dirs: Iterable[Path]) -> pd.DataFrame:
    """Run multi-period validation on best trial returns when available."""
    results = []
    if evaluate_multi_period is None:
        print(f"WARNING: evaluate_multi_period not available: {_MULTI_IMPORT_ERROR}")
        return pd.DataFrame()

    for asset in assets:
        returns_file = _find_returns_matrix(asset, search_dirs)
        if not returns_file or not os.path.exists(returns_file):
            results.append({
                "asset": asset,
                "consistency_ratio": None,
                "consistency_verdict": "NO_DATA",
            })
            continue

        try:
            returns = np.load(returns_file)
            # choose best trial by mean return
            trial_means = returns.mean(axis=1)
            best_idx = int(np.argmax(trial_means))
            series = pd.Series(returns[best_idx])
            result = evaluate_multi_period(series)
            results.append({
                "asset": asset,
                "consistency_ratio": result.consistency_ratio,
                "consistency_verdict": result.verdict,
            })
        except Exception as exc:
            results.append({
                "asset": asset,
                "consistency_ratio": None,
                "consistency_verdict": f"ERROR: {exc}",
            })

    return pd.DataFrame(results)


def run_worst_case_analysis(assets: List[str], search_dirs: Iterable[Path]) -> pd.DataFrame:
    """Run worst-case path analysis on CPCV results."""
    results = []
    if worst_case_path is None:
        print(f"WARNING: worst_case_path not available: {_WORST_IMPORT_ERROR}")
        return pd.DataFrame()

    for asset in assets:
        returns_file = _find_returns_matrix(asset, search_dirs)
        if not returns_file or not os.path.exists(returns_file):
            results.append({
                "asset": asset,
                "fragility_score": None,
                "fragility_verdict": "NO_DATA",
            })
            continue

        try:
            returns = np.load(returns_file)
            result = worst_case_path(returns)
            results.append({
                "asset": asset,
                "fragility_score": result.fragility_score,
                "fragility_verdict": result.verdict,
            })
        except Exception as exc:
            results.append({
                "asset": asset,
                "fragility_score": None,
                "fragility_verdict": f"ERROR: {exc}",
            })

    return pd.DataFrame(results)


def run_regime_stress(assets: List[str], output_dir: str) -> pd.DataFrame:
    """Run regime stress tests on assets."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    output_file = output_path / "regime_stress_results.csv"

    cmd = [
        sys.executable,
        str(PROJECT_ROOT / "scripts" / "run_regime_stress_test.py"),
        "--assets",
        *assets,
        "--regimes",
        "MARKDOWN",
        "SIDEWAYS",
        "--output",
        str(output_file),
    ]

    print("Running regime stress: " + " ".join(cmd))
    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        print("ERROR: Regime stress failed")
        print(result.stderr)
        return pd.DataFrame()

    if output_file.exists():
        return pd.read_csv(output_file)
    return pd.DataFrame()


def analyze_regime_results(df: pd.DataFrame) -> Tuple[List[str], List[str], List[str]]:
    """Categorize assets based on regime stress results."""
    winners: List[str] = []
    concerns: List[str] = []
    excluded: List[str] = []

    if df.empty:
        return winners, concerns, excluded

    for asset in df["asset"].unique():
        asset_data = df[df["asset"] == asset]
        sideways = asset_data[asset_data["regime"] == "SIDEWAYS"]
        markdown = asset_data[asset_data["regime"] == "MARKDOWN"]

        if not sideways.empty:
            sideways_row = sideways.iloc[0]
            if float(sideways_row.get("sharpe", 0.0)) < 0.0:
                excluded.append(asset)
                continue

        if not markdown.empty:
            markdown_row = markdown.iloc[0]
            trades = float(markdown_row.get("trades", 0.0))
            sharpe = float(markdown_row.get("sharpe", 0.0))
            if trades > 10 and sharpe < -2.0:
                concerns.append(asset)
                continue

        winners.append(asset)

    return winners, concerns, excluded


def _safe_row(df: pd.DataFrame, asset: str) -> dict:
    subset = df[df.get("asset") == asset]
    if subset.empty:
        return {}
    return subset.iloc[0].to_dict()


def generate_report(
    phase2_df: pd.DataFrame,
    hard_pass: List[str],
    hard_fail: List[str],
    cpcv_df: pd.DataFrame,
    regime_df: pd.DataFrame,
    winners: List[str],
    concerns: List[str],
    excluded: List[str],
    output_dir: str,
    multi_df: pd.DataFrame,
    worst_df: pd.DataFrame,
) -> str:
    """Generate final analysis report."""
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    report_file = Path(output_dir) / f"analysis_report_{timestamp}.md"

    report_lines = [
        "# Post-Batch Analysis Report",
        f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}",
        f"Batch: {output_dir}",
        "",
        "## Summary",
        "",
        "| Stage | Count | Assets |",
        "|-------|-------|--------|",
        f"| Phase 2 Input | {len(phase2_df)} | All |",
        f"| 7 Hard Guards PASS | {len(hard_pass)} | {', '.join(hard_pass[:10])}{'...' if len(hard_pass) > 10 else ''} |",
        f"| 7 Hard Guards FAIL | {len(hard_fail)} | {', '.join(hard_fail[:10])}{'...' if len(hard_fail) > 10 else ''} |",
        f"| CPCV PASS (PBO<0.30) | {len(cpcv_df[cpcv_df.get('pbo_verdict') == 'PASS']) if not cpcv_df.empty else 0} | - |",
        f"| Regime EXCLUDED | {len(excluded)} | {', '.join(excluded)} |",
        f"| WINNERS | {len(winners)} | {', '.join(winners)} |",
        f"| CONCERNS | {len(concerns)} | {', '.join(concerns)} |",
        "",
        "## Phase 2 Results (Hard Guards)",
        "",
        f"### PASS ({len(hard_pass)} assets)",
        "| Asset | OOS Sharpe | WFE | Trades |",
        "|-------|------------|-----|--------|",
    ]

    for asset in hard_pass:
        row = _safe_row(phase2_df, asset)
        sharpe = row.get("oos_sharpe", row.get("oos_sharpe_scan", "N/A"))
        wfe = row.get("wfe_pardo", row.get("wfe_pardo_scan", "N/A"))
        trades = row.get("oos_trades", row.get("oos_trades_scan", "N/A"))
        report_lines.append(f"| {asset} | {sharpe} | {wfe} | {trades} |")

    report_lines.extend([
        "",
        f"### FAIL ({len(hard_fail)} assets)",
        ", ".join(hard_fail) if hard_fail else "None",
        "",
        "## CPCV Analysis (PBO)",
        "",
        "| Asset | PBO | Verdict |",
        "|-------|-----|---------|",
    ])

    if not cpcv_df.empty:
        for _, row in cpcv_df.iterrows():
            pbo = row.get("pbo")
            pbo_display = f"{pbo:.3f}" if pbo is not None else "N/A"
            report_lines.append(f"| {row.get('asset')} | {pbo_display} | {row.get('pbo_verdict')} |")

    report_lines.extend([
        "",
        "## Regime Stress Results",
        "",
        "### EXCLUDED (SIDEWAYS Sharpe < 0)",
        ", ".join(excluded) if excluded else "None",
        "",
        "### CONCERNS (MARKDOWN issues)",
        ", ".join(concerns) if concerns else "None",
        "",
    ])

    if not multi_df.empty:
        report_lines.extend([
            "## Multi-Period Consistency",
            "",
            "| Asset | Consistency | Verdict |",
            "|-------|-------------|---------|",
        ])
        for _, row in multi_df.iterrows():
            ratio = row.get("consistency_ratio")
            ratio_display = f"{ratio:.2f}" if ratio is not None else "N/A"
            report_lines.append(f"| {row.get('asset')} | {ratio_display} | {row.get('consistency_verdict')} |")
        report_lines.append("")

    if not worst_df.empty:
        report_lines.extend([
            "## Worst-Case Path Analysis",
            "",
            "| Asset | Fragility Score | Verdict |",
            "|-------|-----------------|---------|",
        ])
        for _, row in worst_df.iterrows():
            score = row.get("fragility_score")
            score_display = f"{score:.3f}" if score is not None else "N/A"
            report_lines.append(f"| {row.get('asset')} | {score_display} | {row.get('fragility_verdict')} |")
        report_lines.append("")

    winners_block = "```\n" + " ".join(winners) + "\n```" if winners else "None"
    report_lines.extend([
        "## Final Winners",
        "",
        f"{len(winners)} assets ready for Phase 3+:",
        "",
        winners_block,
        "",
        "## Next Steps",
        "",
        "1. Phase 3A Rescue: run displacement optimization on CONCERNS",
        "2. Phase 3B Filter: test moderate/conservative filters on WINNERS",
        "3. Phase 4: Signal parity validation (Python vs Pine)",
        "4. Phase 5: Portfolio construction",
        "",
    ])

    report_file.write_text("\n".join(report_lines) + "\n", encoding="utf-8")
    print(f"Report saved: {report_file}")
    return str(report_file)


def main() -> int:
    parser = argparse.ArgumentParser(description="Analyze Phase 2 batch results")
    parser.add_argument("--batch-dir", required=True, help="Batch output directory or glob")
    parser.add_argument("--skip-regime", action="store_true", help="Skip regime stress tests")
    parser.add_argument("--output-dir", default="outputs", help="Output directory for reports")
    args = parser.parse_args()

    _print_header("POST-BATCH ANALYSIS PIPELINE")

    batch_dirs = _expand_batch_dirs(args.batch_dir)
    batch_dir_display = ", ".join(str(p) for p in batch_dirs)
    print(f"Batch directory: {batch_dir_display}")

    check_batch_complete(batch_dir_display)

    _print_header("STEP 1: Load Phase 2 Results")
    phase2_df, guards_df, scans_df = load_phase2_results(batch_dirs)

    _print_header("STEP 2: Analyze Hard Guards")
    hard_pass, hard_fail = analyze_hard_guards(guards_df, scans_df, phase2_df)
    print(f"PASS: {len(hard_pass)} assets")
    print(f"FAIL: {len(hard_fail)} assets")
    if not hard_pass:
        print("No assets passed hard guards. Exiting.")
        return 1

    _print_header("STEP 3: CPCV / PBO Analysis")
    search_dirs = batch_dirs + [Path("outputs")]
    cpcv_df = run_cpcv_analysis(hard_pass, search_dirs)
    cpcv_pass = cpcv_df[cpcv_df.get("pbo_verdict") == "PASS"]["asset"].tolist() if not cpcv_df.empty else []

    _print_header("STEP 4: Regime Stress Tests")
    if args.skip_regime:
        print("Skipped (--skip-regime)")
        regime_df = pd.DataFrame()
        winners = cpcv_pass if cpcv_pass else hard_pass
        concerns: List[str] = []
        excluded: List[str] = []
    else:
        assets_to_test = cpcv_pass if cpcv_pass else hard_pass
        regime_df = run_regime_stress(assets_to_test, args.output_dir)
        if not regime_df.empty:
            winners, concerns, excluded = analyze_regime_results(regime_df)
        else:
            print("No regime results; using CPCV PASS as winners")
            winners = cpcv_pass if cpcv_pass else hard_pass
            concerns = []
            excluded = []

    _print_header("STEP 5: Multi-Period and Worst-Case")
    multi_df = run_multi_period_analysis(winners, search_dirs)
    worst_df = run_worst_case_analysis(winners, search_dirs)

    _print_header("STEP 6: Generate Report")
    generate_report(
        phase2_df,
        hard_pass,
        hard_fail,
        cpcv_df,
        regime_df,
        winners,
        concerns,
        excluded,
        args.output_dir,
        multi_df,
        worst_df,
    )

    _print_header("FINAL SUMMARY")
    print(f"Phase 2 Input:     {len(phase2_df)}")
    print(f"Hard Guards PASS:  {len(hard_pass)}")
    print(f"CPCV PASS:         {len(cpcv_pass)}")
    print(f"Regime EXCLUDED:   {len(excluded)}")
    print(f"CONCERNS:          {len(concerns)}")
    print(f"WINNERS:           {len(winners)}")
    print(f"WINNERS: {' '.join(winners)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
