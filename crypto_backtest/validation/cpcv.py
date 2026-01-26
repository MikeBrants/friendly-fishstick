"""
Combinatorial Purged Cross-Validation (CPCV)

Implements López de Prado's CPCV methodology for financial time series,
addressing data leakage issues in standard cross-validation.

References:
- López de Prado, M. (2018) "Advances in Financial Machine Learning" Chapter 7
- MLFinLab: https://github.com/hudson-and-thames/mlfinlab

Key features:
- Purging: Remove observations near test set boundaries to prevent leakage
- Embargo: Additional gap after test set before training resumes
- Combinatorial: Generate all C(n_splits, n_test_splits) combinations
"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
from typing import Generator, List, Tuple, Optional

import numpy as np
import pandas as pd
from scipy.special import comb

__all__ = [
    "CombinatorialPurgedKFold",
    "CPCVSplit",
    "CPCVPBOResult",
    "validate_with_cpcv",
    "pbo_with_cpcv",
    "guard_cpcv_pbo",
]


@dataclass(frozen=True)
class CPCVSplit:
    """Single CPCV train/test split."""
    train_indices: np.ndarray
    test_indices: np.ndarray
    split_id: int


class CombinatorialPurgedKFold:
    """
    Combinatorial Purged K-Fold Cross-Validation.

    Implements López de Prado's CPCV methodology:
    - Purging: Remove observations within purge_gap of test set
    - Embargo: Additional gap after test set before training resumes
    - Combinatorial: Generate all C(n_splits, n_test_splits) combinations

    Args:
        n_splits: Total number of time-based splits (default 6)
        n_test_splits: Number of splits to use for testing (default 2)
        purge_gap: Number of observations to purge around test boundaries (default 0)
        embargo_pct: Percentage of data to embargo after test set (default 0.01)

    Example:
        >>> cpcv = CombinatorialPurgedKFold(n_splits=6, n_test_splits=2)
        >>> for train_idx, test_idx in cpcv.split(X):
        ...     model.fit(X[train_idx], y[train_idx])
        ...     score = model.score(X[test_idx], y[test_idx])
    """

    def __init__(
        self,
        n_splits: int = 6,
        n_test_splits: int = 2,
        purge_gap: int = 0,
        embargo_pct: float = 0.01,
    ):
        if n_test_splits >= n_splits:
            raise ValueError("n_test_splits must be less than n_splits")
        if n_splits < 2:
            raise ValueError("n_splits must be at least 2")

        self.n_splits = n_splits
        self.n_test_splits = n_test_splits
        self.purge_gap = purge_gap
        self.embargo_pct = embargo_pct

    def get_n_splits(self) -> int:
        """Return number of splitting iterations."""
        return int(comb(self.n_splits, self.n_test_splits))

    def split(
        self,
        X: pd.DataFrame | np.ndarray,
        y: Optional[pd.Series | np.ndarray] = None,
        groups: Optional[pd.Series | np.ndarray] = None,
    ) -> Generator[Tuple[np.ndarray, np.ndarray], None, None]:
        """
        Generate train/test indices with purging and embargo.

        Args:
            X: Feature matrix or DataFrame
            y: Target variable (unused, for sklearn compatibility)
            groups: Group labels (unused, for sklearn compatibility)

        Yields:
            train_indices, test_indices for each combination
        """
        n_samples = len(X)
        split_size = n_samples // self.n_splits
        embargo_size = int(n_samples * self.embargo_pct)

        # Define split boundaries
        split_bounds = []
        for i in range(self.n_splits):
            start = i * split_size
            end = (i + 1) * split_size if i < self.n_splits - 1 else n_samples
            split_bounds.append((start, end))

        # Generate all combinations of test splits
        all_splits = list(range(self.n_splits))
        test_combinations = list(combinations(all_splits, self.n_test_splits))

        for test_splits in test_combinations:
            train_splits = [s for s in all_splits if s not in test_splits]

            # Build test indices
            test_indices = []
            for s in test_splits:
                start, end = split_bounds[s]
                test_indices.extend(range(start, end))

            # Build train indices with purging and embargo
            train_indices = []
            test_set = set(test_indices)

            for s in train_splits:
                start, end = split_bounds[s]
                for idx in range(start, end):
                    # Check purging: skip if too close to test set
                    if self._is_purged(idx, test_set):
                        continue
                    # Check embargo: skip if in embargo period after test
                    if self._is_embargoed(idx, test_splits, split_bounds, embargo_size):
                        continue
                    train_indices.append(idx)

            yield np.array(train_indices), np.array(test_indices)

    def _is_purged(self, idx: int, test_set: set) -> bool:
        """Check if index should be purged (too close to test set)."""
        if self.purge_gap == 0:
            return False
        for test_idx in test_set:
            if abs(idx - test_idx) <= self.purge_gap:
                return True
        return False

    def _is_embargoed(
        self,
        idx: int,
        test_splits: tuple,
        split_bounds: List[Tuple[int, int]],
        embargo_size: int,
    ) -> bool:
        """Check if index falls in embargo period after test set."""
        if embargo_size == 0:
            return False
        for s in test_splits:
            _, test_end = split_bounds[s]
            if test_end <= idx < test_end + embargo_size:
                return True
        return False

    def get_all_splits(
        self,
        X: pd.DataFrame | np.ndarray,
    ) -> List[CPCVSplit]:
        """
        Get all splits as a list of CPCVSplit objects.

        Args:
            X: Feature matrix or DataFrame

        Returns:
            List of CPCVSplit objects
        """
        splits = []
        for i, (train_idx, test_idx) in enumerate(self.split(X)):
            splits.append(CPCVSplit(
                train_indices=train_idx,
                test_indices=test_idx,
                split_id=i,
            ))
        return splits


def validate_with_cpcv(
    data: pd.DataFrame,
    strategy_func,
    n_splits: int = 6,
    n_test_splits: int = 2,
    purge_gap: int = 5,
    embargo_pct: float = 0.01,
) -> dict:
    """
    Validate a strategy using CPCV methodology.

    Args:
        data: OHLCV DataFrame with DatetimeIndex
        strategy_func: Function that takes data and returns metrics dict
        n_splits: Total number of splits
        n_test_splits: Number of test splits per combination
        purge_gap: Observations to purge around test boundaries
        embargo_pct: Embargo percentage after test set

    Returns:
        dict with aggregated validation results
    """
    cpcv = CombinatorialPurgedKFold(
        n_splits=n_splits,
        n_test_splits=n_test_splits,
        purge_gap=purge_gap,
        embargo_pct=embargo_pct,
    )

    results = []
    for train_idx, test_idx in cpcv.split(data):
        train_data = data.iloc[train_idx]
        test_data = data.iloc[test_idx]

        # Run strategy on train (IS) and test (OOS)
        is_metrics = strategy_func(train_data)
        oos_metrics = strategy_func(test_data)

        results.append({
            "is_sharpe": is_metrics.get("sharpe_ratio", 0.0),
            "oos_sharpe": oos_metrics.get("sharpe_ratio", 0.0),
            "is_return": is_metrics.get("total_return", 0.0),
            "oos_return": oos_metrics.get("total_return", 0.0),
            "train_size": len(train_idx),
            "test_size": len(test_idx),
        })

    if not results:
        return {"error": "No valid splits generated"}

    # Aggregate results
    is_sharpes = [r["is_sharpe"] for r in results]
    oos_sharpes = [r["oos_sharpe"] for r in results]

    return {
        "n_combinations": len(results),
        "mean_is_sharpe": float(np.mean(is_sharpes)),
        "mean_oos_sharpe": float(np.mean(oos_sharpes)),
        "std_is_sharpe": float(np.std(is_sharpes)),
        "std_oos_sharpe": float(np.std(oos_sharpes)),
        "wfe_mean": float(np.mean(oos_sharpes) / np.mean(is_sharpes)) if np.mean(is_sharpes) != 0 else 0.0,
        "degradation_pct": float(1 - np.mean(oos_sharpes) / np.mean(is_sharpes)) * 100 if np.mean(is_sharpes) != 0 else 0.0,
        "all_results": results,
    }


@dataclass(frozen=True)
class CPCVPBOResult:
    """Result of CPCV-based PBO calculation."""
    pbo: float  # Probability of Backtest Overfitting [0, 1]
    pbo_median_rank: float  # Median rank of best IS strategies on OOS
    n_combinations: int  # Number of CPCV combinations tested
    threshold: float  # Threshold used for pass/fail
    passed: bool  # True if PBO < threshold
    is_sharpes_mean: float  # Mean IS Sharpe across combinations
    oos_sharpes_mean: float  # Mean OOS Sharpe across combinations
    wfe_cpcv: float  # WFE based on CPCV (OOS/IS)
    logits: List[float]  # Relative ranks for each combination


def pbo_with_cpcv(
    returns_matrix: np.ndarray,
    n_splits: int = 6,
    n_test_splits: int = 2,
    purge_gap: int = 0,
    embargo_pct: float = 0.01,
    threshold: float = 0.15,
) -> CPCVPBOResult:
    """
    Calculate Probability of Backtest Overfitting using CPCV.

    This implementation uses Combinatorial Purged Cross-Validation (CPCV)
    instead of Combinatorially Symmetric Cross-Validation (CSCV).

    CPCV with n_splits=6, n_test_splits=2 generates C(6,2) = 15 combinations.
    For each combination:
    1. Identify best strategy on IS (training set)
    2. Record OOS (test set) rank of that strategy
    3. Compute relative rank (0 = best, 1 = worst)

    PBO = proportion where best IS strategy ranks below median on OOS.

    Args:
        returns_matrix: Shape (n_trials, n_periods) - returns for each trial/strategy
        n_splits: Total number of time-based splits (default 6)
        n_test_splits: Number of splits for testing (default 2, gives C(6,2)=15)
        purge_gap: Number of observations to purge around test boundaries (default 0)
        embargo_pct: Percentage of data to embargo after test set (default 0.01)
        threshold: Maximum acceptable PBO (default 0.15)

    Returns:
        CPCVPBOResult with pbo value, statistics, and pass/fail

    Raises:
        ValueError: If n_test_splits >= n_splits or n_splits < 2

    Interpretation:
        PBO < 0.15: PASS - Low overfitting risk, parameters likely robust
        PBO 0.15-0.30: MARGINAL - Moderate overfitting risk
        PBO > 0.30: FAIL - High overfitting risk, best IS params likely overfit

    Example:
        >>> returns = np.random.randn(100, 1000)  # 100 trials, 1000 periods
        >>> result = pbo_with_cpcv(returns, n_splits=6, n_test_splits=2)
        >>> print(f"PBO: {result.pbo:.2%}, Pass: {result.passed}")
    """
    if n_splits < 2:
        raise ValueError("n_splits must be at least 2")
    if n_test_splits >= n_splits:
        raise ValueError("n_test_splits must be less than n_splits")

    n_trials, n_periods = returns_matrix.shape

    # Create dummy data for CPCV split generation
    dummy_data = pd.DataFrame(np.zeros(n_periods))

    # Initialize CPCV splitter
    cpcv = CombinatorialPurgedKFold(
        n_splits=n_splits,
        n_test_splits=n_test_splits,
        purge_gap=purge_gap,
        embargo_pct=embargo_pct,
    )

    underperformance_count = 0
    logits: List[float] = []
    is_sharpes_all = []
    oos_sharpes_all = []

    # Iterate over all CPCV combinations
    for train_idx, test_idx in cpcv.split(dummy_data):
        # Compute Sharpe for each trial on IS and OOS
        is_sharpes = _compute_sharpes_from_returns(returns_matrix, train_idx)
        oos_sharpes = _compute_sharpes_from_returns(returns_matrix, test_idx)

        is_sharpes_all.append(float(np.mean(is_sharpes)))
        oos_sharpes_all.append(float(np.mean(oos_sharpes)))

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

    n_combinations = len(logits)
    pbo = underperformance_count / n_combinations if n_combinations > 0 else 0.0

    # Compute median rank for reporting
    median_rank = float(np.median(logits)) if logits else 0.5

    # Compute mean IS/OOS Sharpe and WFE
    mean_is_sharpe = float(np.mean(is_sharpes_all)) if is_sharpes_all else 0.0
    mean_oos_sharpe = float(np.mean(oos_sharpes_all)) if oos_sharpes_all else 0.0
    wfe_cpcv = mean_oos_sharpe / mean_is_sharpe if mean_is_sharpe != 0 else 0.0

    return CPCVPBOResult(
        pbo=pbo,
        pbo_median_rank=median_rank,
        n_combinations=n_combinations,
        threshold=threshold,
        passed=pbo < threshold,
        is_sharpes_mean=mean_is_sharpe,
        oos_sharpes_mean=mean_oos_sharpe,
        wfe_cpcv=wfe_cpcv,
        logits=logits,
    )


def _compute_sharpes_from_returns(
    returns_matrix: np.ndarray,
    indices: np.ndarray,
) -> np.ndarray:
    """
    Compute Sharpe ratios for all trials on given indices.

    Args:
        returns_matrix: Shape (n_trials, n_periods)
        indices: Array of period indices to use

    Returns:
        Array of Sharpe ratios for each trial
    """
    subset = returns_matrix[:, indices]
    means = np.mean(subset, axis=1)
    stds = np.std(subset, axis=1, ddof=1) + 1e-10  # Avoid division by zero
    return means / stds


def guard_cpcv_pbo(
    returns_matrix: np.ndarray,
    threshold: float = 0.15,
    n_splits: int = 6,
    n_test_splits: int = 2,
    purge_gap: int = 0,
    embargo_pct: float = 0.01,
) -> dict:
    """
    Guard function for CPCV-based PBO validation in pipeline.

    Args:
        returns_matrix: (n_trials, n_periods) array of returns
        threshold: Max acceptable PBO (default 0.15)
        n_splits: Number of CPCV splits (default 6)
        n_test_splits: Number of test splits (default 2, gives C(6,2)=15)
        purge_gap: Observations to purge around test boundaries
        embargo_pct: Embargo percentage after test set

    Returns:
        dict with guard results compatible with validation pipeline
    """
    result = pbo_with_cpcv(
        returns_matrix,
        n_splits=n_splits,
        n_test_splits=n_test_splits,
        purge_gap=purge_gap,
        embargo_pct=embargo_pct,
        threshold=threshold,
    )

    return {
        "guard": "cpcv_pbo",
        "pass": result.passed,
        "pbo": round(result.pbo, 4),
        "pbo_median_rank": round(result.pbo_median_rank, 4),
        "threshold": threshold,
        "interpretation": _interpret_pbo(result.pbo),
        "n_combinations": result.n_combinations,
        "is_sharpe_mean": round(result.is_sharpes_mean, 4),
        "oos_sharpe_mean": round(result.oos_sharpes_mean, 4),
        "wfe_cpcv": round(result.wfe_cpcv, 4),
    }


def _interpret_pbo(pbo: float) -> str:
    """Return human-readable interpretation of PBO value."""
    if pbo < 0.15:
        return "PASS - Low overfitting risk, parameters likely robust"
    elif pbo < 0.30:
        return "MARGINAL - Moderate overfitting risk"
    elif pbo < 0.50:
        return "FAIL - High overfitting risk, significant overfitting detected"
    else:
        return "CRITICAL - Best IS params almost certainly overfit"
