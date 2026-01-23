# Investigation Bug Complex Number - 2026-01-23

## Problème

**Erreur:** `float() argument must be a string or a real number, not 'complex'`

**Assets affectés:** SHIB, STRK, METIS, AEVO, YGG (5 assets)

**Impact:** Guards bloqués malgré scans excellents (ex: SHIB Sharpe 5.88, WFE 2.42)

---

## Analyse du Code

### 1. Fix Timezone Appliqué (Insuffisant)

**Fichier:** `scripts/run_guards_multiasset.py` (lignes 450-453)
```python
if data.index.tz is None:
    data.index = data.index.tz_localize("UTC")
else:
    data.index = data.index.tz_convert("UTC")
```

**Problème:** Le fix timezone ne résout pas le problème. L'erreur se produit probablement dans les calculs numériques, pas dans le timezone.

---

### 2. Sources Potentielles du Bug

#### A. Bootstrap Confidence (Ligne 238-239)
```python
std_returns = returns.std(axis=1, ddof=0)
sharpe = np.where(std_returns == 0, 0.0, mean_returns / std_returns * np.sqrt(n))
```

**Problème potentiel:**
- Si `std_returns` contient des valeurs négatives (erreur numérique), `np.sqrt(n)` avec `n` négatif pourrait produire un complexe
- Mais `n` est la longueur du tableau, donc toujours positif
- Le vrai problème est probablement dans `std_returns` lui-même

#### B. Periods Per Year (metrics.py ligne 85)
```python
return pd.Timedelta(days=365.25) / delta
```

**Problème potentiel:**
- Si `delta` est négatif ou très petit, la division pourrait produire des valeurs infinies ou NaN
- Mais cela ne devrait pas produire de nombres complexes directement

#### C. Sharpe Ratio Calculation (metrics.py ligne 23)
```python
sharpe = _ratio(returns.mean(), returns.std(ddof=0)) * (periods_per_year**0.5)
```

**Problème potentiel:**
- Si `periods_per_year` est négatif (ce qui ne devrait pas arriver), `**0.5` pourrait produire un complexe
- Mais `_periods_per_year` retourne toujours un float positif

---

## Hypothèse Principale

Le problème vient probablement de **valeurs NaN ou infinies** qui se propagent dans les calculs et deviennent complexes lors d'opérations comme `np.sqrt()` ou divisions.

**Scénario probable:**
1. Certains assets ont des données avec des gaps ou des valeurs aberrantes
2. Les calculs de variance/std produisent des NaN
3. Les NaN se propagent dans les calculs de Sharpe
4. Lors de la conversion en float, pandas/numpy détecte un complexe

---

## Solution Proposée

### Fix 1: Protection dans Bootstrap Confidence

```python
def _bootstrap_confidence(...):
    # ... existing code ...
    std_returns = returns.std(axis=1, ddof=0)
    
    # FIX: S'assurer que std_returns est toujours positif et réel
    std_returns = np.abs(std_returns)  # Force positif
    std_returns = np.where(np.isnan(std_returns), 0.0, std_returns)  # Remplace NaN
    std_returns = np.where(np.isinf(std_returns), 0.0, std_returns)  # Remplace inf
    
    sharpe = np.where(std_returns == 0, 0.0, mean_returns / std_returns * np.sqrt(n))
    
    # FIX: S'assurer que sharpe est réel
    sharpe = np.real(sharpe)  # Extrait partie réelle si complexe
    sharpe = np.where(np.isnan(sharpe), 0.0, sharpe)
    sharpe = np.where(np.isinf(sharpe), 0.0, sharpe)
```

### Fix 2: Protection dans Metrics Calculation

```python
def compute_metrics(...):
    # ... existing code ...
    sharpe = _ratio(returns.mean(), returns.std(ddof=0)) * (periods_per_year**0.5)
    
    # FIX: S'assurer que sharpe est réel
    sharpe = float(np.real(sharpe)) if isinstance(sharpe, complex) else float(sharpe)
    if np.isnan(sharpe) or np.isinf(sharpe):
        sharpe = 0.0
```

### Fix 3: Protection dans Periods Per Year

```python
def _periods_per_year(index: pd.Index) -> float:
    # ... existing code ...
    delta = (index[1:] - index[:-1]).median()
    if delta <= pd.Timedelta(0):
        return 252.0
    
    result = pd.Timedelta(days=365.25) / delta
    # FIX: S'assurer que le résultat est positif et fini
    if pd.isna(result) or result <= 0:
        return 252.0
    return float(result)
```

---

## Plan d'Action

1. **Appliquer les fixes** dans les 3 fonctions identifiées
2. **Tester** sur un asset problématique (SHIB)
3. **Valider** que les guards passent
4. **Relancer** tous les assets bloqués (SHIB, STRK, METIS, AEVO, YGG)

---

## Fichiers à Modifier

1. `scripts/run_guards_multiasset.py` — Fix bootstrap confidence
2. `crypto_backtest/analysis/metrics.py` — Fix compute_metrics et _periods_per_year

---

**Date:** 2026-01-23  
**Auteur:** @Jordan  
**Priorité:** P0 (bloque 5 assets PROD potentiels)
