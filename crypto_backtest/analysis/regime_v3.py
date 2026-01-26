"""Crypto Regime Analysis v3 - Multi-Layer Detection

Combines: HMM probabilistic, GMM clustering, Rule-based ensemble
Optimized for 1H timeframe crypto backtesting

Author: Alex (Lead Quant)
Date: 2026-01-26
"""

from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Tuple, Dict, List
import numpy as np
import pandas as pd
from scipy import stats

from crypto_backtest.indicators.atr import compute_atr

# ============================================================================
# PART 1: REGIME DEFINITIONS
# ============================================================================


class TrendRegime(Enum):
    """Directional market state"""

    STRONG_BULL = "STRONG_BULL"  # ADX>25, price>SMA, momentum positive
    WEAK_BULL = "WEAK_BULL"  # Price>SMA but low momentum
    SIDEWAYS = "SIDEWAYS"  # ADX<20, range-bound
    WEAK_BEAR = "WEAK_BEAR"  # Price<SMA but low momentum
    STRONG_BEAR = "STRONG_BEAR"  # ADX>25, price<SMA, momentum negative
    REVERSAL = "REVERSAL"  # Divergence detected, potential turn


class VolatilityRegime(Enum):
    """Volatility state classification"""

    COMPRESSED = "COMPRESSED"  # ATR < 50th percentile, squeeze building
    NORMAL = "NORMAL"  # ATR 50-75th percentile
    ELEVATED = "ELEVATED"  # ATR 75-90th percentile
    EXTREME = "EXTREME"  # ATR > 90th percentile OR drawdown >10%


class CryptoRegime(Enum):
    """Crypto-specific market conditions (Wyckoff-inspired)"""

    ACCUMULATION = "ACCUMULATION"  # Low vol, higher lows, volume declining
    MARKUP = "MARKUP"  # Breakout, volume surge, strong trend
    DISTRIBUTION = "DISTRIBUTION"  # High vol, lower highs, volume high
    MARKDOWN = "MARKDOWN"  # Breakdown, panic selling
    CAPITULATION = "CAPITULATION"  # Extreme drawdown >20%, vol spike
    RECOVERY = "RECOVERY"  # Post-capitulation bounce


@dataclass
class RegimeState:
    """Complete regime classification with confidence"""

    timestamp: pd.Timestamp
    trend: TrendRegime
    trend_confidence: float  # 0-1 probability
    volatility: VolatilityRegime
    vol_percentile: float  # Current vol vs historical
    crypto: CryptoRegime
    crypto_confidence: float
    composite_score: float  # -1 (max bearish) to +1 (max bullish)
    regime_stability: float  # Bars in current regime

    def is_favorable_for_long(self) -> bool:
        """Check if regime favors long entries (Ichimoku+ATR strategy)"""
        return (
            self.trend
            in [TrendRegime.STRONG_BULL, TrendRegime.WEAK_BULL, TrendRegime.REVERSAL]
            and self.volatility != VolatilityRegime.EXTREME
            and self.crypto
            not in [
                CryptoRegime.DISTRIBUTION,
                CryptoRegime.MARKDOWN,
                CryptoRegime.CAPITULATION,
            ]
        )


# Legacy regime names for backward compatibility
REGIMES_V2 = ("CRASH", "HIGH_VOL", "BEAR", "BULL", "SIDEWAYS", "RECOVERY", "OTHER")
REGIMES_V3 = (
    "STRONG_BULL",
    "WEAK_BULL",
    "SIDEWAYS",
    "WEAK_BEAR",
    "STRONG_BEAR",
    "REVERSAL",
)


# ============================================================================
# PART 2: FEATURE ENGINEERING FOR REGIME DETECTION
# ============================================================================


