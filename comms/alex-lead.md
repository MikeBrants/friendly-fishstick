# Alex Lead — Communications

## 2026-01-25 — MISE À JOUR PRIORITÉS (Audit Quant Externe)

### FROM: Casey (Orchestrator) + Audit Quant Specialist
### TO: Alex (Lead Quant)
### STATUS: RE-PRIORISATION URGENTE
### PRIORITY: 🔴 CRITIQUE

---

## ⚠️ CONTEXTE CRITIQUE

Un audit externe a identifié un **problème majeur**: WFE > 1.0 sur 7 assets (SHIB 2.27, DOT 1.74, NEAR 1.69...).

**Statistiquement, WFE > 1.0 est quasi-impossible** sans:
1. Bug de calcul
2. Data leakage / look-ahead bias
3. Effet de période (OOS = bull market)
4. Survivorship bias

L'audit a vérifié: WFE formula ✅, Split overlap ✅, Indicator shifts ✅

**Hypothèse principale**: La période OOS (80-100% du dataset) correspond probablement à un bull run crypto, gonflant artificiellement les performances OOS.

---

## 🔴 NOUVELLES TÂCHES CRITIQUES (Priorité Absolue)

### TASK 0: AUDIT WFE — Period Effect Test ⚡ NOUVEAU
**Priorité**: 🔴 BLOQUANT
**Effort**: 1-2h
**Status**: TODO

**Objectif**: Confirmer ou infirmer l'hypothèse "période OOS favorable"

**Actions**:
1. **Identifier les dates exactes IS/OOS** pour 3 assets (SHIB, ETH, DOT)
2. **Analyser le marché** durant ces périodes (bull/bear/sideways)
3. **Test split inversé**: Exécuter avec IS↔OOS inversés

```python
# Script à créer: scripts/audit_wfe_period_effect.py

def split_data_reversed(df, splits=(0.6, 0.2, 0.2)):
    """OOS devient IS, IS devient OOS — test période"""
    n = len(df)
    oos_end = int(n * splits[2])  # 20% premier
    val_end = int(n * (splits[2] + splits[1]))  # 20% suivant
    # INVERSÉ: anciennes données = OOS, nouvelles = IS
    return df.iloc[val_end:], df.iloc[oos_end:val_end], df.iloc[:oos_end]

def audit_period_effect(asset: str):
    """
    1. Charger données
    2. Afficher dates IS vs OOS
    3. Calculer rendement BTC/marché sur chaque période
    4. Run normal + run inversé
    5. Comparer WFE
    """
    df = load_data(asset)
    df_is, df_val, df_oos = split_data(df)

    print(f"IS Period:  {df_is.index[0]} -> {df_is.index[-1]}")
    print(f"OOS Period: {df_oos.index[0]} -> {df_oos.index[-1]}")

    # Rendement buy & hold sur chaque période
    is_return = (df_is['close'].iloc[-1] / df_is['close'].iloc[0] - 1) * 100
    oos_return = (df_oos['close'].iloc[-1] / df_oos['close'].iloc[0] - 1) * 100

    print(f"IS Buy&Hold:  {is_return:.1f}%")
    print(f"OOS Buy&Hold: {oos_return:.1f}%")

    # Si OOS return >> IS return → effet période confirmé
```

**Résultat attendu**:
- Si WFE inversé << 1.0 → **EFFET PÉRIODE CONFIRMÉ** → tous les WFE actuels sont biaisés
- Si WFE inversé ~ WFE normal → chercher ailleurs

**Deliverable**: `outputs/audit_wfe_period_effect_report.md`

---

### TASK 1: Implémenter PBO (Probability of Backtest Overfitting) ⚡ NOUVEAU
**Priorité**: 🔴 CRITIQUE
**Effort**: 3-4h
**Status**: TODO

**Contexte**: DSR est implémenté ✅ mais **PBO manque**. PBO est le gold standard pour détecter l'overfitting.

**Référence**: Bailey et al. (2015) "The Probability of Backtest Overfitting"

**Fichier à créer**: `crypto_backtest/validation/pbo.py`

