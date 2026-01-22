# Filter Grid ETH - Résumé Visuel

## 🏆 Gagnant : `medium_distance_volume` (ALL GUARDS PASS)

```
✅ OOS Sharpe: 2.09  |  ✅ WFE: 0.82  |  ✅ Variance: 3.95%  |  ✅ ALL GUARDS PASS
```

**Paramètres optimaux** :
- SL: 4.5 ATR | TP1: 4.75 | TP2: 7.0 | TP3: 10.0
- Tenkan: 15 | Kijun: 20 | Tenkan_5: 13 | Kijun_5: 22
- Displacement: 52
- Trades OOS: 57 (borderline mais acceptable)

---

## 📊 Tableau Comparatif Complet

| Mode | Sharpe | WFE | Variance | Guard002 | All Pass | Trades | Verdict |
|------|--------|-----|----------|----------|----------|--------|---------|
| **medium_distance_volume** | **2.09** | **0.82** | **3.95%** | ✅ | ✅ | 57 | 🏆 **PRODUCTION** |
| light_volume | 3.15 | 1.06 | 16.04% | ❌ | ❌ | 78 | ⚠️ Sharpe élevé mais variance |
| medium_kama_distance | 3.59 | 1.05 | 26.01% | ❌ | ❌ | 69 | ⚠️ Très instable |
| light_distance | 2.77 | 1.02 | 19.12% | ❌ | ❌ | 66 | ⚠️ Variance limite |
| strict_ichi | 2.36 | 0.75 | -157% 🔴 | ⚠️ | ❌ | 81 | 🔴 ANOMALIE |
| baseline (grid) | 2.03 | 1.43 | 23.52% | ❌ | ❌ | 84 | ⚠️ Pire que baseline original |
| medium_kama_volume | 1.70 | 0.63 | 14.74% | ❌ | ❌ | 78 | ❌ WFE < 0.6 |
| medium_kama_regression | 1.90 | 0.69 | 12.85% | ❌ | ❌ | 81 | ❌ WFE < 0.6 |
| light_regression | 1.30 | 0.40 | 7.41% | ✅ | ❌ | 72 | ❌ WFE < 0.6 |
| light_kama | 1.56 | 0.53 | 11.88% | ❌ | ❌ | 78 | ❌ WFE < 0.6 |
| moderate | 0.69 | 0.22 | 41.05% | ❌ | ❌ | 66 | ❌ Échec total |

---

## 🎯 Classement par Critère

### Par Sharpe OOS (Performance)
1. 🥇 `medium_kama_distance`: 3.59 (mais variance 26%)
2. 🥈 `light_volume`: 3.15 (mais variance 16%)
3. 🥉 `light_distance`: 2.77 (mais variance 19%)
4. **`medium_distance_volume`**: 2.09 ✅ (variance 3.95%)

### Par Variance (Robustesse)
1. 🥇 **`medium_distance_volume`**: 3.95% ✅
2. 🥈 `light_regression`: 7.41% (mais WFE 0.40)
3. 🥉 `light_kama`: 11.88% (mais WFE 0.53)

### Par WFE (Réplicabilité)
1. 🥇 `baseline (grid)`: 1.43 (mais variance 23%)
2. 🥈 `light_volume`: 1.06 (mais variance 16%)
3. 🥉 `medium_kama_distance`: 1.05 (mais variance 26%)
4. **`medium_distance_volume`**: 0.82 ✅ (variance 3.95%)

---

## 🔍 Insights Clés

### 1. Sweet Spot : 2 Filtres (Distance + Volume)
- ✅ Variance minimale (3.95%)
- ✅ Tous guards pass
- ✅ Sharpe acceptable (2.09)

### 2. Plus de Filtres = Moins de Robustesse
- 0 filtre (baseline): 23.52% variance
- 1 filtre: 7-19% variance
- 2 filtres (distance+volume): **3.95%** ✅
- 2 filtres (kama+distance): 26.01% ❌
- 4 filtres (moderate): 41.05% ❌

### 3. Anomalie strict_ichi
- Variance négative = bug de calcul
- Base Sharpe négatif = stratégie perdante
- Mode trop restrictif pour ETH

---

## 📈 Comparaison avec Baseline Original

| Métrique | Baseline Original | Baseline Grid | medium_distance_volume |
|----------|------------------|---------------|------------------------|
| Sharpe OOS | 3.87 | 2.03 | 2.09 |
| WFE | 2.36 | 1.43 | 0.82 |
| Variance | 12.96% | 23.52% | **3.95%** ✅ |
| Guards | ❌ (variance) | ❌ (variance) | ✅ **ALL PASS** |

**Conclusion** : `medium_distance_volume` sacrifie un peu de Sharpe (2.09 vs 3.87) mais gagne énormément en robustesse (variance 3.95% vs 12.96%).

---

## ✅ Recommandation Finale

**Utiliser `medium_distance_volume` pour ETH en production.**

**Justification** :
- ✅ Seul mode à passer tous les guards
- ✅ Variance 3.95% = très robuste aux variations de paramètres
- ✅ Sharpe 2.09 = acceptable (> 2.0 target)
- ✅ WFE 0.82 = performance répliquable

**Trade-off accepté** : Sharpe légèrement inférieur (2.09 vs 3.87 baseline) mais robustesse 3x meilleure (3.95% vs 12.96%).

---

**Date** : 2026-01-22  
**Fichier source** : `outputs/filter_grid_results_ETH_20260122_1917.csv`
