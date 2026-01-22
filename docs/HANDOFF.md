# Handoff — FINAL TRIGGER v2 Backtest System

> **Date de transmission**: 2026-01-22
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

### Documentation Clé

| Document | Description |
|----------|-------------|
| **[docs/BACKTESTING.md](BACKTESTING.md)** | Résultats, analyses, problèmes, next steps |
| **[docs/WORKFLOW_MULTI_ASSET_SCREEN_VALIDATE_PROD.md](WORKFLOW_MULTI_ASSET_SCREEN_VALIDATE_PROD.md)** | 🆕 Workflow scalable Screen→Validate→Prod (Phase 1: 200 trials, Phase 2: 300 trials + guards) |
| **[README.md](../README.md)** | Guide d'utilisation + interprétation outputs |

### Dernières mises à jour (2026-01-22)
- **Workflow multi-asset**: Nouveau document `docs/WORKFLOW_MULTI_ASSET_SCREEN_VALIDATE_PROD.md` décrivant le processus scalable en 3 phases (Download → Screen 200 trials → Validate 300 trials + guards).
- **Guards timestampés**: `scripts/run_guards_multiasset.py` suffixe chaque fichier guard avec `run_id` et génère un résumé `multiasset_guards_summary_{run_id}.csv`.
- **Streamlit**: page Guards affiche les valeurs (p_value, variance, CI, etc.) en plus des flags pass, et charge automatiquement le résumé guard le plus récent (fallback legacy).
- **Console persistante**: panel "Console" dans la sidebar Streamlit avec logs horodatés et niveaux (RUN/OK/ERR/etc.).
- **Console UI**: version compacte et déplacée en bas de sidebar (corbeille réduite).
- **Machine profile**: config `config/machine_profile.json` + utilitaires `system_utils.py` (workers dynamiques + warning stockage) et sliders Streamlit ajustés.
- **README**: installation corrigée (`crypto_backtest/requirements.txt`) + section Machine Profile.
- **Fail diagnostics**: diagnostic FAIL + réoptimisation conservative dans Streamlit, persistance JSON (diagnostic/reopt/validated/dead).
- **Session dialogs**: remplacement des modals `st.dialog` + fix Portfolio Builder (min 2 assets).
- **Bayesian UX**: progression vers Guards seulement si ≥1 asset PASS (sinon warning + retry/force).
- **Dashboard scans**: historique multi-scan (PASS/FAIL par run) affiché dans le Dashboard.
- **Dashboard scans**: actions rapides par scan (CSV + chargement assets) sans menu secondaire.
- **TP progression**: enforcement default ON; use `--no-enforce-tp-progression` to disable. Audit outputs in `outputs/tp_progression_errors_*.csv`.
- **Pine Strategies**: scripts `FT_BTC.pine`, `FT_ETH.pine`, `FT_AVAX.pine`, `FT_UNI.pine`, `FT_SEI.pine` générés (paramètres frozen + exécution multi-TP).
- **Sessions + Stepper**: ajout d'un système de session (`crypto_backtest/config/session_manager.py`) et d'un stepper visuel dans Streamlit (Dashboard, Download, Bayesian, Guards, Comparateur).
- **Modals Sessions**: création/chargement de session via modals (boutons désormais fonctionnels).
- **Auto-progression**: auto-update des étapes (Download/Optimize/Guards/Validate) + recommandations contextuelles sur le Dashboard.
- **Historique**: page Streamlit "📋 Historique" avec filtres, comparaison, notes et gestion des sessions.
- **Final polish**: pages pipeline "session-aware", liaison outputs→session, footer progression, raccourcis sidebar, empty state Dashboard.
- **Top 50 (sans BTC/ETH/AVAX/UNI/SEI) - 2 batches**:
  - **PASS**: DOT (OOS Sharpe 3.54, WFE 1.24), SHIB (4.71, 1.85), NEAR (3.25, 2.02), SUI (1.39, 0.75), APT (3.77, 8.11)
  - **FAIL**: SOL, XRP, BNB, ADA, DOGE, LINK, MATIC, LTC, ATOM, XLM, FIL, ARB, OP, INJ, RENDER, FET, TAO, PEPE, WIF, BONK, AAVE, MKR, CRV, SNX, SAND
  - **Clustering**: batch 1 only (k=2, silhouette 0.096); batch 2 skipped (&lt;3 assets PASS)
  - **Outputs**: `outputs/multiasset_scan_20260121_1619.csv`, `outputs/multiasset_scan_20260121_1626.csv`, `outputs/cluster_analysis_20260121_1619.json`, `outputs/cluster_param_loss_20260121_1619.csv`
