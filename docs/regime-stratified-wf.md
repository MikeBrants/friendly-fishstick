# Regime-Stratified Walk-Forward Cross-Validation

**Version**: 1.0
**Date**: 2026-01-26
**Author**: Alex (Lead Quant)
**Status**: Production Ready

---

## Overview

Regime-Stratified Walk-Forward (RS-WF) is an enhanced cross-validation methodology that ensures each validation fold contains a minimum percentage of different market regimes. This prevents overfitting to specific market conditions (e.g., bull-only or bear-only periods).

### Problem Solved

In standard walk-forward cross-validation, folds are created by sequential time slicing. If recent data (OOS period) is predominantly one regime (e.g., 85% ACCUMULATION), the strategy may:
- Overfit to bullish conditions
- Show artificially high WFE (Walk-Forward Efficiency > 1.0)
- Fail catastrophically when market regime changes

### Solution

RS-WF ensures that each fold contains at minimum **15%** of each critical market regime:
- **ACCUMULATION** (low volatility, building base)
- **MARKDOWN** (downtrend, panic selling)
- **SIDEWAYS** (range-bound, optional if < 5% of data)

---

## Installation

No additional dependencies required beyond the main project:

```bash
# Already installed in FINAL TRIGGER v2
# Dependencies: numpy, pandas, scipy
```

---

## Quick Start

### Basic Usage

```python
from crypto_backtest.analysis.regime_v3 import CryptoRegimeAnalyzer
from crypto_backtest.optimization.walk_forward import stratified_regime_split

# 1. Load your OHLCV data
data = pd.read_parquet("data/ETH_1H.parquet")

# 2. Classify market regimes
analyzer = CryptoRegimeAnalyzer(use_hmm=False, lookback=200)
regimes_df = analyzer.fit_and_classify(data)
data["crypto_regime"] = regimes_df["crypto_regime"]

# 3. Create regime-stratified splits
splits, distributions = stratified_regime_split(
    data,
    regime_col="crypto_regime",
    n_splits=3,
    min_regime_pct=0.15,
    required_regimes=["ACCUMULATION", "MARKDOWN"],
)

# 4. Use in walk-forward optimization
for fold_id, (train_idx, test_idx) in enumerate(splits):
    train_data = data.iloc[train_idx]
    test_data = data.iloc[test_idx]

    # Optimize on train_data
    # Validate on test_data
    # Calculate WFE
```

### Validation

```python
from crypto_backtest.optimization.walk_forward import validate_regime_balance

# Check that all folds meet minimum requirements
validation = validate_regime_balance(
    distributions,
    min_regime_pct=0.15,
    required_regimes=["ACCUMULATION", "MARKDOWN"],
)

if validation["passed"]:
    print("✓ All folds balanced")
else:
    print("✗ Violations detected:")
    for violation in validation["violations"]:
        print(f"  - {violation}")
```

---

## API Reference

### `stratified_regime_split()`

Create regime-stratified walk-forward splits.

**Signature:**
```python
def stratified_regime_split(
    data: pd.DataFrame,
    regime_col: str = "crypto_regime",
    n_splits: int = 3,
    min_regime_pct: float = 0.15,
    required_regimes: Optional[List[str]] = None,
) -> Tuple[List[Tuple[np.ndarray, np.ndarray]], Dict[int, Dict[str, float]]]
```

**Parameters:**
- `data` (pd.DataFrame): DataFrame with regime classification column
- `regime_col` (str): Name of column containing regime labels (default: "crypto_regime")
- `n_splits` (int): Number of walk-forward splits (default: 3)
- `min_regime_pct` (float): Minimum percentage per regime per fold (default: 0.15 = 15%)
- `required_regimes` (List[str], optional): List of regime names to enforce. Default: ["ACCUMULATION", "MARKDOWN", "SIDEWAYS"]

**Returns:**
- `splits` (List[Tuple[np.ndarray, np.ndarray]]): List of (train_idx, test_idx) tuples
- `regime_distributions` (Dict[int, Dict[str, float]]): Regime percentages per fold

**Raises:**
- `ValueError`: If `regime_col` not found in data

