# Handoff

## Objectif
Finaliser les briques d’analyse (metrics/visualisation), optimisation (Bayesian + walk-forward) et validation des signaux.

## Plan actuel
- [x] Scanner le repo et confirmer la structure
- [x] Poser l'ossature des modules/fichiers
- [x] Implémenter la couche data (fetcher/cache/preprocess)
- [x] Indicateurs core + tests unitaires de base
- [x] Aligner MAMA/FAMA/KAMA sur `computeAlpha()` MESA (alpha/beta dynamiques)
- [x] Stratégie Final Trigger + moteur de backtest + position manager multi-TP
- [x] Rendre l'ordre intra-bar et le sizing configurables + tests associés
- [x] Aligner compounding avec coûts + scénarios backtest multi-legs
- [x] Tests `sizing_mode="equity"` (compounding net of costs)
- [x] Ajouter métriques/visualisation + optimisation (Bayesian, walk-forward)
- [x] Ajouter un outil de comparaison des signaux Pine vs Python

## Décisions prises + raisons
- Reproduction fidèle de la logique Pine (Puzzle + Grace + 5in1 + Ichimoku externe) pour éviter des écarts de signaux.
- Manager multi-TP avec trailing (SL -> BE après TP1, SL -> TP1 après TP2) pour refléter le comportement visuel Pine.
- MAMA/FAMA/KAMA utilisent maintenant `computeAlpha()` MESA basé sur l’ER (alpha/beta dynamiques) pour coller au Pine.
- Backtest initial simple (pnl agrégé par exit_time) pour itérer vite avant metrics/optimisation.
- Ajout d'options `sizing_mode` (fixed/equity) et `intrabar_order` (stop_first/tp_first) pour expliciter l'hypothèse intra-bar.
- Coûts appliqués à la sortie (net_pnl) pour un compounding cohérent en mode `equity`.
- Param space standardisé via `base_params` + `search_space` pour Optuna.
- Tests multi-scénarios (long/short, 3 legs, trailing, compounding) pour verrouiller le comportement du moteur.

## Fichiers modifiés
- `.gitignore`
- `crypto_backtest/analysis/metrics.py`
- `crypto_backtest/analysis/visualization.py`
- `crypto_backtest/analysis/validation.py`
- `crypto_backtest/engine/backtest.py`
- `crypto_backtest/engine/position_manager.py`
- `crypto_backtest/examples/compare_signals.py`
- `crypto_backtest/examples/optimize_final_trigger.py` ← **NEW**
- `crypto_backtest/indicators/mama_fama_kama.py`
- `crypto_backtest/optimization/bayesian.py`
- `crypto_backtest/optimization/walk_forward.py`
- `crypto_backtest/strategies/final_trigger.py`
- `tests/test_indicators.py`
- `tests/test_backtest.py`

## Commandes pour run/test
- `pytest -v`
- `python crypto_backtest/examples/optimize_final_trigger.py` (demo 10 trials)

## Problèmes connus / next steps
- [x] ~~Ajouter un exemple `param_space` complet pour FinalTrigger v2 (ranges + toggles).~~
- [x] ~~Fix: BayesianOptimizer convertit correctement dict → dataclass.~~
- [ ] Valider la cohérence des signaux vs Pine sur données réelles (CSV export TradingView).
- [ ] Ajouter tests unitaires pour `optimize_final_trigger.py` (param_space presets).
- [ ] Documenter le workflow d'optimisation dans un README ou notebook.
- [ ] Fix FutureWarning: `Hour.delta` deprecated dans `metrics.py:81`.

## Dernières MAJ
- Implémentation de `compute_alpha()` (MESA) et KAMA principal basé sur alpha/beta dynamiques.
- La stratégie passe `er_length` à MAMA/FAMA pour refléter `len` Pine.
- Tests: `pytest -v` (17 passed).
