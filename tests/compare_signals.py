"""
Compare Pine Script signals with Python implementation.
Expected columns in CSV from TradingView:
- time, open, high, low, close, volume
- Buy Signal (1 or 0)
- Sell Signal (1 or 0)
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from indicators.ichimoku import compute_ichimoku_light_state  # noqa: E402
from indicators.signals import generate_signals_state_mode  # noqa: E402


def _load_data(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    df.columns = [col.strip() for col in df.columns]
    return df


def _compare_signals(
    signals_py: np.ndarray, buy_pine: np.ndarray, sell_pine: np.ndarray, warmup: int
) -> dict:
    long_py = signals_py == 1
    short_py = signals_py == -1

    long_py = long_py[warmup:]
    short_py = short_py[warmup:]
    buy_pine = buy_pine[warmup:]
    sell_pine = sell_pine[warmup:]

    long_match = int(np.sum(long_py & (buy_pine == 1)))
    short_match = int(np.sum(short_py & (sell_pine == 1)))

    buy_total = int(np.sum(buy_pine == 1))
    sell_total = int(np.sum(sell_pine == 1))

    long_rate = (long_match / max(buy_total, 1)) * 100.0
    short_rate = (short_match / max(sell_total, 1)) * 100.0

    return {
        "long": {"python_total": int(np.sum(long_py)), "pine_total": buy_total, "match_rate": long_rate},
        "short": {"python_total": int(np.sum(short_py)), "pine_total": sell_total, "match_rate": short_rate},
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare Pine vs Python signals")
    parser.add_argument("--file", type=str, default=str(ROOT / "data" / "BYBIT_BTCUSDT-60.csv"))
    parser.add_argument("--warmup", type=int, default=52)
    args = parser.parse_args()

    df = _load_data(Path(args.file))

    is_bullish, is_bearish = compute_ichimoku_light_state(
        df["high"].values,
        df["low"].values,
        df["close"].values,
    )
    signals_py, _states = generate_signals_state_mode(is_bullish, is_bearish)

    buy_pine = df["Buy Signal"].fillna(0).astype(int).values
    sell_pine = df["Sell Signal"].fillna(0).astype(int).values

    results = _compare_signals(signals_py, buy_pine, sell_pine, args.warmup)

    print("PINE vs PYTHON SIGNAL MATCH")
    print(
        f"LONG: Python {results['long']['python_total']} | Pine {results['long']['pine_total']} | "
        f"Match {results['long']['match_rate']:.1f}%"
    )
    print(
        f"SHORT: Python {results['short']['python_total']} | Pine {results['short']['pine_total']} | "
        f"Match {results['short']['match_rate']:.1f}%"
    )


if __name__ == "__main__":
    main()
