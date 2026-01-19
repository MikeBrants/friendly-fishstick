"""Ichimoku indicator implementation."""

from __future__ import annotations

from dataclasses import dataclass
import pandas as pd


def donchian(high: pd.Series, low: pd.Series, length: int) -> pd.Series:
    """Compute the Donchian midpoint."""
    highest = high.rolling(length).max()
    lowest = low.rolling(length).min()
    return (highest + lowest) / 2.0


@dataclass(frozen=True)
class IchimokuConfig:
    tenkan: int = 9
    kijun: int = 26
    displacement: int = 52


class Ichimoku:
    def __init__(self, config: IchimokuConfig | None = None) -> None:
        self.config = config or IchimokuConfig()
        self._last_result: pd.DataFrame | None = None

    def compute(self, data: pd.DataFrame) -> pd.DataFrame:
        """Return Tenkan, Kijun, KumoA, KumoB series."""
        missing = {"high", "low"}.difference(data.columns)
        if missing:
            raise ValueError(f"Missing columns for Ichimoku: {sorted(missing)}")

        tenkan = donchian(data["high"], data["low"], self.config.tenkan)
        kijun = donchian(data["high"], data["low"], self.config.kijun)
        kumo_a = (tenkan + kijun) / 2.0
        kumo_b = donchian(data["high"], data["low"], self.config.displacement)

        result = pd.DataFrame(
            {
                "tenkan": tenkan,
                "kijun": kijun,
                "kumo_a": kumo_a,
                "kumo_b": kumo_b,
            },
            index=data.index,
        )
        self._last_result = result
        return result

    def all_bullish(self, close: pd.Series) -> pd.Series:
        """Return bullish condition mask (full condition set)."""
        if self._last_result is None:
            raise ValueError("Ichimoku.compute must be called before all_bullish.")

        lines = self._last_result.reindex(close.index)
        tenkan = lines["tenkan"]
        kijun = lines["kijun"]
        kumo_a = lines["kumo_a"]
        kumo_b = lines["kumo_b"]

        cond1 = (
            (close > tenkan)
            & (close > kijun)
            & (close > kumo_a.shift(25))
            & (close > kumo_b.shift(25))
        )
        cond2 = (
            (close > kumo_a.shift(50))
            & (close > kumo_b.shift(50))
            & (close > kijun.shift(25))
            & (close > tenkan.shift(25))
        )
        cond3 = (
            (kumo_a > kumo_b)
            & (kumo_a > kumo_a.shift(1))
            & (kumo_b > kumo_b.shift(1))
        )
        cond4 = (kijun > kijun.shift(1)) & (tenkan > tenkan.shift(1))
        return cond1 & cond2 & cond3 & cond4

    def all_bearish(self, close: pd.Series) -> pd.Series:
        """Return bearish condition mask (full condition set)."""
        if self._last_result is None:
            raise ValueError("Ichimoku.compute must be called before all_bearish.")

        lines = self._last_result.reindex(close.index)
        kumo_a = lines["kumo_a"]
        kumo_b = lines["kumo_b"]
        return (
            (close < kumo_a.shift(25))
            & (close < kumo_b.shift(25))
            & (close < kumo_b)
        )
