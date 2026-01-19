"""Base classes for indicators."""

from __future__ import annotations

from abc import ABC, abstractmethod
import pandas as pd


class Indicator(ABC):
    """Abstract indicator interface."""

    @abstractmethod
    def compute(self, data: pd.DataFrame) -> pd.DataFrame:
        """Compute indicator columns from the input data."""
        raise NotImplementedError