def compute_regime_features(df: pd.DataFrame, lookback: int = 200) -> pd.DataFrame:
    """
    Compute all features needed for regime classification.
    Uses .shift(1) to prevent look-ahead bias.

    Args:
        df: OHLCV DataFrame with columns [open, high, low, close, volume]
        lookback: Rolling window for percentile calculations

    Returns:
        DataFrame with regime features
    """
    close = df["close"]
    high = df["high"]
    low = df["low"]
    volume = df["volume"] if "volume" in df.columns else pd.Series(1, index=df.index)

    features = pd.DataFrame(index=df.index)

    # === 1. RETURNS & VOLATILITY ===
    features["returns"] = close.pct_change()
    features["log_returns"] = np.log(close / close.shift(1))

    # ATR-based volatility (no look-ahead)
    tr = pd.concat(
        [
            high - low,
            (high - close.shift(1)).abs(),
            (low - close.shift(1)).abs(),
        ],
        axis=1,
    ).max(axis=1)
    features["atr_14"] = tr.rolling(14).mean().shift(1)
    features["atr_50"] = tr.rolling(50).mean().shift(1)
    features["atr_ratio"] = features["atr_14"] / features["atr_50"]

    # Realized volatility (annualized for 1H bars)
    features["realized_vol_20"] = (
        features["log_returns"].rolling(20).std().shift(1) * np.sqrt(252 * 24)
    )
    features["realized_vol_50"] = (
        features["log_returns"].rolling(50).std().shift(1) * np.sqrt(252 * 24)
    )

    # Volatility percentile (crypto-adaptive)
    features["vol_percentile"] = (
        features["atr_14"]
        .rolling(lookback)
        .apply(
            lambda x: stats.percentileofscore(x.dropna(), x.iloc[-1]) / 100
            if len(x.dropna()) > 10
            else 0.5,
            raw=False,
        )
        .shift(1)
    )

    # === 2. TREND INDICATORS ===
    # SMAs
    features["sma_20"] = close.rolling(20).mean().shift(1)
    features["sma_50"] = close.rolling(50).mean().shift(1)
    features["sma_200"] = close.rolling(200).mean().shift(1)

    # Trend position (-1 to +1)
    features["price_vs_sma20"] = (close.shift(1) - features["sma_20"]) / features[
        "sma_20"
    ]
    features["price_vs_sma50"] = (close.shift(1) - features["sma_50"]) / features[
        "sma_50"
    ]
    features["sma_alignment"] = (
        (features["sma_20"] > features["sma_50"]).astype(int)
        + (features["sma_50"] > features["sma_200"]).astype(int)
    ) / 2  # 0 = bear alignment, 1 = bull alignment

    # ADX for trend strength
    features["adx"] = _compute_adx(high, low, close, 14).shift(1)
    di_plus, di_minus = _compute_di(high, low, close, 14)
    features["di_plus"] = di_plus.shift(1)
    features["di_minus"] = di_minus.shift(1)

    # === 3. MOMENTUM INDICATORS ===
    # RSI
    features["rsi_14"] = _compute_rsi(close, 14).shift(1)
    features["rsi_deviation"] = features["rsi_14"] - 50  # Centered around 0

    # MACD
    ema_12 = close.ewm(span=12, adjust=False).mean()
    ema_26 = close.ewm(span=26, adjust=False).mean()
    features["macd"] = (ema_12 - ema_26).shift(1)
    features["macd_signal"] = features["macd"].ewm(span=9, adjust=False).mean()
    features["macd_hist"] = features["macd"] - features["macd_signal"]

    # Rate of change
    features["roc_10"] = ((close / close.shift(10)) - 1).shift(1)
    features["roc_20"] = ((close / close.shift(20)) - 1).shift(1)

    # === 4. CRYPTO-SPECIFIC METRICS ===
    # Drawdown from rolling high
    rolling_max = close.rolling(50).max().shift(1)
    features["drawdown_50"] = (close.shift(1) - rolling_max) / rolling_max

    # Distance from rolling low
    rolling_min = close.rolling(50).min().shift(1)
    features["from_low_50"] = (close.shift(1) - rolling_min) / rolling_min

    # Volume analysis
    features["volume_sma_20"] = volume.rolling(20).mean().shift(1)
    features["volume_ratio"] = (volume.shift(1) / features["volume_sma_20"]).clip(0, 5)

    # Price range (squeeze detection)
    features["range_20"] = (
        (high.rolling(20).max() - low.rolling(20).min()) / close
    ).shift(1)
    features["range_percentile"] = (
        features["range_20"]
        .rolling(lookback)
        .apply(
            lambda x: stats.percentileofscore(x.dropna(), x.iloc[-1]) / 100
            if len(x.dropna()) > 10
            else 0.5,
            raw=False,
        )
        .shift(1)
    )

    # === 5. DERIVED COMPOSITE FEATURES ===
    # Momentum composite (-1 to +1)
    features["momentum_composite"] = (
        features["rsi_deviation"] / 50 * 0.3  # RSI component
        + np.tanh(features["macd_hist"] * 100) * 0.3  # MACD component (scaled)
        + np.tanh(features["roc_20"] * 10) * 0.4  # ROC component
    ).clip(-1, 1)

    # Trend composite (-1 to +1)
    features["trend_composite"] = (
        features["sma_alignment"] * 2
        - 1  # SMA alignment (-1 to +1)
        + np.tanh(features["price_vs_sma50"] * 10)  # Price vs SMA50
    ).clip(-1, 1) / 2

    return features


