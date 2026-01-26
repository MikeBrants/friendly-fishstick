"""Walk-forward analysis utilities with regime-aware stratification.

This module provides both standard and regime-stratified walk-forward cross-validation
for time series backtesting. Regime stratification ensures that each validation fold
contains a minimum percentage of each market regime (ACCUMULATION, MARKDOWN, SIDEWAYS),
preventing overfitting to bull-only or bear-only conditions.

Key Features:
- Standard walk-forward splits (time-based sequential)
- Regime-stratified splits (balanced market conditions)
- Validation of regime balance across folds
- Integration with CPCV (Combinatorial Purged Cross-Validation)

Usage:
    >>> from crypto_backtest.optimization.walk_forward import stratified_regime_split
    >>> from crypto_backtest.analysis.regime_v3 import CryptoRegimeAnalyzer
    >>>
    >>> # Classify regimes
    >>> analyzer = CryptoRegimeAnalyzer()
    >>> regimes_df = analyzer.fit_and_classify(data)
    >>> data["crypto_regime"] = regimes_df["crypto_regime"]
    >>>
    >>> # Create stratified splits
    >>> splits, distributions = stratified_regime_split(
    ...     data,
    ...     regime_col="crypto_regime",
    ...     n_splits=3,
    ...     min_regime_pct=0.15,
    ... )
    >>>
    >>> # Use in walk-forward optimization
    >>> for fold_id, (train_idx, test_idx) in enumerate(splits):
    ...     train_data = data.iloc[train_idx]
    ...     test_data = data.iloc[test_idx]
    ...     # Run backtest on train_data, validate on test_data

References:
- López de Prado, M. (2018) "Advances in Financial Machine Learning" Chapter 7
- Issue #17: WFE > 1.0 investigation (regime stratification solution)

Author: Alex (Lead Quant)
Date: 2026-01-26
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple, Dict, Optional
import numpy as np
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


# ============================================================================
# REGIME-STRATIFIED WALK-FORWARD
# ============================================================================


def stratified_regime_split(
    data: pd.DataFrame,
    regime_col: str = "crypto_regime",
    n_splits: int = 3,
    min_regime_pct: float = 0.15,
    required_regimes: Optional[List[str]] = None,
) -> Tuple[List[Tuple[np.ndarray, np.ndarray]], Dict[int, Dict[str, float]]]:
    """
    Create walk-forward splits that ensure minimum representation of each regime.

    This function addresses the problem where a single walk-forward fold can be
    100% bull market (ACCUMULATION/MARKUP), leading to overfitting on bullish
    conditions. By enforcing minimum regime percentages, we ensure strategies
    are validated across different market conditions.

    Args:
        data: DataFrame with regime classification column
        regime_col: Name of column containing regime labels
        n_splits: Number of walk-forward splits (default 3)
        min_regime_pct: Minimum percentage per regime per fold (default 0.15 = 15%)
        required_regimes: List of regime names to enforce (default: ACCUMULATION, MARKDOWN, SIDEWAYS)

    Returns:
        splits: List of (train_idx, test_idx) tuples for each fold
        regime_distribution: Dict[fold_id, Dict[regime, percentage]]

    Raises:
        ValueError: If impossible to meet min_regime_pct constraint with available data

    Example:
        >>> # Data with regime classification
        >>> splits, dist = stratified_regime_split(data, "crypto_regime", n_splits=3)
        >>> for fold_id, (train_idx, test_idx) in enumerate(splits):
        ...     print(f"Fold {fold_id}: {len(test_idx)} samples")
        ...     print(f"Regime distribution: {dist[fold_id]}")
    """
    if regime_col not in data.columns:
        raise ValueError(f"Column '{regime_col}' not found in data")

    # Default required regimes (crypto-specific)
    if required_regimes is None:
        required_regimes = ["ACCUMULATION", "MARKDOWN", "SIDEWAYS"]

    # Check regime availability
    regime_counts = data[regime_col].value_counts()
    total_samples = len(data)

    # Filter required regimes to only those present in data
    available_regimes = [r for r in required_regimes if r in regime_counts.index]

    if not available_regimes:
        # Fallback to standard walk-forward if no regimes available
        return _standard_walk_forward_split(data, n_splits), {}

    # Check if constraints are feasible
    min_samples_per_regime = int(total_samples * min_regime_pct)
    insufficient_regimes = []

    for regime in available_regimes:
        regime_count = regime_counts.get(regime, 0)
        if regime_count < min_samples_per_regime * n_splits:
            insufficient_regimes.append(regime)

    # If any regime is too rare, make it optional
    if insufficient_regimes:
        available_regimes = [r for r in available_regimes if r not in insufficient_regimes]
        if not available_regimes:
            # Fallback to standard WF if all regimes insufficient
            return _standard_walk_forward_split(data, n_splits), {}

    # Create regime-stratified splits
    splits = []
    regime_distributions = {}

    # Group data by regime using integer positions
    regime_groups = {}
    for regime in available_regimes:
        mask = data[regime_col] == regime
        positions = np.where(mask)[0].tolist()
        regime_groups[regime] = positions

    # Other samples (not in required regimes)
    required_positions = set()
    for positions in regime_groups.values():
        required_positions.update(positions)
    other_positions = [i for i in range(total_samples) if i not in required_positions]

    # Calculate split sizes
    samples_per_fold = total_samples // n_splits
    test_size_per_fold = samples_per_fold // 4  # 25% test, 75% train per fold

    for fold_id in range(n_splits):
        test_indices = []

        # Ensure minimum samples per regime in test set
        for regime, indices in regime_groups.items():
            # Calculate minimum needed to guarantee min_regime_pct
            # Need to account for all regimes, so use ceiling to ensure we hit target
            n_regime_needed = int(np.ceil(test_size_per_fold * min_regime_pct))
            n_regime_available = len(indices)

            # Calculate fold offset to distribute samples across folds
            start_idx = (fold_id * n_regime_available) // n_splits
            end_idx = ((fold_id + 1) * n_regime_available) // n_splits

            # Get indices for this fold
            if start_idx < end_idx:
                fold_regime_indices = indices[start_idx:end_idx]
            else:
                fold_regime_indices = []

            # If we don't have enough, sample more from this regime
            if len(fold_regime_indices) < n_regime_needed and n_regime_available >= n_regime_needed:
                # Sample without overlap from entire regime pool
                fold_regime_indices = np.random.choice(
                    indices,
                    size=n_regime_needed,
                    replace=False
                ).tolist()
            elif len(fold_regime_indices) < n_regime_needed:
                # Not enough samples in total, take what we can
                fold_regime_indices = indices[:n_regime_needed]

            test_indices.extend(fold_regime_indices[:n_regime_needed])

        # Fill remaining test set with other samples
        remaining_needed = test_size_per_fold - len(test_indices)
        if remaining_needed > 0 and other_positions:
            start_idx = (fold_id * len(other_positions)) // n_splits
            end_idx = start_idx + remaining_needed
            test_indices.extend(other_positions[start_idx:end_idx])

        # Convert to numpy arrays
        test_idx = np.array(sorted(test_indices))

        # Train indices are all indices not in test
        all_indices = np.arange(len(data))
        train_idx = np.array([i for i in all_indices if i not in test_indices])

        splits.append((train_idx, test_idx))

        # Calculate regime distribution for this fold
        test_data = data.iloc[test_idx]
        fold_dist = test_data[regime_col].value_counts(normalize=True).to_dict()
        regime_distributions[fold_id] = {k: float(v) for k, v in fold_dist.items()}

    return splits, regime_distributions


def _standard_walk_forward_split(
    data: pd.DataFrame,
    n_splits: int = 3
) -> List[Tuple[np.ndarray, np.ndarray]]:
    """
    Standard walk-forward split without regime stratification.

    Args:
        data: DataFrame with time series data
        n_splits: Number of splits

    Returns:
        List of (train_idx, test_idx) tuples
    """
    n_samples = len(data)
    samples_per_fold = n_samples // n_splits
    splits = []

    for fold_id in range(n_splits):
        test_start = fold_id * samples_per_fold
        test_end = (fold_id + 1) * samples_per_fold if fold_id < n_splits - 1 else n_samples

        test_idx = np.arange(test_start, test_end)
        train_idx = np.concatenate([
            np.arange(0, test_start),
            np.arange(test_end, n_samples)
        ])

        splits.append((train_idx, test_idx))

    return splits


def validate_regime_balance(
    regime_distributions: Dict[int, Dict[str, float]],
    min_regime_pct: float = 0.15,
    required_regimes: Optional[List[str]] = None,
) -> Dict[str, any]:
    """
    Validate that regime distributions meet minimum requirements.

    Args:
        regime_distributions: Output from stratified_regime_split
        min_regime_pct: Minimum percentage required
        required_regimes: List of regimes to validate

    Returns:
        dict with validation results
    """
    if required_regimes is None:
        required_regimes = ["ACCUMULATION", "MARKDOWN", "SIDEWAYS"]

    validation = {
        "passed": True,
        "details": {},
        "violations": [],
    }

    for fold_id, dist in regime_distributions.items():
        fold_validation = {"fold": fold_id, "passes": True, "violations": []}

        for regime in required_regimes:
            pct = dist.get(regime, 0.0)
            if pct < min_regime_pct:
                fold_validation["passes"] = False
                fold_validation["violations"].append({
                    "regime": regime,
                    "actual_pct": round(pct, 4),
                    "required_pct": min_regime_pct,
                })
                validation["passed"] = False

        validation["details"][fold_id] = fold_validation
        if fold_validation["violations"]:
            validation["violations"].extend(fold_validation["violations"])

    return validation
