"""
Portfolio construction from validated asset parameters.
"""
from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent))

from crypto_backtest.analysis.metrics import compute_metrics
from crypto_backtest.config.scan_assets import OPTIM_CONFIG
from crypto_backtest.engine.backtest import BacktestConfig, VectorizedBacktester
from crypto_backtest.optimization.bayesian import _instantiate_strategy
from crypto_backtest.optimization.parallel_optimizer import build_strategy_params, load_data
from crypto_backtest.portfolio.weights import (
    compute_equal_weights,
    optimize_max_sharpe,
    optimize_risk_parity,
    optimize_min_cvar,
)
from crypto_backtest.strategies.final_trigger import FinalTriggerStrategy


BASE_CONFIG = BacktestConfig(
    initial_capital=10000.0,
    fees_bps=5.0,
    slippage_bps=2.0,
    sizing_mode="fixed",
    intrabar_order="stop_first",
)


def _run_backtest(data: pd.DataFrame, params: dict[str, Any]) -> Any:
    strategy = _instantiate_strategy(FinalTriggerStrategy, params)
    backtester = VectorizedBacktester(BASE_CONFIG)
    return backtester.run(data, strategy)


def _daily_returns(equity_curve: pd.Series) -> pd.Series:
    daily_equity = equity_curve.resample("1D").last().ffill()
    return daily_equity.pct_change().dropna()


