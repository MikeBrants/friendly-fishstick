# Rôles des Agents - FINAL TRIGGER v2

## 1. Data Agent

**Responsabilités** :
- Téléchargement des données OHLCV (CCXT)
- Validation et nettoyage des données
- Gestion du cache Parquet
- Préprocessing (warmup, split train/test/OOS)

**Fichiers clés** :
- `crypto_backtest/data/fetcher.py`
- `crypto_backtest/data/preprocessor.py`
- `crypto_backtest/data/storage.py`

**Outputs** :
- Fichiers CSV dans `data/`
- Métadonnées dans `status/data_agent.json`

---

## 2. Optimization Agent

**Responsabilités** :
- Optimisation ATR (SL, TP1, TP2, TP3)
- Optimisation Ichimoku (Tenkan, Kijun, Displacement)
- Grid search displacement [26, 39, 52, 65, 78]
- Filter grid search (baseline, moderate, conservative, etc.)
- Enforce TP progression (TP1 < TP2 < TP3, gap >= 0.5)

**Fichiers clés** :
- `crypto_backtest/optimization/parallel_optimizer.py`
- `crypto_backtest/optimization/bayesian.py`
- `scripts/run_full_pipeline.py`
- `scripts/run_displacement_grid.py`
- `scripts/run_filter_rescue.py`

**Outputs** :
- `outputs/multiasset_scan_*.csv`
- `outputs/displacement_grid_*.csv`
- `outputs/filter_grid_results_*.csv`
- Statut dans `status/optimization_agent.json`

**Contraintes** :
- TP progression enforced par défaut
- Min trades: 50 IS, 60 OOS
- Min bars: 8000 IS

---

## 3. Validation Agent

**Responsabilités** :
- Exécution des 7 guards :
  - Guard001: Monte Carlo (p < 0.05)
  - Guard002: Sensitivity variance (< 15%)
  - Guard003: Bootstrap CI lower (> 1.0)
  - Guard005: Top 10 trades concentration (< 40%)
  - Guard006: Stress test Sharpe (> 1.0)
  - Guard007: Regime mismatch (< 1%)
  - Guard WFE: Walk-forward efficiency (> 0.6)
- Validation des seuils critiques
- Génération des rapports de validation

**Fichiers clés** :
- `scripts/run_guards_multiasset.py`
- `crypto_backtest/validation/guard_runner.py`

**Outputs** :
- `outputs/multiasset_guards_summary_*.csv`
- `outputs/*_validation_report_*.txt`
- Statut dans `status/validation_agent.json`

**Seuils critiques** :
- WFE > 0.6
- MC p-value < 0.05
- Sensitivity var < 15%
- Bootstrap CI lower > 1.0
- Top10 trades < 40%
- Stress1 Sharpe > 1.0
- Regime mismatch < 1%

---

## 4. Analysis Agent

**Responsabilités** :
- Analyse des résultats de scan
- Diagnostics granulaires (6+ checks)
- Recommandations de re-optimisation
- Analyse de corrélations portfolio
- Génération de rapports d'analyse

**Fichiers clés** :
- `crypto_backtest/analysis/diagnostics.py`
- `crypto_backtest/analysis/cluster_params.py`
- `scripts/portfolio_correlation.py`

**Outputs** :
- `outputs/diagnostic_history.json`
- `outputs/reoptimization_history.json`
- `outputs/ANALYSIS_*.md`
- Statut dans `status/analysis_agent.json`

**Recommandations** :
- Filter mode: MODERATE (défaut reopt), CONSERVATIVE (overfit sévère)
- Displacement grid si WFE borderline (0.3-0.6)
- Exclusion si WFE < 0.3 ou multiple failures

---

## Coordination

Les agents communiquent via :
- Fichiers dans `comms/` (messages, requêtes)
- Statut dans `status/` (état de chaque agent)
- Outputs dans `outputs/` (résultats partagés)
- Documentation dans `docs/` (HANDOFF.md, BACKTESTING.md)
