"""
Cluster guard: validate clustering by re-backtesting OOS with cluster params.
Exports per-asset loss percentages and failure flags.
"""
from __future__ import annotations

import argparse
import json
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


PARAM_COLS = [
    "sl_mult", "tp1_mult", "tp2_mult", "tp3_mult",
    "tenkan", "kijun", "tenkan_5", "kijun_5",
]


def _round_cluster_params(params: dict[str, float]) -> dict[str, Any]:
    params = dict(params)
    params["sl_mult"] = round(params["sl_mult"] * 4) / 4
    params["tp1_mult"] = round(params["tp1_mult"] * 4) / 4
    params["tp2_mult"] = round(params["tp2_mult"] * 2) / 2
    params["tp3_mult"] = round(params["tp3_mult"] * 2) / 2
    params["tenkan"] = int(round(params["tenkan"]))
    params["kijun"] = int(round(params["kijun"]))
    params["tenkan_5"] = int(round(params["tenkan_5"]))
    params["kijun_5"] = int(round(params["kijun_5"]))
    return params


def _derive_cluster_params(
    df: pd.DataFrame,
    assets: list[str],
    method: str = "median",
) -> dict[str, Any]:
    subset = df[df["asset"].isin(assets)]
    if subset.empty:
        return {}

    if method == "median":
        params = subset[PARAM_COLS].median()
    elif method in {"centroid", "mean"}:
        params = subset[PARAM_COLS].mean()
    else:
        raise ValueError(f"Unknown param source: {method}")

    return _round_cluster_params(params.to_dict())


def _safe_loss_pct(individual: float, cluster: float) -> float:
    denom = abs(individual)
    if denom == 0:
        return 0.0
    return (individual - cluster) / denom * 100.0


def _run_oos_backtest(
    asset: str,
    params: dict[str, Any],
    data_dir: str,
) -> dict[str, float]:
    df = load_data(asset, data_dir)
    df = df.iloc[OPTIM_CONFIG["warmup_bars"]:]
    splits = OPTIM_CONFIG.get("validation_split", (0.6, 0.2, 0.2))
    _, _, df_oos = split_data(df, splits)

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


def _export_validated_params(
    scan_df: pd.DataFrame,
    output_path: str,
) -> pd.DataFrame:
    """Export validated parameters for successful assets."""
    pass_df = scan_df[scan_df["status"].str.startswith("SUCCESS", na=False)].copy()
    rows = []
    for _, row in pass_df.iterrows():
        rows.append({
            "asset": row["asset"],
            "mode": "individual",
            "sl_mult": row["sl_mult"],
            "tp1_mult": row["tp1_mult"],
            "tp2_mult": row["tp2_mult"],
            "tp3_mult": row["tp3_mult"],
            "tenkan": row["tenkan"],
            "kijun": row["kijun"],
            "tenkan_5": row["tenkan_5"],
            "kijun_5": row["kijun_5"],
        })

    params_df = pd.DataFrame(rows)
    Path(output_path).parent.mkdir(exist_ok=True)
    params_df.to_csv(output_path, index=False)
    return params_df


