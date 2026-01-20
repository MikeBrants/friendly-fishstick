"""Resolve SIDEWAYS paradox with trade-level attribution and PnL reconciliation."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from crypto_backtest.analysis.regime import REGIMES_V2, classify_regimes_v2
from crypto_backtest.engine.backtest import BacktestConfig, VectorizedBacktester
from crypto_backtest.indicators.five_in_one import FiveInOneConfig
from crypto_backtest.indicators.ichimoku import IchimokuConfig
from crypto_backtest.strategies.final_trigger import FinalTriggerParams, FinalTriggerStrategy


REGIMES = REGIMES_V2


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
    for col in ("net_pnl", "pnl", "gross_pnl"):
        if col in trades.columns:
            return trades[col].astype(float)
    return pd.Series(dtype=float)


def main() -> None:
    print("Loading data...")
    data = load_binance_data(warmup=200)
    regimes = classify_regimes_v2(data)

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
    result = backtester.run(data, FinalTriggerStrategy(params))
    trades = result.trades.copy()

    if trades.empty:
        raise RuntimeError("No trades found for baseline backtest.")

    trades["trade_id"] = np.arange(1, len(trades) + 1)
    trades["entry_time"] = pd.to_datetime(trades["entry_time"], utc=True)
    trades["exit_time"] = pd.to_datetime(trades["exit_time"], utc=True)
    trades["net_pnl"] = _pnl_series(trades)

    entry_idx = data.index.get_indexer(trades["entry_time"], method="nearest")
    if (entry_idx < 0).any():
        trades = trades.loc[entry_idx >= 0].copy()
        entry_idx = entry_idx[entry_idx >= 0]
    trades["regime"] = regimes.iloc[entry_idx].values

    total_pnl_from_trades = float(trades["net_pnl"].sum())
    regime_pnl = trades.groupby("regime")["net_pnl"].sum()
    regime_count = trades.groupby("regime").size()
    total_pnl_from_regimes = float(regime_pnl.sum())

    baseline_return = total_pnl_from_trades / config.initial_capital * 100

    assert abs(total_pnl_from_trades - total_pnl_from_regimes) < 0.01, "PnL mismatch!"
    assert abs(15.69 - baseline_return) < 0.1, "Baseline mismatch!"

    reconciliation = []
    for regime in REGIMES:
        pnl = float(regime_pnl.get(regime, 0.0))
        trades_count = int(regime_count.get(regime, 0))
        return_pct = pnl / config.initial_capital * 100
        pct_total = (pnl / total_pnl_from_trades * 100) if total_pnl_from_trades else 0.0
        avg_pnl = pnl / trades_count if trades_count else 0.0
        reconciliation.append(
            {
                "regime": regime,
                "trades": trades_count,
                "net_pnl": pnl,
                "return_pct": return_pct,
                "pct_of_total_pnl": pct_total,
                "avg_pnl_per_trade": avg_pnl,
            }
        )

    recon_df = pd.DataFrame(reconciliation)
    Path("outputs").mkdir(exist_ok=True)
    recon_df.to_csv("outputs/regime_reconciliation.csv", index=False)
    trades.to_csv("outputs/trades_with_regime.csv", index=False)

    sideways_row = recon_df[recon_df["regime"] == "SIDEWAYS"].iloc[0]
    sideways_return = float(sideways_row["return_pct"])
    verdict = "NEUTRAL"
    if sideways_return > 0.5:
        verdict = "PROFITABLE"
    elif sideways_return < -0.5:
        verdict = "UNPROFITABLE"

    v2_sideways_return = -7.71
    lookahead_bug = sideways_return > 0 and v2_sideways_return < 0

    report_path = "outputs/regime_reconciliation_report.txt"
    with open(report_path, "w") as f:
        f.write("REGIME RECONCILIATION REPORT\n")
        f.write("=" * 70 + "\n")
        f.write(f"Total trades: {len(trades)}\n")
        f.write(f"Total PnL: ${total_pnl_from_trades:.2f}\n")
        f.write(f"Sum of regime PnL: ${total_pnl_from_regimes:.2f}\n")
        f.write(f"Baseline return: {baseline_return:.2f}%\n")
        f.write(f"SIDEWAYS contribution: {sideways_row['pct_of_total_pnl']:.2f}%\n")
        f.write(f"Verdict: SIDEWAYS is {verdict}\n")
        if lookahead_bug:
            f.write("Flag: REGIME_V2_HAD_LOOKAHEAD_BUG\n")

    print("\nReconciliation summary:")
    print(f"  Total trades: {len(trades)}")
    print(f"  Total PnL: ${total_pnl_from_trades:.2f}")
    print(f"  SIDEWAYS contribution: {sideways_row['pct_of_total_pnl']:.2f}%")
    print(f"  Verdict: SIDEWAYS is {verdict}")
    if lookahead_bug:
        print("  Flag: REGIME_V2_HAD_LOOKAHEAD_BUG")
    print("Saved outputs:")
    print("  outputs/regime_reconciliation.csv")
    print("  outputs/regime_reconciliation_report.txt")
    print("  outputs/trades_with_regime.csv")


if __name__ == "__main__":
    main()
