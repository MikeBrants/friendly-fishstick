---
name: filter-grid-analyzer
description: Analyse et teste la grille de 12 combinaisons de filtres (Phase 4) pour les assets PENDING après échec du displacement rescue.
---

# Filter Grid Analyzer

## Quand Utiliser
- Utiliser cette skill pour Phase 4 quand Phase 3A (displacement rescue) a échoué
- Cette skill est utile pour trouver la meilleure combinaison de filtres
- Utiliser pour tester les 12 modes de filtrage
- Utiliser pour déterminer si un asset peut être sauvé avec des filtres

## Commande

```bash
python scripts/run_filter_grid.py --assets PENDING_LIST
```

## 12 Combinaisons

```python
FILTER_MODES = [
    'baseline',           # ichimoku only
    'light_kama',         # ichimoku + kama_oscillator
    'light_distance',     # ichimoku + distance_filter
    'light_volume',       # ichimoku + volume_filter
    'light_regression',   # ichimoku + regression_cloud
    'medium_distance_volume',  # ichimoku + distance + volume (WINNER ETH)
    'medium_kama_distance',    # ichimoku + kama + distance
    'medium_kama_volume',      # ichimoku + kama + volume
    'moderate',           # 5 filtres
    'conservative',       # 7 filtres (tous + strict)
]
```

## Analysis Logic

```python
def analyze_filter_grid(asset, base_params):
    results = []
    for mode in FILTER_MODES:
        params = {**base_params, 'filter_mode': mode}
        metrics = run_backtest_with_guards(asset, params)
        results.append({
            'asset': asset,
            'filter_mode': mode,
            'oos_sharpe': metrics['oos_sharpe'],
            'wfe': metrics['wfe'],
            'trades': metrics['oos_trades'],
            'guards_pass': metrics['all_guards_pass'],
        })
    
    # Trouver le meilleur mode qui passe les guards
    valid = [r for r in results if r['guards_pass'] and r['trades'] >= 60]
    if valid:
        best = max(valid, key=lambda x: x['oos_sharpe'])
        return best
    return None
```

## Output Format

```csv
asset,filter_mode,oos_sharpe,wfe,oos_trades,guards_pass,selected
AVAX,medium_distance_volume,2.34,0.71,87,True,True
AVAX,baseline,1.89,0.52,124,False,False
```

## Critères de sélection
1. `guards_pass == True`
2. `oos_trades >= 60`
3. Maximiser `oos_sharpe`
4. En cas d'égalité, préférer mode plus simple (moins de filtres)

## Workflow complet

```
Phase 2 (guards FAIL)
    ↓
Phase 3A (displacement rescue) - FAIL
    ↓
Phase 4 (filter grid) ← UTILISER CETTE SKILL
    ↓
Si 1+ config PASS → PROD
Si ALL FAIL → EXCLU DÉFINITIF
```
