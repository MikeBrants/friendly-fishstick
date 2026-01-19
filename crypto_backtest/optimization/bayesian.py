"""Bayesian optimization with Optuna."""

from __future__ import annotations

from dataclasses import dataclass, is_dataclass, replace
from typing import Any

import numpy as np

from crypto_backtest.analysis.metrics import compute_metrics
from crypto_backtest.engine.backtest import BacktestConfig, VectorizedBacktester


@dataclass(frozen=True)
class OptimizationResult:
    best_params: dict[str, float]
    best_score: float


class BayesianOptimizer:
    """Optuna-based TPE optimizer."""

    def optimize(self, data, strategy_class, param_space, n_trials: int = 100) -> OptimizationResult:
        """Run optimization and return the best parameters."""
        import optuna

        search_space = param_space.get("search_space")
        if search_space is None:
            raise ValueError("param_space must include 'search_space'")

        base_params = param_space.get("base_params")
        if base_params is None:
            raise ValueError("param_space must include 'base_params'")

        objective_name = param_space.get("objective", "sharpe_ratio")
        direction = param_space.get("direction", "maximize")
        backtest_config = param_space.get("backtest_config") or BacktestConfig()

        def objective(trial: optuna.Trial) -> float:
            overrides = _suggest_params(trial, search_space)
            params = _apply_overrides(base_params, overrides)
            strategy = _instantiate_strategy(strategy_class, params)
            backtester = VectorizedBacktester(backtest_config)
            result = backtester.run(data, strategy)
            metrics = compute_metrics(result.equity_curve, result.trades)
            score = metrics.get(objective_name, float("-inf"))
            if score is None or np.isnan(score):
                return float("-inf")
            return float(score)

        study = optuna.create_study(direction=direction)
        study.optimize(objective, n_trials=n_trials)

        best_params = study.best_params
        return OptimizationResult(best_params=best_params, best_score=float(study.best_value))


def _instantiate_strategy(strategy_class, params: Any):
    if params is None:
        return strategy_class()
    if isinstance(params, dict):
        try:
            return strategy_class(**params)
        except TypeError:
            return strategy_class(params)
    return strategy_class(params)


def _suggest_params(trial, search_space: dict[str, Any]) -> dict[str, Any]:
    overrides: dict[str, Any] = {}
    for name, spec in search_space.items():
        if isinstance(spec, dict):
            param_type = spec.get("type", "float")
            if param_type == "int":
                overrides[name] = trial.suggest_int(
                    name, spec["low"], spec["high"], step=spec.get("step", 1)
                )
            elif param_type == "categorical":
                overrides[name] = trial.suggest_categorical(name, spec["choices"])
            else:
                overrides[name] = trial.suggest_float(
                    name, spec["low"], spec["high"], step=spec.get("step")
                )
        elif isinstance(spec, (list, tuple)) and len(spec) == 2:
            overrides[name] = trial.suggest_float(name, spec[0], spec[1])
        elif isinstance(spec, (list, tuple)):
            overrides[name] = trial.suggest_categorical(name, list(spec))
        else:
            raise ValueError(f"Unsupported search space spec for {name}: {spec}")
    return overrides


def _apply_overrides(params: Any, overrides: dict[str, Any]) -> Any:
    if not is_dataclass(params):
        if isinstance(params, dict):
            updated = dict(params)
            for key, value in overrides.items():
                if "." in key:
                    root, sub = key.split(".", 1)
                    nested = dict(updated.get(root, {}))
                    nested[sub] = value
                    updated[root] = nested
                else:
                    updated[key] = value
            return updated
        raise ValueError("base_params must be a dataclass or dict")

    updated = params
    for key, value in overrides.items():
        if "." in key:
            root, sub = key.split(".", 1)
            nested = getattr(updated, root)
            if is_dataclass(nested):
                nested = replace(nested, **{sub: value})
            elif isinstance(nested, dict):
                nested = {**nested, sub: value}
            else:
                raise ValueError(f"Unsupported nested param for {root}")
            updated = replace(updated, **{root: nested})
        else:
            updated = replace(updated, **{key: value})
    return updated
