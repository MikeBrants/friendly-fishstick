# Handoff — FINAL TRIGGER v2 Backtest System

> **Date de transmission**: 2026-01-22
> **Etat**: REVALIDATION EN COURS - TP progression enforcee, guard variance bloque ETH/CAKE

---

## EXECUTIVE SUMMARY (Pour Agent Suivant)

### Qu'est-ce que c'est ?
Pipeline de backtest complet pour la stratégie TradingView "FINAL TRIGGER v2" convertie en Python. Inclut optimisation bayésienne (ATR + Ichimoku), validation walk-forward, tests Monte Carlo, analyse de régimes, et construction de portfolio multi-asset.

### ETAT CRITIQUE (2026-01-22)

TP progression is now enforced by default. Previous pre-fix scans are invalid.

Revalidation results (2026-01-22):
- ETH SUCCESS (OOS Sharpe 3.87, WFE 2.36) but guard002 variance 12.96% -> guards fail
- AVAX/UNI FAIL (WFE < 0.6); SEI FAIL (OOS Sharpe < 1.0, WFE < 0.6)
- CAKE disp=26 SUCCESS (OOS Sharpe 2.73, WFE 0.73) but guard002 variance 20.70% -> guards fail

No asset besides BTC is cleared for production.

### État Production Réel

| Asset | Status | Raison |
|-------|--------|--------|
| **BTC** | ✅ PRODUCTION | Baseline validé (params manuels historiques) |
| ETH | ⚠️ A REVALIDER | TP enforced: SUCCESS (OOS Sharpe 3.87, WFE 2.36) but guard002 variance 12.96% |
| AVAX | ⚠️ A REVALIDER | TP enforced: WFE 0.52 (<0.6) |
| UNI | ⚠️ A REVALIDER | TP enforced: WFE 0.56 (<0.6), variance 10.27% |
| SEI | ⚠️ A REVALIDER | TP enforced: OOS Sharpe < 1.0, WFE < 0.6 |
| CAKE (disp=26) | ⚠️ A REVALIDER | SUCCESS (OOS Sharpe 2.73, WFE 0.73) but guard002 variance 20.70% |
| OP (disp=78) | ⚠️ À REVALIDER | Guards OK mais params pré-fix |
| DOGE (disp=26) | ⚠️ À REVALIDER | Guards OK mais params pré-fix |
| DOT, SHIB, NEAR | ⚠️ À REVALIDER | Scan PASS mais pré-fix |
| AR, EGLD, CELO, ANKR | ⚠️ À REVALIDER | Guards PASS mais pré-fix |

**Seul BTC est actuellement en production.**

## Etat actuel du pipeline (2026-01-22)

| Batch | Assets | Status |
|:------|:-------|:-------|
| Displacement d26 | JOE, CAKE | JOE PASS (pre-fix); CAKE SUCCESS but guards fail (variance 20.70%) |
| Displacement d65 | OSMO | PASS (57 trades accepted) |
| Displacement d78 | MINA, RUNE, TON | MINA PASS; RUNE/TON FAIL |
| Displacement d39 | AXS | FAIL (excluded) |
| Core P0 | ETH, AVAX, UNI, SEI | RUN DONE: ETH SUCCESS but guards fail (variance 12.96%); AVAX/UNI WFE<0.6; SEI OOS Sharpe<1.0 |
| Winners P1.1 | DOT, SHIB, NEAR | Pending after core re-opt |
| Disp P1.2 | OP, DOGE | Pending after core re-opt |
| Guard-passed P1.3 | AR, EGLD, CELO, ANKR | Pending after P1.1/P1.2 |

### Assets Exclus (définitif)
- SOL, AAVE, HYPE, ATOM, ARB, LINK, INJ, TIA (WFE < 0.6 ou overfit)
- HOOK, ALICE, HMSTR, LOOM (données insuffisantes: <60 trades OOS ou <10K bars)
- APT, EIGEN, ONDO (outliers suspects)

### Documentation Clé

| Document | Description |
|----------|-------------|
| **[docs/BACKTESTING.md](BACKTESTING.md)** | Résultats, analyses, problèmes, next steps |
| **[docs/WORKFLOW_MULTI_ASSET_SCREEN_VALIDATE_PROD.md](WORKFLOW_MULTI_ASSET_SCREEN_VALIDATE_PROD.md)** | Workflow scalable Screen→Validate→Prod (Phase 1: 200 trials, Phase 2: 300 trials + guards) |
| **[README.md](../README.md)** | Guide d'utilisation + interprétation outputs |

---

## RERUNS PRIORITAIRES

### Commande Batch (avec TP enforcement)

Note: for re-optimization, prefer `--optimization-mode moderate` (baseline remains default).

