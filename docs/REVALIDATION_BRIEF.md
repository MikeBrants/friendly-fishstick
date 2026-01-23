# BRIEF COMPLET : Re-validation Pipeline Multi-Asset

**Date:** 2026-01-24
**Status:** READY FOR EXECUTION
**Author:** @Casey (Quant Orchestrator)

---

## 🚨 Contexte : Pourquoi Re-valider

### Problème Identifié
Optuna TPESampler avec `workers > 1` est **non-déterministe par conception**. Les 15 assets PROD actuels ont été optimisés avec un sampler potentiellement mal configuré.

### Impact
- Résultats Phase 1/2 précédents = **potentiellement non-reproductibles**
- Params "optimaux" = possiblement dus à variance aléatoire
- Guards valides mais params source incertains

---

## ✅ État des Fixes (Déjà Appliqués)

### 1. Optuna TPESampler — CORRIGÉ ✅

**Fichier:** `crypto_backtest/optimization/parallel_optimizer.py`

| Paramètre | AVANT (❌) | APRÈS (✅) | Lignes |
|-----------|-----------|-----------|--------|
| `seed` | `42` fixe | `42 + hash(asset)` | 610-620 |
| `multivariate` | `False` | `True` | 89 |
| `constant_liar` | `False` | `True` | 90 |

**Code vérifié:**
```python
def create_sampler(seed: int = None) -> optuna.samplers.TPESampler:
    return optuna.samplers.TPESampler(
        seed=seed,
        multivariate=True,      # ✅ Capture tp1 < tp2 < tp3
        constant_liar=True,     # ✅ Safe parallel workers
        n_startup_trials=10,
    )
```

### 2. Guards — VÉRIFIÉS ✅

**Fichier:** `scripts/run_guards_multiasset.py`

| Paramètre | Valeur Actuelle | Minimum Requis | Status |
|-----------|-----------------|----------------|--------|
| `mc-iterations` | **1000** (ligne 770) | 1000 | ✅ OK |
| `bootstrap-samples` | **10000** (ligne 771) | 2000 | ✅ EXCELLENT |
| `confidence_level` | 0.95 (implicite) | 0.95 | ✅ OK |

**Verdict:** Guards correctement configurés, pas de modification nécessaire.

---

## 📊 État des Données

### Fichiers Parquet
**Status:** ⚠️ **DONNÉES MANQUANTES**

Actuellement dans `data/`:
- `BYBIT_BTCUSDT-60.csv` (uniquement)

**Action requise:** Télécharger toutes les données AVANT re-validation.

```bash
# Phase 0: Télécharger les données
python scripts/download_data.py \
  --assets BTC ETH JOE OSMO MINA AVAX AR ANKR DOGE OP DOT NEAR SHIB METIS YGG \
           PEPE ILV ONE \
           GALA SAND MANA ENJ FLOKI WIF RONIN PIXEL FIL THETA CHZ CRV SUSHI KAVA ZIL CFX ROSE
```

---

## 📋 Matrice Complète : Quoi Refaire

### PHASE 0 : Download

| Élément | À refaire ? | Raison |
|---------|-------------|--------|
| Data Parquet | ✅ **OUI** | Données manquantes |

**Commande:**
```bash
python scripts/download_data.py --assets [ALL_ASSETS]
```

---

### PHASE 1 : Screening

| Élément | À refaire ? | Settings | Workers |
|---------|-------------|----------|---------|
| Optuna ATR | ✅ **OUI** | Sampler corrigé | 10 |
| Optuna Ichimoku | ✅ **OUI** | Sampler corrigé | 10 |
| Guards | ❌ Non | OFF en Phase 1 | - |

**Commande:**
```bash
python scripts/run_full_pipeline.py \
  --assets BTC ETH JOE OSMO MINA AVAX AR ANKR DOGE OP DOT NEAR SHIB METIS YGG \
  --trials-atr 200 \
  --trials-ichi 200 \
  --workers 10 \
  --enforce-tp-progression \
  --output-prefix screening_REVALIDATION_v1
```