# ============================================================================
# PART 3: HIDDEN MARKOV MODEL REGIME DETECTION
# ============================================================================


class HMMRegimeDetector:
    """
    Hidden Markov Model for probabilistic regime detection.
    Uses hmmlearn library or fallback to GMM implementation.
    """

    def __init__(self, n_regimes: int = 3, random_state: int = 42):
        self.n_regimes = n_regimes
        self.random_state = random_state
        self.model = None
        self.is_fitted = False
        self._use_hmm = True

    def fit(self, features: pd.DataFrame, feature_cols: List[str] = None):
        """
        Fit HMM on feature matrix.

        Args:
            features: DataFrame with regime features
            feature_cols: Columns to use (default: returns + volatility)
        """
        if feature_cols is None:
            feature_cols = ["log_returns", "realized_vol_20", "momentum_composite"]

        # Filter to available columns
        available_cols = [c for c in feature_cols if c in features.columns]
        if len(available_cols) < 2:
            available_cols = ["log_returns", "realized_vol_20"]

        X = features[available_cols].dropna().values

        if len(X) < 50:
            self._use_hmm = False
            self.is_fitted = False
            return

        try:
            from hmmlearn.hmm import GaussianHMM

            self.model = GaussianHMM(
                n_components=self.n_regimes,
                covariance_type="full",
                n_iter=200,
                random_state=self.random_state,
            )
            self.model.fit(X)
            self.is_fitted = True
            self._use_hmm = True
            self._feature_cols = available_cols
        except ImportError:
            # Fallback: use GMM-based approximation
            self._fit_gmm_fallback(X, available_cols)
        except Exception as e:
            print(f"HMM fitting failed: {e}, using GMM fallback")
            self._fit_gmm_fallback(X, available_cols)

    def _fit_gmm_fallback(self, X: np.ndarray, feature_cols: List[str]):
        """Fallback GMM if hmmlearn unavailable"""
        try:
            from sklearn.mixture import GaussianMixture

            self.model = GaussianMixture(
                n_components=self.n_regimes,
                covariance_type="full",
                n_init=5,
                random_state=self.random_state,
            )
            self.model.fit(X)
            self.is_fitted = True
            self._use_hmm = False
            self._feature_cols = feature_cols
        except ImportError:
            self.is_fitted = False
            self._use_hmm = False

    def predict_proba(
        self, features: pd.DataFrame, feature_cols: List[str] = None
    ) -> pd.DataFrame:
        """
        Get regime probabilities for each timestep.

        Returns:
            DataFrame with columns [regime_0_prob, regime_1_prob, ..., predicted_regime]
        """
        if not self.is_fitted:
            # Return default values
            result = pd.DataFrame(index=features.index)
            for i in range(self.n_regimes):
                result[f"regime_{i}_prob"] = 1.0 / self.n_regimes
            result["predicted_regime"] = 0
            return result

        if feature_cols is None:
            feature_cols = getattr(
                self, "_feature_cols", ["log_returns", "realized_vol_20"]
            )

        X = features[feature_cols].values
        valid_mask = ~np.isnan(X).any(axis=1)

        proba = np.full((len(X), self.n_regimes), 1.0 / self.n_regimes)

        if valid_mask.sum() > 0:
            try:
                if self._use_hmm and hasattr(self.model, "score_samples"):
                    # HMM returns posteriors via score_samples
                    _, posteriors = self.model.score_samples(X[valid_mask])
                    proba[valid_mask] = posteriors
                elif hasattr(self.model, "predict_proba"):
                    proba[valid_mask] = self.model.predict_proba(X[valid_mask])
            except Exception:
                pass

        result = pd.DataFrame(
            proba,
            index=features.index,
            columns=[f"regime_{i}_prob" for i in range(self.n_regimes)],
        )
        result["predicted_regime"] = proba.argmax(axis=1)
        result.loc[~valid_mask, "predicted_regime"] = -1

        return result


