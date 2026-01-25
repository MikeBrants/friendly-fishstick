"""
Correlation and concurrent risk analysis for multi-asset portfolio.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent))

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


def _daily_open_series(trades: pd.DataFrame, index: pd.DatetimeIndex) -> pd.Series:
    start = index.min().floor("D")
    end = index.max().floor("D")
    daily_index = pd.date_range(start, end, freq="1D", tz=index.tz)
    open_days = pd.Series(False, index=daily_index)

    if trades is None or trades.empty:
        return open_days

    entries = pd.to_datetime(trades["entry_time"], utc=True)
    exits = pd.to_datetime(trades["exit_time"], utc=True)
    for entry, exit_ in zip(entries, exits):
        entry_day = entry.floor("D")
        exit_day = exit_.floor("D")
        if exit_day < entry_day:
            continue
        open_days.loc[entry_day:exit_day] = True
    return open_days


def _load_params(params_file: str) -> dict[str, dict[str, Any]]:
    df = pd.read_csv(params_file)
    params_map = {}
    for row in df.itertuples(index=False):
        params_map[str(row.asset)] = {
            "sl_mult": float(row.sl_mult),
            "tp1_mult": float(row.tp1_mult),
            "tp2_mult": float(row.tp2_mult),
            "tp3_mult": float(row.tp3_mult),
            "tenkan": int(row.tenkan),
            "kijun": int(row.kijun),
            "tenkan_5": int(row.tenkan_5),
            "kijun_5": int(row.kijun_5),
        }
    return params_map


def run_analysis(
    params_file: str,
    data_dir: str,
    corr_output: str,
    dd_output: str,
) -> None:
    params_map = _load_params(params_file)
    assets = list(params_map.keys())
    if len(assets) < 2:
        raise ValueError("Need at least 2 assets for correlation analysis.")

    warmup = OPTIM_CONFIG["warmup_bars"]
    equity_map = {}
    returns_map = {}
    open_days_map = {}

    for asset in assets:
        data = load_data(asset, data_dir)
        if data.index.tz is None:
            data.index = data.index.tz_localize("UTC")
        else:
            data.index = data.index.tz_convert("UTC")
        data = data.iloc[warmup:]

        params = params_map[asset]
        full_params = build_strategy_params(
            sl_mult=params["sl_mult"],
            tp1_mult=params["tp1_mult"],
            tp2_mult=params["tp2_mult"],
            tp3_mult=params["tp3_mult"],
            tenkan=params["tenkan"],
            kijun=params["kijun"],
            tenkan_5=params["tenkan_5"],
            kijun_5=params["kijun_5"],
        )

        result = _run_backtest(data, full_params)
        equity = result.equity_curve.copy()
        if equity.index.tz is None:
            equity.index = equity.index.tz_localize("UTC")
        else:
            equity.index = equity.index.tz_convert("UTC")
        equity_map[asset] = equity
        returns_map[asset] = _daily_returns(equity)
        open_days_map[asset] = _daily_open_series(result.trades, equity.index)

    rows = []
    corrs = []
    for i, asset_a in enumerate(assets):
        for asset_b in assets[i + 1 :]:
            ret_a, ret_b = returns_map[asset_a].align(returns_map[asset_b], join="inner")
            corr = float(ret_a.corr(ret_b)) if len(ret_a) > 1 else np.nan
            corrs.append(corr)

            open_a = open_days_map[asset_a]
            open_b = open_days_map[asset_b]
            common_days = open_a.index.intersection(open_b.index)
            if len(common_days) == 0:
                overlap_days = 0
                overlap_pct = 0.0
            else:
                overlap_days = int((open_a.loc[common_days] & open_b.loc[common_days]).sum())
                overlap_pct = overlap_days / len(common_days) * 100.0

            rows.append(
                {
                    "asset_a": asset_a,
                    "asset_b": asset_b,
                    "daily_return_corr": corr,
                    "overlap_days": overlap_days,
                    "total_days": int(len(common_days)),
                    "overlap_pct": overlap_pct,
                }
            )

    mean_corr = float(np.nanmean(corrs)) if corrs else np.nan
    warn_corr = bool(mean_corr > 0.7)
    corr_df = pd.DataFrame(rows)
    corr_df["mean_correlation"] = mean_corr
    corr_df["warn_mean_corr"] = warn_corr

    Path(corr_output).parent.mkdir(exist_ok=True)
    corr_df.to_csv(corr_output, index=False)

    # Concurrent drawdown on equal-weight portfolio
    equity_df = pd.concat(
        [
            equity / float(equity.iloc[0])
            for equity in equity_map.values()
        ],
        axis=1,
        keys=list(equity_map.keys()),
    )
    equity_df = equity_df.ffill().dropna()
    portfolio_equity = equity_df.mean(axis=1)
    drawdown = (portfolio_equity / portfolio_equity.cummax() - 1.0) * 100.0
    max_dd = float(drawdown.min()) if not drawdown.empty else 0.0
    max_dd_pct = abs(max_dd)
    max_dd_ts = drawdown.idxmin().isoformat() if not drawdown.empty else ""
    fail_dd = bool(max_dd_pct > 15.0)

    dd_df = pd.DataFrame(
        {
            "timestamp": portfolio_equity.index,
            "portfolio_equity": portfolio_equity.values,
            "drawdown_pct": drawdown.values,
        }
    )
    dd_df["max_drawdown_pct"] = max_dd_pct
    dd_df["max_drawdown_ts"] = max_dd_ts
    dd_df["fail_max_drawdown"] = fail_dd

    dd_df.to_csv(dd_output, index=False)


def main() -> None:
    parser = argparse.ArgumentParser(description="Correlation & concurrent risk analysis.")
    parser.add_argument(
        "--params-file",
        default="outputs/validated_params.csv",
        help="CSV with per-asset validated params",
    )
    parser.add_argument("--data-dir", default="data")
    parser.add_argument(
        "--corr-output",
        default="outputs/portfolio_correlation.csv",
        help="Correlation output CSV",
    )
    parser.add_argument(
        "--dd-output",
        default="outputs/concurrent_dd.csv",
        help="Concurrent drawdown output CSV",
    )
    args = parser.parse_args()

    run_analysis(
        params_file=args.params_file,
        data_dir=args.data_dir,
        corr_output=args.corr_output,
        dd_output=args.dd_output,
    )


if __name__ == "__main__":
    main()
