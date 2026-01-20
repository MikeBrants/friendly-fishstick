"""Sensitivity analysis for optimized Ichimoku parameters."""

from __future__ import annotations

import argparse
import itertools
import os
from pathlib import Path
from typing import Iterable

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from concurrent.futures import ProcessPoolExecutor

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


def build_params(tenkan: int, kijun: int, tenkan_5: int, kijun_5: int) -> FinalTriggerParams:
    """Return FinalTriggerParams using the provided Ichimoku values."""
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
        tenkan_5=tenkan_5,
        kijun_5=kijun_5,
        displacement_5=52,
    )

    ichimoku = IchimokuConfig(
        tenkan=tenkan,
        kijun=kijun,
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


def run_backtest(
    data: pd.DataFrame, backtester: VectorizedBacktester, params: FinalTriggerParams
) -> dict[str, float]:
    """Run a backtest and return the required metrics."""
    result = backtester.run(data, FinalTriggerStrategy(params))
    metrics = compute_metrics(result.equity_curve, result.trades)
    final_equity = float(result.equity_curve.iloc[-1]) if len(result.equity_curve) else 0.0

    total_return = (final_equity / backtester.config.initial_capital - 1) * 100
    return {
        "sharpe": metrics.get("sharpe_ratio", 0.0),
        "total_return_pct": total_return,
        "max_drawdown_pct": metrics.get("max_drawdown", 0.0) * 100,
        "profit_factor": metrics.get("profit_factor", 0.0),
        "trades": int(len(result.trades)),
    }

def _run_combo(combo: tuple[int, int, int, int]) -> dict[str, float]:
    """Worker entrypoint for a single parameter combination."""
    tenkan, kijun, tenkan_5, kijun_5 = combo
    data = load_binance_data(warmup=200)
    config = BacktestConfig(
        initial_capital=10000.0,
        fees_bps=5.0,
        slippage_bps=2.0,
        sizing_mode="fixed",
        intrabar_order="stop_first",
    )
    backtester = VectorizedBacktester(config)
    params = build_params(tenkan, kijun, tenkan_5, kijun_5)
    metrics = run_backtest(data, backtester, params)
    return {
        "tenkan": tenkan,
        "kijun": kijun,
        "tenkan_5": tenkan_5,
        "kijun_5": kijun_5,
        **metrics,
    }


def _iter_batches(items: list[tuple[int, int, int, int]], batch_size: int) -> Iterable[list[tuple[int, int, int, int]]]:
    """Yield list batches from items."""
    for i in range(0, len(items), batch_size):
        yield items[i : i + batch_size]


def _load_done(output_csv: str) -> set[tuple[int, int, int, int]]:
    """Load already processed combos from an existing output CSV."""
    if not Path(output_csv).exists():
        return set()
    df_done = pd.read_csv(output_csv)
    return {
        (int(r.tenkan), int(r.kijun), int(r.tenkan_5), int(r.kijun_5))
        for r in df_done.itertuples(index=False)
    }


def plot_heatmap(
    pivot: pd.DataFrame, title: str, xlabel: str, ylabel: str, output_path: str
) -> None:
    """Render and save a heatmap for a pivot table."""
    fig, ax = plt.subplots(figsize=(6, 4))
    im = ax.imshow(pivot.values, origin="lower", aspect="auto", cmap="viridis")
    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_xticks(range(len(pivot.columns)))
    ax.set_yticks(range(len(pivot.index)))
    ax.set_xticklabels(pivot.columns)
    ax.set_yticklabels(pivot.index)
    fig.colorbar(im, ax=ax, label="Sharpe")
    fig.tight_layout()
    fig.savefig(output_path, dpi=150)
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser(description="Sensitivity grid analysis (Ichimoku).")
    parser.add_argument("--workers", type=int, default=max(os.cpu_count() - 1, 1))
    parser.add_argument("--batch-size", type=int, default=50)
    parser.add_argument("--resume", action="store_true", help="Resume from existing CSV.")
    args = parser.parse_args()

    Path("outputs").mkdir(exist_ok=True)
    output_csv = "outputs/sensitivity_grid_results.csv"
    done = _load_done(output_csv) if args.resume else set()

    tenkan_range = range(11, 16)
    kijun_range = range(32, 37)
    tenkan_5_range = range(10, 15)
    kijun_5_range = range(19, 24)

    combos = list(itertools.product(tenkan_range, kijun_range, tenkan_5_range, kijun_5_range))
    pending = [combo for combo in combos if combo not in done]
    total = len(combos)

    if done:
        print(f"Resuming: {len(done)} completed, {len(pending)} pending, total {total}.")
    else:
        print(f"Starting: {total} total runs.")

    if not pending:
        print("All combinations already processed.")
    else:
        header = not Path(output_csv).exists()
        with ProcessPoolExecutor(max_workers=args.workers) as executor:
            completed = len(done)
            for batch in _iter_batches(pending, args.batch_size):
                results = list(executor.map(_run_combo, batch))
                batch_df = pd.DataFrame(results)
                batch_df.to_csv(output_csv, mode="a", header=header, index=False)
                header = False
                completed += len(batch)
                print(f"Completed {completed}/{total} runs...")

    df = pd.read_csv(output_csv)

    # Heatmap: sharpe vs (tenkan, kijun)
    pivot_ichi = (
        df.groupby(["tenkan", "kijun"])["sharpe"]
        .mean()
        .unstack()
        .sort_index()
    )
    plot_heatmap(
        pivot_ichi,
        "Sharpe Heatmap: Ichimoku (tenkan vs kijun)",
        "kijun",
        "tenkan",
        "outputs/sensitivity_heatmap_ichimoku.png",
    )

    # Heatmap: sharpe vs (tenkan_5, kijun_5)
    pivot_5in1 = (
        df.groupby(["tenkan_5", "kijun_5"])["sharpe"]
        .mean()
        .unstack()
        .sort_index()
    )
    plot_heatmap(
        pivot_5in1,
        "Sharpe Heatmap: 5-in-1 (tenkan_5 vs kijun_5)",
        "kijun_5",
        "tenkan_5",
        "outputs/sensitivity_heatmap_5in1.png",
    )

    # Variance in ±1 neighborhood of optimal
    neighborhood = df[
        df["tenkan"].between(12, 14)
        & df["kijun"].between(33, 35)
        & df["tenkan_5"].between(11, 13)
        & df["kijun_5"].between(20, 22)
    ]
    mean_sharpe = float(neighborhood["sharpe"].mean())
    std_sharpe = float(neighborhood["sharpe"].std(ddof=0))
    variance_pct = (std_sharpe / mean_sharpe * 100) if mean_sharpe else float("inf")

    if variance_pct < 10:
        robustness = "ROBUST"
    elif variance_pct > 20:
        robustness = "UNSTABLE"
    else:
        robustness = "MODERATE"

    report_path = "outputs/sensitivity_report.txt"
    with open(report_path, "w") as f:
        f.write("SENSITIVITY ANALYSIS REPORT\n")
        f.write("=" * 70 + "\n")
        f.write("Grid:\n")
        f.write("  tenkan: 11-15\n")
        f.write("  kijun: 32-36\n")
        f.write("  tenkan_5: 10-14\n")
        f.write("  kijun_5: 19-23\n\n")
        f.write("Fixed params:\n")
        f.write("  ATR SL/TP: 3.75/3.75/9.0/7.0\n")
        f.write("  displacement: 52\n")
        f.write("  displacement_5: 52\n")
        f.write("  warmup: 200 bars\n\n")
        f.write("Neighborhood (±1 around 13/34, 12/21):\n")
        f.write(f"  mean sharpe: {mean_sharpe:.4f}\n")
        f.write(f"  std sharpe: {std_sharpe:.4f}\n")
        f.write(f"  variance % (std/mean): {variance_pct:.2f}%\n")
        f.write(f"  robustness: {robustness}\n")

    print(f"\nSaved grid results: {output_csv}")
    print("Saved heatmaps:")
    print("  outputs/sensitivity_heatmap_ichimoku.png")
    print("  outputs/sensitivity_heatmap_5in1.png")
    print(f"Saved report: {report_path}")
    print(f"Neighborhood variance: {variance_pct:.2f}% -> {robustness}")


if __name__ == "__main__":
    main()
