"""FINAL TRIGGER v4.3 - Polish OOS Comparison (A vs A+Gate)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Literal, Optional
import json
import os

import numpy as np
import pandas as pd
try:
    from scipy.stats import binom_test
except ImportError:  # SciPy >= 1.9
    from scipy.stats import binomtest as _binomtest

    def binom_test(k: int, n: int, p: float, alternative: str = "greater") -> float:
        return _binomtest(k, n, p, alternative=alternative).pvalue

PolishDecision = Literal["UPGRADE_TO_B", "STAY_A", "INSUFFICIENT_DATA"]


@dataclass
class FoldResult:
    fold_id: int
    sharpe_a: float
    sharpe_b: float
    maxdd_a: float
    maxdd_b: float
    n_trades_a: int
    n_trades_b: int
    b_wins: bool


@dataclass
class CandidateResult:
    couple_id: str
    b_wins_count: int
    n_folds: int
    p_value: float
    median_delta_sharpe: float
    median_delta_maxdd: float
    fold_results: List[FoldResult]
    passes: bool


@dataclass
class PolishOOSResult:
    decision: PolishDecision
    candidates_results: List[CandidateResult]
    n_candidates_agree: int
    min_candidates_needed: int
    reason: str
    rejection_reason: Optional[str]


def run_polish_oos_comparison(
    baseline_results: dict,
    cscv_folds: List[dict],
    trades_df: pd.DataFrame,
    config: dict,
) -> PolishOOSResult:
    regime_cfg = config.get("policy", {}).get("regime", {})
    polish_cfg = regime_cfg.get("polish_oos", {})

    max_candidates = polish_cfg.get("max_candidates", 5)
    min_candidates_agree = polish_cfg.get("min_candidates_agree", 3)
    min_wins = polish_cfg.get("min_wins", 8)
    min_delta_sharpe = polish_cfg.get("min_median_delta_sharpe", 0.05)
    min_delta_maxdd = polish_cfg.get("min_median_delta_maxdd", 3.0)
    n_min_bucket = regime_cfg.get("n_trades_min_per_bucket", 80)

    # Check data sufficiency
    required_buckets = ["long_bull", "long_bear", "short_bull", "short_bear"]
    for bucket in required_buckets:
        side, regime = bucket.split("_")
        mask = (trades_df["side"] == side) & (trades_df["regime"] == regime)
        if int(mask.sum()) < n_min_bucket:
            return PolishOOSResult(
                decision="INSUFFICIENT_DATA",
                candidates_results=[],
                n_candidates_agree=0,
                min_candidates_needed=min_candidates_agree,
                reason="Insufficient data per bucket",
                rejection_reason=f"Bucket {bucket} < {n_min_bucket}",
            )

    coupled_candidates = baseline_results.get("coupled_candidates", [])[:max_candidates]
    if len(coupled_candidates) < min_candidates_agree:
        return PolishOOSResult(
            decision="INSUFFICIENT_DATA",
            candidates_results=[],
            n_candidates_agree=0,
            min_candidates_needed=min_candidates_agree,
            reason=f"Only {len(coupled_candidates)} candidates",
            rejection_reason="Not enough candidates",
        )

    candidates_results: List[CandidateResult] = []
    n_candidates_pass = 0

    for candidate in coupled_candidates:
        couple_id = candidate.get("couple_id", "unknown")
        fold_results: List[FoldResult] = []
        b_wins_count = 0
        delta_sharpes: List[float] = []
        delta_maxdds: List[float] = []

        for fold in cscv_folds:
            test_idx = fold.get("test_idx", [])
            if len(test_idx) == 0:
                continue
            test_trades = trades_df.iloc[test_idx].copy()

            metrics_a = _eval_trades_metrics(test_trades, regime_gate=False)
            metrics_b = _eval_trades_metrics(test_trades, regime_gate=True)

            delta_sharpe = metrics_b["sharpe"] - metrics_a["sharpe"]
            delta_maxdd = metrics_a["max_dd"] - metrics_b["max_dd"]
            delta_sharpes.append(delta_sharpe)
            delta_maxdds.append(delta_maxdd)

            b_wins = delta_sharpe >= min_delta_sharpe or delta_maxdd >= min_delta_maxdd
            if b_wins:
                b_wins_count += 1

            fold_results.append(
                FoldResult(
                    fold_id=fold.get("fold_id", 0),
                    sharpe_a=metrics_a["sharpe"],
                    sharpe_b=metrics_b["sharpe"],
                    maxdd_a=metrics_a["max_dd"],
                    maxdd_b=metrics_b["max_dd"],
                    n_trades_a=metrics_a["n_trades"],
                    n_trades_b=metrics_b["n_trades"],
                    b_wins=b_wins,
                )
            )

        n_folds = len(fold_results)
        if n_folds > 0:
            p_value = binom_test(b_wins_count, n_folds, 0.5, alternative="greater")
            median_delta_sharpe = float(np.median(delta_sharpes))
            median_delta_maxdd = float(np.median(delta_maxdds))
            candidate_passes = (
                b_wins_count >= min_wins
                and (
                    median_delta_sharpe >= min_delta_sharpe
                    or median_delta_maxdd >= min_delta_maxdd
                )
            )
        else:
            p_value, median_delta_sharpe, median_delta_maxdd = 1.0, 0.0, 0.0
            candidate_passes = False

        if candidate_passes:
            n_candidates_pass += 1

        candidates_results.append(
            CandidateResult(
                couple_id=couple_id,
                b_wins_count=b_wins_count,
                n_folds=n_folds,
                p_value=float(p_value),
                median_delta_sharpe=median_delta_sharpe,
                median_delta_maxdd=median_delta_maxdd,
                fold_results=fold_results,
                passes=candidate_passes,
            )
        )

    if n_candidates_pass >= min_candidates_agree:
        decision = "UPGRADE_TO_B"
        reason = (
            f"Polish passed: {n_candidates_pass}/{len(coupled_candidates)} candidates agree"
        )
        rejection_reason = None
    else:
        decision = "STAY_A"
        reason = (
            f"Polish failed: {n_candidates_pass}/{len(coupled_candidates)} "
            f"(need {min_candidates_agree})"
        )
        rejection_reason = "Not enough candidates agree"

    return PolishOOSResult(
        decision=decision,
        candidates_results=candidates_results,
        n_candidates_agree=n_candidates_pass,
        min_candidates_needed=min_candidates_agree,
        reason=reason,
        rejection_reason=rejection_reason,
    )


def _eval_trades_metrics(trades_df: pd.DataFrame, regime_gate: bool) -> dict:
    if regime_gate:
        mask = (
            ((trades_df["regime"] == "bull") & (trades_df["side"] == "long"))
            | ((trades_df["regime"] == "bear") & (trades_df["side"] == "short"))
            | (trades_df["regime"] == "sideways")
        )
        filtered = trades_df[mask].copy()
    else:
        filtered = trades_df.copy()

    n_trades = len(filtered)
    if n_trades < 5:
        return {
            "sharpe": 0.0,
            "max_dd": 100.0,
            "n_trades": n_trades,
            "total_pnl": 0.0,
        }

    returns = filtered["pnl"].values
    total_pnl = float(returns.sum())
    sharpe = (
        (returns.mean() / returns.std()) * np.sqrt(8760)
        if returns.std() > 1e-9
        else 0.0
    )

    cumulative = np.cumsum(returns)
    running_max = np.maximum.accumulate(cumulative)
    drawdowns = running_max - cumulative
    max_dd = (drawdowns.max() / running_max.max()) * 100 if running_max.max() > 0 else 0.0

    return {
        "sharpe": round(float(sharpe), 4),
        "max_dd": round(float(max_dd), 2),
        "n_trades": n_trades,
        "total_pnl": round(total_pnl, 6),
    }


def save_polish_oos_result(result: PolishOOSResult, output_path: str) -> None:
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    result_dict = {
        "decision": result.decision,
        "n_candidates_agree": result.n_candidates_agree,
        "min_candidates_needed": result.min_candidates_needed,
        "reason": result.reason,
        "rejection_reason": result.rejection_reason,
        "candidates": [
            {
                "couple_id": c.couple_id,
                "b_wins_count": c.b_wins_count,
                "n_folds": c.n_folds,
                "p_value": round(float(c.p_value), 4),
                "median_delta_sharpe": round(float(c.median_delta_sharpe), 4),
                "median_delta_maxdd": round(float(c.median_delta_maxdd), 2),
                "passes": c.passes,
            }
            for c in result.candidates_results
        ],
    }
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result_dict, f, indent=2)
