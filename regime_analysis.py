"""Market regime analysis for optimized strategy performance."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from crypto_backtest.analysis.metrics import compute_metrics
from crypto_backtest.engine.backtest import BacktestConfig, VectorizedBacktester
from crypto_backtest.indicators.five_in_one import FiveInOneConfig
from crypto_backtest.indicators.ichimoku import IchimokuConfig
from crypto_backtest.strategies.final_trigger import FinalTriggerParams, FinalTriggerStrategy


REGIMES = ("BULL", "BEAR", "HIGH_VOL", "SIDEWAYS")


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


def classify_regimes(data: pd.DataFrame) -> pd.Series:
    """Classify each bar into regimes."""
    # Shifted inputs prevent look-ahead in regime labeling.
    returns = data["close"].pct_change().shift(1)
    volatility = returns.rolling(50).std().shift(1)

    vol_median = float(volatility.median())
    vol_p75 = float(volatility.quantile(0.75))

    regimes = pd.Series(index=data.index, dtype=object)

    high_vol = volatility >= vol_p75
    sideways = (returns.abs() < 0.005) & (volatility < vol_median)
    bull = (returns > 0) & (volatility < vol_median)
    bear = (returns < 0) & (volatility < vol_median)

    regimes[high_vol] = "HIGH_VOL"
    regimes[sideways] = "SIDEWAYS"
    regimes[bull] = "BULL"
    regimes[bear] = "BEAR"
    regimes[regimes.isna()] = "OTHER"

    return regimes


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


def main() -> None:
    print("Loading data...")
    data = load_binance_data(warmup=200)
    regimes = classify_regimes(data)

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
    for regime in list(REGIMES) + ["OTHER"]:
        mask = regimes == regime
        regime_returns = equity_returns.loc[mask].dropna()

        sharpe = 0.0
        total_return = 0.0
        if not regime_returns.empty:
            mean = regime_returns.mean()
            std = regime_returns.std(ddof=0)
            sharpe = float(mean / std) * (365.25 * 24) ** 0.5 if std != 0 else 0.0
            total_return = float((1 + regime_returns).prod() - 1) * 100

        regime_trades = trades[trades["regime"] == regime]
        pnl = _pnl_series(regime_trades)

        rows.append(
            {
                "regime": regime,
                "sharpe": sharpe,
                "return_pct": total_return,
                "win_rate": _win_rate(pnl),
                "profit_factor": _profit_factor(pnl),
                "trade_count": int(len(regime_trades)),
                "bar_count": int(mask.sum()),
            }
        )

    df = pd.DataFrame(rows)
    output_csv = "outputs/regime_analysis.csv"
    Path("outputs").mkdir(exist_ok=True)
    df.to_csv(output_csv, index=False)

    target_sharpe = 1.0
    flag_regimes = df[df["regime"].isin(REGIMES)]
    regime_dependent = bool((flag_regimes["sharpe"] < 0.5).any() or (flag_regimes["return_pct"] < 0).any())
    target_failed = flag_regimes[flag_regimes["sharpe"] < target_sharpe]["regime"].tolist()
    negative_return = flag_regimes[flag_regimes["return_pct"] < 0]["regime"].tolist()

    report_path = "outputs/regime_analysis_report.txt"
    with open(report_path, "w") as f:
        f.write("REGIME ANALYSIS REPORT\n")
        f.write("=" * 70 + "\n")
        f.write(f"Target Sharpe > {target_sharpe:.1f} in all regimes\n")
        f.write(f"Regime dependent: {'YES' if regime_dependent else 'NO'}\n")
        if target_failed:
            f.write(f"Sharpe < {target_sharpe:.1f}: {', '.join(target_failed)}\n")
        if negative_return:
            f.write(f"Negative return: {', '.join(negative_return)}\n")
        f.write("\nPer-regime metrics:\n")
        for _, row in df.iterrows():
            f.write(
                f"{row['regime']}: sharpe={row['sharpe']:.2f}, "
                f"return={row['return_pct']:+.2f}%, win_rate={row['win_rate']:.2%}, "
                f"pf={row['profit_factor']:.2f}, trades={int(row['trade_count'])}, "
                f"bars={int(row['bar_count'])}\n"
            )

    print("\nRegime analysis summary:")
    print(f"  Regime dependent: {'YES' if regime_dependent else 'NO'}")
    print(f"  Target Sharpe > {target_sharpe:.1f} failed in: {target_failed or 'none'}")
    print(f"  Negative return regimes: {negative_return or 'none'}")
    print(f"Saved CSV: {output_csv}")
    print(f"Saved report: {report_path}")


if __name__ == "__main__":
    main()
