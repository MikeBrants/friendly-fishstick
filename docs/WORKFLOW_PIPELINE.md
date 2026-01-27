# WORKFLOW PIPELINE — Commandes par Phase

> **Source de verite pour les COMMANDES.**
> Pour les parametres → `.cursor/rules/MASTER_PLAN.mdc`
> Pour l'etat du projet → `status/project-state.md`

---

## Orchestrator (recommande)

```bash
# Phase 1: Screening
python scripts/orchestrator.py --phase 1 --assets ETH BTC DOGE SHIB DOT

# Phase 2: Validation
python scripts/orchestrator.py --phase 2 --assets ETH

# Phase 3: Rescue (displacement ou filter)
python scripts/orchestrator.py --phase 3 --assets ETH --rescue displacement
python scripts/orchestrator.py --phase 3 --assets ETH --rescue filter

# Phase 4: Regime Stress Test
python scripts/orchestrator.py --phase 4 --assets ETH

# Phase 5: Portfolio
python scripts/orchestrator.py --portfolio

# Status
python scripts/orchestrator.py --status
```

---

## Utilitaires

```bash
# Filtrer resultats Phase 1
python scripts/export_screening_results.py \
  --input "outputs/screening_*.csv" \
  --wfe 0.5 --sharpe 0.5 --trades 50 \
  --output candidates.txt --verbose

# Filtrer resultats Guards
python scripts/export_guards_results.py \
  --input "outputs/*_guards_summary_*.csv" \
  --status PASS --output validated.txt --verbose

# Assets FAIL (rescue candidates)
python scripts/export_guards_results.py \
  --input "outputs/*_guards_summary_*.csv" \
  --status FAIL --output rescue.txt --verbose
```

---

## Outputs attendus par phase

| Phase | Output | Pattern |
|-------|--------|---------|
| 1 | Scan CSV | `outputs/{prefix}_multiasset_scan_*.csv` |
| 2 | Scan + Guards CSV | `outputs/{prefix}_guards_summary_*.csv` |
| 3 | Scan + Guards CSV | `outputs/{prefix}_d{26,52,78}_*.csv` |
| 4 | Stress CSV | `outputs/stress_test_*_{ASSET}_*.csv` |
| 5 | Portfolio weights | `outputs/portfolio_weights_*.csv` |
| 6 | asset_config.py | `crypto_backtest/config/asset_config.py` |

---

## Commandes Directes (debug)

<details>
<summary>Phase 1 — run_full_pipeline.py</summary>

```bash
python scripts/run_full_pipeline.py \
  --assets ETH BTC DOGE SHIB DOT \
  --trials-atr 200 --trials-ichi 200 \
  --enforce-tp-progression \
  --workers 10 --skip-guards \
  --output-prefix screening
```
</details>

<details>
<summary>Phase 2 — run_full_pipeline.py</summary>

```bash
python scripts/run_full_pipeline.py \
  --assets ETH \
  --optimization-mode baseline \
  --trials-atr 300 --trials-ichi 300 \
  --enforce-tp-progression \
  --run-guards --workers 1 \
  --output-prefix validation
```
</details>

<details>
<summary>Phase 3A — Displacement rescue</summary>

```bash
python scripts/run_full_pipeline.py \
  --assets ETH \
  --fixed-displacement 26 \
  --trials-atr 300 --trials-ichi 300 \
  --enforce-tp-progression \
  --run-guards --workers 1
```
</details>

<details>
<summary>Phase 3B — Filter rescue</summary>

```bash
python scripts/run_filter_rescue.py ETH --trials 300
```
</details>

<details>
<summary>Phase 4 — Regime stress</summary>

```bash
python scripts/run_regime_stress_test.py --asset ETH --regimes MARKDOWN SIDEWAYS
```
</details>

<details>
<summary>Phase 6 — Portfolio</summary>

```bash
python scripts/portfolio_construction.py \
  --input-validated outputs/multiasset_guards_summary_*.csv \
  --method max_sharpe --min-weight 0.05 --max-weight 0.20
```
</details>

---

## Checklist Pre-Run

- [ ] Data telechargee (`data/*.parquet` existe)
- [ ] `--enforce-tp-progression` inclus
- [ ] Phase 2+: `--workers 1`
- [ ] Phase 2+: `--run-guards`

---

**Version**: 2.0 (27 Jan 2026)
**MAJ**: Orchestrator + utilitaires (Issue #24)
