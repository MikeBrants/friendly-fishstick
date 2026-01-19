"""FINAL TRIGGER v2 strategy implementation."""

from __future__ import annotations

from dataclasses import dataclass
import pandas as pd

from .base import BaseStrategy


@dataclass(frozen=True)
class FinalTriggerParams:
    grace_bars: int = 1


class FinalTriggerStrategy(BaseStrategy):
    """Strategy using Ichimoku + MAMA/KAMA + Five-in-One filters."""

    def __init__(self, params: FinalTriggerParams) -> None:
        self.params = params

    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """Return signal, entry, SL and TP levels for each bar."""
        raise NotImplementedError("FinalTriggerStrategy.generate_signals not implemented yet")
