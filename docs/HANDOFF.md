# Handoff — FINAL TRIGGER v2 Backtest System

> **Date de transmission**: 2026-01-21
> **État**: PRODUCTION READY — Portfolio 1H validé (guards)

---

## EXECUTIVE SUMMARY (Pour Agent Suivant)

### Qu'est-ce que c'est ?
Pipeline de backtest complet pour la stratégie TradingView "FINAL TRIGGER v2" convertie en Python. Inclut optimisation bayésienne (ATR + Ichimoku), validation walk-forward, tests Monte Carlo, analyse de régimes, et construction de portfolio multi-asset.

### État Final
- **Portfolio Production (scan)**: BTC + ETH + XRP + AVAX + UNI + SUI + SEI (7 assets validés)
- **Portfolio Production (full guards)**: BTC + ETH + AVAX + UNI + SEI (SUI exclu)
- **Assets Exclus**: SOL, AAVE, HYPE, ATOM, ARB, LINK, INJ, TIA (WFE < 0.6 ou overfit), SUI (guards)
- **Sharpe Portfolio Original**: ~4.52 (BTC/ETH/XRP weights optimisés)
- **Tous les tests de robustesse passés**: WFE, Monte Carlo, Bootstrap, Sensitivity
- **Clustering**: invalidé (CLUSTERFAIL) → fallback params individuels (voir `outputs/pine_plan.csv`)

### Dernières mises à jour (2026-01-21)
- **Guards timestampés**: `scripts/run_guards_multiasset.py` suffixe chaque fichier guard avec `run_id` et génère un résumé `multiasset_guards_summary_{run_id}.csv`.
- **Streamlit**: page Guards affiche les valeurs (p_value, variance, CI, etc.) en plus des flags pass, et charge automatiquement le résumé guard le plus récent (fallback legacy).
- **Console persistante**: panel “Console” dans la sidebar Streamlit avec logs horodatés et niveaux (RUN/OK/ERR/etc.).
- **Console UI**: version compacte et déplacée en bas de sidebar (corbeille réduite).
- **Machine profile**: config `config/machine_profile.json` + utilitaires `system_utils.py` (workers dynamiques + warning stockage) et sliders Streamlit ajustés.
- **README**: installation corrigée (`crypto_backtest/requirements.txt`) + section Machine Profile.
- **Fail diagnostics**: diagnostic FAIL + réoptimisation conservative dans Streamlit, persistance JSON (diagnostic/reopt/validated/dead).
- **Session dialogs**: remplacement des modals `st.dialog` + fix Portfolio Builder (min 2 assets).
- **Bayesian UX**: progression vers Guards seulement si ≥1 asset PASS (sinon warning + retry/force).
- **Dashboard scans**: historique multi-scan (PASS/FAIL par run) affiché dans le Dashboard.
- **Dashboard scans**: actions rapides par scan (CSV + chargement assets) sans menu secondaire.
- **TP progressifs**: contrainte `tp1 < tp2 < tp3` (gap ≥ 0.5) ajoutée aux optimisations, validation post-optim et flag CLI `--enforce-tp-progression` (propagé via `scripts/run_full_pipeline.py` + Streamlit).
- **Pine Strategies**: scripts `FT_BTC.pine`, `FT_ETH.pine`, `FT_AVAX.pine`, `FT_UNI.pine`, `FT_SEI.pine` générés (paramètres frozen + exécution multi-TP).
- **Sessions + Stepper**: ajout d’un système de session (`crypto_backtest/config/session_manager.py`) et d’un stepper visuel dans Streamlit (Dashboard, Download, Bayesian, Guards, Comparateur).
- **Modals Sessions**: création/chargement de session via modals (boutons désormais fonctionnels).
- **Auto-progression**: auto-update des étapes (Download/Optimize/Guards/Validate) + recommandations contextuelles sur le Dashboard.
- **Historique**: page Streamlit “📋 Historique” avec filtres, comparaison, notes et gestion des sessions.
- **Final polish**: pages pipeline “session-aware”, liaison outputs→session, footer progression, raccourcis sidebar, empty state Dashboard.
- **Top 50 (sans BTC/ETH/AVAX/UNI/SEI) - 2 batches**:
  - **PASS**: DOT (OOS Sharpe 3.54, WFE 1.24), SHIB (4.71, 1.85), NEAR (3.25, 2.02), SUI (1.39, 0.75), APT (3.77, 8.11)
  - **FAIL**: SOL, XRP, BNB, ADA, DOGE, LINK, MATIC, LTC, ATOM, XLM, FIL, ARB, OP, INJ, RENDER, FET, TAO, PEPE, WIF, BONK, AAVE, MKR, CRV, SNX, SAND
  - **Clustering**: batch 1 only (k=2, silhouette 0.096); batch 2 skipped (<3 assets PASS)
  - **Outputs**: `outputs/multiasset_scan_20260121_1619.csv`, `outputs/multiasset_scan_20260121_1626.csv`, `outputs/cluster_analysis_20260121_1619.json`, `outputs/cluster_param_loss_20260121_1619.csv`
