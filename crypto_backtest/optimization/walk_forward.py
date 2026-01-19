"""Walk-forward analysis utilities."""

from __future__ import annotations

from dataclasses import dataclass
import pandas as pd


@dataclass(frozen=True)
class WalkForwardConfig:
    in_sample_days: int = 180
    out_of_sample_days: int = 30


@dataclass(frozen=True)
class WalkForwardResult:
    combined_metrics: dict[str, float]
    efficiency_ratio: float
    degradation_ratio: float


class WalkForwardAnalyzer:
    def __init__(self, config: WalkForwardConfig) -> None:
        self.config = config

    def analyze(self, data: pd.DataFrame, strategy_class, param_space) -> WalkForwardResult:
        """Run walk-forward optimization and return combined results."""
        raise NotImplementedError("WalkForwardAnalyzer.analyze not implemented yet")
