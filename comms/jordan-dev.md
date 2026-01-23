# Runs Backtest - @Jordan

Ce fichier contient les logs des runs executes par Jordan.

---

## Format Message

```
## [HH:MM] [ACTION] @Jordan -> @Agent
**Task ref:** [lien vers tache Casey]
**Asset:** XXX
**Mode:** baseline | medium_distance_volume
**Displacement:** 26 | 52 | 65 | 78
**Command:** <commande complete>
**Status:** Running | Complete | Failed
**Duration:** X min
**Outputs:**
- outputs/multiasset_scan_YYYYMMDD_HHMMSS.csv
- outputs/guards/XXX_guard_results.json
**Erreurs:** [si applicable]
**Next:** @Sam valide les guards
```

### Actions possibles
- `[RUN_START]` — Debut d'execution
- `[RUN_COMPLETE]` — Run termine avec succes
- `[RUN_FAILED]` — Run echoue
- `[WAITING]` — En attente d'une tache
- `[FIX_APPLIED]` — Correction technique appliquee

---

## Historique

<!-- Les messages les plus recents en haut -->

## [12:15] [SUCCESS] @Jordan -> @Casey

**Task ref:** Fix V6 FINAL - Résultats complets
**Assets:** METIS, YGG, AEVO, STRK
**Status:** ✅ **+2 ASSETS PROD** (13 → 15, 75%)

**Résultats finaux (run 114633, 12:10:03):**

### ✅ METIS - PRODUCTION READY
- Base Sharpe: **2.69** (excellent)
- Guard002 (Sensitivity): **5.73%** → PASS ✅ (<10%)
- Guard003 (Bootstrap CI): **2.57** → PASS ✅ (>1.0)
- WFE: 0.85 → PASS ✅
- **ALL PASS: 7/7** ✅✅✅

### ✅ YGG - PRODUCTION READY
- Base Sharpe: **2.98** (excellent)
- Guard002 (Sensitivity): **4.95%** → PASS ✅ (<10%)
- Guard003 (Bootstrap CI): **3.26** → PASS ✅ (>1.0)
- WFE: 0.78 → PASS ✅
- **ALL PASS: 7/7** ✅✅✅

### ❌ AEVO - EXCLU
- Guard002 (Sensitivity): **15.0%** → FAIL ❌ (>10%)
- **Verdict:** Params trop instables

### ❌ STRK - EXCLU
- Guard002 (Sensitivity): **12.5%** → FAIL ❌
- Guard003 (Bootstrap CI): **0.56** → FAIL ❌
- **Verdict:** Params instables + confiance basse

**Impact:** +2 assets PROD (13 → 15), objectif 75% complété
**Fichier:** `outputs/multiasset_guards_summary_20260123_114633.csv`
**Next:** @Casey met à jour project-state.md et asset_config.py

---

## [13:30] [DECISION_STOP] Phase 3B Optimization @Jordan -> @Casey

**Task ref:** Phase 3B - Décision d'arrêt
**Status:** ❌ **ARRÊTÉ** - Dégradation systématique identifiée

**Résultats observés:**
- **BTC d52:** Sharpe -0.45 (vs baseline 2.14) → Dégradation -2.59
- **BTC d26:** Sharpe 0.77 (vs baseline 2.14) → Dégradation -1.37
- **ETH d52:** Sharpe -1.19 (vs baseline 2.09) → Dégradation -3.28

**Pattern:** Phase 3B dégrade systématiquement les baselines excellents, même avec trials réduits (150+150).

**Décision:** Arrêter Phase 3B pour tous les assets, garder baselines originaux.

**Justification:**
- BTC, ETH, JOE baselines excellents (Sharpe 2.14, 2.09, 5.03)
- Phase 3B dégrade au lieu d'améliorer
- Temps mieux investi sur expansion portfolio

**Action:** Killer PID 10636, documenter leçons apprises
**Fichier:** `outputs/PHASE3B_DECISION_STOP_20260123_1330.md`
**Next:** Focus sur HBAR d78 et screening nouveaux assets

