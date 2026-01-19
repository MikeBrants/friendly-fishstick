# Handoff

## Objectif
Implémenter la stratégie FINAL TRIGGER v2 + moteur de backtest multi-TP, puis préparer les prochaines étapes (metrics/optimisation).

## Plan actuel
- [x] Scanner le repo et confirmer la structure
- [x] Poser l’ossature des modules/fichiers
- [x] Implémenter la couche data (fetcher/cache/preprocess)
- [x] Indicateurs core + tests unitaires de base
- [x] Stratégie Final Trigger + moteur de backtest + position manager multi-TP
- [ ] Ajouter métriques/visualisation + optimisation (Bayesian, walk-forward) + example run

## Décisions prises + raisons
- Reproduction fidèle de la logique Pine (Puzzle + Grace + 5in1 + Ichimoku externe) pour éviter des écarts de signaux.
- Manager multi-TP avec trailing (SL -> BE après TP1, SL -> TP1 après TP2) pour refléter le comportement visuel Pine.
- Backtest initial simple (pnl agrégé par exit_time) pour itérer vite avant metrics/optimisation.

## Fichiers modifiés
- `crypto_backtest/indicators/atr.py`
- `crypto_backtest/strategies/final_trigger.py`
- `crypto_backtest/engine/position_manager.py`
- `crypto_backtest/engine/execution.py`
- `crypto_backtest/engine/backtest.py`

## Commandes pour run/test
- `pytest -v`

## Problèmes connus / next steps
- Ajouter tests unitaires pour stratégie + backtest (TP/SL/trailing).
- Implémenter metrics/visualisation + optimisation (Bayesian + walk-forward).
- Valider la cohérence des signaux vs Pine sur données réelles.
