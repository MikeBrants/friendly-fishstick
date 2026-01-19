"""Vectorized backtest engine."""

from __future__ import annotations

from dataclasses import dataclass
import pandas as pd

from crypto_backtest.strategies.base import BaseStrategy


@dataclass(frozen=True)
class BacktestConfig:
    fees_bps: float = 5.0
    slippage_bps: float = 2.0
    initial_capital: float = 10_000.0


@dataclass(frozen=True)
class BacktestResult:
    equity_curve: pd.Series
    trades: pd.DataFrame


class VectorizedBacktester:
    def __init__(self, config: BacktestConfig) -> None:
        self.config = config

    def run(self, data: pd.DataFrame, strategy: BaseStrategy) -> BacktestResult:
        """Run a vectorized backtest and return results."""
        raise NotImplementedError("VectorizedBacktester.run not implemented yet")
