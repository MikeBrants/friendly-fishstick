# Validations Guards - @Sam

Ce fichier contient les validations des 7 guards par Sam.

---

## Format Message

```
## [HH:MM] [ACTION] @Sam -> @Casey
**Asset:** XXX
**Run ref:** [lien vers run Jordan]
**Date run:** YYYY-MM-DD (post-fix TP)

### Guards Check (7/7 requis)

| Guard | Seuil | Valeur | Status |
|-------|-------|--------|--------|
| guard001 MC p-value | < 0.05 | X.XX | PASS/FAIL |
| guard002 Sensitivity | < 10% | X.X% | PASS/FAIL |
| guard003 Bootstrap CI | > 1.0 | X.XX | PASS/FAIL |
| guard005 Top10 trades | < 40% | X.X% | PASS/FAIL |
| guard006 Stress Sharpe | > 1.0 | X.XX | PASS/FAIL |
| guard007 Regime mismatch | < 1% | X.X% | PASS/FAIL |
| WFE | > 0.6 | X.XX | PASS/FAIL |

### Metriques OOS
- Sharpe: X.XX
- MaxDD: X.X%
- Trades: XX

### Verifications
- [ ] TP progression: tp1 < tp2 < tp3, gaps >= 0.5
- [ ] Date post-fix (>= 2026-01-22 12H00)
- [ ] Pas de Sharpe suspect (> 4.0)

### Verdict
**Status:** 7/7 PASS | X/7 FAIL
**Raison si FAIL:** ...
**Recommendation:** PROD | BLOCKED | RETEST avec [variant]
**Next:** @Casey rend verdict final
```

### Actions possibles
- `[VALIDATION]` — Validation complete
- `[WAITING]` — En attente d'un run
- `[RECHECK]` — Re-validation demandee

---

## Historique

<!-- Les messages les plus recents en haut -->

## [14:15] [VALIDATION] @Sam -> @Casey

**Asset:** HBAR
**Run ref:** [14:02] [RUN_COMPLETE] @Jordan -> @Sam
**Date run:** 2026-01-23 14:02:03 (post-fix TP ✅)
**Mode:** baseline
**Displacement:** 78 (Phase 3A Rescue)

### Scan Results (Pre-Guards)

**Status:** ❌ **FAIL** - Scan échoué avant génération des guards

| Métrique | Seuil | Valeur | Status |
|----------|-------|--------|--------|
| OOS Sharpe | > 1.0 | 0.067 | ❌ FAIL |
| WFE | > 0.6 | 0.175 | ❌ FAIL |
| MC p-value | < 0.05 | 0.136 | ❌ FAIL |
| OOS Trades | > 60 | 78 | ✅ PASS |
| IS Sharpe | - | 1.86 | - |
| OOS MaxDD | - | -4.23% | - |

**Fail reason:** `OOS_SHARPE<1.0; WFE<0.6; OVERFIT`

### Guards Check (7/7 requis)

**⚠️ Guards non générés** - Scan FAIL avant guards

| Guard | Seuil | Valeur | Status |
|-------|-------|--------|--------|
| guard001 MC p-value | < 0.05 | 0.136 | ❌ FAIL (scan) |
| guard002 Sensitivity | < 10% | N/A | ❌ N/A |
| guard003 Bootstrap CI | > 1.0 | N/A | ❌ N/A |
| guard005 Top10 trades | < 40% | N/A | ❌ N/A |
| guard006 Stress Sharpe | > 1.0 | N/A | ❌ N/A |
| guard007 Regime mismatch | < 1% | N/A | ❌ N/A |
| WFE | > 0.6 | 0.175 | ❌ FAIL |

### Métriques OOS
- Sharpe: **0.067** ❌ (< 1.0 requis)
- MaxDD: **-4.23%**
- Trades: 78 ✅ (> 60 requis)
- Profit Factor: 1.07
- IS Sharpe: 1.86 (dégradation majeure: OOS/IS = 0.036)

### Vérifications
- [x] TP progression: tp1=2.75 < tp2=9.5 < tp3=10.0 ✅ (gaps: 6.75 et 0.5 >= 0.5)
- [x] Date post-fix (>= 2026-01-22 12H00) ✅ (2026-01-23 14:02:03)
- [x] Pas de Sharpe suspect (> 4.0) ✅ (0.067 très faible)