```python
"""
Probability of Backtest Overfitting (PBO)

Mesure la probabilité que le meilleur paramètre IS ne soit PAS le meilleur OOS.
PBO > 0.5 = overfitting probable

Méthode:
1. Diviser données en S sous-échantillons
2. Pour chaque combinaison de S/2 (IS) vs S/2 (OOS):
   - Trouver best params sur IS
   - Évaluer ce best sur OOS
   - Compter si rank OOS < médiane
3. PBO = proportion où best IS underperforms OOS
"""
import numpy as np
from itertools import combinations
from typing import List, Tuple, Callable

def combinatorial_purged_cross_validation(
    returns_matrix: np.ndarray,  # Shape: (n_trials, n_periods)
    n_splits: int = 10,
    purge_pct: float = 0.01,
) -> Tuple[float, List[float]]:
    """
    Compute PBO using Combinatorial Purged Cross-Validation (CPCV).

    Args:
        returns_matrix: Matrix of returns for each trial configuration
                       rows = different parameter sets
                       cols = time periods
        n_splits: Number of time splits (default 10)
        purge_pct: Percentage of data to purge between train/test

    Returns:
        pbo: Probability of Backtest Overfitting [0, 1]
        logits: Distribution of relative ranks

    Interpretation:
        PBO < 0.3: Low overfitting risk
        PBO 0.3-0.5: Moderate risk
        PBO > 0.5: High overfitting risk (best IS likely NOT best OOS)
    """
    n_trials, n_periods = returns_matrix.shape
    split_size = n_periods // n_splits

    # Generate all combinations of n_splits/2 for IS
    all_splits = list(range(n_splits))
    is_combinations = list(combinations(all_splits, n_splits // 2))

    underperformance_count = 0
    logits = []

    for is_splits in is_combinations:
        oos_splits = [s for s in all_splits if s not in is_splits]

        # Build IS and OOS indices with purging
        is_indices = []
        oos_indices = []

        for s in is_splits:
            start = s * split_size
            end = (s + 1) * split_size
            is_indices.extend(range(start, end))

        for s in oos_splits:
            start = s * split_size
            end = (s + 1) * split_size
            oos_indices.extend(range(start, end))

        # Compute Sharpe for each trial on IS and OOS
        is_sharpes = []
        oos_sharpes = []

        for trial_idx in range(n_trials):
            is_returns = returns_matrix[trial_idx, is_indices]
            oos_returns = returns_matrix[trial_idx, oos_indices]

            is_sharpe = np.mean(is_returns) / (np.std(is_returns) + 1e-10)
            oos_sharpe = np.mean(oos_returns) / (np.std(oos_returns) + 1e-10)

            is_sharpes.append(is_sharpe)
            oos_sharpes.append(oos_sharpe)

        # Find best trial on IS
        best_is_idx = np.argmax(is_sharpes)

        # Rank of best_is trial on OOS
        oos_ranks = np.argsort(np.argsort(oos_sharpes)[::-1])  # Higher = better rank
        best_is_oos_rank = oos_ranks[best_is_idx]

        # Relative rank (0 = best, 1 = worst)
        relative_rank = best_is_oos_rank / (n_trials - 1)
        logits.append(relative_rank)

        # Count if best IS underperforms median on OOS
        if relative_rank > 0.5:
            underperformance_count += 1

    pbo = underperformance_count / len(is_combinations)

    return pbo, logits


def guard_pbo(
    returns_matrix: np.ndarray,
    threshold: float = 0.5,
    n_splits: int = 10,
) -> dict:
    """
    Guard function for PBO validation.

    Args:
        returns_matrix: (n_trials, n_periods) array
        threshold: Max acceptable PBO (default 0.5)
        n_splits: Number of CV splits

    Returns:
        dict with pass/fail and metrics
    """
    pbo, logits = combinatorial_purged_cross_validation(
        returns_matrix, n_splits=n_splits
    )

    return {
        "guard": "pbo",
        "pass": pbo < threshold,
        "pbo": round(pbo, 4),
        "threshold": threshold,
        "interpretation": interpret_pbo(pbo),
        "n_combinations": len(logits),
    }


def interpret_pbo(pbo: float) -> str:
    if pbo < 0.3:
        return "LOW RISK - Parameters likely robust"
    elif pbo < 0.5:
        return "MODERATE RISK - Some overfitting possible"
    else:
        return "HIGH RISK - Best IS params likely overfit"
```

**Intégration**: Ajouter comme `guard_pbo` dans le pipeline de validation.

**Deliverable**:
- `crypto_backtest/validation/pbo.py`
- Test sur 3 assets avec rapport

---

### TASK 2: CPCV (Combinatorial Purged Cross-Validation) ⚡ NOUVEAU
**Priorité**: 🟡 HIGH
**Effort**: 2-3h
**Status**: TODO

**Contexte**: Remplacer le split fixe 60/20/20 par CPCV pour éliminer le biais de période.

**Référence**: MLFinLab implementation

**Objectif**:
- Générer multiples combinaisons IS/OOS
- Calculer WFE moyen sur toutes les combinaisons
- Réduire la variance du WFE estimé

**Fichier à créer**: `crypto_backtest/validation/cpcv.py`

---

## 🟡 TÂCHES EXISTANTES (Re-priorisées)

### TASK 3: DSR Implementation — ✅ DONE
**Status**: COMPLÉTÉ
**Fichier**: `crypto_backtest/validation/deflated_sharpe.py`

Bien fait. Passer à la suite.

---

### TASK 4: Variance Reduction Research
**Priorité**: 🟡 MEDIUM (était HIGH)
**Effort**: 2-4h
**Status**: TODO — DÉPRIORITISÉ

**Raison du changement**: La variance n'est pas le problème principal. Le WFE > 1.0 est plus urgent.