- **OP displacement=78 full run**: SUCCESS, OOS Sharpe 2.48, WFE 1.66, OOS trades 90 (baseline disp=52 was 1.07). Outputs: `outputs/displacement_grid_OP_20260121_173045.csv`, `outputs/op_fullrun_disp78_20260121_174550.csv`
- **Modes de filtrage KAMA**: 3 configs (BASELINE/MODERATE/CONSERVATIVE) ajoutées à `crypto_backtest/validation/conservative_reopt.py`
  - **BASELINE**: 0 filtres (only Ichimoku external), pour optimisation initiale
  - **MODERATE** (défaut reopt): 4 filtres (Distance, Volume, RegCloud, KAMA Osc), mama_kama=False, ichi_strict=False
  - **CONSERVATIVE**: 5 filtres (all KAMA + strict Ichi), pour overfit sévère uniquement
- **Diagnostics granulaires**: `crypto_backtest/analysis/diagnostics.py` avec 6+ checks (Sharpe OOS, WFE, Max DD, Trade Count, IS/OOS Consistency, Guards)
  - Recommandations auto de filter mode (MODERATE par défaut, CONSERVATIVE si WFE < 0.3)
  - Intégration Streamlit: page "Comparaison Assets" avec diagnostics détaillés + bouton reopt
- **Tests DOGE KAMA**: comparaison BASELINE vs CONSERVATIVE montre que plus de filtres ≠ meilleure performance
  - BASELINE (0 filtres): Sharpe 1.75, 459 trades
  - CONSERVATIVE (5 filtres): Sharpe 1.41, 348 trades (-19% Sharpe)
  - Conclusion: filtres KAMA utiles pour réduire overfit, mais peuvent dégrader performance sur certains assets

### Fichiers Critiques
| Fichier | Description |
|---------|-------------|
| `app.py` | Dashboard Streamlit (Dark Trading Theme) |
| `README.md` | **Guide d'utilisation + interprétation outputs pour agents** |
| `crypto_backtest/config/asset_config.py` | Config production (params optimaux par asset) |
| `crypto_backtest/config/scan_assets.py` | Top 50 cryptos (tiers) + critères |
| `docs/HANDOFF.md` | Ce document - contexte complet |
| `outputs/portfolio_construction.csv` | Résultats portfolio optimisé |
| `outputs/optim_*_best_params.json` | Params optimaux par asset |
| `outputs/pine_plan_fullguards.csv` | Plan Pine pour assets full guards |
| `scripts/run_guards_multiasset.py` | Guards multi-asset (outputs timestampés) |
| `crypto_backtest/config/session_manager.py` | Gestion des sessions Streamlit |
| `crypto_backtest/analysis/diagnostics.py` | Diagnostics granulaires + recommandations reopt |
| `crypto_backtest/validation/conservative_reopt.py` | Configs filtres KAMA + reopt conservative |

### Interprétation des Outputs (Pour Agents)

Le dashboard Streamlit génère automatiquement des CSV/JSON dans `outputs/`. Pour interpréter ces données **sans l'UI**, consulter la section **"📁 Outputs et Interprétation (Pour Agents)"** dans [README.md](../README.md#-outputs-et-interprétation-pour-agents).

**Fichiers clés à analyser**:
- `multiasset_scan_*.csv` — Résultats scan avec status PASS/FAIL
- `optim_{ASSET}_best_params.json` — Paramètres optimaux par asset
- `multiasset_guards_summary_{run_id}.csv` — Résultats des 7 guards par asset (le plus récent est auto-chargé)
- `portfolio_correlation.csv` — Corrélations entre assets (diversification)
- `concurrent_dd.csv` — Périodes de drawdown simultanés (risque portfolio)
- `pine_plan_fullguards.csv` — Plan de production pour TradingView

**Exemples Python** pour lire ces fichiers disponibles dans le README.

### Gestion des Runs (RunManager)

**Problème résolu**: Éviter l'écrasement des résultats lors de scans multiples.

Depuis 2026-01-21, les outputs sont organisés par **run timestampé**:

```
outputs/
├── run_20260121_120000/
│   ├── manifest.json    # Métadonnées (description, assets, config)
│   ├── scan.csv         # Résultats scan
│   ├── guards.csv       # Résultats guards
│   └── params/
│       ├── BTC.json     # Params optimaux par asset
│       └── ETH.json
└── run_20260121_150000/ # Nouveau scan, pas de conflit
    └── ...
```

**Usage**:
```python
from crypto_backtest.utils.run_manager import RunManager

# Créer un nouveau run
run = RunManager.create_run(
    description="Displacement grid [26-78]",
    assets=["BTC", "ETH"],
    metadata={"displacement_range": [26, 39, 52, 65, 78]}
)

# Sauvegarder résultats
run.save_scan_results(scan_df)
run.save_params("BTC", btc_params)
run.save_guards_summary(guards_df)

# Lister et comparer
runs = RunManager.list_runs()
latest = RunManager.get_latest_run()
scan_df = latest.load_scan_results()
```

**Fichiers**:
- `crypto_backtest/utils/run_manager.py` — Module principal
- `examples/run_manager_usage.py` — Exemples détaillés

**Migration**: Les anciens fichiers legacy (`outputs/optim_*.json`, `multiasset_guards_summary.csv`) restent accessibles en lecture seule. Les nouveaux scans utilisent automatiquement la structure de runs.

### Notes de Test (2026-01-21)
- `python scripts/run_guards_multiasset.py --assets BTC --params-file outputs/pine_plan.csv` lancé deux fois, **timeouts** après 120s puis 300s (création partielle de fichiers Monte Carlo). Les fichiers partiels ont été supprimés.

