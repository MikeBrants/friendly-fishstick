---
name: filter-grid
description: Teste 12 combinaisons de filtres (baseline, kama, distance, volume, moderate, conservative) pour sauver un asset après échec du displacement rescue. Utiliser en Phase 4 quand Phase 3A a échoué, ou quand guard002 (sensitivity) FAIL avec variance >10%.
---

# Filter Grid - Phase 4

## Quand Utiliser
- Phase 3A (displacement rescue) a échoué pour cet asset
- Guard002 (sensitivity variance) FAIL avec variance >10%
- Asset prioritaire qu'on veut sauver avant BLOCKED
- Casey assigne Phase 4

## Prérequis
- Asset a échoué Phase 3A (displacement rescue)
- Données disponibles dans `data/`
- Meilleur displacement de Phase 3A identifié (même si FAIL)

## Les 12 Modes de Filtrage

| Mode | Filtres actifs | Cas d'usage |
|------|----------------|-------------|
| `baseline` | ichimoku only | Référence, pas de filtre |
| `light_kama` | ichimoku + kama_oscillator | Momentum léger |
| `light_distance` | ichimoku + distance_filter | Distance au cloud |
| `light_volume` | ichimoku + volume_filter | Volume léger |
| `light_regression` | ichimoku + regression_cloud | Trend regression |
| `medium_distance_volume` | ichimoku + distance + volume | **WINNER ETH** |
| `medium_kama_distance` | ichimoku + kama + distance | Combo momentum/distance |
| `medium_kama_volume` | ichimoku + kama + volume | Combo momentum/volume |
| `moderate` | 5 filtres | Filtrage moyen |
| `conservative` | 7 filtres (tous + strict) | Maximum filtrage |

## Instructions

### Étape 1: Identifier le Meilleur Displacement
```bash
# Récupérer le meilleur disp de Phase 3A (même si FAIL)
grep "displacement" outputs/rescue_d*_ASSET*.csv | head -5
```

Utiliser le displacement avec le meilleur Sharpe (même si guards FAIL).

### Étape 2: Lancer le Filter Grid
```bash
python scripts/run_filter_grid.py \
  --asset ASSET_NAME \
  --displacement BEST_DISP \
  --workers 1 \
  --output-prefix filter_grid_ASSET_NAME
```

### Étape 3: OU Tester manuellement les modes prioritaires

**Mode recommandé en premier (winner ETH) :**
```bash
python scripts/run_full_pipeline.py \
  --assets ASSET_NAME \
  --optimization-mode medium_distance_volume \
  --fixed-displacement BEST_DISP \
  --trials-atr 300 --trials-ichi 300 \
  --enforce-tp-progression --run-guards \
  --workers 1
```

**Si échec, tester moderate :**
```bash
python scripts/run_full_pipeline.py \
  --assets ASSET_NAME \
  --optimization-mode moderate \
  --fixed-displacement BEST_DISP \
  --trials-atr 300 --trials-ichi 300 \
  --enforce-tp-progression --run-guards \
  --workers 1
```

### Étape 4: Analyser les Résultats
```python
import pandas as pd
from glob import glob

# Charger résultats filter grid
results = pd.read_csv(sorted(glob("outputs/filter_grid_ASSET*.csv"))[-1])

# Filtrer ceux qui passent
valid = results[(results['guards_pass'] == True) & (results['oos_trades'] >= 60)]

if len(valid) > 0:
    # Trier par Sharpe, puis par simplicité (moins de filtres)
    valid_sorted = valid.sort_values(['oos_sharpe', 'filter_mode'], ascending=[False, True])
    best = valid_sorted.iloc[0]
    print(f"Meilleur mode: {best['filter_mode']} avec Sharpe={best['oos_sharpe']:.2f}")
else:
    print("Aucun mode ne passe → Asset EXCLU DÉFINITIF")
```

### Étape 5: Sélectionner le Meilleur

**Critères de sélection (dans l'ordre) :**
1. `guards_pass == True` (obligatoire)
2. `oos_trades >= 60` (obligatoire)
3. Maximiser `oos_sharpe`
4. En cas d'égalité, préférer mode plus simple (moins de filtres)

**Ordre de préférence des modes :**
1. baseline (si PASS)
2. light_* (kama, distance, volume)
3. medium_distance_volume
4. moderate
5. conservative (dernier recours)

### Étape 6: Documenter le Résultat

**Si filter grid réussi :**
```markdown
# Dans comms/jordan-dev.md
HHMM DONE jordan-dev -> casey-quant:
Asset: ASSET_NAME
Phase: 4 (filter grid)
Result: SUCCESS
Filter mode: medium_distance_volume
Displacement: d52
Metrics: Sharpe=[X.XX], WFE=[X.XX], Trades=[XXX]
Guards: 7/7 PASS
Action: Ready for PROD validation by Sam
```

**Si filter grid échoué :**
```markdown
# Dans comms/jordan-dev.md
HHMM DONE jordan-dev -> casey-quant:
Asset: ASSET_NAME
Phase: 4 (filter grid)
Result: FAIL - Aucun mode ne passe
Tested: 12 modes × 1 displacement
Action: Asset EXCLU DÉFINITIF
Reason: Workflow rescue épuisé (Phase 3A + Phase 4)
```

## Output Attendu

Fichier `outputs/filter_grid_ASSET_YYYYMMDD.csv` :
```csv
asset,filter_mode,displacement,oos_sharpe,wfe,oos_trades,guards_pass,selected
AVAX,medium_distance_volume,52,2.34,0.71,87,True,True
AVAX,baseline,52,1.89,0.52,124,False,False
AVAX,moderate,52,2.12,0.65,72,True,False
AVAX,conservative,52,1.45,0.58,45,False,False
```

## Troubleshooting

| Problème | Solution |
|----------|----------|
| Tous modes FAIL | Asset EXCLU DÉFINITIF (workflow épuisé) |
| Trades < 60 sur tous modes | Asset BLOCKED (données insuffisantes) |
| conservative seul PASS | Acceptable mais surveiller en live |
| Run très long | Réduire trials à 200 |

## Escalade
- Si tous modes FAIL → @Casey pour verdict EXCLU DÉFINITIF
- Si doute entre modes → @Alex arbitrage
- Si filter grid PASS → @Sam validation guards finale
- Après EXCLU → @Riley documentation dans VALIDATION_LOG.md
