"""Market regime analysis (v2) with multi-factor classification."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
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
    for col in ("pnl", "net_pnl", "gross_pnl"):
        if col in trades.columns:
            return trades[col].astype(float)
    return pd.Series(dtype=float)


def _profit_factor(pnl: pd.Series) -> float:
    if pnl.empty:
        return 0.0
    gains = pnl[pnl > 0].sum()
    losses = pnl[pnl < 0].sum()
    if losses == 0:
        return float("inf") if gains > 0 else 0.0
    return float(gains / abs(losses))


def _win_rate(pnl: pd.Series) -> float:
    if pnl.empty:
        return 0.0
    return float((pnl > 0).mean())


def _annualization_factor() -> float:
    return (365.25 * 24) ** 0.5


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

    print("Running backtest with optimized params...")
    result = backtester.run(data, FinalTriggerStrategy(params))
    equity = result.equity_curve
    equity_returns = equity.pct_change()

    trades = result.trades.copy()
    trades["entry_time"] = pd.to_datetime(trades["entry_time"], utc=True)
    entry_idx = data.index.get_indexer(trades["entry_time"], method="nearest")
    trades["regime"] = regimes.iloc[entry_idx].values

    rows = []
    for regime in REGIMES:
        mask = regimes == regime
        regime_returns = equity_returns.loc[mask].dropna()

        if regime_returns.empty:
            sharpe = 0.0
            total_return = 0.0
        else:
            mean = regime_returns.mean()
            std = regime_returns.std(ddof=0)
            sharpe = float(mean / std) * _annualization_factor() if std != 0 else 0.0
            total_return = float((1 + regime_returns).prod() - 1) * 100

        regime_trades = trades[trades["regime"] == regime]
        pnl = _pnl_series(regime_trades)

        winners = pnl[pnl > 0]
        losers = pnl[pnl < 0]

        rows.append(
            {
                "regime": regime,
                "sharpe": sharpe,
                "return_pct": total_return,
                "win_rate": _win_rate(pnl),
                "profit_factor": _profit_factor(pnl),
                "trade_count": int(len(regime_trades)),
                "bar_count": int(mask.sum()),
                "avg_win": float(winners.mean()) if len(winners) else 0.0,
                "avg_loss": float(losers.mean()) if len(losers) else 0.0,
                "max_win": float(winners.max()) if len(winners) else 0.0,
                "max_loss": float(losers.min()) if len(losers) else 0.0,
            }
        )

    df = pd.DataFrame(rows)
    output_csv = "outputs/regime_analysis_v2.csv"
    Path("outputs").mkdir(exist_ok=True)
    df.to_csv(output_csv, index=False)

    # Distribution pie chart by bar count
    dist = df[df["bar_count"] > 0].set_index("regime")["bar_count"]
    plt.figure(figsize=(6, 4))
    plt.pie(dist, labels=dist.index, autopct="%1.1f%%", startangle=90)
    plt.title("Regime Distribution (bar count)")
    plt.tight_layout()
    plt.savefig("outputs/regime_distribution.png", dpi=150)
    plt.close()

    # Flags and targets
    trade_threshold = 20
    target_sharpe = 0.8
    target_trades = 30

    regimes_gt20 = df[df["trade_count"] > trade_threshold]
    regime_dependent = bool((regimes_gt20["sharpe"] < 0.5).any())
    critical = bool((regimes_gt20["return_pct"] < -3.0).any())

    negative_returns = df[df["return_pct"] < 0]["return_pct"]
    total_abs = df["return_pct"].abs().sum()
    losing_share = (abs(negative_returns.sum()) / total_abs) if total_abs else 0.0
    acceptable = losing_share < 0.30

    target_failed = df[(df["trade_count"] > target_trades) & (df["sharpe"] < target_sharpe)]["regime"].tolist()
    return_failed = df[df["return_pct"] < -2.0]["regime"].tolist()

    report_path = "outputs/regime_analysis_v2_report.txt"
    with open(report_path, "w") as f:
        f.write("REGIME ANALYSIS REPORT (V2)\n")
        f.write("=" * 70 + "\n")
        f.write(f"REGIME_DEPENDENT (>20 trades, sharpe < 0.5): {'YES' if regime_dependent else 'NO'}\n")
        f.write(f"CRITICAL (>20 trades, return < -3%): {'YES' if critical else 'NO'}\n")
        f.write(f"ACCEPTABLE (losing share < 30%): {'YES' if acceptable else 'NO'}\n")
        f.write(f"Losing return share: {losing_share:.2%}\n")
        if target_failed:
            f.write(f"Target Sharpe > {target_sharpe:.1f} failed (>30 trades): {', '.join(target_failed)}\n")
        if return_failed:
            f.write(f"Return < -2% regimes: {', '.join(return_failed)}\n")
        f.write("\nPer-regime metrics:\n")
        for _, row in df.iterrows():
            f.write(
                f"{row['regime']}: sharpe={row['sharpe']:.2f}, "
                f"return={row['return_pct']:+.2f}%, win_rate={row['win_rate']:.2%}, "
                f"pf={row['profit_factor']:.2f}, trades={int(row['trade_count'])}, "
                f"bars={int(row['bar_count'])}, avg_win={row['avg_win']:.2f}, "
                f"avg_loss={row['avg_loss']:.2f}, max_win={row['max_win']:.2f}, "
                f"max_loss={row['max_loss']:.2f}\n"
            )

    print("\nRegime analysis summary:")
    print(f"  REGIME_DEPENDENT: {'YES' if regime_dependent else 'NO'}")
    print(f"  CRITICAL: {'YES' if critical else 'NO'}")
    print(f"  ACCEPTABLE: {'YES' if acceptable else 'NO'}")
    print(f"  Target Sharpe > {target_sharpe:.1f} failed (>30 trades): {target_failed or 'none'}")
    print(f"  Return < -2% regimes: {return_failed or 'none'}")
    print(f"Saved CSV: {output_csv}")
    print("Saved pie chart: outputs/regime_distribution.png")
    print(f"Saved report: {report_path}")


if __name__ == "__main__":
    main()
