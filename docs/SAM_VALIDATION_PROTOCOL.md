# SAM VALIDATION PROTOCOL
**Created**: 2026-01-26
**Version**: 1.0
**Owner**: Sam (QA)

---

## VALIDATION PROTOCOL

### Phase 1: Unit Tests

#### 1.1 PBO Tests (GUARD-008)
**Command**:
```bash
pytest tests/validation/test_guard008.py -v
```

**Expected**: 8/8 PASS

**Covered**:
- ✅ Function exists and callable
- ✅ Return format validation (dict with correct keys)
- ✅ PBO probability in range [0, 1]
- ✅ Threshold logic (pass/fail based on 0.30)
- ✅ n_splits validation (even number, >= 2)
- ✅ Interpretation string generation
- ✅ Perfect strategy (low PBO expected)
- ✅ Random strategy (valid PBO calculation)

**Coverage Gaps Identified**: See Section S1 below

**Failure Action**:
- If 0-2 tests fail: Fix individual test issues
- If 3+ tests fail: ROLLBACK - PBO implementation has regression
- If all fail: CRITICAL - Do not merge

---

#### 1.2 CPCV Tests
**Status**: ❌ NO TESTS EXIST

**Command** (once created):
```bash
pytest tests/validation/test_cpcv.py -v
```

**Expected**: 8/8 PASS (proposed tests in Section S2)

**Failure Action**:
- Any failure: Fix before integration
- CPCV is on-demand only, not blocking for production

---

#### 1.3 WFE Dual Tests
**Command**:
```bash
pytest tests/optimization/test_walk_forward_dual.py -v
```

**Expected**: 4/4 PASS

**Covered**:
- ✅ WFE Pardo vs Return Efficiency distinction
- ✅ Degradation percentage calculation
- ✅ WFE Pardo uses Sharpe-based calculation
- ✅ Walk-forward result fields present

**Failure Action**:
- Any failure: BLOCKER - Do not proceed to integration

---

#### 1.4 Regression Test Suite
**Command**:
```bash
pytest tests/ -v --ignore=tests/validation/test_cpcv.py
```

**Expected**: 51/51 PASS (or 43/43 if test_cpcv.py not yet created)

**Critical Tests**:
- Backtest engine: 6 tests
- Indicators: 6 tests
- Optimization: 4 tests
- Overfitting report: 2 tests
- Portfolio: 4 tests

**Failure Action**:
- 0 failures: PROCEED
- 1-2 failures: Review - may be unrelated pre-existing issues
- 3+ failures: ROLLBACK - Changes broke existing functionality

**Duration**: ~10-15 seconds (fast unit tests)

---

### Phase 2: Integration Tests

#### 2.1 Single Asset Validation (ETH Baseline)
**Purpose**: Verify guards execute correctly on known-good asset

**Command**:
```bash
python scripts/run_guards_multiasset.py \
  --assets ETH \
  --params-file outputs/multiasset_params_phase2_20260125_170000.csv \
  --data-dir data \
  --outputs-dir outputs/validation_test \
  --guards mc,sensitivity,bootstrap,stress,regime,trade_dist,wfe,pbo \
  --mc-iterations 100 \
  --bootstrap-samples 1000 \
  --sensitivity-range 2 \
  --overfit-trials 300 \
  --workers 1
```

**Expected Output**:
```
ETH validation report:
GUARD-001 Monte Carlo: p < 0.05 → PASS
GUARD-002 Sensitivity: variance < 15% → PASS
GUARD-003 Bootstrap CI: lower > 1.0 → PASS
GUARD-005 Trade Dist: top10 < 40% → PASS
GUARD-006 Stress: Sharpe > 1.0 → PASS
GUARD-007 Regime: mismatch < 1% → PASS
GUARD-008 PBO: ⚠️ "returns_matrix not tracked" → EXPECTED FAIL (see Section S4)
GUARD-WFE: wfe_pardo 1.22 → ⚠️ SUSPECT (should be 0.6-0.9 after fix)
```

**Critical Checks**:
1. **WFE Value**:
   - Current: 1.22 (OOS better than IS - anomaly)
   - Expected after fix: 0.60-0.90 (healthy degradation)
   - If still > 1.0: Period effect not fixed

2. **PBO Status**:
   - Expected: FAIL with error "returns_matrix not tracked"
   - Should NOT crash pipeline
   - If crashes: BLOCKER - see Section S4

3. **All Other Guards**: Should PASS (ETH is production asset)

**Duration**: ~5-10 minutes (1 asset, reduced iterations)

**Failure Action**:
- WFE still > 1.0: Period effect fix incomplete - DO NOT MERGE
- Guards 001-007 fail: Regression in guard logic - INVESTIGATE
- PBO crashes: BLOCKER - must fix graceful error handling
- All guards PASS: PROCEED to Phase 2.2

---

#### 2.2 Multi-Asset Test (ETH, SHIB, DOT)
**Purpose**: Verify WFE correction on suspect assets

