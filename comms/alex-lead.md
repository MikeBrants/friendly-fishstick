# Alex Lead — Communications

## 2026-01-25 10:00 UTC — NOUVELLES TÂCHES PRIORITAIRES (URGENT)

### FROM: Casey (Orchestrator)
### TO: Alex (Lead Quant)
### STATUS: TODO — REPRIORITISATION MAJEURE
### PRIORITY: 🔴🔴🔴 CRITIQUE

---

## ⚠️ CHANGEMENT DE PRIORITÉS

**La variance reduction est DÉPRIORITISÉE**. Les tâches ci-dessous prennent la priorité immédiate.

---

## TASK 0: Audit WFE Period Effect 🚨 BLOQUANT

### Statut: BLOQUANT — Aucune décision PROD tant que non résolu

### Problème Identifié

Le calcul actuel de WFE dans `crypto_backtest/optimization/walk_forward.py:120` est suspect:

```python
efficiency_ratio = _ratio(mean_oos_return, mean_is_return) * 100.0
```

**Issues potentielles:**
1. **Utilise les returns** au lieu des Sharpe ratios (WFE classique = OOS_Sharpe / IS_Sharpe)
2. **Multiplication par 100** → Valeurs gonflées (ex: WFE 2.36 pour ETH semble trop haut)
3. **Period effect**: Les fenêtres IS (180d) vs OOS (30d) ont des régimes différents

### Questions à Auditer

1. **Le calcul WFE est-il correct?** Comparer avec la définition standard (Robert Pardo)
2. **Y a-t-il un biais temporel?** Les IS contiennent-ils systématiquement plus de bull markets?
3. **Les WFE > 2.0 sont-ils réalistes?** (ETH: 2.36, SHIB: 2.27) — Normalement WFE < 1.0 est attendu

### Références

- **Robert Pardo** (2008) "The Evaluation and Optimization of Trading Strategies"
- **WFE Standard**: Efficiency = OOS_Performance / IS_Performance, attendu entre 0.5-0.8

### Deliverable

Créer fichier: `reports/wfe-audit-2026-01-25.md`
- Diagnostic du calcul actuel
- Comparaison avec définition standard
- Recommandation: FIX ou KEEP avec justification

---

## TASK 1: Implémenter PBO (Probability of Backtest Overfitting) 🔴 CRITIQUE

### Statut: CRITIQUE — Nécessaire pour validation statistique

### Contexte

Le DSR actuel (`deflated_sharpe.py`) corrige le trial count mais **n'est pas le vrai PBO**.

**PBO** (Bailey & López de Prado, 2014) = Probabilité que la meilleure stratégie backtest soit overfittée.

### Définition Formelle

```
PBO = Probability that OOS performance of "best" IS strategy ranks below median

Méthodologie:
1. Diviser données en S sous-ensembles (ex: S=16)
2. Former toutes combinaisons C(S, S/2) de training sets
3. Pour chaque combo: identifier "best" strategy sur IS, mesurer rang OOS
4. PBO = proportion de combos où rang OOS < médiane
```

### Implémentation Requise

**Fichier**: `crypto_backtest/validation/pbo.py`

```python
def probability_of_backtest_overfitting(
    returns_matrix: pd.DataFrame,  # N strategies x T periods
    n_splits: int = 16,
    risk_free: float = 0.0
) -> dict:
    """
    Calculate PBO using CSCV (Combinatorially Symmetric Cross-Validation).

    Returns:
        pbo: float [0,1] — probability of overfitting
        logits: array — distribution of relative ranks
        threshold: float — PBO threshold for significance
    """
```

### Seuils

| PBO | Verdict |
|-----|---------|
| < 0.15 | ✅ PASS — Low overfitting risk |
| 0.15-0.30 | ⚠️ MARGINAL — Proceed with caution |
| > 0.30 | ❌ FAIL — High overfitting probability |

### Références Académiques

1. **Bailey, D. H., & López de Prado, M. (2014)**
   "The Probability of Backtest Overfitting"
   *Journal of Computational Finance*
   https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2326253

2. **Bailey, D. H., Borwein, J., López de Prado, M., & Zhu, Q. J. (2014)**
   "Pseudo-Mathematics and Financial Charlatanism"
   *Notices of the AMS*

