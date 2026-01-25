---
name: guards-runner
description: Exécute les 7 guards de validation anti-overfitting (WFE, Monte Carlo, sensitivity, bootstrap, top10, stress, regime) sur un asset crypto. Utiliser après un backtest pour valider avant PROD, quand Casey demande une validation, ou pour vérifier l'overfitting après optimisation Optuna.
---

# Guards Runner - Validation Anti-Overfitting

## Quand Utiliser
- Après un run de backtest pour valider les résultats
- Avant de passer un asset en PRODUCTION
- Quand Casey demande une validation guards
- Pour vérifier l'overfitting après optimisation Optuna
- Quand Sam doit auditer des résultats existants

## Prérequis
- Fichier `outputs/multiasset_scan*.csv` existe (résultats backtest)
- Python environment activé avec dépendances
- Run post-2026-01-22 12H00 UTC (bug TP fixé)
- **IMPORTANT:** Run avec `workers=1` pour reproductibilité

## Instructions

### Étape 1: Lancer les Guards
```bash
python scripts/run_guards_multiasset.py --assets ASSET_NAME
```

Pour plusieurs assets:
```bash
python scripts/run_guards_multiasset.py --assets BTC ETH SOL
```

**Ou via le pipeline complet (recommandé):**
```bash
python scripts/run_full_pipeline.py \
  --assets ASSET_NAME \
  --workers 1 \
  --trials-atr 300 --trials-ichi 300 \
  --enforce-tp-progression \
  --run-guards \
  --overfit-trials 150
```

### Étape 2: Vérifier les Seuils (7 Guards OBLIGATOIRES)

| Guard | ID | Seuil | PASS si | Action si FAIL |
|-------|:---|-------|---------|----------------|
| WFE | - | ≥0.6 | OOS/IS ratio suffisant | Phase 3A rescue |
| MC p-value | guard001 | <0.05 | Edge statistiquement significatif | Phase 3A rescue |
| Sensitivity | guard002 | <15% | Params stables (±2% perturbation) | Phase 4 filter grid |
| Bootstrap CI | guard003 | >1.0 | Sharpe robuste (95% CI) | Phase 3A rescue |
| Top10 trades | guard005 | <40% | Pas outlier-dependent | BLOCKED (données insuffisantes) |
| Stress Sharpe | guard006 | >1.0 | Rentable sous stress (fees 1.5x) | Phase 3A rescue |
| Regime mismatch | guard007 | ≤1 | Max 1 régime à Sharpe négatif | Phase 3A rescue |

**Seuils additionnels:**

| Paramètre | Seuil | Action si FAIL |
|-----------|-------|----------------|
| Min trades OOS | ≥60 | BLOCKED (données insuffisantes) |
| Min bars IS | ≥8000 | BLOCKED (données insuffisantes) |
| OOS Sharpe | >1.0 (target >2.0) | BLOCKED si <0.8 |
| TP progression | TP1<TP2<TP3, gap≥0.5 | REJECT run (relancer avec `--enforce-tp-progression`) |

**Résultats suspects (challenger):**

| Indicateur | Valeur | Action |
|------------|--------|--------|
| Sharpe élevé | >4.0 | Demander réconciliation avant validation |
| WFE élevé | >2.0 | Vérifier overfitting |
| MaxDD faible | <1% | Vérifier calcul |

### Étape 3: Analyser les Résultats
```python
import pandas as pd
from glob import glob

# Charger derniers résultats guards
guards = pd.read_csv(sorted(glob("outputs/multiasset_guards_summary*.csv"))[-1])

for _, row in guards.iterrows():
    status = '✅ PASS' if row['all_pass'] else '❌ FAIL'
    print(f"{row['asset']}: {status}")
    print(f"  WFE: {row.get('wfe', 'N/A')}")
    print(f"  MC p-value: {row.get('guard001_pvalue', row.get('mc_pvalue', 'N/A'))}")
    print(f"  Sensitivity: {row.get('guard002_variance_pct', 'N/A')}%")
    print(f"  Bootstrap CI: {row.get('guard003_ci_lower', row.get('bootstrap_ci_lower', 'N/A'))}")
```

