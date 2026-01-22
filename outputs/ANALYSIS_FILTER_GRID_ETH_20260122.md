# Analyse du Filter Grid ETH - 22 janvier 2026

## Résumé Exécutif

**12 modes de filtres testés** sur ETH avec TP progression enforced.

**Gagnant unique (tous guards pass)** : `medium_distance_volume`
- Sharpe OOS: **2.09** (acceptable)
- WFE: **0.82** (> 0.6 ✅)
- Variance sensibilité: **3.95%** (< 10% ✅)
- Tous les 7 guards: **PASS**

**Problème critique identifié** : Le mode `baseline` du grid (variance 23.52%) est **pire** que le baseline original (variance 12.96%). Cela suggère que la réoptimisation avec baseline filter mode a dégradé la robustesse.

---

## Résultats Détaillés par Mode

### ✅ Gagnant : `medium_distance_volume` (ALL PASS)

| Métrique | Valeur | Status |
|----------|--------|--------|
| OOS Sharpe | 2.09 | ✅ |
| WFE | 0.82 | ✅ (> 0.6) |
| Variance sensibilité | 3.95% | ✅ (< 10%) |
| Guard002 | PASS | ✅ |
| Tous guards | PASS | ✅ |
| Trades OOS | 57 | ✅ (> 60 borderline) |
| Base Sharpe | 1.68 | ✅ |

**Configuration** :
- `use_distance_filter`: True
- `use_volume_filter`: True
- `use_regression_cloud`: False
- `use_kama_oscillator`: False
- `use_ichimoku_filter`: True
- `ichi5in1_strict`: False

**Verdict** : **RECOMMANDÉ pour production ETH**. Seul mode à passer tous les guards avec variance < 10%.

---

### ⚠️ Performants mais Guards FAIL

#### 1. `light_volume` - Meilleur Sharpe mais variance élevée

| Métrique | Valeur | Status |
|----------|--------|--------|
| OOS Sharpe | **3.15** | ✅ (meilleur) |
| WFE | 1.06 | ✅ |
| Variance sensibilité | 16.04% | ❌ (> 10%) |
| Guard002 | FAIL | ❌ |
| Tous guards | FAIL | ❌ |

**Analyse** : Sharpe excellent mais sensibilité aux paramètres trop élevée. Risque d'overfit.

#### 2. `medium_kama_distance` - Sharpe élevé mais variance critique

| Métrique | Valeur | Status |
|----------|--------|--------|
| OOS Sharpe | **3.59** | ✅ (très élevé) |
| WFE | 1.05 | ✅ |
| Variance sensibilité | 26.01% | ❌ (> 10%) |
| Base Sharpe | 0.53 | ⚠️ (faible) |
| Guard002 | FAIL | ❌ |

**Analyse** : Performance OOS excellente mais base Sharpe très faible (0.53) suggère instabilité. Variance 26% = très sensible aux paramètres.

#### 3. `light_distance` - Bon compromis mais variance limite

| Métrique | Valeur | Status |
|----------|--------|--------|
| OOS Sharpe | 2.77 | ✅ |
| WFE | 1.02 | ✅ |
| Variance sensibilité | 19.12% | ❌ (> 10%) |
| Guard002 | FAIL | ❌ |

**Analyse** : Bonne performance mais variance encore trop élevée.

---

### ❌ Échecs Complets

#### 1. `moderate` - Échec total

| Métrique | Valeur | Status |
|----------|--------|--------|
| OOS Sharpe | 0.69 | ❌ (< 1.0) |
| WFE | 0.22 | ❌ (< 0.6) |
| Variance sensibilité | 41.05% | ❌ (très élevée) |
| Base Sharpe | 0.29 | ❌ (très faible) |

**Analyse** : Tous les filtres activés (4 filtres) = overfit sévère. WFE 0.22 = performance IS ne se réplique pas du tout en OOS.

**Conclusion** : Pour ETH, **plus de filtres ≠ meilleure performance**. Le mode `moderate` (4 filtres) est contre-productif.

#### 2. `light_kama` - WFE trop faible

| Métrique | Valeur | Status |
|----------|--------|--------|
| OOS Sharpe | 1.56 | ⚠️ |
| WFE | 0.53 | ❌ (< 0.6) |
| Variance sensibilité | 11.88% | ❌ (> 10%) |

