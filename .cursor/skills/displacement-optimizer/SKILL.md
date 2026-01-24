---
name: displacement-optimizer
description: Optimise les displacement variants (d26/d52/d65/d78) pour les assets en rescue Phase 3A ou optimisation Phase 3B du pipeline FINAL TRIGGER v2.
---

# Displacement Optimizer

## Quand Utiliser
- Utiliser cette skill pour Phase 3A (rescue PENDING → WINNERS)
- Cette skill est utile quand guards FAIL et qu'on veut tester d'autres displacements
- Utiliser pour Phase 3B (optimisation des WINNERS existants)
- Utiliser pour déterminer le meilleur displacement pour un asset

## Variants

| Type | Displacement | Assets typiques |
|------|--------------|-----------------|
| Fast (meme) | 26 | JOE, DOGE |
| Standard | 52 | BTC, ETH, majeurs |
| Slow (L2) | 65-78 | OP, OSMO, MINA |

## Phase 3A: Rescue (PENDING -> WINNERS)

```bash
python scripts/run_displacement_grid.py --assets PENDING_LIST
```

### Logic

```python
DISPLACEMENTS = [26, 39, 52, 65, 78]

def rescue_asset(asset, current_params):
    results = []
    for disp in DISPLACEMENTS:
        params = {**current_params, 'displacement': disp}
        metrics = run_full_validation(asset, params)
        if metrics['all_guards_pass']:
            results.append((disp, metrics))
    
    if results:
        # Prendre le meilleur Sharpe parmi ceux qui passent
        best = max(results, key=lambda x: x[1]['oos_sharpe'])
        return {'status': 'WINNER', 'displacement': best[0], 'metrics': best[1]}
    return {'status': 'PENDING', 'displacement': None}
```

## Phase 3B: Optimization (WINNERS -> meilleur)

```bash
python scripts/run_phase3b_optimization.py --assets WINNERS_LIST
```

### Logic

```python
def optimize_winner(asset, current_params, current_sharpe):
    improvements = []
    for disp in DISPLACEMENTS:
        if disp == current_params['displacement']:
            continue
        params = {**current_params, 'displacement': disp}
        metrics = run_full_validation(asset, params)
        
        # Critère: +10% ET guards pass
        if (metrics['oos_sharpe'] > current_sharpe * 1.10 
            and metrics['all_guards_pass']):
            improvements.append((disp, metrics))
    
    if improvements:
        best = max(improvements, key=lambda x: x[1]['oos_sharpe'])
        return {'action': 'REPLACE', 'new_displacement': best[0]}
    return {'action': 'KEEP', 'displacement': current_params['displacement']}
```

## Output Format

```csv
asset,original_disp,tested_disp,original_sharpe,new_sharpe,improvement_pct,guards_pass,action
OP,52,78,2.14,2.89,35.0,True,REPLACE
DOGE,52,26,1.89,2.45,29.6,True,REPLACE
ETH,52,52,2.09,2.09,0.0,True,KEEP
```

## Critère de remplacement Phase 3B

```python
if new_sharpe > old_sharpe * 1.10 and all_guards_pass:
    use_new_displacement = True
```