3. **López de Prado, M. (2018)**
   "Advances in Financial Machine Learning" — Chapter 11: Backtesting

### Code de Référence (MLFinLab)

```python
# Reference: hudson-and-thames/mlfinlab
# Module: mlfinlab.cross_validation.combinatorial

from itertools import combinations
import numpy as np
from scipy.special import comb

def cscv_pbo(strategy_returns, n_groups=16):
    """
    Combinatorially Symmetric Cross-Validation for PBO.

    1. Split time series into n_groups blocks
    2. Enumerate all C(n_groups, n_groups/2) train/test splits
    3. For each split:
       - Rank strategies by IS Sharpe
       - Record OOS rank of "best" IS strategy
    4. PBO = P(OOS_rank <= median)
    """
    n_combos = int(comb(n_groups, n_groups // 2))
    oos_ranks = []

    for train_idx in combinations(range(n_groups), n_groups // 2):
        test_idx = [i for i in range(n_groups) if i not in train_idx]

        # Calculate IS performance
        is_sharpes = calculate_sharpes(strategy_returns, train_idx)
        best_is_strategy = np.argmax(is_sharpes)

        # Calculate OOS rank of best IS strategy
        oos_sharpes = calculate_sharpes(strategy_returns, test_idx)
        oos_rank = rankdata(-oos_sharpes)[best_is_strategy]

        # Relative rank (0 = best, 1 = worst)
        relative_rank = oos_rank / len(oos_sharpes)
        oos_ranks.append(relative_rank)

    # PBO = proportion where OOS rank is below median
    pbo = np.mean(np.array(oos_ranks) > 0.5)
    return pbo, oos_ranks
```

---

## TASK 2: Implémenter CPCV (Combinatorial Purged Cross-Validation)

### Statut: HIGH — Complète PBO pour validation robuste

### Contexte

CPCV est la méthode de cross-validation recommandée par López de Prado pour les séries financières.

**Problème des CV classiques**: Data leakage temporel (information future dans training set)

**Solution CPCV**:
1. **Purging**: Supprimer observations autour du split (évite leakage)
2. **Embargo**: Gap temporel entre train/test
3. **Combinatorial**: Toutes les combinaisons possibles de folds

### Implémentation Requise

**Fichier**: `crypto_backtest/validation/cpcv.py`

```python
from typing import Generator, Tuple
import numpy as np
import pandas as pd
from itertools import combinations

class CombinatorialPurgedKFold:
    """
    Combinatorial Purged K-Fold Cross-Validation.

    Implements López de Prado's CPCV methodology:
    - Purging: Remove observations within embargo period of test set
    - Embargo: Additional gap after test set before training resumes
    - Combinatorial: Generate all C(n_splits, n_test_splits) combinations
    """

    def __init__(
        self,
        n_splits: int = 6,
        n_test_splits: int = 2,
        purge_gap: int = 0,
        embargo_pct: float = 0.01
    ):
        self.n_splits = n_splits
        self.n_test_splits = n_test_splits
        self.purge_gap = purge_gap
        self.embargo_pct = embargo_pct

    def split(
        self,
        X: pd.DataFrame,
        y: pd.Series = None,
        groups: pd.Series = None
    ) -> Generator[Tuple[np.ndarray, np.ndarray], None, None]:
        """
        Generate train/test indices with purging and embargo.

        Yields:
            train_indices, test_indices for each combination
        """
        pass  # Implement

    def get_n_splits(self) -> int:
        """Return number of splitting iterations."""
        from scipy.special import comb
        return int(comb(self.n_splits, self.n_test_splits))
```

### Références

1. **López de Prado, M. (2018)**
   "Advances in Financial Machine Learning" — Chapter 7: Cross-Validation in Finance

2. **MLFinLab Documentation**
   https://mlfinlab.readthedocs.io/en/latest/implementations/cross_validation.html

3. **Hudson & Thames Implementation**
   https://github.com/hudson-and-thames/mlfinlab/blob/master/mlfinlab/cross_validation/combinatorial.py

---

## 📚 Références Obligatoires

### Papers López de Prado (À LIRE)

