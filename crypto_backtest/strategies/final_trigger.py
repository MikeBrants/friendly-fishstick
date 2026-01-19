"""FINAL TRIGGER v2 strategy implementation."""

from __future__ import annotations

from dataclasses import dataclass, field
import numpy as np
import pandas as pd

from crypto_backtest.indicators.atr import compute_atr
from crypto_backtest.indicators.five_in_one import FiveInOneConfig, FiveInOneFilter
from crypto_backtest.indicators.ichimoku import Ichimoku, IchimokuConfig
from crypto_backtest.indicators.mama_fama_kama import compute_kama, compute_mama_fama
from .base import BaseStrategy


@dataclass(frozen=True)
class FinalTriggerParams:
    grace_bars: int = 1
    use_mama_kama_filter: bool = False  # Pine default: OFF
    require_fama_between: bool = False
    strict_lock_5in1_last: bool = False
    price_tol_pct: float = 0.0001
    debug_signals: bool = False
    debug_signals_path: str = "debug_signals.csv"
    mama_fast_limit: float = 0.5
    mama_slow_limit: float = 0.05
    kama_length: int = 20
    atr_length: int = 14
    sl_mult: float = 3.0
    tp1_mult: float = 2.0
    tp2_mult: float = 6.0
    tp3_mult: float = 10.0
    ichimoku: IchimokuConfig = field(default_factory=IchimokuConfig)
    five_in_one: FiveInOneConfig = field(default_factory=FiveInOneConfig)


