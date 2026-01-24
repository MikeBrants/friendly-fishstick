# CASEY - Orchestrator & Validation Lead

**Role**: Strategy, Prioritization, Multi-Asset Validation  
**Current Phase**: POST-PR7 INTEGRATION TESTING  
**Last Updated**: 24 janvier 2026, 18:50 UTC

---

## 🎯 CURRENT ASSIGNMENT

### Task C1: Execute Guards on 8 Pending Assets [🔴 URGENT]
**Priority**: 🔴 CRITICAL  
**Status**: ⏳ READY TO START

**Context**: Jordan's overnight run validated **7 assets with 7/7 guards PASS** + **8 more assets pending guards**. TIA (5.16 Sharpe) could be our #2 asset if guards pass!

**Objective**: Complete guards validation for 8 assets that passed optimization but didn't get guards executed

**Assets**: TIA, HBAR, CAKE, TON, RUNE, EGLD, CRV, SUSHI

**Command**:
```bash
python scripts/run_guards_multiasset.py \
  --assets TIA HBAR CAKE TON RUNE EGLD CRV SUSHI \
  --workers 1 \
  --output-prefix phase2_guards_backfill_20260124
```

**Expected Duration**: 2-3 hours (8 assets × ~20 min guards execution)  
**Output Files**: `outputs/phase2_guards_backfill_20260124_<asset>_guards_summary.csv` (one per asset)