| Paper | Année | Relevance |
|-------|-------|-----------|
| "The Probability of Backtest Overfitting" | 2014 | TASK 1 — PBO |
| "The Deflated Sharpe Ratio" | 2014 | Context DSR |
| "Pseudo-Mathematics and Financial Charlatanism" | 2014 | Pourquoi PBO |
| "Advances in Financial Machine Learning" Ch.7,11 | 2018 | CPCV, Backtesting |

### Repos GitHub à Analyser

| Repo | Focus | URL |
|------|-------|-----|
| **mlfinlab** (Hudson & Thames) | PBO, CPCV, DSR | https://github.com/hudson-and-thames/mlfinlab |
| **vectorbt** | WFE, Optimization | https://github.com/polakowo/vectorbt |
| **backtesting.py** | Walk-Forward | https://github.com/kernc/backtesting.py |
| **freqtrade** | Hyperopt, Validation | https://github.com/freqtrade/freqtrade |
| **quantstats** | Metrics, Tearsheets | https://github.com/ranaroussi/quantstats |
| **riskfolio-lib** | Portfolio Optimization | https://github.com/dcajasn/Riskfolio-Lib |

### Focus Analyse GitHub

Pour chaque repo, documenter:
1. **Implémentation PBO** — Existe? Comment?
2. **Implémentation CPCV** — Existe? Paramètres?
3. **Calcul WFE** — Définition utilisée?
4. **Anti-overfitting** — Autres techniques?

---

## 📊 Priorités Mises à Jour

| # | Task | Priority | Status | Blocking |
|---|------|----------|--------|----------|
| 0 | WFE Period Effect Audit | 🔴🔴🔴 BLOQUANT | TODO | Oui |
| 1 | PBO Implementation | 🔴🔴 CRITIQUE | TODO | Non |
| 2 | CPCV Implementation | 🔴 HIGH | TODO | Non |
| 3 | ~~Variance Reduction~~ | ⬜ DÉPRIORITISÉ | HOLD | Non |
| 4 | GitHub Repos Analysis | 🟡 MEDIUM | TODO | Non |

---

## Deliverables Attendus

1. **`reports/wfe-audit-2026-01-25.md`** — Audit WFE (TASK 0)
2. **`crypto_backtest/validation/pbo.py`** — PBO module (TASK 1)
3. **`crypto_backtest/validation/cpcv.py`** — CPCV module (TASK 2)
4. **`reports/github-repos-analysis.md`** — Analyse repos (TASK 4)

---

## Format de Réponse

```
HHMM INPROGRESS alex-lead -> casey-quant: TASK [N] en cours
Fichier: [path]
Progress: [X/Y steps]
Blockers: [if any]
```

Puis:
```
HHMM DONE alex-lead -> casey-quant: TASK [N] terminé
Deliverable: [path to file]
Key Findings: [bullet points]
Recommendation: [action]
```

---

## ⚡ Action Immédiate Requise

**Alex**: Commence par TASK 0 (WFE Audit) — c'est BLOQUANT.

Les décisions PROD sur les 11 assets validés sont en suspens jusqu'à confirmation que le calcul WFE est correct.

---
---

## ARCHIVE — Tâches Précédentes

---

## 2026-01-24 22:30 UTC — TASK: Variance Reduction Research

### FROM: Casey (Orchestrator)
### TO: Alex (Lead Quant)
### STATUS: TODO
### PRIORITY: 🔴 HIGH

---

## Contexte

Avec le nouveau seuil sensitivity à 15%, plusieurs assets passent maintenant guard002.
Cependant, on veut **réduire la variance** même en dessous de 15%, surtout pour les gros assets comme ETH.

**ETH baseline actuel**:
- Sensitivity: 12.96%
- Sharpe: 3.87
- WFE: 2.36

**Objectif**: Trouver des solutions pour réduire la variance sous 10% si possible, sans sacrifier le Sharpe.

---

## Tâches Assignées

### 1. Implémenter Deflated Sharpe Ratio (DSR) — PRIORITÉ 1

Le DSR corrige directement pour le **trial count paradox** que tu as identifié.

**Fichier à créer**: `crypto_backtest/validation/deflated_sharpe.py`

