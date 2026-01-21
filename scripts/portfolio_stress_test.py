"""
Portfolio stress testing for a weighted asset set.
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
from crypto_backtest.strategies.final_trigger import FinalTriggerStrategy
from scripts.run_guards_multiasset import _find_break_even_fees


def _run_backtest(data: pd.DataFrame, params: dict[str, Any], fees_bps: float, slippage_bps: float) -> Any:
    config = BacktestConfig(
        initial_capital=10000.0,
        fees_bps=fees_bps,
        slippage_bps=slippage_bps,
        sizing_mode="fixed",
        intrabar_order="stop_first",
    )
    strategy = _instantiate_strategy(FinalTriggerStrategy, params)
    backtester = VectorizedBacktester(config)
    return backtester.run(data, strategy)


def _daily_returns(equity_curve: pd.Series) -> pd.Series:
    daily_equity = equity_curve.resample("1D").last().ffill()
    return daily_equity.pct_change().dropna()


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


def main() -> None:
    parser = argparse.ArgumentParser(description="Portfolio stress tests.")
    parser.add_argument("--portfolio", required=True, help="CSV with optimized weights")
    parser.add_argument("--params-file", default="outputs/all_validated_assets.csv")
    parser.add_argument("--fees-bps", required=True, help="Comma-separated fees bps list")
    parser.add_argument("--slip-bps", required=True, help="Comma-separated slippage bps list")
    args = parser.parse_args()

    weights_df = pd.read_csv(args.portfolio)
    params_df = pd.read_csv(args.params_file)

    weights = dict(zip(weights_df["asset"], weights_df["weight"]))
    params_map = {row.asset: row for row in params_df.itertuples(index=False)}

    fees_list = [float(x) for x in args.fees_bps.split(",") if x.strip()]
    slip_list = [float(x) for x in args.slip_bps.split(",") if x.strip()]
    if len(fees_list) != len(slip_list):
        raise ValueError("fees-bps and slip-bps must have the same length")

    warmup = OPTIM_CONFIG["warmup_bars"]
    data_cache = {}
    params_cache = {}
    break_even_map = {}

    for asset, weight in weights.items():
        row = params_map.get(asset)
        if row is None:
            raise ValueError(f"Missing params for asset: {asset}")
        data = load_data(asset, "data")
        if data.index.tz is None:
            data.index = data.index.tz_localize("UTC")
        else:
            data.index = data.index.tz_convert("UTC")
        data = data.iloc[warmup:]
        params = _build_params(pd.Series(row._asdict()))
        data_cache[asset] = data
        params_cache[asset] = params
        break_even_map[asset] = _find_break_even_fees(data, params)

    rows = []
    for idx, (fees, slip) in enumerate(zip(fees_list, slip_list), start=1):
        scenario = "Base" if idx == 1 else f"Stress{idx-1}"
        returns_map = {}
        for asset, weight in weights.items():
            result = _run_backtest(data_cache[asset], params_cache[asset], fees, slip)
            equity = result.equity_curve.copy()
            if equity.index.tz is None:
                equity.index = equity.index.tz_localize("UTC")
            returns_map[asset] = _daily_returns(equity)

        returns_df = pd.DataFrame(returns_map).dropna(how="any")
        weights_vec = np.array([weights[a] for a in returns_df.columns])
        portfolio_returns = returns_df.values.dot(weights_vec)
        equity = (1.0 + portfolio_returns).cumprod() * 10000.0
        metrics = compute_metrics(pd.Series(equity, index=returns_df.index), pd.DataFrame())

        weighted_break_even = float(
            sum(break_even_map[a] * weights[a] for a in returns_df.columns)
        )
        edge_bps = weighted_break_even - fees

        rows.append(
            {
                "scenario": scenario,
                "fees_bps": fees,
                "slippage_bps": slip,
                "sharpe": float(metrics.get("sharpe_ratio", 0.0) or 0.0),
                "sortino": float(metrics.get("sortino_ratio", 0.0) or 0.0),
                "max_dd_pct": float(metrics.get("max_drawdown", 0.0) or 0.0) * 100.0,
                "total_return_pct": float(metrics.get("total_return", 0.0) or 0.0) * 100.0,
                "edge_bps": edge_bps,
            }
        )

    out_path = Path("outputs") / f"portfolio_stress_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    pd.DataFrame(rows).to_csv(out_path, index=False)
    print(f"Exported: {out_path}")


if __name__ == "__main__":
    main()