- **OP displacement=78 full run**: SUCCESS, OOS Sharpe 2.48, WFE 1.66, OOS trades 90 (baseline disp=52 was 1.07). Outputs: `outputs/displacement_grid_OP_20260121_173045.csv`, `outputs/op_fullrun_disp78_20260121_174550.csv`
- **OP guards (disp=78)**: ALL PASS. p=0.0000, sens var=5.34%, bootstrap CI lower=2.01, stress1 sharpe=1.73, regime mismatch=0.00. Outputs: `outputs/multiasset_guards_summary_20260121_175759.csv`, `outputs/OP_validation_report_20260121_175759.txt`
- **Displacement grid (near-threshold FAIL)**: SOL best=52 (no gain), DOGE best=26 (+2.18 Sharpe vs 52), LINK best=39 (+1.36). Outputs: `outputs/displacement_grid_summary_20260121_175713.csv`
- **Full runs with fixed displacement**:
  - DOGE disp=26: SUCCESS, OOS Sharpe 3.12, WFE 1.18, OOS trades 78. Output overwritten in `outputs/multiasset_scan_20260121_1759.csv` by LINK; see `optim_DOGE_disp26.log` for details.
  - LINK disp=39: FAIL (WFE&lt;0.6), OOS Sharpe 1.79, WFE 0.46, OOS trades 62. Output: `outputs/multiasset_scan_20260121_1759.csv`
- **Fixed displacement mode**: `scripts/run_full_pipeline.py` and `crypto_backtest/optimization/parallel_optimizer.py` accept `--fixed-displacement` (applies to Ichimoku + 5in1). Guards accept optional `displacement` column in params CSV.
- **Modes de filtrage KAMA**: 3 configs (BASELINE/MODERATE/CONSERVATIVE) ajoutées à `crypto_backtest/validation/conservative_reopt.py`
  - **BASELINE**: 0 filtres (only Ichimoku external), pour optimisation initiale
  - **MODERATE** (défaut reopt): 4 filtres (Distance, Volume, RegCloud, KAMA Osc), mama_kama=False, ichi_strict=False
  - **CONSERVATIVE**: 5 filtres (all KAMA + strict Ichi), pour overfit sévère uniquement
- **Diagnostics granulaires**: `crypto_backtest/analysis/diagnostics.py` avec 6+ checks (Sharpe OOS, WFE, Max DD, Trade Count, IS/OOS Consistency, Guards)
  - Recommandations auto de filter mode (MODERATE par défaut, CONSERVATIVE si WFE &lt; 0.3)
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
| `docs/HANDOFF.md` | Ce document - resume + liens |
| `docs/BACKTESTING.md` | Dossier backtesting (resultats, analyses, problemes, next steps) |
| `docs/WORKFLOW_MULTI_ASSET_SCREEN_VALIDATE_PROD.md` | 🆕 Workflow scalable multi-asset (Screen→Validate→Prod) |
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
8. 🆕 **P7 - Workflow Scalable**: Suivre `docs/WORKFLOW_MULTI_ASSET_SCREEN_VALIDATE_PROD.md` pour batch processing
9. **P8 - Live Trading**: Implémenter connecteur exchange live

### Données (Local Only)
Les fichiers `data/Binance_*_1h.csv` sont ignorés par git. Pour régénérer:
```bash
python fetch_binance_data.py  # ou relancer les scripts de fetch
```

---

## Backtesting dossier
Full backtesting details moved to `docs/BACKTESTING.md` to keep this handoff short.