**Command**:
```bash
python scripts/run_guards_multiasset.py \
  --assets ETH SHIB DOT \
  --params-file outputs/multiasset_params_phase2_20260125_170000.csv \
  --data-dir data \
  --outputs-dir outputs/validation_test \
  --guards wfe,pbo,mc \
  --mc-iterations 100 \
  --workers 3
```

**Expected WFE Values** (Post-Fix):
| Asset | Current WFE | Expected Post-Fix | Verdict |
|-------|-------------|-------------------|---------|
| ETH | 1.22 | 0.65-0.85 | Was suspect |
| SHIB | 2.27 | 0.55-0.75 | Was severe |
| DOT | 1.74 | 0.60-0.80 | Was suspect |

**Critical Validation**:
- ALL WFE values should drop from >1.0 to 0.5-0.9 range
- If any WFE still >1.0: Period effect fix INCOMPLETE
- If any WFE <0.4: Overcorrection or calculation error

**Duration**: ~15-20 minutes (3 assets, reduced iterations)

**Failure Criteria**:
- >1 asset with WFE >1.0: ROLLBACK - Fix ineffective
- >1 asset with WFE <0.4: ROLLBACK - Overcorrection
- Guards crash: BLOCKER - Must fix before proceeding

**Success Criteria**:
- 3/3 assets show WFE in 0.5-0.9 range
- No crashes or timeout errors
- PBO fails gracefully with expected error message

---

### Phase 3: Regression Check (All PROD Assets)

#### 3.1 Full Production Suite
**Purpose**: Ensure no assets regress from PASS to FAIL due to WFE fix

**Command**:
```bash
python scripts/run_guards_multiasset.py \
  --assets SHIB TIA DOT NEAR DOGE ANKR ETH JOE YGG MINA CAKE RUNE EGLD AVAX \
  --params-file outputs/multiasset_params_phase2_20260125_170000.csv \
  --data-dir data \
  --outputs-dir outputs/regression_check \
  --guards wfe,mc,sensitivity,bootstrap \
  --mc-iterations 500 \
  --bootstrap-samples 5000 \
  --workers 6
```

**Expected Results**:
- **Previous PASS count**: 14/14 assets (with WFE >1.0 anomaly)
- **Expected PASS count**: 14/14 assets (with corrected WFE 0.5-0.9)

**Breakdown by WFE Category**:
1. **WFE Suspect (7 assets)**: SHIB, TIA, DOT, NEAR, DOGE, ETH, MINA
   - Expected: All should show WFE drop to 0.5-0.9
   - Should still PASS other guards

2. **WFE OK (7 assets)**: ANKR, JOE, YGG, CAKE, RUNE, EGLD, AVAX
   - Expected: WFE remains stable (0.6-0.9)
   - No change in PASS/FAIL status

**Failure Threshold**:
- **0 new FAILs**: EXCELLENT - Proceed to Phase 4
- **1 new FAIL**: ACCEPTABLE - Investigate individual asset
- **2 new FAILs**: REVIEW - May indicate systematic issue
- **3+ new FAILs**: ROLLBACK - Changes breaking production assets

**Duration**: ~2-3 hours (14 assets, full guards, workers=6)

**Critical Checks**:
```python
# Post-run analysis
df = pd.read_csv("outputs/regression_check/multiasset_guards_summary_*.csv")

# Check 1: No new FAILs
prev_pass = 14
new_pass = df["all_pass"].sum()
assert new_pass >= prev_pass - 2, f"Too many regressions: {prev_pass} → {new_pass}"

# Check 2: WFE values normalized
wfe_suspect = df[df["asset"].isin(["SHIB", "TIA", "DOT", "NEAR", "DOGE", "ETH", "MINA"])]
assert (wfe_suspect["guard_wfe"] < 1.0).all(), "WFE still >1.0 for suspect assets"
assert (wfe_suspect["guard_wfe"] > 0.4).all(), "WFE overcorrected (<0.4)"

# Check 3: WFE OK assets unchanged
wfe_ok = df[df["asset"].isin(["ANKR", "JOE", "YGG", "CAKE", "RUNE", "EGLD", "AVAX"])]
assert (wfe_ok["guard_wfe"] >= 0.5).all(), "Previously OK assets degraded"
```

---

### Phase 4: Manual Verification

#### 4.1 Visual Inspection
**Check**: Review 3 validation reports (ETH, SHIB, DOT)

**Files**:
```
outputs/validation_test/ETH_validation_report_*.txt
outputs/validation_test/SHIB_validation_report_*.txt
outputs/validation_test/DOT_validation_report_*.txt
```

**Verify**:
1. **WFE Line**: Should show corrected value (0.5-0.9)
2. **PBO Line**: Should show graceful failure or SKIP (not crash)
3. **All Guards Section**: Format correct, interpretations present
4. **ALL PASS**: YES (except PBO if not implemented)

---

#### 4.2 Spot Check Calculations
**Purpose**: Manually verify WFE Pardo formula