**Success Criteria**:
- [ ] All 8 assets complete guards execution
- [ ] At least 3-5 assets pass 7/7 guards (50-60% pass rate)
- [ ] TIA passes guards (would become #2 PROD asset)
- [ ] Results documented in this file

**Expected Outcomes**:
| Asset | OOS Sharpe | WFE | Expected Result |
|-------|-----------|-----|-----------------|
| TIA | 5.16 | 1.36 | ✅ **LIKELY PASS** (excellent metrics) |
| HBAR | 2.32 | 1.03 | ✅ LIKELY PASS |
| CAKE | 2.46 | 0.81 | ⚠️ MARGINAL (WFE close to threshold) |
| TON | 2.54 | 1.17 | ✅ LIKELY PASS |
| RUNE | 2.42 | 0.61 | ⚠️ MARGINAL (low WFE) |
| EGLD | 2.04 | 0.66 | ⚠️ MARGINAL |
| CRV | 1.01 | 0.88 | ❌ **LIKELY FAIL** (Sharpe too low) |
| SUSHI | 1.90 | 0.63 | ⚠️ MARGINAL |

**NOTE**: Original Task C1 (Tier 1 baseline) is **OBSOLETE** - we already have 7 validated assets!

---

### Task C2: Phase 1 Screening [⏸️ LOWER PRIORITY]
**Priority**: 🟡 MEDIUM  
**Status**: On hold (not urgent, we already have 7-15 candidates)

**Objective**: Fast parallel screening of candidate pool

**Assets**: ATOM, ARB, LINK, INJ, TIA, HBAR, ICP, IMX, CELO, ARKM, W, STRK, AEVO  
(~13 assets in candidate pool)

**Command** (when C1 complete):
```bash
python scripts/run_full_pipeline.py \
  --assets ATOM ARB LINK INJ TIA HBAR ICP IMX CELO ARKM W STRK AEVO \
  --workers 10 \
  --trials-atr 150 \
  --trials-ichi 150 \
  --phase screening \
  --enforce-tp-progression \
  --skip-download
```

**Expected Duration**: 30-45 minutes (parallel with workers=10)  
**Output**: `outputs/SCREENING_multiasset_scan_<timestamp>.csv`

**Success Criteria**:
- [ ] At least 5-10 candidates show OOS Sharpe > 1.5
- [ ] Identify top 20-30% for Phase 2 validation
- [ ] No reproducibility issues detected
- [ ] Constant_liar strategy works correctly in parallel

**Unblock Trigger**: Decision made on frozen PROD strategy (after Task C1)

---

## 📊 VALIDATION STATUS - OVERNIGHT RUN RESULTS

### ✅ VALIDATED ASSETS (7 assets with 7/7 Guards PASS)
**Status**: 🟢 **PROD READY**

| Rank | Asset | OOS Sharpe | WFE | OOS Trades | Guards | Decision |
|:----:|:------|:-----------|:----|:-----------|:-------|:---------|
| 🥇 | **SHIB** | **5.67** | **2.27** | 93 | ✅ 7/7 | **PROD CONFIRMED** |
| 🥈 | **DOT** | **4.82** | **1.74** | 87 | ✅ 7/7 | **PROD CONFIRMED** |
| 🥉 | **NEAR** | **4.26** | **1.69** | 87 | ✅ 7/7 | **PROD CONFIRMED** |
| 4️⃣ | **DOGE** | **3.88** | **1.55** | 99 | ✅ 7/7 | **PROD CONFIRMED** |
| 5️⃣ | **ANKR** | **3.48** | **0.86** | 87 | ✅ 7/7 | **PROD CONFIRMED** |
| 6️⃣ | **JOE** | **3.16** | **0.73** | 78 | ✅ 7/7 | **PROD CONFIRMED** |
| 7️⃣ | **ETH** | **2.07** | **1.06** | 72 | ✅ 7/7 | **PROD CONFIRMED** |

**Notes**:
- All 7 assets exceed minimum thresholds (Sharpe > 1.0, WFE > 0.6, Trades > 60)
- All guards PASS with excellent margins
- Reproducibility confirmed (< 0.0001% variance across multiple runs)
- **These 7 assets form our NEW PROD BASELINE**

---

### ⏳ PENDING GUARDS VALIDATION (8 assets)
**Status**: 🟡 **AWAITING GUARDS EXECUTION (Task C1)**

| Rank | Asset | OOS Sharpe | WFE | OOS Trades | Guards | Expected |
|:----:|:------|:-----------|:----|:-----------|:-------|:---------|
| 🚀 | **TIA** | **5.16** | **1.36** | 75 | ⚠️ PENDING | **LIKELY PASS** (would be #2) |
| ⭐ | **TON** | **2.54** | **1.17** | 69 | ⚠️ PENDING | **LIKELY PASS** |
| ⭐ | **CAKE** | **2.46** | **0.81** | 90 | ⚠️ PENDING | **MARGINAL** (WFE close) |
| ⭐ | **RUNE** | **2.42** | **0.61** | 102 | ⚠️ PENDING | **MARGINAL** (low WFE) |
| ⭐ | **HBAR** | **2.32** | **1.03** | 114 | ⚠️ PENDING | **LIKELY PASS** |
| ⭐ | **EGLD** | **2.04** | **0.66** | 90 | ⚠️ PENDING | **MARGINAL** |
| ⚠️ | **SUSHI** | **1.90** | **0.63** | 105 | ⚠️ PENDING | **MARGINAL** |
| ⚠️ | **CRV** | **1.01** | **0.88** | 111 | ⚠️ PENDING | **LIKELY FAIL** (Sharpe low) |

**Action**: Execute guards (Task C1) to determine final count

---

### 📋 OLD FROZEN PROD ASSETS (Not yet re-validated)
**Status**: ⏸️ **LOWER PRIORITY** (we already have 7 confirmed)

| Asset | Old Result | Overlap with New? | Re-Validation Status |
|-------|-----------|-------------------|---------------------|
| BTC | 2.14 Sharpe | NO | ⏳ Not yet tested |
| ETH | 2.09 Sharpe | ✅ **YES (confirmed)** | ✅ DONE (2.07 Sharpe) |
| JOE | 5.03 Sharpe | ✅ **YES (confirmed)** | ✅ DONE (3.16 Sharpe) |
| OSMO | 3.18 Sharpe | NO | ⏳ Not yet tested |
| MINA | 1.76 Sharpe | NO | ⏳ Not yet tested |
| AVAX | ? Sharpe | NO | ⏳ Not yet tested |
| AR | ? Sharpe | NO | ⏳ Not yet tested |
| ANKR | ? Sharpe | ✅ **YES (confirmed)** | ✅ DONE (3.48 Sharpe) |
| DOGE | ? Sharpe | ✅ **YES (confirmed)** | ✅ DONE (3.88 Sharpe) |
| OP | ? Sharpe | NO | ⏳ Not yet tested |
| DOT | ? Sharpe | ✅ **YES (confirmed)** | ✅ DONE (4.82 Sharpe) |
| NEAR | ? Sharpe | ✅ **YES (confirmed)** | ✅ DONE (4.26 Sharpe) |
| SHIB | ? Sharpe | ✅ **YES (confirmed)** | ✅ DONE (5.67 Sharpe) |
| METIS | ? Sharpe | NO | ⏳ Not yet tested |
| YGG | ? Sharpe | NO | ⏳ Not yet tested |

**Summary**: 7/15 frozen PROD assets re-validated (all PASS). Remaining 8 can be tested later if needed.

---

## 📋 COMPLETED TASKS

### [2026-01-24 03:23-16:47 UTC] - Overnight Validation Run (Jordan) - COMPLETE ✅
**Task**: Phase 2 validation of 15 assets from Phase 1 screening  
**Duration**: 13h24  
**Status**: **MAJOR SUCCESS**

**Results Summary**:
- **15 assets validated** (optimization complete)
- **7 assets with 7/7 guards PASS** (ETH, JOE, ANKR, DOGE, DOT, NEAR, SHIB)
- **8 assets pending guards** (TIA, HBAR, CAKE, TON, RUNE, EGLD, CRV, SUSHI)
- **Reproducibility confirmed** (< 0.0001% variance)

**Key Findings**:
1. SHIB is top performer (5.67 Sharpe, 2.27 WFE)
2. TIA (pending guards) could be #2 if guards pass (5.16 Sharpe)
3. All 7 validated assets show excellent guard profiles
4. Original frozen PROD assets partially confirmed (7/15 re-validated)

**Outputs**:
- 60 CSV scan files (15 assets × 4 runs due to pipeline loops)
- 14 guards summary files (7 assets × Run1+Run2)
- Main log: `outputs/overnight_log_20260124_032322.txt`

**Decision**: ✅ **ACCEPT 7 VALIDATED ASSETS AS NEW PROD BASELINE**

**Next Step**: Execute guards on 8 pending assets (Task C1)

---

## 🔄 HANDOFFS

### To Alex: Task A2 Now Unblocked ✅
**What's Ready**:
- 7 validated assets available for portfolio construction
- All assets have complete metrics (Sharpe, WFE, trades, guards)
- Can test all 4 portfolio optimization methods

**Assets Available**:
```
SHIB DOT NEAR DOGE ANKR JOE ETH
```

**Command for Alex**:
```bash
python scripts/portfolio_construction.py \
  --assets SHIB DOT NEAR DOGE ANKR JOE ETH \
  --method max_sharpe risk_parity min_cvar equal \
  --min-weight 0.05 \
  --max-weight 0.25 \
  --max-correlation 0.70
```

**Expected Duration**: 10 minutes  
**Can Run**: In parallel while Casey executes guards on 8 pending assets

---

### From Jordan: Overnight Run Complete ✅
**What Was Delivered**:
- 7 assets with 7/7 guards PASS
- 8 assets with optimization complete (guards pending)
- Reproducibility confirmed across multiple runs
- 60+ output files in `outputs/phase2_validation_*`

**Impact**: Original Task C1 (Tier 1 baseline) is obsolete - we already exceeded targets!

---

### From User: PROD Strategy Decision (Optional)
**Context**: After C1 completes, need decision on frozen PROD assets

**Question**: If 2-3 Tier 1 assets pass (marginal outcome):
- A) Trust old validations, keep all 15 frozen
- B) Re-validate suspicious assets only
- C) Full re-validation of all 15

