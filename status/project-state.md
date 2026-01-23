# Project State — FINAL TRIGGER v2

**Derniere mise a jour:** 2026-01-24 02:58 @Casey

***

## 🚨 STATUS GLOBAL: RESET COMPLET REQUIS

| Metrique | Valeur |
|----------|--------|
| Phase | **RESET COMPLET — Re-screening requis** |
| Assets PROD | **0** (tous résultats invalides, bug Optuna) |
| Assets à re-tester | **60+** (anciens PROD + EXCLUS + nouveaux) |
| Assets définitivement exclus | **7** (données insuffisantes: HOOK, ALICE, HMSTR, LOOM, APT, EIGEN, ONDO) |
| Bug critique | ✅ RESOLU (TP progression + complex numbers + Optuna sampler) |
| Optuna Fix | ✅ VERIFIED (deterministic hashlib seeds, 5+ identical runs) |
| Guards Config | ✅ VERIFIED (mc=1000, bootstrap=10000) |
| Reproducibility | ✅ CONFIRMED (100% match across runs) |
| **CONSÉQUENCE** | ⚠️ **TOUS LES RÉSULTATS ANTÉRIEURS SONT INVALIDES** |

***

## 📋 ANCIENS RÉSULTATS (INVALIDES — Bug Optuna)

### Anciens "PROD" (15 assets) — RE-SCREENING REQUIS ⚠️
BTC, ETH, JOE, OSMO, MINA, AVAX, AR, ANKR, DOGE, OP, DOT, NEAR, SHIB, METIS, YGG

**Note:** Ces assets avaient passé 7/7 guards AVEC BUG. Résultats non-reproductibles.  
**Action:** Re-tester en Phase 1 (Batch 1 prioritaire).

### Anciens "EXCLUS" (31+ assets) — RE-SCREENING REQUIS ⚠️
SEI, CAKE, AXS, RUNE, TON, SOL, AAVE, HYPE, ATOM, ARB, LINK, INJ, TIA,
ICP, ARKM, EGLD, UNI, STRK, AEVO, HBAR, IMX, BNB, XRP, ADA, TRX, LTC, XLM

**Note:** Ces assets avaient FAIL guards AVEC BUG. Décisions basées sur résultats faux.  
**Action:** Re-tester en Phase 1 (Batch 2-5).

### Exclusions DÉFINITIVES (7 assets) — Pas de re-test ❌
HOOK, ALICE, HMSTR, LOOM, APT, EIGEN, ONDO

**Raison:** Problèmes techniques fondamentaux (données insuffisantes < 8000 bars, outliers structurels).  
**Action:** EXCLURE définitivement (pas lié au bug Optuna).

***

## Blockers

| Asset | Blocker | Resolution | Status |
|-------|---------|------------|--------|
| UNI | guard002 variance 26.23% > 10%, WFE 0.42 < 0.6, moderate FAIL | Variants épuisés — **EXCLU** | ❌ |
| HBAR | d26 FAIL (Sharpe 0.30, WFE 0.11), d78 FAIL (Sharpe 0.067, WFE 0.175) | Variants épuisés — **EXCLU** | ❌ |
| IMX | baseline d52 (4/7 guards), medium_distance_volume d52 FAIL, d26 FAIL, d78 FAIL | Variants épuisés — **EXCLU** | ❌ |
| SHIB | Guards complex number error | ✅ **RESOLU** — Fix V3 réussi, 7/7 guards PASS | ✅ |
| METIS, YGG | Guards complex number error | ✅ **RESOLU** — Fix V6 réussi, 7/7 guards PASS | ✅ |
| STRK, AEVO | Guards complex number error | Fix V6 appliqué — EXCLUS (sensitivity > 10%) | ❌ |

***

## Corrections Techniques (2026-01-22)

### 1. Timezone Fix
- **Fichier:** `crypto_backtest/optimization/parallel_optimizer.py`
- **Problème:** Index timezone-naive causait erreur "complex numbers" dans guards
- **Solution:** Force UTC timezone sur tous les DataFrames chargés
- **Impact:** Résout guards pour STRK, METIS, AEVO (en cours de validation)

### 2. Asset Config Update
- **Fichier:** `crypto_backtest/config/asset_config.py`
- **Changements:** TP progressifs pour tous les assets PROD
- **Ajouts:** AR, ANKR, DOGE, OP, AVAX, DOT, NEAR avec params validés (12 assets PROD total)

### 3. Data Download
- **Complété:** 15 assets téléchargés (ETH, AVAX, UNI, DOT, SHIB, NEAR, OP, DOGE, AR, EGLD, ANKR, JOE, OSMO, MINA, BTC)

***

## Decisions

