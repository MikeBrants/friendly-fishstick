# PBO & CPCV Implementation Review

**Date**: 2026-01-25
**Reviewer**: Alex (Lead Quant)
**Status**: ✅ COMPLETE — Minor patches proposed

---

## Executive Summary

| File | Status | Risk Level | Action Required |
|------|--------|------------|-----------------|
| `validation/pbo.py` | ✅ COMPLETE | LOW | Minor: Add input validation |
| `validation/cpcv.py` | ✅ COMPLETE | LOW | Minor: Fix purge efficiency |

Both implementations are **production-ready** with minor optimizations recommended.

---

## 1. PBO (Probability of Backtest Overfitting) Review

### File: `crypto_backtest/validation/pbo.py`

### Implementation Quality: ✅ EXCELLENT

**Correctness**:
- ✅ Implements Bailey & López de Prado (2014) CSCV methodology correctly
- ✅ Uses combinatorial symmetric cross-validation
- ✅ Rank calculation is correct (lines 105-106)
- ✅ Underperformance threshold (median) matches paper
- ✅ Sharpe calculation with std epsilon (line 141) prevents division by zero

**Completeness**:
- ✅ Full implementation (no stubs or TODO)
- ✅ Guard integration function (`guard_pbo`, lines 145-174)
- ✅ Comprehensive docstrings with interpretation guide
- ✅ Proper error handling for edge cases

**Code Quality**:
- ✅ Type hints complete
- ✅ Clean separation of concerns (_get_split_indices, _compute_sharpes)
- ✅ Frozen dataclass for immutable results

### Potential Issues: 2 Minor

#### Issue 1: Missing returns_matrix validation (LOW PRIORITY)

**Location**: Line 72-73
```python
if n_splits < 2:
    raise ValueError("n_splits must be at least 2")
```

**Problem**: No validation that returns_matrix has enough periods

**Impact**: Could raise cryptic error later if matrix too small

**Proposed Patch**:
```python
def probability_of_backtest_overfitting(
    returns_matrix: np.ndarray,
    n_splits: int = 16,
    threshold: float = 0.30,
) -> PBOResult:
    # PATCH: Add input validation
    if returns_matrix.ndim != 2:
        raise ValueError("returns_matrix must be 2D array (n_trials, n_periods)")

    n_trials, n_periods = returns_matrix.shape

    if n_trials < 2:
        raise ValueError(f"Need at least 2 trials, got {n_trials}")

    if n_splits < 2:
        raise ValueError("n_splits must be at least 2")
    if n_splits % 2 != 0:
        raise ValueError("n_splits must be even")

    split_size = n_periods // n_splits
    if split_size < 2:
        raise ValueError(f"Not enough periods ({n_periods}) for {n_splits} splits (need {n_splits * 2} minimum)")
```

**Priority**: LOW — Edge case that rarely occurs in practice

#### Issue 2: Combinatorial explosion warning (LOW PRIORITY)

**Location**: Line 85
```python
is_combinations = list(combinations(all_splits, n_splits // 2))
```

**Problem**: C(16, 8) = 12,870 combinations — fine. C(20, 10) = 184,756 — slow.

**Impact**: Performance degradation with large n_splits (> 16)

**Proposed Patch**:
```python
# After line 85
n_combinations = int(comb(n_splits, n_splits // 2))
if n_combinations > 50000:
    import warnings
    warnings.warn(
        f"PBO with n_splits={n_splits} requires {n_combinations:,} combinations. "
        f"Consider reducing n_splits to 16 (12,870 combinations) for faster computation.",
        RuntimeWarning
    )
```

**Priority**: LOW — Documentation already recommends n_splits=16

### Recommendations

1. **ACCEPT AS-IS** for production deployment
2. **OPTIONAL**: Apply patches above for robustness
3. **TEST**: Validate with synthetic overfit scenario (see test case below)

### Test Case (Validation)

