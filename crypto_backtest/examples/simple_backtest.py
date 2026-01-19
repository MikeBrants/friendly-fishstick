"""Simple backtest example using local CSV data.

Usage:
    python crypto_backtest/examples/simple_backtest.py --file data/BYBIT_BTCUSDT-60.csv
    python crypto_backtest/examples/simple_backtest.py --file data/BYBIT_BTCUSDT-60.csv --warmup 150
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from crypto_backtest.strategies.final_trigger import (  # noqa: E402
    FinalTriggerStrategy,
    FinalTriggerParams,
)
from crypto_backtest.indicators.five_in_one import FiveInOneConfig  # noqa: E402
from crypto_backtest.engine.backtest import VectorizedBacktester, BacktestConfig  # noqa: E402
from crypto_backtest.analysis.metrics import compute_metrics  # noqa: E402


def load_csv(path: Path) -> pd.DataFrame:
    """Load and prepare OHLCV data from CSV."""
    df = pd.read_csv(path)
    df.columns = [col.strip() for col in df.columns]

    required = {"open", "high", "low", "close"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing columns: {sorted(missing)}")

    data = df[["open", "high", "low", "close"]].copy()

    if "volume" in df.columns:
        data["volume"] = df["volume"].fillna(0.0)
    else:
        data["volume"] = 0.0

    if "time" in df.columns:
        time_col = df["time"]
        if pd.api.types.is_numeric_dtype(time_col):
            unit = "ms" if time_col.max() >= 1_000_000_000_000 else "s"
            data.index = pd.to_datetime(time_col, unit=unit, utc=True)
        else:
            data.index = pd.to_datetime(time_col, utc=True)

    return data


def build_strategy() -> FinalTriggerStrategy:
    """Build strategy with default Pine-aligned config."""
    five_in_one = FiveInOneConfig(
        use_distance_filter=False,
        use_volume_filter=False,
        use_regression_cloud=False,
        use_kama_oscillator=False,
        use_ichimoku_filter=True,  # SEUL FILTRE ACTIF
        ichi5in1_strict=False,     # Light mode
        use_transition_mode=False, # State mode
    )
    params = FinalTriggerParams(
        grace_bars=1,
        use_mama_kama_filter=False,
        require_fama_between=False,
        strict_lock_5in1_last=False,
        five_in_one=five_in_one,
    )
    return FinalTriggerStrategy(params)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run simple backtest on local CSV")
    parser.add_argument(
        "--file",
        type=str,
        default=str(ROOT / "data" / "BYBIT_BTCUSDT-60.csv"),
        help="Path to OHLCV CSV file",
    )
    parser.add_argument(
        "--warmup",
        type=int,
        default=150,
        help="Warmup bars to skip (default: 150)",
    )
    parser.add_argument(
        "--capital",
        type=float,
        default=10_000.0,
        help="Initial capital (default: 10000)",
    )
    parser.add_argument(
        "--fees",
        type=float,
        default=5.0,
        help="Fees in bps (default: 5 = 0.05%%)",
    )
    args = parser.parse_args()

    # Load data
    data = load_csv(Path(args.file))
    print(f"Loaded {len(data)} bars from {args.file}")

    # Skip warmup
    data = data.iloc[args.warmup:]
    print(f"After warmup ({args.warmup}): {len(data)} bars")

    # Build strategy and backtester
    strategy = build_strategy()
    config = BacktestConfig(
        initial_capital=args.capital,
        fees_bps=args.fees,
        slippage_bps=2.0,
        sizing_mode="fixed",
    )
    backtester = VectorizedBacktester(config)

    # Run backtest
    result = backtester.run(data, strategy)

    # Print results
    print("\n" + "=" * 50)
    print("BACKTEST RESULTS")
    print("=" * 50)

    n_trades = len(result.trades)
    print(f"Total trades: {n_trades}")

    if n_trades > 0:
        final_equity = result.equity_curve.iloc[-1]
        total_return = (final_equity / args.capital - 1) * 100
        print(f"Initial capital: ${args.capital:,.2f}")
        print(f"Final equity: ${final_equity:,.2f}")
        print(f"Total return: {total_return:+.2f}%")

        # Compute metrics
        metrics = compute_metrics(result.equity_curve, result.trades)
        print(f"\nSharpe Ratio: {metrics.get('sharpe_ratio', 0):.2f}")
        print(f"Sortino Ratio: {metrics.get('sortino_ratio', 0):.2f}")
        print(f"Max Drawdown: {metrics.get('max_drawdown', 0):.1%}")
        print(f"Win Rate: {metrics.get('win_rate', 0):.1%}")
        print(f"Profit Factor: {metrics.get('profit_factor', 0):.2f}")

        # Trade stats
        if "pnl" in result.trades.columns:
            winners = result.trades[result.trades["pnl"] > 0]
            losers = result.trades[result.trades["pnl"] < 0]
            print(f"\nWinners: {len(winners)} | Losers: {len(losers)}")
            if len(winners) > 0:
                print(f"Avg win: ${winners['pnl'].mean():,.2f}")
            if len(losers) > 0:
                print(f"Avg loss: ${losers['pnl'].mean():,.2f}")
    else:
        print("No trades generated.")

    print("=" * 50)


if __name__ == "__main__":
    main()