**Analyse** : WFE < 0.6 = overfit. KAMA oscillator seul ne suffit pas.

#### 3. `light_regression` - WFE critique

| Métrique | Valeur | Status |
|----------|--------|--------|
| OOS Sharpe | 1.30 | ⚠️ |
| WFE | 0.40 | ❌ (< 0.6) |
| Variance sensibilité | 7.41% | ✅ (< 10%) |
| Guard002 | PASS | ✅ |

**Analyse** : Variance OK mais WFE 0.40 = overfit sévère. Regression cloud seul = trop restrictif.

---

### 🔴 Anomalie : `strict_ichi`

| Métrique | Valeur | Status |
|----------|--------|--------|
| OOS Sharpe | 2.36 | ✅ |
| WFE | 0.75 | ✅ |
| Variance sensibilité | **-157.0%** | 🔴 ANOMALIE |
| Base Sharpe | **-0.09** | 🔴 NÉGATIF |
| Guard002 | PASS | ⚠️ (faux positif) |
| Tous guards | FAIL | ❌ |

**Analyse de l'anomalie** :

1. **Variance négative (-157%)** : Physiquement impossible. Calcul probablement :
   ```
   variance_pct = (std_sharpe / mean_sharpe) * 100
   ```
   Si `mean_sharpe` est négatif ou proche de zéro, la variance devient négative ou très élevée.

2. **Base Sharpe négatif (-0.09)** : La stratégie perd de l'argent sur l'ensemble des données. Cela suggère que :
   - Les paramètres optimisés sont mauvais
   - Le mode strict_ichi (17 bull + 17 bear conditions) est trop restrictif pour ETH
   - Il y a peut-être un bug dans le calcul de sensibilité quand base_sharpe < 0

3. **Guard002 PASS mais all_pass FAIL** : Le guard002 passe (variance < 10%) mais c'est un **faux positif** dû à l'anomalie de calcul. Les autres guards échouent :
   - Guard001 (MC): p=0.37 > 0.05 ❌
   - Guard003 (Bootstrap CI): -2.20 < 1.0 ❌
   - Guard006 (Stress1): -0.62 < 1.0 ❌

**Recommandation** : 
- **Exclure `strict_ichi`** des résultats valides
- **Investigation requise** : Vérifier le calcul de variance quand base_sharpe ≤ 0
- Le mode strict_ichi (17 conditions) semble trop restrictif pour ETH

---

## Comparaison avec Baseline Original

### Baseline Original (scan 20260122_1322)
- OOS Sharpe: **3.87**
- WFE: **2.36**
- Variance sensibilité: **12.96%**
- Status: SUCCESS mais guards FAIL (variance > 10%)

### Baseline Grid (fgrid_ETH_baseline)
- OOS Sharpe: **2.03** (-47% vs original)
- WFE: **1.43** (-39% vs original)
- Variance sensibilité: **23.52%** (+81% vs original)
- Status: SUCCESS mais guards FAIL

**Analyse** : La réoptimisation avec baseline filter mode a **dégradé** les performances et la robustesse. Cela suggère que :
1. Les paramètres optimaux changent selon les filtres
2. Le baseline original avait de meilleurs paramètres (peut-être optimisés différemment)
3. La variance a presque doublé (12.96% → 23.52%)

**Conclusion** : Ne pas utiliser le baseline du grid. Le baseline original reste meilleur mais échoue toujours sur guard002.

---

## Patterns Identifiés

### 1. Impact des Filtres sur la Variance

| Combinaison | Variance | Pattern |
|-------------|----------|---------|
| Aucun filtre (baseline) | 23.52% | Très élevée |
| 1 filtre seul | 7.41% - 19.12% | Variable |
| 2 filtres (distance+volume) | **3.95%** | ✅ Optimal |
| 2 filtres (kama+distance) | 26.01% | ❌ Dégradé |
| 4 filtres (moderate) | 41.05% | ❌ Très dégradé |

**Insight** : **2 filtres (distance + volume) = sweet spot** pour ETH. Plus de filtres = variance augmentée (contre-intuitif).

### 2. Impact sur WFE

| Mode | WFE | Filtres actifs |
|------|-----|----------------|
| baseline | 1.43 | 0 (Ichimoku seul) |
| light_volume | 1.06 | 1 |
| medium_distance_volume | 0.82 | 2 |
| moderate | 0.22 | 4 |

