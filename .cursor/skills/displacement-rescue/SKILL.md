---
name: displacement-rescue
description: Sauve un asset PENDING en testant les variants de displacement d26/d52/d65/d78. Utiliser en Phase 3A quand un asset échoue les guards avec le displacement standard, quand WFE est proche du seuil (0.5-0.6), ou après validation FAIL. OBLIGATOIRE avant de bloquer un asset.
---

# Displacement Rescue - Phase 3A

## Quand Utiliser
- Asset en status PENDING après validation Phase 2
- WFE entre 0.5 et 0.6 (proche du seuil)
- Guards FAIL avec displacement=52 standard
- Casey assigne Phase 3A rescue
- **AVANT de passer à Phase 4 (filter grid)**
- **OBLIGATOIRE avant tout blocage définitif**

## Prérequis
- Asset a déjà été validé en Phase 2 (guards FAIL)
- Données disponibles dans `data/`
- Run post-2026-01-22 12H00 UTC (bug TP fixé)
- **IMPORTANT:** Toujours `workers=1` pour reproductibilité

## Contexte Displacement

| Type | Valeur | Assets typiques | Caractéristique |
|------|--------|-----------------|-----------------|
| Fast (meme) | 26 | DOGE, JOE, SHIB, PEPE | Volatilité haute, cycles courts |
| Standard | 52 | BTC, ETH, majeurs | Baseline par défaut |
| Custom | 65 | OSMO | Validé empiriquement |
| Slow (L2) | 78 | OP, MINA, infrastructure | Cycles longs |

**Arbre de décision displacement:**
```
Asset type?
├── Majeur (BTC, ETH) ──────────────> d52
├── L2/Infrastructure (OP, ARB) ────> d78
├── Meme/Fast (DOGE, SHIB, JOE) ───> d26
├── Edge case (OSMO) ───────────────> d65
└── Inconnu ────────────────────────> d52, puis ajuster si WFE < 0.6
```

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

**Test d26 (fast):**
```bash
python scripts/run_full_pipeline.py \
  --assets ASSET_NAME \
  --fixed-displacement 26 \
  --trials-atr 300 --trials-ichi 300 \
  --enforce-tp-progression --run-guards \
  --workers 1 \
  --output-prefix rescue_d26_ASSET_NAME
```

**Test d52 (standard) si pas encore testé:**
```bash
python scripts/run_full_pipeline.py \
  --assets ASSET_NAME \
  --fixed-displacement 52 \
  --trials-atr 300 --trials-ichi 300 \
  --enforce-tp-progression --run-guards \
  --workers 1 \
  --output-prefix rescue_d52_ASSET_NAME
```

**Test d78 (slow):**
```bash
python scripts/run_full_pipeline.py \
  --assets ASSET_NAME \
  --fixed-displacement 78 \
  --trials-atr 300 --trials-ichi 300 \
  --enforce-tp-progression --run-guards \
  --workers 1 \
  --output-prefix rescue_d78_ASSET_NAME
```

**Test d65 (custom, si asset type OSMO-like):**
```bash
python scripts/run_full_pipeline.py \
  --assets ASSET_NAME \
  --fixed-displacement 65 \
  --trials-atr 300 --trials-ichi 300 \
  --enforce-tp-progression --run-guards \
  --workers 1 \
  --output-prefix rescue_d65_ASSET_NAME
```

### Étape 4: Analyser les Résultats
```python
import pandas as pd
from glob import glob

# Charger résultats rescue
results = []
for pattern in ["rescue_d26_*", "rescue_d52_*", "rescue_d65_*", "rescue_d78_*"]:
    for f in glob(f"outputs/{pattern}*_scan*.csv"):
        try:
            df = pd.read_csv(f)
            df['source_file'] = f
            results.append(df)
        except:
            pass

if results:
    all_results = pd.concat(results, ignore_index=True)
    
    # Filtrer ceux qui passent les guards
    # Note: vérifier nom colonne selon output
    if 'all_guards_pass' in all_results.columns:
        passed = all_results[all_results['all_guards_pass'] == True]
    elif 'all_pass' in all_results.columns:
        passed = all_results[all_results['all_pass'] == True]
    else:
        print("Colonnes disponibles:", all_results.columns.tolist())
        passed = pd.DataFrame()
    
    if len(passed) > 0:
        print("✅ Variants qui PASS:")
        print(passed[['asset', 'displacement', 'oos_sharpe', 'wfe', 'oos_trades']].to_string(index=False))
    else:
        print("❌ Aucun variant ne passe → Phase 4 (filter grid)")
else:
    print("Aucun fichier rescue trouvé")
```