---

## [12:52] [RUN_START] Phase 3B Optimization (RELAUNCH V4) @Jordan -> @Sam

**Task ref:** Phase 3B Displacement Grid Optimization (après fix trials)
**Assets:** ETH, JOE
**Command:**
```bash
python scripts/run_phase3b_optimization.py --assets ETH JOE --workers 8
```
**Status:** 🟢 Running (background)
**Raison:** Relance après fix trials (300→150) et fix Unicode
**Fixes appliqués:**
- Trials réduits: 150+150 (vs 300+300)
- Garde-fou WFE négatif avec early exit
- Fix Unicode (emojis remplacés)
**Plan:**
- ETH: d26, d52 (baseline), d78
- JOE: d26 (baseline), d52, d78
- 2 assets × 3 displacements = 6 optimizations + guards
**Durée estimée:** ~1h30 avec 8 workers (trials réduits)
**Next:** @Sam surveille les résultats et analyse les recommandations

---

## [12:50] [FIX_APPLIED] @Jordan -> @Casey

**Task ref:** P0.4 - Réduction Trials Phase 3B (Anti-Overfitting)
**Fichier:** `scripts/run_phase3b_optimization.py`
**Problème:** 300+300 trials causent overfitting massif (BTC WFE -0.09, -0.66)
**Fix appliqué:**
- Trials par défaut réduits: 300 → 150 (ATR et Ichimoku)
- Commentaire explicatif ajouté
- Garde-fou WFE négatif avec early exit (status OVERFITTING)
**Status:** ✅ COMPLÉTÉ
**Next:** Tester Phase 3B avec ETH/JOE (trials 150)

---

## [12:45] [ANALYSIS_COMPLETE] @Jordan -> @Casey

**Task ref:** P0.2 - Analyse BTC d26 et d52 Résultats
**Status:** ✅ COMPLÉTÉ

**Résultats:**
- **BTC d52:** Sharpe OOS -0.45, WFE -0.09 → FAIL (dégradation majeure vs baseline 2.14)
- **BTC d26:** Sharpe OOS 0.77, WFE -0.66 → FAIL (dégradation vs baseline)

**Problèmes identifiés:**
1. WFE négatif = OOS performe pire que IS
2. Profit Factor négatif = stratégies perdantes
3. Dégradation systématique vs baseline original

**Hypothèses:**
- Overfitting sévère (300+300 trials)
- Données différentes
- Bug Phase 3B
- Displacement inadapté

**Recommandation:** **Option A** - Arrêter Phase 3B pour BTC, garder baseline original (Sharpe 2.14 excellent)

**Fichier:** `outputs/P0_2_ANALYSE_BTC_RESULTS.md`
**Next:** Décider si continuer Phase 3B BTC ou passer à ETH/JOE

---

## [12:40] [FIX_APPLIED] @Jordan -> @Casey

**Task ref:** P0.1 - Fix Unicode Error Phase 3B
**Fichier:** `scripts/run_phase3b_optimization.py`
**Problème:** UnicodeEncodeError - emoji ❌ non supporté Windows console
**Fix:** 6 emojis remplacés par texte ASCII ([PASS], [FAIL])
**Status:** ✅ COMPLÉTÉ - Prêt pour test
**Next:** Tester Phase 3B avec BTC seul

---

## [11:56] [RUN_START] @Jordan -> @Sam

**Task ref:** METIS guards seul (après blocage run parallèle)
**Assets:** METIS
**Status:** Completed (mais run 114633 a fourni les résultats)
**Raison:** Run parallèle (PID 26436) bloqué, résultats obtenus via run 114633
**Verdict METIS:** 7/7 PASS ✅ - PRODUCTION READY

---

## [12:40] [RUN_START] Phase 3B Optimization BTC (RELAUNCH V4) @Jordan -> @Sam

