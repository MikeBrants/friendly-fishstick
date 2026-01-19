"""Position management for multi-take-profit setups."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal
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
        sizing_mode: Literal["fixed", "equity"] = "fixed",
        intrabar_order: Literal["stop_first", "tp_first"] = "stop_first",
        fees_bps: float = 0.0,
        slippage_bps: float = 0.0,
    ) -> pd.DataFrame:
        """Simulate multi-TP trade management and return trades."""
        required = {"signal", "entry_price", "sl_price", "tp1_price", "tp2_price", "tp3_price"}
        missing = required.difference(signals.columns)
        if missing:
            raise ValueError(f"Missing signal columns: {sorted(missing)}")
        if signals.empty:
            return pd.DataFrame()
        if sizing_mode not in {"fixed", "equity"}:
            raise ValueError("sizing_mode must be 'fixed' or 'equity'")
        if intrabar_order not in {"stop_first", "tp_first"}:
            raise ValueError("intrabar_order must be 'stop_first' or 'tp_first'")

        trades: list[dict[str, Any]] = []
        position: dict[str, Any] | None = None
        equity = initial_capital
        cost_rate = (fees_bps + slippage_bps) / 10_000.0

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

                trade_capital = initial_capital if sizing_mode == "fixed" else equity
                legs = []
                for i, leg in enumerate(self.legs):
                    notional = trade_capital * leg.size
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
                    "realized_pnl": 0.0,
                }
                continue

            direction = position["direction"]
            entry_price = position["entry_price"]

            if direction == 1:
                stop_hit = bar["low"] <= position["stop"]
                tp_hit = bar["high"] >= min(
                    [leg["tp"] for leg in position["legs"] if leg["active"]] or [np.inf]
                )
                if intrabar_order == "stop_first":
                    if stop_hit:
                        position["realized_pnl"] += self._close_all_legs(
                            trades, position, ts, position["stop"], "stop", cost_rate
                        )
                        equity += position["realized_pnl"] if sizing_mode == "equity" else 0.0
                        position = None
                        continue
                    self._process_tp_hits(
                        trades, position, ts, entry_price, bar["high"], direction, cost_rate
                    )
                else:
                    if tp_hit:
                        self._process_tp_hits(
                            trades, position, ts, entry_price, bar["high"], direction, cost_rate
                        )
                    stop_hit = bar["low"] <= position["stop"]
                    if stop_hit and position is not None and any(leg["active"] for leg in position["legs"]):
                        position["realized_pnl"] += self._close_all_legs(
                            trades, position, ts, position["stop"], "stop", cost_rate
                        )
                        equity += position["realized_pnl"] if sizing_mode == "equity" else 0.0
                        position = None
                        continue

            else:
                stop_hit = bar["high"] >= position["stop"]
                tp_hit = bar["low"] <= max(
                    [leg["tp"] for leg in position["legs"] if leg["active"]] or [-np.inf]
                )
                if intrabar_order == "stop_first":
                    if stop_hit:
                        position["realized_pnl"] += self._close_all_legs(
                            trades, position, ts, position["stop"], "stop", cost_rate
                        )
                        equity += position["realized_pnl"] if sizing_mode == "equity" else 0.0
                        position = None
                        continue
                    self._process_tp_hits(
                        trades, position, ts, entry_price, bar["low"], direction, cost_rate
                    )
                else:
                    if tp_hit:
                        self._process_tp_hits(
                            trades, position, ts, entry_price, bar["low"], direction, cost_rate
                        )
                    stop_hit = bar["high"] >= position["stop"]
                    if stop_hit and position is not None and any(leg["active"] for leg in position["legs"]):
                        position["realized_pnl"] += self._close_all_legs(
                            trades, position, ts, position["stop"], "stop", cost_rate
                        )
                        equity += position["realized_pnl"] if sizing_mode == "equity" else 0.0
                        position = None
                        continue

            if position is not None and all(not leg["active"] for leg in position["legs"]):
                if sizing_mode == "equity":
                    equity += position["realized_pnl"]
                position = None

        return pd.DataFrame(trades)

    def _process_tp_hits(
        self,
        trades: list[dict[str, Any]],
        position: dict[str, Any],
        exit_time,
        entry_price: float,
        extreme_price: float,
        direction: int,
        cost_rate: float,
    ) -> None:
        for leg in position["legs"]:
            if not leg["active"]:
                continue
            if (direction == 1 and extreme_price >= leg["tp"]) or (
                direction == -1 and extreme_price <= leg["tp"]
            ):
                pnl = self._close_leg(
                    trades, position, leg, exit_time, leg["tp"], f"tp{leg['index'] + 1}", cost_rate
                )
                position["realized_pnl"] += pnl
                if leg["index"] == 0:
                    position["stop"] = entry_price
                elif leg["index"] == 1:
                    position["stop"] = position["tp1"]

    def _close_leg(
        self,
        trades: list[dict[str, Any]],
        position: dict[str, Any],
        leg: dict[str, Any],
        exit_time,
        exit_price: float,
        reason: str,
        cost_rate: float,
    ) -> float:
        direction = position["direction"]
        pnl = (exit_price - position["entry_price"]) * direction * leg["quantity"]
        costs = leg["notional"] * cost_rate * 2.0
        net_pnl = pnl - costs
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
                "costs": costs,
                "net_pnl": net_pnl,
                "exit_reason": reason,
                "tp_multiple": leg["tp_multiple"],
            }
        )
        leg["active"] = False
        return net_pnl

    def _close_all_legs(
        self,
        trades: list[dict[str, Any]],
        position: dict[str, Any],
        exit_time,
        exit_price: float,
        reason: str,
        cost_rate: float,
    ) -> float:
        pnl_total = 0.0
        for leg in position["legs"]:
            if leg["active"]:
                pnl_total += self._close_leg(
                    trades, position, leg, exit_time, exit_price, reason, cost_rate
                )
        return pnl_total
