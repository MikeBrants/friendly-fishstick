"""
True CSCV (Combinatorially Symmetric Cross-Validation) Implementation
Following Bailey & López de Prado (2014)

Drop-in replacement for the simplified guard_pbo function.

Key differences from current implementation:
- Symmetric data partitioning (not trial pairs)
- Proper logrank (lambda) calculation
- 16 folds x C(16,8) = 12,870 paths
- Purge gap to prevent temporal leakage
- Optional Deflated Sharpe Ratio integration

Usage:
    from crypto_backtest.validation.pbo_cscv import cscv_pbo, guard_pbo_cscv
    
    # Load existing returns matrix
    returns_matrix = np.load(f"outputs/returns_matrix_{asset}_{runid}.npy")
    
    # Run true CSCV
    result = cscv_pbo(returns_matrix, n_folds=16, purge_gap=24)
    print(f"PBO: {result['pbo']:.3f} | Pass: {result['pass']}")
"""

import numpy as np
from itertools import combinations
from typing import Tuple, List, Dict, Optional
from dataclasses import dataclass
import warnings
from scipy import stats


# =============================================================================
# CONFIGURATION
# =============================================================================

@dataclass
class CSCVConfig:
    """Configuration for CSCV analysis."""
    n_folds: int = 16  # Must be even
    purge_gap: int = 24  # Bars between IS/OOS to prevent leakage
    annualization_factor: float = np.sqrt(252 * 24)  # Hourly crypto
    pbo_threshold: float = 0.50  # Pass if PBO < this
    min_bars_per_fold: int = 500  # Minimum data requirement
    max_paths: Optional[int] = None  # Limit paths for speed (None = all)
    random_seed: int = 42  # For reproducible path sampling


DEFAULT_CONFIG = CSCVConfig()


# =============================================================================
# CORE CSCV IMPLEMENTATION
# =============================================================================

def cscv_pbo_compat(
    returns_matrix: np.ndarray,
    folds: int = 16,
    purge_bars: int = 24,
    embargo_bars: int = 0,
    annualization_factor: float | None = None,
) -> Dict:
    """
    Compatibility wrapper for newer pipeline signatures.

    Accepts folds/purge_bars/embargo_bars/annualization_factor and maps to CSCVConfig.
    Note: embargo_bars is not implemented in CSCVConfig and is ignored (warning emitted).
    """
    if embargo_bars not in (0, None):
        warnings.warn(
            "embargo_bars is not supported in cscv_pbo; ignoring.",
            stacklevel=2,
        )
    config = CSCVConfig(
        n_folds=folds,
        purge_gap=purge_bars,
        annualization_factor=annualization_factor
        if annualization_factor is not None
        else DEFAULT_CONFIG.annualization_factor,
    )
    return cscv_pbo(returns_matrix, config=config)

