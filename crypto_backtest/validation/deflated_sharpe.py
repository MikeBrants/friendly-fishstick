"""
Deflated Sharpe Ratio (DSR) Implementation

Calculates the probability that an observed Sharpe ratio is statistically 
significant after correcting for:
1. Number of trials tested (N) - the trial count paradox
2. Non-normality of returns (skewness, kurtosis)
3. Sample size (T)

References:
- Bailey & Lopez de Prado (2014) "The Deflated Sharpe Ratio"
- Lo (2002) "The Statistics of Sharpe Ratios"
"""
from __future__ import annotations

import numpy as np
from scipy.stats import norm, skew, kurtosis
from typing import Tuple, Optional
import pandas as pd


def deflated_sharpe_ratio(
    returns: np.ndarray | pd.Series,
    sharpe_observed: float,
    n_trials: int,
    annualization: float = 1.0,
) -> Tuple[float, float]:
    """
    Calculate DSR - probability that observed Sharpe is statistically significant.
    
    Args:
        returns: Array of strategy returns (trade returns or period returns)
        sharpe_observed: Observed Sharpe ratio
        n_trials: Number of optimization trials tested (e.g., 200-300 for Optuna)
        annualization: Annualization factor (1 if already annualized,
                       sqrt(252) for daily, sqrt(8760) for hourly)
    
    Returns:
        dsr: Probability [0,1] that Sharpe is statistically significant
        sr0: Threshold Sharpe expected from random trials (by chance)
    
    Example:
        >>> returns = np.array([0.01, -0.02, 0.015, ...])  # trade returns
        >>> dsr, sr0 = deflated_sharpe_ratio(returns, sharpe_observed=2.14, n_trials=300)
        >>> print(f"DSR: {dsr:.1%}, Threshold: {sr0:.2f}")
    """
    if isinstance(returns, pd.Series):
        returns = returns.dropna().to_numpy()
    
    T = len(returns)
    if T < 10:
        # Not enough data for reliable estimate
        return 0.0, float('inf')
    
    # De-annualize if needed
    sr = sharpe_observed / annualization
    
    # Higher moments for non-normality correction
    gamma3 = skew(returns)  # Skewness
    gamma4 = kurtosis(returns, fisher=False)  # Excess kurtosis (not Fisher's)
    
    # Variance of Sharpe estimator (Lo 2002 formula adjusted for non-normality)
    # This accounts for the fact that SR is estimated, not known
    var_sr = (1 + 0.5 * sr**2 - gamma3 * sr + ((gamma4 - 3) / 4) * sr**2) / (T - 1)
    
    # Handle edge cases
    if var_sr <= 0:
        var_sr = 1.0 / (T - 1)  # Fallback to normal assumption
    
    std_sr = np.sqrt(var_sr)
    
    # Euler-Mascheroni constant
    gamma = 0.5772156649
    
    # SR0: Expected maximum Sharpe from N random trials (Extreme Value Theory)
    # This is the key correction for multiple testing / trial count paradox
    if n_trials <= 1:
        sr0 = 0.0
    else:
        sr0 = std_sr * (
            (1 - gamma) * norm.ppf(1 - 1/n_trials) + 
            gamma * norm.ppf(1 - 1/(n_trials * np.e))
        )
    
    # DSR: Probability that observed SR exceeds what's expected by chance
    if std_sr > 0:
        dsr = norm.cdf((sr - sr0) / std_sr)
    else:
        dsr = 1.0 if sr > sr0 else 0.0
    
    return float(dsr), float(sr0)


def guard_dsr(
    returns: np.ndarray | pd.Series,
    sharpe_observed: float,
    n_trials: int = 300,
    threshold: float = 0.85,
) -> dict:
    """
    Guard function for DSR validation.
    
    Args:
        returns: Array of strategy returns
        sharpe_observed: Observed Sharpe ratio
        n_trials: Number of optimization trials (default 300 for Phase 2)
        threshold: Minimum DSR to pass (0.85 = 85% confidence)
                  - 0.95 is very strict
                  - 0.85 is recommended when combined with other guards
    
    Returns:
        dict with keys: pass, dsr, sr0, threshold
    
    Example:
        >>> result = guard_dsr(returns, sharpe_observed=2.14, n_trials=300)
        >>> if result['pass']:
        ...     print("Edge is statistically significant")
    """
    dsr, sr0 = deflated_sharpe_ratio(returns, sharpe_observed, n_trials)
    
    return {
        "guard": "dsr",
        "pass": dsr >= threshold,
        "dsr": round(dsr, 4),
        "sr0": round(sr0, 4),
        "threshold": threshold,
        "n_trials": n_trials,
    }