**À faire APRÈS résolution du WFE**:
1. Regime-aware WF splits
2. Parameter averaging (BMA)
3. Regularization Optuna
4. Reduced trial count experiments

---

### TASK 5: GitHub Quant Repos Research
**Priorité**: 🟡 MEDIUM
**Effort**: 2-3h
**Status**: TODO

**Repos à analyser** (ordre de priorité):

#### Priorité 1 — Anti-Overfitting Methods
| Repo | Focus | Fichiers clés |
|------|-------|---------------|
| `hudson-and-thames/mlfinlab` | PBO, CPCV, DSR | `cross_validation/`, `backtest_statistics/` |
| `stefan-jansen/machine-learning-for-trading` | Walk-forward, CV | `Chapter 8/`, validation code |

#### Priorité 2 — Backtesting Best Practices
| Repo | Focus | Fichiers clés |
|------|-------|---------------|
| `polakowo/vectorbt` | Vectorized WF | `portfolio/`, `signals/` |
| `kernc/backtesting.py` | Simple but correct | `backtesting/lib.py` |

#### Priorité 3 — Crypto-Specific
| Repo | Focus | Fichiers clés |
|------|-------|---------------|
| `freqtrade/freqtrade` | Crypto strategies | `freqtrade/optimize/`, `hyperopt/` |
| `jesse-ai/jesse` | Crypto backtesting | `jesse/services/` |

**Questions à répondre**:
1. Comment MLFinLab implémente PBO? (code exact)
2. VectorBT gère-t-il le split IS/OOS différemment?
3. Freqtrade a-t-il des guards anti-overfitting?
4. Existe-t-il une implémentation CPCV en Python prête à l'emploi?

**Deliverable**: `docs/GITHUB_REPOS_ANALYSIS.md` avec:
- Code snippets utiles
- Patterns à adopter
- Warnings/anti-patterns identifiés

---

## 📋 ORDRE D'EXÉCUTION RECOMMANDÉ

| Ordre | Task | Effort | Bloquant? |
|-------|------|--------|-----------|
| 1 | **TASK 0: Audit WFE Period Effect** | 1-2h | 🔴 OUI |
| 2 | **TASK 1: Implémenter PBO** | 3-4h | 🔴 OUI |
| 3 | **TASK 5: GitHub Repos (MLFinLab focus)** | 1h | Non |
| 4 | **TASK 2: CPCV** | 2-3h | Non |
| 5 | TASK 4: Variance Reduction | 2-4h | Non |

**STOP CONDITION**: Si TASK 0 confirme effet période → **tous les résultats actuels sont invalides** → repenser le pipeline avant de continuer.

---

## 📚 RÉFÉRENCES OBLIGATOIRES

### Papers
1. **Bailey & López de Prado (2014)** — "The Deflated Sharpe Ratio"
2. **Bailey et al. (2015)** — "The Probability of Backtest Overfitting"
3. **Bailey & López de Prado (2012)** — "The Sharpe Ratio Efficient Frontier"

### Code References
- MLFinLab PBO: `github.com/hudson-and-thames/mlfinlab/blob/master/mlfinlab/cross_validation/`
- CPCV Original: `github.com/hudson-and-thames/mlfinlab/blob/master/mlfinlab/cross_validation/combinatorial.py`

### Livre
- **"Advances in Financial Machine Learning"** — Marcos López de Prado
  - Chapter 11: The Dangers of Backtesting
  - Chapter 12: Backtesting through Cross-Validation

---

## 🎯 DELIVERABLES ATTENDUS (Mis à jour)

| # | Deliverable | Deadline | Status |
|---|-------------|----------|--------|
| 1 | `outputs/audit_wfe_period_effect_report.md` | URGENT | TODO |
| 2 | `crypto_backtest/validation/pbo.py` | URGENT | TODO |
| 3 | `crypto_backtest/validation/cpcv.py` | HIGH | TODO |
| 4 | `docs/GITHUB_REPOS_ANALYSIS.md` | MEDIUM | TODO |
| 5 | Rapport variance reduction | LOW | DÉPRIORITISÉ |

---

## 💬 MESSAGE D'ALEX ATTENDU

```
HHMM INPROGRESS alex-lead -> casey-quant: TASK 0 Audit WFE en cours
Assets: SHIB, ETH, DOT
Dates IS: [DATE] -> [DATE]
Dates OOS: [DATE] -> [DATE]
Buy&Hold IS: X%
Buy&Hold OOS: Y%
Preliminary finding: [PERIOD EFFECT / NO PERIOD EFFECT]
```

---

## ⚠️ RAPPEL CRITIQUE

> **Ne déclare RIEN "PROD ready" tant que:**
> 1. TASK 0 (audit période) n'est pas complété
> 2. PBO n'est pas implémenté et testé
>
> Un WFE > 1.0 sur 7 assets est un **signal d'alarme majeur**.
> La priorité est de comprendre pourquoi, pas de continuer à valider des assets.

---

*Dernière mise à jour: 25 janvier 2026, 16:30 UTC*
*Source: Audit quant externe*
