"""Performance metrics computation."""

from __future__ import annotations

import pandas as pd


def compute_metrics(equity_curve: pd.Series, trades: pd.DataFrame) -> dict[str, float]:
    """Compute performance metrics from equity and trades."""
    raise NotImplementedError("compute_metrics not implemented yet")