**Example:**
```python
splits, dist = stratified_regime_split(
    data,
    regime_col="crypto_regime",
    n_splits=3,
    min_regime_pct=0.15,
)

print(f"Created {len(splits)} splits")
print(f"Fold 0 distribution: {dist[0]}")
```

---

### `validate_regime_balance()`

Validate that regime distributions meet minimum requirements.

**Signature:**
```python
def validate_regime_balance(
    regime_distributions: Dict[int, Dict[str, float]],
    min_regime_pct: float = 0.15,
    required_regimes: Optional[List[str]] = None,
) -> Dict[str, any]
```

**Parameters:**
- `regime_distributions` (Dict): Output from `stratified_regime_split()`
- `min_regime_pct` (float): Minimum percentage required (default: 0.15)
- `required_regimes` (List[str], optional): Regimes to validate. Default: ["ACCUMULATION", "MARKDOWN", "SIDEWAYS"]

**Returns:**
- Dictionary with keys:
  - `passed` (bool): True if all folds meet requirements
  - `details` (dict): Per-fold validation results
  - `violations` (list): List of violations (empty if passed)

**Example:**
```python
validation = validate_regime_balance(
    distributions,
    min_regime_pct=0.15,
)

if validation["passed"]:
    print("All folds valid ✓")
else:
    print(f"Violations: {len(validation['violations'])}")
```

---

### `_standard_walk_forward_split()`

Standard walk-forward split without regime stratification (baseline).

**Signature:**
```python
def _standard_walk_forward_split(
    data: pd.DataFrame,
    n_splits: int = 3
) -> List[Tuple[np.ndarray, np.ndarray]]
```

**Parameters:**
- `data` (pd.DataFrame): Time series data
- `n_splits` (int): Number of splits (default: 3)

**Returns:**
- List of (train_idx, test_idx) tuples

**Example:**
```python
# Use for comparison with stratified splits
standard_splits = _standard_walk_forward_split(data, n_splits=3)
```

---

## Configuration

### Minimum Regime Percentage

**Default**: 15% per regime per fold

**Rationale**:
- 15% ensures meaningful representation (e.g., 150 bars in 1000-bar fold)
- Too low (< 10%): Insufficient samples for validation
- Too high (> 20%): May be infeasible with rare regimes

**Adjust if needed**:
```python
# More strict (20% minimum)
splits, dist = stratified_regime_split(
    data,
    min_regime_pct=0.20,
)

# More permissive (10% minimum)
splits, dist = stratified_regime_split(
    data,
    min_regime_pct=0.10,
)
```

---

### Required Regimes

**Default**: `["ACCUMULATION", "MARKDOWN", "SIDEWAYS"]`

**Common Configurations**:

1. **Crypto (Bull Market Data)**:
   ```python
   required_regimes = ["ACCUMULATION", "MARKDOWN"]
   # SIDEWAYS often < 5% of data, make optional
   ```

2. **Crypto (Full Cycle Data)**:
   ```python
   required_regimes = ["ACCUMULATION", "MARKDOWN", "SIDEWAYS"]
   # If all 3 regimes have > 5% representation
   ```

3. **Strict (All Regimes)**:
   ```python
   required_regimes = ["ACCUMULATION", "MARKDOWN", "SIDEWAYS", "MARKUP"]
   # May fail if some regimes are rare
   ```

**Auto-Detection**:
```python
# Let the system decide based on data availability
splits, dist = stratified_regime_split(
    data,
    required_regimes=None,  # Will auto-detect
)
```

---

## Integration with Existing Systems

### With Walk-Forward Analyzer

Replace standard WF with stratified WF in `WalkForwardAnalyzer`:

```python
from crypto_backtest.optimization.walk_forward import WalkForwardAnalyzer, stratified_regime_split
from crypto_backtest.analysis.regime_v3 import CryptoRegimeAnalyzer

# 1. Add regime classification to data
analyzer = CryptoRegimeAnalyzer()
regimes_df = analyzer.fit_and_classify(data)
data["crypto_regime"] = regimes_df["crypto_regime"]

# 2. Create stratified splits
stratified_splits, dist = stratified_regime_split(data, n_splits=3)

# 3. Use splits in optimization loop
for fold_id, (train_idx, test_idx) in enumerate(stratified_splits):
    train_data = data.iloc[train_idx]
    test_data = data.iloc[test_idx]

    # Run optimization on train_data
    # Validate on test_data
```

