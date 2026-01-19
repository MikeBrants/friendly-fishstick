"""
Signal generation with state machine and lock system.
"""

from __future__ import annotations

import numpy as np
from numba import njit


@njit
def generate_signals_state_mode(is_bullish: np.ndarray, is_bearish: np.ndarray) -> tuple:
    """
    Generate LONG/SHORT signals using state machine with lock.

    Args:
        is_bullish: array of bool from ichimoku light
        is_bearish: array of bool from ichimoku light

    Returns:
        signals: array of int (1=LONG, -1=SHORT, 0=NONE)
        states: array of int (1=BULL, -1=BEAR, 0=NEUTRAL)
    """
    n = len(is_bullish)
    signals = np.zeros(n, dtype=np.int64)
    states = np.zeros(n, dtype=np.int64)

    ichistate = 0
    long_locked = False
    short_locked = False

    for i in range(n):
        prev_state = ichistate

        if is_bearish[i]:
            ichistate = -1
        elif is_bullish[i]:
            ichistate = 1

        states[i] = ichistate

        if ichistate == 1 and prev_state != 1 and not long_locked:
            signals[i] = 1
            long_locked = True
            short_locked = False

        if ichistate == -1 and prev_state != -1 and not short_locked:
            signals[i] = -1
            short_locked = True
            long_locked = False

    return signals, states