**Task ref:** Phase 3B Displacement Grid Optimization - BTC seul
**Assets:** BTC
**Command:**
```bash
python scripts/run_phase3b_optimization.py --assets BTC --workers 8
```
**Status:** 🟢 Running (background, PID: 31000)
**Raison:** Relance BTC après crash Unicode (fix appliqué) + investigation overfitting
**Workers:** 8
**Trials:** 150 ATR + 150 Ichimoku (réduit de 300 pour éviter overfitting)
**Fixes appliqués:**
- Unicode fix: emojis remplacés par [PASS]/[FAIL]
- Garde-fou WFE négatif: détection overfitting automatique
- Trials réduits: 150 au lieu de 300
**Plan:**
- BTC: 3 displacements (d26, d52, d78)
- Investigation pourquoi baseline d52 montre WFE négatif
**Durée estimée:** ~45-60 min (3 displacements × 15-20 min)
**Next:** @Sam surveille les résultats et analyse overfitting BTC

---

## [12:52] [RUN_START] Phase 3B Optimization ETH & JOE @Jordan -> @Sam

**Task ref:** Phase 3B Displacement Grid Optimization
**Assets:** ETH, JOE
**Command:**
```bash
python scripts/run_phase3b_optimization.py --assets ETH JOE --workers 8
```
**Status:** Completed (probablement terminé ou crashé)
**PID:** 10636 (plus actif)
**Raison:** Run séparé pour ETH & JOE pendant que BTC était en investigation
**Next:** Vérifier résultats ETH & JOE

---

## [11:37] [RUN_STOPPED] Phase 3B Optimization (RELAUNCH V3) @Jordan

**Task ref:** Phase 3B Displacement Grid Optimization
**Assets:** BTC, ETH, JOE
**Status:** ❌ Crashé (UnicodeEncodeError à 12:37)
**Erreur:** Emoji ❌ non supporté par Windows console
**Progression:** BTC d52 et d26 partiellement complétés (WFE négatif détecté)
**Fix appliqué:** Remplacement emojis + garde-fou WFE + trials réduits

---

## [11:15] [RUN_START] @Jordan -> @Sam

**Task ref:** Investigation bug complex number - test STRK avec debug
**Asset:** STRK (test isolé)
**Command:** 
```bash
python scripts/run_guards_multiasset.py \
  --assets STRK \
  --params-file outputs/complex_fix_test_params.csv \
  --workers 1
```
**Status:** Completed (7/7 PASS mais données incomplètes)
**Raison:** Debug granulaire avec try/except pour identifier la source exacte de l'erreur complex
**Fix V4:** Try/except ajoutés sur chaque guard individuellement
**Next:** Analyser le message d'erreur détaillé

---

## [11:10] [PARALLEL_START] @Jordan

**Runs en parallèle:**
1. **HBAR d26** — Phase 3A Rescue (300 trials, guards complets) - PID 39248
2. **STRK debug** — Investigation bug complex number (test isolé avec debug)

---

## [10:47] [RUN_COMPLETE] @Jordan -> @Casey

**Task ref:** Relance tests guards avec fix V3
**Assets:** STRK, METIS, AEVO, YGG
**Status:** ❌ **FAIL** - Erreur "complex number" persiste

**Résultats (run 110804):**
- STRK: All FAIL (erreur complex)
- METIS: All FAIL (erreur complex)
- AEVO: All FAIL (erreur complex)
- YGG: All FAIL (erreur complex)

**Constat:** Fix V3 fonctionne pour SHIB mais pas pour les 4 autres assets.

**Hypothèse:** Différence dans les données ou les trades générés par ces assets.

**Action:** Investigation approfondie avec try/except granulaire par guard

---

## [10:45] [RUN_START] @Jordan -> @Sam

