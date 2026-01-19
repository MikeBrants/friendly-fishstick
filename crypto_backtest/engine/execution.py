"""Execution simulation for fees and slippage."""

from __future__ import annotations

import pandas as pd


def apply_fees_and_slippage(pnl: pd.Series, fees_bps: float, slippage_bps: float) -> pd.Series:
    """Apply transaction costs to a PnL series."""
    raise NotImplementedError("apply_fees_and_slippage not implemented yet")