### Analyse de l'échec

**Overfitting sévère détecté:**
- **Dégradation majeure:** OOS Sharpe 0.067 vs IS Sharpe 1.86 → Ratio 0.036 (3.6% de performance retenue)
- **WFE 0.175:** Performance OOS très faible (17.5% de l'IS), bien en dessous du seuil critique de 0.6
- **MC p-value 0.136:** Guard001 FAIL (pas de significativité statistique, > 0.05)
- **Pattern:** Displacement 78 ne résout pas le problème (similaire à d26 qui avait échoué)

**Comparaison avec variants précédents:**
- **HBAR d52 medium_distance_volume:** WFE 0.63, OOS Sharpe 1.28 (4/7 guards FAIL)
- **HBAR d78 baseline:** WFE 0.175, OOS Sharpe 0.067 (scan FAIL, overfitting sévère)

### Verdict
**Status:** ❌ **SCAN FAIL** - Overfitting sévère, guards non générés

**Raisons FAIL:**
1. OOS Sharpe 0.067 < 1.0 (seuil critique)
2. WFE 0.175 < 0.6 (seuil critique)
3. MC p-value 0.136 > 0.05 (guard001 FAIL)
4. Dégradation majeure IS→OOS (ratio 0.036 = 3.6% performance retenue)
5. Overfitting sévère détecté (IS Sharpe 1.86 vs OOS 0.067)

**Recommandation:** ❌ **BLOCKED** - Variants épuisés

**Rationale:**
- Displacement 78 aggrave le problème (WFE 0.175 vs 0.63 en d52)
- Overfitting sévère (dégradation 96.4% IS→OOS)
- Aucun guard ne peut être validé (scan FAIL avant guards)
- Pattern similaire à d26 (échec précédent)

**Variants testés:**
1. ❌ **d52 baseline:** FAIL (guards non documentés)
2. ❌ **d52 medium_distance_volume:** 4/7 guards FAIL (sensitivity 11.49%, bootstrap CI 0.30, stress 0.62)
3. ❌ **d78 baseline:** Scan FAIL (overfitting sévère, WFE 0.175)

**Conclusion:** HBAR montre un pattern d'overfitting sévère qui ne peut être résolu par changement de displacement ou filter mode. Les variants sont épuisés.

**Next:** @Casey rend verdict final (BLOCKED définitif ou autres options)

---

## [15:30] [ANALYSIS] Phase 1 Screening - Résultats @Sam

**Task ref:** [14:30] [TASK] @Casey -> @Jordan - Phase 1 Screening
**Run ref:** [14:45] @Jordan RUN_START, scan complété 14:22:01
**Assets:** BNB, XRP, ADA, TRX, LTC, XLM (6 assets majeurs)
**Date run:** 2026-01-23 14:22:01 (post-fix TP ✅)

### Résultats Phase 1 Screening

**Verdict global:** ❌ **TOUS FAIL** - Aucun candidat viable pour Phase 2

**Note:** Phase 1 utilise `--skip-guards` (critères souples), donc analyse Sam basée sur métriques scan uniquement.

| Asset | OOS Sharpe | WFE | Trades | MC p-value | Status | Raison |
|:------|:-----------|:----|:-------|:----------|:-------|:-------|
| BNB | -1.28 | -0.56 | 90 | 0.848 | ❌ FAIL | OOS_SHARPE<1.0; WFE<0.6; OVERFIT |
| XRP | -1.04 | -0.33 | 90 | 0.482 | ❌ FAIL | OOS_SHARPE<1.0; WFE<0.6; OVERFIT |
| ADA | -0.23 | -0.08 | 81 | 0.108 | ❌ FAIL | OOS_SHARPE<1.0; WFE<0.6; OVERFIT |
| TRX | 0.56 | 0.19 | 114 | 0.218 | ❌ FAIL | OOS_SHARPE<1.0; WFE<0.6; OVERFIT |
| XLM | -0.82 | -0.36 | 84 | 0.374 | ❌ FAIL | OOS_SHARPE<1.0; WFE<0.6; OVERFIT |
| LTC | -0.81 | -0.24 | 48 | 0.418 | ❌ FAIL | OOS_SHARPE<1.0; WFE<0.6; TRADES<50; OVERFIT |

### Critères Phase 1 (souples)

| Critère | Seuil | Résultat |
|---------|-------|----------|
| WFE | > 0.5 | ❌ **Tous FAIL** (valeurs négatives ou < 0.2) |
| Sharpe OOS | > 0.8 | ❌ **Tous FAIL** (valeurs négatives sauf TRX 0.56) |
| Trades OOS | > 50 | ✅ 5/6 PASS (LTC FAIL avec 48 trades) |

### Analyse détaillée par asset

#### BNB
- **IS Sharpe:** 2.28
- **OOS Sharpe:** -1.28 ❌
- **WFE:** -0.56 ❌ (dégradation négative = OOS pire que IS)
- **MC p-value:** 0.848 ❌ (> 0.05, pas de significativité)
- **OOS MaxDD:** -4.08%
- **Params:** sl=4.5, tp1=3.75, tp2=5.5, tp3=7.5, tenkan=20, kijun=31, disp=52

#### XRP
- **IS Sharpe:** 3.15
- **OOS Sharpe:** -1.04 ❌
- **WFE:** -0.33 ❌
- **MC p-value:** 0.482 ❌
- **OOS MaxDD:** -2.81%
- **Params:** sl=3.75, tp1=4.0, tp2=5.5, tp3=9.5, tenkan=11, kijun=21, disp=52

#### ADA
- **IS Sharpe:** 2.88
- **OOS Sharpe:** -0.23 ❌
- **WFE:** -0.08 ❌ (dégradation presque totale)
- **MC p-value:** 0.108 ❌
- **OOS MaxDD:** -3.53%
- **Params:** sl=3.0, tp1=2.75, tp2=8.5, tp3=10.0, tenkan=9, kijun=36, disp=52

#### TRX
- **IS Sharpe:** 3.00
- **OOS Sharpe:** 0.56 ❌ (< 0.8 requis Phase 1)
- **WFE:** 0.19 ❌ (< 0.5 requis)
- **MC p-value:** 0.218 ❌
- **OOS MaxDD:** -2.75%
- **Params:** sl=3.75, tp1=3.0, tp2=6.0, tp3=9.5, tenkan=10, kijun=31, disp=52

#### XLM
- **IS Sharpe:** 2.25
- **OOS Sharpe:** -0.82 ❌
- **WFE:** -0.36 ❌
- **MC p-value:** 0.374 ❌
- **OOS MaxDD:** -2.45%
- **Params:** sl=3.75, tp1=1.75, tp2=6.5, tp3=10.0, tenkan=7, kijun=27, disp=52

#### LTC
- **IS Sharpe:** 3.38
- **OOS Sharpe:** -0.81 ❌
- **WFE:** -0.24 ❌
- **OOS Trades:** 48 ❌ (< 50 requis)
- **MC p-value:** 0.418 ❌
- **OOS MaxDD:** -3.40%
- **Params:** sl=4.5, tp1=5.0, tp2=8.0, tp3=10.0, tenkan=6, kijun=38, disp=52

### Patterns d'échec observés

**1. Overfitting sévère (tous les assets):**
- WFE négatif ou très faible (< 0.2) → OOS performe pire que IS
- Dégradation IS→OOS massive (souvent > 90%)
- MC p-value élevée (> 0.05) → pas de significativité statistique

**2. Critères Phase 1 non atteints:**
- **WFE > 0.5:** Tous FAIL (valeurs négatives ou < 0.2)
- **Sharpe OOS > 0.8:** Tous FAIL (valeurs négatives sauf TRX 0.56)
- **Trades > 50:** 5/6 PASS (LTC FAIL avec 48 trades)

**3. Pattern commun:**
- Tous les assets montrent IS Sharpe positif (2.25-3.38)
- Tous montrent OOS Sharpe négatif ou très faible (< 0.8)
- Tous montrent WFE négatif ou < 0.2
- Tous montrent MC p-value > 0.05 (pas de significativité)

### Verdict

**Status:** ❌ **TOUS EXCLUS** - Aucun candidat viable pour Phase 2

**Rationale:**
- Aucun asset ne passe les critères Phase 1 (WFE > 0.5, Sharpe OOS > 0.8, Trades > 50)
- Tous montrent overfitting sévère (WFE négatif ou < 0.2)
- MC p-value élevée (> 0.05) pour tous → pas de significativité statistique
- Aucun candidat viable pour Phase 2 validation (300 trials + 7 guards complets)

**Recommandation:** ❌ **EXCLUS** - Tous les assets ajoutés en EXCLUS dans `status/project-state.md`

**Next:** @Casey a déjà rendu verdict [15:00] - Tous EXCLUS

---

## [16:35] [ANALYSIS] Phase 1 Screening Batch 2 - Résultats @Sam

**Task ref:** [15:57] [TASK] @Casey -> @Jordan - Phase 1 Screening Batch 2
**Run ref:** [16:28] [RUN_COMPLETE] @Jordan -> @Casey
**Assets:** GMX, PENDLE, STX, IMX, FET (5 assets)
**Date run:** 2026-01-23 16:28:31 (post-fix TP ✅)

### Résultats Phase 1 Screening Batch 2

**Verdict global:** ✅ **1/5 PASS** - IMX candidat viable pour Phase 2

**Note:** Phase 1 utilise `--skip-guards` (critères souples), donc analyse Sam basée sur métriques scan uniquement.

| Asset | OOS Sharpe | WFE | Trades | MC p-value | Status | Verdict |
|:------|:-----------|:----|:-------|:----------|:-------|:-------|
| **IMX** | **1.64** ✅ | **0.71** ✅ | 85 ✅ | 0.062 | ✅ **SUCCESS** | **PASS Phase 1** 🎯 |
| GMX | -1.37 ❌ | -0.34 ❌ | 96 | 0.49 | ❌ FAIL | EXCLU (overfitting) |
| PENDLE | -0.12 ❌ | -0.12 ❌ | 120 | 0.222 | ❌ FAIL | EXCLU (overfitting) |
| STX | -0.60 ❌ | -0.14 ❌ | 105 | 0.322 | ❌ FAIL | EXCLU (overfitting) |
| FET | -0.09 ❌ | -0.03 ❌ | 81 | 0.232 | ❌ FAIL | EXCLU (overfitting) |

### Critères Phase 1 (souples)

| Critère | Seuil | Résultat |
|---------|-------|----------|
| WFE | > 0.5 | ✅ **1/5 PASS** (IMX 0.71) |
| Sharpe OOS | > 0.8 | ✅ **1/5 PASS** (IMX 1.64) |
| Trades OOS | > 50 | ✅ **5/5 PASS** (tous > 50) |

### Analyse détaillée par asset

#### ✅ IMX - PASS Phase 1
- **IS Sharpe:** 2.30
- **OOS Sharpe:** **1.64** ✅ (> 0.8 requis)
- **WFE:** **0.71** ✅ (> 0.5 requis)
- **OOS Trades:** 85 ✅ (> 50 requis)
- **MC p-value:** 0.062 ❌ (> 0.05, mais acceptable pour Phase 1)
- **OOS MaxDD:** -1.09%
- **Profit Factor:** 1.51
- **Params:** sl=5.0, tp1=2.0, tp2=8.5, tp3=9.5, tenkan=8, kijun=20, disp=52
- **Verdict:** ✅ **CANDIDAT VIABLE** → Phase 2 validation requise (300 trials + 7 guards complets)

#### ❌ GMX - FAIL
- **IS Sharpe:** 4.03
- **OOS Sharpe:** -1.37 ❌
- **WFE:** -0.34 ❌ (dégradation négative)
- **MC p-value:** 0.49 ❌
- **OOS MaxDD:** -2.29%
- **Params:** sl=5.0, tp1=1.5, tp2=7.0, tp3=8.0, tenkan=14, kijun=34, disp=52

#### ❌ PENDLE - FAIL
- **IS Sharpe:** 0.96
- **OOS Sharpe:** -0.12 ❌
- **WFE:** -0.12 ❌
- **MC p-value:** 0.222 ❌
- **OOS MaxDD:** -2.33%
- **Params:** sl=3.0, tp1=3.0, tp2=4.0, tp3=8.5, tenkan=6, kijun=22, disp=52

#### ❌ STX - FAIL
- **IS Sharpe:** 4.41
- **OOS Sharpe:** -0.60 ❌
- **WFE:** -0.14 ❌
- **MC p-value:** 0.322 ❌
- **OOS MaxDD:** -2.65%
- **Params:** sl=3.5, tp1=3.0, tp2=5.0, tp3=7.0, tenkan=6, kijun=38, disp=52

#### ❌ FET - FAIL
- **IS Sharpe:** 2.93
- **OOS Sharpe:** -0.09 ❌
- **WFE:** -0.03 ❌ (dégradation presque totale)
- **MC p-value:** 0.232 ❌
- **OOS MaxDD:** -2.59%
- **Params:** sl=3.25, tp1=2.75, tp2=6.5, tp3=10.0, tenkan=8, kijun=20, disp=52

### Patterns d'échec observés

**1. Overfitting sévère (4/5 assets):**
- GMX, PENDLE, STX, FET montrent WFE négatif ou très faible (< 0.2)
- Dégradation IS→OOS massive (souvent > 90%)
- MC p-value élevée (> 0.05) → pas de significativité statistique

**2. IMX exception:**
- WFE positif (0.71) → Performance OOS meilleure que IS
- Sharpe OOS positif (1.64) → Performance solide
- MC p-value 0.062 (légèrement > 0.05 mais acceptable pour Phase 1)
- Pattern différent des autres assets → Candidat viable

### Verdict

**Status:** ✅ **1/5 PASS** - IMX candidat viable pour Phase 2

**Recommandation:**
- ✅ **IMX:** PASS Phase 1 → Phase 2 validation requise (300 trials + 7 guards complets)
- ❌ **GMX, PENDLE, STX, FET:** EXCLUS (overfitting sévère, critères Phase 1 non atteints)

**Rationale:**
- IMX est le seul asset à passer les 3 critères Phase 1 (WFE > 0.5, Sharpe OOS > 0.8, Trades > 50)
- IMX montre WFE positif (0.71) contrairement aux autres assets (WFE négatif)
- IMX montre Sharpe OOS positif (1.64) avec performance solide
- Les 4 autres assets montrent overfitting sévère (pattern similaire à Phase 1 Batch 1)

**Next:** @Casey décide si IMX passe en Phase 2 validation (300 trials + 7 guards complets)

---

## [16:15] [WAITING] @Sam

**Status:** Validations complétées, surveillance active

**Dernières validations:**
- ✅ [14:15] HBAR d78 - Scan FAIL (overfitting sévère, WFE 0.175) → BLOCKED
- ✅ [15:30] Phase 1 Screening Batch 1 - 6 assets tous FAIL → EXCLUS (BNB, XRP, ADA, TRX, LTC, XLM)
- ✅ [16:35] Phase 1 Screening Batch 2 - 1/5 PASS (IMX) → Phase 2 requis

**Statut actuel:**
- **Assets PROD:** 15/20 (75% objectif)
- **Assets exclus récents:** HBAR, BNB, XRP, ADA, TRX, LTC, XLM, GMX, PENDLE, STX, FET
- **Phase 1 Batch 1:** 0/6 assets viables (tous FAIL)
- **Phase 1 Batch 2:** 1/5 assets viables (IMX PASS)
- **Candidat Phase 2:** IMX (en attente décision @Casey)

**Prochaines actions:**
- Surveiller décision @Casey pour IMX Phase 2
- Valider IMX Phase 2 si lancé (300 trials + 7 guards complets)
- Documenter verdicts dans ce fichier

---

## [10:30] [WAITING] Phase 3B Optimization - Surveillance @Sam

**Task ref:** Phase 3B Displacement Grid Optimization
**Assets:** BTC, ETH, JOE
**Run ref:** @Jordan lance `run_phase3b_optimization.py`
**Date run:** 2026-01-23 (en cours)

### Contexte
Phase 3B lancée sur les 3 premiers assets PROD pour tester les displacements alternatifs (26, 52, 78) et identifier des améliorations potentielles.

**Baseline actuel:**
- BTC: d52, baseline mode, Sharpe 2.14, WFE >0.6
- ETH: d52, medium_distance_volume mode, Sharpe 2.09, WFE 0.82
- JOE: d26, baseline mode, Sharpe 5.03, WFE 1.44

### Objectif
Surveiller les résultats de Phase 3B et analyser:
1. **Fichiers à surveiller:**
   - `outputs/displacement_optimization_*.csv` (résultats détaillés)
   - `outputs/displacement_optimization_summary_*.csv` (résumé avec recommandations)
   - `outputs/phase3b_*_guards_summary_*.csv` (guards par displacement)

2. **Critères d'évaluation:**
   - Amélioration Sharpe OOS > 10% vs baseline
   - 7/7 guards PASS pour le nouveau displacement
   - WFE maintenu > 0.6
   - Trades OOS > 60

3. **Actions requises:**
   - [ ] Vérifier que tous les runs sont complétés (3 assets × 3 displacements = 9 runs)
   - [ ] Analyser les résultats dans `displacement_optimization_summary_*.csv`
   - [ ] Pour chaque asset, valider les guards pour chaque displacement testé
   - [ ] Identifier les recommandations KEEP vs UPDATE
   - [ ] Vérifier que les améliorations > 10% respectent les critères (guards PASS)
   - [ ] Documenter les findings et recommandations

### Checklist Validation

Pour chaque asset (BTC, ETH, JOE) et chaque displacement (26, 52, 78):

- [ ] **Optimization complétée:** Scan results disponibles
- [ ] **Guards complétés:** 7/7 guards PASS/FAIL documentés
- [ ] **Métriques comparées:** Sharpe OOS, WFE, Trades vs baseline
- [ ] **Critère remplacement:** Amélioration > 10% ET 7/7 guards PASS
- [ ] **Recommandation:** KEEP (baseline optimal) ou UPDATE (nouveau displacement meilleur)

### Outputs attendus

1. **Résumé par asset:**
   - Displacement actuel vs meilleur displacement trouvé
   - Amélioration Sharpe (si applicable)
   - Status guards (7/7 PASS requis pour UPDATE)

2. **Recommandations finales:**
   - Assets à mettre à jour dans `asset_config.py` (si amélioration > 10% + guards PASS)
   - Assets à garder avec displacement actuel (baseline optimal)

**Next:** Analyser les résultats dès que disponibles et documenter les recommandations pour @Casey

## [23:20] [VALIDATION] @Sam -> @Casey

**Asset:** HBAR
**Run ref:** [23:06] [RUN_COMPLETE] @Jordan -> @Sam
**Date run:** 2026-01-22 22:56:14 (post-fix TP ✅)
**Mode:** medium_distance_volume
**Displacement:** 52

### Guards Check (7/7 requis)

| Guard | Seuil | Valeur | Status |
|-------|-------|--------|--------|
| guard001 MC p-value | < 0.05 | 0.01 | ✅ PASS |
| guard002 Sensitivity | < 10% | 11.49% | ❌ FAIL |
| guard003 Bootstrap CI | > 1.0 | 0.30 | ❌ FAIL |
| guard005 Top10 trades | < 40% | 41.05% | ❌ FAIL |
| guard006 Stress Sharpe | > 1.0 | 0.62 | ❌ FAIL |
| guard007 Regime mismatch | < 1% | 0.00% | ✅ PASS |
| WFE | > 0.6 | 0.63 | ✅ PASS |

### Métriques OOS
- Sharpe: 1.28 ✅ (> 1.0 requis)
- MaxDD: -3.81%
- Trades: 107 ✅ (> 60 requis)
- Profit Factor: 1.26

### Vérifications
- [x] TP progression: tp1=2.5 < tp2=6.5 < tp3=10.0 ✅ (gaps: 4.0 et 3.5 >= 0.5)
- [x] Date post-fix (>= 2026-01-22 12H00) ✅ (22:56:14)
- [x] Pas de Sharpe suspect (> 4.0) ✅ (1.28 normal)

### Analyse des échecs
**guard002 (Sensitivity 11.49%):** Légère amélioration vs baseline (13.01%) mais toujours > 10%. Le mode `medium_distance_volume` n'a pas suffi à réduire la variance sous le seuil critique.

**guard003 (Bootstrap CI 0.30):** Très faible, indique une robustesse statistique insuffisante. Le CI inférieur à 1.0 suggère un risque élevé de dégradation en production.

**guard005 (Top10 trades 41.05%):** Légèrement au-dessus du seuil (40%). Indique une dépendance à quelques trades exceptionnels.

**guard006 (Stress1 Sharpe 0.62):** Sous le seuil critique de 1.0. La stratégie ne résiste pas aux scénarios de stress test.

### Verdict
**Status:** 4/7 FAIL ❌

**Raisons FAIL:**
1. Sensitivity variance 11.49% > 10% (seuil critique)
2. Bootstrap CI 0.30 < 1.0 (robustesse statistique insuffisante)
3. Top10 trades 41.05% > 40% (dépendance aux outliers)
4. Stress1 Sharpe 0.62 < 1.0 (résistance au stress insuffisante)

**Recommandation:** BLOCKED ❌

**Rationale:**
- Le mode `medium_distance_volume` n'a pas résolu les problèmes de guards critiques (sensitivity, bootstrap CI, stress test)
- 4 guards FAIL dont 3 critiques (guard002, guard003, guard006)
- Amélioration marginale vs baseline mais insuffisante pour production

**Options de retest:**
1. Tester autre displacement (d26 ou d78) avec mode baseline
2. Tester mode `conservative` (tous filtres activés) si overfit sévère détecté
3. Considérer HBAR comme variant épuisé si aucun mode ne passe 7/7

**Next:** @Casey rend verdict final (BLOCKED ou RETEST avec variant)

---

## Référence - Patterns d'Échec Observés

### Overfitting Sévère (Pattern Principal)

**Symptômes:**
- WFE négatif ou très faible (< 0.2)
- Dégradation IS→OOS massive (> 90%)
- MC p-value élevée (> 0.05)
- OOS Sharpe négatif ou très faible (< 0.8)

**Exemples récents:**
- **HBAR d78:** WFE 0.175, OOS Sharpe 0.067, dégradation 96.4%
- **BNB:** WFE -0.56, OOS Sharpe -1.28, MC p-value 0.848
- **ADA:** WFE -0.08, OOS Sharpe -0.23, dégradation presque totale

**Action:** EXCLUS - Variants épuisés, pas de solution via displacement/filter mode

### Guards Critiques FAIL

**Pattern:**
- guard002 (Sensitivity) > 10% → Params instables
- guard003 (Bootstrap CI) < 1.0 → Robustesse statistique insuffisante
- guard006 (Stress Sharpe) < 1.0 → Résistance au stress insuffisante

**Exemple:**
- **HBAR d52 medium_distance_volume:** guard002 11.49%, guard003 0.30, guard006 0.62

**Action:** BLOCKED - Tester autres variants (displacement, filter mode)

### Critères Phase 1 Non Atteints

**Pattern:**
- WFE < 0.5 (souvent négatif)
- Sharpe OOS < 0.8 (souvent négatif)
- Trades < 50 (parfois)

**Exemple:**
- **Phase 1 Screening (6 assets):** Tous FAIL sur au moins 2 critères

**Action:** EXCLUS - Non viable pour Phase 2 validation

---

## Statistiques de Validation

**Total validations (2026-01-23):**
- HBAR d78: SCAN FAIL → BLOCKED
- Phase 1 Screening Batch 1: 6 assets → Tous EXCLUS (0/6)
- Phase 1 Screening Batch 2: 1/5 PASS (IMX) → Phase 2 requis
- **Taux de succès Phase 1:** 1/11 (9.1%) - IMX seul candidat viable
- **Taux de succès global:** 0% (0 assets validés Phase 2 aujourd'hui)

**Assets PROD actuel:** 15/20 (75% objectif)
**Candidat Phase 2:** IMX (en attente décision @Casey)