def run_cluster_guard(
    scan_results_path: str,
    cluster_json_path: str,
    output_path: str,
    param_source: str = "median",
    loss_threshold: float = 15.0,
    data_dir: str = "data",
    validated_params_path: str = "outputs/validated_params.csv",
) -> pd.DataFrame:
    scan_df = pd.read_csv(scan_results_path)
    with open(cluster_json_path, "r") as handle:
        cluster_info = json.load(handle)

    clusters = cluster_info.get("clusters", {})
    if not clusters:
        raise ValueError("No clusters found in cluster analysis JSON.")

    rows: list[dict[str, Any]] = []

    for cluster_name, cluster_data in clusters.items():
        assets = list(cluster_data.get("assets", []))
        cluster_size = len(assets)
        cluster_params = _derive_cluster_params(scan_df, assets, param_source)
        if not cluster_params:
            continue

        cluster_rows: list[dict[str, Any]] = []
        cluster_fail = cluster_size < 3
        cluster_fail_reason = []
        if cluster_fail:
            cluster_fail_reason.append("CLUSTER_SIZE<3")

        for asset in assets:
            asset_rows = scan_df[scan_df["asset"] == asset]
            if asset_rows.empty:
                cluster_rows.append({
                    "asset": asset,
                    "cluster": cluster_name,
                    "cluster_size": cluster_size,
                    "param_source": param_source,
                    "status": "ERROR",
                    "error": "asset_missing_in_scan",
                })
                cluster_fail = True
                cluster_fail_reason.append("ASSET_MISSING")
                continue

            asset_row = asset_rows.iloc[0]
            try:
                cluster_metrics = _run_oos_backtest(asset, cluster_params, data_dir)
                status = "OK"
                error = ""
            except Exception as exc:
                cluster_metrics = {"sharpe": 0.0, "total_return": 0.0, "max_drawdown": 0.0}
                status = "ERROR"
                error = str(exc)
                cluster_fail = True
                cluster_fail_reason.append("BACKTEST_ERROR")

            sharpe_indiv = float(asset_row.get("oos_sharpe", 0.0))
            return_indiv = float(asset_row.get("oos_return", 0.0))
            max_dd_indiv = float(asset_row.get("oos_max_dd", 0.0))

            sharpe_cluster = float(cluster_metrics.get("sharpe", 0.0))
            return_cluster = float(cluster_metrics.get("total_return", 0.0))
            max_dd_cluster = float(cluster_metrics.get("max_drawdown", 0.0))

            sharpe_loss_pct = _safe_loss_pct(sharpe_indiv, sharpe_cluster)
            return_loss_pct = _safe_loss_pct(return_indiv, return_cluster)
            max_dd_loss_pct = _safe_loss_pct(max_dd_indiv, max_dd_cluster)

            asset_loss_exceeds = any(
                loss_pct > loss_threshold
                for loss_pct in (sharpe_loss_pct, return_loss_pct, max_dd_loss_pct)
            )
            if asset_loss_exceeds:
                cluster_fail = True
                cluster_fail_reason.append("LOSS_PCT")

            cluster_rows.append({
                "asset": asset,
                "cluster": cluster_name,
                "cluster_size": cluster_size,
                "param_source": param_source,
                "sl_mult": cluster_params["sl_mult"],
                "tp1_mult": cluster_params["tp1_mult"],
                "tp2_mult": cluster_params["tp2_mult"],
                "tp3_mult": cluster_params["tp3_mult"],
                "tenkan": cluster_params["tenkan"],
                "kijun": cluster_params["kijun"],
                "tenkan_5": cluster_params["tenkan_5"],
                "kijun_5": cluster_params["kijun_5"],
                "sharpe_indiv": sharpe_indiv,
                "sharpe_cluster": sharpe_cluster,
                "sharpe_loss_pct": sharpe_loss_pct,
                "return_indiv": return_indiv,
                "return_cluster": return_cluster,
                "return_loss_pct": return_loss_pct,
                "max_dd_indiv": max_dd_indiv,
                "max_dd_cluster": max_dd_cluster,
                "max_dd_loss_pct": max_dd_loss_pct,
                "asset_loss_exceeds": asset_loss_exceeds,
                "status": status,
                "error": error,
            })

        if cluster_fail_reason:
            cluster_fail_reason = sorted(set(cluster_fail_reason))
        reason_str = ";".join(cluster_fail_reason)

        for row in cluster_rows:
            row["flag_cluster_fail"] = cluster_fail
            row["cluster_fail_reason"] = reason_str

        rows.extend(cluster_rows)

    df = pd.DataFrame(rows)
    cluster_status = "CLUSTERFAIL" if df["flag_cluster_fail"].any() else "CLUSTEROK"
    df["cluster_status"] = cluster_status
    Path(output_path).parent.mkdir(exist_ok=True)
    df.to_csv(output_path, index=False)

    if cluster_status == "CLUSTERFAIL":
        _export_validated_params(scan_df, validated_params_path)

    return df


def main() -> None:
    parser = argparse.ArgumentParser(description="Cluster Guard: re-backtest OOS with cluster params")
    parser.add_argument("--scan", required=True, help="Path to multiasset scan CSV")
    parser.add_argument("--cluster-json", required=True, help="Path to cluster analysis JSON")
    parser.add_argument("--output", default="outputs/cluster_paramloss.csv", help="Output CSV path")
    parser.add_argument("--validated-params", default="outputs/validated_params.csv", help="Output validated params CSV path")
    parser.add_argument("--param-source", choices=["median", "centroid", "mean"], default="median")
    parser.add_argument("--loss-threshold", type=float, default=15.0)
    parser.add_argument("--data-dir", default="data")
    args = parser.parse_args()

    run_cluster_guard(
        scan_results_path=args.scan,
        cluster_json_path=args.cluster_json,
        output_path=args.output,
        param_source=args.param_source,
        loss_threshold=args.loss_threshold,
        data_dir=args.data_dir,
        validated_params_path=args.validated_params,
    )


if __name__ == "__main__":
    main()
