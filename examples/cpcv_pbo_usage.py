"""
Example usage of CPCV Full Activation with PBO integration.

This demonstrates how to use the new pbo_with_cpcv() function
for regime-robust validation with 15 combinations C(6,2).
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import numpy as np
from crypto_backtest.validation.cpcv import pbo_with_cpcv, guard_cpcv_pbo

# =============================================================================
# Example 1: Basic CPCV+PBO validation
# =============================================================================
print("=" * 70)
print("EXAMPLE 1: Basic CPCV+PBO Validation")
print("=" * 70)

# Simulate returns matrix from optimization trials
# Shape: (n_trials=100, n_periods=1000)
np.random.seed(42)
returns_matrix = np.random.normal(loc=0.001, scale=0.01, size=(100, 1000))

# Run CPCV+PBO with default settings (15 combinations)
result = pbo_with_cpcv(
    returns_matrix,
    n_splits=6,
    n_test_splits=2,
    purge_gap=5,
    embargo_pct=0.01,
    threshold=0.15,
)

print(f"\nResults:")
print(f"  - PBO: {result.pbo:.4f} ({result.pbo:.2%})")
print(f"  - Threshold: {result.threshold} (15%)")
print(f"  - Pass: {result.passed}")
print(f"  - N Combinations: {result.n_combinations}")
print(f"  - Median Rank: {result.pbo_median_rank:.4f}")
print(f"  - IS Sharpe (mean): {result.is_sharpes_mean:.4f}")
print(f"  - OOS Sharpe (mean): {result.oos_sharpes_mean:.4f}")
print(f"  - WFE (CPCV): {result.wfe_cpcv:.4f}")
print(f"\nInterpretation:")
if result.passed:
    print("  [PASS] - Low overfitting risk, parameters likely robust")
else:
    print("  [FAIL] - High overfitting risk detected")

# =============================================================================
# Example 2: Perfect strategy (should have low PBO)
# =============================================================================
print("\n" + "=" * 70)
print("EXAMPLE 2: Perfect Strategy (Low PBO Expected)")
print("=" * 70)

# Create a perfect strategy that consistently outperforms
returns_perfect = np.random.normal(loc=0.001, scale=0.01, size=(100, 1000))
returns_perfect[0] += 0.01  # Make trial 0 consistently better

result_perfect = pbo_with_cpcv(
    returns_perfect,
    n_splits=6,
    n_test_splits=2,
    threshold=0.15,
)

print(f"\nPerfect Strategy Results:")
print(f"  - PBO: {result_perfect.pbo:.4f} ({result_perfect.pbo:.2%})")
print(f"  - Pass: {result_perfect.passed}")
print(f"  - Median Rank: {result_perfect.pbo_median_rank:.4f}")
print(f"  - WFE (CPCV): {result_perfect.wfe_cpcv:.4f}")

# =============================================================================
# Example 3: Overfitted strategy (should have high PBO)
# =============================================================================
print("\n" + "=" * 70)
print("EXAMPLE 3: Overfitted Strategy (High PBO Expected)")
print("=" * 70)

# Create an overfitted strategy (good on first half, poor on second half)
returns_overfit = np.random.normal(loc=0.0, scale=0.01, size=(100, 1000))
# Make trial 0 excellent on first half but poor on second half
returns_overfit[0, :500] += 0.02
returns_overfit[0, 500:] -= 0.01

result_overfit = pbo_with_cpcv(
    returns_overfit,
    n_splits=6,
    n_test_splits=2,
    threshold=0.15,
)

print(f"\nOverfitted Strategy Results:")
print(f"  - PBO: {result_overfit.pbo:.4f} ({result_overfit.pbo:.2%})")
print(f"  - Pass: {result_overfit.passed}")
print(f"  - Median Rank: {result_overfit.pbo_median_rank:.4f}")
print(f"  - WFE (CPCV): {result_overfit.wfe_cpcv:.4f}")

# =============================================================================
# Example 4: Using guard function for pipeline integration
# =============================================================================
print("\n" + "=" * 70)
print("EXAMPLE 4: Guard Function for Pipeline Integration")
print("=" * 70)

guard_result = guard_cpcv_pbo(
    returns_matrix,
    threshold=0.15,
    n_splits=6,
    n_test_splits=2,
    purge_gap=5,
    embargo_pct=0.01,
)

print(f"\nGuard Result (dict format):")
for key, value in guard_result.items():
    print(f"  {key}: {value}")

# =============================================================================
# Example 5: Different CPCV configurations
# =============================================================================
print("\n" + "=" * 70)
print("EXAMPLE 5: Different CPCV Configurations")
print("=" * 70)

configs = [
    (4, 1, "C(4,1) = 4 combinations"),
    (5, 2, "C(5,2) = 10 combinations"),
    (6, 2, "C(6,2) = 15 combinations (default)"),
    (6, 3, "C(6,3) = 20 combinations"),
    (7, 2, "C(7,2) = 21 combinations"),
]

for n_splits, n_test_splits, description in configs:
    result = pbo_with_cpcv(
        returns_matrix,
        n_splits=n_splits,
        n_test_splits=n_test_splits,
        threshold=0.15,
    )
    print(f"\n{description}:")
    print(f"  - PBO: {result.pbo:.4f}")
    print(f"  - N Combinations: {result.n_combinations}")
    print(f"  - Pass: {result.passed}")

# =============================================================================
# Example 6: Purging and embargo effects
# =============================================================================
print("\n" + "=" * 70)
print("EXAMPLE 6: Purging and Embargo Effects")
print("=" * 70)

configs_leakage = [
    (0, 0.00, "No purging, no embargo"),
    (5, 0.00, "Purge gap = 5, no embargo"),
    (0, 0.01, "No purging, embargo = 1%"),
    (5, 0.01, "Purge gap = 5, embargo = 1%"),
]

for purge_gap, embargo_pct, description in configs_leakage:
    result = pbo_with_cpcv(
        returns_matrix,
        n_splits=6,
        n_test_splits=2,
        purge_gap=purge_gap,
        embargo_pct=embargo_pct,
        threshold=0.15,
    )
    print(f"\n{description}:")
    print(f"  - PBO: {result.pbo:.4f}")
    print(f"  - WFE (CPCV): {result.wfe_cpcv:.4f}")
    print(f"  - Pass: {result.passed}")

print("\n" + "=" * 70)
print("CPCV+PBO Examples Complete")
print("=" * 70)
