# CASEY - Orchestrateur & Coordinateur

**Role**: Strategy, Prioritization, Coordination (ne code pas, ne lance pas de commandes)  
**Current Phase**: POST-OVERNIGHT VALIDATION - Coordination guards 8 pending  
**Last Updated**: 24 janvier 2026, 19:30 UTC

---

## 🎯 CURRENT DECISIONS NEEDED

### Decision D1: Execute Guards on 7 Pending Assets 🔴 URGENT
**Priority**: 🔴 CRITICAL  
**Context**: Jordan a complété l'overnight run avec **8 assets validés** (SHIB, DOT, NEAR, DOGE, ANKR, JOE, ETH, ONE) + **7 assets pending guards** (TIA, HBAR, CAKE, TON, RUNE, EGLD, SUSHI)

**Decision Matrix**:
| Asset | OOS Sharpe | WFE | Expected Guards | Priority |
|:------|:-----------|:----|:----------------|:---------|
| **TIA** 🚀 | **5.16** | **1.36** | **LIKELY PASS** | **P0** (could be #2!) |
| **HBAR** | 2.32 | 1.03 | LIKELY PASS | P0 |
| **TON** | 2.54 | 1.17 | LIKELY PASS | P0 |
| **CAKE** | 2.46 | 0.81 | MARGINAL | P1 |
| **RUNE** | 2.42 | 0.61 | MARGINAL | P1 |
| **EGLD** | 2.04 | 0.66 | MARGINAL | P1 |
| **SUSHI** | 1.90 | 0.63 | MARGINAL | P2 |

**Note**: CRV exclu (OOS Sharpe 1.01 < seuil minimum 1.0)

**Decision**: ✅ **PROCEED - Execute guards on 7 assets** (CRV removed)

**Rationale**:
- TIA (5.16 Sharpe) pourrait devenir notre #2 asset si guards passent
- 3-5 assets devraient passer guards (estimation conservatrice)
- Total PROD projection: 11-13 assets (excellent diversification)

**Task Assignment**: @Jordan → Execute guards pipeline (commande dans section ci-dessous)  
**Validation Assignment**: @Sam → Validate guards results when complete

---

### Decision D2: PROD Portfolio Strategy ✅ RESOLVED
**Question**: Garder 8 assets validés ou attendre les 7 pending?

**Decision**: ✅ **ACCEPT 8 VALIDATED ASSETS AS NEW PROD BASELINE**

**Rationale**:
- 8 assets avec 7/7 guards PASS (7 overnight + ONE backfill)
- Mean Sharpe 3.75 (excellent)
- Tous WFE > 0.6, Trades > 60
- Reproducibilité < 0.0001% confirmée
- Sufficient pour portfolio construction test

**Action**: 
- Immediate: Use 8 assets for portfolio construction (@Jordan)
- Parallel: Execute guards on 7 pending (@Jordan)
- After guards: Final decision on 8 vs 11-13 vs 15 assets

---

### Decision D3: Old Frozen PROD Assets ✅ RESOLVED
**Question**: Re-valider les 8 frozen PROD restants (BTC, OSMO, MINA, AVAX, AR, OP, METIS, YGG)?

**Decision**: ⏸️ **LOWER PRIORITY** - Focus on completing 8 pending guards first

**Rationale**:
- 8/15 frozen PROD déjà re-validés (100% success rate)
- 7 pending guards plus prometteurs (TIA = 5.16 Sharpe!)
- Pas urgent de re-valider remaining 7 frozen

**Action**: Defer validation of remaining 8 frozen assets until after guards complete

---

## 📊 VALIDATED ASSETS STATUS (7 PROD READY)

| Rank | Asset | OOS Sharpe | WFE | OOS Trades | Guards | Status |
|:----:|:------|:-----------|:----|:-----------|:-------|:-------|
| 🥇 | **SHIB** | **5.67** | **2.27** | 93 | ✅ 7/7 | **PROD** |
| 🥈 | **DOT** | **4.82** | **1.74** | 87 | ✅ 7/7 | **PROD** |
| 🥉 | **NEAR** | **4.26** | **1.69** | 87 | ✅ 7/7 | **PROD** |
| 4️⃣ | **DOGE** | **3.88** | **1.55** | 99 | ✅ 7/7 | **PROD** |
| 5️⃣ | **ANKR** | **3.48** | **0.86** | 87 | ✅ 7/7 | **PROD** |
| 6️⃣ | **JOE** | **3.16** | **0.73** | 78 | ✅ 7/7 | **PROD** |
| 7️⃣ | **ETH** | **2.07** | **1.06** | 72 | ✅ 7/7 | **PROD** |

**Portfolio Metrics**: Mean Sharpe 3.91, All WFE > 0.6, Reproducibility < 0.0001%

---

## 📋 TASK ASSIGNMENTS

### Task J1: Execute Guards on 7 Pending [ASSIGNED to @Jordan]
**Priority**: 🔴 P0 (CRITICAL)  
**Status**: ⏳ WAITING FOR JORDAN TO EXECUTE

**Command for @Jordan**:
```bash
python scripts/run_guards_multiasset.py \
  --assets TIA HBAR CAKE TON RUNE EGLD SUSHI \
  --workers 1 \
  --mc-iterations 1000 \
  --bootstrap-samples 10000 \
  --sensitivity-range 5 \
  --output-prefix phase2_guards_backfill_20260124
```

**Expected Duration**: 2-3 hours (7 assets × ~20 min guards)  
**Output**: `outputs/phase2_guards_backfill_20260124_<asset>_guards_summary.csv`

**Success Criteria**:
- [ ] All 7 assets complete guards execution
- [ ] No errors or timeouts
- [ ] Output files generated for all 7 assets
- [ ] Jordan notifies Sam when complete

**Note**: CRV exclu (OOS Sharpe 1.01 < threshold 1.0, prediction: FAIL guards)

**Handoff**: When complete, @Jordan hands off to @Sam for validation

---

### Task J2: Portfolio Construction Test [ASSIGNED to @Jordan]
**Priority**: 🟡 P1 (MEDIUM)  
**Status**: ⏳ CAN RUN IN PARALLEL with Task J1

**Command for @Jordan**:
```bash
python scripts/portfolio_construction.py \
  --assets SHIB DOT NEAR DOGE ANKR JOE ETH \
  --method max_sharpe risk_parity min_cvar equal \
  --min-weight 0.05 \
  --max-weight 0.25 \
  --max-correlation 0.70
```

**Expected Duration**: 10 minutes  
**Output**: Portfolio allocation CSVs + correlation matrix

**Success Criteria**:
- [ ] All 4 methods execute successfully
- [ ] Weights sum to 1.0 for each method
- [ ] Weights respect min/max bounds
- [ ] Output files generated

**Handoff**: When complete, @Jordan reports results to @Casey

---

### Task S1: Validate Guards Results [ASSIGNED to @Sam]
**Priority**: 🔴 P0 (CRITICAL)  
**Status**: ⏸️ BLOCKED (waiting for Task J1 completion)

**Scope**: Validate 7 guards for 7 pending assets

**Assets to Validate**: TIA, HBAR, CAKE, TON, RUNE, EGLD, SUSHI

**Checklist per Asset**:
- [ ] guard001: MC p-value < 0.05
- [ ] guard002: Sensitivity < 10%
- [ ] guard003: Bootstrap CI > 1.0
- [ ] guard005: Top10 trades < 40%
- [ ] guard006: Stress1 Sharpe > 1.0
- [ ] guard007: Regime mismatch < 1%
- [ ] WFE > 0.6
- [ ] OOS Sharpe > 1.0
- [ ] OOS Trades > 60

**Expected Outcome**: 3-5 assets pass 7/7 guards (conservative estimate) → 11-13 total PROD

**Handoff**: When complete, @Sam reports verdict to @Casey for final decision

---

## 🔄 WORKFLOW STATUS

### Phase 1: Overnight Validation ✅ COMPLETE
**Executor**: @Jordan  
**Duration**: 13h24 (03:23-16:47 UTC)  
**Result**: 8 assets 7/7 guards PASS (7 overnight + ONE backfill) + 7 assets pending guards

### Phase 2: Guards on 7 Pending ⏳ IN PROGRESS
**Coordinator**: @Casey (moi)  
**Executor**: @Jordan  
**Validator**: @Sam  
**Status**: Task J1 assigned to @Jordan (CRV excluded, 7 assets remaining)

**Workflow**:
1. @Casey → Decision to proceed (DONE)
2. @Jordan → Execute guards pipeline (IN PROGRESS)
3. @Sam → Validate results when complete (WAITING)
4. @Casey → Final decision on PROD list (WAITING)

### Phase 3: Portfolio Construction ⏳ IN PROGRESS
**Coordinator**: @Casey  
**Executor**: @Jordan  
**Status**: Task J2 can run in parallel

---

## 📊 STRATEGIC ANALYSIS

### Portfolio Size Projection

**Current State**: 8 confirmed PROD assets

**After Guards (Scenarios)**:
- **Conservative** (2-3 pass): 10-11 total PROD assets
- **Medium** (4-5 pass): 12-13 total PROD assets
- **Optimistic** (6-7 pass): 14-15 total PROD assets

**Original Target**: 20+ assets  
**Current Achievement**: 8 confirmed (40% of goal)  
**Projected Achievement**: 11-13 assets (55-65% of goal)  
**Status**: 🟢 **ON TRACK**

### Key Observations

**Observation 1: SHIB is Star Performer**
- Highest Sharpe (5.67)
- Highest WFE (2.27)
- Excellent guards profile
- **Recommendation**: Consider 15-20% weight in portfolio

**Observation 2: TIA High Priority**
- 5.16 Sharpe (would be #2 if guards pass)
- Excellent WFE (1.36)
- **Impact**: If TIA passes, significantly improves portfolio

**Observation 3: ONE Added to Portfolio**
- Validated via Phase 1 Batch 3 + Guards backfill (19:35 UTC)
- 3.00 Sharpe, 0.92 WFE, 7/7 guards PASS
- **Recommendation**: 8th asset expands diversification options

---

## 📋 PENDING DECISIONS (After Guards Complete)

### Decision D4: Final PROD Asset List
**Trigger**: After @Sam validates guards results

**Question**: Use 8, 11-13, or 15 assets for PROD portfolio?

**Decision Matrix**:
| Scenario | Assets Passing | Total PROD | Action |
|----------|---------------|-----------|---------|
| Conservative | 0-2 pass | 8-10 assets | Use 8 only (high quality) |
| Medium | 3-5 pass | 11-13 assets | Balanced portfolio |
| Optimistic | 6-7 pass | 14-15 assets | Aggressive diversification |

**Inputs Needed**:
- @Sam validation results (how many pass 7/7?)
- Portfolio construction results (@Jordan Task J2)
- Risk/return trade-off analysis

---

### Decision D5: Phase 1 Screening
**Trigger**: After Decision D4 resolved

**Question**: Proceed with Phase 1 screening of ~13 candidate assets?

**Candidates**: ATOM, ARB, LINK, INJ, ICP, IMX, CELO, ARKM, W, STRK, AEVO

**Decision Factors**:
- If we have 13-15 PROD assets → ⏸️ **SKIP** (sufficient diversification)
- If we have 7-9 PROD assets → ✅ **PROCEED** (need more assets)
- If we have 10-12 PROD assets → ⚠️ **OPTIONAL** (user preference)

**Command (if proceed)**:
```bash
python scripts/run_full_pipeline.py \
  --assets ATOM ARB LINK INJ ICP IMX CELO ARKM W STRK AEVO \
  --workers 10 \
  --trials-atr 150 \
  --trials-ichi 150 \
  --phase screening \
  --enforce-tp-progression \
  --skip-download
```

---

## 🎯 COORDINATION CHECKPOINTS

### Checkpoint 1: After Task J1 Complete (2-3h)
**Trigger**: @Jordan reports guards execution complete

**Actions**:
1. Acknowledge @Jordan completion
2. Assign @Sam to validate results (Task S1)
3. Estimate: How many assets likely to pass?

---

### Checkpoint 2: After Task S1 Complete (1-2h after Checkpoint 1)
**Trigger**: @Sam reports validation verdict

**Actions**:
1. Review @Sam validation results
2. Count assets with 7/7 guards PASS
3. Make Decision D4 (Final PROD list)
4. Update `status/project-state.md`

---

### Checkpoint 3: After Decision D4 (immediate)
**Trigger**: Final PROD list decided

**Actions**:
1. Make Decision D5 (Phase 1 screening)
2. If proceed, assign @Jordan to execute
3. If skip, plan next validation cycle

---

## 📁 KEY REFERENCES

**Source of Truth**: `status/project-state.md`  
**Overnight Analysis**: `comms/OVERNIGHT_RESULTS_ANALYSIS.md`  
**Jordan Tasks**: `comms/jordan-dev.md`  
**Sam Validation**: `comms/sam-qa.md`  
**Quick Reference**: `memo.md`

---

## 🔄 CURRENT STATUS

**Active Decisions**: 3 resolved, 2 pending (D4, D5)  
**Active Tasks**: 2 assigned (@Jordan J1, J2)  
**Waiting For**: @Jordan to execute Task J1 (guards)  
**Next Checkpoint**: After guards complete (2-3h)  
**Coordination Status**: 🟢 **CLEAR WORKFLOW ESTABLISHED**

---

**NEXT UPDATE**: After @Jordan reports Task J1 completion  
**THEN DECIDE**: Assign @Sam to validate results (Task S1)

**Last Decision**: 24 janvier 2026, 19:30 UTC  
**Coordinator**: @Casey
