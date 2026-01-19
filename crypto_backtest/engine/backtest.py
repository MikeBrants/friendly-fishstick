"""Vectorized backtest engine."""

from __future__ import annotations

from dataclasses import dataclass
import pandas as pd

from crypto_backtest.strategies.base import BaseStrategy
from crypto_backtest.engine.execution import apply_fees_and_slippage
from crypto_backtest.engine.position_manager import MultiTPPositionManager, PositionLeg


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
        if data.empty:
            return BacktestResult(equity_curve=pd.Series(dtype=float), trades=pd.DataFrame())

        signals = strategy.generate_signals(data)
        position_manager = MultiTPPositionManager(
            [
                PositionLeg(size=0.5, tp_multiple=2.0),
                PositionLeg(size=0.3, tp_multiple=6.0),
                PositionLeg(size=0.2, tp_multiple=10.0),
            ]
        )
        trades = position_manager.simulate(signals, data, self.config.initial_capital)
        if trades.empty:
            equity_curve = pd.Series(self.config.initial_capital, index=data.index)
            return BacktestResult(equity_curve=equity_curve, trades=trades)

        trades["pnl"] = apply_fees_and_slippage(
            trades["gross_pnl"],
            trades["notional"],
            self.config.fees_bps,
            self.config.slippage_bps,
        )

        pnl_by_time = trades.groupby("exit_time")["pnl"].sum()
        pnl_series = pnl_by_time.reindex(data.index, fill_value=0.0)
        equity_curve = self.config.initial_capital + pnl_series.cumsum()

        return BacktestResult(equity_curve=equity_curve, trades=trades)
