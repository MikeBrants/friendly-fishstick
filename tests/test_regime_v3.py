"""Tests for regime analysis v3."""

import numpy as np
import pandas as pd
import pytest

from crypto_backtest.analysis.regime_v3 import (
    TrendRegime,
    VolatilityRegime,
    CryptoRegime,
    compute_regime_features,
    classify_trend_regime,
    classify_volatility_regime,
    classify_crypto_regime,
    CryptoRegimeAnalyzer,
    HMMRegimeDetector,
    add_regime_filter_to_signals,
    regime_aware_position_sizing,
    classify_regimes_v2,
)


# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture
def sample_ohlcv():
    """Generate sample OHLCV data for testing."""
    np.random.seed(42)
    n = 500

    # Generate trending price with noise
    trend = np.linspace(100, 150, n) + np.cumsum(np.random.randn(n) * 0.5)
    noise = np.random.randn(n) * 2

    close = trend + noise
    high = close + np.abs(np.random.randn(n) * 1.5)
    low = close - np.abs(np.random.randn(n) * 1.5)
    open_ = close.copy()
    open_[1:] = close[:-1]
    volume = np.random.randint(1000, 10000, n).astype(float)

    df = pd.DataFrame(
        {
            "open": open_,
            "high": high,
            "low": low,
            "close": close,
            "volume": volume,
        },
        index=pd.date_range("2024-01-01", periods=n, freq="1H"),
    )
    return df


@pytest.fixture
def bear_market_ohlcv():
    """Generate bear market data."""
    np.random.seed(123)
    n = 500

    # Declining trend
    trend = np.linspace(150, 80, n) + np.cumsum(np.random.randn(n) * 0.3)
    noise = np.random.randn(n) * 2

    close = trend + noise
    high = close + np.abs(np.random.randn(n) * 2)
    low = close - np.abs(np.random.randn(n) * 2)
    open_ = close.copy()
    open_[1:] = close[:-1]
    volume = np.random.randint(1000, 15000, n).astype(float)

    df = pd.DataFrame(
        {
            "open": open_,
            "high": high,
            "low": low,
            "close": close,
            "volume": volume,
        },
        index=pd.date_range("2024-01-01", periods=n, freq="1H"),
    )
    return df


# ============================================================================
# TEST: FEATURE COMPUTATION
# ============================================================================


def test_compute_regime_features_shape(sample_ohlcv):
    """Test feature computation returns correct shape."""
    features = compute_regime_features(sample_ohlcv)

    assert len(features) == len(sample_ohlcv)
    assert "atr_14" in features.columns
    assert "rsi_14" in features.columns
    assert "momentum_composite" in features.columns
    assert "trend_composite" in features.columns


def test_compute_regime_features_no_lookahead(sample_ohlcv):
    """Test that features don't look ahead (shifted properly)."""
    features = compute_regime_features(sample_ohlcv)

    # First 200+ rows should have NaN for features requiring long lookback
    # But RSI/ATR with 14 period should have values after ~15 rows
    assert features["rsi_14"].iloc[:14].isna().any()
    assert features["rsi_14"].iloc[50:].notna().any()


def test_feature_bounds(sample_ohlcv):
    """Test that computed features are within expected bounds."""
    features = compute_regime_features(sample_ohlcv)

    # RSI should be 0-100
    valid_rsi = features["rsi_14"].dropna()
    assert (valid_rsi >= 0).all() and (valid_rsi <= 100).all()

    # Momentum composite should be -1 to 1
    valid_momentum = features["momentum_composite"].dropna()
    assert (valid_momentum >= -1).all() and (valid_momentum <= 1).all()

    # Vol percentile should be 0 to 1
    valid_vol = features["vol_percentile"].dropna()
    assert (valid_vol >= 0).all() and (valid_vol <= 1).all()


# ============================================================================
# TEST: TREND REGIME CLASSIFICATION
# ============================================================================


def test_classify_trend_regime_returns_valid_regimes(sample_ohlcv):
    """Test trend classification returns valid regime labels."""
    features = compute_regime_features(sample_ohlcv)
    regimes, confidence = classify_trend_regime(features)

    valid_regimes = {r.value for r in TrendRegime}
    assert set(regimes.dropna().unique()).issubset(valid_regimes)


def test_classify_trend_regime_confidence_bounds(sample_ohlcv):
    """Test confidence scores are within 0-1."""
    features = compute_regime_features(sample_ohlcv)
    _, confidence = classify_trend_regime(features)

    valid_conf = confidence.dropna()
    assert (valid_conf >= 0).all() and (valid_conf <= 1).all()


def test_bull_market_mostly_bullish(sample_ohlcv):
    """Test that uptrending data is classified as bullish."""
    features = compute_regime_features(sample_ohlcv)
    regimes, _ = classify_trend_regime(features)

    # After warmup, should have significant bullish classification
    valid_regimes = regimes.iloc[250:]
    bullish_pct = (
        valid_regimes.isin([TrendRegime.STRONG_BULL.value, TrendRegime.WEAK_BULL.value]).mean()
    )
    assert bullish_pct > 0.3, f"Expected >30% bullish in uptrend, got {bullish_pct*100:.1f}%"


