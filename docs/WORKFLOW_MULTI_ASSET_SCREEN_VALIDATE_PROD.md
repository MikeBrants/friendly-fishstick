# Pipeline Multi-Asset — 6 Phases (Screen → Validate → Prod)

**Derniere mise a jour:** 2026-01-25 15:45 UTC  
**Status**: 🟢 RESET COMPLETE — 14 Assets PROD  
**Version**: v2.2 (filter system v2, deterministic validation)

**⚠️ BREAKING CHANGE**: Parallel screening (workers > 1) is non-deterministic by Optuna design. Phase 2 MUST use workers=1 for scientific validity.

Ce document decrit le workflow **scalable** pour executer le pipeline FINAL TRIGGER v2 sur des dizaines d'assets, en minimisant le compute gaspille et en maximisant la robustesse des assets qui passent en production.

**SEE ALSO**: 
- [REPRODUCIBILITY_STRATEGY.md](../REPRODUCIBILITY_STRATEGY.md) — Scientific foundation for Option B workflow
- [REVALIDATION_BRIEF.md](./REVALIDATION_BRIEF.md) — Complete re-validation brief with commands
- [../status/project-state.md](../status/project-state.md) — **CURRENT PROJECT STATUS** (single source of truth)
- [../comms/TESTING_COORDINATION.md](../comms/TESTING_COORDINATION.md) — Agent coordination protocol

**RECENT UPDATES (2026-01-25):**
- ✅ **RESET COMPLETE**: 6 assets re-validés avec workers=1 (ETH, AVAX, MINA, YGG, RUNE, EGLD)
- ✅ **14 Assets PROD**: Portefeuille validé avec système déterministe
- ✅ **Filter System v2**: 3 modes (baseline/moderate/conservative), modes obsolètes supprimés
- ✅ **AVAX Rescue**: baseline FAIL → moderate PASS (WFE 0.66)
- 🔴 **3 Assets PENDING RESCUE**: OSMO, AR, METIS (Phase 3A required)
- ❌ **OP EXCLU**: Sharpe 0.03, WFE 0.01 — rescue impossible

