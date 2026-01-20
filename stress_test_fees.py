"""Stress test execution costs across fee/slippage scenarios."""

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


def _pnl_series(trades: pd.DataFrame) -> pd.Series:
    if trades is None or trades.empty:
        return pd.Series(dtype=float)
    for col in ("pnl", "net_pnl", "gross_pnl"):
        if col in trades.columns:
            return trades[col].astype(float)
    return pd.Series(dtype=float)


def run_scenario(
    data: pd.DataFrame,
    params: FinalTriggerParams,
    fees_bps: float,
    slippage_bps: float,
) -> dict:
    config = BacktestConfig(
        initial_capital=10000.0,
        fees_bps=fees_bps,
        slippage_bps=slippage_bps,
        sizing_mode="fixed",
        intrabar_order="stop_first",
    )
    backtester = VectorizedBacktester(config)
    result = backtester.run(data, FinalTriggerStrategy(params))

    final_equity = float(result.equity_curve.iloc[-1]) if len(result.equity_curve) else config.initial_capital
    total_return = (final_equity / config.initial_capital - 1) * 100 if config.initial_capital else 0.0

    metrics = compute_metrics(result.equity_curve, result.trades)
    pnl = _pnl_series(result.trades)
    winners = pnl[pnl > 0]
    losers = pnl[pnl < 0]

    sharpe = float(metrics.get("sharpe_ratio", 0.0))
    return {
        "fees_bps": fees_bps,
        "slippage_bps": slippage_bps,
        "total_return_pct": total_return,
        "sharpe": sharpe,
        "sortino": float(metrics.get("sortino_ratio", 0.0)),
        "max_drawdown_pct": float(metrics.get("max_drawdown", 0.0)) * 100,
        "profit_factor": float(metrics.get("profit_factor", 0.0)),
        "trades": int(len(result.trades)),
        "avg_win": float(winners.mean()) if len(winners) else 0.0,
        "avg_loss": float(losers.mean()) if len(losers) else 0.0,
        "expectancy": float(pnl.mean()) if len(pnl) else 0.0,
        "break_even": bool(total_return > 0 and sharpe > 0),
    }


def find_break_even_fees(data: pd.DataFrame, params: FinalTriggerParams) -> float:
    """Find max fees_bps with slippage=fees*0.4 where return>0 and sharpe>0."""
    break_even = 0.0
    for fees in range(0, 51):
        slippage = fees * 0.4
        result = run_scenario(data, params, fees_bps=fees, slippage_bps=slippage)
        if result["total_return_pct"] > 0 and result["sharpe"] > 0:
            break_even = fees
    return float(break_even)


def main() -> None:
    print("Loading data...")
    data = load_binance_data(warmup=200)
    params = build_optimized_params()

    scenarios = [
        ("Base", 5, 2),
        ("Stress 1", 10, 5),
        ("Stress 2", 15, 10),
        ("Stress 3", 20, 15),
        ("Stress 4", 25, 20),
    ]

    rows = []
    for label, fees, slippage in scenarios:
        metrics = run_scenario(data, params, fees_bps=fees, slippage_bps=slippage)
        metrics["scenario"] = label
        rows.append(metrics)

    break_even_fees = find_break_even_fees(data, params)
    edge_buffer_bps = break_even_fees - 5

    for row in rows:
        row["edge_buffer_bps"] = edge_buffer_bps

    df = pd.DataFrame(rows)
    output_csv = "outputs/stress_test_fees.csv"
    Path("outputs").mkdir(exist_ok=True)
    df.to_csv(output_csv, index=False)

    stress1 = df[df["scenario"] == "Stress 1"].iloc[0]
    stress2 = df[df["scenario"] == "Stress 2"].iloc[0]

    fragile = stress1["sharpe"] < 1.0
    weak_edge = stress1["sharpe"] < 1.5 or break_even_fees < 15
    robust = stress2["sharpe"] > 1.5

    report_path = "outputs/stress_test_fees_report.txt"
    with open(report_path, "w") as f:
        f.write("STRESS TEST FEES REPORT\n")
        f.write("=" * 70 + "\n")
        f.write(f"edge_buffer_bps: {edge_buffer_bps:.1f}\n")
        f.write(f"FRAGILE (Sharpe < 1.0 at Stress 1): {'YES' if fragile else 'NO'}\n")
        f.write(f"WEAK_EDGE (Sharpe < 1.5 at Stress 1 OR break_even < 15): {'YES' if weak_edge else 'NO'}\n")
        f.write(f"ROBUST (Sharpe > 1.5 at Stress 2): {'YES' if robust else 'NO'}\n")

    print("\nStress test summary:")
    print(f"  edge_buffer_bps: {edge_buffer_bps:.1f}")
    print(f"  FRAGILE: {'YES' if fragile else 'NO'}")
    print(f"  WEAK_EDGE: {'YES' if weak_edge else 'NO'}")
    print(f"  ROBUST: {'YES' if robust else 'NO'}")
    print(f"\nSaved CSV: {output_csv}")
    print(f"Saved report: {report_path}")


if __name__ == "__main__":
    main()