**Recommendation**: Will provide after C1 results

---

## 📋 COMMUNICATION PROTOCOL

### When Task Completes (Template)
```markdown
## [TIMESTAMP UTC] - [Task Name] - COMPLETE ✅

**Task**: [Task ID and description]
**Assets**: [List]
**Duration**: [Actual time]
**Status**: [SUCCESS/PARTIAL/FAILED]

**Results Summary**:
| Asset | OOS Sharpe | WFE | Guards | PSR | Decision |
|-------|-----------|-----|--------|-----|----------|
| [Asset] | X.XX | X.XX | X/7 | 0.XX | [PASS/FAIL/MARGINAL] |

**Decision**: [What strategy to pursue next]

**Outputs**:
- [File paths]

**Handoff to Alex**:
- [What's ready for Alex]
- [Any tasks unblocked]

**Next Step**: [What Casey does next]
```

### When Blocked (Template)
```markdown
## [TIMESTAMP UTC] - BLOCKED ⏸️

**Task**: [Task ID]
**Blocker**: [Waiting for Alex / User decision / etc.]
**Impact**: [Cannot proceed with X until...]

**Estimated Unblock**: [Time/condition]
**Alternative Work**: [Can review Y / prepare Z / etc.]
```

### When Decision Needed (Template)
```markdown
## [TIMESTAMP UTC] - DECISION NEEDED ⁉️

**Context**: [Current situation]
**Question**: [Specific decision to make]

**Options**:
A. [Option A] - [Pros/cons]
B. [Option B] - [Pros/cons]
C. [Option C] - [Pros/cons]

**Recommendation**: Option [X] because [reason]

**Impact**: [How this affects timeline/strategy]

**Urgency**: [Can wait / Need before next task / ASAP]
```