**GUARDS CONFIG:**
- Monte Carlo iterations: **1000** (minimum standard)
- Bootstrap samples: **10000** (5x minimum, excellent)
- Confidence level: **0.95**
- Sensitivity threshold: **15%** (PR#8)
- **Overfitting metrics**: PSR/DSR (report-only)

---

## 🎯 CURRENT STATUS (25 Jan 2026, 16:00 UTC)

### Assets PROD (14 validés)

| # | Asset | Sharpe | WFE | Mode | Validation |
|---|-------|--------|-----|------|------------|
| 1 | SHIB | 5.67 | 2.27 | baseline | Pre-reset |
| 2 | TIA | 5.16 | 1.36 | baseline | PR#8 |
| 3 | DOT | 4.82 | 1.74 | baseline | Pre-reset |
| 4 | NEAR | 4.26 | 1.69 | baseline | Pre-reset |
| 5 | DOGE | 3.88 | 1.55 | baseline | Pre-reset |
| 6 | ANKR | 3.48 | 0.86 | baseline | Pre-reset |
| 7 | ETH | 3.22 | 1.22 | baseline | **25 Jan** |
| 8 | JOE | 3.16 | 0.73 | baseline | Pre-reset |
| 9 | YGG | 3.11 | 0.78 | baseline | **25 Jan** |
| 10 | MINA | 2.58 | 1.13 | baseline | **25 Jan** |
| 11 | CAKE | 2.46 | 0.81 | baseline | PR#8 |
| 12 | RUNE | 2.42 | 0.61 | baseline | **25 Jan** |
| 13 | EGLD | 2.13 | 0.69 | baseline | **25 Jan** |
| 14 | AVAX | 2.00 | 0.66 | **moderate** | **25 Jan rescue** |

### Assets Pending Rescue (Phase 3A)

| Asset | Sharpe | WFE | Reason | Action |
|-------|--------|-----|--------|--------|
| OSMO | 0.68 | 0.19 | Severe overfit | Try d26/d78 |
| AR | 1.64 | 0.39 | WFE + low trades | Try d26/d78 |
| METIS | 1.59 | 0.48 | WFE fail | Try d26/d78 |

### Assets Exclus

- **OP**: Sharpe 0.03, WFE 0.01 — severe fail, EXCLU définitif

**Status Files**:
- [../status/project-state.md](../status/project-state.md) — **SOURCE DE VÉRITÉ**
- [../crypto_backtest/config/asset_config.py](../crypto_backtest/config/asset_config.py) — Params PROD

---

## Pipeline Actuel (7 Phases)

| Phase | Nom | Input | Output | Status |
|-------|-----|-------|--------|--------|
| 0 | Download | - | `data/*.parquet` | ✅ READY |
| 1 | Screening | Candidats | `outputs/multiasset_scan_*.csv` | 🔄 Batch 1 en cours |
| 2 | Validation | Screening winners | WINNERS + PENDING | ✅ 14 PROD |
| 3A | Rescue (PENDING) | PENDING | `displacement_rescue_*.csv` | 🔴 3 assets pending |
| 3B | Optimization (WINNERS) | WINNERS | `displacement_optimization_*.csv` | ✅ READY |
| 4 | Filter Rescue | PENDING restants | `filter_rescue_*.csv` | ✅ v2 (3 modes) |
| 5 | Production | Tous valides | `asset_config.py` | ✅ 14 assets |
| 6 | Portfolio Construction | 5+ assets PROD | `portfolio_weights_*.csv` | ✅ READY |

**Pipeline v2.2**: Filter System v2 (3 modes), reproducibilité workers=1, overfitting metrics (PSR/DSR)

---

## Diagramme de Flux

```
Phase 0: Download
    |
Phase 1: Screening (200 trials, workers=10, guards OFF)
    |
    +---> FAIL --> Stop ou Phase 3A (si asset important)
    |
Phase 2: Validation (300 trials, workers=1, --run-guards, --overfit-trials 150)
    |
    +---> WINNERS (7/7 + PSR/DSR OK) --> Phase 3B (optional) --> Phase 5
    |
    +---> PENDING (<7/7) --> Phase 3A
                               |
                               +---> PASS --> Phase 5
                               |
                               +---> FAIL --> Phase 4
                                              |
                                              +---> PASS --> Phase 5
                                              |
                                              +---> FAIL --> EXCLU

Phase 5: Production Config (asset_config.py updated)
    |
    v
Phase 6: Portfolio Construction (5+ assets PROD)
    |
    +---> Equal weights (baseline)
    +---> Max Sharpe (performance)
    +---> Risk Parity (risk-balanced)
    +---> Min CVaR (downside protection)
```

**NEW (v2.1)**: Phase 2 now includes overfitting diagnostics (PSR/DSR), Phase 6 enables portfolio optimization

---

## Phase 0 : Download

**Objectif** : Telecharger OHLCV 1H pour tous les assets depuis Binance.

- Stocke en Parquet dans `data/`
- Evite les re-telechargements si fichier existe
- Verifie que chaque asset a assez d'historique (min 8000 barres)

**Commande :**

```bash
python scripts/download_data.py --assets [ASSET_LIST]
```

**Outputs :** `data/Binance_*_1h.parquet`

---

## Phase 1 : Screening (rapide, filtering grossier)

**Objectif** : Eliminer rapidement les assets non-viables. **IMPORTANT**: Results are approximate only due to parallel non-determinism.

### Parametres

| Parametre | Valeur | Justification |
|-----------|--------|---------------|
| Trials | 200 | Balance speed vs exploration |
| Workers | **10** | Fast filtering, non-exact OK |
| Guards | OFF | Guards trop coûteux à cette phase |
| TP progression | ON | Enforce realistic SL/TP ratios |

### Criteres PASS (souples, ordre de grandeur)

| Metrique | Seuil |
|----------|-------|
| WFE | > 0.4 (approximate) |
| Sharpe OOS | > 0.5 (approximate) |
| Trades OOS | > 30 |

**⚠️ These thresholds are SOFT — parallel execution introduces variance. Use to identify ~20-30 candidates for Phase 2.**

### Commande

```bash
# Phase 1: SCREENING with parallel workers (fast)
# NOTE: --phase and --workers-screening don't exist, use --workers instead
python scripts/run_full_pipeline.py \
  --assets BNB ADA DOGE TRX DOT ... \
  --trials-atr 200 \
  --trials-ichi 200 \
  --enforce-tp-progression \
  --workers 10 \
  --skip-guards \
  --skip-download \
  --output-prefix screening_batch1
```

**Output :** `outputs/multiasset_scan_*.csv`

**Next Step:** Extract SUCCESS/HIGH-POTENTIAL assets for Phase 2 validation

```bash
# Export candidates for strict validation
python scripts/export_screening_results.py \
  --input outputs/multiasset_scan_*.csv \
  --status SUCCESS \
  --output candidates_for_validation.txt
```

---

## Phase 2 : Validation (Rigoureuse & Reproductible)

**Objectif** : Valider scientifiquement les candidates de Phase 1 avec reproducibilité 100%.

**🚨 CRITICAL**: Phase 2 MUST use `workers=1` for reproducibility. Parallel execution causes non-deterministic results.

### Parametres

| Parametre | Valeur | Justification |
|-----------|--------|---------------|
| Trials | 300 | More exploration for accuracy |
| Workers | **1** (ENFORCED) | Optuna reproducibility requirement |
| Guards | ON (`--run-guards`) | Robustness validation |
| TP progression | ON | Enforce realistic ratios |
| Reproducibility Test | 2x run | Verify bit-exact match |

### Criteres PASS (stricts) — 7 Guards Obligatoires

| Guard | Seuil | Critique |
|-------|-------|----------|
| WFE | > 0.6 | OUI |
| MC p-value | < 0.05 | OUI |
| Sensitivity var | < 15% | OUI |
| Bootstrap CI lower | > 1.0 | OUI |
| Top10 trades | < 40% | OUI |
| Stress1 Sharpe | > 1.0 | OUI |
| Regime mismatch | < 1% | OUI |

**Seuils additionnels :**
- OOS Sharpe > 1.0 (target > 2.0)
- OOS Trades > 60
- **Reproducible across 2 identical runs**

**NEW — Overfitting Metrics (Alex's DSR Implementation):**

Le **Deflated Sharpe Ratio (DSR)** corrige le "trial count paradox" identifié par Alex:
- Plus de trials = plus de chances de trouver un Sharpe élevé par hasard
- DSR calcule la probabilité que le Sharpe soit statistiquement significatif

| Métrique | Description | Seuil | Status |
|----------|-------------|-------|--------|
| **PSR** | P(SR > 0) | > 0.85 | Report-only |
| **DSR** | Sharpe after n_trials correction | > 0.70 | Report-only |
| **SR*** | Threshold Sharpe (by chance) | - | Computed |

**Fichier**: `crypto_backtest/validation/deflated_sharpe.py`

**Usage**:
```python
from crypto_backtest.validation.deflated_sharpe import deflated_sharpe_ratio
dsr, sr0 = deflated_sharpe_ratio(returns, sharpe_observed=2.14, n_trials=300)
print(f"DSR: {dsr:.1%}, Threshold: {sr0:.2f}")
```

**Interprétation**:
- DSR > 95%: **STRONG** — Edge statistiquement significatif
- DSR 85-95%: **MARGINAL** — Acceptable si autres guards OK
- DSR < 85%: **SUSPECT** — Probablement overfitting

**Status**: Report-only (ne bloque PAS la validation, mais flag pour review)

### Commande — Validation

```bash
# Phase 2: VALIDATION with sequential workers (reproducible)
# CRITICAL: workers=1 is REQUIRED for reproducibility
python scripts/run_full_pipeline.py \
  --assets ETH AVAX MINA YGG \
  --trials-atr 300 \
  --trials-ichi 300 \
  --enforce-tp-progression \
  --run-guards \
  --workers 1 \
  --skip-download \
  --output-prefix validated_batch1
```

**IMPORTANT**: 
- `--workers 1` is MANDATORY for Phase 2 (Optuna reproducibility)
- `--phase` and `--workers-validation` arguments DO NOT EXIST
- Use `--workers` instead (applies to optimization parallelism)

### Reproducibility Verification

```bash
# Verify Run 1 and Run 2 are 100% identical
python scripts/verify_reproducibility.py \
  --run1 outputs/multiasset_scan_*_run1.csv \
  --run2 outputs/multiasset_scan_*_run2.csv

# Expected output:
# ✅ PASS: 100% identical across runs
# All metrics match bit-for-bit
```

### Resultats

- **WINNERS** (7/7 PASS + Reproducible) → Phase 3B (optionnel) → Phase 5
- **PENDING** (<7/7 PASS) → Phase 3A
- **INVALID** (Fails reproducibility) → Investigate source of randomness

**Output :** `outputs/{ASSET}_validation_report_*.txt`

---

## Phase 3A : Rescue — Displacement Grid (PENDING only)

**Objectif** : Sauver les assets qui echouent avec d52 en testant d'autres displacements.

### Principe

Teste d26, d52, d78 sur chaque PENDING. Si un displacement passe 7/7 → passe en WINNERS.

### Displacement Variants

| Displacement | Type d'asset | Exemples |
|--------------|--------------|----------|
| d26 | Meme/fast | DOGE, SHIB, JOE |
| d52 | Standard | BTC, ETH, majeurs |
| d78 | L2/slow | OP, ARB |

### Commande

```bash
python scripts/run_full_pipeline.py \
  --assets [PENDING_ASSET] \
  --fixed-displacement 26 \
  --trials-atr 300 \
  --trials-ichi 300 \
  --enforce-tp-progression \
  --run-guards \
  --overfit-trials 150 \
  --workers 1
```

**Note (v2.1)**: Use `workers=1` for reproducibility. Add `--overfit-trials 150` for PSR/DSR metrics.

Repeter pour d52, d78.

**Output :** `outputs/displacement_rescue_*.csv`

---

## Phase 3B : Optimization — Displacement Grid (WINNERS only)

**Objectif** : Ameliorer les winners avec un displacement alternatif.

### Principe

- Teste d26, d52, d78 sur chaque winner
- Compare Sharpe OOS et WFE vs baseline d52
- **Garde le meilleur** si amelioration > 10% ET toujours 7/7 PASS

### Critere de remplacement

```python
if new_sharpe > old_sharpe * 1.10 and all_guards_pass:
    use_new_displacement = True
```

### Commande

**Script dédié (recommandé) :**

```bash
python scripts/run_phase3b_optimization.py \
  --workers 1 \
  --trials-atr 300 \
  --trials-ichi 300 \
  --overfit-trials 150
```

**Note (v2.1)**: Changed to `workers=1` for reproducibility, added overfitting metrics.

**Pour des assets spécifiques :**

```bash
python scripts/run_phase3b_optimization.py \
  --assets BTC ETH \
  --workers 1 \
  --trials-atr 300 \
  --trials-ichi 300 \
  --overfit-trials 150
```

**Outputs :**
- `outputs/displacement_optimization_*.csv` — Résultats détaillés par asset/displacement
- `outputs/displacement_optimization_summary_*.csv` — Résumé avec recommandations (KEEP/UPDATE)

**Note :** Le script teste automatiquement tous les displacements (26, 52, 78) pour chaque asset PROD et compare avec le baseline actuel. Il recommande une mise à jour si amélioration > 10% ET 7/7 guards PASS.

---

## Phase 4 : Filter Rescue (PENDING restants)

**Objectif** : Sauver les assets qui echouent guard002 (sensitivity > 15%) via cascade de filtres.

**⚠️ REFONTE 2026-01-24**: Ancien grid de 12 combinaisons remplacé par cascade de 3 modes rationnels.

### Principe

Cascade simplifiée: `baseline` → `moderate` → `conservative`
- Évite le data mining des 12 combinaisons arbitraires
- Max 3 tests par asset (correction Bonferroni ÷3 au lieu de ÷12)
- Arrêt dès le premier PASS

### Workflow Décisionnel

```
Asset FAIL baseline (sensitivity > 15%)
    │
    └─→ moderate (5 filtres)
         │
         ├─ PASS → PROD ✓
         └─ FAIL → conservative (7 filtres)
                   │
                   ├─ PASS → PROD ✓
                   └─ FAIL → EXCLU ✗
```

### Filter Modes (3 modes rationnels)

| Mode | Filtres | Sensitivity | Trades OOS | WFE |
|------|---------|-------------|------------|-----|
| baseline | ichimoku only | <15% | ≥60 | ≥0.6 |
| moderate | 5 filtres (distance, volume, regression, kama, ichimoku) | <15% | ≥50 | ≥0.6 |
| conservative | 7 filtres (all + strict ichimoku) | <15% | ≥40 | ≥0.55 |

### Commande

```bash
# Script de rescue automatique (cascade baseline → moderate → conservative)
python scripts/run_filter_rescue.py ASSET
python scripts/run_filter_rescue.py ETH --trials 300 --workers 1

# Ou manuellement pour un mode spécifique
python scripts/run_full_pipeline.py \
  --assets [PENDING_ASSET] \
  --optimization-mode moderate \
  --trials-atr 300 \
  --trials-ichi 300 \
  --enforce-tp-progression \
  --run-guards \
  --overfit-trials 150 \
  --workers 1
```

**Note (v2.1)**: Use `workers=1` for reproducibility, added overfitting diagnostics.

### Règles Critiques

- TOUJOURS commencer par baseline
- Max 3 tests par asset (correction statistique OK)
- Si conservative FAIL → EXCLU définitif
- NE PAS chercher d'autres combinaisons (data mining)

**Output :** `outputs/filter_rescue_{ASSET}_*.csv`

---

## Phase 5 : Production Config

**Objectif** : Figer les parametres finaux pour tous les assets valides.

### Actions

1. Mettre a jour `crypto_backtest/config/asset_config.py` avec :
   - Displacement optimal
   - Filter mode
   - Parametres ATR/Ichimoku optimaux
   - TP progressifs (TP1 < TP2 < TP3)

2. Mettre a jour `status/project-state.md` :
   - Ajouter asset en PROD
   - Retirer de PENDING
   - Documenter la date de validation

3. **Ne pas toucher** `docs/HANDOFF.md` (obsolete)

---

## Phase 6 : Portfolio Construction (NEW in v2.1)

**Objectif** : Construire des portfolios optimises a partir des assets PROD valides.

**Prerequisites** : Au moins 5 assets valides en PROD (7/7 guards PASS + overfitting OK)

### Methodes d'Optimisation

| Methode | Description | Use Case |
|---------|-------------|----------|
| `equal` | Poids egaux (baseline) | Benchmark simple |
| `max_sharpe` | Maximise Sharpe ratio | Performance focus |
| `risk_parity` | Equalise contribution au risque | Risk-balanced |
| `min_cvar` | Minimise CVaR (expected shortfall) | Downside protection |

### Contraintes de Poids

- **Min weight**: 5-10% (eviter positions negligeables)
- **Max weight**: 20-30% (eviter concentration)
- **Sum**: 100% (fully invested)
- **Correlation max**: < 0.70-0.75 (diversification)

### Commande

```bash
# Construire portfolio avec methode Max Sharpe
python scripts/portfolio_construction.py \
  --input-validated outputs/multiasset_guards_summary_<timestamp>.csv \
  --method max_sharpe \
  --min-weight 0.05 \
  --max-weight 0.20 \
  --max-correlation 0.75 \
  --output-prefix production_portfolio

# Repeter pour toutes les methodes
for method in equal risk_parity min_cvar; do
  python scripts/portfolio_construction.py \
    --input-validated outputs/multiasset_guards_summary_<timestamp>.csv \
    --method $method \
    --min-weight 0.05 \
    --max-weight 0.20 \
    --output-prefix production_portfolio
done
```

### Outputs

- `outputs/production_portfolio_weights_<method>_<timestamp>.csv` — Poids optimaux par asset
- `outputs/production_portfolio_correlation_matrix_<timestamp>.csv` — Matrice de correlation
- `outputs/production_portfolio_metrics_<timestamp>.csv` — Comparaison des methodes
- `outputs/production_portfolio_high_correlation_<timestamp>.csv` — Paires correlees (si > max)

### Analyse des Resultats

**Comparer les 4 methodes** :
- Sharpe ratio (rendement ajuste du risque)
- Sortino ratio (rendement ajuste du downside)
- Max drawdown (pire perte)
- Diversification ratio (benefice de diversification)
- Max pairwise correlation (risque de concentration)

**Choisir le portfolio** :
- `max_sharpe` si objectif = performance
- `risk_parity` si objectif = balance risque
- `min_cvar` si objectif = protection downside
- `equal` comme benchmark (toujours calculer)

### Validation du Portfolio

**Verifier** :
- [ ] Tous les poids entre min/max bounds
- [ ] Sum des poids = 1.0
- [ ] Aucune paire > max correlation threshold
- [ ] Diversification ratio > 1.0 (sinon pas de benefice)
- [ ] Sharpe portfolio >= moyenne des Sharpe individuels

**Backtest du portfolio** (optionnel mais recommande) :
```bash
# Simuler le portfolio avec les poids optimaux
python scripts/backtest_portfolio.py \
  --weights outputs/production_portfolio_weights_max_sharpe_<timestamp>.csv \
  --start-date 2022-01-01 \
  --end-date 2025-12-31 \
  --rebalance-frequency monthly
```

---

---

## Travail d'Alex — DSR et Variance Reduction

### DSR (Deflated Sharpe Ratio) — IMPLÉMENTÉ ✅

**Fichier**: `crypto_backtest/validation/deflated_sharpe.py`

Le DSR corrige le **trial count paradox**:
- Plus de trials Optuna = plus de chances de trouver un Sharpe élevé par hasard
- La formule Bailey & Lopez de Prado (2014) calcule le seuil SR₀ attendu par chance

```python
from crypto_backtest.validation.deflated_sharpe import deflated_sharpe_ratio

# Calculer DSR pour un asset
dsr, sr0 = deflated_sharpe_ratio(
    returns=trade_returns,
    sharpe_observed=2.14,
    n_trials=300
)
print(f"DSR: {dsr:.1%}, SR threshold: {sr0:.2f}")
```

### Variance Reduction Research — TODO

**Objectif**: Réduire la variance (sensitivity) sous 10% pour gros assets.

**Pistes à explorer**:
1. **Regime-aware WF splits** — Stratifier les splits par régime (BULL/BEAR/SIDEWAYS)
2. **Parameter averaging** — Moyenner top N trials au lieu du best
3. **Regularization Optuna** — Ajouter pénalité variance dans objective
4. **Reduced trial count** — Tests montrent que 50 trials peut > 100 trials pour WFE

**Assets cibles**: Tout asset avec sensitivity > 10%

---

## NE PAS FAIRE

- Ne jamais utiliser `docs/HANDOFF.md` comme reference
- Ne jamais utiliser `medium_distance_volume` ou autres modes obsolètes
- Ne jamais modifier les seuils guards sans validation
- Ne jamais skip le warmup (200 barres minimum)
- Ne jamais oublier `.shift(1)` sur les rolling features (look-ahead)
- Ne jamais valider avec Sharpe > 4 ou WFE > 2 sans reconciliation (trop beau = suspect)
- Ne jamais utiliser `workers > 1` en Phase 2+ (reproductibilité obligatoire)

---

## IMPORTANT — Fichiers de Reference

### Source de Vérité

| Fichier | Description |
|---------|-------------|
| **`status/project-state.md`** | **MASTER STATUS** — État actuel du projet |
| **`crypto_backtest/config/asset_config.py`** | Params PROD pour 14 assets |
| **`.cursor/rules/MASTER_PLAN.mdc`** | Master Plan (chargé automatiquement) |

### Documentation Technique

| Fichier | Description |
|---------|-------------|
| **`docs/WORKFLOW_MULTI_ASSET_SCREEN_VALIDATE_PROD.md`** | Ce fichier (workflow reference) |
| **`CLAUDE.md`** | Architecture système + plan |
| **`crypto_backtest/validation/deflated_sharpe.py`** | DSR implementation (Alex) |

### Agent Rules (chargées automatiquement)

| Fichier | Agent | Rôle |
|---------|-------|------|
| `.cursor/rules/agents/casey-orchestrator.mdc` | Casey | Orchestration, verdicts |
| `.cursor/rules/agents/jordan-dev.mdc` | Jordan | Exécution, patterns code |
| `.cursor/rules/agents/sam-qa.mdc` | Sam | 7 guards, validation |
| `.cursor/rules/agents/alex-lead.mdc` | Alex | Architecture, DSR, variance |

### Scripts Principaux

| Script | Phase | Description |
|--------|-------|-------------|
| `scripts/run_full_pipeline.py` | 1-3 | Pipeline complet (download → optimize → guards) |
| `scripts/run_filter_rescue.py` | 4 | Filter cascade (3 modes) |
| `scripts/portfolio_construction.py` | 6 | Construction portfolio |
| `scripts/run_guards_multiasset.py` | 2-3 | Guards + overfitting report |

### OBSOLETE (Ne Pas Utiliser)

- ❌ `docs/HANDOFF.md` — Obsolete
- ❌ `medium_distance_volume` — Mode obsolète, utiliser `baseline` ou `moderate`

---

## Suivi et Tracabilite

**Source de vérité**: `status/project-state.md` et `crypto_backtest/config/asset_config.py`

### Assets PROD (14 validés, 25 Jan 2026)

| Asset | Mode | Disp | Sharpe | WFE | Trades | Date Validation |
|:------|:-----|:-----|:-------|:----|:-------|:---------------|
| SHIB | baseline | 52 | 5.67 | 2.27 | - | Pre-reset |
| TIA | baseline | 52 | 5.16 | 1.36 | 75 | PR#8 (24 Jan) |
| DOT | baseline | 52 | 4.82 | 1.74 | - | Pre-reset |
| NEAR | baseline | 52 | 4.26 | 1.69 | - | Pre-reset |
| DOGE | baseline | 26 | 3.88 | 1.55 | - | Pre-reset |
| ANKR | baseline | 52 | 3.48 | 0.86 | - | Pre-reset |
| ETH | baseline | 52 | 3.22 | 1.22 | 72 | **25 Jan reset** |
| JOE | baseline | 26 | 3.16 | 0.73 | 63 | Pre-reset |
| YGG | baseline | 52 | 3.11 | 0.78 | 78 | **25 Jan reset** |
| MINA | baseline | 52 | 2.58 | 1.13 | 60 | **25 Jan reset** |
| CAKE | baseline | 52 | 2.46 | 0.81 | 90 | PR#8 (24 Jan) |
| RUNE | baseline | 52 | 2.42 | 0.61 | 102 | **25 Jan reset** |
| EGLD | baseline | 52 | 2.13 | 0.69 | 91 | **25 Jan reset** |
| AVAX | **moderate** | 52 | 2.00 | 0.66 | 81 | **25 Jan rescue** |

### Modes de Filtres Valides (v2)

| Mode | Description | Filtres | Usage |
|------|-------------|---------|-------|
| `baseline` | Ichimoku only | 1 | Default, première optimisation |
| `moderate` | 5 filtres actifs | 5 | Si baseline FAIL WFE/sensitivity |
| `conservative` | Tous + strict | 7 | Dernier recours avant EXCLU |

### Modes OBSOLÈTES (ne plus utiliser)

- ❌ `medium_distance_volume` — Remplacé par `baseline` ou `moderate`
- ❌ `light_*` — Supprimés
- ❌ `medium_kama_*` — Supprimés

---

## Checklist

### Pre-flight

- [x] Donnees 1H telechargees pour le batch
- [x] TP progression enforcement ON (`--enforce-tp-progression`)
- [x] Verifier timestamp fichier > 2026-01-22 12:00 UTC (cutoff bug TP)
- [x] Utiliser `workers=1` pour Phase 2+ (reproductibilité)

### Phase 1 — Screening

- [x] Filter System v2 déployé (3 modes)
- [ ] Batch 1 (15 assets) en cours
- [ ] Analyser résultats et identifier candidats

### Phase 2 — Validation

- [x] 14 assets validés avec workers=1
- [x] Guards 7/7 PASS pour tous les PROD
- [x] ETH, AVAX, MINA, YGG, RUNE, EGLD re-validés (25 Jan)

### Phase 3A — Rescue (PENDING)

- [ ] OSMO: displacement rescue (d26, d78)
- [ ] AR: displacement rescue (d26, d78)
- [ ] METIS: displacement rescue (d26, d78)

### Phase 4 — Filter Rescue

- [x] AVAX: baseline FAIL → moderate PASS
- [ ] Autres assets si Phase 3A échoue

### Phase 5 — Production

- [x] `asset_config.py` à jour (14 assets)
- [x] `status/project-state.md` à jour
- [x] Modes obsolètes documentés

### Phase 6 — Portfolio

- [x] 14 assets disponibles
- [ ] Construction portfolio (4 méthodes)