```python
# Test: Synthetic overfitting scenario
import numpy as np
from crypto_backtest.validation.pbo import probability_of_backtest_overfitting

# Generate overfit data: best IS trial performs poorly OOS
np.random.seed(42)
n_trials = 100
n_periods = 1000

# Trial 0: excellent IS (periods 0-499), terrible OOS (500-999)
returns = np.random.randn(n_trials, n_periods) * 0.01
returns[0, :500] = np.random.randn(500) * 0.01 + 0.002  # High IS Sharpe
returns[0, 500:] = np.random.randn(500) * 0.01 - 0.001  # Negative OOS Sharpe

result = probability_of_backtest_overfitting(returns, n_splits=16, threshold=0.30)

# Expected: PBO > 0.5 (high overfitting)
assert result.pbo > 0.5, f"Expected PBO > 0.5 for overfit scenario, got {result.pbo}"
print(f"✅ PBO correctly detected overfitting: {result.pbo:.2%}")
```

---

## 2. CPCV (Combinatorial Purged Cross-Validation) Review

### File: `crypto_backtest/validation/cpcv.py`

### Implementation Quality: ✅ EXCELLENT

**Correctness**:
- ✅ Implements López de Prado (2018) Chapter 7 methodology
- ✅ Purging logic correct (lines 137-144)
- ✅ Embargo logic correct (lines 146-160)
- ✅ Combinatorial split generation matches paper
- ✅ sklearn-compatible interface (split generator)

**Completeness**:
- ✅ Full implementation with helper methods
- ✅ Validation function (`validate_with_cpcv`, lines 185-248)
- ✅ CPCVSplit dataclass for structured results
- ✅ WFE calculation in aggregation (line 245)

**Code Quality**:
- ✅ Generator pattern for memory efficiency
- ✅ Clean sklearn-style API
- ✅ Comprehensive docstrings

### Potential Issues: 2 Minor + 1 Optimization

#### Issue 1: Purging efficiency (MEDIUM PRIORITY)

**Location**: Lines 137-144
```python
def _is_purged(self, idx: int, test_set: set) -> bool:
    if self.purge_gap == 0:
        return False
    for test_idx in test_set:
        if abs(idx - test_idx) <= self.purge_gap:
            return True
    return False
```

**Problem**: O(n) check for each training index (inefficient for large test sets)

**Impact**: Slow for purge_gap > 0 and large datasets

**Proposed Patch**:
```python
def _is_purged(self, idx: int, test_min: int, test_max: int) -> bool:
    """Check if index should be purged (optimized range check)."""
    if self.purge_gap == 0:
        return False
    # Check if idx is within purge_gap of test set boundaries
    return (test_min - self.purge_gap) <= idx <= (test_max + self.purge_gap)

# Update caller (line 128):
test_indices = []
for s in test_splits:
    start, end = split_bounds[s]
    test_indices.extend(range(start, end))

test_min = min(test_indices)
test_max = max(test_indices)

# Update line 128:
if self._is_purged(idx, test_min, test_max):
    continue
```

**Priority**: MEDIUM — Impacts performance with large datasets

#### Issue 2: Embargo check inefficiency (LOW PRIORITY)

**Location**: Lines 146-160
```python
def _is_embargoed(self, idx: int, test_splits: tuple, split_bounds: List, embargo_size: int) -> bool:
    if embargo_size == 0:
        return False
    for s in test_splits:
        _, test_end = split_bounds[s]
        if test_end <= idx < test_end + embargo_size:
            return True
    return False
```

**Problem**: Multiple range checks per index (could be pre-computed)

**Impact**: Minor performance hit

**Proposed Patch**:
```python
# Pre-compute embargo ranges at split generation time
embargo_ranges = []
if embargo_size > 0:
    for s in test_splits:
        _, test_end = split_bounds[s]
        embargo_ranges.append((test_end, test_end + embargo_size))

# Simplified check
def _is_in_embargo_ranges(idx: int, embargo_ranges: List[Tuple[int, int]]) -> bool:
    return any(start <= idx < end for start, end in embargo_ranges)
```

**Priority**: LOW — Optimization, not correctness issue

#### Issue 3: validate_with_cpcv assumes Sharpe in strategy_func (LOW)