# ============================================================================
# PART 4: RULE-BASED REGIME CLASSIFICATION (ENHANCED)
# ============================================================================


def classify_trend_regime(features: pd.DataFrame) -> Tuple[pd.Series, pd.Series]:
    """
    Classify trend regime with confidence scores.

    Returns:
        Tuple of (regime_series, confidence_series)
    """
    regimes = pd.Series(index=features.index, dtype=object)
    confidence = pd.Series(index=features.index, dtype=float)

    adx = features["adx"].fillna(15)
    di_plus = features["di_plus"].fillna(25)
    di_minus = features["di_minus"].fillna(25)
    price_vs_sma = features["price_vs_sma50"].fillna(0)
    momentum = features["momentum_composite"].fillna(0)
    rsi = features["rsi_14"].fillna(50)

    # Strong Bull: ADX>25, DI+>DI-, price above SMA, momentum positive
    strong_bull = (
        (adx > 25) & (di_plus > di_minus) & (price_vs_sma > 0.02) & (momentum > 0.2)
    )

    # Strong Bear: ADX>25, DI->DI+, price below SMA, momentum negative
    strong_bear = (
        (adx > 25) & (di_minus > di_plus) & (price_vs_sma < -0.02) & (momentum < -0.2)
    )

    # Weak Bull: Price above SMA but low momentum/ADX
    weak_bull = (price_vs_sma > 0) & (momentum > 0) & ~strong_bull

    # Weak Bear: Price below SMA but low momentum/ADX
    weak_bear = (price_vs_sma < 0) & (momentum < 0) & ~strong_bear

    # Sideways: Low ADX, price near SMA
    sideways = (adx < 20) & (price_vs_sma.abs() < 0.03)

    # Reversal: RSI divergence detection (simplified)
    oversold_reversal = (rsi < 30) & (momentum > -0.3)
    overbought_reversal = (rsi > 70) & (momentum < 0.3)
    reversal = oversold_reversal | overbought_reversal

    # Assign regimes (priority order)
    regimes[:] = TrendRegime.SIDEWAYS.value
    regimes.loc[weak_bull] = TrendRegime.WEAK_BULL.value
    regimes.loc[weak_bear] = TrendRegime.WEAK_BEAR.value
    regimes.loc[strong_bull] = TrendRegime.STRONG_BULL.value
    regimes.loc[strong_bear] = TrendRegime.STRONG_BEAR.value
    regimes.loc[reversal] = TrendRegime.REVERSAL.value

    # Confidence based on ADX and momentum alignment
    confidence = (adx / 50).clip(0, 1) * 0.5 + momentum.abs() * 0.5
    confidence = confidence.clip(0, 1)

    return regimes, confidence


def classify_volatility_regime(features: pd.DataFrame) -> Tuple[pd.Series, pd.Series]:
    """
    Classify volatility regime using percentile approach.

    Returns:
        Tuple of (regime_series, percentile_series)
    """
    vol_pct = features["vol_percentile"].fillna(0.5)
    drawdown = features["drawdown_50"].fillna(0)
    atr_ratio = features["atr_ratio"].fillna(1)

    regimes = pd.Series(index=features.index, dtype=object)

    # Extreme: >90th percentile OR significant drawdown OR ATR spike
    extreme = (vol_pct > 0.90) | (drawdown < -0.10) | (atr_ratio > 2.0)

    # Elevated: 75-90th percentile
    elevated = (vol_pct > 0.75) & ~extreme

    # Normal: 50-75th percentile
    normal = (vol_pct > 0.50) & ~elevated & ~extreme

    # Compressed: <50th percentile (squeeze)
    compressed = vol_pct <= 0.50

    regimes[:] = VolatilityRegime.NORMAL.value
    regimes.loc[compressed] = VolatilityRegime.COMPRESSED.value
    regimes.loc[elevated] = VolatilityRegime.ELEVATED.value
    regimes.loc[extreme] = VolatilityRegime.EXTREME.value

    return regimes, vol_pct


