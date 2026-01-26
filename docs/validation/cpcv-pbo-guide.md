# CPCV + PBO Integration Guide

## Overview

This guide explains how to use the **Combinatorial Purged Cross-Validation (CPCV)** with **Probability of Backtest Overfitting (PBO)** integration for robust strategy validation.

## Quick Start

```python
from crypto_backtest.validation.cpcv import pbo_with_cpcv

# Assume you have a returns matrix from optimization trials
# Shape: (n_trials, n_periods)
import numpy as np
returns_matrix = np.load("returns_matrix_ASSET_20260126.npy")

# Run CPCV+PBO validation with 15 combinations
result = pbo_with_cpcv(
    returns_matrix,
    n_splits=6,           # Total splits
    n_test_splits=2,      # Test splits per combination (C(6,2)=15)
    purge_gap=5,          # Observations to purge around boundaries
    embargo_pct=0.01,     # 1% embargo after test set
    threshold=0.15,       # Pass threshold (15%)
)

# Check results
print(f"PBO: {result.pbo:.2%}")
print(f"Pass: {result.passed}")
print(f"Interpretation: {result.interpretation}")
```

## What is CPCV?

**Combinatorial Purged Cross-Validation (CPCV)** is a robust cross-validation methodology designed for financial time series data. It addresses two critical issues:

1. **Data Leakage**: Standard cross-validation can leak information from future to past
2. **Limited Coverage**: Single train/test split may not capture regime diversity

### Key Features

- **Combinatorial**: Generates C(n_splits, n_test_splits) combinations (e.g., C(6,2) = 15)
- **Purging**: Removes observations near test boundaries to prevent leakage
- **Embargo**: Adds gap after test set before training resumes
- **Time-Aware**: Respects temporal order of financial data

### Example: C(6,2) = 15 Combinations

With `n_splits=6` and `n_test_splits=2`:

```
Split:  [0] [1] [2] [3] [4] [5]

Combination 1:  IS: 0,1,2,3  OOS: 4,5
Combination 2:  IS: 0,1,2,4  OOS: 3,5
Combination 3:  IS: 0,1,2,5  OOS: 3,4
Combination 4:  IS: 0,1,3,4  OOS: 2,5
Combination 5:  IS: 0,1,3,5  OOS: 2,4
Combination 6:  IS: 0,1,4,5  OOS: 2,3
Combination 7:  IS: 0,2,3,4  OOS: 1,5
Combination 8:  IS: 0,2,3,5  OOS: 1,4
Combination 9:  IS: 0,2,4,5  OOS: 1,3
Combination 10: IS: 0,3,4,5  OOS: 1,2
Combination 11: IS: 1,2,3,4  OOS: 0,5
Combination 12: IS: 1,2,3,5  OOS: 0,4
Combination 13: IS: 1,2,4,5  OOS: 0,3
Combination 14: IS: 1,3,4,5  OOS: 0,2
Combination 15: IS: 2,3,4,5  OOS: 0,1
```

## What is PBO?

**Probability of Backtest Overfitting (PBO)** measures the likelihood that the best in-sample (IS) strategy will underperform out-of-sample (OOS).

### Methodology

For each CPCV combination:
1. Find best strategy on IS (training set)
2. Record OOS (test set) rank of that strategy
3. Compute relative rank: 0 = best, 1 = worst

**PBO** = Proportion of combinations where best IS strategy ranks below median on OOS

### Interpretation

| PBO Range | Interpretation | Action |
|-----------|----------------|--------|
| < 0.15 | **PASS** - Low overfitting risk | ✅ Deploy to production |
| 0.15 - 0.30 | **MARGINAL** - Moderate risk | ⚠️ Review other guards |
| 0.30 - 0.50 | **FAIL** - High risk | ❌ Reject strategy |
| > 0.50 | **CRITICAL** - Certain overfit | ❌ Reject strategy |

## Purging and Embargo

### Purging (`purge_gap`)

**Purpose**: Prevent look-ahead bias from overlapping observations

**How it works**:
- Removes observations within `purge_gap` of test boundaries
- Example: `purge_gap=5` removes 5 bars before and after test set

**When to use**:
- High-frequency data (1m, 5m bars): Use `purge_gap=5-10`
- Daily+ data: Use `purge_gap=0` (minimal overlap)

**Visual Example**:
```
Original:
Train: [0,1,2,3,4,5,6,7,8,9]  Test: [10,11,12,13,14]  Train: [15,16,17,18,19]

With purge_gap=2:
Train: [0,1,2,3,4,5,6,7]      Test: [10,11,12,13,14]  Train: [17,18,19]
       (removed: 8,9)                                   (removed: 15,16)
```