### Étape 4: Vérifier TP Progression
```python
# Charger scan pour vérifier TP
scan = pd.read_csv(sorted(glob("outputs/multiasset_scan*.csv"))[-1])

for _, row in scan.iterrows():
    tp1, tp2, tp3 = row['tp1_mult'], row['tp2_mult'], row['tp3_mult']
    gap1, gap2 = tp2 - tp1, tp3 - tp2
    valid = tp1 < tp2 < tp3 and gap1 >= 0.5 and gap2 >= 0.5
    print(f"{row['asset']}: TP1={tp1:.2f} < TP2={tp2:.2f} < TP3={tp3:.2f}")
    print(f"  Gaps: {gap1:.2f}, {gap2:.2f} → {'✅ PASS' if valid else '❌ FAIL'}")
```

### Étape 5: Actions selon Résultat

| Résultat | Status | Action |
|----------|--------|--------|
| **7/7 PASS** | PROD ready | @Sam validation → @Casey mise à jour project-state |
| **6/7 PASS** | PENDING | Phase 3A (displacement rescue) |
| **<6/7 PASS** | PENDING | Phase 3A puis Phase 4 si nécessaire |
| **Top10 >40% ou Trades<60** | BLOCKED | Données insuffisantes |
| **Sharpe <0.8** | BLOCKED | Performance trop faible |

## ⚠️ WORKFLOW RESCUE OBLIGATOIRE

**Source de vérité:** `docs/WORKFLOW_MULTI_ASSET_SCREEN_VALIDATE_PROD.md`

```
Guards FAIL → Phase 3A (displacement rescue) → Phase 4 (filter grid) → EXCLU
                    ↓ si PASS                        ↓ si PASS
                   PROD                              PROD
```

**JAMAIS bloquer un asset sans épuiser le workflow rescue!**

## Output Attendu

Fichier `outputs/multiasset_guards_summary_YYYYMMDD_HHMMSS.csv`:
```csv
asset,all_pass,wfe,guard001_pvalue,guard002_variance_pct,guard003_ci_lower,guard005_top10_pct,guard006_stress1_sharpe,guard007_regime_mismatch
BTC,True,1.23,0.003,4.98,1.84,22.6,1.52,0
ETH,True,0.82,0.012,7.21,1.42,31.2,1.31,1
SOL,False,0.54,0.089,12.3,0.91,45.1,0.87,2
```

## Format Communication (@Sam → @Casey)

### Guards PASS (7/7)
```
HHMM GUARDS sam-qa -> casey-quant:
Asset: [ASSET] | Run: YYYYMMDD_HHMMSS (post-fix ✓)

| Guard | Seuil | Valeur | Status |
|-------|-------|--------|--------|
| WFE | ≥0.6 | [X.XX] | ✅ |
| MC p-value | <0.05 | [X.XXX] | ✅ |
| Sensitivity | <15% | [X.X%] | ✅ |
| Bootstrap CI | >1.0 | [X.XX] | ✅ |
| Top10 | <40% | [XX%] | ✅ |
| Stress Sharpe | >1.0 | [X.XX] | ✅ |
| Regime | ≤1 | [X] | ✅ |

TP: [X.X] < [X.X] < [X.X] ✅

Verdict: **7/7 PASS** → Recommend PROD
```

### Guards FAIL (<7/7)
```
HHMM GUARDS sam-qa -> casey-quant:
Asset: [ASSET] | Run: YYYYMMDD_HHMMSS (post-fix ✓)

Verdict: **X/7 PASS**
Failed: [guard002 (11.2%), ...]

**Recommendation:** PENDING → Phase 3A (displacement rescue)
Rationale: Workflow rescue non épuisé
Next: @Jordan execute Phase 3A

⚠️ NE PAS BLOQUER - Utiliser skill `displacement-rescue`
```

## Troubleshooting

| Problème | Solution |
|----------|----------|
| `guard002 FAIL` (sensitivity >10%) | Phase 4 filter grid (`medium_distance_volume`) |
| `guard001 FAIL` (MC p >0.05) | Plus de trials (300) ou données |
| `guard005 FAIL` (top10 >40%) | BLOCKED (outlier-dependent) |
| `wfe < 0.6` proche (0.5-0.6) | Phase 3A displacement rescue |
| Résultats pré-fix | REJETER, relancer avec `--enforce-tp-progression` |

## Escalade
- Si guard borderline (ex: variance 13-16%) → @Alex arbitrage seuil
- Si résultat suspect (Sharpe >4, WFE >2) → Réconciliation avant validation
- Si guards FAIL → **Utiliser skill `displacement-rescue`** (PAS bloquer)
- Si Phase 3A+4 épuisées → @Casey verdict EXCLU définitif
