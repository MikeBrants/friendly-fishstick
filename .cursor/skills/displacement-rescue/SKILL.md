---
name: displacement-rescue
description: Sauve un asset PENDING en testant les variants de displacement d26/d52/d65/d78. Utiliser quand un asset échoue les guards avec le displacement standard, quand WFE est proche du seuil (0.5-0.6), ou en Phase 3A du workflow après validation FAIL.
---

# Displacement Rescue - Phase 3A

## Quand Utiliser
- Asset en status PENDING après validation Phase 2
- WFE entre 0.5 et 0.6 (proche du seuil)
- Guards FAIL avec displacement=52 standard
- Casey assigne Phase 3A rescue
- Avant de passer à Phase 4 (filter grid)

## Prérequis
- Asset a déjà été validé en Phase 2 (guards FAIL)
- Données disponibles dans `data/`
- Run post-2026-01-22 12H00 (bug TP fixé)

## Contexte Displacement

| Type | Valeur | Assets typiques | Caractéristique |
|------|--------|-----------------|-----------------|
| Fast (meme) | 26 | DOGE, JOE, SHIB, PEPE | Volatilité haute, cycles courts |
| Standard | 52 | BTC, ETH, majeurs | Baseline par défaut |
| Custom | 65 | OSMO | Validé empiriquement |
| Slow (L2) | 78 | OP, MINA, infrastructure | Cycles longs |

## Instructions

### Étape 1: Identifier les Candidats
```bash
# Vérifier assets PENDING dans project-state.md
grep -E "PENDING|guards.*FAIL" status/project-state.md
```

### Étape 2: Lancer le Rescue (méthode automatique)
```bash
python scripts/run_displacement_grid.py --assets ASSET_NAME
```

Ce script teste automatiquement d26, d39, d52, d65, d78.

### Étape 3: OU Lancer manuellement chaque variant

**Test d26 (fast) :**
```bash
python scripts/run_full_pipeline.py \
  --assets ASSET_NAME \
  --fixed-displacement 26 \
  --trials-atr 300 --trials-ichi 300 \
  --enforce-tp-progression --run-guards \
  --workers 1 \
  --output-prefix rescue_d26_ASSET_NAME
```

**Test d78 (slow) :**
```bash
python scripts/run_full_pipeline.py \
  --assets ASSET_NAME \
  --fixed-displacement 78 \
  --trials-atr 300 --trials-ichi 300 \
  --enforce-tp-progression --run-guards \
  --workers 1 \
  --output-prefix rescue_d78_ASSET_NAME
```

### Étape 4: Analyser les Résultats
```python
import pandas as pd
from glob import glob

# Charger résultats rescue
results = []
for f in glob("outputs/rescue_d*_ASSET_NAME*.csv"):
    df = pd.read_csv(f)
    results.append(df)

if results:
    all_results = pd.concat(results)
    # Filtrer ceux qui passent les guards
    passed = all_results[all_results['all_guards_pass'] == True]
    print("Variants qui PASS:")
    print(passed[['asset', 'displacement', 'oos_sharpe', 'wfe', 'oos_trades']])
```

### Étape 5: Sélectionner le Meilleur

**Critères de sélection (dans l'ordre) :**
1. `all_guards_pass == True` (obligatoire)
2. `oos_trades >= 60` (obligatoire)
3. Maximiser `oos_sharpe`
4. En cas d'égalité, préférer d52 (standard)

```python
if len(passed) > 0:
    best = passed.sort_values('oos_sharpe', ascending=False).iloc[0]
    print(f"Meilleur variant: d{best['displacement']} avec Sharpe={best['oos_sharpe']:.2f}")
else:
    print("Aucun variant ne passe → Phase 4 (filter grid)")
```

### Étape 6: Mettre à Jour le Status

**Si rescue réussi :**
```markdown
# Dans comms/jordan-dev.md
HHMM DONE jordan-dev -> casey-quant:
Asset: ASSET_NAME
Phase: 3A (displacement rescue)
Result: SUCCESS
Best displacement: d[XX]
Metrics: Sharpe=[X.XX], WFE=[X.XX], Trades=[XXX]
Guards: 7/7 PASS
Action: Ready for PROD validation by Sam
```

**Si rescue échoué :**
```markdown
# Dans comms/jordan-dev.md
HHMM DONE jordan-dev -> casey-quant:
Asset: ASSET_NAME
Phase: 3A (displacement rescue)
Result: FAIL - Aucun variant ne passe
Tested: d26, d52, d78
Action: Proceed to Phase 4 (filter grid)
```

## Output Attendu

Fichier `outputs/displacement_rescue_ASSET.csv` :
```csv
asset,displacement,oos_sharpe,wfe,oos_trades,all_guards_pass,guard002_variance
DOGE,26,2.45,0.71,87,True,6.2
DOGE,52,1.89,0.52,124,False,12.3
DOGE,78,1.62,0.48,65,False,8.9
```

## Troubleshooting

| Problème | Solution |
|----------|----------|
| Tous variants FAIL | Passer à Phase 4 (filter grid) |
| Plusieurs variants PASS | Choisir celui avec meilleur Sharpe |
| d26 PASS mais trades < 60 | Ignorer, sample insuffisant |
| Run timeout | Réduire trials à 200 |

## Escalade
- Si aucun variant ne passe → Utiliser skill `filter-grid`
- Si doute sur sélection → @Alex arbitrage
- Si rescue réussi → @Sam validation guards
- Après validation → @Casey mise à jour project-state.md
