"""Position management for multi-take-profit setups."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
import numpy as np
import pandas as pd


@dataclass(frozen=True)
class PositionLeg:
    size: float
    tp_multiple: float


class MultiTPPositionManager:
    """Manages 3-leg trades with trailing stop updates."""

    def __init__(self, legs: list[PositionLeg]) -> None:
        self.legs = legs

    def simulate(
        self,
        signals: pd.DataFrame,
        data: pd.DataFrame,
        initial_capital: float,
    ) -> pd.DataFrame:
        """Simulate multi-TP trade management and return trades."""
        required = {"signal", "entry_price", "sl_price", "tp1_price", "tp2_price", "tp3_price"}
        missing = required.difference(signals.columns)
        if missing:
            raise ValueError(f"Missing signal columns: {sorted(missing)}")
        if signals.empty:
            return pd.DataFrame()

        trades: list[dict[str, Any]] = []
        position: dict[str, Any] | None = None

        for idx, ts in enumerate(data.index):
            bar = data.iloc[idx]
            signal = int(signals["signal"].iloc[idx])

            if position is None:
                if signal == 0:
                    continue
                entry = float(signals["entry_price"].iloc[idx])
                sl = float(signals["sl_price"].iloc[idx])
                tp1 = float(signals["tp1_price"].iloc[idx])
                tp2 = float(signals["tp2_price"].iloc[idx])
                tp3 = float(signals["tp3_price"].iloc[idx])
                if any(np.isnan([entry, sl, tp1, tp2, tp3])):
                    continue

                legs = []
                for i, leg in enumerate(self.legs):
                    notional = initial_capital * leg.size
                    quantity = 0.0 if entry == 0 else notional / entry
                    legs.append(
                        {
                            "index": i,
                            "size": leg.size,
                            "tp": [tp1, tp2, tp3][i],
                            "tp_multiple": leg.tp_multiple,
                            "quantity": quantity,
                            "notional": notional,
                            "active": True,
                        }
                    )

                position = {
                    "direction": signal,
                    "entry_price": entry,
                    "entry_time": ts,
                    "stop": sl,
                    "tp1": tp1,
                    "legs": legs,
                }
                continue

            direction = position["direction"]
            entry_price = position["entry_price"]
            stop = position["stop"]

            if direction == 1:
                if bar["low"] <= stop:
                    self._close_all_legs(trades, position, ts, stop, "stop")
                    position = None
                    continue

                for leg in position["legs"]:
                    if not leg["active"]:
                        continue
                    if bar["high"] >= leg["tp"]:
                        self._close_leg(trades, position, leg, ts, leg["tp"], f"tp{leg['index'] + 1}")
                        if leg["index"] == 0:
                            position["stop"] = entry_price
                        elif leg["index"] == 1:
                            position["stop"] = position["tp1"]

            else:
                if bar["high"] >= stop:
                    self._close_all_legs(trades, position, ts, stop, "stop")
                    position = None
                    continue

                for leg in position["legs"]:
                    if not leg["active"]:
                        continue
                    if bar["low"] <= leg["tp"]:
                        self._close_leg(trades, position, leg, ts, leg["tp"], f"tp{leg['index'] + 1}")
                        if leg["index"] == 0:
                            position["stop"] = entry_price
                        elif leg["index"] == 1:
                            position["stop"] = position["tp1"]

            if position is not None and all(not leg["active"] for leg in position["legs"]):
                position = None

        return pd.DataFrame(trades)

    def _close_leg(
        self,
        trades: list[dict[str, Any]],
        position: dict[str, Any],
        leg: dict[str, Any],
        exit_time,
        exit_price: float,
        reason: str,
    ) -> None:
        direction = position["direction"]
        pnl = (exit_price - position["entry_price"]) * direction * leg["quantity"]
        trades.append(
            {
                "entry_time": position["entry_time"],
                "exit_time": exit_time,
                "direction": direction,
                "entry_price": position["entry_price"],
                "exit_price": exit_price,
                "size": leg["size"],
                "notional": leg["notional"],
                "quantity": leg["quantity"],
                "gross_pnl": pnl,
                "exit_reason": reason,
                "tp_multiple": leg["tp_multiple"],
            }
        )
        leg["active"] = False

    def _close_all_legs(
        self,
        trades: list[dict[str, Any]],
        position: dict[str, Any],
        exit_time,
        exit_price: float,
        reason: str,
    ) -> None:
        for leg in position["legs"]:
            if leg["active"]:
                self._close_leg(trades, position, leg, exit_time, exit_price, reason)