**ETH Example**:
```python
# From outputs/ETH_wfe_dual_*.json
is_sharpe = 2.64  # Example value
oos_sharpe = 1.75  # Example value (after fix)
wfe_pardo = oos_sharpe / is_sharpe
# Expected: 1.75 / 2.64 = 0.66 (healthy degradation)

# OLD (wrong): wfe_return = oos_return / is_return → caused >1.0 values
```

**Red Flags**:
- WFE Pardo = WFE Return (should be different formulas)
- WFE Pardo > 1.0 (OOS should not exceed IS)
- WFE Pardo < 0.3 (excessive degradation, possible bug)

---

#### 4.3 PBO Error Message Validation
**Purpose**: Ensure PBO fails gracefully when returns_matrix unavailable

**Check**:
```bash
grep -r "returns_matrix not tracked" outputs/validation_test/*.txt
```

**Expected**:
- All validation reports should contain PBO error message
- No Python tracebacks or crashes
- Pipeline continues past PBO failure

**Red Flag**:
- If grep returns empty: PBO not attempted or error message changed
- If crash logs exist: PBO blocking pipeline (BLOCKER)

---

#### 4.4 Cross-Reference Asset Config
**Purpose**: Verify production configs not accidentally modified

**Command**:
```bash
git diff crypto_backtest/config/asset_config.py
```

**Expected**: NO CHANGES

**If changes found**:
- Review each change individually
- Ensure no production params altered
- If unintended: Revert config file

---

## PASS/FAIL CRITERIA SUMMARY

### Unit Tests (Phase 1)
| Status | Criteria | Action |
|--------|----------|--------|
| ✅ PASS | 51/51 tests pass | Proceed to Phase 2 |
| ⚠️ WARN | 49-50/51 pass | Review failures, may proceed |
| 🔴 FAIL | <49/51 pass | ROLLBACK |

### Integration Tests (Phase 2)
| Status | Criteria | Action |
|--------|----------|--------|
| ✅ PASS | ETH WFE 0.5-0.9, all guards OK | Proceed to Phase 3 |
| ✅ PASS | SHIB/DOT/ETH all WFE <1.0 | Proceed to Phase 3 |
| 🔴 FAIL | Any WFE still >1.0 | ROLLBACK - Fix incomplete |

### Regression Tests (Phase 3)
| Status | Criteria | Action |
|--------|----------|--------|
| ✅ PASS | 14/14 PASS, all WFE normalized | Proceed to Phase 4 |
| ⚠️ WARN | 13/14 PASS | Review failure, may proceed |
| 🔴 FAIL | ≤12/14 PASS | ROLLBACK - Systematic issue |

### Manual Verification (Phase 4)
| Check | Criteria | Status |
|-------|----------|--------|
| Reports | WFE values corrected | Visual |
| Calculations | WFE Pardo formula correct | Manual |
| PBO | Fails gracefully | Grep check |
| Config | No unintended changes | Git diff |

---

## ESTIMATED TOTAL DURATION

| Phase | Duration | Parallelizable |
|-------|----------|----------------|
| Phase 1 (Unit) | 15 seconds | Yes (pytest -n auto) |
| Phase 2.1 (ETH) | 5-10 minutes | No |
| Phase 2.2 (3 assets) | 15-20 minutes | Yes (workers=3) |
| Phase 3 (14 assets) | 2-3 hours | Yes (workers=6) |
| Phase 4 (Manual) | 15-20 minutes | No |
| **TOTAL** | **2.5-3.5 hours** | - |

**Optimization**: Run Phase 1 and 2.1 sequentially (fast), then Phase 2.2 and 3 in parallel overnight.

---

## ROLLBACK PROCEDURE

If ANY phase triggers ROLLBACK:

1. **Immediate**:
   ```bash
   git stash  # Save any uncommitted work
   git checkout main  # Return to last stable
   ```

2. **Document Failure**:
   - Log which phase failed
   - Capture error messages
   - Save all output files to `outputs/failed_validation_<timestamp>/`

3. **Root Cause Analysis**:
   - Review implementation changes
   - Check if period effect fix applied correctly
   - Verify WFE Pardo formula uses `oos_sharpe / is_sharpe`

4. **Fix and Retry**:
   - Apply fix to separate branch
   - Re-run validation from Phase 1
   - Only merge after full PASS

---

## CONTINUOUS MONITORING

Post-merge, track these metrics:

1. **WFE Distribution**: Should be 0.5-0.9 for all assets
2. **PASS Rate**: Should remain 14/14 or improve
3. **PBO Adoption**: Track when returns_matrix tracking implemented
4. **False Positives**: Monitor for assets failing due to overcorrection

**Quarterly Review**: Re-run full validation suite on all production assets

---

## NOTES

- PBO (GUARD-008) will fail gracefully until returns_matrix tracking implemented (see Section S4)
- CPCV tests are nice-to-have (on-demand feature, not production critical)
- If validation takes >4 hours, reduce iterations (trade speed for precision)
- Always use `--workers 1` for reproducibility-critical tests

---

**END OF VALIDATION PROTOCOL**
