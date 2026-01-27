"""Worst-case path analysis based on CPCV combinations."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List

import numpy as np
import pandas as pd

from crypto_backtest.validation.cpcv import CombinatorialPurgedKFold


@dataclass(frozen=True)
class WorstCaseResult:
    worst_sharpe: float
    fragility_score: float
    verdict: str
    oos_sharpes: List[float]


def _compute_sharpes(returns_matrix: np.ndarray, indices: np.ndarray) -> np.ndarray:
    subset = returns_matrix[:, indices]
    means = np.mean(subset, axis=1)
    stds = np.std(subset, axis=1, ddof=1) + 1e-10
    return means / stds


def _fragility_score(values: List[float]) -> float:
    arr = np.array(values, dtype=float)
    mean = float(np.mean(arr))
    std = float(np.std(arr))
    if mean <= 0:
        return float("inf")
    return std / mean


def _classify_fragility(score: float) -> str:
    if score < 0.3:
        return "ROBUST"
    if score <= 0.5:
        return "ACCEPTABLE"
    return "FRAGILE"


def worst_case_path(
    returns_matrix: np.ndarray | pd.DataFrame,
    n_splits: int = 6,
    n_test_splits: int = 2,
    purge_gap: int = 3,
    embargo_pct: float = 0.01,
) -> WorstCaseResult:
    if isinstance(returns_matrix, pd.DataFrame):
        returns_matrix = returns_matrix.values

    if returns_matrix.ndim != 2:
        raise ValueError("returns_matrix must be 2D")

    n_trials, n_periods = returns_matrix.shape
    dummy = pd.DataFrame(np.zeros(n_periods))

    cpcv = CombinatorialPurgedKFold(
        n_splits=n_splits,
        n_test_splits=n_test_splits,
        purge_gap=purge_gap,
        embargo_pct=embargo_pct,
    )

    oos_sharpes: List[float] = []
    for train_idx, test_idx in cpcv.split(dummy):
        is_sharpes = _compute_sharpes(returns_matrix, train_idx)
        best_idx = int(np.argmax(is_sharpes))
        oos_sharpes_all = _compute_sharpes(returns_matrix, test_idx)
        oos_sharpes.append(float(oos_sharpes_all[best_idx]))

    worst_sharpe = float(np.min(oos_sharpes)) if oos_sharpes else 0.0
    fragility_score = _fragility_score(oos_sharpes) if oos_sharpes else float("inf")
    verdict = _classify_fragility(fragility_score)

    return WorstCaseResult(
        worst_sharpe=worst_sharpe,
        fragility_score=fragility_score,
        verdict=verdict,
        oos_sharpes=oos_sharpes,
    )
