# Investigation Bug Complex Number V4 - 2026-01-23 11:18

## Contexte

**Assets affectés:** STRK, METIS, AEVO, YGG  
**Asset SUCCESS:** SHIB  
**Erreur:** `float() argument must be a string or a real number, not 'complex'`  
**Localisation:** `[DEBUG] Monte Carlo failed for STRK: TypeError`

## Historique des Fixes

### Fix V1-V2 (avant 10:02)
- Protection timezone
- Protection bootstrap
- Protection metrics

### Fix V3 (10:02)
- Fonction `_safe_float()` créée
- Utilisée 24 fois dans le code
- **Résultat:** SHIB réussit, autres FAIL

### Fix V4 (11:10-11:18)
- Protections ajoutées:
  - ligne 167: `float(total_return)` → `_safe_float(total_return)`
  - ligne 322: `float(pnls.sum())` → `_safe_float(pnls.sum())`
  - ligne 324-325: `float(top_5/10_sum)` → `_safe_float(...)`
  - ligne 352: `float(result.equity_curve.iloc[-1])` → `_safe_float(...)`
  - ligne 383: `float(break_even)` → `_safe_float(...)`
  - ligne 405, 408, 418: `float(...)` dans regime → `_safe_float(...)`
  - ligne 546: `float(wfe_value)` → `_safe_float(...)`
  - ligne 155-162: Try/except autour de compute_metrics dans Monte Carlo
- **Résultat:** En cours de test (run toujours actif après 3+ minutes)

## Analyse

### Différences SHIB vs Autres

| Attribut | SHIB | STRK | METIS | AEVO | YGG |
|:---------|:-----|:-----|:------|:-----|:----|
| Bars | 17520 | 16825 | 16346 | 16300 | 17520 |
| Date start | 2024-01-22 | 2024-02-20 | 2024-03-11 | 2024-03-13 | 2024-01-23 |
| WFE | 2.42 | 0.85 | 0.85 | 0.62 | 0.78 |
| MC p-value (scan) | 0.0 | 0.218 | 0.0 | 0.072 | 0.008 |

### Hypothèse

Le problème pourrait venir de:
1. **Dates différentes** - STRK/METIS/AEVO commencent plus tard que SHIB
2. **Moins de données** - STRK, METIS, AEVO ont moins de bars
3. **Opération numpy spécifique** - Quelque chose dans compute_metrics ou _build_random_equity_curve qui génère un complexe pour certaines equity curves mais pas d'autres

## Stratégie Alternative

### Option 1: Protection Globale numpy
Forcer tous les résultats numpy à être réels:

```python
# Au début de _monte_carlo_permutation
import warnings
warnings.filterwarnings('ignore', category=np.ComplexWarning)

# Après chaque opération numpy critique
equity = np.real(equity)  # Force réel
```

### Option 2: Comparer SHIB vs STRK Trades
Analyser les différences dans les trades générés:
- Nombre de trades
- Durée moyenne
- P&L distribution
- Equity curve caractéristiques

### Option 3: Wrapper Global
Créer un wrapper autour de tous les calculs numpy/pandas pour forcer les types réels:

```python
def _force_real_array(arr):
    """Force array to be real-valued."""
    if np.iscomplexobj(arr):
        return np.real(arr)
    return arr
```

## Tests Prochains

1. Si fix V4 échoue encore → appliquer Option 1 (protection globale numpy)
2. Tester SHIB avec les mêmes params que STRK pour voir si c'est les params ou les données
3. Analyser les equity curves générées par Monte Carlo pour STRK vs SHIB

## Status

- **Run en cours:** STRK avec fix V4 (3+ minutes, anormalement long)
- **HBAR d26:** En cours (5+ minutes, normal pour optimization)
- **SHIB:** SUCCESS avec fix V3
- **Autres:** FAIL avec fix V3

## Prochaines Actions

1. Attendre résultats fix V4
2. Si FAIL → appliquer Option 1 (protection globale numpy)
3. Si SUCCESS → tester METIS, AEVO, YGG avec fix V4
4. Documenter le fix qui fonctionne