**Temps estimé:** ~30-45 min pour 15 assets

---

### PHASE 2 : Validation

| Élément | À refaire ? | Settings | Workers | Raison |
|---------|-------------|----------|---------|--------|
| Optuna ATR | ✅ **OUI** | 300 trials | **1** | Reproductibilité |
| Optuna Ichimoku | ✅ **OUI** | 300 trials | **1** | Reproductibilité |
| Guard 1: WFE | ✅ **OUI** | Seuil >0.6 | 10 | Recalcul |
| Guard 2: MC p-value | ✅ **OUI** | 1000 perms, p<0.05 | 10 | Recalcul |
| Guard 3: Sensitivity | ✅ **OUI** | ±2 radius, <10% | 10 | Recalcul |
| Guard 4: Bootstrap CI | ✅ **OUI** | 10000 samples | 10 | Recalcul |
| Guard 5: Top10 | ✅ **OUI** | <40% | 10 | Recalcul |
| Guard 6: Stress Sharpe | ✅ **OUI** | >1.0 | 10 | Recalcul |
| Guard 7: Regime | ✅ **OUI** | <1% mismatch | 10 | Recalcul |

**Commande — Run 1:**
```bash
python scripts/run_full_pipeline.py \
  --assets BTC ETH JOE OSMO MINA AVAX AR ANKR DOGE OP DOT NEAR SHIB METIS YGG \
  --trials-atr 300 \
  --trials-ichi 300 \
  --workers 1 \
  --run-guards \
  --enforce-tp-progression \
  --skip-download \
  --output-prefix validation_REVALIDATION_run1
```

**Commande — Run 2 (Reproductibilité):**
```bash
python scripts/run_full_pipeline.py \
  --assets BTC ETH JOE OSMO MINA AVAX AR ANKR DOGE OP DOT NEAR SHIB METIS YGG \
  --trials-atr 300 \
  --trials-ichi 300 \
  --workers 1 \
  --run-guards \
  --enforce-tp-progression \
  --skip-download \
  --output-prefix validation_REVALIDATION_run2
```

**Vérification Reproductibilité:**
```bash
python scripts/verify_reproducibility.py \
  --run1 outputs/multiasset_scan_*_run1.csv \
  --run2 outputs/multiasset_scan_*_run2.csv

# Attendu: 100% match
```

**Temps estimé:** 15 assets × 2-3h = **30-45 heures** (×2 pour reproductibilité)

---

### PHASE 3A : Rescue (PENDING)

| Élément | À refaire ? | Settings | Workers |
|---------|-------------|----------|---------|
| Optuna (d26/d52/d78) | ✅ **OUI** | 300 trials | **1** |
| Guards (7) | ✅ **OUI** | Params corrects | 10 |

**Assets concernés:** PENDING après Phase 2

**Commande:**
```bash
for DISP in 26 52 78; do
  python scripts/run_full_pipeline.py \
    --assets [PENDING_ASSETS] \
    --fixed-displacement $DISP \
    --trials-atr 300 \
    --trials-ichi 300 \
    --workers 1 \
    --run-guards \
    --enforce-tp-progression \
    --skip-download \
    --output-prefix rescue_d${DISP}_REVALIDATION
done
```

---

### PHASE 3B : Optimization (WINNERS)

| Élément | À refaire ? | Settings | Workers |
|---------|-------------|----------|---------|
| Optuna (d26/d52/d78) | ✅ **OUI** | 300 trials | **1** |
| Guards (7) | ✅ **OUI** | Params corrects | 10 |

**Assets concernés:** WINNERS après Phase 2

**Commande:**
```bash
python scripts/run_phase3b_optimization.py \
  --assets [WINNERS] \
  --workers 1 \
  --trials-atr 300 \
  --trials-ichi 300
```

---

### PHASE 4 : Filter Grid (PENDING restants)

| Élément | À refaire ? | Settings | Workers |
|---------|-------------|----------|---------|
| Optuna (12 modes) | ✅ **OUI** | 300 trials | **1** |
| Guards (7) | ✅ **OUI** | Params corrects | 10 |

