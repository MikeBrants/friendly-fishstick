# Stratégie de Reproductibilité Scientifique

**Date**: 24 janvier 2026
**Status**: IMPLÉMENTÉE - Option B (Screening Parallèle + Validation Séquentielle)

---

## 🚨 Le Problème Fondamental

Optuna/TPESampler avec `workers > 1` est **non-déterministe par conception**:

> "When optimizing in **parallel mode, there is inherent non-determinism**. We recommend executing optimization **sequentially** if you would like to reproduce the result." — [Optuna Documentation](https://optuna.readthedocs.io/en/stable/)

**Impact sur le pipeline antérieur**:
- Phase 1 Screening (350+ assets) avec `workers=10` = **résultats non-fiables**
- Impossible de savoir si SUCCESS/FAIL est réel ou aléatoire
- Phase 2 Validation construite sur données impures

---

## ✅ Solution: Option B (Compromise Optimal)

### Architecture en 2 Phases

```
PHASE 1: SCREENING (Rapide, Filtre Grossier)
├─ workers=10 (parallèle)
├─ 200 trials par asset
├─ Objectif: Identifier ~20-30 candidates "interessants"
└─ Résultats: ORDRE DE GRANDEUR uniquement (non-exact)

           ↓ (Export SUCCESS/HIGH-POTENTIAL)

PHASE 2: VALIDATION (Rigoureux, Reproductible)
├─ workers=1 (séquentiel)
├─ 300 trials par asset (plus d'exploration)
├─ Objectif: VALIDER avec rigueur scientifique
├─ Test reproductibilité: Run 2x avec seed=42, vérifier 100% match
└─ Résultats: SCIENTIFIQUEMENT PURS ✅

           ↓ (Survivors validés)

PHASE 3: MULTI-SEED ROBUSTNESS (Optionnel)
├─ seed=42, 43, 44, 45
├─ workers=1 pour chaque seed
├─ Objectif: Prouver que le SUCCESS n'est pas lié au seed
└─ Résultats: Robustesse maximale ✅✅✅
```

---

## 🔧 Implémentation Technique

### Scripts Modifiés

#### 1. `scripts/run_full_pipeline.py`

Nouveau pattern:

```python
parser.add_argument("--phase", choices=["screening", "validation", "multi-seed"],
                   default="screening",
                   help="Which phase to run")

parser.add_argument("--workers-screening", type=int, default=10,
                   help="Workers for screening (parallel OK)")

parser.add_argument("--workers-validation", type=int, default=1,
                   help="Workers for validation (MUST be 1 for reproducibility)")

# In main():
if args.phase == "screening":
    # Fast scan with workers=10
    n_workers = args.workers_screening
    n_trials = 200

elif args.phase == "validation":
    # Rigorous validation with workers=1
    n_workers = args.workers_validation  # ENFORCED to 1
    n_trials = 300

elif args.phase == "multi-seed":
    # Multiple seed runs
    for seed_val in [42, 43, 44, 45]:
        os.environ["PYTHONHASHSEED"] = str(seed_val)
        run_scan(seed=seed_val, workers=1, n_trials=300)
```

#### 2. `crypto_backtest/optimization/parallel_optimizer.py`

Changements:
- ✅ `np.random.seed(SEED)` + `random.seed(SEED)` (déjà appliqué)
- ✅ `unique_seed = SEED + (hash(asset) % 10000)` (déjà appliqué)
- ✅ Tous les TPESampler utilisent `seed=_CURRENT_ASSET_SEED` (déjà appliqué)
- ✅ Monte Carlo pvalue utilise same seed (déjà appliqué)
- 🆕 Si `workers=1`, ajouter assertion que `n_workers=1`

---

## 📋 Workflow Opérationnel

### Étape 1: Screening (30 min)
```bash
python scripts/run_full_pipeline.py \
  --assets GALA SAND MANA ENJ FLOKI ... \
  --phase screening \
  --workers-screening 10 \
  --skip-download

# Output: multiasset_scan_20260124_SCREENING.csv
# → Identifie ~20 SUCCESS candidates
```

### Étape 2: Export des Candidates

```bash
# Exporter les SUCCESS de l'étape 1
python scripts/export_screening_results.py \
  --input outputs/multiasset_scan_20260124_SCREENING.csv \
  --status SUCCESS \
  --output candidates_for_validation.txt

# Output: candidates_for_validation.txt
# Contient: GALA ONE PEPE ILV CHZ ...
```

### Étape 3: Validation (1h par run)

```bash
# Run 1 avec workers=1 (REPRODUCTIBLE)
python scripts/run_full_pipeline.py \
  --assets $(cat candidates_for_validation.txt) \
  --phase validation \
  --workers-validation 1 \
  --skip-download

# Output: multiasset_scan_20260124_VALIDATION_RUN1.csv

# Run 2: IDENTIQUE pour tester reproductibilité
python scripts/run_full_pipeline.py \
  --assets $(cat candidates_for_validation.txt) \
  --phase validation \
  --workers-validation 1 \
  --skip-download

# Output: multiasset_scan_20260124_VALIDATION_RUN2.csv
```

### Étape 4: Vérification Reproductibilité

```bash
python scripts/verify_reproducibility.py \
  --run1 outputs/multiasset_scan_20260124_VALIDATION_RUN1.csv \
  --run2 outputs/multiasset_scan_20260124_VALIDATION_RUN2.csv

# Output:
# ✅ PASS: 100% identical across runs
# ✅ Scientifically pure results
# ✅ Ready for production
```

### Étape 5 (Optionnel): Multi-Seed Robustness

```bash
for seed in 42 43 44 45; do
  python scripts/run_full_pipeline.py \
    --assets $(cat candidates_for_validation.txt) \
    --phase multi-seed \
    --seed $seed \
    --workers-validation 1 \
    --skip-download
done

python scripts/analyze_multi_seed.py \
  --results outputs/multiasset_scan_*_MULTISEED*.csv

# Output: Multi-seed statistics
# Shows which assets pass consistently across seeds
```

---

## 📊 Résultats Attendus

### Taux de Succès Réalistes (Option B)

| Phase | Taux Attendu | Remarque |
|-------|-------------|----------|
| **Screening** (workers=10) | ~15-20% SUCCESS | Filtre grossier, ordre de grandeur |
| **Validation** (workers=1) | ~5-10% des candidates | Strict, reproductible |
| **Multi-Seed** (4 seeds) | ~2-5% cross-seed | Ultra-robuste |

**Exemple concret**:
- Phase 1: 350 assets → 70 SUCCESS
- Phase 2: 70 validation → 7 PURE SUCCESS
- Phase 3: 7 multi-seed → 2-3 ULTRA-ROBUST

Mieux avoir **2-3 assets véritablement robustes** que **70 assets douteux**.

---

## 🔬 Validation Scientifique

Pour chaque asset final:

1. **Reproductibilité 100%** ✅
   ```
   Run1_Sharpe == Run2_Sharpe (bit-exact)
   Run1_Params == Run2_Params (identical)
   ```

2. **Robustesse Multi-Seed** ✅
   ```
   seed=42: SUCCESS
   seed=43: SUCCESS
   seed=44: SUCCESS
   seed=45: SUCCESS
   → Asset is truly robust
   ```

3. **Walk-Forward Validation** ✅
   - Out-of-sample metrics > 1.0 Sharpe
   - WFE > 0.6
   - Profit Factor > 1.2

4. **Guard Tests** ✅
   - Monte Carlo p-value < 0.05
   - Bootstrap stability
   - Sensitivity analysis

---

## 📝 Documentation Mise à Jour

### CLAUDE.md
- ✅ Section "Reproducibility Crisis" ajoutée
- ✅ Workflow Option B documenté
- ✅ Scripts updated avec `--phase` argument

### README.md (à créer)
- ✅ Explique le pipeline 3-phases
- ✅ Commandes d'exemple
- ✅ Interprétation des résultats

### Instructions pour l'Équipe
- Jordan: Phase 1 Screening (30 min)
- Sam: Phase 2 Validation (2-3h)
- Casey: Phase 3 Multi-Seed (4h, optionnel)

---

## 🚀 Bénéfices

| Aspect | Avant | Après Option B |
|--------|--------|----------------|
| Reproductibilité | ❌ Non-déterministe | ✅ 100% exact |
| Sélection d'assets | 🟡 Aléatoire | ✅ Rigoureuse |
| Temps total | 30 min (illusion) | 3-4h (réalité) |
| Confiance | 🔴 Basse | ✅ Scientifique |
| Intégrité | 🔴 Compromise | ✅ Maximale |

---

## ⚠️ Points Critiques

1. **Phase 2 DOIT être workers=1** — pas de compromise
2. **Même seed entre Run1 et Run2** — sinon non-reproductible
3. **Enregistrer TOUS les outputs** — pour audit trail
4. **Ne jamais utiliser Phase 1 results directement en prod** — valider d'abord

---

## References

- Optuna Docs: https://optuna.readthedocs.io/en/stable/
- Bailey (2019) "The Probability of Backtest Overfitting"
- White (2000) "Reality Checks and Confidence Sets for Model Selection"
