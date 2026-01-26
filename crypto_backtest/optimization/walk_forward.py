"""Walk-forward analysis utilities."""

from __future__ import annotations

from dataclasses import dataclass
import pandas as pd

from crypto_backtest.analysis.metrics import compute_metrics
from crypto_backtest.engine.backtest import BacktestConfig, VectorizedBacktester
from crypto_backtest.optimization.bayesian import BayesianOptimizer, _apply_overrides


@dataclass(frozen=True)
class WalkForwardConfig:
    in_sample_days: int = 180
    out_of_sample_days: int = 30
    n_trials: int = 50


@dataclass(frozen=True)
class WalkForwardResult:
    combined_metrics: dict[str, float]
    return_efficiency: float  # RENAMED from efficiency_ratio - measures return degradation
    wfe_pardo: float  # RENAMED from degradation_ratio - TRUE WFE using Sharpe ratios
    degradation_pct: float  # Display-friendly degradation percentage


class WalkForwardAnalyzer:
    def __init__(self, config: WalkForwardConfig) -> None:
        self.config = config
        self.optimizer = BayesianOptimizer()

    def analyze(self, data: pd.DataFrame, strategy_class, param_space) -> WalkForwardResult:
        """Run walk-forward optimization and return combined results."""
        if data.empty:
            return WalkForwardResult(
                combined_metrics={},
                return_efficiency=0.0,
                wfe_pardo=0.0,
                degradation_pct=0.0,
            )

        base_params = param_space.get("base_params")
        search_space = param_space.get("search_space")
        if base_params is None or search_space is None:
            raise ValueError("param_space must include 'base_params' and 'search_space'")

        backtest_config = param_space.get("backtest_config") or BacktestConfig()
        objective_name = param_space.get("objective", "sharpe_ratio")
        direction = param_space.get("direction", "maximize")

        in_sample = pd.Timedelta(days=self.config.in_sample_days)
        out_sample = pd.Timedelta(days=self.config.out_of_sample_days)

        start = data.index.min()
        end = data.index.max()
        if not isinstance(start, pd.Timestamp):
            raise ValueError("data must use a DatetimeIndex for walk-forward analysis")

        oos_equity_curves = []
        oos_trades = []
        is_scores = []
        oos_scores = []
        is_returns = []
        oos_returns = []

        window_start = start
        while window_start + in_sample + out_sample <= end:
            train_end = window_start + in_sample
            test_end = train_end + out_sample

            train = data[(data.index >= window_start) & (data.index < train_end)]
            test = data[(data.index >= train_end) & (data.index < test_end)]
            if len(train) < 2 or len(test) < 2:
                break

            opt_space = {
                "base_params": base_params,
                "search_space": search_space,
                "objective": objective_name,
                "direction": direction,
                "backtest_config": backtest_config,
            }
            opt_result = self.optimizer.optimize(
                train, strategy_class, opt_space, n_trials=self.config.n_trials
            )
            best_params = _apply_overrides(base_params, opt_result.best_params)

            backtester = VectorizedBacktester(backtest_config)

            strategy_is = strategy_class(best_params)
            result_is = backtester.run(train, strategy_is)
            metrics_is = compute_metrics(result_is.equity_curve, result_is.trades)
            is_score = metrics_is.get(objective_name, 0.0)
            is_return = metrics_is.get("total_return", 0.0)

            strategy_oos = strategy_class(best_params)
            result_oos = backtester.run(test, strategy_oos)
            metrics_oos = compute_metrics(result_oos.equity_curve, result_oos.trades)
            oos_score = metrics_oos.get(objective_name, 0.0)
            oos_return = metrics_oos.get("total_return", 0.0)

            is_scores.append(is_score)
            oos_scores.append(oos_score)
            is_returns.append(is_return)
            oos_returns.append(oos_return)

            oos_equity_curves.append(result_oos.equity_curve)
            oos_trades.append(result_oos.trades)

            window_start = test_end

        if not oos_equity_curves:
            return WalkForwardResult(
                combined_metrics={},
                return_efficiency=0.0,
                wfe_pardo=0.0,
                degradation_pct=0.0,
            )

        combined_equity = _stitch_equity(oos_equity_curves, backtest_config.initial_capital)
        combined_trades = pd.concat(oos_trades, ignore_index=True)
        combined_metrics = compute_metrics(combined_equity, combined_trades)

        mean_is_score = _mean_safe(is_scores)
        mean_oos_score = _mean_safe(oos_scores)
        wfe_pardo = _ratio(mean_oos_score, mean_is_score)  # TRUE WFE using Sharpe ratios

        mean_is_return = _mean_safe(is_returns)
        mean_oos_return = _mean_safe(oos_returns)
        return_efficiency = _ratio(mean_oos_return, mean_is_return)  # Return ratio (NOT WFE)

        # Calculate display-friendly degradation percentage
        degradation_pct = (1 - wfe_pardo) * 100.0 if wfe_pardo < 1 else 0.0

        return WalkForwardResult(
            combined_metrics=combined_metrics,
            return_efficiency=return_efficiency,
            wfe_pardo=wfe_pardo,
            degradation_pct=degradation_pct,
        )


def _stitch_equity(curves: list[pd.Series], initial_capital: float) -> pd.Series:
    equity = initial_capital
    stitched = []
    for curve in curves:
        if curve.empty:
            continue
        offset = equity - curve.iloc[0]
        adjusted = curve + offset
        equity = float(adjusted.iloc[-1])
        stitched.append(adjusted)
    return pd.concat(stitched)


def _mean_safe(values: list[float]) -> float:
    if not values:
        return 0.0
    return float(sum(values) / len(values))


def _ratio(numerator: float, denominator: float) -> float:
    if denominator == 0:
        return 0.0
    return float(numerator / denominator)
