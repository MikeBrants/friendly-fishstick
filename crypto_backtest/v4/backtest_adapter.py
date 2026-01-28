"""Backtest adapter for v4.2 pipeline."""
from __future__ import annotations

import copy
from typing import Any

import numpy as np
import pandas as pd

from crypto_backtest.analysis.metrics import compute_metrics
from crypto_backtest.engine.backtest import BacktestConfig, VectorizedBacktester
from crypto_backtest.optimization.bayesian import _instantiate_strategy
from crypto_backtest.optimization.parallel_optimizer import load_data
from crypto_backtest.strategies.final_trigger import FinalTriggerStrategy


def _normalize_params(params: dict[str, Any]) -> dict[str, Any]:
    if "ichimoku" in params or "five_in_one" in params:
        return params
    displacement = params.get("displacement", 52)
    return {
        "sl_mult": params.get("sl_mult", 3.0),
        "tp1_mult": params.get("tp1_mult", 2.0),
        "tp2_mult": params.get("tp2_mult", 6.0),
        "tp3_mult": params.get("tp3_mult", 10.0),
        "ichimoku": {
            "tenkan": params.get("tenkan", 9),
            "kijun": params.get("kijun", 26),
            "displacement": displacement,
        },
        "five_in_one": {
            "tenkan_5": params.get("tenkan_5", 9),
            "kijun_5": params.get("kijun_5", 26),
            "displacement_5": params.get("displacement_5", displacement),
        },
    }


def _slice_data(data: pd.DataFrame, start_ts: str | None, end_ts: str | None) -> pd.DataFrame:
    if start_ts:
        data = data.loc[pd.to_datetime(start_ts) :]
    if end_ts:
        data = data.loc[: pd.to_datetime(end_ts)]
    return data


def _bar_returns_from_equity(equity_curve: pd.Series) -> np.ndarray:
    values = equity_curve.to_numpy(dtype=float)
    if len(values) < 2:
        return np.asarray([], dtype=float)
    prev = values[:-1]
    diff = np.diff(values)
    with np.errstate(divide="ignore", invalid="ignore"):
        returns = np.where(prev != 0, diff / prev, 0.0)
    return returns


def _extract_trade_pnls(trades: pd.DataFrame) -> np.ndarray:
    if trades is None or trades.empty:
        return np.asarray([], dtype=float)
    for col in ("pnl", "net_pnl", "gross_pnl"):
        if col in trades.columns:
            return trades[col].astype(float).to_numpy()
    return np.asarray([], dtype=float)


def _top10_concentration(trades: pd.DataFrame) -> float:
    pnls = _extract_trade_pnls(trades)
    if pnls.size == 0:
        return 0.0
    total_pnl = float(pnls.sum())
    if total_pnl <= 0:
        return 0.0
    top10 = float(np.sort(pnls)[-10:].sum()) if pnls.size >= 10 else float(pnls.sum())
    return (top10 / total_pnl) * 100.0


def run_coupled_backtest(
    asset: str,
    recipe_config: dict[str, Any],
    mode: str = "combined",
    start_ts: str | None = None,
    end_ts: str | None = None,
) -> dict[str, Any]:
    enable_long = mode in ("combined", "long_only")
    enable_short = mode in ("combined", "short_only")

    params = recipe_config
    if "long_params" in recipe_config or "short_params" in recipe_config:
        if mode == "short_only":
            params = recipe_config.get("short_params") or recipe_config.get("long_params") or {}
        else:
            params = recipe_config.get("long_params") or recipe_config.get("short_params") or {}

    config = _normalize_params(copy.deepcopy(params))
    config["enable_long"] = enable_long
    config["enable_short"] = enable_short

    data = load_data(asset, data_dir="data")
    data = _slice_data(data, start_ts, end_ts)

    strategy = _instantiate_strategy(FinalTriggerStrategy, config)
    backtester = VectorizedBacktester(BacktestConfig())
    result = backtester.run(data, strategy)
    metrics = compute_metrics(result.equity_curve, result.trades)
    trade_count = int(len(result.trades)) if result.trades is not None else 0
    top10_concentration = _top10_concentration(result.trades)

    return {
        "metrics": metrics,
        "trades": result.trades,
        "trade_count": trade_count,
        "top10_concentration": top10_concentration,
        "equity_curve": result.equity_curve,
        "bar_returns": _bar_returns_from_equity(result.equity_curve),
    }


def run_two_pass_backtest(
    asset: str,
    recipe_config: dict[str, Any],
    start_ts: str | None = None,
    end_ts: str | None = None,
) -> dict[str, Any]:
    long_result = run_coupled_backtest(
        asset=asset,
        recipe_config=recipe_config,
        mode="long_only",
        start_ts=start_ts,
        end_ts=end_ts,
    )
    short_result = run_coupled_backtest(
        asset=asset,
        recipe_config=recipe_config,
        mode="short_only",
        start_ts=start_ts,
        end_ts=end_ts,
    )
    return {"long": long_result, "short": short_result}