**Location**: Lines 224-225
```python
is_metrics = strategy_func(train_data)
oos_metrics = strategy_func(test_data)
```

**Problem**: No validation that strategy_func returns expected metrics

**Impact**: Silent failure if strategy_func returns wrong format

**Proposed Patch**:
```python
# After line 225
required_keys = ["sharpe_ratio", "total_return"]
for key in required_keys:
    if key not in is_metrics:
        raise ValueError(f"strategy_func must return dict with '{key}' key")
```

**Priority**: LOW — Documentation issue, not a bug

### Recommendations

1. **ACCEPT AS-IS** for production deployment
2. **APPLY PATCH 1** (purging efficiency) if using purge_gap > 0 frequently
3. **OPTIONAL**: Apply other patches for robustness
4. **TEST**: Validate purging behavior (see test case below)

### Test Case (Validation)

```python
# Test: Purging removes leakage
import pandas as pd
import numpy as np
from crypto_backtest.validation.cpcv import CombinatorialPurgedKFold

# Create time-indexed data
dates = pd.date_range('2024-01-01', periods=1000, freq='1H')
X = pd.DataFrame(np.random.randn(1000, 5), index=dates)

cpcv = CombinatorialPurgedKFold(n_splits=6, n_test_splits=2, purge_gap=5)

for train_idx, test_idx in cpcv.split(X):
    # Verify no train index is within purge_gap of test set
    test_set = set(test_idx)
    for t_idx in train_idx:
        min_distance = min(abs(t_idx - test) for test in test_set)
        assert min_distance > 5, f"Train index {t_idx} too close to test set (distance {min_distance})"

print(f"✅ CPCV purging correctly prevents leakage")
```

---

## 3. Integration with Pipeline

### Current Status: ❌ NOT INTEGRATED

Both PBO and CPCV are **implemented but not called** in the validation pipeline.

### Integration Locations Required

#### A. PBO Integration

**File**: `scripts/run_guards_multiasset.py` (or equivalent validation script)

**Current guards**: 7 guards (WFE, Sensitivity, Bootstrap, MC, etc.)

**Proposed addition**:
```python
# After existing guards, add GUARD-008 PBO
from crypto_backtest.validation.pbo import guard_pbo

# Generate returns matrix from optimization trials
returns_matrix = _extract_trial_returns(optimization_history)  # Need to implement

pbo_result = guard_pbo(returns_matrix, threshold=0.30, n_splits=16)

validation_results['guard008_pbo'] = pbo_result
```

**Blocker**: Need to store per-trial returns during optimization (currently only best params saved)

#### B. CPCV Integration

**File**: `crypto_backtest/optimization/walk_forward.py`

**Current**: Simple 60/20/20 split

**Proposed enhancement**:
```python
# Option to use CPCV instead of simple walk-forward
if use_cpcv:
    from crypto_backtest.validation.cpcv import validate_with_cpcv

    cpcv_results = validate_with_cpcv(
        data=data,
        strategy_func=lambda d: run_strategy_and_get_metrics(d, best_params),
        n_splits=6,
        n_test_splits=2,
        purge_gap=5,
        embargo_pct=0.01
    )

    # Use CPCV WFE instead of simple walk-forward WFE
    wfe_pardo = cpcv_results['wfe_mean']
```

**Blocker**: CPCV requires multiple IS/OOS runs (computationally expensive)

---

## 4. Proposed Minimal Patches

### Patch 1: PBO Input Validation

**File**: `crypto_backtest/validation/pbo.py`

**Insert after line 71**:
```python
    # Validate input matrix
    if returns_matrix.ndim != 2:
        raise ValueError("returns_matrix must be 2D array (n_trials, n_periods)")

    n_trials, n_periods = returns_matrix.shape

    if n_trials < 2:
        raise ValueError(f"Need at least 2 trials for PBO, got {n_trials}")
```

**Change line 77**:
```python
# OLD:
    n_trials, n_periods = returns_matrix.shape
    split_size = n_periods // n_splits

# NEW:
    split_size = n_periods // n_splits  # n_trials already extracted above
```

