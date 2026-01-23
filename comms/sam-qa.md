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

## [14:20] [WAITING] @Sam

**Status:** Validation complétée, en attente de nouveaux runs

**Dernière validation:**
- ✅ [14:15] HBAR d78 - Scan FAIL (overfitting sévère, WFE 0.175) → BLOCKED

**Runs en attente:**
- 🔄 Phase 1 Screening: BNB, XRP, ADA, TRX, LTC, XLM (assigné [14:30] @Casey -> @Jordan, critères souples: WFE > 0.5, Sharpe > 0.8, Trades > 50)
  - **Note:** Phase 1 utilise `--skip-guards`, donc validation Sam requise seulement pour Phase 2 (si assets PASS Phase 1)

**Prochaines actions:**
- Surveiller `comms/jordan-dev.md` pour Phase 1 Screening results
- Valider les assets qui PASS Phase 1 → Phase 2 (300 trials + 7 guards complets)
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