def cscv_pbo(
    returns_matrix: np.ndarray,
    n_folds: int = 16,
    purge_gap: int = 24,
    config: Optional[CSCVConfig] = None,
) -> Dict:
    """
    Combinatorially Symmetric Cross-Validation for Probability of Backtest Overfitting.
    
    This implements the full Bailey/López de Prado (2014) methodology:
    1. Partition data into S folds
    2. Generate all C(S, S/2) symmetric IS/OOS combinations
    3. For each combination:
       - Find best trial on IS data
       - Compute its rank on OOS data (logrank lambda)
    4. PBO = proportion of paths where lambda < 0.5
    
    Parameters
    ----------
    returns_matrix : np.ndarray
        Shape (n_trials, n_bars). Each row is one trial's bar-by-bar returns.
        This should come from your Bayesian optimization output.
    n_folds : int
        Number of folds for partitioning. Must be even. Default 16.
    purge_gap : int
        Number of bars to skip at IS/OOS boundaries to prevent leakage.
    config : CSCVConfig, optional
        Advanced configuration options.
        
    Returns
    -------
    dict with keys:
        - pbo: float, probability of backtest overfitting [0, 1]
        - pass: bool, True if pbo < threshold
        - lambda_distribution: list of lambda values for each path
        - lambda_median: float, median lambda
        - lambda_mean: float, mean lambda
        - n_paths: int, number of paths evaluated
        - n_trials: int, number of trials in matrix
        - n_bars: int, number of bars in data
        - degradation: float, average OOS/IS Sharpe ratio
        - details: dict with additional diagnostics
        
    Raises
    ------
    ValueError
        If n_folds is odd or data is insufficient.
        
    Examples
    --------
    >>> returns = np.load("outputs/returns_matrix_ETH_run123.npy")
    >>> result = cscv_pbo(returns)
    >>> print(f"PBO: {result['pbo']:.3f}")
    PBO: 0.423
    >>> print(f"Pass: {result['pass']}")
    Pass: True
    """
    if config is None:
        config = CSCVConfig(n_folds=n_folds, purge_gap=purge_gap)
    
    # Validate inputs
    _validate_inputs(returns_matrix, config)
    
    n_trials, n_bars = returns_matrix.shape
    
    # Step 1: Create fold indices
    fold_indices = _create_fold_indices(n_bars, config.n_folds)
    
    # Step 2: Generate all symmetric partitions
    half = config.n_folds // 2
    all_is_combinations = list(combinations(range(config.n_folds), half))
    n_total_paths = len(all_is_combinations)
    
    # Optionally sample paths for speed
    if config.max_paths and n_total_paths > config.max_paths:
        np.random.seed(config.random_seed)
        sampled_idx = np.random.choice(n_total_paths, config.max_paths, replace=False)
        all_is_combinations = [all_is_combinations[i] for i in sorted(sampled_idx)]
        warnings.warn(
            f"Sampled {config.max_paths} paths from {n_total_paths} total. "
            f"Set config.max_paths=None for full CSCV."
        )
    
    # Step 3: Compute lambda for each path
    lambda_values = []
    omega_values = []
    degradation_ratios = []
    
    for is_fold_ids in all_is_combinations:
        oos_fold_ids = tuple(i for i in range(config.n_folds) if i not in is_fold_ids)
        
        # Get bar indices for IS and OOS with purge gap
        is_bars, oos_bars = _get_purged_indices(
            fold_indices, is_fold_ids, oos_fold_ids, config.purge_gap
        )
        
        if len(is_bars) < config.min_bars_per_fold or len(oos_bars) < config.min_bars_per_fold:
            continue  # Skip if insufficient data after purging
        
        # Compute Sharpe for each trial on IS and OOS
        is_sharpes = np.array([
            _compute_sharpe(returns_matrix[t, is_bars], config.annualization_factor)
            for t in range(n_trials)
        ])
        oos_sharpes = np.array([
            _compute_sharpe(returns_matrix[t, oos_bars], config.annualization_factor)
            for t in range(n_trials)
        ])
        
        # Find best trial on IS
        best_is_idx = np.argmax(is_sharpes)
        best_is_sharpe = is_sharpes[best_is_idx]
        
        # Get OOS performance of best IS trial
        best_trial_oos_sharpe = oos_sharpes[best_is_idx]
        
        # Compute relative rank omega (omega) per Bailey & Lopez de Prado (2014)
        # omega = rank / (N + 1) in (0, 1), avoids omega = 0 or 1
        rank = np.sum(oos_sharpes <= best_trial_oos_sharpe)
        omega = rank / (n_trials + 1)

        # Compute logit lambda = ln(omega / (1 - omega)) in (-inf, +inf)
        # lambda < 0 iff omega < 0.5 (underperformance)
        lambda_val = np.log(omega / (1 - omega))

        omega_values.append(omega)
        lambda_values.append(lambda_val)
        
        # Track degradation (OOS/IS performance ratio)
        if best_is_sharpe > 0:
            degradation_ratios.append(best_trial_oos_sharpe / best_is_sharpe)
    
    if not lambda_values:
        raise ValueError("No valid paths computed. Check data size and purge gap.")
    
    # Step 4: Compute PBO
    omega_array = np.array(omega_values)
    lambda_array = np.array(lambda_values)

    # PBO = P(lambda < 0) = P(omega < 0.5) - proportion of paths where best IS underperforms OOS
    pbo = np.mean(lambda_array < 0)
    
    return {
        "pbo": float(pbo),
        "pass": pbo < config.pbo_threshold,
        "omega_distribution": omega_values,
        "lambda_distribution": lambda_values,
        "omega_median": float(np.median(omega_array)),
        "omega_mean": float(np.mean(omega_array)),
        "lambda_median": float(np.median(lambda_array)),
        "lambda_mean": float(np.mean(lambda_array)),
        "n_paths": len(lambda_values),
        "n_trials": n_trials,
        "n_bars": n_bars,
        "degradation": float(np.mean(degradation_ratios)) if degradation_ratios else None,
        "details": {
            "n_folds": config.n_folds,
            "purge_gap": config.purge_gap,
            "threshold": config.pbo_threshold,
            "omega_std": float(np.std(omega_array)),
            "omega_q25": float(np.percentile(omega_array, 25)),
            "omega_q75": float(np.percentile(omega_array, 75)),
            "lambda_std": float(np.std(lambda_array)),
        }
    }


