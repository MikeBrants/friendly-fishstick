"""
Run displacement grid optimization for a list of assets.
"""
from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd
from joblib import Parallel, delayed

sys.path.insert(0, str(Path(__file__).parent.parent))

from crypto_backtest.optimization.parallel_optimizer import (
    optimize_single_asset,
    _result_to_row,
)


def _run_one(
    asset: str,
    displacement: int,
    trials_atr: int,
    trials_ichi: int,
    mc_iterations: int,
    enforce_tp: bool,
) -> dict[str, object]:
    result = optimize_single_asset(
        asset=asset,
        data_dir="data",
        n_trials_atr=trials_atr,
        n_trials_ichi=trials_ichi,
        mc_iterations=mc_iterations,
        conservative=False,
        enforce_tp_progression=enforce_tp,
        fixed_displacement=displacement,
    )
    row = _result_to_row(result)
    row["fixed_displacement"] = displacement
    return row


def main() -> None:
    parser = argparse.ArgumentParser(description="Displacement grid runner.")
    parser.add_argument("--assets", nargs="+", required=True)
    parser.add_argument("--displacements", nargs="+", type=int, required=True)
    parser.add_argument("--trials-atr", type=int, default=50)
    parser.add_argument("--trials-ichi", type=int, default=50)
    parser.add_argument("--mc-iterations", type=int, default=500)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument(
        "--enforce-tp-progression",
        action="store_true",
        dest="enforce_tp_progression",
        help="Enforce TP1 < TP2 < TP3 with minimum gap (default: on)",
    )
    parser.add_argument(
        "--no-enforce-tp-progression",
        action="store_false",
        dest="enforce_tp_progression",
        help="Allow non-progressive TP levels",
    )
    parser.set_defaults(enforce_tp_progression=True)
    args = parser.parse_args()

    tasks = []
    for asset in args.assets:
        for disp in args.displacements:
            tasks.append((asset, disp))

    results = Parallel(n_jobs=args.workers)(
        delayed(_run_one)(
            asset,
            disp,
            args.trials_atr,
            args.trials_ichi,
            args.mc_iterations,
            args.enforce_tp_progression,
        )
        for asset, disp in tasks
    )

    df = pd.DataFrame(results)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = Path("outputs") / f"displacement_grid_batch3_{stamp}.csv"
    df.to_csv(out_path, index=False)

    print(f"Exported: {out_path}")

    summary = []
    for asset, asset_df in df.groupby("asset"):
        asset_df = asset_df.copy()
        asset_df = asset_df.sort_values("oos_sharpe", ascending=False)
        default_row = asset_df.loc[asset_df["displacement"] == 52]
        default_sharpe = float(default_row["oos_sharpe"].iloc[0]) if not default_row.empty else 0.0

        best_row = asset_df.iloc[0]
        summary.append(
            {
                "asset": asset,
                "best_displacement": int(best_row["displacement"]),
                "best_oos_sharpe": float(best_row["oos_sharpe"]),
                "best_wfe": float(best_row["wfe"]),
                "best_trades": int(best_row["oos_trades"]),
                "default_oos_sharpe": default_sharpe,
                "improvement": float(best_row["oos_sharpe"] - default_sharpe),
            }
        )

    summary_df = pd.DataFrame(summary)
    summary_path = Path("outputs") / f"displacement_grid_batch3_summary_{stamp}.csv"
    summary_df.to_csv(summary_path, index=False)
    print(f"Exported: {summary_path}")


if __name__ == "__main__":
    main()