---

## 🔧 COORDINATION RULES

### Before Starting Any Validation Run
1. ✅ Read `comms/alex-dev.md` - Is Alex running integration tests?
2. ✅ Check `status/project-state.md` - Any new blockers?
3. ✅ Verify compute resources available (not overlapping with Alex)
4. ✅ Update this file: "Task X - STARTED"
5. ✅ Create output file with proper prefix (REVALIDATION_, SCREENING_, etc.)

### During Validation Run
1. 🔄 Monitor progress (check log files every 30 min)
2. 📊 Update tracking dashboard if milestones hit
3. 🐛 If errors occur, document and notify Alex if code issue
4. ⏱️ If running long, estimate remaining time

### After Validation Completes
1. ✅ Analyze results (compare to thresholds)
2. 📝 Update this file with results table
3. 🎯 Make decision based on decision matrix
4. 📊 Update `status/project-state.md` with new validated assets
5. 🗂️ Organize outputs and create manifest if needed

### File Naming Convention
```
# Casey's validation outputs
outputs/REVALIDATION_<asset>_guards_<timestamp>.csv
outputs/SCREENING_multiasset_scan_<timestamp>.csv
outputs/PHASE2_<asset>_guards_<timestamp>.csv

# Casey's analysis outputs
outputs/BASELINE_ANALYSIS_<timestamp>.txt
outputs/DECISION_REPORT_<timestamp>.md
```

---

## 🎯 DECISION FRAMEWORKS

### Framework 1: PROD Asset Strategy (After C1)
```
IF (3-4 assets PASS):
  Decision: KEEP FROZEN PROD (trust old validations)
  Action: Proceed to Phase 1 Screening
  Confidence: HIGH
  
ELSE IF (2 assets PASS):
  Decision: HYBRID (validate Tier 2 selectively)
  Action: Test AR, ANKR, OP, DOT (4 more assets)
  Confidence: MEDIUM
  
ELSE IF (0-1 assets PASS):
  Decision: REBUILD (full re-validation)
  Action: Re-validate all 15 frozen PROD assets
  Confidence: LOW (old system was unreliable)
```

### Framework 2: Phase 1 Candidate Selection
```
IF (OOS Sharpe > 2.0 AND WFE > 0.8):
  Priority: TIER A (high confidence)
  Phase 2: Immediate validation
  
ELSE IF (OOS Sharpe > 1.5 AND WFE > 0.6):
  Priority: TIER B (medium confidence)
  Phase 2: After Tier A validated
  
ELSE IF (OOS Sharpe > 1.0 AND WFE > 0.4):
  Priority: TIER C (marginal)
  Phase 2: Only if need more assets
  
ELSE:
  Priority: EXCLUDED
  Phase 2: Skip
```