# =============================================================================
# GUARD INTERFACE (Drop-in replacement)
# =============================================================================

def guard_pbo_cscv(
    returns_matrix: np.ndarray,
    n_splits: int = 16,  # Renamed from n_folds for compatibility
    threshold: float = 0.50,
) -> Dict:
    """
    Drop-in replacement for existing guard_pbo function.
    
    Maintains same interface but uses true CSCV methodology.
    
    Parameters
    ----------
    returns_matrix : np.ndarray
        Shape (n_trials, n_bars)
    n_splits : int
        Number of folds (renamed for backward compatibility)
    threshold : float
        PBO threshold for pass/fail
        
    Returns
    -------
    dict with keys matching original guard_pbo output:
        - pbo: float
        - pass: bool
        - n_paths: int
        - method: str ("CSCV" to indicate new implementation)
    """
    config = CSCVConfig(
        n_folds=n_splits,
        pbo_threshold=threshold,
    )
    
    result = cscv_pbo(returns_matrix, config=config)
    
    # Return format compatible with existing guard system
    return {
        "pbo": float(result["pbo"]),
        "pass": bool(result["pass"]),
        "n_paths": int(result["n_paths"]),
        "method": "CSCV",
        "omega_median": float(result["omega_median"]),
        "lambda_median": float(result["lambda_median"]),
        "degradation": float(result["degradation"]) if result["degradation"] is not None else None,
        "threshold": float(threshold),
    }


# =============================================================================
# DEFLATED SHARPE RATIO
# =============================================================================

def deflated_sharpe_ratio(
    observed_sharpe: float,
    n_trials: int,
    n_bars: int,
    skewness: float = 0.0,
    kurtosis: float = 3.0,
    annualization_factor: float = np.sqrt(252 * 24),
) -> Dict:
    """
    Compute Deflated Sharpe Ratio (DSR) following Bailey & López de Prado.
    
    DSR adjusts the observed Sharpe for:
    - Multiple testing (number of trials)
    - Non-normality (skewness, kurtosis)
    - Sample size
    
    Parameters
    ----------
    observed_sharpe : float
        The Sharpe ratio of the selected strategy (annualized)
    n_trials : int
        Number of strategies tested during optimization
    n_bars : int
        Number of observations used
    skewness : float
        Skewness of returns (0 for normal)
    kurtosis : float
        Kurtosis of returns (3 for normal)
    annualization_factor : float
        Factor for annualization
        
    Returns
    -------
    dict with keys:
        - dsr: float, deflated Sharpe ratio
        - dsr_pvalue: float, p-value for DSR > 0
        - expected_max_sharpe: float, E[max(SR)] under null
        - haircut: float, how much Sharpe was "haircut"
        - pass: bool, True if DSR significantly > 0
    """
    # Expected maximum Sharpe under null hypothesis (all trials are random)
    # Using approximation from Bailey & López de Prado
    e_max_sharpe = _expected_max_sharpe(n_trials, n_bars, skewness, kurtosis)
    
    # Variance of Sharpe ratio estimator
    sr_std = _sharpe_std(observed_sharpe, n_bars, skewness, kurtosis)
    
    # Deflated Sharpe = observed - expected_max
    dsr = observed_sharpe - e_max_sharpe
    
    # P-value: probability that DSR > 0 by chance
    if sr_std > 0:
        z_score = dsr / sr_std
        dsr_pvalue = 1 - stats.norm.cdf(z_score)
    else:
        dsr_pvalue = 1.0
    
    return {
        "dsr": float(dsr),
        "dsr_pvalue": float(dsr_pvalue),
        "expected_max_sharpe": float(e_max_sharpe),
        "haircut": float(e_max_sharpe),  # How much was "lost" to multiple testing
        "pass": dsr_pvalue < 0.05,  # Significant at 5%
        "observed_sharpe": float(observed_sharpe),
        "n_trials": n_trials,
    }


