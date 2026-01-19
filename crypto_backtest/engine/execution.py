"""Execution simulation for fees and slippage."""

from __future__ import annotations

import pandas as pd


def apply_fees_and_slippage(
    pnl: pd.Series,
    notional: pd.Series,
    fees_bps: float,
    slippage_bps: float,
) -> pd.Series:
    """Apply transaction costs to a PnL series."""
    if pnl.empty:
        return pnl
    cost_rate = (fees_bps + slippage_bps) / 10_000.0
    costs = notional * cost_rate * 2.0
    return pnl - costs
