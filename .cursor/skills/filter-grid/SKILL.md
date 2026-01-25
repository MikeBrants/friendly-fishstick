---
name: filter-grid
description: Teste 12 combinaisons de filtres (baseline, light_kama, light_distance, light_volume, light_regression, medium_distance_volume, moderate, conservative) pour sauver un asset après échec du displacement rescue. Utiliser en Phase 4 quand Phase 3A a échoué, ou quand guard002 (sensitivity) FAIL avec variance >15%. DERNIÈRE CHANCE avant EXCLU.
---

# Filter Grid - Phase 4

## Quand Utiliser
- Phase 3A (displacement rescue) a échoué pour cet asset
- Guard002 (sensitivity variance) FAIL avec variance >15%
- Asset prioritaire qu'on veut sauver avant EXCLU
- Casey assigne Phase 4
- **DERNIÈRE ÉTAPE avant blocage définitif**

## Prérequis
- Asset a échoué Phase 3A (displacement rescue)
- Données disponibles dans `data/`
- Meilleur displacement de Phase 3A identifié (même si FAIL)
- **IMPORTANT:** Toujours `workers=1` pour reproductibilité

## Les 12 Modes de Filtrage

| Mode | Filtres actifs | Cas d'usage |
|------|----------------|-------------|
| `baseline` | ichimoku only | Référence, pas de filtre |
| `light_kama` | ichimoku + kama_oscillator | Momentum léger |
| `light_distance` | ichimoku + distance_filter | Distance au cloud |
| `light_volume` | ichimoku + volume_filter | Volume léger |
| `light_regression` | ichimoku + regression_cloud | Trend regression |
| `medium_kama_distance` | ichimoku + kama + distance | Combo momentum/distance |
| `medium_kama_volume` | ichimoku + kama + volume | Combo momentum/volume |
| `medium_kama_regression` | ichimoku + kama + regression | Combo momentum/trend |
| `medium_distance_volume` | ichimoku + distance + volume | **WINNER ETH** ⭐ |
| `moderate` | 5 filtres (tous sauf strict) | Filtrage moyen |
| `strict_ichi` | ichimoku strict (17 cond) | Strict sans autres filtres |
| `conservative` | 6 filtres + strict | Maximum filtrage, dernier recours |

**Ordre de test recommandé:**
1. `medium_distance_volume` (winner ETH, tester en premier)
2. `light_kama`
3. `light_distance`
4. `moderate`
5. `conservative` (dernier recours)

## Instructions

### Étape 1: Identifier le Meilleur Displacement
```bash
# Récupérer le meilleur disp de Phase 3A (même si FAIL)
# Prendre celui avec le meilleur Sharpe
ls outputs/rescue_d*_ASSET_NAME*.csv
```

Utiliser le displacement avec le meilleur Sharpe (même si guards FAIL).

### Étape 2: Lancer le Filter Grid (méthode automatique)
```bash
python scripts/run_filter_rescue.py ASSET_NAME \
  --trials 300 \
  --workers 1
```

### Étape 3: OU Tester manuellement les modes prioritaires

**Mode recommandé #1 (winner ETH):**
```bash
python scripts/run_full_pipeline.py \
  --assets ASSET_NAME \
  --optimization-mode medium_distance_volume \
  --fixed-displacement BEST_DISP \
  --trials-atr 300 --trials-ichi 300 \
  --enforce-tp-progression --run-guards \
  --workers 1 \
  --output-prefix filter_medium_dist_vol_ASSET_NAME
```

**Si échec, tester light_kama:**
```bash
python scripts/run_full_pipeline.py \
  --assets ASSET_NAME \
  --optimization-mode light_kama \
  --fixed-displacement BEST_DISP \
  --trials-atr 300 --trials-ichi 300 \
  --enforce-tp-progression --run-guards \
  --workers 1 \
  --output-prefix filter_light_kama_ASSET_NAME
```

**Si échec, tester moderate:**
```bash
python scripts/run_full_pipeline.py \
  --assets ASSET_NAME \
  --optimization-mode moderate \
  --fixed-displacement BEST_DISP \
  --trials-atr 300 --trials-ichi 300 \
  --enforce-tp-progression --run-guards \
  --workers 1 \
  --output-prefix filter_moderate_ASSET_NAME
```

**Dernier recours, conservative:**
```bash
python scripts/run_full_pipeline.py \
  --assets ASSET_NAME \
  --optimization-mode conservative \
  --fixed-displacement BEST_DISP \
  --trials-atr 300 --trials-ichi 300 \
  --enforce-tp-progression --run-guards \
  --workers 1 \
  --output-prefix filter_conservative_ASSET_NAME
```

