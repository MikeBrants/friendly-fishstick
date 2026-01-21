"""
Portfolio construction from validated asset parameters.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from scipy.optimize import minimize

sys.path.insert(0, str(Path(__file__).parent.parent))

from crypto_backtest.analysis.metrics import compute_metrics
from crypto_backtest.config.scan_assets import OPTIM_CONFIG
from crypto_backtest.engine.backtest import BacktestConfig, VectorizedBacktester
from crypto_backtest.optimization.bayesian import _instantiate_strategy
from crypto_backtest.optimization.parallel_optimizer import build_strategy_params, load_data
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


def _optimize_weights(returns_df: pd.DataFrame, min_w: float, max_w: float) -> np.ndarray:
    n = returns_df.shape[1]
    if n == 0:
        return np.array([])
    bounds = [(min_w, max_w)] * n

    def neg_sharpe(weights: np.ndarray) -> float:
        portfolio_returns = returns_df.values.dot(weights)
        if portfolio_returns.std() == 0:
            return 0.0
        sharpe = portfolio_returns.mean() / portfolio_returns.std()
        return -sharpe

    constraints = [{"type": "eq", "fun": lambda w: np.sum(w) - 1.0}]
    x0 = np.array([1.0 / n] * n)
    result = minimize(neg_sharpe, x0, bounds=bounds, constraints=constraints)
    if not result.success:
        return x0
    return result.x


def main() -> None:
    parser = argparse.ArgumentParser(description="Portfolio construction.")
    parser.add_argument("--input-validated", required=True, help="CSV with validated asset params")
    parser.add_argument("--correlation-method", default="pearson")
    parser.add_argument("--min-weight", type=float, default=0.03)
    parser.add_argument("--max-weight", type=float, default=0.15)
    parser.add_argument("--target-sharpe", type=float, default=2.5)
    parser.add_argument("--max-correlation", type=float, default=0.75)
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
    corr_matrix = returns_df.corr(method=args.correlation_method)
    corr_path = Path("outputs/portfolio_correlation_matrix.csv")
    corr_matrix.to_csv(corr_path)

    high_pairs = []
    for i, a in enumerate(returns_df.columns):
        for b in returns_df.columns[i + 1 :]:
            corr = float(corr_matrix.loc[a, b])
            if corr > args.max_correlation:
                high_pairs.append({"asset_a": a, "asset_b": b, "corr": corr})
    if high_pairs:
        pd.DataFrame(high_pairs).to_csv("outputs/portfolio_high_correlation.csv", index=False)

    equal_weights = np.array([1.0 / len(returns_df.columns)] * len(returns_df.columns))
    eq_returns = returns_df.values.dot(equal_weights)
    eq_metrics = _portfolio_metrics(pd.Series(eq_returns, index=returns_df.index))

    opt_weights = _optimize_weights(returns_df, args.min_weight, args.max_weight)
    opt_returns = returns_df.values.dot(opt_weights)
    opt_metrics = _portfolio_metrics(pd.Series(opt_returns, index=returns_df.index))

    vols = returns_df.std(ddof=0)
    eq_vol = eq_returns.std(ddof=0)
    opt_vol = opt_returns.std(ddof=0)
    div_ratio_eq = float((vols.values * equal_weights).sum() / eq_vol) if eq_vol > 0 else 0.0
    div_ratio_opt = float((vols.values * opt_weights).sum() / opt_vol) if opt_vol > 0 else 0.0

    max_pair_corr = float(corr_matrix.where(~np.eye(len(corr_matrix), dtype=bool)).max().max())

    weights_equal_df = pd.DataFrame({"asset": returns_df.columns, "weight": equal_weights})
    weights_equal_df.to_csv("outputs/portfolio_weights_equalweight.csv", index=False)

    weights_opt_df = pd.DataFrame({"asset": returns_df.columns, "weight": opt_weights})
    weights_opt_df.to_csv("outputs/portfolio_weights_optimized.csv", index=False)

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
                "profile": "optimized",
                "sharpe": opt_metrics["sharpe"],
                "sortino": opt_metrics["sortino"],
                "max_dd_pct": opt_metrics["max_dd_pct"],
                "total_return_pct": opt_metrics["total_return_pct"],
                "assets": len(returns_df.columns),
                "diversification_ratio": div_ratio_opt,
                "max_pair_corr": max_pair_corr,
            },
        ]
    )
    metrics_df.to_csv("outputs/portfolio_metrics.csv", index=False)

    print(f"Exported: {corr_path}")
    print("Exported: outputs/portfolio_weights_equalweight.csv")
    print("Exported: outputs/portfolio_weights_optimized.csv")
    print("Exported: outputs/portfolio_metrics.csv")


if __name__ == "__main__":
    main()