### Étape 5: Sélectionner le Meilleur

**Critères de sélection (dans l'ordre):**
1. `all_guards_pass == True` (obligatoire)
2. `oos_trades >= 60` (obligatoire)
3. Maximiser `oos_sharpe`
4. En cas d'égalité, préférer d52 (standard)

```python
if len(passed) > 0:
    best = passed.sort_values('oos_sharpe', ascending=False).iloc[0]
    print(f"✅ Meilleur variant: d{int(best['displacement'])}")
    print(f"   Sharpe: {best['oos_sharpe']:.2f}")
    print(f"   WFE: {best['wfe']:.2f}")
    print(f"   Trades: {int(best['oos_trades'])}")
else:
    print("❌ Aucun variant ne passe → Procéder à Phase 4 (filter grid)")
```

### Étape 6: Mettre à Jour le Status

**Si rescue réussi:**
```markdown
HHMM DONE jordan-dev -> casey-quant:
Asset: ASSET_NAME
Phase: 3A (displacement rescue)
Result: SUCCESS ✅
Best displacement: d[XX]
Metrics: Sharpe=[X.XX], WFE=[X.XX], Trades=[XXX]
Guards: 7/7 PASS
Action: Ready for PROD validation by @Sam
Output: outputs/rescue_d[XX]_ASSET_NAME_*.csv
```

**Si rescue échoué:**
```markdown
HHMM DONE jordan-dev -> casey-quant:
Asset: ASSET_NAME
Phase: 3A (displacement rescue)
Result: FAIL ❌
Tested: d26 (FAIL), d52 (FAIL), d78 (FAIL)
Action: Proceed to Phase 4 (filter grid) - OBLIGATOIRE
Next: Utiliser skill `filter-grid`

⚠️ NE PAS BLOQUER - Workflow rescue non épuisé
```

## ⚠️ WORKFLOW RESCUE OBLIGATOIRE

**Source de vérité:** `docs/WORKFLOW_MULTI_ASSET_SCREEN_VALIDATE_PROD.md`

```
Phase 3A FAIL (tous displacements)
         ↓
    Phase 4 (filter grid) ← OBLIGATOIRE
         ↓
    Si FAIL → EXCLU définitif (justifié)
```

**JAMAIS bloquer après Phase 3A seule!**

## Output Attendu

Fichiers `outputs/rescue_d[XX]_ASSET_*_scan_*.csv`:
```csv
asset,displacement,oos_sharpe,wfe,oos_trades,all_guards_pass,guard002_variance_pct
DOGE,26,2.45,0.71,87,True,6.2
DOGE,52,1.89,0.52,124,False,12.3
DOGE,78,1.62,0.48,65,False,8.9
```

## Troubleshooting

| Problème | Solution |
|----------|----------|
| Tous variants FAIL | **Phase 4 obligatoire** (skill `filter-grid`) |
| Plusieurs variants PASS | Choisir celui avec meilleur Sharpe |
| d26 PASS mais trades < 60 | Ignorer, sample insuffisant |
| Run timeout | Réduire trials à 200 (screening mode) |
| Erreur "data not found" | Lancer `python scripts/download_data.py --assets ASSET` |

## Escalade
- Si aucun variant ne passe → **Utiliser skill `filter-grid`** (OBLIGATOIRE)
- Si doute sur sélection → @Alex arbitrage
- Si rescue réussi → @Sam validation guards
- Après validation 7/7 → @Casey mise à jour project-state.md
- **BLOCKED seulement si:** Phase 3A + Phase 4 toutes deux épuisées
