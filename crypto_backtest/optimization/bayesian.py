"""Bayesian optimization with Optuna."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class OptimizationResult:
    best_params: dict[str, float]
    best_score: float


class BayesianOptimizer:
    """Optuna-based TPE optimizer."""

    def optimize(self, data, strategy_class, param_space, n_trials: int = 100) -> OptimizationResult:
        """Run optimization and return the best parameters."""
        raise NotImplementedError("BayesianOptimizer.optimize not implemented yet")
