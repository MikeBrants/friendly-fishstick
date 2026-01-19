"""Five-in-one composite filter implementation."""

from __future__ import annotations

from dataclasses import dataclass
import numpy as np
import pandas as pd

from .ichimoku import donchian


@dataclass(frozen=True)
class FiveInOneConfig:
    fast_period: int = 7
    slow_period: int = 19
    er_period: int = 8
    norm_period: int = 50
    use_norm: bool = True
    ad_norm_period: int = 50
    use_ad_line: bool = True
    ichi5in1_strict: bool = True
    use_transition_mode: bool = True
    use_distance_filter: bool = False
    use_volume_filter: bool = False
    use_regression_cloud: bool = False
    use_kama_oscillator: bool = False
    use_ichimoku_filter: bool = True
    tenkan_5: int = 9
    kijun_5: int = 26
    displacement_5: int = 52


class FiveInOneFilter:
    def __init__(self, config: FiveInOneConfig) -> None:
        self.config = config

    def distance_filter(self, ohlc4: pd.Series) -> pd.Series:
        """Distance filter using multiple KAMA periods."""
        lengths = [5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 75, 80, 85, 90, 100]
        kamas = {length: self._kama_distance(ohlc4, length) for length in lengths}

        dist1 = (
            self._safe_div(kamas[5] - kamas[10], kamas[10])
            + self._safe_div(kamas[10] - kamas[15], kamas[15])
            + self._safe_div(kamas[15] - kamas[20], kamas[20])
            + self._safe_div(kamas[20] - kamas[25], kamas[25])
            + self._safe_div(kamas[25] - kamas[30], kamas[30])
            + self._safe_div(kamas[30] - kamas[35], kamas[35])
        )
        dist2 = (
            self._safe_div(kamas[35] - kamas[40], kamas[40])
            + self._safe_div(kamas[40] - kamas[45], kamas[45])
            + self._safe_div(kamas[45] - kamas[50], kamas[50])
            + self._safe_div(kamas[50] - kamas[55], kamas[55])
            + self._safe_div(kamas[55] - kamas[60], kamas[60])
            + self._safe_div(kamas[60] - kamas[65], kamas[65])
        )
        dist3 = (
            self._safe_div(kamas[65] - kamas[70], kamas[70])
            + self._safe_div(kamas[70] - kamas[75], kamas[75])
            + self._safe_div(kamas[75] - kamas[80], kamas[80])
            + self._safe_div(kamas[80] - kamas[85], kamas[85])
            + self._safe_div(kamas[85] - kamas[90], kamas[90])
            + self._safe_div(kamas[90] - kamas[100], kamas[100])
        )
        return (dist1 + dist2 + dist3) / 18.0

    def ad_line_filter(self, high: pd.Series, low: pd.Series, close: pd.Series, volume: pd.Series) -> pd.Series:
        """A/D Line filter with normalization and slope."""
        price_range = (high - low).replace(0, np.nan)
        mfm = (close - low - (high - close)) / price_range
        mfm = mfm.fillna(0.0)
        mfv = mfm * volume
        ad_line = mfv.cumsum()

        ad_lowest = ad_line.rolling(self.config.ad_norm_period).min()
        ad_highest = ad_line.rolling(self.config.ad_norm_period).max()
        denom = (ad_highest - ad_lowest).replace(0, np.nan)
        ad_norm = (ad_line - ad_lowest) / denom
        ad_norm = ad_norm.fillna(0.0) - 0.5
        ad_slope = ad_norm - ad_norm.shift(3).fillna(0.0)

        ad_bull = (ad_norm > 0.1) & (ad_slope > 0)
        ad_bear = (ad_norm < -0.1) & (ad_slope < 0)
        return pd.Series(
            np.where(ad_bull, 1, np.where(ad_bear, -1, 0)), index=close.index
        )

    def obv_filter(self, close: pd.Series, volume: pd.Series) -> pd.Series:
        """OBV filter with EMA smoothing."""
        delta = close.diff().fillna(0.0)
        direction = np.sign(delta)
        obv = (direction * volume).fillna(0.0).cumsum()

        obv_short = obv.ewm(span=3, adjust=False).mean()
        obv_medium = obv.ewm(span=9, adjust=False).mean()
        obv_long = obv.ewm(span=21, adjust=False).mean()
        obv_bull = (obv_short > obv_medium) & (obv_short > obv_long)
        obv_bear = (obv_short < obv_medium) & (obv_short < obv_long)
        return pd.Series(
            np.where(obv_bull, 1, np.where(obv_bear, -1, 0)), index=close.index
        )

    def regression_cloud_filter(self, close: pd.Series) -> pd.Series:
        """Regression cloud filter based on multiple slopes."""
        lengths = [10, 20, 50, 100, 200, 300, 400, 500]
        slopes = [self._rolling_slope(close, length) for length in lengths]

        diffs = [(slopes[idx] - slopes[idx + 1]) * lengths[idx] for idx in range(len(slopes) - 1)]
        reg_total_distance = diffs[0]
        for diff in diffs[1:]:
            reg_total_distance = reg_total_distance + diff

        baseline = close.rolling(100).mean()
        cloud_line = baseline + reg_total_distance * 0.1
        reg_above = close > pd.concat([baseline, cloud_line], axis=1).max(axis=1)
        reg_below = close < pd.concat([baseline, cloud_line], axis=1).min(axis=1)
        return pd.Series(
            np.where(reg_above, 1, np.where(reg_below, -1, 0)), index=close.index
        )

    def kama_oscillator(self, close: pd.Series) -> pd.Series:
        """KAMA oscillator normalized to [-0.5, 0.5]."""
        ch = (close - close.shift(self.config.er_period)).abs()
        volatility = (close - close.shift(1)).abs().rolling(self.config.er_period).sum()
        er_val = ch / volatility.replace(0, np.nan)
        er_val = er_val.fillna(0.0)

        fast = 2 / (self.config.fast_period + 1)
        slow = 2 / (self.config.slow_period + 1)
        sc = er_val * (fast - slow) + slow
        ema_fast = close.ewm(span=self.config.fast_period, adjust=False).mean()
        kama_val = ema_fast + sc * (close - ema_fast)

        lowest = kama_val.rolling(self.config.norm_period).min()
        highest = kama_val.rolling(self.config.norm_period).max()
        denom = (highest - lowest).clip(lower=1e-10)
        normalized = (kama_val - lowest) / denom - 0.5
        kama_osc = normalized if self.config.use_norm else kama_val

        kama_bull = kama_osc > 0
        kama_bear = kama_osc < 0
        return pd.Series(
            np.where(kama_bull, 1, np.where(kama_bear, -1, 0)), index=close.index
        )

    def ichimoku_5_filter(self, data: pd.DataFrame, strict: bool) -> pd.Series:
        """Ichimoku 5-in-1 strict/light filter."""
        missing = {"high", "low", "close"}.difference(data.columns)
        if missing:
            raise ValueError(f"Missing columns for Ichimoku 5-in-1: {sorted(missing)}")

        tenkan = donchian(data["high"], data["low"], self.config.tenkan_5)
        kijun = donchian(data["high"], data["low"], self.config.kijun_5)
        kumo_a = (tenkan + kijun) / 2.0
        kumo_b = donchian(data["high"], data["low"], self.config.displacement_5)
        close = data["close"]

        bull = (
            (close > tenkan)
            & (close > kijun)
            & (close > kumo_a.shift(25))
            & (close > kumo_b.shift(25))
        )
        bull &= (
            (close > kumo_a.shift(50))
            & (close > kumo_b.shift(50))
            & (close > kijun.shift(25))
            & (close > tenkan.shift(25))
        )
        bull &= (kumo_a > kumo_b) & (kumo_a > kumo_a.shift(1)) & (kumo_b > kumo_b.shift(1))
        bull &= (kijun > kijun.shift(1)) & (tenkan > tenkan.shift(1))

        if strict:
            bear = (
                (close < tenkan)
                & (close < kijun)
                & (close < kumo_a.shift(25))
                & (close < kumo_b.shift(25))
            )
            bear &= (kijun < kumo_a.shift(25)) & (kijun < kumo_b.shift(25))
            bear &= (tenkan < kumo_a.shift(25)) & (tenkan < kumo_b.shift(25))
            bear &= (kijun < kijun.shift(1)) & (tenkan < tenkan.shift(1))
            bear &= (
                (close < kumo_a.shift(50))
                & (close < kumo_b.shift(50))
                & (close < kijun.shift(25))
                & (close < tenkan.shift(25))
            )
            bear &= (kumo_a < kumo_b) & (kumo_a < kumo_a.shift(1)) & (kumo_b < kumo_b.shift(1))
        else:
            bear = (
                (close < kumo_a.shift(25))
                & (close < kumo_b.shift(25))
                & (close < kumo_b)
            )

        return pd.Series(np.where(bull, 1, np.where(bear, -1, 0)), index=data.index)

    def compute_combined(self, data: pd.DataFrame, transition_mode: bool) -> pd.Series:
        """Combine filters into a single signal series."""
        missing = {"open", "high", "low", "close", "volume"}.difference(data.columns)
        if missing:
            raise ValueError(f"Missing columns for FiveInOne: {sorted(missing)}")

        index = data.index
        always_true = pd.Series(True, index=index)

        if self.config.use_distance_filter:
            ohlc4 = (data["open"] + data["high"] + data["low"] + data["close"]) / 4.0
            total_distance = self.distance_filter(ohlc4)
            distance_bull = total_distance > 0
            distance_bear = total_distance < 0
        else:
            distance_bull = always_true
            distance_bear = always_true

        if self.config.use_volume_filter:
            if self.config.use_ad_line:
                vol_signal = self.ad_line_filter(
                    data["high"], data["low"], data["close"], data["volume"]
                )
            else:
                vol_signal = self.obv_filter(data["close"], data["volume"])
            volume_bull = vol_signal > 0
            volume_bear = vol_signal < 0
        else:
            volume_bull = always_true
            volume_bear = always_true

        if self.config.use_regression_cloud:
            reg_signal = self.regression_cloud_filter(data["close"])
            reg_bull = reg_signal > 0
            reg_bear = reg_signal < 0
        else:
            reg_bull = always_true
            reg_bear = always_true

        if self.config.use_kama_oscillator:
            kama_signal = self.kama_oscillator(data["close"])
            kama_bull = kama_signal > 0
            kama_bear = kama_signal < 0
        else:
            kama_bull = always_true
            kama_bear = always_true

        if self.config.use_ichimoku_filter:
            ichi_signal = self.ichimoku_5_filter(data, self.config.ichi5in1_strict)
            ichi_bull = ichi_signal > 0
            ichi_bear = ichi_signal < 0
        else:
            ichi_bull = always_true
            ichi_bear = always_true

        all_bull = distance_bull & volume_bull & reg_bull & kama_bull & ichi_bull
        all_bear = distance_bear & volume_bear & reg_bear & kama_bear & ichi_bear

        if transition_mode:
            prev_all_bull = all_bull.shift(1, fill_value=False)
            prev_all_bear = all_bear.shift(1, fill_value=False)
            bull_signal = all_bull & ~prev_all_bull
            bear_signal = all_bear & ~prev_all_bear
        else:
            bull_signal = all_bull
            bear_signal = all_bear

        return pd.Series(
            np.where(bull_signal, 1, np.where(bear_signal, -1, 0)),
            index=index,
        )

    def _kama_distance(self, src: pd.Series, length: int) -> pd.Series:
        price = src.to_numpy(dtype=float)
        n = len(price)
        if n == 0:
            return pd.Series(dtype=float, index=src.index)
        if length < 1:
            raise ValueError("length must be >= 1")

        change = np.abs(price - np.roll(price, length))
        change[: min(length, n)] = 0.0
        volatility = np.abs(np.diff(price, prepend=price[0]))
        noise = (
            pd.Series(volatility, index=src.index)
            .rolling(length)
            .sum()
            .fillna(0.0)
            .to_numpy()
        )
        er = np.divide(change, noise, out=np.zeros_like(change), where=noise != 0)

        fast_end = 0.666
        slow_end = 0.0645
        smooth = (er * (fast_end - slow_end) + slow_end) ** 2

        kama = np.zeros(n, dtype=float)
        kama[0] = price[0]
        for i in range(1, n):
            kama[i] = kama[i - 1] + smooth[i] * (price[i] - kama[i - 1])
        return pd.Series(kama, index=src.index)

    @staticmethod
    def _safe_div(numerator: pd.Series, denominator: pd.Series) -> pd.Series:
        denom = denominator.replace(0, np.nan)
        return (numerator / denom).fillna(0.0)

    @staticmethod
    def _rolling_slope(series: pd.Series, length: int) -> pd.Series:
        if length < 2:
            return pd.Series(0.0, index=series.index)
        x = np.arange(1, length + 1, dtype=float)
        sum_x = x.sum()
        sum_x2 = (x**2).sum()
        denom = length * sum_x2 - sum_x**2
        if denom == 0:
            return pd.Series(0.0, index=series.index)

        def slope(values: np.ndarray) -> float:
            sum_y = values.sum()
            sum_xy = (values * x).sum()
            return (length * sum_xy - sum_x * sum_y) / denom

        return series.rolling(length).apply(slope, raw=True)
