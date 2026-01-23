## 🔴 CRITICAL UPDATE - 24 janvier 2026 (UPDATED)

**BREAKING CHANGES**: Optuna parallel optimization is non-deterministic.
All Phase 1 screening results before today are unreliable.

**NEW WORKFLOW**: Option B (Screening parallel + Validation sequential)

### ✅ OPTUNA FIX COMPLETE
Applied full TPESampler configuration:
- ✅ `create_sampler()` helper function
- ✅ Unique seed per asset (avoid collisions)
- ✅ `multivariate=True` (capture tp1<tp2<tp3 correlations)
- ✅ `constant_liar=True` (safe parallel with workers>1)
- ✅ All RNG sources synchronized with unique seed

### Documents to Read
1. **EVERYONE**: `BREAKING_CHANGES_24JAN.md` — What changed and why
2. **TECHNICAL**: `OPTUNA_CONFIGURATION_FIX.md` — Optuna fix details
3. **JORDAN**: `comms/PHASE1_PHASE2_INSTRUCTIONS.md` (Phase 1 Screening)
4. **SAM**: `comms/PHASE1_PHASE2_INSTRUCTIONS.md` (Phase 2 Validation)
5. **CASEY**: `REPRODUCIBILITY_STRATEGY.md` (Scientific foundation)

### Current Tasks
- **JORDAN**: Phase 1 Screening (30 min) — Use `--phase screening --workers-screening 10`
- **SAM**: Phase 2 Validation (2-3h) — Use `--phase validation --workers-validation 1` (Run 2x)
- **CASEY**: Monitor & manage Phase 3 (Rescue/Optimization)

### Key Points
- ✅ Reproducibility fixes COMPLETE + Optuna optimization params
- ✅ New scripts created (export_screening_results.py, verify_reproducibility.py)
- ✅ Complete documentation ready
- ✅ Go/No-Go: **GO FOR PHASE 1**

### Timeline
- Today: Phase 1 Screening (Jordan) → export candidates
- Tomorrow: Phase 2 Validation Run 1 (Sam) + Run 2 + reproducibility check
- Friday: Phase 3 (Casey) based on Phase 2 results

---

**For implementation details**: See OPTUNA_CONFIGURATION_FIX.md
**For status tracking**: See IMPLEMENTATION_CHECKLIST.md