| Date | Decision | Rationale | Par |
|:-----|:---------|:----------|:----|
| 2026-01-22 | TP progression enforced par defaut | Bug invalidait tous les resultats | @Casey |
| 2026-01-22 | ETH mode medium_distance_volume | WFE 0.82 vs 0.52 baseline | @Sam |
| 2026-01-22 | AVAX mode medium_distance_volume | WFE 0.94 vs 0.52 baseline | @Jordan |
| 2026-01-22 | Timezone fix appliqué | Résout erreur complex numbers | @Jordan |
| 2026-01-22 | AR, ANKR, DOGE, OP ajoutés en PROD | 7/7 guards PASS | @Jordan |
| 2026-01-23 | UNI test moderate mode | FAIL (OOS Sharpe 0.03, WFE 0.01) — EXCLU | @Jordan |
| 2026-01-23 | asset_config.py mis à jour | 12 assets PROD avec params validés | @Jordan |
| 2026-01-23 | DOT, NEAR ajoutés en PROD | 6/7 guards PASS, WFE > 0.6 (scan) | @Jordan |
| 2026-01-23 | HBAR exclu | d26 et d78 FAIL, variants épuisés | @Casey |
| 2026-01-23 | Phase 1 Screening | BNB, XRP, ADA, TRX, LTC, XLM tous FAIL | @Casey |

***

## Corrections Techniques (2026-01-24)

### Optuna Reproducibility Fix — VERIFIED ✅
- **Fichier:** `crypto_backtest/optimization/parallel_optimizer.py`
- **Problème:** TPESampler non-déterministe avec workers > 1 (Python hash() non-déterministe)
- **Solution:** 
  - Deterministic seed: `hashlib.md5(asset).hexdigest()` au lieu de `hash(asset)`
  - Reseed before each optimizer (atr, ichimoku, conservative)
  - `create_sampler()` avec `multivariate=True`, `constant_liar=True`
- **Verification:** 5+ runs consécutifs produisent résultats identiques ✅
- **Impact:** Système maintenant scientifiquement reproductible

### Re-validation Test Results (24-JAN 02:44-02:50)
- **BTC**: Sharpe 1.21, WFE 0.42 → FAIL (overfit) ✅ Reproductible
- **ETH**: Sharpe 3.22, WFE 1.17 → SUCCESS ✅ Reproductible
- **ONE, GALA, ZIL**: Tous FAIL mais reproductibles ✅

### Guards Audit — VERIFIED ✅
- **Fichier:** `scripts/run_guards_multiasset.py`
- **Vérification:** mc-iterations=1000 ✅, bootstrap-samples=10000 ✅
- **Status:** Conformes aux best practices académiques

***

## Prochaines Étapes — RESET COMPLET

### Phase 0: Préparation (DONE ✅)
1. ✅ Pipeline fix complet (TP progression + complex numbers + Optuna)
2. ✅ Reproducibility audit (BTC, ETH, ONE, GALA, ZIL confirmés)
3. ✅ Guards config verification (mc=1000, bootstrap=10000)
4. ✅ Stratégie RESET COMPLET définie

### Phase 1: Re-screening (60+ assets, ~3h total) — URGENT ⚠️
**TOUS LES ANCIENS RÉSULTATS SONT INVALIDES** (bug Optuna non-déterministe)

**Batch 1** (15 assets, 45 min): BTC, ETH, JOE, OSMO, MINA, AVAX, AR, ANKR, DOGE, OP, DOT, NEAR, SHIB, METIS, YGG  
**Batch 2** (15 assets, 45 min): SOL, ADA, XRP, BNB, TRX, LTC, MATIC, ATOM, LINK, UNI, ARB, HBAR, ICP, ALGO, FTM  
**Batch 3** (10 assets, 30 min): AAVE, MKR, CRV, SUSHI, RUNE, INJ, TIA, SEI, CAKE, TON  
**Batch 4** (10 assets, 30 min): PEPE, ILV, GALA, SAND, MANA, ENJ, FLOKI, WIF, RONIN, AXS  
**Batch 5** (10 assets, 30 min): FIL, GRT, THETA, VET, RENDER, EGLD, KAVA, CFX, ROSE, STRK

**Critères:** WFE > 0.5, Sharpe OOS > 0.8, Trades > 50 (screening souples, workers=10)

### Phase 2: Validation (15-20 assets, ~30h)
Pour chaque SUCCESS de Phase 1:
- Run 1 + Run 2 avec `workers=1` (300 trials)
- Vérifier reproducibilité 100%
- Guards 7/7 PASS (workers=10)
- → **PROD**

### Target Final
**Objectif:** 20+ assets PROD validés avec système reproductible  
**Timeline:** Phase 1 = 3h, Phase 2 = 1-2 semaines  
**Status:** Système reproductible vérifié ✅, prêt pour re-screening déterministe