def interpret_dsr(dsr: float) -> str:
    """
    Interpret DSR value.
    
    Args:
        dsr: DSR value [0, 1]
    
    Returns:
        Human-readable interpretation
    """
    if dsr >= 0.95:
        return "STRONG - Edge is statistically significant (>95%)"
    elif dsr >= 0.85:
        return "MARGINAL - Acceptable if other guards pass (85-95%)"
    elif dsr >= 0.70:
        return "WEAK - Likely noise/overfitting (70-85%)"
    else:
        return "FAIL - Almost certainly overfitting (<70%)"


def calculate_required_sharpe(
    n_trials: int,
    n_returns: int,
    target_dsr: float = 0.95,
    skewness: float = 0.0,
    kurtosis_excess: float = 3.0,
) -> float:
    """
    Calculate the minimum Sharpe required to achieve target DSR.
    
    Useful for understanding what performance is needed given your trial count.
    
    Args:
        n_trials: Number of optimization trials
        n_returns: Number of return observations
        target_dsr: Target DSR (default 0.95)
        skewness: Expected skewness of returns (0 for normal)
        kurtosis_excess: Expected kurtosis (3 for normal)
    
    Returns:
        Minimum Sharpe ratio required
    
    Example:
        >>> min_sr = calculate_required_sharpe(n_trials=300, n_returns=100)
        >>> print(f"Need Sharpe >= {min_sr:.2f} for DSR > 95%")
    """
    gamma = 0.5772156649
    T = n_returns
    
    # Approximate std_sr assuming SR ~ 1.5 (typical good strategy)
    sr_assumed = 1.5
    var_sr = (1 + 0.5 * sr_assumed**2) / (T - 1)
    std_sr = np.sqrt(var_sr)
    
    # SR0 threshold
    if n_trials > 1:
        sr0 = std_sr * (
            (1 - gamma) * norm.ppf(1 - 1/n_trials) + 
            gamma * norm.ppf(1 - 1/(n_trials * np.e))
        )
    else:
        sr0 = 0.0
    
    # Required SR for target DSR
    z_target = norm.ppf(target_dsr)
    required_sr = sr0 + z_target * std_sr
    
    return float(required_sr)


# === Convenience Functions ===

def dsr_summary(
    returns: np.ndarray | pd.Series,
    sharpe_observed: float,
    n_trials: int,
) -> str:
    """
    Generate a summary string for DSR analysis.
    
    Args:
        returns: Array of strategy returns
        sharpe_observed: Observed Sharpe ratio
        n_trials: Number of optimization trials
    
    Returns:
        Formatted summary string
    """
    dsr, sr0 = deflated_sharpe_ratio(returns, sharpe_observed, n_trials)
    interpretation = interpret_dsr(dsr)
    
    lines = [
        "=" * 50,
        "DEFLATED SHARPE RATIO (DSR) ANALYSIS",
        "=" * 50,
        f"Observed Sharpe:     {sharpe_observed:.2f}",
        f"Threshold (SR₀):     {sr0:.2f} (expected by chance with {n_trials} trials)",
        f"DSR:                 {dsr:.1%}",
        f"Interpretation:      {interpretation}",
        "=" * 50,
    ]
    
    return "\n".join(lines)


# === Integration with existing guards ===

def run_dsr_guard(
    trades_df: pd.DataFrame,
    sharpe_oos: float,
    n_trials: int = 300,
    threshold: float = 0.85,
    return_col: str = "return_pct",
) -> dict:
    """
    Run DSR guard on a trades dataframe.
    
    Args:
        trades_df: DataFrame with trade results
        sharpe_oos: OOS Sharpe ratio
        n_trials: Number of Optuna trials used
        threshold: DSR threshold (0.85 recommended)
        return_col: Column name for returns
    
    Returns:
        Guard result dict compatible with existing guard system
    """
    if return_col not in trades_df.columns:
        return {
            "guard": "dsr",
            "pass": False,
            "error": f"Column '{return_col}' not found",
            "dsr": None,
            "sr0": None,
        }
    
    returns = trades_df[return_col].dropna().to_numpy()
    
    if len(returns) < 10:
        return {
            "guard": "dsr",
            "pass": False,
            "error": "Not enough trades for DSR calculation",
            "dsr": None,
            "sr0": None,
        }
    
    result = guard_dsr(returns, sharpe_oos, n_trials, threshold)
    return result
