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
