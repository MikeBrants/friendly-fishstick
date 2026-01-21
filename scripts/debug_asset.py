"""
Debug assets with suspicious scan results and optionally rerun guards.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent))

from crypto_backtest.optimization.parallel_optimizer import load_data


def _latest_scan() -> str:
    scan_files = sorted(Path("outputs").glob("multiasset_scan_*.csv"))
    if not scan_files:
        raise FileNotFoundError("No multiasset_scan_*.csv found in outputs/")
    return str(scan_files[-1])


def _data_quality(asset: str) -> dict[str, Any]:
    data = load_data(asset, "data")
    bars = int(len(data))
    nan_rows = int(data.isna().any(axis=1).sum())
    dup_index = int(data.index.duplicated().sum())
    return {
        "bars": bars,
        "nan_rows": nan_rows,
        "duplicate_index": dup_index,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Investigate anomaly assets.")
    parser.add_argument("--assets", nargs="+", required=True)
    parser.add_argument("--params-file", default=None)
    parser.add_argument("--min-trades", type=int, default=60)
    parser.add_argument("--min-bars", type=int, default=10000)
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument("--check-trades-count", action="store_true")
    parser.add_argument("--check-wfe-calc", action="store_true")
    parser.add_argument("--check-data-quality", action="store_true")
    parser.add_argument("--rerun-if-valid", action="store_true")
    parser.add_argument("--guards-workers", type=int, default=4)
    args = parser.parse_args()

    params_file = args.params_file or _latest_scan()
    scan_df = pd.read_csv(params_file)

    rows = []
    valid_assets = []

    for asset in args.assets:
        row = scan_df.loc[scan_df["asset"] == asset]
        if row.empty:
            rows.append(
                {
                    "asset": asset,
                    "status": "MISSING",
                    "notes": "not_found_in_scan",
                }
            )
            continue
        row = row.iloc[0]

        wfe_calc = None
        wfe_diff = None
        if args.check_wfe_calc and float(row.get("is_sharpe", 0) or 0) > 0:
            wfe_calc = float(row.get("oos_sharpe", 0)) / float(row.get("is_sharpe", 0))
            wfe_diff = abs(float(row.get("wfe", 0)) - wfe_calc)

        data_info = {"bars": None, "nan_rows": None, "duplicate_index": None}
        if args.check_data_quality:
            data_info = _data_quality(asset)

        trades_ok = True
        if args.check_trades_count:
            trades_ok = int(row.get("oos_trades", 0) or 0) >= args.min_trades

        bars_ok = True
        if args.check_data_quality and data_info["bars"] is not None:
            bars_ok = data_info["bars"] >= args.min_bars

        should_rerun = trades_ok and bars_ok
        if should_rerun:
            valid_assets.append(asset)

        rows.append(
            {
                "asset": asset,
                "status": row.get("status"),
                "oos_sharpe": row.get("oos_sharpe"),
                "wfe": row.get("wfe"),
                "wfe_calc": wfe_calc,
                "wfe_diff": wfe_diff,
                "oos_trades": row.get("oos_trades"),
                "total_bars": row.get("total_bars"),
                "bars": data_info["bars"],
                "nan_rows": data_info["nan_rows"],
                "duplicate_index": data_info["duplicate_index"],
                "trades_ok": trades_ok,
                "bars_ok": bars_ok,
                "should_rerun_guards": should_rerun,
                "notes": row.get("fail_reason"),
            }
        )

        if args.verbose:
            print(f"[{asset}] status={row.get('status')} oos_sharpe={row.get('oos_sharpe')} wfe={row.get('wfe')}")

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = Path("outputs") / f"anomaly_investigation_{stamp}.csv"
    pd.DataFrame(rows).to_csv(out_path, index=False)
    print(f"Exported: {out_path}")

    if args.rerun_if_valid and valid_assets:
        cmd = [
            sys.executable,
            str(Path(__file__).parent / "run_guards_multiasset.py"),
            "--assets",
            *valid_assets,
            "--params-file",
            params_file,
            "--workers",
            str(args.guards_workers),
        ]
        subprocess.run(cmd, check=False)


if __name__ == "__main__":
    main()
