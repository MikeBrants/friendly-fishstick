"""Ichimoku indicator implementation."""

from __future__ import annotations

from dataclasses import dataclass
import pandas as pd


def donchian(high: pd.Series, low: pd.Series, length: int) -> pd.Series:
    """Compute the Donchian midpoint."""
    raise NotImplementedError("donchian not implemented yet")


@dataclass(frozen=True)
class IchimokuConfig:
    tenkan: int = 9
    kijun: int = 26
    displacement: int = 52


class Ichimoku:
    def __init__(self, config: IchimokuConfig | None = None) -> None:
        self.config = config or IchimokuConfig()

    def compute(self, data: pd.DataFrame) -> pd.DataFrame:
        """Return Tenkan, Kijun, KumoA, KumoB series."""
        raise NotImplementedError("Ichimoku.compute not implemented yet")

    def all_bullish(self, close: pd.Series) -> pd.Series:
        """Return bullish condition mask (full condition set)."""
        raise NotImplementedError("Ichimoku.all_bullish not implemented yet")

    def all_bearish(self, close: pd.Series) -> pd.Series:
        """Return bearish condition mask (full condition set)."""
        raise NotImplementedError("Ichimoku.all_bearish not implemented yet")
