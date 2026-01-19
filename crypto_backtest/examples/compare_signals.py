"""Compare model signals against Pine Script exports."""

from __future__ import annotations

import argparse
import pandas as pd

from crypto_backtest.analysis.validation import compare_signals, load_pine_signals
from crypto_backtest.strategies.final_trigger import FinalTriggerParams, FinalTriggerStrategy


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare strategy signals vs Pine exports.")
    parser.add_argument(
        "--ohlcv",
        default="btc_for_compare_signals.csv",
        help="CSV with time/open/high/low/close (and optionally signal).",
    )
    parser.add_argument(
        "--pine",
        default=None,
        help="Optional CSV with Pine signals (time + signal).",
    )
    parser.add_argument("--time-col", default="time", help="Time column name.")
    parser.add_argument("--signal-col", default="signal", help="Signal column name.")
    args = parser.parse_args()

    data = pd.read_csv(args.ohlcv)
    if args.time_col not in data.columns:
        raise ValueError(f"Missing time column '{args.time_col}' in {args.ohlcv}")
    data[args.time_col] = pd.to_datetime(data[args.time_col], utc=True, errors="coerce")
    data = data.dropna(subset=[args.time_col]).set_index(args.time_col)

    if args.pine:
        pine_signals = load_pine_signals(
            args.pine, time_col=args.time_col, signal_col=args.signal_col
        )
    else:
        if args.signal_col not in data.columns:
            raise ValueError(
                f"Missing '{args.signal_col}' in {args.ohlcv}; add it or pass --pine."
            )
        pine_signals = data[args.signal_col]

    strategy = FinalTriggerStrategy(FinalTriggerParams())
    signals = strategy.generate_signals(data)
    comparison = compare_signals(pine_signals, signals["signal"])

    print(f"Match rate: {comparison.match_rate:.2%}")
    print(f"Long precision: {comparison.long_precision:.2%} | recall: {comparison.long_recall:.2%}")
    print(f"Short precision: {comparison.short_precision:.2%} | recall: {comparison.short_recall:.2%}")


if __name__ == "__main__":
    main()