def _load_params(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    return df


def _build_params(row: pd.Series) -> dict[str, Any]:
    params = build_strategy_params(
        sl_mult=float(row.sl_mult),
        tp1_mult=float(row.tp1_mult),
        tp2_mult=float(row.tp2_mult),
        tp3_mult=float(row.tp3_mult),
        tenkan=int(row.tenkan),
        kijun=int(row.kijun),
        tenkan_5=int(row.tenkan_5),
        kijun_5=int(row.kijun_5),
    )
    if "displacement" in row and pd.notna(row.displacement):
        disp = int(row.displacement)
        params["ichimoku"]["displacement"] = disp
        params["five_in_one"]["displacement_5"] = disp
    return params


def _portfolio_metrics(returns: pd.Series) -> dict[str, float]:
    equity = (1.0 + returns).cumprod()
    equity = equity * 10000.0
    metrics = compute_metrics(equity, pd.DataFrame())
    return {
        "sharpe": float(metrics.get("sharpe_ratio", 0.0) or 0.0),
        "sortino": float(metrics.get("sortino_ratio", 0.0) or 0.0),
        "max_dd_pct": float(metrics.get("max_drawdown", 0.0) or 0.0) * 100.0,
        "total_return_pct": float(metrics.get("total_return", 0.0) or 0.0) * 100.0,
    }


def _compute_weights(method: str, returns_df: pd.DataFrame, min_w: float, max_w: float) -> np.ndarray:
    method = method.lower()
    if method == "equal":
        return compute_equal_weights(len(returns_df.columns), min_w=min_w, max_w=max_w)
    if method == "max_sharpe":
        return optimize_max_sharpe(returns_df, min_w=min_w, max_w=max_w)
    if method == "risk_parity":
        return optimize_risk_parity(returns_df, min_w=min_w, max_w=max_w)
    if method == "min_cvar":
        return optimize_min_cvar(returns_df, alpha=0.05, min_w=min_w, max_w=max_w)
    raise ValueError(f"Unknown method: {method}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Portfolio construction.")
    parser.add_argument("--input-validated", required=True, help="CSV with validated asset params")
    parser.add_argument(
        "--method",
        choices=["equal", "max_sharpe", "risk_parity", "min_cvar"],
        default="max_sharpe",
        help="Weighting method to export (default: max_sharpe)",
    )
    parser.add_argument("--correlation-method", default="pearson")
    parser.add_argument("--min-weight", type=float, default=0.03)
    parser.add_argument("--max-weight", type=float, default=0.15)
    parser.add_argument("--max-correlation", type=float, default=0.75)
    parser.add_argument("--output-prefix", default="portfolio")
    args = parser.parse_args()

    params_df = _load_params(args.input_validated)
    assets = params_df["asset"].tolist()
    if len(assets) < 2:
        raise ValueError("Need at least 2 assets for portfolio construction.")

    warmup = OPTIM_CONFIG["warmup_bars"]
    returns_map = {}
    equity_map = {}

    for row in params_df.itertuples(index=False):
        asset = str(row.asset)
        data = load_data(asset, "data")
        if data.index.tz is None:
            data.index = data.index.tz_localize("UTC")
        else:
            data.index = data.index.tz_convert("UTC")
        data = data.iloc[warmup:]
        params = _build_params(pd.Series(row._asdict()))
        result = _run_backtest(data, params)
        equity = result.equity_curve.copy()
        if equity.index.tz is None:
            equity.index = equity.index.tz_localize("UTC")
        returns_map[asset] = _daily_returns(equity)
        equity_map[asset] = equity

    returns_df = pd.DataFrame(returns_map).dropna(how="any")
    if returns_df.shape[1] < 2:
        raise ValueError("Need at least 2 assets with aligned returns.")

    corr_matrix = returns_df.corr(method=args.correlation_method)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    outputs_dir = Path("outputs")
    outputs_dir.mkdir(exist_ok=True)
    corr_path = outputs_dir / f"{args.output_prefix}_correlation_matrix_{timestamp}.csv"
    corr_matrix.to_csv(corr_path)

    high_pairs = []
    for i, a in enumerate(returns_df.columns):
        for b in returns_df.columns[i + 1 :]:
            corr = float(corr_matrix.loc[a, b])
            if corr > args.max_correlation:
                high_pairs.append({"asset_a": a, "asset_b": b, "corr": corr})
    if high_pairs:
        pd.DataFrame(high_pairs).to_csv(
            outputs_dir / f"{args.output_prefix}_high_correlation_{timestamp}.csv", index=False
        )

    equal_weights = compute_equal_weights(
        len(returns_df.columns), min_w=args.min_weight, max_w=args.max_weight
    )
    eq_returns = returns_df.values.dot(equal_weights)
    eq_metrics = _portfolio_metrics(pd.Series(eq_returns, index=returns_df.index))

    selected_weights = _compute_weights(args.method, returns_df, args.min_weight, args.max_weight)
    sel_returns = returns_df.values.dot(selected_weights)
    sel_metrics = _portfolio_metrics(pd.Series(sel_returns, index=returns_df.index))

    vols = returns_df.std(ddof=0)
    eq_vol = eq_returns.std(ddof=0)
    div_ratio_eq = float((vols.values * equal_weights).sum() / eq_vol) if eq_vol > 0 else 0.0
    sel_vol = sel_returns.std(ddof=0)
    div_ratio_sel = float((vols.values * selected_weights).sum() / sel_vol) if sel_vol > 0 else 0.0

    max_pair_corr = float(corr_matrix.where(~np.eye(len(corr_matrix), dtype=bool)).max().max())

    weights_equal_df = pd.DataFrame({"asset": returns_df.columns, "weight": equal_weights})
    weights_equal_path = outputs_dir / f"{args.output_prefix}_weights_equal_{timestamp}.csv"
    weights_equal_df.to_csv(weights_equal_path, index=False)

    weights_sel_df = pd.DataFrame({"asset": returns_df.columns, "weight": selected_weights})
    weights_sel_path = outputs_dir / f"{args.output_prefix}_weights_{args.method}_{timestamp}.csv"
    weights_sel_df.to_csv(weights_sel_path, index=False)

    metrics_df = pd.DataFrame(
        [
            {
                "profile": "equal_weight",
                "sharpe": eq_metrics["sharpe"],
                "sortino": eq_metrics["sortino"],
                "max_dd_pct": eq_metrics["max_dd_pct"],
                "total_return_pct": eq_metrics["total_return_pct"],
                "assets": len(returns_df.columns),
                "diversification_ratio": div_ratio_eq,
                "max_pair_corr": max_pair_corr,
            },
            {
                "profile": args.method,
                "sharpe": sel_metrics["sharpe"],
                "sortino": sel_metrics["sortino"],
                "max_dd_pct": sel_metrics["max_dd_pct"],
                "total_return_pct": sel_metrics["total_return_pct"],
                "assets": len(returns_df.columns),
                "diversification_ratio": div_ratio_sel,
                "max_pair_corr": max_pair_corr,
            },
        ]
    )
    metrics_path = outputs_dir / f"{args.output_prefix}_metrics_{timestamp}.csv"
    metrics_df.to_csv(metrics_path, index=False)

    print(f"Exported: {corr_path}")
    print(f"Exported: {weights_equal_path}")
    print(f"Exported: {weights_sel_path}")
    print(f"Exported: {metrics_path}")


if __name__ == "__main__":
    main()
