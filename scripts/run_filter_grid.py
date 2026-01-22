"""
Filter combination grid search.

Runs the full pipeline for each filter mode on a single asset and collects
scan/guards results in a summary CSV.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from datetime import datetime
from glob import glob
from pathlib import Path

import pandas as pd

from config.filter_modes import FILTER_MODES


def _latest_new_file(pattern: str, before: list[str]) -> str | None:
    after = sorted(glob(pattern))
    new_files = [path for path in after if path not in before]
    if new_files:
        return new_files[-1]
    return after[-1] if after else None


def _read_asset_row(df: pd.DataFrame, asset: str) -> pd.Series:
    row = df[df["asset"] == asset]
    if row.empty:
        raise ValueError(f"Asset not found in results: {asset}")
    return row.iloc[0]


def run_mode(asset: str, mode: str, workers: int, trials_atr: int, trials_ichi: int) -> dict:
    before_scan = sorted(glob("outputs/multiasset_scan_*.csv"))
    before_guards = sorted(glob("outputs/multiasset_guards_summary_*.csv"))

    cmd = [
        sys.executable,
        str(Path(__file__).parent / "run_full_pipeline.py"),
        "--assets",
        asset,
        "--workers",
        str(workers),
        "--trials-atr",
        str(trials_atr),
        "--trials-ichi",
        str(trials_ichi),
        "--enforce-tp-progression",
        "--optimization-mode",
        mode,
        "--skip-download",
        "--run-guards",
    ]

    subprocess.run(cmd, check=False)

    scan_file = _latest_new_file("outputs/multiasset_scan_*.csv", before_scan)
    guards_file = _latest_new_file("outputs/multiasset_guards_summary_*.csv", before_guards)

    if not scan_file or not guards_file:
        return {
            "mode": mode,
            "status": "ERROR",
            "error": "Missing scan or guards output",
        }

    try:
        scan = pd.read_csv(scan_file)
        guards = pd.read_csv(guards_file)
        scan_row = _read_asset_row(scan, asset)
        guard_row = _read_asset_row(guards, asset)

        return {
            "mode": mode,
            "status": scan_row.get("status", "UNKNOWN"),
            "oos_sharpe": round(float(scan_row.get("oos_sharpe", 0.0)), 2),
            "wfe": round(float(scan_row.get("wfe", 0.0)), 2),
            "oos_trades": int(scan_row.get("oos_trades", 0)),
            "sens_var": round(float(guard_row.get("guard002_variance_pct", 0.0)), 2),
            "guard002_pass": bool(guard_row.get("guard002_pass", False)),
            "all_pass": bool(guard_row.get("all_pass", False)),
            "base_sharpe": round(float(guard_row.get("base_sharpe", 0.0)), 2),
            "scan_file": scan_file,
            "guards_file": guards_file,
            "error": "",
        }
    except Exception as exc:
        return {
            "mode": mode,
            "status": "ERROR",
            "error": str(exc),
        }


def main() -> None:
    parser = argparse.ArgumentParser(description="Filter grid search for one asset.")
    parser.add_argument("asset", nargs="?", default="ETH")
    parser.add_argument("--workers", type=int, default=6)
    parser.add_argument("--trials-atr", type=int, default=100)
    parser.add_argument("--trials-ichi", type=int, default=100)
    args = parser.parse_args()

    modes = list(FILTER_MODES.keys())
    results = []

    print("=" * 60)
    print(f"FILTER GRID SEARCH - {args.asset}")
    print(f"Testing {len(modes)} filter combinations")
    print("=" * 60)

    for index, mode in enumerate(modes, 1):
        print(f"\n[{index}/{len(modes)}] Running {mode}...")
        result = run_mode(args.asset, mode, args.workers, args.trials_atr, args.trials_ichi)
        results.append(result)
        if "oos_sharpe" in result:
            print(
                "  -> Sharpe={sharpe}, WFE={wfe}, Trades={trades}, Sens={sens}%, Pass={pass_flag}".format(
                    sharpe=result.get("oos_sharpe", "NA"),
                    wfe=result.get("wfe", "NA"),
                    trades=result.get("oos_trades", "NA"),
                    sens=result.get("sens_var", "NA"),
                    pass_flag="PASS" if result.get("all_pass") else "FAIL",
                )
            )

    df = pd.DataFrame(results)
    ts = datetime.now().strftime("%Y%m%d_%H%M")
    output_file = f"outputs/filter_grid_results_{args.asset}_{ts}.csv"
    df.to_csv(output_file, index=False)

    print("\n" + "=" * 60)
    print("FILTER GRID RESULTS SUMMARY")
    print("=" * 60)

    df_valid = df[df["status"] != "ERROR"].copy()
    if not df_valid.empty:
        df_sorted = df_valid.sort_values("oos_sharpe", ascending=False)
        print(
            df_sorted[
                [
                    "mode",
                    "oos_sharpe",
                    "wfe",
                    "oos_trades",
                    "sens_var",
                    "guard002_pass",
                    "all_pass",
                ]
            ].to_string(index=False)
        )

    print("\n" + "-" * 60)
    all_pass = df[df["all_pass"] == True] if "all_pass" in df.columns else pd.DataFrame()
    if not all_pass.empty:
        best = all_pass.sort_values("oos_sharpe", ascending=False).iloc[0]
        print(
            f"BEST (all guards pass): {best['mode']} "
            f"Sharpe={best['oos_sharpe']}, WFE={best['wfe']}, Sens={best['sens_var']}%"
        )
    else:
        print("No mode passed all guards.")

    sens_pass = df[df["guard002_pass"] == True] if "guard002_pass" in df.columns else pd.DataFrame()
    if not sens_pass.empty:
        best_sens = sens_pass.sort_values("oos_sharpe", ascending=False).iloc[0]
        print(
            f"BEST (sens<10%): {best_sens['mode']} "
            f"Sharpe={best_sens['oos_sharpe']}, WFE={best_sens['wfe']}, "
            f"Sens={best_sens['sens_var']}%"
        )

    if not df_valid.empty:
        best_sharpe = df_valid.sort_values("oos_sharpe", ascending=False).iloc[0]
        print(
            f"BEST Sharpe: {best_sharpe['mode']} "
            f"Sharpe={best_sharpe['oos_sharpe']}, WFE={best_sharpe['wfe']}, "
            f"Sens={best_sharpe['sens_var']}%"
        )

    print(f"\nResults saved to: {output_file}")


if __name__ == "__main__":
    main()