def test_bear_market_mostly_bearish(bear_market_ohlcv):
    """Test that downtrending data is classified as bearish."""
    features = compute_regime_features(bear_market_ohlcv)
    regimes, _ = classify_trend_regime(features)

    # After warmup, should have significant bearish classification
    valid_regimes = regimes.iloc[250:]
    bearish_pct = (
        valid_regimes.isin([TrendRegime.STRONG_BEAR.value, TrendRegime.WEAK_BEAR.value]).mean()
    )
    assert bearish_pct > 0.3, f"Expected >30% bearish in downtrend, got {bearish_pct*100:.1f}%"


# ============================================================================
# TEST: VOLATILITY REGIME CLASSIFICATION
# ============================================================================


def test_classify_volatility_regime_returns_valid_regimes(sample_ohlcv):
    """Test volatility classification returns valid regime labels."""
    features = compute_regime_features(sample_ohlcv)
    regimes, vol_pct = classify_volatility_regime(features)

    valid_regimes = {r.value for r in VolatilityRegime}
    assert set(regimes.dropna().unique()).issubset(valid_regimes)


def test_volatility_percentile_distribution(sample_ohlcv):
    """Test vol percentile is reasonably distributed."""
    features = compute_regime_features(sample_ohlcv)
    _, vol_pct = classify_volatility_regime(features)

    # Should have values across the range
    valid_pct = vol_pct.dropna()
    assert valid_pct.min() < 0.3
    assert valid_pct.max() > 0.7


# ============================================================================
# TEST: CRYPTO REGIME CLASSIFICATION
# ============================================================================


def test_classify_crypto_regime_returns_valid_regimes(sample_ohlcv):
    """Test crypto classification returns valid regime labels."""
    features = compute_regime_features(sample_ohlcv)
    regimes, confidence = classify_crypto_regime(features)

    valid_regimes = {r.value for r in CryptoRegime}
    assert set(regimes.dropna().unique()).issubset(valid_regimes)


# ============================================================================
# TEST: HMM DETECTOR
# ============================================================================


def test_hmm_detector_fit(sample_ohlcv):
    """Test HMM detector can fit on data."""
    features = compute_regime_features(sample_ohlcv)
    detector = HMMRegimeDetector(n_regimes=3)

    # Should not raise
    detector.fit(features)

    # May or may not be fitted depending on library availability
    # Just check it doesn't crash


def test_hmm_detector_predict_proba(sample_ohlcv):
    """Test HMM detector returns valid probabilities."""
    features = compute_regime_features(sample_ohlcv)
    detector = HMMRegimeDetector(n_regimes=3)
    detector.fit(features)

    proba = detector.predict_proba(features)

    assert len(proba) == len(features)
    assert "predicted_regime" in proba.columns


# ============================================================================
# TEST: MAIN ANALYZER
# ============================================================================


def test_crypto_regime_analyzer_full_pipeline(sample_ohlcv):
    """Test complete analysis pipeline."""
    analyzer = CryptoRegimeAnalyzer(use_hmm=True, n_hmm_regimes=3, lookback=200)
    regimes = analyzer.fit_and_classify(sample_ohlcv)

    # Check output structure
    assert len(regimes) == len(sample_ohlcv)
    assert "trend_regime" in regimes.columns
    assert "vol_regime" in regimes.columns
    assert "crypto_regime" in regimes.columns
    assert "favorable_for_long" in regimes.columns
    assert "composite_score" in regimes.columns


def test_crypto_regime_analyzer_stats(sample_ohlcv):
    """Test stats generation."""
    analyzer = CryptoRegimeAnalyzer(use_hmm=False, lookback=200)
    analyzer.fit_and_classify(sample_ohlcv)
    stats = analyzer.get_regime_stats()

    assert "trend_distribution" in stats
    assert "vol_distribution" in stats
    assert "crypto_distribution" in stats
    assert "pct_favorable_long" in stats
    assert 0 <= stats["pct_favorable_long"] <= 100


def test_favorable_for_long_logic(sample_ohlcv):
    """Test favorable_for_long flag logic."""
    analyzer = CryptoRegimeAnalyzer(use_hmm=False, lookback=200)
    regimes = analyzer.fit_and_classify(sample_ohlcv)

    # In uptrend, should have some favorable periods
    favorable_pct = regimes["favorable_for_long"].mean() * 100
    assert favorable_pct > 10, f"Expected some favorable periods, got {favorable_pct:.1f}%"


# ============================================================================
# TEST: SIGNAL FILTERING
# ============================================================================


