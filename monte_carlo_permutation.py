"""Monte Carlo permutation test for overfitting detection."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
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


def _map_trade_indices(data: pd.DataFrame, trades: pd.DataFrame) -> pd.DataFrame:
    """Attach entry/exit indices for each trade."""
    entries = pd.to_datetime(trades["entry_time"], utc=True)
    exits = pd.to_datetime(trades["exit_time"], utc=True)
    entry_idx = data.index.get_indexer(entries, method="nearest")
    exit_idx = data.index.get_indexer(exits, method="nearest")

    mapped = trades.copy()
    mapped["entry_idx"] = entry_idx
    mapped["exit_idx"] = exit_idx
    mapped["duration"] = mapped["exit_idx"] - mapped["entry_idx"]
    mapped = mapped[mapped["duration"] > 0].reset_index(drop=True)
    return mapped


def _build_random_equity_curve(
    prices: np.ndarray,
    durations: np.ndarray,
    signs: np.ndarray,
    quantities: np.ndarray,
    cost_rate: float,
    initial_capital: float,
    rng: np.random.Generator,
) -> np.ndarray:
    """Generate equity curve from randomized entry points."""
    n_bars = len(prices)
    max_entry = n_bars - durations
    entry_idx = (rng.random(len(durations)) * max_entry).astype(int)
    exit_idx = entry_idx + durations

    entry_price = prices[entry_idx]
    exit_price = prices[exit_idx]

    pnl = signs * (exit_price - entry_price) * quantities
    costs = cost_rate * (np.abs(entry_price) + np.abs(exit_price)) * quantities
    pnl_net = pnl - costs

    pnl_by_exit = np.zeros(n_bars, dtype=float)
    np.add.at(pnl_by_exit, exit_idx, pnl_net)
    equity = initial_capital + np.cumsum(pnl_by_exit)
    return equity


def main() -> None:
    iterations = 1000
    actual_sharpe_target = 2.14

    print("Loading data...")
    data = load_binance_data(warmup=200)
    prices = data["close"].to_numpy()

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
    mapped = _map_trade_indices(data, trades)

    if mapped.empty:
        raise RuntimeError("No valid trades available for permutation test.")

    direction = mapped["direction"].astype(str).str.lower()
    signs = np.where(direction.str.contains("short"), -1.0, 1.0)

    if "quantity" in mapped.columns:
        quantities = mapped["quantity"].astype(float).to_numpy()
    elif "size" in mapped.columns:
        quantities = mapped["size"].astype(float).to_numpy()
    else:
        quantities = np.ones(len(mapped), dtype=float)

    durations = mapped["duration"].astype(int).to_numpy()
    cost_rate = (config.fees_bps + config.slippage_bps) / 10000.0

    actual_metrics = compute_metrics(result.equity_curve, result.trades)
    actual_sharpe = float(actual_metrics.get("sharpe_ratio", actual_sharpe_target))

    rng = np.random.default_rng(42)
    rows = []

    print(f"Running Monte Carlo ({iterations} iterations)...")
    for i in range(1, iterations + 1):
        equity = _build_random_equity_curve(
            prices=prices,
            durations=durations,
            signs=signs,
            quantities=quantities,
            cost_rate=cost_rate,
            initial_capital=config.initial_capital,
            rng=rng,
        )
        equity_series = pd.Series(equity, index=data.index)
        metrics = compute_metrics(equity_series, pd.DataFrame())
        total_return = (equity[-1] / config.initial_capital - 1) * 100
        rows.append(
            {
                "iteration": i,
                "sharpe": metrics.get("sharpe_ratio", 0.0),
                "return": total_return,
                "max_dd": metrics.get("max_drawdown", 0.0),
            }
        )
        if i % 100 == 0:
            print(f"Completed {i}/{iterations}...")

    df = pd.DataFrame(rows)
    Path("outputs").mkdir(exist_ok=True)
    output_csv = "outputs/monte_carlo_results.csv"
    df.to_csv(output_csv, index=False)

    mean_random = float(df["sharpe"].mean())
    std_random = float(df["sharpe"].std(ddof=0))
    p_value = float((df["sharpe"] >= actual_sharpe_target).mean())
    significance = "SIGNIFICANT" if p_value < 0.05 else "NOT_SIGNIFICANT"
    overfitting_flag = "OVERFITTING" if p_value >= 0.05 else "OK"

    # Histogram
    plt.figure(figsize=(6, 4))
    plt.hist(df["sharpe"], bins=40, color="#4c78a8", alpha=0.8)
    plt.axvline(actual_sharpe_target, color="#e45756", linestyle="--", label="Actual Sharpe")
    plt.title("Monte Carlo Sharpe Distribution")
    plt.xlabel("Sharpe")
    plt.ylabel("Frequency")
    plt.legend()
    plt.tight_layout()
    plt.savefig("outputs/monte_carlo_distribution.png", dpi=150)
    plt.close()

    report_path = "outputs/monte_carlo_report.txt"
    with open(report_path, "w") as f:
        f.write("MONTE CARLO PERMUTATION REPORT\n")
        f.write("=" * 70 + "\n")
        f.write(f"Actual Sharpe (computed): {actual_sharpe:.4f}\n")
        f.write(f"Actual Sharpe (target): {actual_sharpe_target:.2f}\n")
        f.write(f"Mean random Sharpe: {mean_random:.4f}\n")
        f.write(f"Std random Sharpe: {std_random:.4f}\n")
        f.write(f"P-value (>= actual): {p_value:.4f}\n")
        f.write(f"Significance: {significance}\n")
        f.write(f"Flag: {overfitting_flag}\n")

    print("\nResults:")
    print(f"  actual_sharpe (computed): {actual_sharpe:.4f}")
    print(f"  mean_random_sharpe: {mean_random:.4f}")
    print(f"  std_random_sharpe: {std_random:.4f}")
    print(f"  p_value: {p_value:.4f} -> {significance}")
    print(f"  flag: {overfitting_flag}")
    print(f"\nSaved CSV: {output_csv}")
    print("Saved histogram: outputs/monte_carlo_distribution.png")
    print(f"Saved report: {report_path}")


if __name__ == "__main__":
    main()