class FinalTriggerStrategy(BaseStrategy):
    """Strategy using Ichimoku + MAMA/KAMA + Five-in-One filters."""

    def __init__(self, params: FinalTriggerParams) -> None:
        self.params = params

    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """Return signal, entry, SL and TP levels for each bar."""
        missing = {"open", "high", "low", "close", "volume"}.difference(data.columns)
        if missing:
            raise ValueError(f"Missing columns for strategy: {sorted(missing)}")

        close = data["close"]
        mama_fama = compute_mama_fama(
            close,
            self.params.mama_fast_limit,
            self.params.mama_slow_limit,
            er_length=self.params.kama_length,
        )
        mama = mama_fama["mama"]
        fama = mama_fama["fama"]
        kama = compute_kama(close, self.params.kama_length)

        # Apply a small relative tolerance to reduce boundary flips vs Pine.
        tol = close * self.params.price_tol_pct
        cond_mk_long_base = (close > mama + tol) & (mama > kama)
        cond_mk_short_base = (close < mama - tol) & (mama < kama)
        cond_fama_between_long = (kama < fama) & (fama < mama)
        cond_fama_between_short = (mama < fama) & (fama < kama)

        if self.params.require_fama_between:
            cond_mk_long = cond_mk_long_base & cond_fama_between_long
            cond_mk_short = cond_mk_short_base & cond_fama_between_short
        else:
            cond_mk_long = cond_mk_long_base
            cond_mk_short = cond_mk_short_base

        cross_long_ok = (mama.shift(1) <= kama.shift(1)) & (mama > kama)
        cross_short_ok = (mama.shift(1) >= kama.shift(1)) & (mama < kama)
        if self.params.require_fama_between:
            cross_long_ok &= cond_fama_between_long
            cross_short_ok &= cond_fama_between_short

        ichi = Ichimoku(self.params.ichimoku)
        ichi.compute(data)
        all_bullish = ichi.all_bullish(close).fillna(False)
        all_bearish = ichi.all_bearish(close).fillna(False)

        n = len(data)
        debug_enabled = self.params.debug_signals
        buy_signal_raw = np.zeros(n, dtype=bool)
        sell_signal_raw = np.zeros(n, dtype=bool)
        ichi_long_active = np.zeros(n, dtype=bool)
        ichi_short_active = np.zeros(n, dtype=bool)

        trade_op = False
        ichi_state = 0
        for i in range(n):
            if all_bullish.iloc[i] and not trade_op:
                buy_signal_raw[i] = True
            if all_bearish.iloc[i] and trade_op:
                sell_signal_raw[i] = True

            if buy_signal_raw[i]:
                trade_op = True
                ichi_state = 1
            elif sell_signal_raw[i]:
                trade_op = False
                ichi_state = -1

            ichi_long_active[i] = ichi_state == 1
            ichi_short_active[i] = ichi_state == -1

        five_filter = FiveInOneFilter(self.params.five_in_one)
        five_signal = five_filter.compute_combined(
            data, transition_mode=self.params.five_in_one.use_transition_mode
        )
        bullish_signal = five_signal == 1
        bearish_signal = five_signal == -1

        new_long_close = np.zeros(n, dtype=bool)
        new_short_close = np.zeros(n, dtype=bool)
        if debug_enabled:
            armed_long_strict_state = np.zeros(n, dtype=bool)
            armed_short_strict_state = np.zeros(n, dtype=bool)
            armed_long_grace_state = np.zeros(n, dtype=bool)
            armed_short_grace_state = np.zeros(n, dtype=bool)
            pending_long_state = np.zeros(n, dtype=bool)
            pending_short_state = np.zeros(n, dtype=bool)
            lock_long_cycle_state = np.zeros(n, dtype=bool)
            lock_short_cycle_state = np.zeros(n, dtype=bool)
            allow_long_state = np.zeros(n, dtype=bool)
            allow_short_state = np.zeros(n, dtype=bool)
            trigger_long_state = np.zeros(n, dtype=bool)
            trigger_short_state = np.zeros(n, dtype=bool)
            final_long_active_state = np.zeros(n, dtype=bool)
            final_short_active_state = np.zeros(n, dtype=bool)

        lock_long_cycle = False
        lock_short_cycle = False
        pending_long = False
        pending_short = False
        final_long_active = False
        final_short_active = False

        for i in range(n):
            prev_pending_long = pending_long
            prev_pending_short = pending_short

            armed_long_strict = ichi_long_active[i] and (
                not self.params.use_mama_kama_filter or cond_mk_long.iloc[i]
            )
            armed_short_strict = ichi_short_active[i] and (
                not self.params.use_mama_kama_filter or cond_mk_short.iloc[i]
            )
            armed_long_grace_ok = ichi_long_active[i] and (
                not self.params.use_mama_kama_filter
                or cond_mk_long.iloc[i]
                or cross_long_ok.iloc[i]
            )
            armed_short_grace_ok = ichi_short_active[i] and (
                not self.params.use_mama_kama_filter
                or cond_mk_short.iloc[i]
                or cross_short_ok.iloc[i]
            )

            if buy_signal_raw[i] or sell_signal_raw[i]:
                lock_long_cycle = False
                lock_short_cycle = False
                pending_long = False
                pending_short = False

            if not ichi_long_active[i]:
                final_long_active = False
            if not ichi_short_active[i]:
                final_short_active = False

            if (
                self.params.strict_lock_5in1_last
                and bullish_signal.iloc[i]
                and ichi_long_active[i]
                and not armed_long_strict
            ):
                if self.params.grace_bars == 1:
                    pending_long = True
                else:
                    lock_long_cycle = True

            if (
                self.params.strict_lock_5in1_last
                and bearish_signal.iloc[i]
                and ichi_short_active[i]
                and not armed_short_strict
            ):
                if self.params.grace_bars == 1:
                    pending_short = True
                else:
                    lock_short_cycle = True

            if prev_pending_long and not armed_long_grace_ok:
                pending_long = False
                if self.params.strict_lock_5in1_last:
                    lock_long_cycle = True

            if prev_pending_short and not armed_short_grace_ok:
                pending_short = False
                if self.params.strict_lock_5in1_last:
                    lock_short_cycle = True

            allow_long = not self.params.strict_lock_5in1_last or not lock_long_cycle
            allow_short = not self.params.strict_lock_5in1_last or not lock_short_cycle

            pending_long_ok = (
                self.params.grace_bars == 1 and prev_pending_long and armed_long_grace_ok
            )
            pending_short_ok = (
                self.params.grace_bars == 1 and prev_pending_short and armed_short_grace_ok
            )

            trigger_long = (bullish_signal.iloc[i] and armed_long_strict) or pending_long_ok
            trigger_short = (bearish_signal.iloc[i] and armed_short_strict) or pending_short_ok

            new_long = trigger_long and allow_long and not final_long_active
            new_short = trigger_short and allow_short and not final_short_active

            if new_long:
                final_long_active = True
                final_short_active = False
                pending_long = False
                new_long_close[i] = True

            if new_short:
                final_short_active = True
                final_long_active = False
                pending_short = False
                new_short_close[i] = True
            if debug_enabled:
                armed_long_strict_state[i] = armed_long_strict
                armed_short_strict_state[i] = armed_short_strict
                armed_long_grace_state[i] = armed_long_grace_ok
                armed_short_grace_state[i] = armed_short_grace_ok
                pending_long_state[i] = pending_long
                pending_short_state[i] = pending_short
                lock_long_cycle_state[i] = lock_long_cycle
                lock_short_cycle_state[i] = lock_short_cycle
                allow_long_state[i] = allow_long
                allow_short_state[i] = allow_short
                trigger_long_state[i] = trigger_long
                trigger_short_state[i] = trigger_short
                final_long_active_state[i] = final_long_active
                final_short_active_state[i] = final_short_active

        atr = compute_atr(data["high"], data["low"], close, self.params.atr_length)
        signal = np.zeros(n, dtype=int)
        entry_price = np.full(n, np.nan)
        sl_price = np.full(n, np.nan)
        tp1_price = np.full(n, np.nan)
        tp2_price = np.full(n, np.nan)
        tp3_price = np.full(n, np.nan)

        for i in range(n):
            if new_long_close[i]:
                entry = float(close.iloc[i])
                atr_val = float(atr.iloc[i])
                signal[i] = 1
                entry_price[i] = entry
                sl_price[i] = entry - self.params.sl_mult * atr_val
                tp1_price[i] = entry + self.params.tp1_mult * atr_val
                tp2_price[i] = entry + self.params.tp2_mult * atr_val
                tp3_price[i] = entry + self.params.tp3_mult * atr_val
            elif new_short_close[i]:
                entry = float(close.iloc[i])
                atr_val = float(atr.iloc[i])
                signal[i] = -1
                entry_price[i] = entry
                sl_price[i] = entry + self.params.sl_mult * atr_val
                tp1_price[i] = entry - self.params.tp1_mult * atr_val
                tp2_price[i] = entry - self.params.tp2_mult * atr_val
                tp3_price[i] = entry - self.params.tp3_mult * atr_val
        if debug_enabled:
            debug_df = pd.DataFrame(
                {
                    "close": close,
                    "mama": mama,
                    "fama": fama,
                    "kama": kama,
                    "tol": tol,
                    "cond_mk_long": cond_mk_long,
                    "cond_mk_short": cond_mk_short,
                    "cross_long_ok": cross_long_ok,
                    "cross_short_ok": cross_short_ok,
                    "all_bullish": all_bullish,
                    "all_bearish": all_bearish,
                    "buy_signal_raw": buy_signal_raw,
                    "sell_signal_raw": sell_signal_raw,
                    "ichi_long_active": ichi_long_active,
                    "ichi_short_active": ichi_short_active,
                    "five_signal": five_signal,
                    "bullish_signal": bullish_signal,
                    "bearish_signal": bearish_signal,
                    "armed_long_strict": armed_long_strict_state,
                    "armed_short_strict": armed_short_strict_state,
                    "armed_long_grace_ok": armed_long_grace_state,
                    "armed_short_grace_ok": armed_short_grace_state,
                    "pending_long": pending_long_state,
                    "pending_short": pending_short_state,
                    "lock_long_cycle": lock_long_cycle_state,
                    "lock_short_cycle": lock_short_cycle_state,
                    "allow_long": allow_long_state,
                    "allow_short": allow_short_state,
                    "trigger_long": trigger_long_state,
                    "trigger_short": trigger_short_state,
                    "final_long_active": final_long_active_state,
                    "final_short_active": final_short_active_state,
                    "new_long": new_long_close,
                    "new_short": new_short_close,
                    "signal": signal,
                },
                index=data.index,
            )
            debug_df.to_csv(self.params.debug_signals_path)

        return pd.DataFrame(
            {
                "signal": signal,
                "entry_price": entry_price,
                "sl_price": sl_price,
                "tp1_price": tp1_price,
                "tp2_price": tp2_price,
                "tp3_price": tp3_price,
            },
            index=data.index,
        )