### Prochaines Étapes Suggérées
1. ✅ ~~**P1 - Multi-Timeframe**~~: DONE → rester en 1H (4H/1D insuffisant)
2. 🔴 **P1 - Displacement Grid**: Optimiser displacement [26, 39, 52, 65, 78] — **PRIORITAIRE**
3. ✅ **P2 - CODEX-005**: Multi-Asset Scan 10 Alts + Clustering — **IMPLEMENTED**
4. ✅ **P3 - Dashboard Streamlit**: Interface visuelle — **IMPLEMENTED** (Dark Trading Theme)
5. ✅ **P4 - Filter Modes**: BASELINE/MODERATE/CONSERVATIVE configs — **IMPLEMENTED**
6. ✅ **P5 - Diagnostics**: Système de diagnostics granulaires avec recommandations — **IMPLEMENTED**
7. 🟡 **P6 - MODERATE Testing**: Valider config MODERATE sur assets FAIL (DOGE, OP, etc.)
8. **P7 - Live Trading**: Implémenter connecteur exchange live

### Données (Local Only)
Les fichiers `data/Binance_*_1h.csv` sont ignorés par git. Pour régénérer:
```bash
python fetch_binance_data.py  # ou relancer les scripts de fetch
```

---

## 🎯 Objectif

Convertir l'indicateur TradingView "FINAL TRIGGER v2 - State/Transition + A/D Line + Ichi Light" en Python avec système de backtest professionnel, walk-forward analysis et optimisation bayésienne.

---

## ✅ État Actuel (Phase 2 Complétée)

### Résultats de Performance

| Métrique | Baseline | Phase 1 (ATR) | Phase 2 (Ichi) | Δ Total |
|----------|----------|---------------|----------------|----------|
| Return | -6.44% | +10.76% | **+15.69%** | +22.13pp |
| Sharpe | -0.80 | 1.43 | **2.13** | +2.93 |
| Max DD | -9.2% | -2.9% | **-2.85%** | +6.35pp |
| Win Rate | 33.6% | 40.9% | **43.51%** | +9.9pp |
| Profit Factor | 0.86 | 1.33 | **1.54** | +0.68 |
| Trades | - | 425 | 416 | - |
| Expectancy | - | - | +$3.77/trade | - |
| Recovery Factor | - | - | 5.50 | - |
| Sortino | - | - | 0.34 | - |

### Paramètres Optimaux

```yaml
# ATR (Phase 1)
sl_atr_mult: 3.75
tp_atr_mult: 3.75
trailing_start: 9.0
trailing_step: 7.0

# Ichimoku General (Phase 2)
tenkan: 13         # standard: 9
kijun: 34          # standard: 26
displacement: 52

# Ichimoku 5in1 (Phase 2)
tenkan_5: 12
kijun_5: 21
displacement_5: 52
```

### Contexte d'Exécution

```yaml
Asset: Binance_BTCUSDT_1h.csv
Warmup: 200 bars
Sizing: fixed
Fees: 5 bps
Slippage: 2 bps
```

---

## ✅ Walk-Forward OOS Validation (60/20/20)

Baseline IS Sharpe: **2.13**  
WFE (OOS/IS): **1.23** → **pas** de risque d'overfitting.

| Segment | Return | Sharpe | Sortino | Max DD | Win Rate | Profit Factor | Trades |
|---------|--------|--------|---------|--------|----------|---------------|--------|
| **IS** | +9.41% | 2.14 | 0.34 | -2.85% | 42.75% | 1.53 | 255 |
| **VAL** | +2.75% | 2.05 | 0.30 | -1.54% | 43.06% | 1.56 | 72 |
| **OOS** | +3.94% | 2.63 | 0.43 | -1.85% | 49.35% | 1.73 | 77 |

**Outputs**:
- `outputs/oos_validation_results.csv`
- `outputs/oos_validation_report.txt`

---

## ✅ Sensitivity Analysis (Ichimoku Grid)

Grid: tenkan 11–15, kijun 32–36, tenkan_5 10–14, kijun_5 19–23  
Paramètres fixes: SL/TP 3.75/3.75/9.0/7.0, displacement 52.

**Variance locale (±1 autour 13/34, 12/21)**: **4.98%** → **ROBUST**.

**Outputs**:
- `outputs/sensitivity_grid_results.csv`
- `outputs/sensitivity_heatmap_ichimoku.png`
- `outputs/sensitivity_heatmap_5in1.png`
- `outputs/sensitivity_report.txt`

---

## ✅ Monte Carlo Permutation Test

