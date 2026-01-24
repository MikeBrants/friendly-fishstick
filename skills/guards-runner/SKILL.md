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
- Run post-2026-01-22 12H00 (bug TP fixé)

## Instructions

### Étape 1: Lancer les Guards
```bash
python scripts/run_guards_multiasset.py --assets ASSET_NAME --workers 6
```

Pour plusieurs assets :
```bash
python scripts/run_guards_multiasset.py --assets BTC ETH SOL --workers 6
```

### Étape 2: Vérifier les Seuils

| Guard | ID | Seuil | PASS si |
|-------|:---|-------|---------|
| WFE | - | ≥0.6 | OOS/IS ratio suffisant |
| MC p-value | guard001 | <0.05 | Edge statistiquement significatif |
| Sensitivity | guard002 | <10% | Params stables (±2% perturbation) |
| Bootstrap CI | guard003 | >1.0 | Sharpe robuste (95% CI) |
| Top10 trades | guard005 | <40% | Pas outlier-dependent |
| Stress Sharpe | guard006 | >1.0 | Rentable sous stress (fees 1.5x) |
| Regime mismatch | guard007 | ≤1 | Max 1 régime à Sharpe négatif |

**Seuils additionnels :**
| Paramètre | Seuil | Notes |
|-----------|-------|-------|
| Min trades OOS | ≥60 | Sample size suffisant |
| Min bars IS | ≥8000 | Données suffisantes |
| TP progression | TP1<TP2<TP3, gap≥0.5 | Contrainte Optuna |

### Étape 3: Analyser les Résultats
```python
import pandas as pd
from glob import glob

# Charger derniers résultats guards
guards = pd.read_csv(sorted(glob("outputs/multiasset_guards_summary*.csv"))[-1])

for _, row in guards.iterrows():
    status = '✅ PASS' if row['all_pass'] else '❌ FAIL'
    print(f"{row['asset']}: {status}")
    print(f"  WFE: {row['wfe']:.2f}, MC p: {row['mc_pvalue']:.4f}")
    print(f"  Sensitivity: {row['guard002_variance_pct']:.1f}%")
    print(f"  Bootstrap CI: {row['bootstrap_ci_lower']:.2f}")
```

### Étape 4: Vérifier TP Progression
```python
# Charger scan pour vérifier TP
scan = pd.read_csv(sorted(glob("outputs/multiasset_scan*.csv"))[-1])

for _, row in scan.iterrows():
    tp1, tp2, tp3 = row['tp1_mult'], row['tp2_mult'], row['tp3_mult']
    valid = tp1 < tp2 < tp3 and (tp2-tp1) >= 0.5 and (tp3-tp2) >= 0.5
    print(f"{row['asset']}: TP1={tp1:.1f} < TP2={tp2:.1f} < TP3={tp3:.1f} → {'✅' if valid else '❌'}")
```

### Étape 5: Actions selon Résultat

| Résultat | Action |
|----------|--------|
| **7/7 PASS** | Asset ready for PROD → notifier Casey dans `comms/casey-quant.md` |
| **6/7 PASS** | Identifier guard FAIL → tenter Phase 3A (displacement rescue) |
| **<6/7 PASS** | Asset PENDING → Phase 3A puis Phase 4 si nécessaire |
| **Données insuffisantes** | Asset BLOCKED (trades<60 ou bars<8000) |

## Output Attendu

Fichier `outputs/multiasset_guards_summary_YYYYMMDD_HHMMSS.csv` :
```csv
asset,all_pass,wfe,mc_pvalue,guard002_variance_pct,bootstrap_ci_lower,top10_pct,stress_pass,regime_mismatch
BTC,True,1.23,0.003,4.98,1.84,22.6,True,0
ETH,True,0.82,0.012,7.21,1.42,31.2,True,1
SOL,False,0.54,0.089,12.3,0.91,45.1,False,2
```

## Troubleshooting

| Problème | Solution |
|----------|----------|
| `guard002 FAIL` (sensitivity >10%) | Tester filter mode `medium_distance_volume` |
| `mc_pvalue > 0.05` | Plus de données ou trials |
| `top10 > 40%` | Données insuffisantes, probablement BLOCKED |
| `wfe < 0.6` proche (0.5-0.6) | Tester autre displacement (d26, d78) |
| Résultats pré-fix | REJETER, relancer avec `--enforce-tp-progression` |

## Escalade
- Si guard002 variance 10-12% (borderline) → @Alex arbitrage seuil
- Si résultat suspect (Sharpe >4, WFE >2) → Réconciliation avant validation
- Si tous guards FAIL → Utiliser skill `displacement-rescue`