**Pattern** : Plus de filtres = WFE réduit (mais variance augmente). Trade-off complexe.

### 3. Impact sur Sharpe OOS

| Mode | Sharpe OOS | Filtres |
|------|------------|---------|
| medium_kama_distance | 3.59 | 2 (kama+distance) |
| light_volume | 3.15 | 1 (volume) |
| light_distance | 2.77 | 1 (distance) |
| strict_ichi | 2.36 | 0 (strict mode) |
| medium_distance_volume | 2.09 | 2 (distance+volume) |
| baseline | 2.03 | 0 |

**Pattern** : Les combinaisons avec KAMA oscillator ou volume seul donnent les meilleurs Sharpes, mais au prix d'une variance élevée.

---

## Recommandations

### 1. Configuration Production ETH

**Mode recommandé** : `medium_distance_volume`

**Justification** :
- ✅ Seul mode à passer tous les guards
- ✅ Variance 3.95% (< 10%) = robuste
- ✅ WFE 0.82 (> 0.6) = performance répliquable
- ✅ Sharpe 2.09 (> 1.0) = acceptable

**Action** :
1. Extraire les paramètres optimaux de `fgrid_ETH_medium_distance_volume_20260122_183348_multiasset_scan_20260122_183544.csv`
2. Valider avec un rerun complet (scan + guards)
3. Mettre à jour `crypto_backtest/config/asset_config.py` avec ces paramètres

### 2. Investigation Requise

#### A. Anomalie strict_ichi
- **Problème** : Variance négative (-157%), base_sharpe négatif
- **Cause probable** : Calcul de variance quand mean_sharpe ≤ 0
- **Action** : Vérifier `scripts/run_guards_multiasset.py` ligne 207 :
  ```python
  variance_pct = (std_sharpe / mean_sharpe * 100.0) if mean_sharpe != 0 else 0.0
  ```
  Si `mean_sharpe < 0`, la variance devient négative. Ajouter une protection.

#### B. Trade-off Filtres vs Variance
- **Observation** : Plus de filtres = variance augmentée (contre-intuitif)
- **Hypothèse** : Les filtres supplémentaires créent des optima locaux instables
- **Action** : Tester sur d'autres assets (CAKE, AVAX) pour valider le pattern

### 3. Alternatives à Considérer

Si `medium_distance_volume` ne donne pas satisfaction en production :

1. **`light_volume`** (Sharpe 3.15) : 
   - Re-optimiser avec contrainte de variance < 10%
   - Tester avec plus de trials pour trouver un optimum plus stable

2. **Baseline original** (Sharpe 3.87) :
   - Garder les paramètres originaux
   - Accepter variance 12.96% si acceptable pour le risque

### 4. Prochaines Étapes

1. ✅ **Attendre résultats définitifs** du grid (si encore en cours)
2. 🔴 **Valider `medium_distance_volume`** avec rerun complet
3. 🟡 **Investigation anomalie strict_ichi** (fix calcul variance)
4. 🟡 **Tester pattern sur CAKE** (variance 20.70% → peut-être améliorable avec distance+volume)
5. ⬜ **Mettre à jour docs** (HANDOFF.md, BACKTESTING.md) avec résultats finaux

---

## Métriques de Référence

### Seuils de Validation (Rappel)

| Guard | Seuil | Critique |
|-------|-------|----------|
| WFE | > 0.6 | OUI |
| MC p-value | < 0.05 | OUI |
| Sensitivity var | < 10% | OUI |
| Bootstrap CI lower | > 1.0 | OUI |
| Top10 trades | < 40% | OUI |
| Stress1 Sharpe | > 1.0 | OUI |
| Regime mismatch | < 1% | OUI |

### Targets

- Sharpe > 1.0 (target > 2.0) ✅
- PF > 1.3
- MaxDD < 15%

---

## Fichiers de Référence

- Grid results: `outputs/filter_grid_results_ETH_20260122_1917.csv`
- Gagnant scan: `outputs/fgrid_ETH_medium_distance_volume_20260122_183348_multiasset_scan_20260122_183544.csv`
- Gagnant guards: `outputs/fgrid_ETH_medium_distance_volume_20260122_183348_guards_summary_20260122_183544.csv`
- Baseline original: `outputs/multiasset_scan_20260122_1322.csv`

---

**Date d'analyse** : 2026-01-22  
**Statut** : En attente des résultats définitifs du grid
