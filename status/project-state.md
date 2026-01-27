# PROJECT STATE — FINAL TRIGGER v2

**Updated**: 27 Jan 2026, 04:56 UTC  
**Phase**: 🟡 **PHASE 1 SCREENING** en cours  
**Status**: 0/26 PROD

> Pour les paramètres → `.cursor/rules/MASTER_PLAN.mdc`  
> Pour les commandes → `docs/WORKFLOW_PIPELINE.md`

---

## ⚠️ RÈGLES DE MISE À JOUR

**CE FICHIER CHANGE SOUVENT** — Mettre à jour:
- Après chaque Phase complétée
- Quand un asset change de status (PENDING → PROD ou → EXCLU)
- Max 1× par jour sauf urgence

**FORMAT OBLIGATOIRE:**
- Header "Updated" : toujours mettre à jour la date
- Assets : listes simples, pas de tableaux détaillés
- Historique : garder **max 10 entrées** (supprimer les plus anciennes)
- Progression : mettre à jour les chiffres "Actuel"

**NE PAS AJOUTER:**
- Détails des guards (→ MASTER_PLAN.mdc)
- Commandes (→ WORKFLOW_PIPELINE.md)
- Blocs de code Python
- Explications longues

**OWNER:** Casey (Orchestrateur) — Seul autorisé à modifier ce fichier

---

## 🚨 CONTEXTE: RESET PR#20

**Tous les résultats précédents sont invalidés** suite au bug PR#19 (SHORT signal).

| Catégorie | Avant | Après |
|----------|-------|-------|
| PROD | 12 | **0** |
| PENDING | 0 | **26** |
| EXCLU | 14 | **0** |

---

## 📊 ASSET STATUS

### ✅ PROD (0)

*Aucun asset validé pour le moment.*

### 🟡 EN COURS (Phase 1 Screening)

```
SHIB DOT TIA NEAR DOGE ANKR ETH JOE YGG MINA CAKE RUNE
EGLD AVAX HBAR TON SUSHI CRV BTC ONE SEI AXS SOL AAVE ZIL GALA
```

### ❌ EXCLU (0)

*Aucun asset exclu pour le moment.*

---

## 🎯 PHASE ACTUELLE

| Phase | Status | Détails |
|-------|--------|--------|
| 0 Data | ✅ Done | 26 assets téléchargés |
| **1 Screening** | 🟡 **EN COURS** | 200 trials, workers=10 |
| 2 Validation | ⏳ Pending | - |
| 3 Rescue | ⏳ Pending | - |
| 4 Signal Parity | ⏳ Pending | - |
| 5 Portfolio | ⏳ Pending | - |
| 6 Production | ⏳ Pending | - |

---

## 📈 PROGRESSION

| Métrique | Cible | Actuel |
|----------|-------|--------|
| Assets PROD | 20+ | **0** |
| Phase 1 complete | 26 | 0 |
| Phase 2 complete | - | 0 |

---

## ⏭️ PROCHAINE ACTION

1. **Attendre fin Phase 1** (screening 26 assets)
2. Analyser résultats: `outputs/screening_multiasset_scan_*.csv`
3. Identifier candidats: WFE>0.5, Sharpe>0.5, Trades>50, SHORT 25-75%
4. Lancer Phase 2 sur candidats (workers=1)

---

## 🗓️ HISTORIQUE RÉCENT

| Date | Action |
|------|--------|
| 27 Jan 04:56 | ? Worst-Case Path Analysis (Agent: Sam) ? crypto_backtest/validation/worst_case.py, tests/test_worst_case.py |
| 27 Jan 04:55 | ? Multi-Period Validation (Agent: Alex) ? crypto_backtest/validation/multi_period.py, tests/test_multi_period.py |
| 27 Jan 04:53 | ? CPCV Full defaults + calculate_pbo (Agent: Alex) ? crypto_backtest/validation/cpcv.py |
| 27 Jan 04:48 | ? Regime Stress Test Script (Agent: Jordan) ? scripts/run_regime_stress_test.py, tests/test_regime_stress.py |
| 27 Jan 04:33 | GitHub cleanup: branches obsol?tes supprim?es; Issue #21 + PR #13/#14 ? fermer via Web UI; fichiers untracked conserv?s (PID 159404 actif) |
| 26 Jan 20:57 | Ajout règles MAJ dans 3 fichiers |
| 26 Jan 20:52 | Doc refonte (MASTER_PLAN, WORKFLOW_PIPELINE, project-state) |
| 26 Jan 19:27 | PR#20 mergé — Reset 0 PROD |
| 26 Jan 16:00 | PR#19 mergé — Fix SHORT signal bug |
| 25 Jan | 12 assets validés (maintenant invalidés) |

---

## 🤖 AGENTS

| Agent | Focus actuel |
|-------|-------------|
| **Casey** | Supervision Phase 1 |
| **Jordan** | Exécution screening |
| **Sam** | Préparation guards Phase 2 |
| **Alex** | - |

---

## 📁 FICHIERS

| Fichier | Contenu |
|---------|---------|
| `.cursor/rules/MASTER_PLAN.mdc` | Params, guards, règles |
| `docs/WORKFLOW_PIPELINE.md` | Commandes par phase |
| `status/project-state.md` | **CE FICHIER** (état) |
| `comms/*.md` | Communication agents |

---

**Version**: 2.1 (26 Jan 2026)