def classify_crypto_regime(features: pd.DataFrame) -> Tuple[pd.Series, pd.Series]:
    """
    Classify crypto-specific market phase (Wyckoff-inspired).

    Returns:
        Tuple of (regime_series, confidence_series)
    """
    regimes = pd.Series(index=features.index, dtype=object)
    confidence = pd.Series(index=features.index, dtype=float)

    vol_pct = features["vol_percentile"].fillna(0.5)
    drawdown = features["drawdown_50"].fillna(0)
    from_low = features["from_low_50"].fillna(0)
    volume_ratio = features["volume_ratio"].fillna(1)
    trend = features["trend_composite"].fillna(0)
    momentum = features["momentum_composite"].fillna(0)

    # Capitulation: Extreme drawdown + vol spike + negative momentum
    capitulation = (drawdown < -0.20) & (vol_pct > 0.80) & (momentum < -0.5)

    # Markdown: Strong downtrend, high volume, breaking supports
    markdown = (trend < -0.3) & (momentum < -0.2) & (drawdown < -0.05) & ~capitulation

    # Distribution: Near highs but momentum fading, volume high
    distribution = (from_low > 0.15) & (momentum < 0) & (volume_ratio > 1.2)

    # Recovery: Post-capitulation bounce
    recovery = (drawdown.shift(5).fillna(0) < -0.15) & (momentum > 0) & (trend > -0.2)

    # Markup: Strong uptrend, volume confirming
    markup = (trend > 0.3) & (momentum > 0.2) & (volume_ratio > 0.8)

    # Accumulation: Low vol, building base, volume declining
    accumulation = (vol_pct < 0.40) & (trend.abs() < 0.2) & (volume_ratio < 1.0)

    # Assign (priority order: extreme conditions first)
    regimes[:] = CryptoRegime.ACCUMULATION.value
    regimes.loc[accumulation] = CryptoRegime.ACCUMULATION.value
    regimes.loc[markup] = CryptoRegime.MARKUP.value
    regimes.loc[distribution] = CryptoRegime.DISTRIBUTION.value
    regimes.loc[markdown] = CryptoRegime.MARKDOWN.value
    regimes.loc[recovery] = CryptoRegime.RECOVERY.value
    regimes.loc[capitulation] = CryptoRegime.CAPITULATION.value

    # Confidence based on signal clarity
    confidence = (
        momentum.abs() * 0.4 + (vol_pct - 0.5).abs() * 0.3 + trend.abs() * 0.3
    ).clip(0, 1)

    return regimes, confidence


# ============================================================================
# PART 5: ENSEMBLE REGIME CLASSIFIER
# ============================================================================


