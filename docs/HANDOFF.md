# Handoff

## Objectif
Implémenter la stratégie FINAL TRIGGER v2 + moteur de backtest multi-TP, puis préparer les prochaines étapes (metrics/optimisation).

## Plan actuel
- [x] Scanner le repo et confirmer la structure
- [x] Poser l'ossature des modules/fichiers
- [x] Implémenter la couche data (fetcher/cache/preprocess)
- [x] Indicateurs core + tests unitaires de base
- [x] Stratégie Final Trigger + moteur de backtest + position manager multi-TP
- [x] Rendre l'ordre intra-bar et le sizing configurables + tests associés
- [x] Aligner compounding avec coûts + scénarios backtest multi-legs
- [x] Tests `sizing_mode="equity"` (compounding net of costs)
- [ ] Implémenter `analysis/metrics.py` (Sharpe, Sortino, Calmar, Max DD, Win Rate, Expectancy)
- [ ] Implémenter `analysis/visualization.py` (equity curve, drawdown chart via Plotly)
- [ ] Implémenter `optimization/bayesian.py` (Optuna TPE avec pruning)
- [ ] Implémenter `optimization/walk_forward.py` (IS/OOS split, stitching)
- [ ] Ajouter `examples/run_backtest.py` (script de démo end-to-end)
- [ ] Valider la cohérence des signaux vs Pine sur données réelles

## Décisions prises + raisons
- Reproduction fidèle de la logique Pine (Puzzle + Grace + 5in1 + Ichimoku externe) pour éviter des écarts de signaux.
- Manager multi-TP avec trailing (SL -> BE après TP1, SL -> TP1 après TP2) pour refléter le comportement visuel Pine.
- Backtest initial simple (pnl agrégé par exit_time) pour itérer vite avant metrics/optimisation.
- Ajout d'options `sizing_mode` (fixed/equity) et `intrabar_order` (stop_first/tp_first) pour expliciter l'hypothèse intra-bar.
- Coûts appliqués à la sortie (net_pnl) pour un compounding cohérent en mode `equity`.
- Tests multi-scénarios (long/short, 3 legs, trailing, compounding) pour verrouiller le comportement du moteur.

## Fichiers modifiés
- `.gitignore`
- `crypto_backtest/engine/backtest.py`
- `crypto_backtest/engine/position_manager.py`
- `tests/test_indicators.py`
- `tests/test_backtest.py`

## Commandes pour run/test
- `pytest -v`

## Next steps détaillés

### 1. Metrics (`analysis/metrics.py`)
Créer un module qui calcule sur un `BacktestResult`:
- **Performance**: Total Return, CAGR, Sharpe, Sortino, Calmar
- **Risk**: Max Drawdown (%), Max DD Duration, VaR 95%, CVaR 95%
- **Trading**: Win Rate, Profit Factor, Expectancy (R-multiple moyen), Avg Win/Loss
- **Distribution**: Stats par heure UTC (6 blocs de 4h), stats par jour de semaine

```python
# Interface suggérée
def compute_metrics(result: BacktestResult, risk_free_rate: float = 0.0) -> dict:
    ...
```

### 2. Visualization (`analysis/visualization.py`)
- Equity curve (Plotly line chart)
- Drawdown chart (area chart)
- Monthly returns heatmap
- Trade distribution (histogram par R-multiple)

### 3. Optimisation Bayésienne (`optimization/bayesian.py`)
- Wrapper Optuna avec TPE sampler
- Pruning via `trial.report()` + `trial.should_prune()` sur Sharpe intermédiaire
- Paramètres à optimiser: len (MAMA), TS_D1, KS_D1, fast_period, slow_period, adNormPeriod, slMult, tp1Mult, tp2Mult, tp3Mult

### 4. Walk-Forward (`optimization/walk_forward.py`)
- Config: IS=180 jours, OOS=30 jours, step=30 jours
- Pour chaque fenêtre: optimise sur IS, teste sur OOS
- Combine tous les OOS pour métriques "réelles"
- Calcule degradation ratio (OOS/IS) et efficiency ratio

### 5. Example script (`examples/run_backtest.py`)
```python
from crypto_backtest.data.fetcher import DataFetcher
from crypto_backtest.strategies.final_trigger import FinalTriggerStrategy
from crypto_backtest.engine.backtest import VectorizedBacktester, BacktestConfig
from crypto_backtest.analysis.metrics import compute_metrics

fetcher = DataFetcher("binance")
data = fetcher.fetch_ohlcv("BTC/USDT", "1h", days=365)

strategy = FinalTriggerStrategy(FinalTriggerParams())
config = BacktestConfig(sizing_mode="equity", intrabar_order="stop_first")
backtester = VectorizedBacktester(config)
result = backtester.run(data, strategy)

metrics = compute_metrics(result)
print(f"Sharpe: {metrics['sharpe_ratio']:.2f}")
print(f"Max DD: {metrics['max_drawdown']:.1%}")
```

## Problèmes connus
- `crypto_backtest/indicators/atr.py` référencé dans `final_trigger.py` mais absent du repo (à créer ou corriger l'import)
- Ichimoku `shift(25/50)` hardcodés dans conditions, non liés à `IchimokuConfig.displacement`