**Formule**:
```
SR₀ = σ(SR) × [(1-γ)Φ⁻¹(1-1/N) + γΦ⁻¹(1-1/Ne)]
DSR = Φ((SR - SR₀) / σ(SR))
```

**Seuils recommandés**:
| DSR | Verdict |
|-----|---------|
| > 95% | PASS |
| 85-95% | MARGINAL |
| < 85% | FAIL |

**Intégration**: Ajouter comme `guard008` ou metric informative.

### 2. Rechercher Solutions Variance Reduction — PRIORITÉ 2

**Assets cibles**: ETH (12.96%), CAKE (10.76%), autres >10%

**Pistes à explorer**:
1. **Regime-aware WF splits** — Les splits actuels ignorent si on coupe en bull/bear/sideways
2. **Parameter averaging** — Moyenner top N trials au lieu de prendre le best
3. **Regularization Optuna** — Ajouter pénalité variance dans objective
4. **Ensemble de paramètres** — Combiner plusieurs sets de params
5. **Reduced trial count** — Tu as montré que 50 trials > 100 trials pour WFE

### 3. Recherche GitHub Quant Repos — PRIORITÉ 3

**Objectif**: Trouver des stratégies/filtres complémentaires sur les repos quant populaires.

**Repos à explorer**:
- `quantopian/zipline`
- `pmorissette/bt`
- `ranaroussi/quantstats`
- `polakowo/vectorbt`
- `kernc/backtesting.py`
- `freqtrade/freqtrade`

**Focus**:
- Filtres de volatilité
- Méthodes de réduction overfitting
- Walk-forward robustes
- Ensemble methods

---

## Deliverables Attendus

1. **Code DSR** (`crypto_backtest/validation/deflated_sharpe.py`)
2. **Rapport variance reduction** (solutions testées, résultats)
3. **Liste de filtres/stratégies** identifiés sur GitHub (à intégrer ou tester)

---

## Timeline

| Task | Durée estimée |
|------|---------------|
| DSR implementation | 1-2h |
| Variance reduction research | 2-4h |
| GitHub repos scan | 1-2h |

---

## Notes Techniques

### DSR — Code de référence

```python
import numpy as np
from scipy.stats import norm, skew, kurtosis

def deflated_sharpe_ratio(returns, sharpe_observed, n_trials, annualization=1):
    """
    Calculate DSR - probability that observed Sharpe is statistically significant.
    
    Args:
        returns: array of strategy returns (not annualized)
        sharpe_observed: observed Sharpe ratio (not annualized)
        n_trials: number of optimization trials tested
        annualization: 1 for already annualized
    
    Returns:
        dsr: probability [0,1] that Sharpe is significant
        sr0: threshold Sharpe expected from random trials
    """
    T = len(returns)
    sr = sharpe_observed / annualization
    
    # Higher moments
    gamma3 = skew(returns)
    gamma4 = kurtosis(returns, fisher=False)
    
    # Variance of Sharpe estimator
    var_sr = (1 + 0.5 * sr**2 - gamma3 * sr + ((gamma4 - 3) / 4) * sr**2) / (T - 1)
    std_sr = np.sqrt(var_sr)
    
    # Euler-Mascheroni constant
    gamma = 0.5772156649
    
    # SR0: threshold expected by chance
    sr0 = std_sr * ((1 - gamma) * norm.ppf(1 - 1/n_trials) + 
                     gamma * norm.ppf(1 - 1/(n_trials * np.e)))
    
    # DSR
    dsr = norm.cdf((sr - sr0) / std_sr)
    
    return dsr, sr0
```

### Regime-Aware Splits

Problème actuel: Les splits WF (60/20/20) ignorent la distribution des régimes.
- Si IS = 100% BULL et OOS = 100% BEAR → WFE biaisé
- Solution: Stratified splits par régime

---

## Réponse Attendue

Format:
```
HHMM INPROGRESS alex-lead -> casey-quant: [Task] en cours
Fichier: [path]
Progress: [X/Y steps]
ETA: [time]
```

Puis:
```
HHMM DONE alex-lead -> casey-quant: [Task] terminé
Deliverable: [path to file/report]
Summary: [key findings]
Next: [recommended actions]
```
