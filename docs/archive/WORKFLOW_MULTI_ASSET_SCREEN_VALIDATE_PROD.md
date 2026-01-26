# ⚠️ ARCHIVED — DO NOT USE

**This file is obsolete since 26 Jan 2026.**

Replaced by:
- `.cursor/rules/MASTER_PLAN.mdc` → Parameters, guards, rules
- `docs/WORKFLOW_PIPELINE.md` → Commands per phase
- `status/project-state.md` → Current state

---

*Original content preserved below for historical reference only.*

---

# Pipeline Multi-Asset — 6 Phases (Screen → Validate → Prod)

**Derniere mise a jour:** 2026-01-25 15:45 UTC  
**Status**: 🟢 RESET COMPLETE — 14 Assets PROD  
**Version**: v2.2 (filter system v2, deterministic validation)

**⚠️ BREAKING CHANGE**: Parallel screening (workers > 1) is non-deterministic by Optuna design. Phase 2 MUST use workers=1 for scientific validity.

[... truncated for archive ...]