class CryptoRegimeAnalyzer:
    """
    Main class combining all regime detection methods.
    Provides unified interface for backtesting integration.
    """

    def __init__(
        self, use_hmm: bool = True, n_hmm_regimes: int = 3, lookback: int = 200
    ):
        self.use_hmm = use_hmm
        self.n_hmm_regimes = n_hmm_regimes
        self.lookback = lookback
        self.hmm_detector = (
            HMMRegimeDetector(n_regimes=n_hmm_regimes) if use_hmm else None
        )
        self.features_df = None
        self.regimes_df = None

    def fit_and_classify(self, ohlcv: pd.DataFrame) -> pd.DataFrame:
        """
        Complete regime analysis pipeline.

        Args:
            ohlcv: DataFrame with [open, high, low, close, volume] columns

        Returns:
            DataFrame with all regime classifications and features
        """
        # 1. Compute features
        self.features_df = compute_regime_features(ohlcv, lookback=self.lookback)

        # 2. Fit HMM if enabled
        if self.use_hmm and len(self.features_df.dropna()) > 100:
            train_end = int(len(self.features_df) * 0.7)  # Train on first 70%
            train_data = self.features_df.iloc[:train_end]
            self.hmm_detector.fit(train_data)
            hmm_proba = self.hmm_detector.predict_proba(self.features_df)
        else:
            hmm_proba = pd.DataFrame(index=self.features_df.index)
            hmm_proba["predicted_regime"] = -1

        # 3. Rule-based classifications
        trend_regime, trend_conf = classify_trend_regime(self.features_df)
        vol_regime, vol_pct = classify_volatility_regime(self.features_df)
        crypto_regime, crypto_conf = classify_crypto_regime(self.features_df)

        # 4. Combine results
        self.regimes_df = pd.DataFrame(
            {
                # Trend
                "trend_regime": trend_regime,
                "trend_confidence": trend_conf,
                # Volatility
                "vol_regime": vol_regime,
                "vol_percentile": vol_pct,
                # Crypto-specific
                "crypto_regime": crypto_regime,
                "crypto_confidence": crypto_conf,
                # HMM
                "hmm_regime": hmm_proba["predicted_regime"],
                # Composite score (-1 to +1)
                "composite_score": self._compute_composite_score(),
                # Regime stability
                "regime_stability": self._compute_stability(trend_regime),
                # Strategy filters
                "favorable_for_long": self._is_favorable_long(
                    trend_regime, vol_regime, crypto_regime
                ),
            },
            index=self.features_df.index,
        )

        # Add key features for inspection
        for col in [
            "adx",
            "rsi_14",
            "atr_ratio",
            "drawdown_50",
            "momentum_composite",
            "trend_composite",
        ]:
            if col in self.features_df.columns:
                self.regimes_df[col] = self.features_df[col]

        return self.regimes_df

    def _compute_composite_score(self) -> pd.Series:
        """Compute overall market score (-1 bearish to +1 bullish)"""
        trend = self.features_df["trend_composite"].fillna(0)
        momentum = self.features_df["momentum_composite"].fillna(0)
        vol_penalty = (
            self.features_df["vol_percentile"].fillna(0.5) - 0.5
        ) * 0.2  # High vol = slight penalty

        score = (trend * 0.4 + momentum * 0.4 - vol_penalty * 0.2).clip(-1, 1)
        return score

    def _compute_stability(self, regime_series: pd.Series) -> pd.Series:
        """Compute how many bars we've been in current regime"""
        stability = pd.Series(index=regime_series.index, dtype=float)

        changes = regime_series != regime_series.shift(1)
        groups = changes.cumsum()

        for group_id in groups.unique():
            mask = groups == group_id
            stability.loc[mask] = range(1, mask.sum() + 1)

        return stability

    def _is_favorable_long(
        self, trend: pd.Series, vol: pd.Series, crypto: pd.Series
    ) -> pd.Series:
        """Determine if current regime favors long positions"""
        favorable_trends = [TrendRegime.STRONG_BULL.value, TrendRegime.WEAK_BULL.value]
        unfavorable_crypto = [
            CryptoRegime.DISTRIBUTION.value,
            CryptoRegime.MARKDOWN.value,
            CryptoRegime.CAPITULATION.value,
        ]

        return (
            trend.isin(favorable_trends)
            & (vol != VolatilityRegime.EXTREME.value)
            & ~crypto.isin(unfavorable_crypto)
        )

    def get_regime_stats(self) -> Dict:
        """Get summary statistics of regime distribution"""
        if self.regimes_df is None:
            raise ValueError("Run fit_and_classify() first")

        stats = {
            "trend_distribution": self.regimes_df["trend_regime"]
            .value_counts(normalize=True)
            .to_dict(),
            "vol_distribution": self.regimes_df["vol_regime"]
            .value_counts(normalize=True)
            .to_dict(),
            "crypto_distribution": self.regimes_df["crypto_regime"]
            .value_counts(normalize=True)
            .to_dict(),
            "mean_stability": self.regimes_df["regime_stability"].mean(),
            "pct_favorable_long": self.regimes_df["favorable_for_long"].mean() * 100,
            "mean_composite_score": self.regimes_df["composite_score"].mean(),
        }
        return stats


# ============================================================================
# PART 6: HELPER FUNCTIONS
# ============================================================================