### Framework 3: Overfitting Assessment
```
IF (PSR > 0.90 AND DSR > 0.80):
  Confidence: EXCELLENT (low overfit risk)
  
ELSE IF (PSR > 0.85 AND DSR > 0.70):
  Confidence: GOOD (acceptable overfit risk)
  
ELSE IF (PSR > 0.75 AND DSR > 0.60):
  Confidence: MARGINAL (monitor closely)
  
ELSE:
  Confidence: POOR (high overfit risk)
  Recommendation: REJECT or try conservative filters
```

---

## ⚠️ ESCALATION TRIGGERS

### When to Notify Alex (Development Issues)
- 🐛 Script crashes or hangs
- 🔢 Metrics calculations return NaN/inf
- 📁 Output files missing or corrupted
- ⚡ Performance degradation (>2x expected time)
- 🔁 Reproducibility issues (different results on re-run)

### When to Notify User (Strategic Decisions)
- ⁉️ Baseline validation shows unexpected results (e.g., 0-1/4 PASS)
- 🎯 Major strategy pivot needed (rebuild PROD from scratch)
- ⏱️ Timeline at risk (blockers >4 hours)
- 📊 Trade-offs require user input (quality vs speed)
- 🚨 Critical assumption violated (e.g., frozen PROD all fail)

---

## 📚 QUICK REFERENCE

### Important Files
- **This file**: `comms/casey-quant.md`
- **Alex's status**: `comms/alex-dev.md`
- **Coordination**: `comms/TESTING_COORDINATION.md`
- **Project state**: `status/project-state.md`
- **Quick memo**: `memo.md`

### Common Commands
```bash
# Tier 1 baseline validation (C1)
python scripts/run_full_pipeline.py --assets JOE OSMO MINA AVAX --workers 1 --run-guards --overfit-trials 150

# Phase 1 screening (C2)
python scripts/run_full_pipeline.py --assets <POOL> --workers 10 --phase screening

# Check recent outputs
ls -lt outputs/REVALIDATION_* | head -10

# Analyze results quickly
python scripts/analyze_scan_results.py outputs/REVALIDATION_*_guards_*.csv

# Monitor running job
tail -f outputs/overnight_log_<timestamp>.txt
```

### Key Thresholds
- **Guards**: 7/7 PASS required (no exceptions)
- **OOS Sharpe**: >1.0 minimum, >2.0 target
- **WFE**: >0.6 required, >0.8 preferred
- **PSR**: >0.85 informational (not enforced)
- **DSR**: >0.70 informational (not enforced)
- **Trades OOS**: >60 minimum

---

## 🎯 SESSION GOALS

### Today (24 JAN)
- [ ] Wait for Alex to complete Task A1 (ETH integration test)
- [ ] Start Task C1 when unblocked (Tier 1 baseline)
- [ ] Complete 4-asset validation (JOE, OSMO, MINA, AVAX)
- [ ] Make decision on frozen PROD strategy
- [ ] (If time) Prepare Phase 1 screening command

### This Week
- [ ] Complete Tier 1 baseline validation
- [ ] Execute Phase 1 screening on candidate pool
- [ ] Identify 10-15 top candidates for Phase 2
- [ ] Begin Phase 2 validation on top tier
- [ ] Handoff 5+ validated assets to Alex for portfolio construction

---

## 🔄 CURRENT STATUS

**Active Task**: None (waiting for Alex A1)  
**Blocked By**: Alex Task A1 (ETH integration test)  
**Estimated Unblock**: ~45 minutes from now  
**Ready to Start**: Task C1 (all dependencies met except Alex handoff)  
**Compute Available**: Yes (can use workers=1 for sequential validation)

---

**NEXT UPDATE**: When Alex completes Task A1 and hands off ETH results  
**THEN START**: Task C1 (Tier 1 baseline validation)