**Assets concernés:** PENDING après Phase 3A

---

### PHASE 5 : Production

| Élément | À refaire ? |
|---------|-------------|
| `asset_config.py` | ✅ **OUI** — après validation complète |
| `project-state.md` | ✅ **OUI** — mettre à jour statuts |

---

## 📊 Tableau Récapitulatif Workers

| Phase | Optuna Workers | Guards Workers | Reproductible |
|-------|----------------|----------------|---------------|
| **1 Screening** | 10 + `constant_liar` | - | ~90% |
| **2 Validation** | **1** | 10 | ✅ 100% |
| **3A Rescue** | **1** | 10 | ✅ 100% |
| **3B Optimization** | **1** | 10 | ✅ 100% |
| **4 Filter Grid** | **1** | 10 | ✅ 100% |

---

## ⏱️ Planning Estimé

| Étape | Durée | Overnight |
|-------|-------|-----------|
| Phase 0 Download | 10-15 min | ❌ |
| Phase 1 Screening (15 assets) | 30-45 min | ✅ |
| Phase 2 Run 1 (15 assets) | 30-45h | ✅ |
| Phase 2 Run 2 (reproductibilité) | 30-45h | ✅ |
| Phase 3A/3B (si PENDING) | 2-4h | ✅ |
| **TOTAL** | **60-90h** | - |

**Note:** Phase 2 avec workers=1 est LENTE mais NÉCESSAIRE pour reproductibilité scientifique.

---

## ✅ Checklist Pré-Run

```markdown
[ ] Fix TPESampler vérifié (multivariate, constant_liar, seed unique) ✅
[ ] Fix Guards vérifié (mc=1000, bootstrap=10000) ✅
[ ] Data Parquet téléchargées
[ ] Commit état actuel
[ ] Lancer Phase 1 screening (workers=10)
[ ] Extraire WINNERS
[ ] Lancer Phase 2 validation Run 1 (workers=1)
[ ] Lancer Phase 2 validation Run 2 (workers=1)
[ ] Vérifier reproductibilité (100% match)
[ ] Si OK → Phase 3A/3B
[ ] Mettre à jour asset_config.py
[ ] Mettre à jour project-state.md
```

---

## 🚫 Ce qui NE change PAS

| Élément | Raison |
|---------|--------|
| Seuils Guards (WFE>0.6, p<0.05, etc.) | Déjà corrects |
| Logique backtest | Inchangée |
| Contrainte TP1<TP2<TP3 | Inchangée |
| Engine vectorisé | Inchangé |

---

## 🎯 Décision: Option C (Recommandée)

**FREEZE & MOVE FORWARD**

1. ✅ **Freeze les 15 assets PROD actuels** comme références historiques
2. ✅ **Appliquer fix pour nouveaux assets uniquement** (PEPE, ILV, ONE)
3. ✅ **Monitor performance live** — re-optimiser si dégradation

**Raisons:**
- ⏱️ Économise 60-90h de compute
- 📊 Assets PROD déjà robustes (7/7 guards PASS)
- 🎯 Focus sur expansion (objectif 20+ assets)

**Alternative:** Si rigueur scientifique absolue requise → Full Re-validation (60-90h)

---

## 📁 Fichiers de Référence

| Fichier | Description |
|---------|-------------|
| `docs/WORKFLOW_MULTI_ASSET_SCREEN_VALIDATE_PROD.md` | Workflow 6 phases |
| `REPRODUCIBILITY_STRATEGY.md` | Fondation scientifique Option B |
| `comms/PHASE1_PHASE2_INSTRUCTIONS.md` | Instructions détaillées |
| `status/project-state.md` | Source de vérité |
| `crypto_backtest/config/asset_config.py` | Config production |

---

**Verdict Final:** 
- Fixes code = ✅ DÉJÀ APPLIQUÉS
- Guards = ✅ BIEN CONFIGURÉS (mc=1000, bootstrap=10000)
- Données = ⚠️ À TÉLÉCHARGER
- Re-validation complète = OPTIONNELLE (60-90h) vs FREEZE (0h)
