# FINAL TRIGGER v2 — Backtest System

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Status](https://img.shields.io/badge/status-Production%20Ready-green.svg)](docs/HANDOFF.md)
[![Portfolio](https://img.shields.io/badge/Portfolio%20Sharpe-4.35-brightgreen.svg)](docs/HANDOFF.md)
[![Assets](https://img.shields.io/badge/Validated%20Assets-5-blue.svg)](outputs/pine_plan_fullguards.csv)

> Système de backtest professionnel pour **FINAL TRIGGER v2** — Implémentation Python de l'indicateur TradingView avec walk-forward analysis et optimisation bayésienne.

---

## 📈 Résultats Actuels (Production Ready)

### Portfolio Validé (5 Assets)
**BTC, ETH, AVAX, UNI, SEI** — Tous les assets ont passé les 7 guards de robustesse

| Asset | OOS Sharpe | WFE | Max DD | Trades |
|-------|------------|-----|--------|--------|
| **BTC** | 2.63 | 1.23 | -2.85% | 416 |
| **ETH** | 7.12 | 2.46 | -2.61% | 450 |
| **AVAX** | 4.22 | 1.10 | -3.14% | 402 |
| **UNI** | 3.83 | 1.78 | -2.89% | 389 |
| **SEI** | 3.88 | 1.02 | -3.21% | 371 |

**Portfolio Global** (equal-weight):
- Sharpe: **~4.35**
- Max DD: **-0.63%**
- Corrélation moyenne: **0.086** (faible corrélation = bonne diversification)

---

## 🎯 Objectif

Convertir l'indicateur TradingView "FINAL TRIGGER v2 - State/Transition + A/D Line + Ichi Light" (1223 lignes Pine Script) en Python avec :
- Backtest vectorisé haute performance
- Walk-forward analysis
- Optimisation bayésienne (Optuna)
- Validation Pine vs Python

---

## ⚙️ Configuration Active (Default)

> **IMPORTANT**: Seuls 2 filtres sont actifs dans la configuration par défaut.

| Paramètre | Valeur | Description |
|-----------|--------|-------------|
| `use_ichimoku_filter` | **TRUE** | Ichimoku Externe (17 bull / 3 bear Light) |
| `use_5in1_ichi_light` | **TRUE** | Ichi Light dans le 5-in-1 Filter |
| `use_mama_kama_filter` | FALSE | MAMA/FAMA/KAMA désactivé |
| `use_transition_mode` | FALSE | Mode transition désactivé |
| Autres filtres 5in1 | FALSE | Distance, Volume, AD Line, Regression, KAMA Osc |

### Paramètres Optimaux (Phase 2)

```yaml
ATR:
  sl_atr_mult: 3.75
  tp_atr_mult: 3.75
  trailing_start: 9.0
  trailing_step: 7.0

Ichimoku General:
  tenkan: 13
  kijun: 34
  displacement: 52

Ichimoku 5in1:
  tenkan_5: 12
  kijun_5: 21
  displacement_5: 52
```

### Pipeline de Signaux

```
Ichimoku External (17/3) → ichi_long_active / ichi_short_active
        ↓
Ichi Light (5in1) → allBull / allBear → bullish_signal / bearish_signal  
        ↓
Puzzle + Grace → trigger_long = (bullish_signal AND ichi_long_active) OR pending_grace
        ↓
ATR → SL / TP1 / TP2 / TP3
```

---

## 📊 Composants Implémentés

| Composant | Status | Description |
|-----------|--------|-------------|
| **Ichimoku Externe** | ✅ Actif | State machine biais directionnel (13/34) |
| **Ichi Light (5in1)** | ✅ Actif | Filtre Ichimoku simplifié (12/21) |
| **Puzzle + Grace** | ✅ Implémenté | Validation avec fenêtre 1 bar |
| **ATR Multi-TP** | ✅ Implémenté | SL + 3 TP (50%/30%/20%) + trailing |
| MAMA/FAMA/KAMA | ⚪ Inactif | Disponible mais désactivé |
| Autres 5in1 | ⚪ Inactif | Distance, Volume, AD, Regression, KAMA Osc |

---

## 🏗️ Structure du Projet

```
crypto_backtest/
├── config/settings.py          # Paramètres globaux
├── data/
│   ├── fetcher.py              # CCXT multi-exchange
│   ├── storage.py              # Cache Parquet
│   └── preprocessor.py         # Nettoyage données
├── indicators/
│   ├── ichimoku.py             # Ichimoku (13/34) ✅ ACTIF
│   ├── five_in_one.py          # Ichi Light (12/21) ✅ ACTIF
│   └── mama_fama_kama.py       # MESA Adaptive MA (inactif)
├── strategies/
│   └── final_trigger.py        # Logique principale
└── engine/
    ├── backtest.py             # Moteur vectorisé
    └── position_manager.py     # Multi-TP + trailing SL
```

---

## ⚡ Quick Start

### Installation

```bash
pip install -r crypto_backtest/requirements.txt
```

### Dashboard Streamlit (Recommandé)

Interface visuelle complète pour piloter tous les backtests:

```bash
streamlit run app.py
# Accès: http://localhost:8501
```

**Pages disponibles:**
- 📊 Dashboard — Vue d'ensemble
- 📥 Download OHLCV — Téléchargement données (Top 50 cryptos)
- 🔄 Comparateur Pine — Validation Python vs Pine Script
- ⚡ Bayesian — Optimisation bayésienne (ATR + Ichimoku)
- 🎚️ Displacement Grid — Grid search displacement [26-78]
- 🛡️ Guards — Tests de robustesse (7 guards automatiques)
- 🏆 Comparaison Assets — Tri/filtre des résultats
- 💼 Portfolio Builder — Corrélations + auto-sélection
- 📉 Visualisation — Graphiques interactifs

### FAIL Diagnostics & Reoptimization

Le dashboard propose un diagnostic automatique pour les assets en FAIL, avec
réoptimisation conservative (grille discrète) et historique persistant:

- Diagnostics: `outputs/diagnostic_history.json`
- Reoptimisations: `outputs/reoptimization_history.json`
- Assets validés: `outputs/validated_assets.json`
- Assets morts: `outputs/dead_assets.json`

### Ligne de Commande

```bash
# Pipeline complet (download → optimize → cluster)
python scripts/run_full_pipeline.py --workers 8

# Optimisation multi-asset avec guards
python scripts/run_guards_multiasset.py --assets BTC ETH AVAX --workers 4

# Analyse corrélations portfolio
python scripts/portfolio_correlation.py

# Backtest simple
python backtest_optimized.py
```

---

## 🖥️ Machine Profile & Workers

La configuration des workers dépend du profil machine (`config/machine_profile.json`).
Les sliders Streamlit utilisent désormais ces valeurs par défaut via
`crypto_backtest/utils/system_utils.py`.

Exemple (profil actuel):
```json
{
  "workers": {
    "bayesian": 6,
    "guards": 4,
    "download": 8,
    "displacement_grid": 6
  }
}
```

Le Dashboard affiche aussi un warning stockage si l’espace disque dépasse 90%.

---

## 🗂️ Gestion des Runs (Éviter l'écrasement des résultats)

### Problème

Avant: Si vous relancez un scan sur BTC, les anciens fichiers sont écrasés:
- `optim_BTC_best_params.json` ← Écrasé ❌
- `multiasset_guards_summary.csv` ← Écrasé ❌

### Solution: RunManager

Chaque run est isolé dans un dossier timestampé:

```
outputs/
├── run_20260121_120000/
│   ├── manifest.json          # Métadonnées (description, assets, config)
│   ├── scan.csv                # Résultats scan
│   ├── guards.csv              # Résultats guards
│   └── params/
│       ├── BTC.json            # Params optimaux BTC
│       └── ETH.json            # Params optimaux ETH
└── run_20260121_150000/        # Nouveau scan, aucun conflit
    └── ...
```

### Usage Python

```python
from crypto_backtest.utils.run_manager import RunManager

# Créer un nouveau run
run = RunManager.create_run(
    description="Displacement grid test [26-78]",
    assets=["BTC", "ETH", "AVAX"],
    metadata={"displacement_range": [26, 39, 52, 65, 78]}
)

# Sauvegarder résultats
run.save_scan_results(scan_df)
run.save_params("BTC", btc_params)
run.save_guards_summary(guards_df)

# Lister tous les runs
runs = RunManager.list_runs()
for r in runs:
    print(r.run_id, r.get_summary())

# Charger un run spécifique
run = RunManager.load_run("run_20260121_120000")
scan_df = run.load_scan_results()
btc_params = run.load_params("BTC")

# Trouver tous les runs avec un asset
btc_runs = RunManager.find_runs_with_asset("BTC")
```

### Exemple Complet

Voir [examples/run_manager_usage.py](examples/run_manager_usage.py) pour des exemples détaillés.

### Workflow Typique

1. **Avant un scan**: `run = RunManager.create_run(description="...")`
2. **Pendant**: `run.save_scan_results(df)`, `run.save_params(asset, params)`
3. **Guards**: `run.save_guards_summary(guards_df)`
4. **Après**: `run.get_summary()` pour vérifier
5. **Comparaison**: `RunManager.list_runs()` pour comparer les résultats

### Migration Legacy

Si vous avez des anciens fichiers (`outputs/optim_*.json`, `multiasset_guards_summary.csv`):

```bash
# Les scripts Streamlit gèrent automatiquement les deux formats
# Les anciens fichiers restent accessibles en lecture seule
# Les nouveaux runs utilisent la structure de dossiers
```

---

## 📁 Outputs et Interprétation (Pour Agents)

Le dashboard Streamlit génère des fichiers dans `outputs/`. Depuis la version v2, les outputs sont organisés par **run** (dossiers timestampés). Les anciens fichiers legacy (racine `outputs/`) restent compatibles.

### Structure des Outputs

**Nouveau format** (recommandé):
```
outputs/run_20260121_120000/
├── manifest.json     # Métadonnées
├── scan.csv          # Résultats scan
├── guards.csv        # Résultats guards
└── params/
    ├── BTC.json
    └── ETH.json
```

**Format legacy** (lecture seule):
```
outputs/
├── multiasset_scan_20260121_120000.csv
├── multiasset_guards_summary.csv      # Écrasé à chaque run
└── optim_BTC_best_params.json         # Écrasé à chaque run
```

Voici comment interpréter les fichiers en ligne de commande:

### 1. Scan Multi-Asset

**Nouveau format**: `outputs/run_YYYYMMDD_HHMMSS/scan.csv`
**Legacy**: `outputs/multiasset_scan_YYYYMMDD_HHMMSS.csv`

Colonnes clés:
- `asset` — Symbole de l'asset
- `oos_sharpe` — Sharpe ratio OOS (critère principal)
- `wfe` — Walk-Forward Efficiency (OOS/IS, doit être > 0.6)
- `oos_trades` — Nombre de trades OOS
- `max_dd` — Max drawdown (doit être < 15%)
- `status` — PASS/FAIL

```python
# Option 1: Via RunManager (recommandé)
from crypto_backtest.utils.run_manager import RunManager
run = RunManager.get_latest_run()
df = run.load_scan_results()
passed = df[df['status'] == 'PASS']
print(passed[['asset', 'oos_sharpe', 'wfe', 'max_dd']])

# Option 2: Lecture directe
import pandas as pd
df = pd.read_csv("outputs/run_20260121_120000/scan.csv")
passed = df[df['status'] == 'PASS']
print(passed[['asset', 'oos_sharpe', 'wfe', 'max_dd']])
```

### 2. Paramètres Optimaux par Asset

**Nouveau format**: `outputs/run_YYYYMMDD_HHMMSS/params/{ASSET}.json`
**Legacy**: `outputs/optim_{ASSET}_best_params.json`

```python
# Option 1: Via RunManager (recommandé)
from crypto_backtest.utils.run_manager import RunManager
run = RunManager.get_latest_run()
params = run.load_params("BTC")
print(f"SL: {params['sl_atr_mult']}, TP: {params['tp_atr_mult']}")
print(f"Tenkan: {params['tenkan']}, Kijun: {params['kijun']}")

# Option 2: Lecture directe
import json
with open("outputs/run_20260121_120000/params/BTC.json") as f:
    params = json.load(f)
print(f"SL: {params['sl_atr_mult']}, TP: {params['tp_atr_mult']}")
```

### 3. Guards Summary

**Nouveau format**: `outputs/run_YYYYMMDD_HHMMSS/guards.csv`
**Legacy**: `outputs/multiasset_guards_summary.csv`

Les 7 guards testés:
- `GUARD-001` — Monte Carlo (p-value < 0.05)
- `GUARD-002` — Regime Analysis (acceptable loss < 30%)
- `GUARD-003` — Bootstrap CI (Sharpe lower > 1.0)
- `GUARD-005` — Trade Distribution (top 10 < 40%)
- `GUARD-006` — Stress Test (edge buffer > 0)
- `GUARD-007` — Sensitivity (variance < 15%)
- `WFE` — Walk-Forward Efficiency (> 0.6)

```python
# Option 1: Via RunManager (recommandé)
from crypto_backtest.utils.run_manager import RunManager
run = RunManager.get_latest_run()
df = run.load_guards_summary()
all_pass = df[df['all_guards_pass'] == True]
print(all_pass[['asset', 'oos_sharpe', 'wfe']])

# Option 2: Lecture directe
import pandas as pd
df = pd.read_csv("outputs/run_20260121_120000/guards.csv")
all_pass = df[df['all_guards_pass'] == True]
print(all_pass[['asset', 'oos_sharpe', 'wfe']])
```

### 4. Portfolio Correlation

**Fichier**: `outputs/portfolio_correlation.csv`

Analyse des corrélations entre assets pour diversification:

```python
import pandas as pd
df = pd.read_csv("outputs/portfolio_correlation.csv")
# Corrélations > 0.5 (risque de sur-corrélation)
high_corr = df[df['daily_return_corr'] > 0.5]
print(high_corr[['asset_a', 'asset_b', 'daily_return_corr']])
```

### 5. Concurrent Drawdowns

**Fichier**: `outputs/concurrent_dd.csv`

Périodes où plusieurs assets sont en drawdown simultanément (risque portfolio):

```python
import pandas as pd
df = pd.read_csv("outputs/concurrent_dd.csv")
# Périodes critiques (≥3 assets en DD)
critical = df[df['count'] >= 3]
print(critical[['date', 'count', 'assets']])
```

### 6. Plan Pine (Production)

**Fichier**: `outputs/pine_plan_fullguards.csv`

Paramètres validés pour implémentation TradingView:

```python
import pandas as pd
df = pd.read_csv("outputs/pine_plan_fullguards.csv")
print(df[['asset', 'sl_atr_mult', 'tp_atr_mult', 'tenkan', 'kijun', 'displacement']])
```

### 7. Validation Walk-Forward

**Fichier**: `outputs/oos_validation_results.csv`

Split 60/20/20 (IS/VAL/OOS):

```python
import pandas as pd
df = pd.read_csv("outputs/oos_validation_results.csv")
print(df[['segment', 'sharpe', 'return_pct', 'max_dd', 'trades']])
# WFE = OOS Sharpe / IS Sharpe
wfe = df.loc[df['segment'] == 'OOS', 'sharpe'].values[0] / df.loc[df['segment'] == 'IS', 'sharpe'].values[0]
print(f"WFE: {wfe:.2f}")
```

### 8. Détails des Trades

**Fichiers**: `outputs/backtest_*.csv`

Chaque trade avec détails:

```python
import pandas as pd
df = pd.read_csv("outputs/backtest_BTC_final.csv")
print(df[['entry_time', 'exit_time', 'direction', 'pnl', 'return_pct']].head())
# Win rate
win_rate = (df['pnl'] > 0).mean() * 100
print(f"Win Rate: {win_rate:.1f}%")
```

---

## 🚀 Phases du Projet

| Phase | Status | Description |
|-------|--------|-------------|
| Phase 1 | ✅ | ATR TP/SL Optimization (Sharpe: 1.43) |
| Phase 2 | ✅ | Ichimoku Optimization (Sharpe: 2.13) |
| Phase 3 | ✅ | Walk-Forward OOS Validation (WFE: 1.23) |
| Phase 4 | ✅ | Sensitivity Analysis (variance: 4.98%) |
| Phase 5 | ✅ | Multi-Asset Scan + Clustering (10 alts) |
| Phase 6 | ✅ | Full Guards Suite (7 guards) |
| Phase 7 | ✅ | Dashboard Streamlit (Dark Trading Theme) |
| Phase 8 | ✅ | Multi-Timeframe Validation (rester 1H) |
| Phase 9 | 🔴 **P1** | **Displacement Grid Optimization** [26-78] |
| Phase 10 | 🟡 P4 | Live Trading Connector |

---

## 📚 Documentation

- **[instructions.md](instructions.md)** — Prompt Agent Comet + instructions GPT Codex
- **[claude.md](claude.md)** — Plan détaillé et spécifications techniques
- **[docs/HANDOFF.md](docs/HANDOFF.md)** — Documentation technique complète

---

## 🧪 Tests

```bash
pytest -v
```

---

## 📄 License

MIT