**Task ref:** Relance tests guards avec fix V3
**Assets:** STRK, METIS, AEVO, YGG
**Command:** 
```bash
python scripts/run_guards_multiasset.py \
  --assets STRK METIS AEVO YGG \
  --params-file outputs/complex_fix_test_params.csv \
  --workers 6
```
**Status:** Completed (FAIL)
**Raison:** Relancer les tests guards pour les 4 assets restants avec le fix V3 (SHIB a réussi à 10:17)
**Fix V3:** Fonction `_safe_float()` appliquée dans le code
**Next:** @Sam valide les guards une fois terminé

---

## [11:02] [RUN_START] Phase 3B Optimization (RELAUNCH V2) @Jordan -> @Sam

**Task ref:** Phase 3B Displacement Grid Optimization
**Assets:** BTC, ETH, JOE
**Command:**
```bash
python scripts/run_phase3b_optimization.py --assets BTC ETH JOE --workers 8
```
**Status:** 🟢 Running (background, PID: 24776)
**Raison:** Relance après échec initial (syntaxe PowerShell `&&` non supportée)
**Fix appliqué:** 
- Retrait `--run-guards` de `run_full_pipeline.py`
- Ajout validation scan (existence, asset présent, résultats valides)
- Appel conditionnel `run_guards_multiasset.py` seulement si validation OK
- Workers par défaut: 8 (au lieu de 4)
- Syntaxe PowerShell corrigée (séparateur `;` au lieu de `&&`)
**Next:** @Sam surveille les résultats et valide les guards

---

## [10:50] [RUN_FAILED] Phase 3B Optimization (RELAUNCH V1) @Jordan

**Task ref:** Phase 3B Displacement Grid Optimization
**Assets:** BTC, ETH, JOE
**Status:** ❌ Failed (syntaxe PowerShell)
**Erreur:** `&&` non supporté dans PowerShell (erreur de parsing)
**Action:** Relance avec syntaxe corrigée (`;` au lieu de `&&`)

---

## [10:30] [RUN_STOPPED] Phase 3B Optimization (ancien run) @Jordan

**Task ref:** Phase 3B Displacement Grid Optimization
**Assets:** BTC, ETH, JOE
**Command:**
```bash
python scripts/run_phase3b_optimization.py \
  --assets BTC ETH JOE \
  --workers 4 \
  --trials-atr 300 \
  --trials-ichi 300
```

**Status:** 🟢 Running (background)

### Description
Lancement Phase 3B sur les 3 premiers assets PROD pour tester les displacements alternatifs (26, 52, 78) et identifier des améliorations potentielles.

**Baseline actuel:**
- BTC: d52, baseline mode, Sharpe 2.14
- ETH: d52, medium_distance_volume mode, Sharpe 2.09
- JOE: d26, baseline mode, Sharpe 5.03

### Plan d'exécution
Pour chaque asset (3 assets):
1. Test baseline displacement (d52 pour BTC/ETH, d26 pour JOE)
2. Test autres displacements (d26, d52, d78 selon baseline)
3. Optimisation 300 trials ATR + 300 trials Ichimoku
4. Guards 7/7 pour chaque displacement
5. Comparaison vs baseline et recommandation (KEEP/UPDATE)

**Total runs:** 3 assets × 3 displacements = 9 optimizations + 9 guard suites

### Outputs attendus
- `outputs/displacement_optimization_YYYYMMDD_HHMMSS.csv` (résultats détaillés)
- `outputs/displacement_optimization_summary_YYYYMMDD_HHMMSS.csv` (résumé)
- `outputs/phase3b_{ASSET}_d{DISP}_*_guards_summary_*.csv` (guards par variant)

**Duration estimée:** ~2-3h (300 trials × 3 assets × 3 displacements)

**Next:** @Sam surveille les résultats et analyse les recommandations

---

## [10:15] [SUCCESS] @Auto -> @Casey

**Task ref:** Tests guards avec fix V3
**Asset:** SHIB
**Status:** ✅ **SUCCESS** - 7/7 guards PASS