def _expected_max_sharpe(n_trials: int, n_bars: int, skew: float, kurt: float) -> float:
    """
    Compute E[max(SR)] under null hypothesis.

    Uses approximation: E[max] ~= (1 - gamma) * Z_{1-1/N} + gamma * Z_{1-1/(N*e)}
    where gamma = Euler-Mascheroni constant ~= 0.5772
    """
    gamma = 0.5772156649  # Euler-Mascheroni
    
    # Quantiles of standard normal
    z1 = stats.norm.ppf(1 - 1/n_trials) if n_trials > 1 else 0
    z2 = stats.norm.ppf(1 - 1/(n_trials * np.e)) if n_trials > 1 else 0
    
    e_max = (1 - gamma) * z1 + gamma * z2
    
    # Adjust for sample size
    e_max *= (1 / np.sqrt(n_bars))
    
    # Adjust for non-normality (higher kurtosis increases expected max)
    if kurt > 3:
        e_max *= (1 + (kurt - 3) / 24)
    
    return e_max


def _sharpe_std(sr: float, n_bars: int, skew: float, kurt: float) -> float:
    """
    Standard error of Sharpe ratio estimator.
    
    SE(SR) = sqrt((1 + 0.5*SR^2 - skew*SR + (kurt-3)/4 * SR^2) / (n-1))
    """
    if n_bars <= 1:
        return np.inf
    
    variance = (
        1
        + 0.5 * sr**2
        - skew * sr
        + (kurt - 3) / 4 * sr**2
    ) / (n_bars - 1)
    
    return np.sqrt(max(variance, 0))


# =============================================================================
# COMBINED PBO + DSR ANALYSIS
# =============================================================================

def full_overfitting_analysis(
    returns_matrix: np.ndarray,
    observed_sharpe: Optional[float] = None,
    config: Optional[CSCVConfig] = None,
) -> Dict:
    """
    Complete overfitting analysis: CSCV PBO + Deflated Sharpe Ratio.
    
    Parameters
    ----------
    returns_matrix : np.ndarray
        Shape (n_trials, n_bars)
    observed_sharpe : float, optional
        Sharpe of selected strategy. If None, uses best trial.
    config : CSCVConfig, optional
        Configuration for CSCV.
        
    Returns
    -------
    dict with keys:
        - pbo: PBO results dict
        - dsr: DSR results dict
        - combined_pass: bool, True if BOTH pass
        - risk_level: str, "LOW" / "MEDIUM" / "HIGH"
    """
    if config is None:
        config = DEFAULT_CONFIG
    
    n_trials, n_bars = returns_matrix.shape
    
    # CSCV PBO
    pbo_result = cscv_pbo(returns_matrix, config=config)
    
    # Compute observed Sharpe if not provided
    if observed_sharpe is None:
        trial_sharpes = np.array([
            _compute_sharpe(returns_matrix[t], config.annualization_factor)
            for t in range(n_trials)
        ])
        observed_sharpe = np.max(trial_sharpes)
    
    # Compute skewness and kurtosis from best trial
    best_idx = np.argmax([
        _compute_sharpe(returns_matrix[t], config.annualization_factor)
        for t in range(n_trials)
    ])
    best_returns = returns_matrix[best_idx]
    skewness = float(stats.skew(best_returns))
    kurtosis = float(stats.kurtosis(best_returns, fisher=False))  # Excess kurtosis
    
    # Deflated Sharpe Ratio
    dsr_result = deflated_sharpe_ratio(
        observed_sharpe=observed_sharpe,
        n_trials=n_trials,
        n_bars=n_bars,
        skewness=skewness,
        kurtosis=kurtosis,
        annualization_factor=config.annualization_factor,
    )
    
    # Combined assessment
    combined_pass = pbo_result["pass"] and dsr_result["pass"]
    
    # Risk level
    if pbo_result["pbo"] < 0.30 and dsr_result["dsr_pvalue"] < 0.01:
        risk_level = "LOW"
    elif pbo_result["pbo"] < 0.50 and dsr_result["dsr_pvalue"] < 0.05:
        risk_level = "MEDIUM"
    else:
        risk_level = "HIGH"
    
    return {
        "pbo": pbo_result,
        "dsr": dsr_result,
        "combined_pass": combined_pass,
        "risk_level": risk_level,
        "summary": {
            "pbo_score": pbo_result["pbo"],
            "pbo_pass": pbo_result["pass"],
            "dsr_score": dsr_result["dsr"],
            "dsr_pvalue": dsr_result["dsr_pvalue"],
            "dsr_pass": dsr_result["pass"],
            "degradation": pbo_result["degradation"],
            "haircut": dsr_result["haircut"],
        }
    }


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def _validate_inputs(returns_matrix: np.ndarray, config: CSCVConfig) -> None:
    """Validate inputs for CSCV."""
    if returns_matrix.ndim != 2:
        raise ValueError(f"returns_matrix must be 2D, got {returns_matrix.ndim}D")
    
    n_trials, n_bars = returns_matrix.shape
    
    if n_trials < 2:
        raise ValueError(f"Need at least 2 trials, got {n_trials}")
    
    if config.n_folds % 2 != 0:
        raise ValueError(f"n_folds must be even, got {config.n_folds}")
    
    min_bars_required = config.n_folds * config.min_bars_per_fold
    if n_bars < min_bars_required:
        raise ValueError(
            f"Insufficient data: {n_bars} bars < {min_bars_required} required "
            f"({config.n_folds} folds × {config.min_bars_per_fold} min bars)"
        )
    
    if np.any(np.isnan(returns_matrix)):
        raise ValueError("returns_matrix contains NaN values")


