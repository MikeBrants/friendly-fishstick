# Alex Lead — Communications

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