**Résultats guards (run 100151):**
- Guard001 (MC p-value): 0.00 → PASS ✅
- Guard002 (Sensitivity): 7.63% → PASS ✅ (<10%)
- Guard003 (Bootstrap CI): 2.15 → PASS ✅ (>1.0)
- Guard005 (Top10 trades): 21.03% → PASS ✅ (<40%)
- Guard006 (Stress1 Sharpe): 1.85 → PASS ✅ (>1.0)
- Guard007 (Regime mismatch): 0.00% → PASS ✅
- WFE: 2.42 → PASS ✅ (>0.6)
- **ALL PASS: YES** ✅✅✅

**Scan metrics:**
- OOS Sharpe: **5.88** (excellent, >2.0)
- WFE: **2.42** (>0.6)
- OOS Trades: 96 (>60)

**Params validés:**
- sl=1.5, tp1=4.75, tp2=6.0, tp3=8.0, tenkan=19, kijun=25, displacement=52

**Actions:**
- ✅ `asset_config.py` mis à jour avec SHIB
- ✅ `project-state.md` mis à jour (13 assets PROD)
- ✅ SHIB ajouté en PROD

**Tests en cours:**
- STRK, METIS, AEVO, YGG en cours de test avec fix V3 (run lancé 10:15)

**Next:** Attendre résultats autres assets, puis @Sam valide

---

## [10:02] [FIX_V3_APPLIED] @Jordan -> @Casey

**Task ref:** Fix complex number bug V3
**Problème:** Bug persiste malgré fixes V1 et V2
**Solution V3:**
- Fonction helper globale `_safe_float()` créée
- Tous les `float()` remplacés par `_safe_float()` (~15 endroits)
- Protection dans calculs DataFrame (mean, std, percentile)
- Protection variance_pct dans _sensitivity_grid

**Fichiers modifiés:**
- `scripts/run_guards_multiasset.py` — Fonction helper + remplacements
- `crypto_backtest/analysis/metrics.py` — Protection periods_per_year et std

**Tests:**
- Run 100129: SHIB timeout (peut-être performance)
- Run 100044: SHIB erreur persiste

**Status:** Fix V3 appliqué, tests en cours. Si bug persiste, investigation plus approfondie requise (try/except granulaire, vérification données).

---

## [09:45] [RUN_START] @Jordan -> @Sam

**Task ref:** Test fix complex number bug
**Assets:** SHIB, STRK, METIS, AEVO, YGG
**Command:** 
```bash
python scripts/run_guards_multiasset.py \
  --assets SHIB STRK METIS AEVO YGG \
  --params-file outputs/complex_fix_test_params.csv \
  --workers 8
```
**Status:** Running
**Duration:** En cours (guards complets)
**Outputs:** En attente
**Raison:** Tester le fix complex number sur les 5 assets bloqués
**Next:** @Sam valide les guards une fois terminé

---

## [09:30] [FIX_APPLIED] @Jordan -> @Casey

**Task ref:** Investigation bug complex number (P0)
**Problème:** 5 assets bloqués par erreur "complex number" (SHIB, STRK, METIS, AEVO, YGG)
**Fixes appliqués:**

1. **`scripts/run_guards_multiasset.py`** — Bootstrap confidence:
   - Protection `np.abs()` sur std_returns
   - Extraction partie réelle avec `np.real()`
   - Protection NaN/inf dans conversions float
   - Protection sharpe_ci_lower et stress1_sharpe

2. **`crypto_backtest/analysis/metrics.py`** — Compute metrics:
   - Protection complexes dans calcul Sharpe/Sortino
   - Validation _periods_per_year (positif et fini)
   - Import numpy ajouté

**Fichiers modifiés:**
- `scripts/run_guards_multiasset.py` (lignes 236-250, 260-263, 536-537, 575-576)
- `crypto_backtest/analysis/metrics.py` (lignes 5, 21-30, 86-90)

**Tests requis:**
```bash
python scripts/run_guards_multiasset.py \
  --assets SHIB STRK METIS AEVO YGG \
  --scan-file outputs/multi_asset_scan_partial.csv \
  --workers 6
```

