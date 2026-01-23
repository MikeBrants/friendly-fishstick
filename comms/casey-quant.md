# Taches Quant - @Casey

Ce fichier contient les taches assignees par Casey aux autres agents.

---

## Format Message

```
## [HH:MM] [ACTION] @Casey -> @Agent
**Context:** ...
**Task:** ...
**Command:** ...
**Criteres succes:** ...
**Next:** @Agent fait X
```

### Actions possibles
- `[TASK]` — Nouvelle tache assignee
- `[DECISION]` — Verdict rendu (PROD/BLOCKED/RETEST)
- `[WAITING]` — En attente d'un autre agent
- `[CYCLE COMPLETE]` — Fin du cycle

---

## Historique

<!-- Les messages les plus recents en haut -->

## [23:35] [DECISION] @Casey -> HBAR

**Asset:** HBAR
**Run ref:** [23:06] @Jordan, [23:20] @Sam validation
**Mode teste:** medium_distance_volume (displacement 52)

**Resultats:**
- Scan: SUCCESS (Sharpe 1.28, WFE 0.63, Trades 107)
- Guards: 4/7 FAIL ❌
  - guard002: FAIL (sensitivity 11.49% > 10%)
  - guard003: FAIL (bootstrap CI 0.30 < 1.0)
  - guard005: FAIL (top10 41.05% > 40%)
  - guard006: FAIL (stress1 0.62 < 1.0)

**Verdict:** BLOCKED ❌

**Rationale:**
- Le mode `medium_distance_volume` n'a pas resolu les problemes critiques
- 3 guards critiques FAIL (guard002, guard003, guard006)
- Amelioration marginale vs baseline (sens 11.49% vs 13%) mais insuffisante

**Options de retest (si priorite future):**
1. Tester displacement d26 avec baseline (meme pattern que JOE)
2. Tester displacement d78 avec baseline (meme pattern que OSMO/MINA)
3. Tester mode `conservative` si overfit severe detecte

**Status:** HBAR bloque pour production. Variants disponibles si besoin futur.

---

## [23:35] [DECISION] @Casey -> AVAX

**Asset:** AVAX
**Run ref:** [23:27] @Jordan RUN_COMPLETE
**Mode teste:** medium_distance_volume (displacement 52)

**Resultats:**
- Scan: SUCCESS (Sharpe 3.52, WFE 0.94, Trades 96)
- Guards: 7/7 PASS ✅✅✅
  - guard001: PASS (MC p-value 0.00)
  - guard002: PASS (sensitivity 6.00% < 10%)
  - guard003: PASS (bootstrap CI 1.52 > 1.0)
  - guard005: PASS (top10 26.73% < 40%)
  - guard006: PASS (stress1 1.40 > 1.0)
  - guard007: PASS (regime mismatch 0.00%)
  - WFE: PASS (0.94 > 0.6)

**Verdict:** PRODUCTION ✅

**Rationale:**
- Tous les guards critiques passes
- WFE excellent (0.94 vs 0.52 baseline)
- Sharpe OOS excellent (3.52 > 2.0 target)
- Trades suffisants (96 > 60)

**Action:** AVAX ajoute en PROD dans `status/project-state.md` (deja fait par @Jordan)

---

## [23:35] [SUPERVISION] @Casey

**Cycle P0 - Etat actuel:**

**Completes:**
- ✅ AVAX: PRODUCTION (7/7 guards PASS, WFE 0.94)
- ❌ HBAR: BLOCKED (4/7 guards FAIL, variants disponibles)

**En cours:**
- 🔄 UNI: Test `moderate` en cours (run start [23:30] @Jordan)

**Prochaines actions:**
- Attendre validation UNI par @Sam
- Si UNI FAIL: Considerer autres variants (d78, conservative)

---

## [22:45] [TASK] @Casey -> @Jordan

**Context:** HBAR a passe le scan (Sharpe 1.28, WFE 0.63) mais guards FAIL (sensitivity 13% > 10%, stress1 0.72 < 1.0). On teste avec filter grid medium_distance_volume comme pour ETH.

**Asset:** HBAR
**Variant:** medium_distance_volume (comme ETH winner)
**Hypothese:** Le filter mode reduira la sensitivity variance sous 10%

**Command:**
```bash
python scripts/run_full_pipeline.py \
  --assets HBAR \
  --workers 6 \
  --trials-atr 150 \
  --trials-ichi 150 \
  --enforce-tp-progression \
  --optimization-mode medium_distance_volume \
  --skip-download \
  --run-guards
```

**Criteres succes:** 
- 7/7 guards PASS
- WFE > 0.6
- Sensitivity < 10%

**Next:** @Jordan execute, puis @Sam valide

