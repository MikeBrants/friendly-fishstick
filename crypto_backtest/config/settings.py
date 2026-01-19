"""Global settings and defaults for the backtest system."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class BacktestSettings:
    fees_bps: float = 5.0
    slippage_bps: float = 2.0
    initial_capital: float = 10_000.0


@dataclass(frozen=True)
class DataSettings:
    default_exchange: str = "binance"
    default_timeframe: str = "1h"
    cache_dir: str = "./data/cache"
