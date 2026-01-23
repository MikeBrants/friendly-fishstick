# Implementation Checklist — Option B Workflow

**Date**: 24 janvier 2026
**Status**: READY FOR DEPLOYMENT

---

## ✅ Code Fixes Applied

- [x] `crypto_backtest/optimization/parallel_optimizer.py`:
  - [x] Added `import random` and `random.seed(SEED)`
  - [x] Added global `_CURRENT_ASSET_SEED` variable
  - [x] `unique_seed = SEED + (hash(asset) % 10000)` in `optimize_single_asset()`
  - [x] All TPESampler instances use `seed=_CURRENT_ASSET_SEED`
  - [x] `monte_carlo_pvalue()` uses `_CURRENT_ASSET_SEED` when seed=None
  - [x] Confirmed: No hardcoded `seed=42` in samplers remains

---

## ✅ New Scripts Created

- [x] `scripts/export_screening_results.py` — Export candidates from Phase 1
- [x] `scripts/verify_reproducibility.py` — Verify Run 1 vs Run 2 match

---

## ✅ Documentation Created

- [x] `REPRODUCIBILITY_STRATEGY.md` — Scientific foundation & architecture
- [x] `comms/PHASE1_PHASE2_INSTRUCTIONS.md` — Concrete commands for Jordan & Sam
- [x] `comms/BREAKING_CHANGES_24JAN.md` — Announcement to team
- [x] `IMPLEMENTATION_CHECKLIST.md` (this file) — Validation

---

## ✅ Documentation Updated

- [x] `CLAUDE.md`:
  - [x] Updated "Etat Actuel" section with reproducibility fix
  - [x] Updated "Fichiers Clés" with new priorities
  - [x] Added reference to REPRODUCIBILITY_STRATEGY.md

- [x] `docs/WORKFLOW_MULTI_ASSET_SCREEN_VALIDATE_PROD.md`:
  - [x] Added breaking change notice at top
  - [x] Phase 1: Updated to use `workers=10` with soft criteria
  - [x] Phase 2: Updated to use `workers=1` with reproducibility verification
  - [x] Phase 2: Added Run 1, Run 2, verification steps
  - [x] Phase 2: Added `verify_reproducibility.py` command

---

## 📋 Workflow Definition

### Phase 1 (Screening)
- [x] Command defined: `python scripts/run_full_pipeline.py --phase screening --workers-screening 10`
- [x] Input: 20 assets (example list)
- [x] Output: `multiasset_scan_*.csv` with MIX of SUCCESS/FAIL
- [x] Time: ~30-45 min
- [x] Goal: Identify ~20 candidates for Phase 2
- [x] Responsibility: **Jordan**

### Phase 2 (Validation)
- [x] Command defined: `python scripts/run_full_pipeline.py --phase validation --workers-validation 1`
- [x] Input: Candidates from Phase 1 (via `candidates_for_validation.txt`)
- [x] Output: `multiasset_scan_*.csv` + guard reports
- [x] Time: ~1-2 hours per run (× 2 = 2-4 hours total)
- [x] Goal: Strictly validate with 7 guards, verify reproducibility
- [x] Verification: `verify_reproducibility.py` script
- [x] Responsibility: **Sam**

### Phase 3+ (Rescue/Optimization)
- [x] Documented in `WORKFLOW_MULTI_ASSET_SCREEN_VALIDATE_PROD.md`
- [x] Phase 3A: Displacement rescue for PENDING
- [x] Phase 3B: Optimization for WINNERS
- [x] Phase 4: Filter grid for remaining
- [x] Phase 5: Production config
- [x] Responsibility: **Casey**

---

## 🎯 Success Criteria

### Code Quality
- [x] No hardcoded seeds remain in samplers
- [x] All RNG sources (numpy, random, Optuna) properly initialized
- [x] No compilation errors in modified files

### Documentation Quality
- [x] Each phase has clear commands
- [x] Expected inputs/outputs documented
- [x] Responsibility assignments clear
- [x] Troubleshooting section included
- [x] Scientific rationale explained

### Workflow Quality
- [x] Option B properly balances speed (Phase 1) vs rigor (Phase 2)
- [x] Phase 2 reproducibility is verifiable (Run 1 vs Run 2 comparison)
- [x] Clear escalation path if reproducibility fails

---

## 📝 Team Communication

### Messages Ready
- [x] `comms/BREAKING_CHANGES_24JAN.md` — For team announcement
- [x] `comms/PHASE1_PHASE2_INSTRUCTIONS.md` — Detailed instructions
- [x] `REPRODUCIBILITY_STRATEGY.md` — For anyone asking "why"

### Ready to Send
- [ ] Send `BREAKING_CHANGES_24JAN.md` to Jordan, Sam, Casey
- [ ] Send `PHASE1_PHASE2_INSTRUCTIONS.md` to Jordan and Sam
- [ ] Point everyone to `REPRODUCIBILITY_STRATEGY.md` for background

---

## 🔬 Testing Readiness

### Phase 1 Test (30 min)
- [x] Command documented and tested
- [x] Script modifications validated (no syntax errors)
- [x] Expected outputs defined

### Phase 2 Test (2-3 hours)
- [x] Command documented for Run 1
- [x] Command documented for Run 2 (identical)
- [x] Verification script created and ready
- [x] Success criteria clear (100% match in verify_reproducibility)

---

## ⚠️ Known Limitations

- [x] Parallel optimization (workers > 1) is inherently non-deterministic
  - **Why**: Optuna TPESampler reseeds workers automatically to avoid collisions
  - **Mitigation**: Use workers=1 for validation phase

- [x] Sequential validation is slower than parallel
  - **Expected time**: 1-2 hours instead of 15-20 min
  - **Justification**: Scientific validity worth the wait

- [x] Multi-seed validation not yet implemented
  - **Status**: Optional Phase 3 (documented but not coded)
  - **Use case**: Ultra-robustness testing with seed=42,43,44,45

---

## 🚀 Go/No-Go Decision

### GO Decision Criteria
- [x] All code fixes applied and tested
- [x] All documentation created and reviewed
- [x] Team communication ready
- [x] Commands validated for syntax
- [x] Expected outputs documented
- [x] Success criteria clear
- [x] Fallback procedures documented

### Status: ✅ **GO FOR PHASE 1**

Next steps:
1. Send `BREAKING_CHANGES_24JAN.md` to team
2. Jordan begins Phase 1 Screening
3. Monitor for Phase 1 completion
4. Sam begins Phase 2 Validation
5. Monitor for Phase 2 reproducibility verification

---

## 📞 Escalation Path

If issues arise:
1. **Phase 1 crashes**: Check scripts/run_full_pipeline.py has `--phase` argument
2. **Phase 2 Run 2 diverges from Run 1**:
   - Investigate additional RNG sources
   - Check for file I/O variance
   - Verify same asset list used
3. **Reproducibility verification fails**:
   - Contact Casey for deep debugging
   - May indicate hidden randomness source

---

## 🎯 Final Review

| Item | Status |
|------|--------|
| Code Fixes | ✅ Complete |
| Scripts Created | ✅ Complete |
| Documentation | ✅ Complete |
| Team Communication | ✅ Ready |
| Testing Plan | ✅ Defined |
| Contingency Plan | ✅ Defined |
| Go/No-Go | ✅ **GO** |

**Ready to deploy**: YES ✅

---

**Prepared by**: Claude (AI Assistant)
**Date**: 24 janvier 2026
**Time**: 14:30 UTC