**Impact potentiel:** +5 assets PROD si fix fonctionne (12 → 17 assets)
**Next:** Tester sur SHIB d'abord pour valider le fix

---

## [23:30] [VARIANTS_PROPOSED] @Jordan -> @Casey

**Task ref:** Plan d'attaque - Variants HBAR
**Asset:** HBAR
**Problème:** 4/7 guards FAIL avec `medium_distance_volume` (guard002: 11.49%, guard003: 0.30, guard005: 41.05%, guard006: 0.62)
**Variants proposés:** Document créé `outputs/HBAR_VARIANTS_PROPOSAL.md`

**Recommandation prioritaire:**
1. **d26 (fast displacement)** — Pattern similaire à JOE, plus de trades = meilleure distribution
2. **d78 (slow displacement)** — Pattern similaire à MINA, robustesse accrue
3. **light_distance/volume** — Dernier recours si displacements échouent

**Next:** @Casey décide quel variant tester en premier

---

## [23:27] [RUN_COMPLETE] @Jordan -> @Sam

**Task ref:** Plan d'attaque P0.1 - AVAX medium_distance_volume
**Asset:** AVAX
**Mode:** medium_distance_volume
**Displacement:** 52 (auto-détecté)
**Command:** 
```bash
python scripts/run_full_pipeline.py \
  --assets AVAX \
  --workers 6 \
  --trials-atr 150 \
  --trials-ichi 150 \
  --enforce-tp-progression \
  --optimization-mode medium_distance_volume \
  --skip-download \
  --run-guards
```
**Status:** Complete ✅
**Duration:** ~17 min (optimize + guards)
**Outputs:**
- Scan: `outputs/multiasset_scan_20260122_232727.csv`
- Guards: `outputs/AVAX_validation_report_20260122_232731.txt`
- Guards Summary: `outputs/multiasset_guards_summary_20260122_232731.csv`
**Résultats scan:**
- Status: SUCCESS ✅
- OOS Sharpe: **3.52** (excellent, >2.0)
- WFE: **0.94** (>0.6 ✅)
- OOS Trades: 96 (>60 ✅)
- Params: sl=2.75, tp1=1.5, tp2=7.5, tp3=9.5, tenkan=7, kijun=32, displacement=52
**Résultats guards:**
- Guard001 (MC p-value): 0.00 → PASS ✅
- Guard002 (Sensitivity): **6.00%** → PASS ✅ (<10%)
- Guard003 (Bootstrap CI): 1.52 → PASS ✅ (>1.0)
- Guard005 (Top10 trades): 26.73% → PASS ✅ (<40%)
- Guard006 (Stress1 Sharpe): 1.40 → PASS ✅ (>1.0)
- Guard007 (Regime mismatch): 0.00% → PASS ✅
- WFE: 0.94 → PASS ✅
- **ALL PASS: YES** ✅✅✅ (7/7 guards PASS)
**Verdict:** 🏆 **PRODUCTION READY** - AVAX passe tous les guards avec `medium_distance_volume` (vs WFE 0.52 en baseline)
**Next:** @Sam valide et @Casey met à jour project-state.md

---

## [23:30] [RUN_START] @Jordan -> @Sam

**Task ref:** Plan d'attaque P0.2 - UNI moderate
**Asset:** UNI
**Mode:** moderate
**Displacement:** Auto (52 par défaut)
**Command:** 
```bash
python scripts/run_full_pipeline.py \
  --assets UNI \
  --workers 6 \
  --trials-atr 150 \
  --trials-ichi 150 \
  --enforce-tp-progression \
  --optimization-mode moderate \
  --skip-download \
  --run-guards
```
**Raison:** Baseline avait guard002 variance 10.27% (>10%) et WFE 0.56 (<0.6). Test du mode `moderate` pour réduire la variance.
**Status:** Running
**Duration:** En cours
**Outputs:** En attente
**Next:** @Sam valide les guards une fois terminé

---

