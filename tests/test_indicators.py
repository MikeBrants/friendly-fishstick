import numpy as np
import pandas as pd

from crypto_backtest.indicators.five_in_one import FiveInOneConfig, FiveInOneFilter
from crypto_backtest.indicators.atr import compute_atr
from crypto_backtest.indicators.ichimoku import Ichimoku, IchimokuConfig, donchian
from crypto_backtest.indicators.mama_fama_kama import (
    compute_kama,
    compute_mama_fama,
    compute_mesa_period,
)


def _sample_ohlcv(rows: int = 600) -> pd.DataFrame:
    index = pd.date_range("2020-01-01", periods=rows, freq="h", tz="UTC")
    close = pd.Series(np.linspace(100.0, 200.0, rows), index=index)
    open_ = close.shift(1).fillna(close)
    high = pd.Series(np.maximum(open_, close) + 1.0, index=index)
    low = pd.Series(np.minimum(open_, close) - 1.0, index=index)
    volume = pd.Series(np.linspace(1000.0, 2000.0, rows), index=index)
    return pd.DataFrame(
        {"open": open_, "high": high, "low": low, "close": close, "volume": volume},
        index=index,
    )


def test_mama_fama_kama_constant_series():
    index = pd.date_range("2020-01-01", periods=80, freq="h", tz="UTC")
    src = pd.Series(100.0, index=index)
    mama_fama = compute_mama_fama(src, fast_limit=0.5, slow_limit=0.05)
    kama = compute_kama(src, length=10)

    assert len(mama_fama) == len(src)
    assert len(kama) == len(src)
    assert abs(mama_fama["mama"].iloc[-1] - 100.0) < 1e-6
    assert abs(mama_fama["fama"].iloc[-1] - 100.0) < 1e-6
    assert abs(kama.iloc[-1] - 100.0) < 1e-6


def test_mesa_period_bounds():
    index = pd.date_range("2020-01-01", periods=120, freq="h", tz="UTC")
    src = pd.Series(np.linspace(1.0, 2.0, len(index)), index=index)
    period = compute_mesa_period(src)
    valid = period.iloc[60:]
    assert (valid >= 6.0).all()
    assert (valid <= 50.0).all()


def test_donchian_midpoint():
    index = pd.date_range("2020-01-01", periods=5, freq="h", tz="UTC")
    high = pd.Series([1, 2, 3, 4, 5], index=index)
    low = pd.Series([0, 1, 1, 2, 2], index=index)
    midpoint = donchian(high, low, length=3)
    expected = (max(high.iloc[2:5]) + min(low.iloc[2:5])) / 2.0
    assert abs(midpoint.iloc[-1] - expected) < 1e-6


def test_ichimoku_outputs():
    data = _sample_ohlcv(200)
    ichi = Ichimoku(IchimokuConfig(tenkan=9, kijun=26, displacement=52))
    lines = ichi.compute(data)

    assert {"tenkan", "kijun", "kumo_a", "kumo_b"}.issubset(lines.columns)

    bullish = ichi.all_bullish(data["close"])
    bearish = ichi.all_bearish(data["close"])

    assert bullish.index.equals(data.index)
    assert bearish.index.equals(data.index)
    assert bullish.dropna().isin([True, False]).all()
    assert bearish.dropna().isin([True, False]).all()


def test_five_in_one_signals():
    data = _sample_ohlcv(600)
    config = FiveInOneConfig(
        use_distance_filter=True,
        use_volume_filter=True,
        use_regression_cloud=True,
        use_kama_oscillator=True,
        use_ichimoku_filter=True,
        use_transition_mode=True,
    )
    filt = FiveInOneFilter(config)
    signal = filt.compute_combined(data, transition_mode=config.use_transition_mode)

    assert len(signal) == len(data)
    assert set(signal.dropna().unique()).issubset({-1, 0, 1})


def test_atr_constant_range():
    index = pd.date_range("2020-01-01", periods=20, freq="h", tz="UTC")
    high = pd.Series(110.0, index=index)
    low = pd.Series(100.0, index=index)
    close = pd.Series(105.0, index=index)
    atr = compute_atr(high, low, close, length=14)
    assert abs(atr.iloc[-1] - 10.0) < 1e-6
