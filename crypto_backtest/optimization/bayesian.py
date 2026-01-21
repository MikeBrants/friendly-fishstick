"""Bayesian optimization with Optuna."""

from __future__ import annotations

from dataclasses import dataclass, is_dataclass, replace
from typing import Any

import numpy as np

MIN_TP_GAP = 0.5

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
        # Convert nested dicts to dataclasses if strategy expects a params dataclass
        params_obj = _dict_to_params(strategy_class, params)
        return strategy_class(params_obj)
    return strategy_class(params)


def _dict_to_params(strategy_class, params_dict: dict) -> Any:
    """Convert a nested dict to the appropriate params dataclass."""
    import inspect
    from crypto_backtest.strategies.final_trigger import FinalTriggerParams
    from crypto_backtest.indicators.ichimoku import IchimokuConfig
    from crypto_backtest.indicators.five_in_one import FiveInOneConfig

    # Check if strategy expects FinalTriggerParams
    sig = inspect.signature(strategy_class.__init__)
    param_names = list(sig.parameters.keys())
    if len(param_names) >= 2:  # self + params
        first_param = param_names[1]
        annotation = sig.parameters[first_param].annotation
        if annotation is FinalTriggerParams or str(annotation) == 'FinalTriggerParams':
            # Convert nested dicts
            d = dict(params_dict)
            if 'ichimoku' in d and isinstance(d['ichimoku'], dict):
                d['ichimoku'] = IchimokuConfig(**d['ichimoku'])
            if 'five_in_one' in d and isinstance(d['five_in_one'], dict):
                d['five_in_one'] = FiveInOneConfig(**d['five_in_one'])
            return FinalTriggerParams(**d)

    # Fallback: try to instantiate directly
    return params_dict


def _suggest_params(trial, search_space: dict[str, Any]) -> dict[str, Any]:
    overrides: dict[str, Any] = {}

    tp_keys = {"tp1_mult", "tp2_mult", "tp3_mult"}
    if tp_keys.issubset(search_space.keys()):
        import optuna

        tp1_spec = search_space["tp1_mult"]
        tp2_spec = search_space["tp2_mult"]
        tp3_spec = search_space["tp3_mult"]

        if isinstance(tp1_spec, dict) and isinstance(tp2_spec, dict) and isinstance(tp3_spec, dict):
            if tp1_spec.get("type", "float") == "float":
                tp1_low = tp1_spec["low"]
                tp1_high = tp1_spec["high"]
                tp1_step = tp1_spec.get("step")
                tp2_low = tp2_spec["low"]
                tp2_high = tp2_spec["high"]
                tp2_step = tp2_spec.get("step")
                tp3_low = tp3_spec["low"]
                tp3_high = tp3_spec["high"]
                tp3_step = tp3_spec.get("step")

                max_tp1 = min(tp1_high, tp2_high - MIN_TP_GAP, tp3_high - 2 * MIN_TP_GAP)
                if max_tp1 < tp1_low:
                    raise optuna.TrialPruned()

                tp1 = trial.suggest_float("tp1_mult", tp1_low, max_tp1, step=tp1_step)

                tp2_low_eff = max(tp2_low, tp1 + MIN_TP_GAP)
                tp2_high_eff = min(tp2_high, tp3_high - MIN_TP_GAP)
                if tp2_high_eff < tp2_low_eff:
                    raise optuna.TrialPruned()
                tp2 = trial.suggest_float("tp2_mult", tp2_low_eff, tp2_high_eff, step=tp2_step)

                tp3_low_eff = max(tp3_low, tp2 + MIN_TP_GAP)
                tp3_high_eff = tp3_high
                if tp3_high_eff < tp3_low_eff:
                    raise optuna.TrialPruned()
                tp3 = trial.suggest_float("tp3_mult", tp3_low_eff, tp3_high_eff, step=tp3_step)

                overrides["tp1_mult"] = tp1
                overrides["tp2_mult"] = tp2
                overrides["tp3_mult"] = tp3
    for name, spec in search_space.items():
        if name in overrides:
            continue
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
