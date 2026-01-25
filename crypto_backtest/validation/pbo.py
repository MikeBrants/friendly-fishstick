"""
Probability of Backtest Overfitting (PBO)

Implements Bailey & López de Prado (2014) methodology for detecting
overfitting in backtested trading strategies.

References:
- Bailey, D. H., & López de Prado, M. (2014) "The Probability of Backtest Overfitting"
- López de Prado, M. (2018) "Advances in Financial Machine Learning" Chapter 11

PBO measures the probability that the best in-sample strategy will
underperform out-of-sample. PBO > 0.5 indicates likely overfitting.
"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
from typing import List, Tuple

import numpy as np
from scipy.special import comb


@dataclass(frozen=True)
class PBOResult:
    """Result of PBO calculation."""
    pbo: float  # Probability of Backtest Overfitting [0, 1]
    logits: List[float]  # Distribution of relative ranks
    n_combinations: int  # Number of IS/OOS combinations tested
    threshold: float  # Threshold used for pass/fail
    passed: bool  # True if PBO < threshold


def probability_of_backtest_overfitting(
    returns_matrix: np.ndarray,
    n_splits: int = 16,
    threshold: float = 0.30,
) -> PBOResult:
    """
    Calculate Probability of Backtest Overfitting using CSCV.

    Combinatorially Symmetric Cross-Validation (CSCV) methodology:
    1. Split time series into n_splits blocks
    2. Enumerate all C(n_splits, n_splits/2) train/test combinations
    3. For each combination:
       - Identify best strategy on IS (training)
       - Record OOS (test) rank of that strategy
    4. PBO = proportion where OOS rank is below median

    Args:
        returns_matrix: Shape (n_trials, n_periods) - returns for each trial
        n_splits: Number of time splits (must be even, default 16)
        threshold: Maximum acceptable PBO (default 0.30)

    Returns:
        PBOResult with pbo value, logits distribution, and pass/fail

    Interpretation:
        PBO < 0.15: LOW RISK - Parameters likely robust
        PBO 0.15-0.30: MODERATE RISK - Some overfitting possible
        PBO > 0.30: HIGH RISK - Best IS params likely overfit

    Example:
        >>> returns = np.random.randn(100, 1000)  # 100 trials, 1000 periods
        >>> result = probability_of_backtest_overfitting(returns)
        >>> print(f"PBO: {result.pbo:.2%}, Pass: {result.passed}")
    """
    if n_splits % 2 != 0:
        raise ValueError("n_splits must be even")

    n_trials, n_periods = returns_matrix.shape
    split_size = n_periods // n_splits

    if split_size < 2:
        raise ValueError(f"Not enough periods ({n_periods}) for {n_splits} splits")

    # Generate all combinations of n_splits/2 for IS
    all_splits = list(range(n_splits))
    is_combinations = list(combinations(all_splits, n_splits // 2))

    underperformance_count = 0
    logits: List[float] = []

    for is_splits in is_combinations:
        oos_splits = tuple(s for s in all_splits if s not in is_splits)

        # Build IS and OOS indices
        is_indices = _get_split_indices(is_splits, split_size)
        oos_indices = _get_split_indices(oos_splits, split_size)

        # Compute Sharpe for each trial on IS and OOS
        is_sharpes = _compute_sharpes(returns_matrix, is_indices)
        oos_sharpes = _compute_sharpes(returns_matrix, oos_indices)

        # Find best trial on IS
        best_is_idx = int(np.argmax(is_sharpes))

        # Rank of best_is trial on OOS (0 = best, n_trials-1 = worst)
        oos_ranks = np.argsort(np.argsort(-oos_sharpes))
        best_is_oos_rank = oos_ranks[best_is_idx]

        # Relative rank (0 = best, 1 = worst)
        relative_rank = best_is_oos_rank / (n_trials - 1) if n_trials > 1 else 0.5
        logits.append(float(relative_rank))

        # Count if best IS underperforms median on OOS
        if relative_rank > 0.5:
            underperformance_count += 1

    pbo = underperformance_count / len(is_combinations) if is_combinations else 0.0

    return PBOResult(
        pbo=pbo,
        logits=logits,
        n_combinations=len(is_combinations),
        threshold=threshold,
        passed=pbo < threshold,
    )


def _get_split_indices(splits: tuple, split_size: int) -> np.ndarray:
    """Get array indices for given splits."""
    indices = []
    for s in splits:
        start = s * split_size
        end = (s + 1) * split_size
        indices.extend(range(start, end))
    return np.array(indices)


def _compute_sharpes(returns_matrix: np.ndarray, indices: np.ndarray) -> np.ndarray:
    """Compute Sharpe ratios for all trials on given indices."""
    subset = returns_matrix[:, indices]
    means = np.mean(subset, axis=1)
    stds = np.std(subset, axis=1) + 1e-10  # Avoid division by zero
    return means / stds


def guard_pbo(
    returns_matrix: np.ndarray,
    threshold: float = 0.30,
    n_splits: int = 16,
) -> dict:
    """
    Guard function for PBO validation in pipeline.

    Args:
        returns_matrix: (n_trials, n_periods) array of returns
        threshold: Max acceptable PBO (default 0.30)
        n_splits: Number of CV splits (must be even)

    Returns:
        dict with guard results compatible with validation pipeline
    """
    result = probability_of_backtest_overfitting(
        returns_matrix,
        n_splits=n_splits,
        threshold=threshold,
    )

    return {
        "guard": "pbo",
        "pass": result.passed,
        "pbo": round(result.pbo, 4),
        "threshold": threshold,
        "interpretation": _interpret_pbo(result.pbo),
        "n_combinations": result.n_combinations,
    }


def _interpret_pbo(pbo: float) -> str:
    """Return human-readable interpretation of PBO value."""
    if pbo < 0.15:
        return "LOW RISK - Parameters likely robust"
    elif pbo < 0.30:
        return "MODERATE RISK - Some overfitting possible"
    elif pbo < 0.50:
        return "HIGH RISK - Significant overfitting detected"
    else:
        return "CRITICAL - Best IS params almost certainly overfit"
