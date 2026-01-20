"""Execute GUARD-003 and GUARD-005 sequentially for the optimal strategy."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

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


def _bootstrap_confidence(
    pnls: np.ndarray,
    initial_capital: float,
    iterations: int = 10000,
    seed: int = 42,
) -> tuple[pd.DataFrame, dict[str, float]]:
    """Bootstrap confidence intervals for Sharpe, return, profit factor."""
    n = len(pnls)
    rng = np.random.default_rng(seed)
    indices = rng.integers(0, n, size=(iterations, n))
    samples = pnls[indices]

    sample_sum = samples.sum(axis=1)
    total_return = sample_sum / initial_capital * 100

    positives = np.where(samples > 0, samples, 0).sum(axis=1)
    negatives = np.where(samples < 0, samples, 0).sum(axis=1)
    profit_factor = np.where(
        negatives == 0,
        np.where(positives > 0, np.inf, 0.0),
        positives / np.abs(negatives),
    )

    returns = samples / initial_capital
    mean_returns = returns.mean(axis=1)
    std_returns = returns.std(axis=1, ddof=0)
    sharpe = np.where(std_returns == 0, 0.0, mean_returns / std_returns * np.sqrt(n))

    metrics = {
        "sharpe": sharpe,
        "total_return": total_return,
        "profit_factor": profit_factor,
    }

    rows = []
    for name, values in metrics.items():
        rows.append(
            {
                "metric": name,
                "mean": float(np.mean(values)),
                "std": float(np.std(values, ddof=0)),
                "ci_lower_95": float(np.percentile(values, 2.5)),
                "ci_upper_95": float(np.percentile(values, 97.5)),
            }
        )

    summary = {row["metric"]: row for row in rows}
    df_summary = pd.DataFrame(rows)
    return df_summary, summary


def _skewness(values: np.ndarray) -> float:
    mean = values.mean()
    m2 = np.mean((values - mean) ** 2)
    if m2 == 0:
        return 0.0
    m3 = np.mean((values - mean) ** 3)
    return float(m3 / (m2 ** 1.5))


def _kurtosis(values: np.ndarray) -> float:
    mean = values.mean()
    m2 = np.mean((values - mean) ** 2)
    if m2 == 0:
        return 0.0
    m4 = np.mean((values - mean) ** 4)
    return float(m4 / (m2 ** 2) - 3.0)


def _longest_streak(signs: np.ndarray, target: int) -> int:
    longest = 0
    current = 0
    for val in signs:
        if val == target:
            current += 1
            longest = max(longest, current)
        else:
            current = 0
    return longest


def main() -> None:
    print("Loading data...")
    data = load_binance_data(warmup=200)

    config = BacktestConfig(
        initial_capital=10000.0,
        fees_bps=5.0,
        slippage_bps=2.0,
        sizing_mode="fixed",
        intrabar_order="stop_first",
    )
    backtester = VectorizedBacktester(config)
    params = build_optimized_params()

    print("Running optimal backtest...")
    result = backtester.run(data, FinalTriggerStrategy(params))
    pnls = _pnl_series(result.trades).to_numpy()

    if len(pnls) == 0:
        raise RuntimeError("No trades found for optimal backtest.")

    print(f"Trades loaded: {len(pnls)}")

    # GUARD-003: Bootstrap confidence intervals
    print("Running bootstrap confidence intervals (10000 iterations)...")
    bootstrap_df, bootstrap_summary = _bootstrap_confidence(
        pnls,
        initial_capital=config.initial_capital,
        iterations=10000,
        seed=42,
    )

    Path("outputs").mkdir(exist_ok=True)
    bootstrap_path = "outputs/bootstrap_confidence.csv"
    bootstrap_df.to_csv(bootstrap_path, index=False)

    sharpe_ci = bootstrap_summary["sharpe"]["ci_lower_95"]
    return_ci = bootstrap_summary["total_return"]["ci_lower_95"]
    statistically_weak = sharpe_ci < 1.0 or return_ci < 0.0

    # GUARD-005: Trade distribution analysis
    print("Running trade distribution analysis...")
    sorted_pnls = np.sort(pnls)[::-1]
    total_pnl = float(pnls.sum())

    top_5_sum = float(sorted_pnls[:5].sum()) if len(sorted_pnls) >= 5 else float(sorted_pnls.sum())
    top_10_sum = float(sorted_pnls[:10].sum()) if len(sorted_pnls) >= 10 else float(sorted_pnls.sum())

    pct_return_top_5 = (top_5_sum / total_pnl * 100) if total_pnl != 0 else 0.0
    pct_return_top_10 = (top_10_sum / total_pnl * 100) if total_pnl != 0 else 0.0

    signs = np.where(pnls > 0, 1, np.where(pnls < 0, -1, 0))
    longest_win_streak = _longest_streak(signs, 1)
    longest_loss_streak = _longest_streak(signs, -1)

    winners = pnls[pnls > 0]
    losers = pnls[pnls < 0]

    distribution_row = {
        "pct_return_top_5": pct_return_top_5,
        "pct_return_top_10": pct_return_top_10,
        "skewness": _skewness(pnls),
        "kurtosis": _kurtosis(pnls),
        "longest_win_streak": longest_win_streak,
        "longest_loss_streak": longest_loss_streak,
        "avg_win": float(winners.mean()) if len(winners) else 0.0,
        "avg_loss": float(losers.mean()) if len(losers) else 0.0,
        "max_win": float(winners.max()) if len(winners) else 0.0,
        "max_loss": float(losers.min()) if len(losers) else 0.0,
    }

    distribution_path = "outputs/trade_distribution.csv"
    pd.DataFrame([distribution_row]).to_csv(distribution_path, index=False)

    outlier_dependent = pct_return_top_5 > 50 or pct_return_top_10 > 70

    print("\nGUARD-003:")
    print(f"  Sharpe CI lower: {sharpe_ci:.2f}")
    print(f"  Return CI lower: {return_ci:+.2f}%")
    print(f"  Flag STATISTICALLY_WEAK: {'YES' if statistically_weak else 'NO'}")
    print(f"  Saved: {bootstrap_path}")

    print("\nGUARD-005:")
    print(f"  pct_return_top_5: {pct_return_top_5:.2f}%")
    print(f"  pct_return_top_10: {pct_return_top_10:.2f}%")
    print(f"  Flag OUTLIER_DEPENDENT: {'YES' if outlier_dependent else 'NO'}")
    print(f"  Saved: {distribution_path}")


if __name__ == "__main__":
    main()
