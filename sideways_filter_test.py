"""Test SIDEWAYS regime with partial (50%) and full (0%) sizing filters."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from crypto_backtest.analysis.metrics import compute_metrics
from crypto_backtest.engine.backtest import BacktestConfig, VectorizedBacktester
from crypto_backtest.indicators.five_in_one import FiveInOneConfig
from crypto_backtest.indicators.ichimoku import IchimokuConfig
from crypto_backtest.strategies.final_trigger import FinalTriggerParams, FinalTriggerStrategy


def load_binance_data(warmup: int = 200) -> pd.DataFrame:
    """Load Binance data with warmup."""
    df = pd.read_csv("data/Binance_BTCUSDT_1h.csv")
    df.columns = [col.strip() for col in df.columns]
    data = df[["open", "high", "low", "close"]].copy()

    if "volume" in df.columns:
        data["volume"] = df["volume"].fillna(0.0)
    else:
        data["volume"] = 0.0

    if "timestamp" in df.columns:
        data.index = pd.to_datetime(df["timestamp"], utc=True)

    return data.iloc[warmup:]


def build_optimized_params() -> FinalTriggerParams:
    """Return optimized Ichimoku + SL/TP parameters."""
    five_in_one = FiveInOneConfig(
        fast_period=7,
        slow_period=19,
        er_period=8,
        norm_period=50,
        use_norm=True,
        ad_norm_period=50,
        use_ad_line=True,
        ichi5in1_strict=False,
        use_transition_mode=False,
        use_distance_filter=False,
        use_volume_filter=False,
        use_regression_cloud=False,
        use_kama_oscillator=False,
        use_ichimoku_filter=True,
        tenkan_5=12,
        kijun_5=21,
        displacement_5=52,
    )

    ichimoku = IchimokuConfig(
        tenkan=13,
        kijun=34,
        displacement=52,
    )

    return FinalTriggerParams(
        grace_bars=1,
        use_mama_kama_filter=False,
        require_fama_between=False,
        strict_lock_5in1_last=False,
        mama_fast_limit=0.5,
        mama_slow_limit=0.05,
        kama_length=20,
        atr_length=14,
        sl_mult=3.75,
        tp1_mult=3.75,
        tp2_mult=9.0,
        tp3_mult=7.0,
        ichimoku=ichimoku,
        five_in_one=five_in_one,
    )


def classify_sideways(data: pd.DataFrame) -> pd.Series:
    """Return boolean series for SIDEWAYS regime."""
    close = data["close"]
    from_high_50 = (close / close.rolling(50).max()) - 1
    from_low_50 = (close / close.rolling(50).min()) - 1
    is_sideways = (from_high_50.abs() < 0.05) & (from_low_50.abs() < 0.05)
    return is_sideways.fillna(False)


def compute_metrics_from_trades(
    trades: pd.DataFrame,
    pnl_col: str,
    data_index: pd.Index,
    initial_capital: float,
) -> dict:
    """Compute metrics and equity curve from scaled trades."""
    if trades.empty:
        equity = pd.Series(initial_capital, index=data_index)
        metrics = compute_metrics(equity, trades)
        return {"equity": equity, "metrics": metrics}

    pnl_by_time = trades.groupby("exit_time")[pnl_col].sum()
    pnl_series = pnl_by_time.reindex(data_index, fill_value=0.0)
    equity = initial_capital + pnl_series.cumsum()

    trades_for_metrics = trades.copy()
    trades_for_metrics["pnl"] = trades_for_metrics[pnl_col]
    metrics = compute_metrics(equity, trades_for_metrics)
    return {"equity": equity, "metrics": metrics}


def main() -> None:
    print("Loading data...")
    data = load_binance_data(warmup=200)
    is_sideways = classify_sideways(data)

    config = BacktestConfig(
        initial_capital=10000.0,
        fees_bps=5.0,
        slippage_bps=2.0,
        sizing_mode="fixed",
        intrabar_order="stop_first",
    )
    backtester = VectorizedBacktester(config)
    params = build_optimized_params()

    print("Running baseline backtest...")
    baseline_result = backtester.run(data, FinalTriggerStrategy(params))
    trades = baseline_result.trades.copy()
    trades["entry_time"] = pd.to_datetime(trades["entry_time"], utc=True)
    entry_idx = data.index.get_indexer(trades["entry_time"], method="nearest")
    trades["is_sideways"] = is_sideways.iloc[entry_idx].values

    pnl_col = "pnl" if "pnl" in trades.columns else "net_pnl"
    trades["pnl"] = trades[pnl_col]

    # Baseline metrics
    baseline_metrics = compute_metrics(baseline_result.equity_curve, trades)
    baseline_return = (
        baseline_result.equity_curve.iloc[-1] / config.initial_capital - 1
    ) * 100 if len(baseline_result.equity_curve) else 0.0

    def _summary(metrics: dict, total_return: float, trades_count: int) -> dict:
        return {
            "trades": trades_count,
            "return_pct": total_return,
            "sharpe": metrics.get("sharpe_ratio", 0.0),
            "max_dd": metrics.get("max_drawdown", 0.0),
        }

    # 50% sizing in SIDEWAYS
    trades_50 = trades.copy()
    trades_50["pnl_scaled"] = trades_50["pnl"] * np.where(trades_50["is_sideways"], 0.5, 1.0)
    metrics_50 = compute_metrics_from_trades(
        trades_50,
        "pnl_scaled",
        data.index,
        config.initial_capital,
    )
    return_50 = (
        metrics_50["equity"].iloc[-1] / config.initial_capital - 1
    ) * 100 if len(metrics_50["equity"]) else 0.0

    # 100% filter (drop SIDEWAYS trades)
    trades_100 = trades[~trades["is_sideways"]].copy()
    trades_100["pnl_scaled"] = trades_100["pnl"]
    metrics_100 = compute_metrics_from_trades(
        trades_100,
        "pnl_scaled",
        data.index,
        config.initial_capital,
    )
    return_100 = (
        metrics_100["equity"].iloc[-1] / config.initial_capital - 1
    ) * 100 if len(metrics_100["equity"]) else 0.0

    # Output files
    Path("outputs").mkdir(exist_ok=True)
    pd.DataFrame(
        [
            _summary(metrics_50["metrics"], return_50, len(trades_50)),
        ]
    ).to_csv("outputs/backtest_sideways_filter_50pct.csv", index=False)
    pd.DataFrame(
        [
            _summary(metrics_100["metrics"], return_100, len(trades_100)),
        ]
    ).to_csv("outputs/backtest_sideways_filter_100pct.csv", index=False)

    print("\nBaseline:")
    print(_summary(baseline_metrics, baseline_return, len(trades)))
    print("\nSIDEWAYS 50% sizing:")
    print(_summary(metrics_50["metrics"], return_50, len(trades_50)))
    print("\nSIDEWAYS 100% filter:")
    print(_summary(metrics_100["metrics"], return_100, len(trades_100)))


if __name__ == "__main__":
    main()