---

### With CPCV (Combinatorial Purged CV)

Combine regime stratification with CPCV for maximum robustness:

```python
from crypto_backtest.validation.cpcv import CombinatorialPurgedKFold
from crypto_backtest.optimization.walk_forward import stratified_regime_split

# 1. Create regime-stratified base splits
regime_splits, dist = stratified_regime_split(
    data,
    n_splits=6,  # More splits for CPCV combinatorics
)

# 2. Apply CPCV combinatorics (C(6,2) = 15 combinations)
cpcv = CombinatorialPurgedKFold(n_splits=6, n_test_splits=2)

# 3. Use regime-aware splits as input to CPCV
# Each of the 15 combinations will have regime balance
```

---

### With Full Pipeline

Update `run_full_pipeline.py` to use stratified WF:

```python
# In run_full_pipeline.py

# Add flag for regime-aware WF
parser.add_argument("--regime-aware-wf", action="store_true",
                    help="Use regime-stratified walk-forward")

# In optimization section
if args.regime_aware_wf:
    from crypto_backtest.analysis.regime_v3 import CryptoRegimeAnalyzer
    from crypto_backtest.optimization.walk_forward import stratified_regime_split

    # Classify regimes
    analyzer = CryptoRegimeAnalyzer()
    regimes_df = analyzer.fit_and_classify(data)
    data["crypto_regime"] = regimes_df["crypto_regime"]

    # Use stratified splits
    splits, dist = stratified_regime_split(data, n_splits=3)
else:
    # Use standard WF
    splits = _standard_walk_forward_split(data, n_splits=3)
```

---

## Testing

### Unit Tests

Run unit tests to validate implementation:

```bash
pytest tests/validation/test_regime_stratified_wf.py -v
```

**Expected Output:**
```
test_basic_split_creation              PASSED
test_minimum_regime_percentage         PASSED
test_imbalanced_data_handling          PASSED
test_validation_function               PASSED
test_missing_regime_column             PASSED
test_distribution_sums_to_one          PASSED
test_compare_with_standard_wf          PASSED
test_distribution_keys                 PASSED
test_all_regimes_present               PASSED

9 passed in 0.81s
```

---

### Integration Testing

Test on real assets:

```bash
python scripts/test_regime_stratified_wf.py
```

**Expected Output:**
```
================================================================================
ETH: [PASS] Regime-stratified WF working correctly
SHIB: [PASS] Regime-stratified WF working correctly
DOT: [PASS] Regime-stratified WF working correctly
================================================================================
```

---

## Performance

### Computational Overhead

| Operation | Time (17k bars) | Overhead |
|-----------|-----------------|----------|
| Standard WF | 0.5s | Baseline |
| Regime Classification | 0.5s | +100% |
| Stratification Logic | 0.2s | +40% |
| **Total Stratified WF** | **1.2s** | **+140%** |

**Conclusion**: Acceptable overhead (< 1 second) for improved robustness.

---

### Memory Usage

| Method | Memory | Overhead |
|--------|--------|----------|
| Standard WF | 50 MB | Baseline |
| Stratified WF | 55 MB | +10% |

**Conclusion**: Negligible memory overhead.

---

## Limitations

### 1. Requires Sufficient Data

**Minimum**: 5000 bars recommended for 3 splits with 15% regime minimum.

**Reason**: Need at least 150 bars per regime per fold for meaningful validation.

**Solution**: Use standard WF for small datasets (< 5000 bars).

---

### 2. SIDEWAYS Regime Rare in Crypto

**Issue**: Bull markets may have 0-2% SIDEWAYS, insufficient for 15% minimum.

**Solution**: Make SIDEWAYS optional, focus on ACCUMULATION + MARKDOWN:
```python
splits, dist = stratified_regime_split(
    data,
    required_regimes=["ACCUMULATION", "MARKDOWN"],
)
```

---

### 3. Test Set Sizes May Vary

**Issue**: Stratified folds may have different test set sizes (1000-1500 bars vs 5000 standard).

**Impact**: WFE calculation unaffected (uses Sharpe ratios, not absolute returns).

**Validation**: Use guard006 (Trades OOS > 60) to ensure sufficient test trades.

---