def _create_fold_indices(n_bars: int, n_folds: int) -> List[Tuple[int, int]]:
    """Create fold boundary indices."""
    fold_size = n_bars // n_folds
    indices = []
    for i in range(n_folds):
        start = i * fold_size
        end = (i + 1) * fold_size if i < n_folds - 1 else n_bars
        indices.append((start, end))
    return indices


def _get_purged_indices(
    fold_indices: List[Tuple[int, int]],
    is_fold_ids: Tuple[int, ...],
    oos_fold_ids: Tuple[int, ...],
    purge_gap: int,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Get bar indices for IS and OOS with purge gap applied.
    
    Purge removes bars at the boundary between IS and OOS to prevent leakage.
    """
    is_bars = []
    oos_bars = []
    
    # Collect IS bars
    for fold_id in is_fold_ids:
        start, end = fold_indices[fold_id]
        
        # Check if adjacent fold is OOS (need purge)
        prev_is_oos = (fold_id - 1) in oos_fold_ids if fold_id > 0 else False
        next_is_oos = (fold_id + 1) in oos_fold_ids if fold_id < len(fold_indices) - 1 else False
        
        # Apply purge at boundaries
        if prev_is_oos:
            start += purge_gap
        if next_is_oos:
            end -= purge_gap
        
        if start < end:
            is_bars.extend(range(start, end))
    
    # Collect OOS bars
    for fold_id in oos_fold_ids:
        start, end = fold_indices[fold_id]
        
        prev_is_is = (fold_id - 1) in is_fold_ids if fold_id > 0 else False
        next_is_is = (fold_id + 1) in is_fold_ids if fold_id < len(fold_indices) - 1 else False
        
        if prev_is_is:
            start += purge_gap
        if next_is_is:
            end -= purge_gap
        
        if start < end:
            oos_bars.extend(range(start, end))
    
    return np.array(is_bars), np.array(oos_bars)


def _compute_sharpe(returns: np.ndarray, annualization: float) -> float:
    """Compute annualized Sharpe ratio."""
    if len(returns) < 2:
        return 0.0
    std = np.std(returns, ddof=1)
    if std < 1e-10:
        return 0.0
    return (np.mean(returns) / std) * annualization


# =============================================================================
# VISUALIZATION HELPERS
# =============================================================================

def plot_lambda_distribution(result: Dict, save_path: Optional[str] = None):
    """
    Plot the lambda distribution (logit) from CSCV results.

    Requires matplotlib.
    """
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        warnings.warn("matplotlib not available for plotting")
        return
    
    lambda_vals = result["lambda_distribution"]
    pbo = result["pbo"]
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Histogram
    ax.hist(lambda_vals, bins=50, density=True, alpha=0.7, color='steelblue',
            edgecolor='white', linewidth=0.5)
    
    # Reference lines
    ax.axvline(0, color='red', linestyle='--', linewidth=2, label='lambda = 0 (random)')
    ax.axvline(np.median(lambda_vals), color='green', linestyle='-', linewidth=2,
               label=f'Median lambda = {np.median(lambda_vals):.3f}')

    # Shading for overfit region (lambda < 0)
    left_bound = ax.get_xlim()[0]
    ax.axvspan(left_bound, 0, alpha=0.1, color='red', label='Overfit region (lambda<0)')

    ax.set_xlabel('lambda (Logit of relative rank)', fontsize=12)
    ax.set_ylabel('Density', fontsize=12)
    ax.set_title(f'CSCV lambda Distribution | PBO = {pbo:.3f}', fontsize=14)
    ax.legend(loc='upper right')
    
    # Add text box
    textstr = f'PBO: {pbo:.3f}\nPaths: {result["n_paths"]}\nTrials: {result["n_trials"]}'
    props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)
    ax.text(0.02, 0.98, textstr, transform=ax.transAxes, fontsize=10,
            verticalalignment='top', bbox=props)
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=150)
        print(f"Saved plot to {save_path}")
    
    return fig


# =============================================================================
# CLI INTERFACE
# =============================================================================

def main():
    """Command-line interface for CSCV PBO analysis."""
    import argparse
    import json
    from pathlib import Path
    
    parser = argparse.ArgumentParser(description="Run CSCV PBO analysis")
    parser.add_argument("returns_file", help="Path to returns_matrix .npy file")
    parser.add_argument("--folds", type=int, default=16, help="Number of folds")
    parser.add_argument("--purge", type=int, default=24, help="Purge gap in bars")
    parser.add_argument("--threshold", type=float, default=0.50, help="PBO threshold")
    parser.add_argument("--plot", type=str, default=None, help="Save plot to path")
    parser.add_argument("--full", action="store_true", help="Include DSR analysis")
    parser.add_argument("--output", type=str, default=None, help="Save results to JSON")
    
    args = parser.parse_args()
    
    # Load returns matrix
    returns_matrix = np.load(args.returns_file)
    print(f"Loaded returns matrix: {returns_matrix.shape} (trials × bars)")
    
    # Configure
    config = CSCVConfig(
        n_folds=args.folds,
        purge_gap=args.purge,
        pbo_threshold=args.threshold,
    )
    
    # Run analysis
    if args.full:
        result = full_overfitting_analysis(returns_matrix, config=config)
        print("\n" + "="*60)
        print("FULL OVERFITTING ANALYSIS")
        print("="*60)
        print(f"PBO Score: {result['pbo']['pbo']:.3f} ({'PASS' if result['pbo']['pass'] else 'FAIL'})")
        print(f"DSR Score: {result['dsr']['dsr']:.3f} (p={result['dsr']['dsr_pvalue']:.4f})")
        print(f"Degradation: {result['pbo']['degradation']:.2f}x")
        print(f"Haircut: {result['dsr']['haircut']:.3f}")
        print(f"Risk Level: {result['risk_level']}")
        print(f"Combined: {'PASS' if result['combined_pass'] else 'FAIL'}")
    else:
        result = cscv_pbo(returns_matrix, config=config)
        print("\n" + "="*60)
        print("CSCV PBO ANALYSIS")
        print("="*60)
        print(f"PBO Score: {result['pbo']:.3f}")
        print(f"Pass: {'YES' if result['pass'] else 'NO'}")
        print(f"lambda Median: {result['lambda_median']:.3f}")
        print(f"Degradation: {result['degradation']:.2f}x" if result['degradation'] else "Degradation: N/A")
        print(f"Paths: {result['n_paths']}")
        print(f"Trials: {result['n_trials']}")
    
    # Plot
    if args.plot:
        if args.full:
            plot_lambda_distribution(result['pbo'], args.plot)
        else:
            plot_lambda_distribution(result, args.plot)
    
    # Save results
    if args.output:
        # Convert numpy types for JSON serialization
        def convert(obj):
            if isinstance(obj, np.ndarray):
                return obj.tolist()
            if isinstance(obj, (np.int64, np.int32)):
                return int(obj)
            if isinstance(obj, (np.float64, np.float32)):
                return float(obj)
            return obj
        
        with open(args.output, 'w') as f:
            json.dump(result, f, indent=2, default=convert)
        print(f"\nResults saved to {args.output}")


if __name__ == "__main__":
    main()
