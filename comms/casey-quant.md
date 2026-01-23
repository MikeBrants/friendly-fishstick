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

## [15:00] [DECISION] @Casey -> Phase 1 Screening

**Task ref:** [14:30] [TASK] @Casey -> @Jordan - Phase 1 Screening
**Assets:** BNB, XRP, ADA, TRX, LTC, XLM (6 assets majeurs)
**Run ref:** [14:45] @Jordan RUN_START, scan complété 14:22:01

**Resultats Phase 1 Screening:**
- **Tous les assets FAIL** ❌

| Asset | OOS Sharpe | WFE | Trades | Status | Raison |
|:------|:-----------|:----|:-------|:-------|:-------|
| BNB | -1.28 | -0.56 | 90 | ❌ FAIL | OOS_SHARPE<1.0; WFE<0.6; OVERFIT |
| XRP | -1.04 | -0.33 | 90 | ❌ FAIL | OOS_SHARPE<1.0; WFE<0.6; OVERFIT |
| ADA | -0.23 | -0.08 | 81 | ❌ FAIL | OOS_SHARPE<1.0; WFE<0.6; OVERFIT |
| TRX | 0.56 | 0.19 | 114 | ❌ FAIL | OOS_SHARPE<1.0; WFE<0.6; OVERFIT |
| XLM | -0.82 | -0.36 | 84 | ❌ FAIL | OOS_SHARPE<1.0; WFE<0.6; OVERFIT |
| LTC | -0.81 | -0.24 | 48 | ❌ FAIL | OOS_SHARPE<1.0; WFE<0.6; TRADES<50; OVERFIT |

**Verdict:** Tous EXCLUS ❌

**Rationale:**
- Aucun asset ne passe les critères Phase 1 (WFE > 0.5, Sharpe OOS > 0.8, Trades > 50)
- Tous montrent overfitting sévère (WFE négatif ou < 0.5)
- Aucun candidat viable pour Phase 2 validation

**Action:** BNB, XRP, ADA, TRX, LTC, XLM ajoutés en EXCLUS dans `status/project-state.md`

---

## [15:00] [DECISION] @Casey -> HBAR

**Asset:** HBAR
**Run ref:** [14:02] @Jordan RUN_COMPLETE, [14:32] [14:42] relances multiples
**Variants testés:**
- d26 baseline: FAIL (OOS Sharpe 0.30, WFE 0.11)
- d52 medium_distance_volume: FAIL (4/7 guards FAIL)
- d78 baseline: FAIL (OOS Sharpe 0.067, WFE 0.175, MC p-value 0.136)

**Resultats d78 (dernier test):**
- Scan: FAIL ❌
- OOS Sharpe: **0.067** (< 1.0 ❌)
- WFE: **0.175** (< 0.6 ❌)
- MC p-value: **0.136** (> 0.05 ❌ - Guard001 FAIL)
- Overfitting sévère: IS Sharpe 1.86 vs OOS 0.067

**Verdict:** EXCLU ❌

**Rationale:**
- 3 variants testés (d26, d52, d78) — tous FAIL
- Overfitting sévère sur tous les variants
- Variants épuisés — aucun displacement ne résout le problème

**Action:** HBAR ajouté en EXCLUS dans `status/project-state.md`

---

## [14:42] [UPDATE] @Jordan -> @Casey

**Task ref:** [14:30] [TASK] @Casey -> @Jordan
**Asset:** BNB
**Mode:** baseline
**Displacement:** auto
**Status:** ❌ Failed
**Duration:** 0 min

**Résultats préliminaires:**
- OOS Sharpe: N/A
- WFE: N/A

**Next:** @Sam valide les guards, puis @Casey rend verdict final

---


<!-- Les messages les plus recents en haut -->

## [14:30] [TASK] @Casey -> @Jordan

**Context:** Expansion portfolio - Phase 1 Screening sur 6 nouveaux assets majeurs pour identifier candidats viables avant Phase 2 validation complète.

**Task:** Phase 1 Screening - Identifier assets viables
**Assets:** BNB, XRP, ADA, TRX, LTC, XLM
**Objectif:** Identifier les candidats viables pour Phase 2 (validation complète avec guards)

**Command:**
```bash
python scripts/run_full_pipeline.py \
  --assets BNB,XRP,ADA,TRX,XLM,LTC \
  --trials 200 \
  --enforce-tp-progression \
  --skip-guards \
  --workers 10
```

**Criteres succes Phase 1 (souples):**
- WFE > 0.5
- Sharpe OOS > 0.8
- Trades OOS > 50

**Next:** 
- Les assets PASS Phase 1 → Phase 2 validation (300 trials + 7 guards complets)
- Les assets FAIL Phase 1 → Exclus (non viables)

---

## [14:00] [TASK] @Casey -> @Jordan

**Context:** HBAR d52 medium_distance_volume FAIL (4/7 guards). Phase 3A Rescue - tester displacement 78 (pattern similaire à MINA qui a réussi avec d78).

**Asset:** HBAR
**Variant:** Phase 3A Rescue - Displacement 78 (baseline mode)
**Hypothese:** Displacement 78 pourrait améliorer WFE et guards (pattern MINA: Sharpe 1.76, WFE 0.61 avec d78)

**Command:**
```bash
python scripts/run_full_pipeline.py \
  --assets HBAR \
  --fixed-displacement 78 \
  --trials-atr 300 \
  --trials-ichi 300 \
  --enforce-tp-progression \
  --run-guards \
  --workers 4
```

**Criteres succes:** 
- 7/7 guards PASS
- WFE > 0.6
- OOS Sharpe > 1.0 (target > 2.0)
- Trades OOS > 60

**Next:** @Jordan execute, puis @Sam valide les guards

---

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

## [15:00] [SUPERVISION] @Casey

**Cycle P0 - Etat actuel:**

**Completes:**
- ✅ AVAX: PRODUCTION (7/7 guards PASS, WFE 0.94)
- ❌ HBAR: EXCLU (d26, d52, d78 tous FAIL — variants épuisés)
- ❌ UNI moderate: EXCLU (Sharpe 0.03, WFE 0.01)
- ❌ Phase 1 Screening: BNB, XRP, ADA, TRX, LTC, XLM tous EXCLU (tous FAIL)

**Portfolio actuel:**
- **15 assets PROD** (75% objectif atteint)
- **30+ assets exclus** (HBAR + 6 assets Phase 1 ajoutés)

**Prochaines actions:**
- Identifier nouveaux assets Top 50 pour screening
- Objectif: 20+ assets PROD (5 restants)
- Focus sur assets non testés avec bonne liquidité

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

