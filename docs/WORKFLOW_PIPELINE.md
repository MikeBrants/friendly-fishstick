# WORKFLOW PIPELINE — Commandes par Phase

> **Source de vérité pour les COMMANDES.**
> Pour les paramètres → `.cursor/rules/MASTER_PLAN.mdc`
> Pour l'état du projet → `status/project-state.md`

---

## ⚠️ RÈGLES DE MISE À JOUR

**CE FICHIER EST STABLE** — Modifier uniquement si:
- Nouveau script ajouté au repo
- Argument CLI changé/ajouté
- Correction de commande erronée

**NE PAS MODIFIER:**
- Les paramètres (workers, trials, seuils) → voir `MASTER_PLAN.mdc`
- L'ordre des phases

**OWNER:** Jordan (Dev) — Peut mettre à jour après test de la commande

---

## Phase 0: Download Data

```bash
python scripts/download_data.py --assets ETH BTC DOGE SHIB DOT
```

**Output:** `data/Binance_*_1h.parquet`

---

## Phase 1: Screening (rapide, multi-workers)

```bash
python scripts/run_full_pipeline.py \
  --assets ETH BTC DOGE SHIB DOT \
  --trials-atr 200 \
  --trials-ichi 200 \
  --enforce-tp-progression \
  --workers 10 \
  --skip-guards \
  --output-prefix screening
```

**Seuils SOFT:** WFE>0.5, Sharpe>0.5, Trades>50, SHORT 25-75%
**Output:** `outputs/screening_multiasset_scan_*.csv`

---

## Phase 2: Validation (rigoureux, workers=1)

```bash
python scripts/run_full_pipeline.py \
  --assets ETH \
  --trials-atr 300 \
  --trials-ichi 300 \
  --enforce-tp-progression \
  --run-guards \
  --workers 1 \
  --output-prefix validation
```

**Seuils STRICTS:** WFE>0.6, Sharpe>1.0, Trades>60, 7/7 hard guards PASS
**Output:** `outputs/validation_*_report.txt`

---

## Phase 3A: Rescue Displacement (si WFE FAIL)

```bash
# Tester d26
python scripts/run_full_pipeline.py \
  --assets ETH \
  --fixed-displacement 26 \
  --trials-atr 300 \
  --trials-ichi 300 \
  --enforce-tp-progression \
  --run-guards \
  --workers 1

# Tester d78
python scripts/run_full_pipeline.py \
  --assets ETH \
  --fixed-displacement 78 \
  --trials-atr 300 \
  --trials-ichi 300 \
  --enforce-tp-progression \
  --run-guards \
  --workers 1
```

**Critère:** 7/7 hard guards PASS avec nouveau displacement

---

## Phase 3B: Filter Rescue (si Sensitivity FAIL)

```bash
# Cascade automatique: baseline → moderate → conservative
python scripts/run_filter_rescue.py ETH --trials 300

# Ou manuellement
python scripts/run_full_pipeline.py \
  --assets ETH \
  --optimization-mode moderate \
  --trials-atr 300 \
  --trials-ichi 300 \
  --enforce-tp-progression \
  --run-guards \
  --workers 1
```

**Modes:** baseline (1 filtre) → moderate (5) → conservative (7)
**Si conservative FAIL → EXCLU**

---

## Phase 4: Regime Stress Test

```bash
python scripts/run_regime_stress_test.py --asset ETH --regime MARKDOWN
python scripts/run_regime_stress_test.py --asset ETH --regime SIDEWAYS
```

**Critères:**
- MARKDOWN: Trades<10 OR Sharpe≥0
- SIDEWAYS: Sharpe>0 (sinon EXCLU)

**Output:** `outputs/stress_test_*_{ASSET}_*.csv`

---

## Phase 5: Production Config

1. Mettre à jour `crypto_backtest/config/asset_config.py`
2. Mettre à jour `status/project-state.md`
3. Vérifier reproductibilité (2 runs identiques)

---

## Phase 6: Portfolio Construction

```bash
python scripts/portfolio_construction.py \
  --input-validated outputs/multiasset_guards_summary_*.csv \
  --method max_sharpe \
  --min-weight 0.05 \
  --max-weight 0.20 \
  --output-prefix portfolio
```

**Méthodes:** equal | max_sharpe | risk_parity | min_cvar
**Output:** `outputs/portfolio_weights_*.csv`

---

## Commandes Utilitaires

### Vérifier reproductibilité
```bash
python scripts/verify_reproducibility.py \
  --run1 outputs/run1_*.csv \
  --run2 outputs/run2_*.csv
```

### Analyser résultats Phase 1
```bash
python scripts/export_screening_results.py \
  --input outputs/screening_*.csv \
  --status SUCCESS \
  --output candidates.txt
```

---

## Checklist Pré-Run

- [ ] Data téléchargée (`data/*.parquet` existe)
- [ ] `--enforce-tp-progression` inclus
- [ ] Phase 2+: `--workers 1`
- [ ] Phase 2+: `--run-guards`

---

**Version**: 1.1 (26 Jan 2026)
**Dernière MAJ**: Ajout règles MAJ + SHORT ratio Phase 1
