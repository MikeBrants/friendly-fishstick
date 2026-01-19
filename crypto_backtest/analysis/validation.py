"""Helpers to compare Python signals against Pine Script exports."""

from __future__ import annotations

from dataclasses import dataclass
import pandas as pd


@dataclass(frozen=True)
class SignalComparison:
    match_rate: float
    long_precision: float
    long_recall: float
    short_precision: float
    short_recall: float


def compare_signals(
    pine_signals: pd.Series,
    model_signals: pd.Series,
) -> SignalComparison:
    """Compare Pine signals with model signals aligned by index."""
    aligned = pd.concat(
        [pine_signals.rename("pine"), model_signals.rename("model")], axis=1
    ).dropna()
    if aligned.empty:
        return SignalComparison(0.0, 0.0, 0.0, 0.0, 0.0)

    pine = aligned["pine"].astype(int)
    model = aligned["model"].astype(int)
    match_rate = float((pine == model).mean())

    long_precision, long_recall = _precision_recall(pine == 1, model == 1)
    short_precision, short_recall = _precision_recall(pine == -1, model == -1)

    return SignalComparison(
        match_rate=match_rate,
        long_precision=long_precision,
        long_recall=long_recall,
        short_precision=short_precision,
        short_recall=short_recall,
    )


def load_pine_signals(path: str, time_col: str = "timestamp", signal_col: str = "signal") -> pd.Series:
    """Load Pine CSV export with timestamp and signal columns."""
    df = pd.read_csv(path)
    df[time_col] = pd.to_datetime(df[time_col], utc=True, errors="coerce")
    df = df.dropna(subset=[time_col, signal_col])
    df = df.set_index(time_col).sort_index()
    return df[signal_col].astype(int)


def _precision_recall(true_mask: pd.Series, pred_mask: pd.Series) -> tuple[float, float]:
    tp = (true_mask & pred_mask).sum()
    fp = (~true_mask & pred_mask).sum()
    fn = (true_mask & ~pred_mask).sum()
    precision = float(tp / (tp + fp)) if (tp + fp) else 0.0
    recall = float(tp / (tp + fn)) if (tp + fn) else 0.0
    return precision, recall