### Embargo (`embargo_pct`)

**Purpose**: Prevent reverse leakage from test to training

**How it works**:
- Removes `embargo_pct` of observations AFTER test set
- Example: `embargo_pct=0.01` removes 1% of bars after test

**When to use**:
- Always recommended: Use `embargo_pct=0.01` (1%)
- Conservative: Use `embargo_pct=0.02` (2%)

**Visual Example**:
```
With embargo_pct=0.01 (10 bars out of 1000):

Train: [0-9]  Test: [10-14]  Embargo: [15-24]  Train: [25-999]
                              (removed)
```

## API Reference

### `pbo_with_cpcv()`

```python
def pbo_with_cpcv(
    returns_matrix: np.ndarray,
    n_splits: int = 6,
    n_test_splits: int = 2,
    purge_gap: int = 0,
    embargo_pct: float = 0.01,
    threshold: float = 0.15,
) -> CPCVPBOResult
```

**Parameters**:
- `returns_matrix`: Shape (n_trials, n_periods) - Returns for each trial/strategy
- `n_splits`: Total number of time-based splits (default 6)
- `n_test_splits`: Number of splits for testing (default 2, gives C(6,2)=15)
- `purge_gap`: Observations to purge around test boundaries (default 0)
- `embargo_pct`: Percentage to embargo after test set (default 0.01)
- `threshold`: Maximum acceptable PBO (default 0.15)

**Returns**: `CPCVPBOResult` with fields:
- `pbo`: Probability of overfitting [0, 1]
- `pbo_median_rank`: Median rank of best IS strategies on OOS
- `n_combinations`: Number of CPCV combinations tested
- `threshold`: Threshold for pass/fail
- `passed`: Boolean indicating if PBO < threshold
- `is_sharpes_mean`: Mean IS Sharpe across combinations
- `oos_sharpes_mean`: Mean OOS Sharpe across combinations
- `wfe_cpcv`: Walk-Forward Efficiency (OOS/IS)
- `logits`: Relative ranks for each combination

### `guard_cpcv_pbo()`

```python
def guard_cpcv_pbo(
    returns_matrix: np.ndarray,
    threshold: float = 0.15,
    n_splits: int = 6,
    n_test_splits: int = 2,
    purge_gap: int = 0,
    embargo_pct: float = 0.01,
) -> dict
```

**Purpose**: Guard function for integration with validation pipeline

**Returns**: Dict with standardized guard format compatible with `run_guards_multiasset.py`

## Usage Examples

### Example 1: Basic Validation

```python
from crypto_backtest.validation.cpcv import pbo_with_cpcv
import numpy as np

# Load returns matrix
returns = np.load("returns_matrix_ETH_20260126.npy")

# Validate with default settings
result = pbo_with_cpcv(returns)

if result.passed:
    print(f"✅ PASS - PBO={result.pbo:.2%} < {result.threshold}")
else:
    print(f"❌ FAIL - PBO={result.pbo:.2%} >= {result.threshold}")
```

### Example 2: Custom Configuration

```python
# More conservative: C(7,3) = 35 combinations
result = pbo_with_cpcv(
    returns,
    n_splits=7,
    n_test_splits=3,
    purge_gap=10,      # 10-bar purge for 5m data
    embargo_pct=0.02,  # 2% embargo
    threshold=0.10,    # Stricter threshold (10%)
)
```

### Example 3: Pipeline Integration

```python
from crypto_backtest.validation.cpcv import guard_cpcv_pbo

# Use guard function for pipeline
guard_result = guard_cpcv_pbo(
    returns,
    threshold=0.15,
    n_splits=6,
    n_test_splits=2,
)

print(f"Guard: {guard_result['guard']}")
print(f"Pass: {guard_result['pass']}")
print(f"PBO: {guard_result['pbo']}")
print(f"Interpretation: {guard_result['interpretation']}")
```

### Example 4: Comparing Strategies

```python
# Compare two different parameter sets
returns_baseline = np.load("returns_baseline.npy")
returns_optimized = np.load("returns_optimized.npy")

result_baseline = pbo_with_cpcv(returns_baseline)
result_optimized = pbo_with_cpcv(returns_optimized)

print(f"Baseline PBO: {result_baseline.pbo:.2%}")
print(f"Optimized PBO: {result_optimized.pbo:.2%}")

if result_optimized.pbo < result_baseline.pbo:
    print("✅ Optimization reduced overfitting")
else:
    print("❌ Optimization increased overfitting")
```

