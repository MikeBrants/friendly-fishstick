"""Tests for new indicators (ADX filter, Regime filter) - Alex R&D Plan."""

import pandas as pd
import numpy as np
import pytest


def make_sample_data(n_bars: int = 500) -> pd.DataFrame:
    """Create sample OHLCV data for testing."""
    np.random.seed(42)
    
    # Generate realistic price data
    returns = np.random.normal(0.0001, 0.02, n_bars)
    close = 100 * np.cumprod(1 + returns)
    
    # Generate OHLC from close
    high = close * (1 + np.abs(np.random.normal(0, 0.005, n_bars)))
    low = close * (1 - np.abs(np.random.normal(0, 0.005, n_bars)))
    open_price = np.roll(close, 1)
    open_price[0] = close[0]
    
    volume = np.random.uniform(1000, 10000, n_bars)
    
    dates = pd.date_range(start="2024-01-01", periods=n_bars, freq="1h")
    
    return pd.DataFrame({
        "open": open_price,
        "high": high,
        "low": low,
        "close": close,
        "volume": volume,
    }, index=dates)


class TestADXFilter:
    """Tests for ADX trend strength filter."""
    
    def test_compute_adx_returns_series(self):
        """ADX should return a pandas Series."""
        from crypto_backtest.indicators.adx_filter import compute_adx
        
        data = make_sample_data()
        adx = compute_adx(data["high"], data["low"], data["close"], period=14)
        
        assert isinstance(adx, pd.Series)
        assert len(adx) == len(data)
    
    def test_compute_adx_values_in_range(self):
        """ADX values should be between 0 and 100."""
        from crypto_backtest.indicators.adx_filter import compute_adx
        
        data = make_sample_data()
        adx = compute_adx(data["high"], data["low"], data["close"], period=14)
        
        # After warmup period, ADX should be in valid range
        valid_adx = adx.dropna()
        assert (valid_adx >= 0).all(), "ADX should be >= 0"
        assert (valid_adx <= 100).all(), "ADX should be <= 100"
    
    def test_adx_filter_reduces_signals(self):
        """ADX filter should reduce or maintain signal count."""
        from crypto_backtest.indicators.adx_filter import adx_filter
        
        data = make_sample_data(n_bars=1000)
        
        # Create some random signals
        np.random.seed(123)
        signals = pd.Series(
            np.random.choice([-1, 0, 1], size=len(data), p=[0.1, 0.8, 0.1]),
            index=data.index
        )
        
        filtered = adx_filter(
            data["high"], data["low"], data["close"],
            signals, period=14, threshold=25
        )
        
        # Filtered signals should be <= original signals
        original_signal_count = (signals != 0).sum()
        filtered_signal_count = (filtered != 0).sum()
        
        assert filtered_signal_count <= original_signal_count
    
    def test_adx_filter_preserves_zero_signals(self):
        """Zero signals should remain zero after filtering."""
        from crypto_backtest.indicators.adx_filter import adx_filter
        
        data = make_sample_data()
        signals = pd.Series(0, index=data.index)  # All zeros
        
        filtered = adx_filter(
            data["high"], data["low"], data["close"],
            signals, period=14, threshold=25
        )
        
        assert (filtered == 0).all()
    
    def test_compute_adx_invalid_period_raises(self):
        """ADX with period < 1 should raise ValueError."""
        from crypto_backtest.indicators.adx_filter import compute_adx
        
        data = make_sample_data()
        
        with pytest.raises(ValueError):
            compute_adx(data["high"], data["low"], data["close"], period=0)