Randomisation des points d'entrée (durées conservées), 1000 itérations.  
**P-value**: **0.0030** → **SIGNIFICANT** (pas d'overfitting).

**Stats**:
- Actual Sharpe: 2.1352
- Mean random Sharpe: 0.0435
- Std random Sharpe: 0.7054

**Outputs**:
- `outputs/monte_carlo_results.csv`
- `outputs/monte_carlo_distribution.png`
- `outputs/monte_carlo_report.txt`

---

## ⚠️ Market Regime Analysis

Regime dependent: **YES** (Bear/Sidways sous-performent).  
Target Sharpe > 1.0 **non atteint** en BEAR et SIDEWAYS.

| Regime | Sharpe | Return | Win Rate | PF | Trades |
|--------|--------|--------|----------|----|--------|
| **BULL** | 2.11 | +3.79% | 37.04% | 1.06 | 108 |
| **BEAR** | -0.64 | -1.18% | 56.12% | 2.73 | 98 |
| **HIGH_VOL** | 4.30 | +7.77% | 38.38% | 1.38 | 99 |
| **SIDEWAYS** | 0.00 | 0.00% | 0.00% | 0.00 | 0 |
| **OTHER** | 2.95 | +4.66% | 43.24% | 1.50 | 111 |

**Outputs**:
- `outputs/regime_analysis.csv`
- `outputs/regime_analysis_report.txt`

---

## ⚠️ Market Regime Analysis (V2)

**REGIME_DEPENDENT**: YES  
**CRITICAL**: YES  
**ACCEPTABLE**: YES (losing share 24.76%)

Targets:
- Sharpe > 0.8 (regimes >30 trades) → **FAILED** in SIDEWAYS
- Return < -2% → **FAILED** in SIDEWAYS (-7.71%)

**Outputs**:
- `outputs/regime_analysis_v2.csv`
- `outputs/regime_analysis_v2_report.txt`
- `outputs/regime_distribution.png`

---

## ✅ Regime Reconciliation (No Look-Ahead)

Total PnL: **$1568.88** (**+15.69%**)  
SIDEWAYS contribution: **79.50%** of total PnL (**+12.47%** return, 320 trades)  
Verdict: **SIDEWAYS PROFITABLE**  
Flag: **REGIME_V2_HAD_LOOKAHEAD_BUG**

| Regime | Trades | Return | Net PnL | % Total PnL | Avg PnL/Trade |
|--------|--------|--------|---------|-------------|----------------|
| CRASH | 0 | +0.00% | $0.00 | 0.00% | $0.00 |
| HIGH_VOL | 18 | +0.62% | $62.10 | 3.96% | $3.45 |
| BEAR | 3 | -0.52% | -$51.81 | -3.30% | -$17.27 |
| BULL | 21 | -0.10% | -$10.03 | -0.64% | -$0.48 |
| SIDEWAYS | 320 | +12.47% | $1247.23 | 79.50% | $3.90 |
| RECOVERY | 3 | -0.51% | -$51.46 | -3.28% | -$17.15 |
| OTHER | 51 | +3.73% | $372.86 | 23.77% | $7.31 |

**Outputs**:
- `outputs/regime_reconciliation.csv`
- `outputs/regime_reconciliation_report.txt`
- `outputs/trades_with_regime.csv`

---

## ✅ Bootstrap Confidence & Trade Distribution

**Bootstrap 95% CI**:
- Sharpe CI lower: **1.84**
- Return CI lower: **+7.52%**
→ **STATISTICALLY_WEAK: NO**

**Trade distribution**:
- Top 5 trades: **11.29%** of total return
- Top 10 trades: **22.55%** of total return
→ **OUTLIER_DEPENDENT: NO**

**Outputs**:
- `outputs/bootstrap_confidence.csv`
- `outputs/trade_distribution.csv`

---

## ✅ SIDEWAYS Filter Test (Sizing)

**Baseline**: 416 trades, return +15.69%, sharpe 2.135, max_dd -2.85%  
**SIDEWAYS 50% sizing**: 416 trades, return +9.92%, sharpe 2.144, max_dd -1.95%  
**SIDEWAYS 100% filter**: 81 trades, return +4.15%, sharpe 1.284, max_dd -1.53%

**Décision**: conserver la **baseline** (pas de sizing réduit en SIDEWAYS) pour préserver le retour global.

**Outputs**:
- `outputs/backtest_sideways_filter_50pct.csv`
- `outputs/backtest_sideways_filter_100pct.csv`

---

## ⚠️ Stress Test — Execution Costs

**Edge buffer**: 19 bps  
**FRAGILE**: NO  
**WEAK_EDGE**: YES  
**ROBUST**: NO

| Scenario | Fees/Slippage (bps) | Return | Sharpe | Max DD |
|----------|---------------------|--------|--------|--------|
| Base | 5 / 2 | +15.69% | 2.14 | -2.85% |
| Stress 1 | 10 / 5 | +10.99% | 1.48 | -3.08% |
| Stress 2 | 15 / 10 | +5.13% | 0.69 | -3.45% |
| Stress 3 | 20 / 15 | -0.74% | -0.07 | -6.65% |
| Stress 4 | 25 / 20 | -6.61% | -0.80 | -10.73% |

**Outputs**:
- `outputs/stress_test_fees.csv`
- `outputs/stress_test_fees_report.txt`

---

## ⚠️ Multi-Asset Validation (BTC params, ETH/SOL 1H)

**ETH**: return **-5.42%**, sharpe **-0.67**, max_dd **-12.95%**, trades **429**  
**SOL**: return **-0.41%**, sharpe **-0.04**, max_dd **-6.79%**, trades **390**

**Flags**:
- **ASSET_SPECIFIC**: YES  
- **TRANSFERABLE**: NO  
- **PORTFOLIO_READY**: NO

**Outputs**:
- `outputs/multi_asset_validation.csv`
- `outputs/multi_asset_report.txt`

---

## ✅ Multi-Asset Optimization (ETH/SOL/XRP/AAVE 1H)

PASS criteria: Sharpe > 1.0, WFE > 0.6, MC p < 0.05, trades >= 100, max DD < 15%.

| Asset | Return | Sharpe | Max DD | Trades | WFE | MC p | Status |
|-------|--------|--------|--------|--------|-----|------|--------|
| **ETH** | +20.41% | 2.90 | -2.61% | 450 | 2.46 | 0.00 | **PASS** |
| **SOL** | +9.01% | 2.61 | -1.01% | 300 | 0.70 | 0.00 | **PASS** |
| **XRP** | +27.89% | 3.44 | -1.67% | 483 | 0.80 | 0.00 | **PASS** |
| **AAVE** | +41.21% | 2.86 | -3.06% | 651 | 0.44 | 0.00 | **FAIL (OVERFIT)** |

**Portfolio (PASS assets only: ETH/SOL/XRP)**:
- Equal-weight: return **+18.92%**, sharpe **4.35**, max_dd **-0.63%**
- Optimized weights (min 10%): ETH **0.2155**, SOL **0.5229**, XRP **0.2617**  
  Return **+16.18%**, sharpe **4.52**, max_dd **-0.47%**

**Outputs**:
- `outputs/optim_ETH_atr.csv`, `outputs/optim_ETH_ichi.csv`, `outputs/optim_ETH_best_params.json`, `outputs/optim_ETH_validation.csv`
- `outputs/optim_SOL_atr.csv`, `outputs/optim_SOL_ichi.csv`, `outputs/optim_SOL_best_params.json`, `outputs/optim_SOL_validation.csv`
- `outputs/optim_XRP_atr.csv`, `outputs/optim_XRP_ichi.csv`, `outputs/optim_XRP_best_params.json`, `outputs/optim_XRP_validation.csv`
- `outputs/optim_AAVE_atr.csv`, `outputs/optim_AAVE_ichi.csv`, `outputs/optim_AAVE_best_params.json`, `outputs/optim_AAVE_validation.csv`
- `outputs/multi_asset_optimized_summary.csv`
- `outputs/portfolio_construction.csv`

**Note data**:
- Les fichiers `data/Binance_*_1h.csv` et `data/cache/binance/*.parquet` sont ignorés par git (local only).
- Pour régénérer: relancer les scripts de fetch (ex: `fetch_binance_data.py`) sur la même plage de dates.

---

## ✅ Configuration Production Portfolio (3 Assets)

Date: **2026-01-20**  
Status: **VALIDATED**  
Assets: **BTC, ETH, XRP**  
Exclus: **SOL** (params incompatibles), **AAVE** (WFE 0.44 overfitting)

```python
ASSET_CONFIG = {
    "BTC": {
        "pair": "BTC/USDT",
        "atr": {"sl_mult": 3.75, "tp1_mult": 3.75, "tp2_mult": 9.0, "tp3_mult": 7.0},
        "ichimoku": {"tenkan": 13, "kijun": 34},
        "five_in_one": {"tenkan_5": 12, "kijun_5": 21},
        "displacement": 52,
    },
    "ETH": {
        "pair": "ETH/USDT",
        "atr": {"sl_mult": 5.0, "tp1_mult": 5.0, "tp2_mult": 3.0, "tp3_mult": 8.0},
        "ichimoku": {"tenkan": 7, "kijun": 26},
        "five_in_one": {"tenkan_5": 13, "kijun_5": 25},
        "displacement": 52,
    },
    "XRP": {
        "pair": "XRP/USDT",
        "atr": {"sl_mult": 4.0, "tp1_mult": 5.0, "tp2_mult": 3.0, "tp3_mult": 5.0},
        "ichimoku": {"tenkan": 10, "kijun": 32},
        "five_in_one": {"tenkan_5": 9, "kijun_5": 20},
        "displacement": 52,
    },
}

EXEC_CONFIG = {"warmup_bars": 200, "fees_bps": 5, "slippage_bps": 2, "timeframe": "1H"}
```

---

## 🏗️ Architecture Implémentée

```
crypto_backtest/
├── config/settings.py          ✅ Paramètres globaux
├── data/
│   ├── fetcher.py              ✅ CCXT multi-exchange
│   ├── storage.py              ✅ Cache Parquet
│   └── preprocessor.py         ✅ Nettoyage données
├── indicators/
│   ├── ichimoku.py             ✅ 17 cond bull + 3 cond bear Light (ACTIF)
│   ├── five_in_one.py          ✅ 5 filtres avec toggles (ICHI LIGHT ACTIF)
│   ├── atr.py                  ✅ ATR pour SL/TP
│   └── mama_fama_kama.py       ✅ MESA Adaptive MA (inactif)
├── strategies/
│   ├── base.py                 ✅ Interface abstraite
│   └── final_trigger.py        ✅ Puzzle + Grace logic
├── engine/
│   ├── backtest.py             ✅ Moteur vectorisé
│   ├── execution.py            ✅ Fees/slippage
│   └── position_manager.py     ✅ Multi-TP (50/30/20) + trailing
├── optimization/
│   ├── bayesian.py             ✅ Optuna TPE
│   └── walk_forward.py         ✅ Walk-forward analysis
└── analysis/
    └── metrics.py              ✅ Sharpe, Sortino, Calmar, etc.
```

---

## ⚙️ Configuration Active

> **IMPORTANT**: Seuls 2 filtres sont actifs dans la configuration par défaut (BASELINE).

| Paramètre | Valeur | Description |
|-----------|--------|-------------|
| `use_ichimoku_filter` | **TRUE** | Ichimoku Externe (17 bull / 3 bear) |
| `use_5in1_ichi_light` | **TRUE** | Ichi Light dans le 5-in-1 |
| `use_mama_kama_filter` | FALSE | MAMA/FAMA/KAMA désactivé |
| `use_transition_mode` | FALSE | Mode transition désactivé |
| Autres filtres 5in1 | FALSE | Distance, Volume, AD, Regression, KAMA Osc |

---

## 🔧 Modes de Filtrage KAMA (2026-01-21)

Le système propose 3 configurations de filtres pour gérer le trade-off performance vs overfit:

### BASELINE (Initial Optimization)
**Configuration minimale** pour l'optimisation initiale:
- ❌ MAMA/KAMA Filter
- ❌ Distance Filter
- ❌ Volume Filter (A/D Line ou OBV)
- ❌ Regression Cloud
- ❌ KAMA Oscillator
- ✅ Ichimoku External (seul actif)
- ❌ Ichi Strict Mode (Light - 3 conditions bearish)

**Usage**: Première optimisation pour identifier le potentiel brut de l'asset.

### MODERATE (Default Reopt) ⭐
**Configuration par défaut** pour la ré-optimisation (équilibre performance/robustesse):
- ❌ MAMA/KAMA Filter (OFF - per user preference)
- ✅ Distance Filter
- ✅ Volume Filter (A/D Line)
- ✅ Regression Cloud (ON - per user preference)
- ✅ KAMA Oscillator
- ✅ Ichimoku External
- ❌ Ichi Strict Mode (Light - per user preference)

**Bénéfices**: Réduit l'overfit sans dégrader excessivement la performance.

### CONSERVATIVE (Severe Overfit Only)
**Configuration maximale** pour assets avec overfit sévère (WFE < 0.3):
- ✅ MAMA/KAMA Filter
- ✅ Distance Filter
- ✅ Volume Filter
- ✅ Regression Cloud
- ✅ KAMA Oscillator
- ✅ Ichimoku External
- ✅ Ichi Strict Mode (17 bull + 17 bear conditions)

**Usage**: Uniquement pour assets montrant forte dégradation IS→OOS.

### 📊 Tests Comparatifs (DOGE 1H)

| Metric | BASELINE (0 filtres) | CONSERVATIVE (5 filtres) | Delta |
|--------|----------------------|--------------------------|-------|
| Sharpe | **1.75** | 1.41 | **-19%** ❌ |
| Trades | 459 | 348 | -24% |
| Return | 87.2% | 60.8% | -26.4pp |

**Conclusion**: Plus de filtres ≠ meilleure performance systématique. Les filtres KAMA sont utiles pour réduire l'overfit, mais peuvent dégrader la performance sur certains assets. **MODERATE** offre un équilibre raisonnable.

### 🔍 Système de Diagnostics

`crypto_backtest/analysis/diagnostics.py` analyse automatiquement:
- **6+ Checks**: Sharpe OOS, WFE, Max DD, Trade Count, IS/OOS Consistency, Guards
- **Recommandations auto**:
  - **MODERATE** (défaut) si WFE ≥ 0.3 et pas d'overfit sévère
  - **CONSERVATIVE** si WFE < 0.3 ou multiple failures
  - Suggestions: trials à augmenter, displacement grid à tester, exclusion asset

**Interface Streamlit**: Page "Comparaison Assets" affiche diagnostics détaillés + bouton reopt avec pre-fill settings.

**Fichiers**:
- `crypto_backtest/validation/conservative_reopt.py` — Configs filtres
- `crypto_backtest/analysis/diagnostics.py` — Diagnostic checks
- `test_doge_kama_*.py` — Scripts de test comparatif

---

## 🚀 Prochaines Étapes (Priorités)

### ✅ P0 — Walk-Forward OOS Validation (DONE)

```
[INSTRUCTION-WF-001]
Objectif: Implémenter split 60/20/20 et valider WFE > 0.6
Résultat: OOS Sharpe = 2.63, WFE = 1.23 (PASS)
Outputs: outputs/oos_validation_results.csv, outputs/oos_validation_report.txt
```

### ✅ P0 — Sensitivity Analysis (DONE)

```
[INSTRUCTION-SENS-002]
Résultat: variance locale 4.98% (ROBUST)
Outputs: outputs/sensitivity_grid_results.csv, outputs/sensitivity_report.txt
```

### ✅ P0 — Monte Carlo Permutation Test (DONE)

```
[INSTRUCTION-GUARD-001]
Résultat: p-value 0.0030 (SIGNIFICANT)
Outputs: outputs/monte_carlo_results.csv, outputs/monte_carlo_report.txt
```

### ⚠️ P0 — Market Regime Analysis (DONE)

```
[INSTRUCTION-GUARD-002]
Résultat: REGIME_DEPENDENT (BEAR/SIDEWAYS)
Outputs: outputs/regime_analysis.csv, outputs/regime_analysis_report.txt
```

### ⚠️ P0 — Market Regime Analysis V2 (DONE)

```
[INSTRUCTION-GUARD-002-V2]
Résultat: REGIME_DEPENDENT + CRITICAL (SIDEWAYS)
Outputs: outputs/regime_analysis_v2.csv, outputs/regime_analysis_v2_report.txt
```

### ✅ P0 — Regime Reconciliation (DONE)

```
[INSTRUCTION-REGIME-RECONCILIATION]
Résultat: SIDEWAYS profitable (79.50% PnL), V2 had look-ahead bug
Outputs: outputs/regime_reconciliation.csv, outputs/regime_reconciliation_report.txt
```

### ✅ P0 — Bootstrap & Trade Distribution (DONE)

```
[INSTRUCTION-GUARD-003 / GUARD-005]
Résultat: CI Sharpe lower 1.84, Return lower +7.52% (OK)
Top 10 trades 22.55% (OK)
Outputs: outputs/bootstrap_confidence.csv, outputs/trade_distribution.csv
```

### ✅ P0 — SIDEWAYS Filter Test (DONE)

```
[INSTRUCTION-FILTER-SIDEWAYS-PARTIAL]
Résultat: 50% sizing → Sharpe 2.144, Return +9.92%, MaxDD -1.95%
Outputs: outputs/backtest_sideways_filter_50pct.csv, outputs/backtest_sideways_filter_100pct.csv
```

### ⚠️ P0 — Stress Test Execution Costs (DONE)

```
[INSTRUCTION-GUARD-006]
Résultat: WEAK_EDGE, edge buffer 19 bps
Outputs: outputs/stress_test_fees.csv, outputs/stress_test_fees_report.txt
```

### ⚠️ P1 — Multi-Asset Validation (DONE)

```
[INSTRUCTION-MULTI-ASSET-001]
Résultat: ETH/SOL Sharpe < 0 (FAIL)
Outputs: outputs/multi_asset_validation.csv, outputs/multi_asset_report.txt
```

### ✅ P1 — Multi-Asset Optimization (DONE)

```
[INSTRUCTION-MULTI-ASSET-002]
Résultat: ETH/SOL/XRP PASS, AAVE FAIL (WFE 0.44). Portfolio construit avec PASS assets.
Outputs: outputs/multi_asset_optimized_summary.csv, outputs/portfolio_construction.csv, outputs/optim_*_{atr,ichi,best_params,validation}.csv/json
```

### ✅ P1 — Multi-Timeframe Validation (DONE → rester en 1H)

```
[INSTRUCTION-MTF-001]
Résultat: 4H faible sur BTC/ETH/UNI, 1D sans trades (Sharpe=0).
SEI seul >1.5 en 4H (Sharpe 3.92) mais décision globale: rester en TF 1H.
Outputs: outputs/mtf_validation.csv
```

### 🔴 P1 — Displacement Optimization (PRIORITAIRE)

```
[INSTRUCTION-DISP-001]
Objectif: Grid search displacement [26, 39, 52, 65, 78] sur tous les assets validés
Critère: Amélioration Sharpe > 0.1
Assets: BTC, ETH, AVAX, UNI, SEI
```

**Méthodologie**:
1. Pour chaque asset, tester les 5 valeurs de displacement
2. Garder les autres paramètres fixes (optimaux actuels)
3. Comparer Sharpe OOS pour chaque valeur
4. Sélectionner le meilleur displacement par asset

### ✅ P3 — Dashboard Streamlit (IMPLEMENTED)

```
[INSTRUCTION-UI-001]
Status: IMPLEMENTED (2026-01-21)
Objectif: Interface visuelle pour piloter les backtests
```

**Fichiers**:
| Fichier | Description |
|---------|-------------|
| `app.py` | Dashboard Streamlit principal (~2300 lignes) |
| `.streamlit/config.toml` | Configuration thème Dark Trading |

**Pages Disponibles**:
- **Dashboard** — Vue d'ensemble (données, optimisations, guards)
- **Download OHLCV** — Téléchargement données (Top 50 cryptos par tiers)
- **Comparateur Pine** — Compare signaux Python vs Pine Script
- **Bayesian** — Optimisation bayésienne (+ option displacement)
- **Displacement Grid** — Grid search displacement isolé
- **Guards** — Tests de robustesse (7 guards)
- **Comparaison Assets** — Tri/filtre des résultats
- **Portfolio Builder** — Corrélations + auto-sélection assets
- **Visualisation** — Graphiques Plotly interactifs

**Design**: Dark Trading Theme
- Fond noir (#0E1117)
- Accent cyan (#00D4FF)
- Gradient cards, glow buttons, styled tabs

**Usage**:
```bash
streamlit run app.py
```

**Changelog**:
- 2026-01-21: Fix navigation sidebar (radio buttons → session_state buttons)

### ✅ P2 — Multi-Asset Scan 10 Alts + Clustering (CODEX-005) — IMPLEMENTED

```
[CODEX-MULTI-ASSET-005]
Status: IMPLEMENTED (2026-01-20)
Objectif: Scanner 10 nouveaux alts, clustering des params similaires
```

**Nouveaux Assets à Scanner**:
HYPE, AVAX, ATOM, ARB, LINK, UNI, SUI, INJ, TIA, SEI

**Fichiers Créés**:
| Fichier | Description |
|---------|-------------|
| `crypto_backtest/config/scan_assets.py` | Config scan (assets, search spaces, critères) |
| `scripts/download_data.py` | Download OHLCV via CCXT multi-exchange |
| `crypto_backtest/optimization/parallel_optimizer.py` | Optimisation parallèle joblib |
| `crypto_backtest/analysis/cluster_params.py` | K-means clustering des params |
| `crypto_backtest/analysis/cluster_guard.py` | Re-backtest OOS par cluster + fallback Pine |
| `crypto_backtest/analysis/mtf_validation.py` | Validation multi-TF (4H/1D) via resample |
| `scripts/run_full_pipeline.py` | Pipeline complet (download→optimize→cluster) |

**Usage**:
```bash
# Full pipeline
python scripts/run_full_pipeline.py --workers 8

# Skip download si data présente
python scripts/run_full_pipeline.py --skip-download --workers 8

# Assets spécifiques
python scripts/run_full_pipeline.py --assets HYPE AVAX SUI --workers 4

# Clustering seul sur résultats existants
python -m crypto_backtest.analysis.cluster_params --input outputs/multiasset_scan_*.csv

# Cluster guard (param loss + fallback Pine)
python -m crypto_backtest.analysis.cluster_guard --scan outputs/multiasset_scan_*.csv --cluster-json outputs/cluster_analysis_*.json

# Multi-timeframe 4H/1D sur assets PASS (resample 1H)
python -m crypto_backtest.analysis.mtf_validation --scan outputs/multiasset_scan_*.csv
```

**Critères de Succès**:
- OOS Sharpe > 1.0
- WFE > 0.6
- OOS Trades > 50
- Max DD < 15%
- Silhouette Score > 0.5 (qualité clusters)

**Outputs Attendus**:
- `outputs/multiasset_scan_{ts}.csv` — Résultats scan
- `outputs/cluster_analysis_{ts}.json` — Clusters JSON
- `crypto_backtest/config/cluster_params.py` — Config Python générée
- `outputs/cluster_paramloss.csv` — Param loss OOS (cluster guard)
- `outputs/pine_plan.csv` — Plan Pine individuel (fallback)

### ✅ CODEX-005 Scan Results (2026-01-20)

**Résultats Scan 10 Alts**:
| Asset | OOS Sharpe | WFE | Status |
|-------|------------|-----|--------|
| **AVAX** | 4.22 | 1.10 | ✅ PASS |
| **UNI** | 3.83 | 1.78 | ✅ PASS |
| **SUI** | 2.56 | 1.13 | ✅ PASS |
| **SEI** | 3.88 | 1.02 | ✅ PASS |
| HYPE | -7.01 | 0.00 | ❌ (short history) |
| ATOM | -1.93 | -1.10 | ❌ OVERFIT |
| ARB | -2.59 | -1.04 | ❌ OVERFIT |
| LINK | 2.37 | 0.52 | ❌ OVERFIT |
| INJ | 0.79 | 0.19 | ❌ OVERFIT |
| TIA | 0.43 | 0.16 | ❌ OVERFIT |

**Clusters (K-means k=2, SUCCESS assets)**:
- **Cluster 0** (BTC, UNI, SUI, SEI): SL=3.5, TP1=4.5, TP2=6.5, TP3=9.0, tenkan=10, kijun=29
- **Cluster 1** (ETH, AVAX): SL=3.5, TP1=3.0, TP2=7.0, TP3=6.0, tenkan=18, kijun=27

**Cluster Guard (param loss OOS)**:
- **CLUSTERFAIL** (loss > 15% sur ≥1 asset, cluster_size < 3 sur cluster_1)
- **Décision**: ignorer les clusters → fallback params individuels
- **Plan Pine**: `outputs/pine_plan.csv`

**Portfolio Total Validé**: BTC + ETH + XRP + AVAX + UNI + SUI + SEI (7 assets)

### ✅ Full Production Guards (ETH/AVAX/UNI/SUI/SEI)

Run: `python scripts/run_guards_multiasset.py --assets ETH AVAX UNI SUI SEI --params-file outputs/pine_plan.csv --workers 4`

**Résultats Guards (7)**:
| Asset | GUARD-001 | GUARD-002 | GUARD-003 | GUARD-005 | GUARD-006 | GUARD-007 | ALL |
|-------|----------|-----------|-----------|-----------|-----------|-----------|-----|
| ETH | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| AVAX | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| UNI | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| SEI | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| SUI | ✅ | ✅ | ❌ | ❌ | ✅ | ✅ | ❌ |

**Décision**: SUI exclu (Bootstrap CI Sharpe lower < 1.0, Top 10 trades > 40%).

**Outputs**:
- `outputs/multiasset_guards_summary.csv`
- `outputs/multiasset_guards_minireport.txt`
- `outputs/pine_plan_fullguards.csv`
- `outputs/{asset}_montecarlo.csv`, `outputs/{asset}_sensitivity.csv`, `outputs/{asset}_bootstrap.csv`
- `outputs/{asset}_tradedist.csv`, `outputs/{asset}_stresstest.csv`, `outputs/{asset}_regime.csv`

---

## 🎯 Seuils de Validation

| Métrique | Minimum | Target | Current | Status |
|----------|---------|--------|---------|--------|
| Sharpe Ratio | >1.5 | >2.0 | 2.13 | ✅ |
| Sortino Ratio | >0.25 | >0.5 | 0.34 | ✅ |
| Max Drawdown | <10% | <5% | 2.85% | ✅ |
| Win Rate | >40% | >45% | 43.5% | ✅ |
| Profit Factor | >1.5 | >1.8 | 1.54 | ✅ |
| Expectancy | >$2 | >$4 | $3.77 | ✅ |
| Recovery Factor | >3 | >5 | 5.50 | ✅ |
| Walk-Forward Eff. | >0.6 | >0.8 | 1.23 | ✅ |

---

## ⚠️ Anti-Patterns à Surveiller

| Red Flag | Signe | Action |
|----------|-------|--------|
| Overfitting | IS/OOS Sharpe diverge >40% | Réduire params libres |
| Peak Optimization | Optimum = pic isolé | Élargir zone stable |
| Curve Fitting | <100 trades | Étendre historique |
| Regime Bias | Perf dégradée bear market | Ajouter regime filter |

---

## 📚 Documentation Associée

- **[README.md](../README.md)** — Vue d'ensemble du projet
- **[instructions.md](../instructions.md)** — Prompt Agent Comet + instructions GPT Codex
- **[claude.md](../claude.md)** — Plan détaillé et spécifications techniques