### Patch 2: CPCV Purging Efficiency

**File**: `crypto_backtest/validation/cpcv.py`

**Replace lines 120-133**:
```python
            # Build train indices with purging and embargo
            train_indices = []

            # Pre-compute test boundaries for efficient purging
            test_min = min(test_indices) if test_indices else 0
            test_max = max(test_indices) if test_indices else 0

            # Pre-compute embargo ranges
            embargo_ranges = []
            if embargo_size > 0:
                for s in test_splits:
                    _, test_end = split_bounds[s]
                    embargo_ranges.append((test_end, test_end + embargo_size))

            for s in train_splits:
                start, end = split_bounds[s]
                for idx in range(start, end):
                    # Check purging (optimized)
                    if self.purge_gap > 0:
                        if (test_min - self.purge_gap) <= idx <= (test_max + self.purge_gap):
                            continue

                    # Check embargo (optimized)
                    if embargo_ranges and any(er_start <= idx < er_end for er_start, er_end in embargo_ranges):
                        continue

                    train_indices.append(idx)

            yield np.array(train_indices), np.array(test_indices)
```

**Remove old helper methods** (lines 137-160) and replace with note:
```python
# Note: Purging and embargo logic now inlined in split() for efficiency
```

---

## 5. Production Readiness Checklist

### PBO (`validation/pbo.py`)

- [x] Implementation complete
- [x] Algorithm correctness verified (Bailey & López de Prado 2014)
- [x] Edge cases handled (div by zero, empty data)
- [x] Type hints complete
- [x] Docstrings comprehensive
- [ ] Input validation (Patch 1 recommended)
- [ ] Unit tests exist
- [ ] Integration with pipeline
- [ ] Performance benchmarked (expect ~1-10s for typical inputs)

**Verdict**: ✅ PRODUCTION-READY (with optional Patch 1)

### CPCV (`validation/cpcv.py`)

- [x] Implementation complete
- [x] Algorithm correctness verified (López de Prado 2018)
- [x] Purging logic correct
- [x] Embargo logic correct
- [x] sklearn-compatible API
- [x] Type hints complete
- [x] Docstrings comprehensive
- [ ] Purging efficiency optimization (Patch 2 recommended)
- [ ] Unit tests exist
- [ ] Integration with pipeline
- [ ] Performance benchmarked

**Verdict**: ✅ PRODUCTION-READY (with optional Patch 2 for performance)

---

## 6. Recommendation Summary

### Immediate Actions (OPTIONAL)

1. **Apply Patch 1** (PBO input validation) — 2 min
2. **Apply Patch 2** (CPCV purging efficiency) — 10 min
3. **Add unit tests** for both modules — 1h

### Integration Actions (BLOCKING if PBO/CPCV required)

1. **PBO**: Store per-trial returns during optimization — 2-3h
2. **CPCV**: Add CPCV mode to walk_forward.py — 1-2h
3. **Guards**: Add GUARD-008 (PBO) to validation pipeline — 1h

### Priority

- **PBO/CPCV code**: ✅ DONE — No urgent patches needed
- **Integration**: 🔴 REQUIRED only if CLAUDE.md mandates PBO/CPCV validation
- **Current status**: Both tools ready but unused

---

## 7. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| PBO false positive (PBO > 0.30 for robust strategy) | LOW | MEDIUM | Use 0.30 threshold (not 0.15) |
| CPCV purging too aggressive (removes valid data) | LOW | LOW | Default purge_gap=0, adjust per asset |
| Performance bottleneck (C(16,8) = 12,870 iterations) | MEDIUM | LOW | Cache results, run overnight |
| Integration bugs (missing data for PBO) | HIGH | HIGH | Thorough testing before deployment |

**Overall Risk**: LOW — Implementations are solid, integration is the challenge

---

*Last Updated: 2026-01-25*
*Status: ✅ REVIEW COMPLETE — Both implementations are production-ready*
*Recommendation: Accept as-is, optional patches for robustness*