## Configuration Recommendations

### For Different Asset Classes

| Asset Class | n_splits | n_test_splits | purge_gap | embargo_pct | Combinations |
|-------------|----------|---------------|-----------|-------------|--------------|
| Crypto (1h) | 6 | 2 | 0 | 0.01 | 15 |
| Crypto (5m) | 6 | 2 | 5 | 0.01 | 15 |
| Stocks (daily) | 6 | 2 | 0 | 0.01 | 15 |
| Forex (1m) | 6 | 2 | 10 | 0.02 | 15 |

### For Different Data Lengths

| Data Length | n_splits | Rationale |
|-------------|----------|-----------|
| < 1000 bars | 4 | Too few bars for many splits |
| 1000-5000 bars | 6 | Standard (default) |
| 5000-10000 bars | 7 | More splits for better coverage |
| > 10000 bars | 8 | Maximum coverage |

## Common Pitfalls

### 1. Data Leakage

**Problem**: Not using purging/embargo allows information leak

**Solution**: Always use `embargo_pct=0.01` minimum, add `purge_gap` for HFT

```python
# ❌ BAD - No leakage prevention
result = pbo_with_cpcv(returns, purge_gap=0, embargo_pct=0.0)

# ✅ GOOD - Proper leakage prevention
result = pbo_with_cpcv(returns, purge_gap=5, embargo_pct=0.01)
```

### 2. Too Few Combinations

**Problem**: Using C(4,1) = 4 combinations doesn't provide enough coverage

**Solution**: Use at least C(5,2) = 10 combinations, preferably C(6,2) = 15

```python
# ❌ BAD - Too few combinations
result = pbo_with_cpcv(returns, n_splits=4, n_test_splits=1)  # 4 combinations

# ✅ GOOD - Sufficient combinations
result = pbo_with_cpcv(returns, n_splits=6, n_test_splits=2)  # 15 combinations
```

### 3. Threshold Too Lenient

**Problem**: Using threshold=0.30 allows overfitted strategies to pass

**Solution**: Use default threshold=0.15 for production

```python
# ❌ BAD - Too lenient
result = pbo_with_cpcv(returns, threshold=0.50)  # 50% overfitting allowed

# ✅ GOOD - Production threshold
result = pbo_with_cpcv(returns, threshold=0.15)  # 15% max overfitting
```

### 4. Insufficient Data

**Problem**: Using CPCV with very short time series

**Solution**: Ensure at least 20 bars per split

```python
# Check data length
n_periods = returns.shape[1]
min_bars_per_split = n_periods / n_splits

if min_bars_per_split < 20:
    print(f"⚠️ WARNING: Only {min_bars_per_split:.0f} bars per split")
    print("Consider reducing n_splits or collecting more data")
```

## Troubleshooting

### High PBO (> 0.30)

**Possible Causes**:
1. Overfitted parameters (too many optimization trials)
2. Period-specific patterns (e.g., bull market only)
3. Insufficient data (fewer than 1000 bars)
4. Unstable strategy (regime-dependent)

**Solutions**:
- Reduce optimization trials (100-200 is usually enough)
- Collect more diverse historical data
- Use regime-stratified validation (TASK 2)
- Simplify strategy (fewer parameters)

### Low WFE (< 0.6)

**Possible Causes**:
1. Severe overfitting (OOS much worse than IS)
2. Regime shift between IS and OOS periods
3. Market structure change

**Solutions**:
- Check regime distribution across IS/OOS splits
- Verify data quality (no gaps, outliers)
- Consider regime-robust optimization

### All Strategies Fail

**Possible Causes**:
1. Threshold too strict for asset class
2. Returns matrix has errors (NaN, inf)
3. Insufficient diversification in trials

**Solutions**:
- Check returns matrix for data quality issues
- Verify optimization trials are diverse
- Consider adjusting threshold for research (not production)

## References

### Papers
- López de Prado, M. (2018) "Advances in Financial Machine Learning" Chapter 7 (CPCV)
- Bailey, D. H., & López de Prado, M. (2014) "The Probability of Backtest Overfitting"

### Related Documentation
- `crypto_backtest/validation/cpcv.py` - Implementation
- `tests/validation/test_cpcv_full.py` - Comprehensive tests
- `examples/cpcv_pbo_usage.py` - Usage examples
- `reports/cpcv-full-activation-20260126.md` - Implementation report

### External Resources
- [MLFinLab Documentation](https://mlfinlab.readthedocs.io/) - CPCV reference implementation
- [QuantConnect Forums](https://www.quantconnect.com/forum/) - PBO discussions
