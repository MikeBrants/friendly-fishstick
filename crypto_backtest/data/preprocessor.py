"""Data validation and preprocessing utilities."""

from __future__ import annotations

import numpy as np
import pandas as pd


class DataPreprocessor:
    """Validate and normalize raw OHLCV data."""

    def __init__(
        self,
        expected_timeframe: str | None = None,
        max_return_zscore: float = 8.0,
        safety_gap_bars: int = 1,
        allow_gaps: bool = True,
    ) -> None:
        self.expected_timeframe = expected_timeframe
        self.max_return_zscore = max_return_zscore
        self.safety_gap_bars = safety_gap_bars
        self.allow_gaps = allow_gaps

    def validate(self, data: pd.DataFrame) -> pd.DataFrame:
        """Run gap/outlier checks and return cleaned data."""
        df = data.copy()
        if "timestamp" not in df.columns:
            if isinstance(df.index, pd.DatetimeIndex):
                df = df.reset_index().rename(columns={"index": "timestamp"})
            else:
                raise ValueError("Data must include a 'timestamp' column or datetime index.")

        df = self.normalize_timezone(df)

        required = {"open", "high", "low", "close", "volume"}
        missing = required.difference(df.columns)
        if missing:
            raise ValueError(f"Missing columns: {sorted(missing)}")

        for col in ["open", "high", "low", "close", "volume"]:
            df[col] = pd.to_numeric(df[col], errors="coerce")

        df = df.dropna(subset=["open", "high", "low", "close"]).copy()
        df = df.sort_values("timestamp").drop_duplicates(subset=["timestamp"])

        corrected_high = df[["high", "open", "close", "low"]].max(axis=1)
        corrected_low = df[["high", "open", "close", "low"]].min(axis=1)
        df["high"] = corrected_high
        df["low"] = corrected_low

        df = self._filter_outliers(df)
        df = df.reset_index(drop=True)
        self._attach_gap_stats(df)
        return df

    def normalize_timezone(self, data: pd.DataFrame) -> pd.DataFrame:
        """Ensure timestamps are UTC and sorted."""
        df = data.copy()
        if "timestamp" in df.columns:
            df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True, errors="coerce")
        elif isinstance(df.index, pd.DatetimeIndex):
            df.index = df.index.tz_convert("UTC") if df.index.tz is not None else df.index.tz_localize("UTC")
            df = df.reset_index().rename(columns={"index": "timestamp"})
        else:
            raise ValueError("Unable to normalize timezone without timestamps.")
        df = df.dropna(subset=["timestamp"])
        return df

    def train_test_split(self, data: pd.DataFrame, split_ratio: float) -> tuple[pd.DataFrame, pd.DataFrame]:
        """Split the data into train/test with a safety gap."""
        if not 0.0 < split_ratio < 1.0:
            raise ValueError("split_ratio must be between 0 and 1.")
        n = len(data)
        split_idx = int(n * split_ratio)
        gap = min(self.safety_gap_bars, max(0, n - split_idx - 1))
        train = data.iloc[: max(0, split_idx - gap)].reset_index(drop=True)
        test = data.iloc[split_idx + gap :].reset_index(drop=True)
        return train, test

    def _filter_outliers(self, data: pd.DataFrame) -> pd.DataFrame:
        if len(data) < 3:
            return data
        returns = data["close"].pct_change().replace([np.inf, -np.inf], np.nan)
        log_returns = np.log1p(returns).dropna()
        if log_returns.std(ddof=0) == 0:
            return data
        zscores = (log_returns - log_returns.mean()) / log_returns.std(ddof=0)
        mask = pd.Series(True, index=data.index)
        mask.iloc[1:] = zscores.abs().values <= self.max_return_zscore
        data.attrs["outlier_count"] = int((~mask).sum())
        return data.loc[mask]

    def _attach_gap_stats(self, data: pd.DataFrame) -> None:
        if not self.expected_timeframe:
            return
        try:
            expected = pd.Timedelta(self.expected_timeframe)
        except ValueError:
            return
        diffs = data["timestamp"].diff().dropna()
        gap_mask = diffs > expected * 1.5
        gap_count = int(gap_mask.sum())
        data.attrs["gap_count"] = gap_count
        if gap_count and not self.allow_gaps:
            raise ValueError(f"Detected {gap_count} gaps in data.")
