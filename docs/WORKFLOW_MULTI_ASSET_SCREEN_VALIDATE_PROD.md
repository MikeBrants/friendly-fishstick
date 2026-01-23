# Pipeline Multi-Asset — 6 Phases (Screen → Validate → Prod)

**Derniere mise a jour:** 2026-01-23

Ce document decrit le workflow **scalable** pour executer le pipeline FINAL TRIGGER v2 sur des dizaines d'assets, en minimisant le compute gaspille et en maximisant la robustesse des assets qui passent en production.

---

## Pipeline Actuel (6 Phases)

| Phase | Nom | Input | Output |
|-------|-----|-------|--------|
| 0 | Download | - | `data/*.parquet` |
| 1 | Screening | 97 assets | `outputs/multiasset_scan_*.csv` |
| 2 | Validation | Screening winners | WINNERS + PENDING |
| 3A | Rescue (PENDING) | PENDING | `displacement_rescue_*.csv` |
| 3B | Optimization (WINNERS) | WINNERS | `displacement_optimization_*.csv` |
| 4 | Filter Grid | PENDING restants | `ANALYSIS_FILTER_GRID_*.md` |
| 5 | Production | Tous valides | `asset_config.py` |

---

## Diagramme de Flux

```
Phase 0: Download
    |
Phase 1: Screening (200 trials, --skip-guards)
    |
    +---> FAIL --> Stop ou Phase 3A (si asset important)
    |
Phase 2: Validation (300 trials, --run-guards)
    |
    +---> WINNERS (7/7) --> Phase 3B --> Phase 5
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
```

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

## Phase 1 : Screening (rapide)

**Objectif** : Eliminer rapidement les assets non-viables sans payer le cout des guards.

### Parametres

| Parametre | Valeur |
|-----------|--------|
| Trials | 200 |
| Guards | OFF (`--skip-guards`) |
| TP progression | ON (`--enforce-tp-progression`) |

### Criteres PASS (souples)

| Metrique | Seuil |
|----------|-------|
| WFE | > 0.5 |
| Sharpe OOS | > 0.8 |
| Trades OOS | > 50 |

### Commande

```bash
python scripts/run_full_pipeline.py \
  --assets BNB,ADA,DOGE,TRX,DOT \
  --trials 200 \
  --enforce-tp-progression \
  --skip-guards \
  --workers 4 \
  --output-prefix screen_batch1
```

**Output :** `outputs/multiasset_scan_*.csv`

---

## Phase 2 : Validation (robuste)

**Objectif** : Produire des params production-grade avec validation complete des 7 guards.

### Parametres

| Parametre | Valeur |
|-----------|--------|
| Trials | 300 |
| Guards | ON (`--run-guards`) |
| TP progression | ON (toujours) |

### Criteres PASS (stricts) — 7 Guards Obligatoires

| Guard | Seuil | Critique |
|-------|-------|----------|
| WFE | > 0.6 | OUI |
| MC p-value | < 0.05 | OUI |
| Sensitivity var | < 10% | OUI |
| Bootstrap CI lower | > 1.0 | OUI |
| Top10 trades | < 40% | OUI |
| Stress1 Sharpe | > 1.0 | OUI |
| Regime mismatch | < 1% | OUI |

**Seuils additionnels :**
- OOS Sharpe > 1.0 (target > 2.0)
- OOS Trades > 60

### Commande

```bash
python scripts/run_full_pipeline.py \
  --assets AVAX,SEI,NEAR,DOT \
  --trials 300 \
  --enforce-tp-progression \
  --run-guards \
  --workers 4 \
  --output-prefix validated
```

### Resultats

- **WINNERS** (7/7 PASS) → Phase 3B (optionnel) → Phase 5
- **PENDING** (<7/7 PASS) → Phase 3A

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
  --trials 300 \
  --enforce-tp-progression \
  --run-guards \
  --workers 4
```

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
  --workers 4 \
  --trials-atr 300 \
  --trials-ichi 300
```

