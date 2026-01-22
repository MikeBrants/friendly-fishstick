# Brief — Workflow multi-assets (Screen → Revalidate → Prod)

Ce document décrit une stratégie **scalable** pour exécuter le pipeline FINAL TRIGGER v2 sur **des dizaines d'assets**, en minimisant le compute gaspillé et en maximisant la robustesse des assets qui passent en production.

---

## Architecture en 3 phases

```
┌─────────────────────────────────────────────────────────────────┐
│                     PHASE 0 — DOWNLOAD (1x)                     │
│            Télécharger toutes les données 1H (batch)            │
└─────────────────────────────────────────────────────────────────┘
                                │
┌─────────────────────────────────────────────────────────────────┐
│                 PHASE 1 — SCREENING PARALLÈLE                   │
│      Batches 5–8 assets × 200 trials × --skip-guards (rapide)   │
└─────────────────────────────────────────────────────────────────┘
                                │
                ┌───────────────┴───────────────┐
              PASS                            FAIL
                │                               │
┌───────────────▼───────────────┐               │
│       PHASE 2 — VALIDATION    │               ▼
│  Winners × 300 trials × full  │     Grid / Diagnostic / Stop
│            guards             │
└───────────────────────────────┘
                │
        ┌───────▼────────┐
        │  PROD READY ?  │
        └───────┬────────┘
                │
         Pine + Alerts
```

---

## Phase 0 — Download centralisé (1 fois)

**Objectif** : ne **pas** re-télécharger les données à chaque run.

- Télécharger tous les assets (ou un tier complet) en batch.
- Vérifier que chaque asset a assez d'historique (barres) et de trades potentiels.

Exemple (à adapter selon scripts disponibles) :

```bash
python scripts/batch_download.py \
  --assets-file crypto_backtest/config/scan_assets.py \
  --tier ALL \
  --interval 1h \
  --workers 4
```

**Outputs attendus** : `data/Binance_*_1h.csv`

---

## Phase 1 — Screening rapide (200 trials)

**Objectif** : éliminer vite les assets faibles (sur des critères "souples"), sans payer le coût des guards.

### Paramètres Phase 1

| Paramètre | Valeur |
|-----------|--------|
| Trials | 200 |
| Guards | OFF (`--skip-guards`) |
| TP progression | ON (`--enforce-tp-progression`) — critique pour éviter des plans multi-TP incohérents. |

### Organisation des batches (pratique)

- **Batch size** : 5 à 8 assets (selon CPU/RAM)
- **Priorisation** : TIER1 → TIER2 → TIER3 → TIER4 → BONUS.
- **Référence tiers** : `crypto_backtest/config/scan_assets.py` (TIER1..4, BONUS, VALIDATED, EXCLUDED).

### Commande type

```bash
python scripts/run_full_pipeline.py \
  --assets BNB,ADA,DOGE,TRX,DOT \
  --trials 200 \
  --enforce-tp-progression \
  --skip-guards \
  --workers 4 \
  --output-prefix screen_tier1
```

### Critères PASS (souples) Phase 1

| Métrique | Seuil |
|----------|-------|
| WFE | > 0.5 |
| Sharpe OOS | > 0.8 |
| Trades OOS | > 50 |

L'objectif est de sortir une **shortlist "winners"** rapidement.

---

## Phase 2 — Validation des winners (300 trials + guards)

**Objectif** : produire des params production-grade, robustes et justifiés par les 7 guards.

### Paramètres Phase 2

| Paramètre | Valeur |
|-----------|--------|
| Trials | 300 (reopt des winners) |
| Guards | ON (`--run-guards`) |
| TP progression | ON (toujours) |

### Commande type

```bash
python scripts/run_full_pipeline.py \
  --assets AVAX,SEI,NEAR,DOT \
  --trials 300 \
  --enforce-tp-progression \
  --run-guards \
  --workers 4 \
  --output-prefix validated
```

### Critères PASS (stricts) Phase 2

| Métrique | Seuil | Critique |
|----------|-------|----------|
| WFE | > 0.6 | OUI |
| Sharpe OOS | > 1.0 | OUI |
| Trades OOS | > 60 | OUI |
| MC p-value | < 0.05 | OUI |
| Sensitivity var | < 10% | OUI |
| Bootstrap CI lower | > 1.0 | OUI |
| Top10 trades | < 40% | OUI |
| Stress1 Sharpe | > 1.0 | OUI |
| Regime mismatch | < 1% | OUI |

---

## Gestion FAIL : grid / diagnostic / stop

### Si FAIL en phase 1

- **Option 1** : Stop (asset non prioritaire)
- **Option 2** : lancer un **displacement grid** (26/39/52/65/78) si l'asset est important.

### Si FAIL en phase 2 (guards)

- **Diagnostic** : sur/sous-fitting, trades insuffisants, instabilité sensi, top10 trop dominant.
- **Reopt "conservative"** (modes KAMA) si overfit détecté.

---

## Suivi et traçabilité (indispensable)

Créer / maintenir un **tracker CSV** (ex : `outputs/pipeline_tracker.csv`) :

| Asset | Tier | Screen Status | WFE | Sharpe | Reopt Status | Guards | Prod Ready |
|-------|------|---------------|-----|--------|--------------|--------|------------|
| BTC | 1 | DONE | 1.05 | 2.14 | DONE | 7/7 | YES |
| AVAX | 1 | DONE | 0.78 | 2.10 | RERUN | - | NO (TP) |

**But** : savoir en 10 secondes où en est chaque asset.

---

## Planning réaliste (ordre de grandeur)

| Étape | Durée estimée |
|-------|---------------|
| Download 50 assets | ~30 min |
| Screening 25 assets en 4 batches | ~1–2h (selon workers) |
| Validation 8–12 winners | ~2–3h |
| Pine + mise en prod | ~1h |

---

## Checklist

### Pre-flight

- [ ] Machine profile OK (`config/machine_profile.json`)
- [ ] Données 1H téléchargées pour le batch
- [ ] TP progression enforcement ON

### Phase 1 — Screening

- [ ] Tous les batches run
- [ ] Shortlist winners exportée (ex : `outputs/phase2_candidates.txt`)

### Phase 2 — Validation

- [ ] Reopt 300 trials
- [ ] Guards 7/7
- [ ] Plans multi-TP cohérents

### Production

- [ ] Génération Pine
- [ ] `pine_plan_fullguards.csv` à jour
- [ ] Alerts TradingView / exécution live définies
