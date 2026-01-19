"""
Compare Pine Script FINAL LONG/SHORT signals with Python implementation.
Expected columns in CSV from TradingView:
- time, open, high, low, close
- FINAL LONG (1 or 0)
- FINAL SHORT (1 or 0)
Optional debug columns:
- All Confimed (trend state)
- Buy Signal / Sell Signal (trend transitions)
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from crypto_backtest.indicators.five_in_one import FiveInOneConfig  # noqa: E402
from crypto_backtest.indicators.ichimoku import Ichimoku, IchimokuConfig  # noqa: E402
from crypto_backtest.strategies.final_trigger import (  # noqa: E402
    FinalTriggerParams,
    FinalTriggerStrategy,
)


def _load_data(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    df.columns = [col.strip() for col in df.columns]
    return df


def _prepare_ohlcv(df: pd.DataFrame) -> pd.DataFrame:
    missing = {"open", "high", "low", "close"}.difference(df.columns)
    if missing:
        raise ValueError(f"Missing OHLC columns: {sorted(missing)}")
    data = df.copy()
    if "volume" not in data.columns:
        data["volume"] = 0.0
    if "time" in data.columns:
        time_series = data["time"]
        if pd.api.types.is_numeric_dtype(time_series):
            time_unit = "ms" if time_series.max() >= 1_000_000_000_000 else "s"
            data["time"] = pd.to_datetime(time_series, unit=time_unit, utc=True, errors="coerce")
        else:
            data["time"] = pd.to_datetime(time_series, utc=True, errors="coerce")
        data = data.dropna(subset=["time"]).set_index("time")
    return data[["open", "high", "low", "close", "volume"]]


def _build_strategy() -> FinalTriggerStrategy:
    five_in_one = FiveInOneConfig(
        use_distance_filter=False,
        use_volume_filter=False,
        use_regression_cloud=False,
        use_kama_oscillator=False,
        use_ichimoku_filter=True,
        ichi5in1_strict=False,
        use_transition_mode=False,
    )
    params = FinalTriggerParams(
        grace_bars=1,
        use_mama_kama_filter=False,
        require_fama_between=False,
        strict_lock_5in1_last=False,
        five_in_one=five_in_one,
    )
    return FinalTriggerStrategy(params)


def _compare_signals(
    signals_py: np.ndarray,
    final_long_pine: np.ndarray,
    final_short_pine: np.ndarray,
    warmup: int,
) -> dict:
    long_py = signals_py == 1
    short_py = signals_py == -1

    long_py = long_py[warmup:]
    short_py = short_py[warmup:]
    final_long_pine = final_long_pine[warmup:]
    final_short_pine = final_short_pine[warmup:]

    long_match = int(np.sum(long_py & (final_long_pine == 1)))
    short_match = int(np.sum(short_py & (final_short_pine == 1)))

    long_total = int(np.sum(final_long_pine == 1))
    short_total = int(np.sum(final_short_pine == 1))

    long_rate = (long_match / max(long_total, 1)) * 100.0
    short_rate = (short_match / max(short_total, 1)) * 100.0

    return {
        "long": {"python_total": int(np.sum(long_py)), "pine_total": long_total, "match_rate": long_rate},
        "short": {"python_total": int(np.sum(short_py)), "pine_total": short_total, "match_rate": short_rate},
    }


def _compute_ichimoku_trend_state(
    data: pd.DataFrame, config: IchimokuConfig
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    ichi = Ichimoku(config)
    ichi.compute(data)
    all_bullish = ichi.all_bullish(data["close"]).fillna(False).to_numpy()
    all_bearish = ichi.all_bearish(data["close"]).fillna(False).to_numpy()

    n = len(data)
    buy_signal_raw = np.zeros(n, dtype=bool)
    sell_signal_raw = np.zeros(n, dtype=bool)
    trend_state = np.zeros(n, dtype=int)

    trade_op = False
    ichi_state = 0
    for i in range(n):
        if all_bullish[i] and not trade_op:
            buy_signal_raw[i] = True
        if all_bearish[i] and trade_op:
            sell_signal_raw[i] = True

        if buy_signal_raw[i]:
            trade_op = True
            ichi_state = 1
        elif sell_signal_raw[i]:
            trade_op = False
            ichi_state = -1

        trend_state[i] = ichi_state

    return trend_state, buy_signal_raw, sell_signal_raw


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare Pine vs Python FINAL signals")
    parser.add_argument("--file", type=str, default=str(ROOT / "data" / "BYBIT_BTCUSDT-60.csv"))
    parser.add_argument("--warmup", type=int, default=150)
    parser.add_argument(
        "--debug-trend",
        action="store_true",
        help="Compare Ichimoku trend state vs All Confimed and transitions vs Buy/Sell.",
    )
    args = parser.parse_args()

    warmup = args.warmup
    if warmup < 100:
        print("Warmup < 100 requested; using minimum warmup of 100.")
        warmup = 100

    df = _load_data(Path(args.file))
    data = _prepare_ohlcv(df)

    strategy = _build_strategy()
    signals_df = strategy.generate_signals(data)
    signals_py = signals_df["signal"].to_numpy()

    if "FINAL LONG" not in df.columns or "FINAL SHORT" not in df.columns:
        raise ValueError("Missing FINAL LONG/FINAL SHORT columns in CSV.")

    final_long_pine = df["FINAL LONG"].fillna(0).astype(int).values
    final_short_pine = df["FINAL SHORT"].fillna(0).astype(int).values

    results = _compare_signals(signals_py, final_long_pine, final_short_pine, warmup)

    print("PINE vs PYTHON SIGNAL MATCH")
    print(
        f"LONG: Python {results['long']['python_total']} | Pine {results['long']['pine_total']} | "
        f"Match {results['long']['match_rate']:.1f}%"
    )
    print(
        f"SHORT: Python {results['short']['python_total']} | Pine {results['short']['pine_total']} | "
        f"Match {results['short']['match_rate']:.1f}%"
    )

    if args.debug_trend:
        trend_state, buy_transitions, sell_transitions = _compute_ichimoku_trend_state(
            data, IchimokuConfig()
        )
        if "All Confimed" in df.columns:
            all_confirmed = df["All Confimed"].fillna(0).astype(int).values
            mask = all_confirmed[warmup:] != 0
            if mask.any():
                match_rate = (
                    (trend_state[warmup:][mask] == all_confirmed[warmup:][mask]).mean() * 100.0
                )
                print(f"DEBUG trend match vs All Confimed: {match_rate:.1f}%")
            else:
                print("DEBUG trend match vs All Confimed: no non-zero rows after warmup.")
        else:
            print("DEBUG trend: column All Confimed not found.")

        if "Buy Signal" in df.columns and "Sell Signal" in df.columns:
            buy_pine = df["Buy Signal"].fillna(0).astype(int).values
            sell_pine = df["Sell Signal"].fillna(0).astype(int).values
            buy_match = int(np.sum(buy_transitions[warmup:] & (buy_pine[warmup:] == 1)))
            sell_match = int(np.sum(sell_transitions[warmup:] & (sell_pine[warmup:] == 1)))
            buy_total = int(np.sum(buy_pine[warmup:] == 1))
            sell_total = int(np.sum(sell_pine[warmup:] == 1))
            buy_rate = (buy_match / max(buy_total, 1)) * 100.0
            sell_rate = (sell_match / max(sell_total, 1)) * 100.0
            print(f"DEBUG transitions vs Buy Signal: {buy_rate:.1f}%")
            print(f"DEBUG transitions vs Sell Signal: {sell_rate:.1f}%")
        else:
            print("DEBUG transitions: Buy Signal/Sell Signal columns not found.")


if __name__ == "__main__":
    main()