**Pour des assets spécifiques :**

```bash
python scripts/run_phase3b_optimization.py \
  --assets BTC ETH \
  --workers 4 \
  --trials-atr 300 \
  --trials-ichi 300
```

**Outputs :**
- `outputs/displacement_optimization_*.csv` — Résultats détaillés par asset/displacement
- `outputs/displacement_optimization_summary_*.csv` — Résumé avec recommandations (KEEP/UPDATE)

**Note :** Le script teste automatiquement tous les displacements (26, 52, 78) pour chaque asset PROD et compare avec le baseline actuel. Il recommande une mise à jour si amélioration > 10% ET 7/7 guards PASS.

---

## Phase 4 : Filter Grid (PENDING restants)

**Objectif** : Tester des combinaisons de filtres pour les assets toujours en echec apres Phase 3A.

### Principe

Teste 12 combinaisons de filtres (baseline, medium_distance_volume, moderate, conservative, etc.)

### Filter Modes (ordre de test)

| Mode | Quand l'utiliser | Effet |
|:-----|:-----------------|:------|
| baseline | Premier test, toujours | Aucun filtre |
| medium_distance_volume | Si guard002 (sensitivity) FAIL | Reduit bruit |
| light_kama | Si baseline trop sensible | Filtre momentum |
| light_distance / light_volume | Tests intermediaires | Filtres legers |
| moderate | Si light_* insuffisant | Filtres moyens |
| conservative | Dernier recours avant BLOCKED | Filtre agressif |

### Commande

```bash
python scripts/run_full_pipeline.py \
  --assets [PENDING_ASSET] \
  --optimization-mode medium_distance_volume \
  --trials 300 \
  --enforce-tp-progression \
  --run-guards \
  --workers 4
```

**Output :** `outputs/ANALYSIS_FILTER_GRID_{ASSET}_*.md`

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

## NE PAS FAIRE

- Ne jamais utiliser `docs/HANDOFF.md` comme reference
- Ne jamais modifier les seuils guards sans validation
- Ne jamais skip le warmup (200 barres minimum)
- Ne jamais oublier `.shift(1)` sur les rolling features (look-ahead)
- Ne jamais valider avec Sharpe > 4 ou WFE > 2 sans reconciliation (trop beau = suspect)

---

## IMPORTANT

- **`status/project-state.md`** = source de verite actuelle
- **`docs/HANDOFF.md`** = obsolete, ne pas utiliser
- **`docs/BACKTESTING.md`** = historique seulement, pas l'etat actuel
- **`.cursor/rules/*.mdc`** = regles generales (lues automatiquement)

---

## Suivi et Tracabilite

Maintenir `status/project-state.md` a jour avec :

| Asset | Mode | Disp | Sharpe | WFE | Trades | Date Validation |
|:------|:-----|:-----|:-------|:----|:-------|:---------------|
| BTC | baseline | 52 | 2.14 | >0.6 | 416 | Pre-fix |
| ETH | medium_distance_volume | 52 | 2.09 | 0.82 | 57 | 2026-01-22 |

---

## Checklist

### Pre-flight

- [ ] Donnees 1H telechargees pour le batch
- [ ] TP progression enforcement ON
- [ ] Verifier timestamp fichier > 2026-01-22 12:00 UTC (cutoff bug TP)

### Phase 1 — Screening

- [ ] Tous les batches run
- [ ] Shortlist winners exportee

### Phase 2 — Validation

- [ ] Reopt 300 trials
- [ ] Guards 7/7 pour WINNERS

### Phase 3A/3B — Displacement

- [ ] Grid displacement teste pour PENDING/WINNERS
- [ ] Meilleur displacement documente

### Phase 4 — Filter Grid

- [ ] Combinaisons testees pour PENDING restants
- [ ] Resultats documentes

### Phase 5 — Production

- [ ] `asset_config.py` a jour
- [ ] `status/project-state.md` a jour
- [ ] Plans Pine generes si necessaire
