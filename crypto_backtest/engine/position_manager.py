"""Position management for multi-take-profit setups."""

from __future__ import annotations

from dataclasses import dataclass
import pandas as pd


@dataclass(frozen=True)
class PositionLeg:
    size: float
    tp_multiple: float


class MultiTPPositionManager:
    """Manages 3-leg trades with trailing stop updates."""

    def __init__(self, legs: list[PositionLeg]) -> None:
        self.legs = legs

    def simulate(self, signals: pd.DataFrame, data: pd.DataFrame) -> pd.DataFrame:
        """Simulate multi-TP trade management and return trades."""
        raise NotImplementedError("MultiTPPositionManager.simulate not implemented yet")