class TestRegimeFilter:
    """Tests for regime-based trade filters."""
    
    def test_filter_recovery_regime_returns_series(self):
        """filter_recovery_regime should return a pandas Series."""
        from crypto_backtest.indicators.regime_filter import filter_recovery_regime
        
        data = make_sample_data(n_bars=500)
        signals = pd.Series(
            np.random.choice([-1, 0, 1], size=len(data)),
            index=data.index
        )
        
        filtered = filter_recovery_regime(data, signals)
        
        assert isinstance(filtered, pd.Series)
        assert len(filtered) == len(data)
    
    def test_filter_regimes_with_exclude(self):
        """filter_regimes with exclude should filter specified regimes."""
        from crypto_backtest.indicators.regime_filter import filter_regimes
        
        data = make_sample_data(n_bars=500)
        signals = pd.Series(1, index=data.index)  # All longs
        
        filtered = filter_regimes(data, signals, exclude=["RECOVERY", "CRASH"])
        
        # Some signals may be filtered
        assert isinstance(filtered, pd.Series)
        assert len(filtered) == len(signals)
    
    def test_filter_regimes_with_include_only(self):
        """filter_regimes with include_only should only allow specified regimes."""
        from crypto_backtest.indicators.regime_filter import filter_regimes
        
        data = make_sample_data(n_bars=500)
        signals = pd.Series(1, index=data.index)
        
        filtered = filter_regimes(data, signals, include_only=["BULL", "SIDEWAYS"])
        
        assert isinstance(filtered, pd.Series)
    
    def test_apply_regime_filter_config_none(self):
        """Config 'none' should not filter any signals."""
        from crypto_backtest.indicators.regime_filter import apply_regime_filter_config
        
        data = make_sample_data(n_bars=500)
        signals = pd.Series(1, index=data.index)
        
        filtered = apply_regime_filter_config(data, signals, config_name="none")
        
        # 'none' config should preserve all signals
        assert (filtered == signals).all()
    
    def test_apply_regime_filter_config_invalid_raises(self):
        """Invalid config name should raise ValueError."""
        from crypto_backtest.indicators.regime_filter import apply_regime_filter_config
        
        data = make_sample_data()
        signals = pd.Series(1, index=data.index)
        
        with pytest.raises(ValueError):
            apply_regime_filter_config(data, signals, config_name="invalid_config")


class TestVolatilityProfiles:
    """Tests for volatility-based parameter ranges."""
    
    def test_get_volatility_profile_meme_coins(self):
        """Meme coins should be classified as HIGH_VOL."""
        from crypto_backtest.config.scan_assets import get_volatility_profile
        
        assert get_volatility_profile("SHIB") == "HIGH_VOL"
        assert get_volatility_profile("DOGE") == "HIGH_VOL"
        assert get_volatility_profile("PEPE") == "HIGH_VOL"
    
    def test_get_volatility_profile_majors(self):
        """Major coins should be classified as LOW_VOL."""
        from crypto_backtest.config.scan_assets import get_volatility_profile
        
        assert get_volatility_profile("BTC") == "LOW_VOL"
        assert get_volatility_profile("ETH") == "LOW_VOL"
    
    def test_get_volatility_profile_unknown_defaults_med(self):
        """Unknown assets should default to MED_VOL."""
        from crypto_backtest.config.scan_assets import get_volatility_profile
        
        assert get_volatility_profile("UNKNOWN_ASSET_XYZ") == "MED_VOL"
    
    def test_get_atr_search_space_for_asset(self):
        """get_atr_search_space_for_asset should return appropriate ranges."""
        from crypto_backtest.config.scan_assets import (
            get_atr_search_space_for_asset,
            ATR_SEARCH_SPACE_HIGH_VOL,
            ATR_SEARCH_SPACE_LOW_VOL,
        )
        
        btc_space = get_atr_search_space_for_asset("BTC")
        shib_space = get_atr_search_space_for_asset("SHIB")
        
        assert btc_space == ATR_SEARCH_SPACE_LOW_VOL
        assert shib_space == ATR_SEARCH_SPACE_HIGH_VOL
    
    def test_is_meme_coin(self):
        """is_meme_coin should correctly identify meme coins."""
        from crypto_backtest.config.scan_assets import is_meme_coin
        
        assert is_meme_coin("SHIB") is True
        assert is_meme_coin("DOGE") is True
        assert is_meme_coin("BTC") is False
        assert is_meme_coin("ETH") is False
