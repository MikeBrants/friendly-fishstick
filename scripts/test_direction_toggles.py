"""Directional toggle smoke tests for FinalTriggerStrategy."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from crypto_backtest.strategies.final_trigger import FinalTriggerParams, FinalTriggerStrategy


def _make_data(n: int = 800) -> pd.DataFrame:
    rng = np.random.default_rng(42)
    close = 100 + np.cumsum(rng.normal(0, 1, n))
    open_ = close + rng.normal(0, 0.5, n)
    high = np.maximum(open_, close) + 1.0
    low = np.minimum(open_, close) - 1.0
    volume = rng.integers(100, 1000, n)
    index = pd.date_range("2020-01-01", periods=n, freq="H", tz="UTC")
    return pd.DataFrame(
        {
            "open": open_,
            "high": high,
            "low": low,
            "close": close,
            "volume": volume,
        },
        index=index,
    )


def _signals(enable_long: bool, enable_short: bool) -> np.ndarray:
    data = _make_data()
    params = FinalTriggerParams(enable_long=enable_long, enable_short=enable_short)
    strategy = FinalTriggerStrategy(params)
    signals = strategy.generate_signals(data)["signal"].to_numpy()
    return signals


def main() -> None:
    sig_both = _signals(True, True)
    assert set(np.unique(sig_both)).issubset({-1, 0, 1})

    sig_long = _signals(True, False)
    assert (sig_long >= 0).all(), "long-only mode emitted short signals"

    sig_short = _signals(False, True)
    assert (sig_short <= 0).all(), "short-only mode emitted long signals"

    print("PASS")


if __name__ == "__main__":
    main()