def _compute_rsi(close: pd.Series, period: int = 14) -> pd.Series:
    """Compute RSI indicator"""
    delta = close.diff()
    gain = delta.where(delta > 0, 0).rolling(period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(period).mean()
    rs = gain / loss.replace(0, np.inf)
    return 100 - (100 / (1 + rs))


def _compute_adx(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
    """Compute ADX indicator"""
    tr = pd.concat(
        [
            high - low,
            (high - close.shift(1)).abs(),
            (low - close.shift(1)).abs(),
        ],
        axis=1,
    ).max(axis=1)

    atr = tr.rolling(period).mean()

    up_move = high - high.shift(1)
    down_move = low.shift(1) - low

    plus_dm = up_move.where((up_move > down_move) & (up_move > 0), 0)
    minus_dm = down_move.where((down_move > up_move) & (down_move > 0), 0)

    plus_di = 100 * plus_dm.rolling(period).mean() / atr
    minus_di = 100 * minus_dm.rolling(period).mean() / atr

    dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, np.inf)
    adx = dx.rolling(period).mean()

    return adx


def _compute_di(
    high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14
) -> Tuple[pd.Series, pd.Series]:
    """Compute DI+ and DI- indicators"""
    tr = pd.concat(
        [
            high - low,
            (high - close.shift(1)).abs(),
            (low - close.shift(1)).abs(),
        ],
        axis=1,
    ).max(axis=1)

    atr = tr.rolling(period).mean()

    up_move = high - high.shift(1)
    down_move = low.shift(1) - low

    plus_dm = up_move.where((up_move > down_move) & (up_move > 0), 0)
    minus_dm = down_move.where((down_move > up_move) & (down_move > 0), 0)

    plus_di = 100 * plus_dm.rolling(period).mean() / atr
    minus_di = 100 * minus_dm.rolling(period).mean() / atr

    return plus_di, minus_di


# ============================================================================
# PART 7: INTEGRATION WITH BACKTEST
# ============================================================================


def add_regime_filter_to_signals(
    signals: pd.DataFrame, regimes: pd.DataFrame, filter_mode: str = "moderate"
) -> pd.DataFrame:
    """
    Filter trading signals based on regime classification.

    Args:
        signals: DataFrame with entry signals
        regimes: DataFrame from CryptoRegimeAnalyzer
        filter_mode: 'strict', 'moderate', 'permissive'

    Returns:
        Filtered signals DataFrame
    """
    filtered = signals.copy()

    if filter_mode == "strict":
        # Only trade in STRONG_BULL/MARKUP with normal/compressed vol
        allowed = (
            (regimes["trend_regime"] == TrendRegime.STRONG_BULL.value)
            & (regimes["crypto_regime"] == CryptoRegime.MARKUP.value)
            & (
                regimes["vol_regime"].isin(
                    [VolatilityRegime.NORMAL.value, VolatilityRegime.COMPRESSED.value]
                )
            )
        )
    elif filter_mode == "moderate":
        # Use favorable_for_long flag
        allowed = regimes["favorable_for_long"]
    else:  # permissive
        # Avoid only the worst conditions
        blocked = (
            (regimes["crypto_regime"] == CryptoRegime.CAPITULATION.value)
            | (regimes["vol_regime"] == VolatilityRegime.EXTREME.value)
        )
        allowed = ~blocked

    # Apply filter (assuming 'entry_long' column exists)
    if "entry_long" in filtered.columns:
        filtered.loc[~allowed, "entry_long"] = False
    if "entry_signal" in filtered.columns:
        filtered.loc[~allowed, "entry_signal"] = 0

    return filtered


def regime_aware_position_sizing(
    base_size: float,
    regime_row: pd.Series,
    max_size: float = 1.0,
    min_size: float = 0.25,
) -> float:
    """
    Adjust position size based on current regime.

    Args:
        base_size: Default position size (0-1)
        regime_row: Single row from regimes DataFrame
        max_size: Maximum position multiplier
        min_size: Minimum position multiplier

    Returns:
        Adjusted position size
    """
    multiplier = 1.0

    # Volatility adjustment
    vol_regime = regime_row.get("vol_regime", "NORMAL")
    if vol_regime == VolatilityRegime.COMPRESSED.value:
        multiplier *= 1.2  # Squeeze often precedes big moves
    elif vol_regime == VolatilityRegime.ELEVATED.value:
        multiplier *= 0.75
    elif vol_regime == VolatilityRegime.EXTREME.value:
        multiplier *= 0.5

    # Trend confidence adjustment
    trend_conf = regime_row.get("trend_confidence", 0.5)
    multiplier *= 0.5 + trend_conf * 0.5  # 0.5x to 1.0x based on confidence

    # Stability bonus (longer regime = more confidence)
    stability = regime_row.get("regime_stability", 1)
    if stability > 10:
        multiplier *= 1.1

    adjusted = base_size * multiplier
    return float(np.clip(adjusted, min_size, max_size))


# ============================================================================
# PART 8: LEGACY COMPATIBILITY
# ============================================================================


def classify_regimes_v2(data: pd.DataFrame) -> pd.Series:
    """
    Legacy function for backward compatibility.
    Wraps new v3 analyzer and returns simplified regime labels.
    """
    analyzer = CryptoRegimeAnalyzer(use_hmm=False, lookback=200)
    regimes_df = analyzer.fit_and_classify(data)

    # Map v3 regimes to v2 labels
    v3_to_v2 = {
        TrendRegime.STRONG_BULL.value: "BULL",
        TrendRegime.WEAK_BULL.value: "BULL",
        TrendRegime.SIDEWAYS.value: "SIDEWAYS",
        TrendRegime.WEAK_BEAR.value: "BEAR",
        TrendRegime.STRONG_BEAR.value: "BEAR",
        TrendRegime.REVERSAL.value: "RECOVERY",
    }

    # Override with volatility-based classifications
    result = regimes_df["trend_regime"].map(v3_to_v2).fillna("OTHER")

    # Check for crash/high_vol conditions
    crash_mask = regimes_df["crypto_regime"] == CryptoRegime.CAPITULATION.value
    high_vol_mask = regimes_df["vol_regime"] == VolatilityRegime.EXTREME.value
    recovery_mask = regimes_df["crypto_regime"] == CryptoRegime.RECOVERY.value

    result.loc[crash_mask] = "CRASH"
    result.loc[high_vol_mask & ~crash_mask] = "HIGH_VOL"
    result.loc[recovery_mask] = "RECOVERY"

    return result


# ============================================================================
# PART 9: ANALYSIS REPORTING
# ============================================================================


def generate_regime_report(
    ohlcv: pd.DataFrame, asset_name: str = "ASSET", output_path: str = None
) -> str:
    """
    Generate comprehensive regime analysis report.

    Args:
        ohlcv: OHLCV DataFrame
        asset_name: Name for report header
        output_path: Optional path to save markdown report

    Returns:
        Markdown report string
    """
    analyzer = CryptoRegimeAnalyzer(use_hmm=True, lookback=200)
    regimes = analyzer.fit_and_classify(ohlcv)
    stats = analyzer.get_regime_stats()

    report = f"""# Regime Analysis Report: {asset_name}

**Generated**: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M UTC')}
**Bars Analyzed**: {len(regimes)}
**Period**: {regimes.index[0]} to {regimes.index[-1]}

## Regime Distribution

### Trend Regimes
| Regime | Percentage |
|--------|------------|
"""

    for regime, pct in sorted(
        stats["trend_distribution"].items(), key=lambda x: -x[1]
    ):
        report += f"| {regime} | {pct*100:.1f}% |\n"

    report += """
### Volatility Regimes
| Regime | Percentage |
|--------|------------|
"""

    for regime, pct in sorted(
        stats["vol_distribution"].items(), key=lambda x: -x[1]
    ):
        report += f"| {regime} | {pct*100:.1f}% |\n"

    report += """
### Crypto-Specific Regimes (Wyckoff)
| Regime | Percentage |
|--------|------------|
"""

    for regime, pct in sorted(
        stats["crypto_distribution"].items(), key=lambda x: -x[1]
    ):
        report += f"| {regime} | {pct*100:.1f}% |\n"

    report += f"""
## Summary Statistics

| Metric | Value |
|--------|-------|
| Mean Regime Stability | {stats['mean_stability']:.1f} bars |
| % Favorable for Long | {stats['pct_favorable_long']:.1f}% |
| Mean Composite Score | {stats['mean_composite_score']:.3f} |

## Trading Implications

- **Favorable Long Windows**: {stats['pct_favorable_long']:.1f}% of the time
- **Average Regime Duration**: {stats['mean_stability']:.0f} bars ({stats['mean_stability']/24:.1f} days at 1H)
- **Market Bias**: {"Bullish" if stats['mean_composite_score'] > 0.1 else "Bearish" if stats['mean_composite_score'] < -0.1 else "Neutral"}
"""

    if output_path:
        with open(output_path, "w") as f:
            f.write(report)

    return report