### Étape 4: Analyser les Résultats
```python
import pandas as pd
from glob import glob

# Charger résultats filter grid
results = []
for f in glob("outputs/filter_*_ASSET_NAME*_scan*.csv"):
    try:
        df = pd.read_csv(f)
        # Extraire filter mode du nom de fichier
        df['source_file'] = f
        results.append(df)
    except:
        pass

if results:
    all_results = pd.concat(results, ignore_index=True)
    
    # Vérifier colonnes disponibles
    pass_col = 'all_guards_pass' if 'all_guards_pass' in all_results.columns else 'all_pass'
    trades_col = 'oos_trades' if 'oos_trades' in all_results.columns else 'trades'
    
    # Filtrer ceux qui passent
    valid = all_results[
        (all_results[pass_col] == True) & 
        (all_results[trades_col] >= 60)
    ]
    
    if len(valid) > 0:
        # Trier par Sharpe
        valid_sorted = valid.sort_values('oos_sharpe', ascending=False)
        best = valid_sorted.iloc[0]
        print(f"✅ Meilleur mode trouvé!")
        print(f"   File: {best['source_file']}")
        print(f"   Sharpe: {best['oos_sharpe']:.2f}")
        print(f"   WFE: {best['wfe']:.2f}")
        print(f"   Trades: {int(best[trades_col])}")
    else:
        print("❌ Aucun mode ne passe → Asset EXCLU DÉFINITIF")
else:
    print("Aucun fichier filter grid trouvé")
```

### Étape 5: Sélectionner le Meilleur

**Critères de sélection (dans l'ordre):**
1. `guards_pass == True` (obligatoire)
2. `oos_trades >= 60` (obligatoire)
3. Maximiser `oos_sharpe`
4. En cas d'égalité, préférer mode plus simple (moins de filtres)

**Ordre de préférence des modes (à Sharpe égal):**
1. `baseline` (si PASS)
2. `light_*` (kama, distance, volume, regression)
3. `medium_distance_volume`
4. `moderate`
5. `conservative` (dernier recours)

### Étape 6: Documenter le Résultat

**Si filter grid réussi:**
```markdown
HHMM DONE jordan-dev -> casey-quant:
Asset: ASSET_NAME
Phase: 4 (filter grid)
Result: SUCCESS ✅
Filter mode: medium_distance_volume
Displacement: d52
Metrics: Sharpe=[X.XX], WFE=[X.XX], Trades=[XXX]
Guards: 7/7 PASS
Action: Ready for PROD validation by @Sam
Output: outputs/filter_*_ASSET_NAME_*.csv
```

**Si filter grid échoué:**
```markdown
HHMM DONE jordan-dev -> casey-quant:
Asset: ASSET_NAME
Phase: 4 (filter grid)
Result: FAIL ❌
Tested: 5+ filter modes
Workflow: Phase 3A ❌ + Phase 4 ❌ = ÉPUISÉ

**Verdict:** EXCLU DÉFINITIF (justifié)
Reason: Workflow rescue complet épuisé
        Phase 3A: d26/d52/d78 tous FAIL
        Phase 4: filter grid épuisé

Action: @Casey update project-state.md → EXCLU
```

## ⚠️ BLOCAGE JUSTIFIÉ

**Après Phase 4 FAIL, le blocage est JUSTIFIÉ car:**
- Phase 3A (displacement rescue) épuisée
- Phase 4 (filter grid) épuisée
- Workflow rescue complet tenté
- Asset n'a pas d'edge exploitable

**Format verdict EXCLU:**
```markdown
ASSET: [NAME]
Status: EXCLU DÉFINITIF

Workflow exhausted:
- [x] Phase 2 validation: FAIL
- [x] Phase 3A displacement: d26 FAIL, d52 FAIL, d78 FAIL
- [x] Phase 4 filter grid: 5+ modes FAIL

Conclusion: No exploitable edge with current strategy
```

## Output Attendu

Fichier `outputs/filter_grid_ASSET_YYYYMMDD.csv`:
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
| Tous modes FAIL | EXCLU DÉFINITIF (workflow épuisé, justifié) |
| Trades < 60 sur tous modes | BLOCKED (données insuffisantes) |
| conservative seul PASS | Acceptable mais surveiller en live |
| Run très long | Réduire trials à 200 |
| guard002 toujours >15% | Essayer `conservative` (max filtrage) |

## Escalade
- Si tous modes FAIL → @Casey verdict EXCLU DÉFINITIF (justifié)
- Si doute entre modes → @Alex arbitrage
- Si filter grid PASS → @Sam validation guards finale
