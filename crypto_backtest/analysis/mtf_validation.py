"""
Multi-timeframe validation using 1H params on 4H and 1D data.
Resamples 1H OHLCV and evaluates OOS metrics per timeframe.
"""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import pandas as pd

from crypto_backtest.config.scan_assets import OPTIM_CONFIG
from crypto_backtest.optimization.parallel_optimizer import (
    build_strategy_params,
    load_data,
    run_backtest,
    split_data,
)


RESAMPLE_MAP = {
    "4H": "4H",
    "1D": "1D",
}


def _resample_ohlcv(df: pd.DataFrame, rule: str) -> pd.DataFrame:
    agg = {
        "open": "first",
        "high": "max",
        "low": "min",
        "close": "last",
        "volume": "sum",
    }
    resampled = df.resample(rule).agg(agg).dropna()
    return resampled


def _scaled_warmup(timeframe: str, warmup_bars_1h: int) -> int:
    if timeframe == "4H":
        return max(1, warmup_bars_1h // 4)
    if timeframe == "1D":
        return max(1, warmup_bars_1h // 24)
    return warmup_bars_1h


def _oos_metrics_for_tf(
    df_1h: pd.DataFrame,
    params: dict[str, Any],
    timeframe: str,
    warmup_bars_1h: int,
) -> dict[str, float]:
    df_tf = _resample_ohlcv(df_1h, RESAMPLE_MAP[timeframe])
    warmup = _scaled_warmup(timeframe, warmup_bars_1h)
    df_tf = df_tf.iloc[warmup:]
    splits = OPTIM_CONFIG.get("validation_split", (0.6, 0.2, 0.2))
    _, _, df_oos = split_data(df_tf, splits)

    strategy_params = build_strategy_params(
        sl_mult=params["sl_mult"],
        tp1_mult=params["tp1_mult"],
        tp2_mult=params["tp2_mult"],
        tp3_mult=params["tp3_mult"],
        tenkan=params["tenkan"],
        kijun=params["kijun"],
        tenkan_5=params["tenkan_5"],
        kijun_5=params["kijun_5"],
    )
    return run_backtest(df_oos, strategy_params)


def run_mtf_validation(
    scan_results_path: str,
    output_path: str,
    data_dir: str = "data",
    mtf_sharpe_min: float = 1.5,
) -> pd.DataFrame:
    scan_df = pd.read_csv(scan_results_path)
    pass_df = scan_df[scan_df["status"].str.startswith("SUCCESS", na=False)].copy()

    rows: list[dict[str, Any]] = []
    warmup_bars_1h = OPTIM_CONFIG["warmup_bars"]

    for _, row in pass_df.iterrows():
        asset = row["asset"]
        df_1h = load_data(asset, data_dir)

        params = {
            "sl_mult": row["sl_mult"],
            "tp1_mult": row["tp1_mult"],
            "tp2_mult": row["tp2_mult"],
            "tp3_mult": row["tp3_mult"],
            "tenkan": row["tenkan"],
            "kijun": row["kijun"],
            "tenkan_5": row["tenkan_5"],
            "kijun_5": row["kijun_5"],
        }

        metrics_4h = _oos_metrics_for_tf(df_1h, params, "4H", warmup_bars_1h)
        metrics_1d = _oos_metrics_for_tf(df_1h, params, "1D", warmup_bars_1h)

        sharpe_4h = float(metrics_4h.get("sharpe", 0.0))
        sharpe_1d = float(metrics_1d.get("sharpe", 0.0))

        tf_specific = max(sharpe_4h, sharpe_1d) < mtf_sharpe_min
        tf_reason = "NO_TF_SHARPE>=%.1f" % mtf_sharpe_min if tf_specific else ""

        rows.append({
            "asset": asset,
            "base_oos_sharpe": float(row.get("oos_sharpe", 0.0)),
            "base_oos_return": float(row.get("oos_return", 0.0)),
            "base_oos_max_dd": float(row.get("oos_max_dd", 0.0)),
            "oos_sharpe_4h": sharpe_4h,
            "oos_return_4h": float(metrics_4h.get("total_return", 0.0)),
            "oos_max_dd_4h": float(metrics_4h.get("max_drawdown", 0.0)),
            "oos_trades_4h": int(metrics_4h.get("trades", 0)),
            "oos_sharpe_1d": sharpe_1d,
            "oos_return_1d": float(metrics_1d.get("total_return", 0.0)),
            "oos_max_dd_1d": float(metrics_1d.get("max_drawdown", 0.0)),
            "oos_trades_1d": int(metrics_1d.get("trades", 0)),
            "warmup_bars_4h": _scaled_warmup("4H", warmup_bars_1h),
            "warmup_bars_1d": _scaled_warmup("1D", warmup_bars_1h),
            "tf_specific": tf_specific,
            "tf_specific_reason": tf_reason,
        })

    result_df = pd.DataFrame(rows)
    Path(output_path).parent.mkdir(exist_ok=True)
    result_df.to_csv(output_path, index=False)
    return result_df


def main() -> None:
    parser = argparse.ArgumentParser(description="Multi-timeframe validation on PASS assets")
    parser.add_argument("--scan", required=True, help="Path to multiasset scan CSV")
    parser.add_argument("--output", default="outputs/mtf_validation.csv", help="Output CSV path")
    parser.add_argument("--data-dir", default="data")
    parser.add_argument("--mtf-sharpe-min", type=float, default=1.5)
    args = parser.parse_args()

    run_mtf_validation(
        scan_results_path=args.scan,
        output_path=args.output,
        data_dir=args.data_dir,
        mtf_sharpe_min=args.mtf_sharpe_min,
    )


if __name__ == "__main__":
    main()
