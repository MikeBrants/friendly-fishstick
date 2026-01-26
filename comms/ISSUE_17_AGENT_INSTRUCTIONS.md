# 🎯 Instructions Agents — Issue #17: Regime-Robust Validation Framework

**Date**: 26 janvier 2026  
**Issue**: [#17](https://github.com/MikeBrants/friendly-fishstick/issues/17)  
**Priorité**: 🔴 CRITIQUE  
**Objectif**: Éliminer le period effect bias via validation multi-régime

---

## 📝 CONTEXTE OBLIGATOIRE (Lire en premier)

### Problème Identifié

L'analyse régime v3 du 26 janvier 2026 a révélé:

```
┌─────────────────────────────────────────────────────────────┐
│  BIAIS CRITIQUE DANS LE BACKTEST ACTUEL                        │
├─────────────────────────────────────────────────────────────┤
│  • ACCUMULATION = 82-86% de la période OOS                      │
│  • MARKDOWN = 6-14% seulement (aucune validation bear)          │
│  • 13/14 assets ont un score composite NÉGATIF                  │
│  • WFE > 1.0 sur 7 assets (period effect, pas edge)            │
│                                                                 │
│  RISQUE: Dégradation live 40-60% si regime shift                │
└─────────────────────────────────────────────────────────────┘
```

### Références Scientifiques Obligatoires

| Paper | Concept | Lien |
|-------|---------|------|
| Bailey & López de Prado (2014) | PBO via CSCV | [SSRN](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2326253) |
| López de Prado (2018) | CPCV Ch.7, 11 | Advances in Financial ML |
| Deep et al. (2025) | 34 independent periods | [arXiv](https://arxiv.org/abs/2512.12924) |

### Fichiers Existants à Connaître

```
crypto_backtest/validation/pbo.py      # GUARD-008 (stub)
crypto_backtest/validation/cpcv.py     # Stub à compléter
crypto_backtest/analysis/regime_v3.py  # Classifier régimes
outputs/regime_analysis/*.csv          # Régimes barre par barre
```

---

## 🟥 TASK 1: CPCV Full Activation

### Méta-informations

| Champ | Valeur |
|-------|--------|
| **Owner** | Alex |
| **Effort** | 6h |
| **Priorité** | 🔴 P0 CRITIQUE |
| **Dépend de** | Rien |
| **Bloque** | TASK 2, TASK 5, TASK 6 |
| **Fichier principal** | `crypto_backtest/validation/cpcv.py` |

### Objectif

Implémenter Combinatorial Purged Cross-Validation pour générer **15 chemins OOS** au lieu d'un seul split fixe 70/30.

### Spécification Technique Détaillée

#### 1.1 Classe CombinatorialPurgedKFold

```python
# Fichier: crypto_backtest/validation/cpcv.py

from itertools import combinations
from typing import Generator, Tuple, List
import numpy as np
import pandas as pd
from scipy.special import comb

class CombinatorialPurgedKFold:
    """
    Combinatorial Purged K-Fold Cross-Validation.
    
    Implémente la méthodologie López de Prado (2018) Ch.7:
    - Purging: Supprime observations proches du split (leakage)
    - Embargo: Gap temporel après test set
    - Combinatorial: Génère toutes les C(n_splits, n_test_splits) combinaisons
    
    Référence:
        López de Prado, M. (2018). Advances in Financial Machine Learning.
        Chapter 7: Cross-Validation in Finance.
    """
    
    def __init__(
        self,
        n_splits: int = 6,
        n_test_splits: int = 2,
        purge_gap: int = 3,
        embargo_pct: float = 0.01
    ):
        """
        Args:
            n_splits: Nombre de blocs temporels (défaut 6)
            n_test_splits: Nombre de blocs en test (défaut 2)
            purge_gap: Barres à purger autour du split (défaut 3)
            embargo_pct: % du dataset en embargo après test (défaut 0.01)
        
        Avec n_splits=6, n_test_splits=2: C(6,2) = 15 combinaisons
        """
        if n_test_splits >= n_splits:
            raise ValueError("n_test_splits must be < n_splits")
        
        self.n_splits = n_splits
        self.n_test_splits = n_test_splits
        self.purge_gap = purge_gap
        self.embargo_pct = embargo_pct
        self.n_combinations = int(comb(n_splits, n_test_splits))
    
    def split(
        self,
        X: pd.DataFrame,
        y: pd.Series = None,
        groups: pd.Series = None
    ) -> Generator[Tuple[np.ndarray, np.ndarray], None, None]:
        """
        Génère les indices train/test avec purging et embargo.
        
        Yields:
            Tuple[train_indices, test_indices] pour chaque combinaison
        """
        n_samples = len(X)
        indices = np.arange(n_samples)
        
        # Découper en n_splits blocs
        fold_sizes = np.full(self.n_splits, n_samples // self.n_splits)
        fold_sizes[:n_samples % self.n_splits] += 1
        fold_bounds = np.cumsum(np.concatenate([[0], fold_sizes]))
        
        # Calculer embargo en nombre de barres
        embargo_size = int(n_samples * self.embargo_pct)
        
        # Générer toutes les combinaisons de test folds
        for test_fold_indices in combinations(range(self.n_splits), self.n_test_splits):
            test_indices = []
            train_indices = []
            
            for fold_idx in range(self.n_splits):
                start = fold_bounds[fold_idx]
                end = fold_bounds[fold_idx + 1]
                fold_indices = indices[start:end]
                
                if fold_idx in test_fold_indices:
                    test_indices.extend(fold_indices)
                else:
                    train_indices.extend(fold_indices)
            
            train_indices = np.array(train_indices)
            test_indices = np.array(test_indices)
            
            # Appliquer purging: retirer barres proches du test set
            if self.purge_gap > 0:
                test_min, test_max = test_indices.min(), test_indices.max()
                purge_mask = (
                    (train_indices < test_min - self.purge_gap) |
                    (train_indices > test_max + self.purge_gap)
                )
                train_indices = train_indices[purge_mask]
            
            # Appliquer embargo: retirer barres juste après test
            if embargo_size > 0:
                test_max = test_indices.max()
                embargo_mask = (
                    (train_indices <= test_max) |
                    (train_indices > test_max + embargo_size)
                )
                train_indices = train_indices[embargo_mask]
            
            yield train_indices, test_indices
    
    def get_n_splits(self) -> int:
        """Retourne le nombre de combinaisons."""
        return self.n_combinations
```

#### 1.2 Fonction de Calcul PBO

```python
# Ajouter dans crypto_backtest/validation/pbo.py

def calculate_pbo(
    strategy_returns: np.ndarray,
    cpcv: CombinatorialPurgedKFold,
    data: pd.DataFrame,
    risk_free: float = 0.0
) -> dict:
    """
    Calcule Probability of Backtest Overfitting via CSCV.
    
    Méthodologie Bailey & López de Prado (2014):
    1. Pour chaque combinaison train/test:
       - Calculer Sharpe de chaque stratégie sur train (IS)
       - Identifier la "meilleure" stratégie (max Sharpe IS)
       - Calculer le rang OOS de cette stratégie
    2. PBO = proportion où rang OOS > médiane
    
    Args:
        strategy_returns: Matrice (n_strategies, n_periods) des returns
        cpcv: Instance de CombinatorialPurgedKFold
        data: DataFrame avec index temporel
        risk_free: Taux sans risque (défaut 0)
    
    Returns:
        dict avec:
            - pbo: float [0, 1] probabilité d'overfitting
            - logits: array des rangs relatifs OOS
            - threshold: seuil de significance
            - is_overfit: bool (pbo > 0.30)
    """
    from scipy.stats import rankdata
    
    n_strategies = strategy_returns.shape[0]
    relative_ranks = []
    
    for train_idx, test_idx in cpcv.split(data):
        # Calculer Sharpe IS pour chaque stratégie
        is_returns = strategy_returns[:, train_idx]
        is_sharpes = np.array([
            _sharpe_ratio(r, risk_free) for r in is_returns
        ])
        
        # Identifier meilleure stratégie IS
        best_is_strategy = np.argmax(is_sharpes)
        
        # Calculer rang OOS de cette stratégie
        oos_returns = strategy_returns[:, test_idx]
        oos_sharpes = np.array([
            _sharpe_ratio(r, risk_free) for r in oos_returns
        ])
        
        # Rang (1 = meilleur, n = pire)
        ranks = rankdata(-oos_sharpes)  # négatif car on veut max = rang 1
        oos_rank = ranks[best_is_strategy]
        
        # Rang relatif [0, 1] (0 = meilleur, 1 = pire)
        relative_rank = (oos_rank - 1) / (n_strategies - 1)
        relative_ranks.append(relative_rank)
    
    relative_ranks = np.array(relative_ranks)
    
    # PBO = proportion où rang OOS > médiane (0.5)
    pbo = np.mean(relative_ranks > 0.5)
    
    # Logit transformation pour analyse
    # Eviter log(0) et log(inf)
    eps = 1e-6
    clamped_ranks = np.clip(relative_ranks, eps, 1 - eps)
    logits = np.log(clamped_ranks / (1 - clamped_ranks))
    
    return {
        'pbo': pbo,
        'logits': logits,
        'relative_ranks': relative_ranks,
        'threshold': 0.30,  # López de Prado threshold
        'is_overfit': pbo > 0.30,
        'n_combinations': len(relative_ranks),
        'verdict': _pbo_verdict(pbo)
    }


def _sharpe_ratio(returns: np.ndarray, risk_free: float = 0.0) -> float:
    """Calcule Sharpe ratio annualisé (1H = 8760 périodes/an)."""
    excess = returns - risk_free / 8760
    if len(excess) < 2 or np.std(excess) == 0:
        return 0.0
    return np.mean(excess) / np.std(excess) * np.sqrt(8760)


def _pbo_verdict(pbo: float) -> str:
    """Retourne verdict textuel."""
    if pbo < 0.15:
        return "PASS - Low overfitting risk"
    elif pbo < 0.30:
        return "MARGINAL - Proceed with caution"
    else:
        return "FAIL - High overfitting probability"
```

#### 1.3 Intégration Guard Pipeline

```python
# Modifier crypto_backtest/validation/guards.py

def guard_008_pbo(
    returns_matrix: np.ndarray,
    data: pd.DataFrame,
    threshold: float = 0.30
) -> dict:
    """
    GUARD-008: Probability of Backtest Overfitting.
    
    Args:
        returns_matrix: Shape (n_trials, n_periods)
        data: DataFrame source avec timestamps
        threshold: PBO max pour PASS (défaut 0.30)
    
    Returns:
        dict avec pass/fail et détails
    """
    from .cpcv import CombinatorialPurgedKFold
    from .pbo import calculate_pbo
    
    cpcv = CombinatorialPurgedKFold(
        n_splits=6,
        n_test_splits=2,
        purge_gap=3,
        embargo_pct=0.01
    )
    
    result = calculate_pbo(returns_matrix, cpcv, data)
    
    return {
        'guard': 'guard_008_pbo',
        'passed': result['pbo'] < threshold,
        'value': result['pbo'],
        'threshold': threshold,
        'verdict': result['verdict'],
        'details': {
            'n_combinations': result['n_combinations'],
            'mean_relative_rank': float(np.mean(result['relative_ranks'])),
            'std_relative_rank': float(np.std(result['relative_ranks'])),
        }
    }
```

### Critères d'Acceptance TASK 1

- [ ] `CombinatorialPurgedKFold` génère exactement 15 combinaisons pour n_splits=6, n_test_splits=2
- [ ] Purging retire les barres dans `[-purge_gap, +purge_gap]` du test set
- [ ] Embargo retire les barres dans `[test_max, test_max + embargo_size]` du train set
- [ ] `calculate_pbo()` retourne PBO dans [0, 1]
- [ ] `guard_008_pbo()` intégré dans pipeline guards
- [ ] Tests unitaires: `tests/validation/test_cpcv.py` (min 10 tests)
- [ ] Test sur ETH: PBO calculé et documenté

### Commande de Test

```bash
# Unit tests
pytest tests/validation/test_cpcv.py -v

# Intégration test sur ETH
python -c "
from crypto_backtest.validation.cpcv import CombinatorialPurgedKFold
from crypto_backtest.validation.pbo import calculate_pbo
import pandas as pd
import numpy as np

# Simuler 100 stratégies, 17520 périodes
np.random.seed(42)
returns = np.random.randn(100, 17520) * 0.001
data = pd.DataFrame(index=pd.date_range('2024-01-01', periods=17520, freq='1H'))

cpcv = CombinatorialPurgedKFold(n_splits=6, n_test_splits=2)
result = calculate_pbo(returns, cpcv, data)
print(f'PBO: {result[\"pbo\"]:.3f}')
print(f'Verdict: {result[\"verdict\"]}')
"
```

### Livrable

```
1545 DONE alex-lead -> casey-quant: TASK 1 CPCV terminé
Fichiers:
  - crypto_backtest/validation/cpcv.py (CombinatorialPurgedKFold)
  - crypto_backtest/validation/pbo.py (calculate_pbo)
  - crypto_backtest/validation/guards.py (guard_008_pbo)
  - tests/validation/test_cpcv.py (15 tests)
Résultats ETH:
  - PBO: X.XXX
  - Verdict: [PASS/MARGINAL/FAIL]
PR: #XX
```

---

## 🟥 TASK 2: Regime-Stratified Walk-Forward

### Méta-informations

| Champ | Valeur |
|-------|--------|
| **Owner** | Alex |
| **Effort** | 8h |
| **Priorité** | 🔴 P0 CRITIQUE |
| **Dépend de** | TASK 1 |
| **Bloque** | TASK 4 |
| **Fichier principal** | `crypto_backtest/validation/regime_stratified.py` |

### Objectif

Garantir que chaque fold CPCV contient un **mix représentatif de régimes** (min 15% de chaque régime majeur).

### Spécification Technique Détaillée

#### 2.1 Classe RegimeStratifiedCPCV

```python
# Fichier: crypto_backtest/validation/regime_stratified.py

import numpy as np
import pandas as pd
from typing import Generator, Tuple, Dict, List
from .cpcv import CombinatorialPurgedKFold

class RegimeStratifiedCPCV:
    """
    CPCV avec stratification par régime.
    
    Garantit que chaque fold contient un mix représentatif de régimes
    au lieu de splits purement chronologiques.
    
    Problème résolu:
        Split chronologique peut donner 100% ACCUMULATION dans un fold
        et 100% MARKDOWN dans un autre → biais de sélection.
    
    Solution:
        1. Identifier blocs contigus de même régime
        2. Distribuer ces blocs équitablement entre folds
        3. Appliquer CPCV sur les folds stratifiés
    """
    
    MAJOR_REGIMES = ['ACCUMULATION', 'MARKDOWN', 'MARKUP', 'SIDEWAYS']
    MIN_REGIME_PCT = 0.15  # 15% minimum par régime dans chaque fold
    
    def __init__(
        self,
        n_splits: int = 6,
        n_test_splits: int = 2,
        purge_gap: int = 3,
        embargo_pct: float = 0.01,
        regime_column: str = 'crypto_regime',
        min_regime_pct: float = 0.15
    ):
        """
        Args:
            n_splits: Nombre de folds (défaut 6)
            n_test_splits: Folds en test (défaut 2)
            purge_gap: Barres à purger (défaut 3)
            embargo_pct: % embargo (défaut 0.01)
            regime_column: Colonne contenant le régime
            min_regime_pct: % minimum de chaque régime par fold
        """
        self.n_splits = n_splits
        self.n_test_splits = n_test_splits
        self.purge_gap = purge_gap
        self.embargo_pct = embargo_pct
        self.regime_column = regime_column
        self.min_regime_pct = min_regime_pct
        
        self._base_cpcv = CombinatorialPurgedKFold(
            n_splits=n_splits,
            n_test_splits=n_test_splits,
            purge_gap=purge_gap,
            embargo_pct=embargo_pct
        )
    
    def _identify_regime_blocks(self, regimes: pd.Series) -> List[Dict]:
        """
        Identifie les blocs contigus de même régime.
        
        Returns:
            Liste de dicts avec 'regime', 'start', 'end', 'size'
        """
        blocks = []
        current_regime = regimes.iloc[0]
        block_start = 0
        
        for i, regime in enumerate(regimes):
            if regime != current_regime:
                blocks.append({
                    'regime': current_regime,
                    'start': block_start,
                    'end': i,
                    'size': i - block_start
                })
                current_regime = regime
                block_start = i
        
        # Dernier bloc
        blocks.append({
            'regime': current_regime,
            'start': block_start,
            'end': len(regimes),
            'size': len(regimes) - block_start
        })
        
        return blocks
    
    def _distribute_blocks_to_folds(
        self,
        blocks: List[Dict],
        n_folds: int
    ) -> List[List[int]]:
        """
        Distribue les blocs entre folds en maximisant la diversité de régimes.
        
        Algorithme:
            1. Grouper blocs par régime
            2. Pour chaque régime, round-robin vers les folds
            3. Vérifier contrainte min_regime_pct
        
        Returns:
            Liste de listes d'indices de blocs par fold
        """
        # Grouper par régime
        regime_blocks = {r: [] for r in self.MAJOR_REGIMES}
        other_blocks = []
        
        for i, block in enumerate(blocks):
            regime = block['regime']
            if regime in regime_blocks:
                regime_blocks[regime].append(i)
            else:
                other_blocks.append(i)
        
        # Initialiser folds
        folds = [[] for _ in range(n_folds)]
        
        # Round-robin pour chaque régime majeur
        for regime, block_indices in regime_blocks.items():
            for i, block_idx in enumerate(block_indices):
                fold_idx = i % n_folds
                folds[fold_idx].append(block_idx)
        
        # Distribuer les autres blocs
        for i, block_idx in enumerate(other_blocks):
            fold_idx = i % n_folds
            folds[fold_idx].append(block_idx)
        
        return folds
    
    def _blocks_to_indices(self, blocks: List[Dict], block_indices: List[int]) -> np.ndarray:
        """
        Convertit liste de block indices en array d'indices de barres.
        """
        indices = []
        for block_idx in sorted(block_indices):
            block = blocks[block_idx]
            indices.extend(range(block['start'], block['end']))
        return np.array(indices)
    
    def _validate_fold_distribution(
        self,
        fold_indices: np.ndarray,
        regimes: pd.Series
    ) -> Dict[str, float]:
        """
        Vérifie la distribution des régimes dans un fold.
        
        Returns:
            Dict regime -> percentage
        """
        fold_regimes = regimes.iloc[fold_indices]
        distribution = fold_regimes.value_counts(normalize=True).to_dict()
        return distribution
    
    def split(
        self,
        X: pd.DataFrame,
        regimes: pd.Series
    ) -> Generator[Tuple[np.ndarray, np.ndarray, Dict], None, None]:
        """
        Génère les splits stratifiés par régime.
        
        Args:
            X: DataFrame des features
            regimes: Series des régimes (même index que X)
        
        Yields:
            Tuple[train_indices, test_indices, metadata]
            metadata contient la distribution des régimes par split
        """
        # Identifier blocs
        blocks = self._identify_regime_blocks(regimes)
        
        # Distribuer entre folds
        fold_block_indices = self._distribute_blocks_to_folds(blocks, self.n_splits)
        
        # Convertir en indices
        fold_indices = [
            self._blocks_to_indices(blocks, block_indices)
            for block_indices in fold_block_indices
        ]
        
        # Générer combinaisons CPCV
        from itertools import combinations
        
        for test_fold_ids in combinations(range(self.n_splits), self.n_test_splits):
            # Construire train et test
            test_indices = np.concatenate([
                fold_indices[i] for i in test_fold_ids
            ])
            train_indices = np.concatenate([
                fold_indices[i] for i in range(self.n_splits)
                if i not in test_fold_ids
            ])
            
            # Trier pour maintenir l'ordre temporel
            test_indices = np.sort(test_indices)
            train_indices = np.sort(train_indices)
            
            # Appliquer purging
            if self.purge_gap > 0:
                test_min, test_max = test_indices.min(), test_indices.max()
                purge_mask = (
                    (train_indices < test_min - self.purge_gap) |
                    (train_indices > test_max + self.purge_gap)
                )
                train_indices = train_indices[purge_mask]
            
            # Appliquer embargo
            embargo_size = int(len(X) * self.embargo_pct)
            if embargo_size > 0:
                test_max = test_indices.max()
                embargo_mask = (
                    (train_indices <= test_max) |
                    (train_indices > test_max + embargo_size)
                )
                train_indices = train_indices[embargo_mask]
            
            # Métadonnées
            metadata = {
                'test_folds': test_fold_ids,
                'train_regime_distribution': self._validate_fold_distribution(train_indices, regimes),
                'test_regime_distribution': self._validate_fold_distribution(test_indices, regimes),
                'train_size': len(train_indices),
                'test_size': len(test_indices),
            }
            
            yield train_indices, test_indices, metadata
    
    def validate_stratification(self, regimes: pd.Series) -> Dict:
        """
        Vérifie que la stratification respecte les contraintes.
        
        Returns:
            Dict avec validation status et détails
        """
        blocks = self._identify_regime_blocks(regimes)
        fold_block_indices = self._distribute_blocks_to_folds(blocks, self.n_splits)
        
        results = {
            'valid': True,
            'folds': [],
            'violations': []
        }
        
        for fold_idx, block_indices in enumerate(fold_block_indices):
            fold_indices = self._blocks_to_indices(blocks, block_indices)
            distribution = self._validate_fold_distribution(fold_indices, regimes)
            
            fold_result = {
                'fold': fold_idx,
                'distribution': distribution,
                'valid': True
            }
            
            # Vérifier contrainte min_regime_pct
            for regime in self.MAJOR_REGIMES:
                pct = distribution.get(regime, 0)
                if pct < self.min_regime_pct:
                    fold_result['valid'] = False
                    results['valid'] = False
                    results['violations'].append({
                        'fold': fold_idx,
                        'regime': regime,
                        'actual_pct': pct,
                        'required_pct': self.min_regime_pct
                    })
            
            results['folds'].append(fold_result)
        
        return results
```

#### 2.2 Loader de Régimes

```python
# Ajouter dans crypto_backtest/validation/regime_stratified.py

def load_regimes_for_asset(asset: str) -> pd.Series:
    """
    Charge les régimes pré-calculés pour un asset.
    
    Args:
        asset: Code asset (ex: 'ETH')
    
    Returns:
        Series indexée par timestamp avec régimes
    """
    import os
    
    path = f"outputs/regime_analysis/{asset}_regimes.csv"
    if not os.path.exists(path):
        raise FileNotFoundError(f"Regime file not found: {path}. Run regime analysis first.")
    
    df = pd.read_csv(path, parse_dates=['timestamp'], index_col='timestamp')
    
    if 'crypto_regime' not in df.columns:
        raise ValueError(f"Column 'crypto_regime' not found in {path}")
    
    return df['crypto_regime']
```

### Critères d'Acceptance TASK 2

- [ ] `RegimeStratifiedCPCV` génère 15 combinaisons stratifiées
- [ ] Chaque fold contient **min 15% de ACCUMULATION, MARKDOWN, MARKUP**
- [ ] `validate_stratification()` retourne violations si contrainte non respectée
- [ ] Metadata inclut distribution régimes pour chaque split
- [ ] Intégration avec `calculate_pbo()` de TASK 1
- [ ] Tests unitaires: `tests/validation/test_regime_stratified.py`
- [ ] Test sur ETH avec régimes réels

### Commande de Test

```bash
# Vérifier stratification ETH
python -c "
from crypto_backtest.validation.regime_stratified import RegimeStratifiedCPCV, load_regimes_for_asset
import pandas as pd

regimes = load_regimes_for_asset('ETH')
data = pd.DataFrame(index=regimes.index)

cpcv = RegimeStratifiedCPCV(n_splits=6, n_test_splits=2, min_regime_pct=0.10)
validation = cpcv.validate_stratification(regimes)

print(f'Stratification valid: {validation[\"valid\"]}')
if not validation['valid']:
    print('Violations:')
    for v in validation['violations']:
        print(f'  Fold {v[\"fold\"]}: {v[\"regime\"]} = {v[\"actual_pct\"]*100:.1f}% < {v[\"required_pct\"]*100:.1f}%')
"
```

### Livrable

```
1730 DONE alex-lead -> casey-quant: TASK 2 Regime-Stratified terminé
Fichiers:
  - crypto_backtest/validation/regime_stratified.py
  - tests/validation/test_regime_stratified.py
Résultats ETH:
  - Stratification valid: [True/False]
  - ACCUMULATION range: [X% - Y%] par fold
  - MARKDOWN range: [X% - Y%] par fold
PR: #XX
```

---

## 🟥 TASK 3: Isolated Regime Stress Tests

### Méta-informations

| Champ | Valeur |
|-------|--------|
| **Owner** | Jordan |
| **Effort** | 4h |
| **Priorité** | 🔴 P0 CRITIQUE |
| **Dépend de** | Régimes pré-calculés |
| **Bloque** | Recommandations live |
| **Fichier principal** | `scripts/run_regime_stress_test.py` |

### Objectif

Backtester la stratégie **uniquement sur les barres d'un régime donné** pour identifier si l'edge survit en conditions bear.

### Spécification Technique Détaillée

#### 3.1 Script de Stress Test

```python
#!/usr/bin/env python3
# Fichier: scripts/run_regime_stress_test.py

"""
Régime Stress Test
==================

Backtest la stratégie Ichimoku+ATR sur un régime isolé.

Usage:
    python scripts/run_regime_stress_test.py --asset ETH --regime MARKDOWN
    python scripts/run_regime_stress_test.py --asset ETH --regime ACCUMULATION --trials 100
    python scripts/run_regime_stress_test.py --all-assets --regime MARKDOWN

Régimes supportés:
    ACCUMULATION, MARKDOWN, MARKUP, DISTRIBUTION, CAPITULATION, RECOVERY
    SIDEWAYS, WEAK_BULL, WEAK_BEAR, STRONG_BULL, STRONG_BEAR (trend regimes)
    COMPRESSED, NORMAL, ELEVATED, EXTREME (volatility regimes)
"""

import argparse
import sys
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

# Ajouter root au path
sys.path.insert(0, str(Path(__file__).parent.parent))

from crypto_backtest.data.loader import load_asset_data
from crypto_backtest.strategy.ichimoku_atr import IchimokuATRStrategy
from crypto_backtest.backtest.engine import BacktestEngine
from crypto_backtest.config.asset_config import get_asset_params


PROD_ASSETS = [
    'SHIB', 'DOT', 'TIA', 'NEAR', 'DOGE', 'ANKR', 'ETH',
    'JOE', 'YGG', 'MINA', 'CAKE', 'RUNE', 'EGLD', 'AVAX'
]

CRYPTO_REGIMES = ['ACCUMULATION', 'MARKDOWN', 'MARKUP', 'DISTRIBUTION', 'CAPITULATION', 'RECOVERY']
TREND_REGIMES = ['SIDEWAYS', 'WEAK_BULL', 'WEAK_BEAR', 'STRONG_BULL', 'STRONG_BEAR', 'REVERSAL']
VOL_REGIMES = ['COMPRESSED', 'NORMAL', 'ELEVATED', 'EXTREME']


def load_regime_data(asset: str) -> pd.DataFrame:
    """Charge les données de régime pour un asset."""
    path = Path(f"outputs/regime_analysis/{asset}_regimes.csv")
    if not path.exists():
        raise FileNotFoundError(f"Regime data not found: {path}")
    
    df = pd.read_csv(path, parse_dates=['timestamp'])
    df.set_index('timestamp', inplace=True)
    return df


def filter_by_regime(
    data: pd.DataFrame,
    regime_data: pd.DataFrame,
    regime: str,
    regime_column: str
) -> pd.DataFrame:
    """
    Filtre les données OHLCV pour ne garder que les barres d'un régime donné.
    
    IMPORTANT: Utilise le régime à l'ENTRÉE, pas à la sortie.
    """
    # Aligner les index
    common_index = data.index.intersection(regime_data.index)
    data_aligned = data.loc[common_index]
    regime_aligned = regime_data.loc[common_index]
    
    # Filtrer
    mask = regime_aligned[regime_column] == regime
    filtered = data_aligned[mask]
    
    return filtered


def run_stress_test(
    asset: str,
    regime: str,
    trials: int = 50
) -> Dict:
    """
    Exécute un stress test sur un régime isolé.
    
    Args:
        asset: Code asset
        regime: Régime à tester
        trials: Nombre de trials Optuna (réduit car moins de data)
    
    Returns:
        Dict avec résultats détaillés
    """
    print(f"\n{'='*60}")
    print(f"STRESS TEST: {asset} sur régime {regime}")
    print(f"{'='*60}\n")
    
    # Déterminer colonne de régime
    if regime in CRYPTO_REGIMES:
        regime_column = 'crypto_regime'
    elif regime in TREND_REGIMES:
        regime_column = 'trend_regime'
    elif regime in VOL_REGIMES:
        regime_column = 'volatility_regime'
    else:
        raise ValueError(f"Unknown regime: {regime}")
    
    # Charger données
    data = load_asset_data(asset)
    regime_data = load_regime_data(asset)
    
    print(f"Données totales: {len(data)} barres")
    
    # Filtrer par régime
    filtered_data = filter_by_regime(data, regime_data, regime, regime_column)
    
    n_bars = len(filtered_data)
    pct = n_bars / len(data) * 100
    print(f"Barres {regime}: {n_bars} ({pct:.1f}%)")
    
    if n_bars < 500:
        print(f"\n⚠️ ATTENTION: Seulement {n_bars} barres - résultats peu fiables")
    
    if n_bars < 100:
        return {
            'asset': asset,
            'regime': regime,
            'status': 'SKIP',
            'reason': f'Insufficient data ({n_bars} bars < 100 minimum)',
            'bars': n_bars,
            'pct': pct
        }
    
    # Récupérer params PROD
    try:
        params = get_asset_params(asset)
    except KeyError:
        return {
            'asset': asset,
            'regime': regime,
            'status': 'ERROR',
            'reason': f'Asset {asset} not in asset_config.py'
        }
    
    # Backtester avec params figés
    strategy = IchimokuATRStrategy(**params)
    engine = BacktestEngine(strategy)
    
    try:
        results = engine.run(filtered_data)
    except Exception as e:
        return {
            'asset': asset,
            'regime': regime,
            'status': 'ERROR',
            'reason': str(e)
        }
    
    # Calculer métriques
    sharpe = results.get('sharpe_ratio', 0)
    max_dd = results.get('max_drawdown', 0)
    n_trades = results.get('n_trades', 0)
    win_rate = results.get('win_rate', 0)
    total_return = results.get('total_return', 0)
    
    # Verdict
    if sharpe < 0:
        verdict = '🔴 FAIL - Sharpe négatif'
        status = 'FAIL'
    elif sharpe < 0.5:
        verdict = '⚠️ MARGINAL - Sharpe faible'
        status = 'MARGINAL'
    else:
        verdict = '✅ PASS - Sharpe acceptable'
        status = 'PASS'
    
    result = {
        'asset': asset,
        'regime': regime,
        'status': status,
        'verdict': verdict,
        'bars': n_bars,
        'pct': pct,
        'sharpe': sharpe,
        'max_dd': max_dd,
        'n_trades': n_trades,
        'win_rate': win_rate,
        'total_return': total_return
    }
    
    print(f"\nRésultats:")
    print(f"  Sharpe: {sharpe:.2f}")
    print(f"  Max DD: {max_dd:.2%}")
    print(f"  Trades: {n_trades}")
    print(f"  Win Rate: {win_rate:.1%}")
    print(f"  Return: {total_return:.2%}")
    print(f"\n  Verdict: {verdict}")
    
    return result


def main():
    parser = argparse.ArgumentParser(description='Regime Stress Test')
    parser.add_argument('--asset', type=str, help='Asset to test')
    parser.add_argument('--all-assets', action='store_true', help='Test all PROD assets')
    parser.add_argument('--regime', type=str, required=True, help='Regime to isolate')
    parser.add_argument('--trials', type=int, default=50, help='Optuna trials')
    parser.add_argument('--output', type=str, help='Output CSV path')
    
    args = parser.parse_args()
    
    if not args.asset and not args.all_assets:
        parser.error('--asset or --all-assets required')
    
    assets = PROD_ASSETS if args.all_assets else [args.asset]
    results = []
    
    for asset in assets:
        try:
            result = run_stress_test(asset, args.regime, args.trials)
            results.append(result)
        except Exception as e:
            print(f"\n❌ Error testing {asset}: {e}")
            results.append({
                'asset': asset,
                'regime': args.regime,
                'status': 'ERROR',
                'reason': str(e)
            })
    
    # Résumé
    print(f"\n{'='*60}")
    print(f"RÉSUMÉ STRESS TEST: {args.regime}")
    print(f"{'='*60}\n")
    
    df = pd.DataFrame(results)
    print(df.to_string(index=False))
    
    # Sauvegarder
    if args.output:
        output_path = args.output
    else:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_path = f"outputs/stress_test_{args.regime}_{timestamp}.csv"
    
    df.to_csv(output_path, index=False)
    print(f"\nSauvegardé: {output_path}")
    
    # Alerte critique
    fails = df[df['status'] == 'FAIL']
    if len(fails) > 0:
        print(f"\n🔴 ALERTE: {len(fails)} assets FAIL sur {args.regime}!")
        print("   La stratégie ne survit PAS dans ce régime.")
        print("   Recommandation: FLAT ou hedge si ce régime est détecté live.")


if __name__ == '__main__':
    main()
```

### Critères d'Acceptance TASK 3

- [ ] Script `run_regime_stress_test.py` fonctionnel
- [ ] Supporte `--asset`, `--all-assets`, `--regime`
- [ ] Filtre par `entry_regime` (pas exit)
- [ ] Output CSV avec Sharpe, MaxDD, Trades, WinRate par asset
- [ ] Alerte si Sharpe < 0 sur MARKDOWN
- [ ] Test sur les 14 assets PROD pour MARKDOWN

### Commandes de Test

```bash
# Test ETH sur MARKDOWN
python scripts/run_regime_stress_test.py --asset ETH --regime MARKDOWN

# Test tous les assets sur MARKDOWN (CRITIQUE)
python scripts/run_regime_stress_test.py --all-assets --regime MARKDOWN

# Test sur ACCUMULATION (baseline)
python scripts/run_regime_stress_test.py --all-assets --regime ACCUMULATION
```

### Livrable

```
1400 DONE jordan-dev -> casey-quant: TASK 3 Stress Test terminé
Fichiers:
  - scripts/run_regime_stress_test.py
  - outputs/stress_test_MARKDOWN_20260127_XXXXXX.csv
Résultats MARKDOWN:
  - PASS: X assets
  - MARGINAL: X assets
  - FAIL: X assets
  - Assets FAIL: [liste]
Recommandation: [action]
```

---

## 🟧 TASK 4: Synthetic Regime Injection

### Méta-informations

| Champ | Valeur |
|-------|--------|
| **Owner** | Alex |
| **Effort** | 12h |
| **Priorité** | 🟡 P1 HIGH |
| **Dépend de** | TASK 2 |
| **Bloque** | Rien |
| **Fichier principal** | `crypto_backtest/validation/synthetic.py` |

### Objectif

Générer des **périodes bear synthétiques** pour augmenter les données MARKDOWN et tester la robustesse sans attendre un vrai bear market.

### Spécification Technique Détaillée

```python
# Fichier: crypto_backtest/validation/synthetic.py

import numpy as np
import pandas as pd
from typing import Optional, Dict


class SyntheticRegimeGenerator:
    """
    Génère des scénarios de marché synthétiques pour stress testing.
    
    Méthodes:
    1. Block Bootstrap: Resample blocs existants d'un régime
    2. Stylized Facts: Monte Carlo avec contraintes statistiques
    3. GARCH: Simulation avec volatilité conditionnelle
    
    Référence:
        AWS (2025) "Enhancing Equity Strategy Backtesting with Synthetic Data"
    """
    
    def __init__(self, random_state: int = 42):
        self.rng = np.random.default_rng(random_state)
    
    def bootstrap_regime_blocks(
        self,
        data: pd.DataFrame,
        regime_data: pd.DataFrame,
        source_regime: str,
        target_regime: str = None,
        injection_pct: float = 0.20,
        block_size: int = 24  # 24h en 1H
    ) -> pd.DataFrame:
        """
        Resample des blocs d'un régime source et les injecte.
        
        Args:
            data: OHLCV original
            regime_data: DataFrame avec régimes
            source_regime: Régime à resampler (ex: 'MARKDOWN')
            target_regime: Régime à remplacer (défaut: 'ACCUMULATION')
            injection_pct: % de barres à remplacer
            block_size: Taille des blocs (conserve autocorrélation)
        
        Returns:
            DataFrame augmenté avec blocs synthétiques
        """
        if target_regime is None:
            target_regime = 'ACCUMULATION'
        
        # Identifier barres source
        source_mask = regime_data['crypto_regime'] == source_regime
        source_indices = np.where(source_mask)[0]
        
        if len(source_indices) < block_size:
            raise ValueError(f"Not enough {source_regime} bars for bootstrap")
        
        # Identifier barres target à remplacer
        target_mask = regime_data['crypto_regime'] == target_regime
        target_indices = np.where(target_mask)[0]
        
        n_replace = int(len(target_indices) * injection_pct)
        
        # Sélectionner blocs à remplacer (aléatoire)
        replace_starts = self.rng.choice(
            target_indices[:-block_size],
            size=n_replace // block_size,
            replace=False
        )
        
        # Copier data
        augmented = data.copy()
        augmented_regime = regime_data.copy()
        
        # Remplacer blocs
        for target_start in replace_starts:
            # Choisir bloc source aléatoire
            source_start_options = source_indices[source_indices <= len(data) - block_size]
            source_start = self.rng.choice(source_start_options)
            
            # Copier returns (pas prix absolus!)
            source_returns = data.iloc[source_start:source_start + block_size]['close'].pct_change()
            
            # Appliquer au target
            target_slice = slice(target_start, target_start + block_size)
            base_price = augmented.iloc[target_start]['close']
            
            # Reconstruire prix à partir des returns
            new_prices = [base_price]
            for ret in source_returns.dropna():
                new_prices.append(new_prices[-1] * (1 + ret))
            
            augmented.iloc[target_slice, augmented.columns.get_loc('close')] = new_prices[:block_size]
            augmented_regime.iloc[target_slice, augmented_regime.columns.get_loc('crypto_regime')] = source_regime
        
        return augmented, augmented_regime
    
    def generate_stylized_bear(
        self,
        n_bars: int,
        base_price: float = 100.0,
        params: Optional[Dict] = None
    ) -> pd.DataFrame:
        """
        Génère une série bear synthétique respectant les stylized facts.
        
        Stylized Facts Bear Market:
        - Drift négatif (-0.5% à -2% par jour)
        - Volatilité élevée (1.5x à 3x normale)
        - Skewness négative (crashes)
        - Fat tails (kurtosis > 3)
        - Volatilité clustering (GARCH effect)
        
        Args:
            n_bars: Nombre de barres à générer
            base_price: Prix initial
            params: Override des paramètres par défaut
        
        Returns:
            DataFrame OHLCV synthétique
        """
        # Params par défaut bear market
        default_params = {
            'hourly_drift': -0.0005,     # -0.05% par heure (~-1.2%/jour)
            'hourly_vol': 0.015,         # 1.5% vol horaire
            'skewness': -0.5,            # Skew négatif
            'kurtosis': 5.0,             # Fat tails
            'garch_alpha': 0.1,          # GARCH alpha
            'garch_beta': 0.85,          # GARCH beta
        }
        
        if params:
            default_params.update(params)
        p = default_params
        
        # Générer returns avec GARCH(1,1)
        returns = np.zeros(n_bars)
        variance = np.zeros(n_bars)
        variance[0] = p['hourly_vol'] ** 2
        
        for t in range(1, n_bars):
            # GARCH variance
            variance[t] = (
                (1 - p['garch_alpha'] - p['garch_beta']) * p['hourly_vol']**2 +
                p['garch_alpha'] * returns[t-1]**2 +
                p['garch_beta'] * variance[t-1]
            )
            
            # Générer return avec skewed t-distribution
            z = self.rng.standard_t(df=4)  # Fat tails
            z = z - p['skewness'] * (z**2 - 1) / 2  # Skew adjustment
            
            returns[t] = p['hourly_drift'] + np.sqrt(variance[t]) * z
        
        # Construire prix
        prices = base_price * np.cumprod(1 + returns)
        
        # Construire OHLCV
        df = pd.DataFrame({
            'open': prices,
            'high': prices * (1 + np.abs(self.rng.normal(0, 0.005, n_bars))),
            'low': prices * (1 - np.abs(self.rng.normal(0, 0.005, n_bars))),
            'close': prices,
            'volume': self.rng.lognormal(10, 1, n_bars)
        })
        
        # Corriger high/low
        df['high'] = df[['open', 'close', 'high']].max(axis=1)
        df['low'] = df[['open', 'close', 'low']].min(axis=1)
        
        return df
    
    def validate_stylized_facts(self, returns: np.ndarray) -> Dict:
        """
        Vérifie que les returns synthétiques respectent les stylized facts.
        
        Returns:
            Dict avec métriques et validation
        """
        from scipy import stats
        
        mean_ret = np.mean(returns)
        std_ret = np.std(returns)
        skew = stats.skew(returns)
        kurt = stats.kurtosis(returns)
        
        # Ljung-Box test pour autocorrélation des carrés (vol clustering)
        squared = returns ** 2
        lb_stat, lb_pvalue = stats.acorr_ljungbox(squared, lags=[10], return_df=False)
        
        return {
            'mean_return': mean_ret,
            'volatility': std_ret,
            'skewness': skew,
            'kurtosis': kurt,
            'vol_clustering_pvalue': lb_pvalue[0],
            'is_bear': mean_ret < 0,
            'has_negative_skew': skew < 0,
            'has_fat_tails': kurt > 0,
            'has_vol_clustering': lb_pvalue[0] < 0.05
        }
```

### Critères d'Acceptance TASK 4

- [ ] `bootstrap_regime_blocks()` fonctionnel
- [ ] `generate_stylized_bear()` produit returns avec skew < 0, kurtosis > 3
- [ ] `validate_stylized_facts()` confirme les propriétés
- [ ] Test backtest sur data augmenté (+20% MARKDOWN)
- [ ] Comparaison Sharpe: original vs augmented

### Livrable

```
1800 DONE alex-lead -> casey-quant: TASK 4 Synthetic Injection terminé
Fichiers:
  - crypto_backtest/validation/synthetic.py
  - tests/validation/test_synthetic.py
Résultats:
  - Bootstrap validation: [PASS/FAIL]
  - Stylized facts validation: [PASS/FAIL]
  - Sharpe original ETH: X.XX
  - Sharpe augmented (+20% MARKDOWN): X.XX
  - Dégradation: X%
```

---

## 🟧 TASK 5: Multi-Period Independent Validation

### Méta-informations

| Champ | Valeur |
|-------|--------|
| **Owner** | Jordan |
| **Effort** | 4h |
| **Priorité** | 🟡 P1 HIGH |
| **Dépend de** | TASK 1 |
| **Bloque** | Rien |
| **Fichier principal** | `scripts/run_multi_period_validation.py` |

### Objectif

Implémenter **34 périodes de test indépendantes** (Deep et al., 2025) pour calculer le Consistency Ratio.

### Spécification

```python
# Fichier: scripts/run_multi_period_validation.py

def rolling_walk_forward(
    data: pd.DataFrame,
    strategy_params: dict,
    n_windows: int = 34,
    train_pct: float = 0.60,
    step_pct: float = 0.03
) -> Dict:
    """
    34 rolling windows indépendants.
    
    Window 1: IS [0-60%] → OOS [60-63%]
    Window 2: IS [3-63%] → OOS [63-66%]
    ...
    Window 34: IS [37-97%] → OOS [97-100%]
    
    Returns:
        Dict avec:
        - consistency_ratio: % windows avec Sharpe OOS > 0
        - sharpes_oos: array des Sharpes par window
        - worst_window: index de la pire window
        - best_window: index de la meilleure window
    """
    n_bars = len(data)
    train_size = int(n_bars * train_pct)
    test_size = int(n_bars * step_pct)
    step_size = test_size
    
    sharpes = []
    window_details = []
    
    for i in range(n_windows):
        start = i * step_size
        train_end = start + train_size
        test_end = train_end + test_size
        
        if test_end > n_bars:
            break
        
        train_data = data.iloc[start:train_end]
        test_data = data.iloc[train_end:test_end]
        
        # Backtest avec params figés
        # ... (utiliser IchimokuATRStrategy)
        
        sharpe_oos = calculate_sharpe(test_returns)
        sharpes.append(sharpe_oos)
        
        window_details.append({
            'window': i,
            'train_start': data.index[start],
            'train_end': data.index[train_end],
            'test_start': data.index[train_end],
            'test_end': data.index[test_end],
            'sharpe_oos': sharpe_oos
        })
    
    sharpes = np.array(sharpes)
    consistency_ratio = np.mean(sharpes > 0)
    
    return {
        'consistency_ratio': consistency_ratio,
        'sharpes_oos': sharpes,
        'mean_sharpe': np.mean(sharpes),
        'std_sharpe': np.std(sharpes),
        'worst_window': int(np.argmin(sharpes)),
        'best_window': int(np.argmax(sharpes)),
        'n_windows': len(sharpes),
        'window_details': window_details,
        'verdict': _consistency_verdict(consistency_ratio)
    }


def _consistency_verdict(ratio: float) -> str:
    if ratio >= 0.80:
        return "PASS - Robust (>80% positive)"
    elif ratio >= 0.60:
        return "MARGINAL - Regime-dependent (60-80%)"
    else:
        return "FAIL - Fragile (<60% positive)"
```

### Critères d'Acceptance TASK 5

- [ ] Script génère 34 windows rolling
- [ ] Consistency Ratio calculé
- [ ] Identification worst/best windows avec dates
- [ ] Output CSV avec détails par window
- [ ] Test sur ETH

### Livrable

```
1500 DONE jordan-dev -> casey-quant: TASK 5 Multi-Period terminé
Fichiers:
  - scripts/run_multi_period_validation.py
  - outputs/multi_period_ETH_20260127.csv
Résultats ETH:
  - Consistency Ratio: XX%
  - Mean Sharpe OOS: X.XX
  - Worst Window: #X (dates)
  - Verdict: [PASS/MARGINAL/FAIL]
```

---

## 🟨 TASK 6: Worst-Case Path Analysis

### Méta-informations

| Champ | Valeur |
|-------|--------|
| **Owner** | Sam |
| **Effort** | 3h |
| **Priorité** | 🟡 P1 MEDIUM |
| **Dépend de** | TASK 1 |
| **Bloque** | Rien |
| **Fichier principal** | `crypto_backtest/validation/worst_case.py` |

### Objectif

Identifier le **worst-case backtest path** parmi les 15 combinaisons CPCV et calculer un Fragility Score.

### Spécification

```python
# Fichier: crypto_backtest/validation/worst_case.py

def analyze_worst_case(cpcv_results: List[Dict]) -> Dict:
    """
    Analyse worst-case parmi toutes les combinaisons CPCV.
    
    Citation López de Prado:
    "A parameter that performs brilliantly on average but has a 
    terrible worst-case performance is fragile and dangerous."
    
    Args:
        cpcv_results: Liste des résultats par combinaison CPCV
    
    Returns:
        Dict avec:
        - min_sharpe_oos: Pire Sharpe OOS
        - max_drawdown_oos: Pire drawdown OOS  
        - worst_path_id: Index de la pire combinaison
        - fragility_score: std(sharpes) / mean(sharpes)
        - is_fragile: fragility_score > 0.5
    """
    sharpes = [r['sharpe_oos'] for r in cpcv_results]
    drawdowns = [r['max_drawdown_oos'] for r in cpcv_results]
    
    fragility = np.std(sharpes) / (np.mean(sharpes) + 1e-6)
    
    return {
        'min_sharpe_oos': min(sharpes),
        'max_sharpe_oos': max(sharpes),
        'mean_sharpe_oos': np.mean(sharpes),
        'max_drawdown_oos': max(drawdowns),
        'worst_path_id': int(np.argmin(sharpes)),
        'best_path_id': int(np.argmax(sharpes)),
        'fragility_score': fragility,
        'is_fragile': fragility > 0.5,
        'verdict': 'PASS' if fragility <= 0.5 else 'FAIL - High fragility'
    }
```

### Critères d'Acceptance TASK 6

- [ ] `analyze_worst_case()` implémenté
- [ ] Fragility Score calculé (threshold 0.5)
- [ ] Rapport détaillé du worst path (dates, régimes)
- [ ] Intégration avec output CPCV

---

## 📅 TIMELINE & SÉQUENCEMENT

```
Jour 1 (27 Jan):
  ├─ TASK 1: CPCV Full (Alex, 6h) ─────────────────────┤ P0
  └─ TASK 3: Stress Test MARKDOWN (Jordan, 4h) ────────┤ P0 (parallèle)

Jour 2 (28 Jan):
  ├─ TASK 2: Regime-Stratified (Alex, 8h) ─────────────┤ P0 (après TASK 1)
  └─ TASK 5: Multi-Period (Jordan, 4h) ───────────────┤ P1

Jour 3 (29 Jan):
  ├─ TASK 6: Worst-Case (Sam, 3h) ────────────────────┤ P1
  └─ Intégration & Tests (All, 4h) ──────────────────┤

Jour 4-5 (30-31 Jan):
  └─ TASK 4: Synthetic Injection (Alex, 12h) ────────┤ P2
```

---

## 🏁 DEFINITION OF DONE GLOBALE

### P0 (BLOQUANT pour production)

- [ ] CPCV génère 15 combinaisons avec purging/embargo
- [ ] PBO < 0.30 sur les 14 assets PROD
- [ ] Stress test MARKDOWN exécuté (même si résultats mauvais)
- [ ] Regime-stratified garantit min 15% par régime

### P1 (Confiance renforcée)

- [ ] Consistency Ratio calculé (34 windows)
- [ ] Fragility Score < 0.5
- [ ] Worst-case path documenté

### P2 (Validation complète)

- [ ] Synthetic injection testé
- [ ] Comparaison original vs augmented

---

## 📣 FORMAT DE COMMUNICATION

### Début de task

```
HHMM INPROGRESS [agent] -> casey-quant: TASK [N] en cours
Fichier: [path]
Progress: [X/Y steps]
ETA: [HH:MM]
```

### Fin de task

```
HHMM DONE [agent] -> casey-quant: TASK [N] terminé
Fichiers: [liste]
Résultats: [métriques clés]
PR: #XX
Next: TASK [N+1] ou BLOCKED BY [reason]
```

### Blocage

```
HHMM BLOCKED [agent] -> casey-quant: TASK [N] bloqué
Raison: [description]
Besoin: [aide requise]
```

---

*Instructions générées le 26 janvier 2026. Référence: Issue #17.*