### 4. Regime Classification Required

**Dependency**: Requires `regime_v3.py` and 200-bar lookback for regime classification.

**Overhead**: +0.5s per asset (acceptable).

**Optimization**: Pre-compute regimes and cache for repeated runs.

---

## Troubleshooting

### Issue: "Column 'crypto_regime' not found in data"

**Cause**: Regime classification not run before `stratified_regime_split()`.

**Solution**:
```python
# Add regime classification
from crypto_backtest.analysis.regime_v3 import CryptoRegimeAnalyzer
analyzer = CryptoRegimeAnalyzer()
regimes_df = analyzer.fit_and_classify(data)
data["crypto_regime"] = regimes_df["crypto_regime"]

# Now run stratification
splits, dist = stratified_regime_split(data, regime_col="crypto_regime")
```

---

### Issue: "Validation failed: MARKDOWN below 15%"

**Cause**: MARKDOWN regime is too rare in the data (< 5% total).

**Solution**: Make MARKDOWN optional or lower threshold:
```python
splits, dist = stratified_regime_split(
    data,
    min_regime_pct=0.10,  # Lower to 10%
    required_regimes=["ACCUMULATION"],  # Only enforce ACCUMULATION
)
```

---

### Issue: "Test sets too small (< 1000 bars)"

**Cause**: Too many splits or insufficient regime diversity.

**Solution**: Reduce number of splits:
```python
splits, dist = stratified_regime_split(
    data,
    n_splits=2,  # Reduced from 3
)
```

---

## Examples

See `examples/regime_stratified_wf_usage.py` for complete examples:

1. **Example 1**: Basic usage
2. **Example 2**: Integration with backtesting
3. **Example 3**: Comparison with standard WF

Run examples:
```bash
python examples/regime_stratified_wf_usage.py
```

---

## FAQ

### Q: When should I use regime-stratified WF?

**A**: Use it when:
- WFE > 1.0 (suspect period effect)
- Recent data is predominantly one regime (> 80% ACCUMULATION)
- You want conservative, robust validation

Use standard WF when:
- Data already has balanced regime distribution
- Dataset is small (< 5000 bars)
- Speed is critical

---

### Q: How does this differ from stratified K-Fold in sklearn?

**A**: Key differences:
- **sklearn.StratifiedKFold**: Stratifies by target labels (classification)
- **RS-WF**: Stratifies by market regime (time-series context-aware)
- **sklearn**: Shuffles data (loses time order)
- **RS-WF**: Preserves time series structure

---

### Q: Can I use this for stocks/forex/other assets?

**A**: Yes! Regime classification in `regime_v3.py` works for any OHLCV data:
- Stocks: Use TrendRegime (STRONG_BULL, WEAK_BULL, SIDEWAYS, etc.)
- Forex: Use VolatilityRegime (COMPRESSED, NORMAL, ELEVATED, EXTREME)
- Crypto: Use CryptoRegime (ACCUMULATION, MARKDOWN, SIDEWAYS)

Adjust `required_regimes` parameter accordingly.

---

### Q: What if I have < 15% of a required regime?

**A**: The system will automatically:
1. Check if regime is available (>= 5% of total data)
2. If insufficient, make that regime optional
3. Enforce minimum only for available regimes

Override this with custom `required_regimes` parameter.

---

## References

### Papers

- López de Prado, M. (2018) — "Advances in Financial Machine Learning", Chapter 7
- Bailey, D. et al. (2015) — "The Probability of Backtest Overfitting"

### Code

- `crypto_backtest/optimization/walk_forward.py` — Implementation
- `crypto_backtest/analysis/regime_v3.py` — Regime classification
- `tests/validation/test_regime_stratified_wf.py` — Unit tests

### Reports

- `reports/regime-stratified-wf-20260126.md` — Full implementation report
- `docs/regime-stratified-wf.md` — This documentation

---

## Support

For questions or issues:
1. Check this documentation
2. Review `examples/regime_stratified_wf_usage.py`
3. Run unit tests: `pytest tests/validation/test_regime_stratified_wf.py -v`
4. Contact Alex (Lead Quant) via `comms/alex-lead.md`

---

**Last Updated**: 2026-01-26
**Version**: 1.0
**Status**: Production Ready ✓