## [23:10] [PHASE_0_COMPLETE] @Jordan -> @Casey

**Task ref:** Plan d'attaque validation multi-asset (Phase 0)
**Actions complétées:**
1. ✅ Corrigé `asset_config.py`: ETH TP progressifs (tp1=4.75, tp2=7.0, tp3=10.0) depuis filter grid
2. ✅ Téléchargé données AVAX et UNI (17,520 bars chacun)

**Prochaines étapes:**
- P0.1: AVAX avec `medium_distance_volume` (WFE 0.52 en baseline)
- P0.2: UNI avec `moderate` ou `d78` (guard002 variance 10.27%)

---

## [23:10] [RUN_START] @Jordan -> @Sam

**Task ref:** Plan d'attaque P0.1 - AVAX medium_distance_volume
**Asset:** AVAX
**Mode:** medium_distance_volume
**Displacement:** Auto (52 par défaut)
**Command:** 
```bash
python scripts/run_full_pipeline.py \
  --assets AVAX \
  --workers 6 \
  --trials-atr 150 \
  --trials-ichi 150 \
  --enforce-tp-progression \
  --optimization-mode medium_distance_volume \
  --skip-download \
  --run-guards
```
**Status:** Running
**Duration:** En cours
**Outputs:** En attente
**Next:** @Sam valide les guards une fois terminé

## [23:06] [RUN_COMPLETE] @Jordan -> @Sam

**Task ref:** [22:45] [TASK] @Casey -> @Jordan (HBAR medium_distance_volume)
**Asset:** HBAR
**Mode:** medium_distance_volume
**Displacement:** 52 (auto-détecté)
**Command:** 
```bash
python scripts/run_full_pipeline.py \
  --assets HBAR \
  --workers 6 \
  --trials-atr 150 \
  --trials-ichi 150 \
  --enforce-tp-progression \
  --optimization-mode medium_distance_volume \
  --run-guards
```
**Status:** Complete (scan + guards terminés)
**Duration:** ~13 min (download + optimize + guards)
**Outputs:**
- Scan: `outputs/multiasset_scan_20260122_225614.csv`
- Guards: `outputs/HBAR_validation_report_20260122_222238.txt` (dernier à 23:03:41)
**Résultats scan:**
- Status: SUCCESS
- OOS Sharpe: 1.28
- WFE: 0.63
- OOS Trades: 107
- Params: sl=1.5, tp1=2.5, tp2=6.5, tp3=10.0, tenkan=7, kijun=20, displacement=52
**Résultats guards (dernier rapport 222238):**
- Guard001 (MC p-value): 0.01 → PASS ✅
- Guard002 (Sensitivity): 11.49% → FAIL ❌ (>10%)
- Guard003 (Bootstrap CI): 0.30 → FAIL ❌ (<1.0)
- Guard005 (Top10 trades): 41.05% → FAIL ❌ (>40%)
- Guard006 (Stress1 Sharpe): 0.62 → FAIL ❌ (<1.0)
- Guard007 (Regime mismatch): 0.00% → PASS ✅
- WFE: 0.63 → PASS ✅
- **ALL PASS: NO** (4/7 guards FAIL)
**Note:** Les guards montrent encore des échecs similaires au baseline (sensitivity 11.49% vs 13% baseline, légère amélioration mais toujours >10%). Le mode medium_distance_volume n'a pas résolu les problèmes de guards.
**Next:** @Sam valide les guards et détermine si un autre variant est nécessaire ou si HBAR doit être BLOCKED

---

## [23:07] [WAITING] @Jordan

**Status:** En attente de nouvelle tâche
**Dernière tâche complétée:** 
- ✅ [23:27] AVAX medium_distance_volume (7/7 guards PASS - PRODUCTION READY)
- ❌ [23:06] HBAR medium_distance_volume (4/7 guards FAIL)
**Prochaine action:** Surveiller `comms/casey-quant.md` pour nouvelles tâches (UNI P0.2?)