```bash
# Batch 1: Core assets (disp=52)
python scripts/run_full_pipeline.py \
  --assets ETH AVAX UNI SEI DOT SHIB NEAR \
  --workers 6 --trials-atr 100 --trials-ichi 100 \
  --enforce-tp-progression \
  --skip-download

# Batch 2: Displacement variants
python scripts/run_full_pipeline.py \
  --assets OP --fixed-displacement 78 \
  --workers 6 --trials-atr 100 --trials-ichi 100 \
  --enforce-tp-progression --skip-download

python scripts/run_full_pipeline.py \
  --assets DOGE --fixed-displacement 26 \
  --workers 6 --trials-atr 100 --trials-ichi 100 \
  --enforce-tp-progression --skip-download

# Batch 3: Nouveaux displacement winners (non encore validés)
python scripts/run_full_pipeline.py \
  --assets MINA RUNE TON --fixed-displacement 78 \
  --workers 6 --trials-atr 100 --trials-ichi 100 \
  --enforce-tp-progression --skip-download

python scripts/run_full_pipeline.py \
  --assets OSMO --fixed-displacement 65 \
  --workers 6 --trials-atr 100 --trials-ichi 100 \
  --enforce-tp-progression --skip-download
```

### Validation Post-Rerun

```python
import pandas as pd
from glob import glob

scan = pd.read_csv(sorted(glob("outputs/multiasset_scan_*.csv"))[-1])
for _, row in scan.iterrows():
    tp1, tp2, tp3 = row['tp1_mult'], row['tp2_mult'], row['tp3_mult']
    ok = (tp1 < tp2 < tp3) and (tp2 - tp1 >= 0.5) and (tp3 - tp2 >= 0.5)
    print(f"{row['asset']}: TP {tp1:.2f}<{tp2:.2f}<{tp3:.2f} | {'✅' if ok else '❌'}")
```

---

## Dernières mises à jour (2026-01-22)

- **CRITICAL - TP progression**: Enforcement is default; pre-fix results are invalid.
- **Revalidation (2026-01-22)**: ETH SUCCESS but guard002 variance 12.96%; AVAX/UNI/SEI fail WFE; CAKE SUCCESS but guard002 variance 20.70%.
- **Optimization modes**: baseline/moderate/conservative available; moderate is default for re-optimization.
- **Workflow multi-asset**: Nouveau document `docs/WORKFLOW_MULTI_ASSET_SCREEN_VALIDATE_PROD.md` decrivant le processus scalable en 3 phases.
- **Guards timestampes**: `scripts/run_guards_multiasset.py` suffixe chaque fichier avec `run_id`.
- **Fixed displacement mode**: `--fixed-displacement` disponible pour optimiser avec displacement fige.

### Historique (2026-01-21)
- Top 50 scan (2 batches): DOT, SHIB, NEAR, SUI, APT PASS (mais pré-fix TP)
- OP displacement=78: OOS Sharpe 2.48, WFE 1.66 (guards PASS mais pré-fix)
- DOGE displacement=26: OOS Sharpe 3.12, WFE 1.18 (pré-fix)
- Guard errors "complex numbers": YGG, ARKM, STRK, METIS, AEVO (debug requis)

---

## Fichiers Critiques

| Fichier | Description |
|---------|-------------|
| `app.py` | Dashboard Streamlit (Dark Trading Theme) |
| `README.md` | Guide d'utilisation + interprétation outputs |
| `crypto_backtest/config/asset_config.py` | Config production (params optimaux par asset) |
| `crypto_backtest/config/scan_assets.py` | Top 50 cryptos (tiers) + critères |
| `docs/HANDOFF.md` | Ce document - résumé + liens |
| `docs/BACKTESTING.md` | Dossier backtesting (résultats, analyses, next steps) |
| `docs/WORKFLOW_MULTI_ASSET_SCREEN_VALIDATE_PROD.md` | Workflow scalable multi-asset |
| `outputs/tp_progression_errors_*.csv` | ⚠️ Audit des erreurs TP (519 détectées) |
| `scripts/run_guards_multiasset.py` | Guards multi-asset (outputs timestampés) |

---

## Seuils de Validation (Rappel)

| Guard | Seuil | Critique |
|-------|-------|----------|
| WFE | > 0.6 | OUI |
| MC p-value | < 0.05 | OUI |
| Sensitivity var | < 10% | OUI |
| Bootstrap CI lower | > 1.0 | OUI |
| Top10 trades | < 40% | OUI |
| Stress1 Sharpe | > 1.0 | OUI |
| Regime mismatch | < 1% | OUI |
| Min trades OOS | > 60 | OUI |
| Min bars IS | > 8000 | OUI |

**Targets**: Sharpe > 1.0 (target > 2.0) | PF > 1.3 | MaxDD < 15%

---

## Prochaines Étapes

1. 🔴 **P0 - Revalidation (TP enforced)**: ETH/CAKE (guard002 variance), AVAX/UNI/SEI (WFE < 0.6), OP/DOGE (pre-fix)
2. 🔴 **P1 - Guards post-rerun**: Lancer 7 guards sur tous les assets PASS
3. 🟡 **P2 - Displacement grid**: Finaliser MINA, OSMO, RUNE, TON
4. 🟡 **P3 - Debug guard errors**: Investiguer YGG, ARKM, STRK, METIS, AEVO
5. ⬜ **P4 - Portfolio construction**: Apres validation, construire portfolio final
6. ⬜ **P5 - Pine generation**: Generer scripts TradingView pour assets valides
7. ⬜ **P6 - Live trading**: Implementer connecteur exchange

---

## Données (Local Only)

Les fichiers `data/Binance_*_1h.csv` sont ignorés par git. Pour régénérer:
```bash
python fetch_binance_data.py
```

---

## Backtesting Dossier

Détails complets dans `docs/BACKTESTING.md`.