def test_add_regime_filter_moderate(sample_ohlcv):
    """Test signal filtering in moderate mode."""
    analyzer = CryptoRegimeAnalyzer(use_hmm=False, lookback=200)
    regimes = analyzer.fit_and_classify(sample_ohlcv)

    # Create mock signals
    signals = pd.DataFrame(
        {"entry_long": True, "entry_signal": 1}, index=sample_ohlcv.index
    )

    filtered = add_regime_filter_to_signals(signals, regimes, filter_mode="moderate")

    # Should filter some signals
    original_signals = signals["entry_long"].sum()
    filtered_signals = filtered["entry_long"].sum()
    assert filtered_signals <= original_signals


def test_add_regime_filter_permissive(sample_ohlcv):
    """Test signal filtering in permissive mode."""
    analyzer = CryptoRegimeAnalyzer(use_hmm=False, lookback=200)
    regimes = analyzer.fit_and_classify(sample_ohlcv)

    signals = pd.DataFrame(
        {"entry_long": True, "entry_signal": 1}, index=sample_ohlcv.index
    )

    filtered = add_regime_filter_to_signals(signals, regimes, filter_mode="permissive")

    # Permissive should filter less than moderate
    filtered_mod = add_regime_filter_to_signals(signals, regimes, filter_mode="moderate")

    assert filtered["entry_long"].sum() >= filtered_mod["entry_long"].sum()


# ============================================================================
# TEST: POSITION SIZING
# ============================================================================


def test_regime_aware_position_sizing_compressed():
    """Test position sizing increases in compressed volatility."""
    regime_row = pd.Series(
        {
            "vol_regime": VolatilityRegime.COMPRESSED.value,
            "trend_confidence": 0.8,
            "regime_stability": 15,
        }
    )

    size = regime_aware_position_sizing(0.5, regime_row)

    # Compressed vol + high confidence + stability should increase size
    assert size > 0.5


def test_regime_aware_position_sizing_extreme():
    """Test position sizing decreases in extreme volatility."""
    regime_row = pd.Series(
        {
            "vol_regime": VolatilityRegime.EXTREME.value,
            "trend_confidence": 0.3,
            "regime_stability": 2,
        }
    )

    size = regime_aware_position_sizing(0.5, regime_row)

    # Extreme vol + low confidence should decrease size
    assert size < 0.5


def test_position_sizing_bounds():
    """Test position sizing respects min/max bounds."""
    regime_row = pd.Series(
        {
            "vol_regime": VolatilityRegime.EXTREME.value,
            "trend_confidence": 0.1,
            "regime_stability": 1,
        }
    )

    size = regime_aware_position_sizing(0.5, regime_row, min_size=0.2, max_size=1.5)

    assert size >= 0.2
    assert size <= 1.5


# ============================================================================
# TEST: LEGACY COMPATIBILITY
# ============================================================================


def test_classify_regimes_v2_backward_compatible(sample_ohlcv):
    """Test v2 function returns expected regime labels."""
    regimes = classify_regimes_v2(sample_ohlcv)

    # Should return v2 regime labels
    valid_v2 = {"CRASH", "HIGH_VOL", "BEAR", "BULL", "SIDEWAYS", "RECOVERY", "OTHER"}
    actual_regimes = set(regimes.dropna().unique())
    assert actual_regimes.issubset(valid_v2), f"Got unexpected regimes: {actual_regimes - valid_v2}"


def test_classify_regimes_v2_same_length(sample_ohlcv):
    """Test v2 returns same length as input."""
    regimes = classify_regimes_v2(sample_ohlcv)
    assert len(regimes) == len(sample_ohlcv)


# ============================================================================
# TEST: EDGE CASES
# ============================================================================


def test_small_dataset():
    """Test handling of small datasets."""
    np.random.seed(42)
    n = 50  # Very small

    df = pd.DataFrame(
        {
            "open": np.random.randn(n) * 10 + 100,
            "high": np.random.randn(n) * 10 + 102,
            "low": np.random.randn(n) * 10 + 98,
            "close": np.random.randn(n) * 10 + 100,
            "volume": np.random.randint(1000, 5000, n),
        },
        index=pd.date_range("2024-01-01", periods=n, freq="1H"),
    )

    # Should not crash
    analyzer = CryptoRegimeAnalyzer(use_hmm=True, lookback=50)
    regimes = analyzer.fit_and_classify(df)

    assert len(regimes) == n


def test_missing_volume_column():
    """Test handling when volume is missing."""
    np.random.seed(42)
    n = 200

    df = pd.DataFrame(
        {
            "open": np.random.randn(n) * 10 + 100,
            "high": np.random.randn(n) * 10 + 102,
            "low": np.random.randn(n) * 10 + 98,
            "close": np.random.randn(n) * 10 + 100,
            # No volume column
        },
        index=pd.date_range("2024-01-01", periods=n, freq="1H"),
    )

    # Should not crash
    features = compute_regime_features(df)
    assert "volume_ratio" in features.columns
