# Handoff

## Objectif
Implémenter les indicateurs core (MAMA/FAMA/KAMA, Ichimoku externe, Five-in-One) en Python à partir du Pine Script FINAL TRIGGER v2.

## Plan actuel
- [x] Scanner le repo et confirmer la structure
- [x] Poser l’ossature des modules/fichiers
- [x] Implémenter la couche data (fetcher/cache/preprocess)
- [ ] Ajouter des tests unitaires pour les indicateurs
- [ ] Implémenter la stratégie Final Trigger + moteur de backtest + position manager
- [ ] Ajouter métriques/visualisation + optimisation (Bayesian, walk-forward) + example run

## Décisions prises + raisons
- Implémentation MESA/MAMA/FAMA et KAMA basée sur les formules Pine Script pour coller au comportement original.
- Ichimoku stocke le dernier calcul (compute) et réutilise les lignes pour les conditions bullish/bearish afin d’éviter des recalculs incohérents.
- Five-in-One expose les toggles et paramètres 5in1 (Ichimoku strict/light, périodes) pour rester fidèle à la config Pine Script.

## Fichiers modifiés
- `crypto_backtest/indicators/mama_fama_kama.py`
- `crypto_backtest/indicators/ichimoku.py`
- `crypto_backtest/indicators/five_in_one.py`

## Commandes pour run/test
- Pas de tests ajoutés/exécutés pour l’instant.

## Problèmes connus / next steps
- Ajouter des tests unitaires vs valeurs Pine Script pour MAMA/KAMA/Ichimoku/5in1.
- Valider les signaux strict/light Ichimoku 5in1 sur données réelles.
- Optimiser la performance (regression cloud et boucles) si nécessaire.
