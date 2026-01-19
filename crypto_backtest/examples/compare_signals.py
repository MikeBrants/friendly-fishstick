"""Compare model signals against Pine Script exports."""

from __future__ import annotations

import pandas as pd

from crypto_backtest.analysis.validation import compare_signals, load_pine_signals
from crypto_backtest.strategies.final_trigger import FinalTriggerParams, FinalTriggerStrategy


def main() -> None:
    ohlcv_path = "data/ohlcv.csv"
    pine_path = "data/pine_signals.csv"

    data = pd.read_csv(ohlcv_path)
    data["timestamp"] = pd.to_datetime(data["timestamp"], utc=True, errors="coerce")
    data = data.dropna(subset=["timestamp"]).set_index("timestamp")

    pine_signals = load_pine_signals(pine_path, time_col="timestamp", signal_col="signal")

    strategy = FinalTriggerStrategy(FinalTriggerParams())
    signals = strategy.generate_signals(data)
    comparison = compare_signals(pine_signals, signals["signal"])

    print(f"Match rate: {comparison.match_rate:.2%}")
    print(f"Long precision: {comparison.long_precision:.2%} | recall: {comparison.long_recall:.2%}")
    print(f"Short precision: {comparison.short_precision:.2%} | recall: {comparison.short_recall:.2%}")


if __name__ == "__main__":
    main()
