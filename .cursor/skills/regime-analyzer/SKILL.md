---
name: regime-analyzer
description: Analyse les régimes de marché (BULL/BEAR/SIDEWAYS) et leur contribution au profit. Utiliser pour comprendre d'où vient la performance, vérifier guard007 (regime mismatch), ou avant de filtrer un régime. CRITIQUE - SIDEWAYS génère 79.5% du profit.
---

# Regime Analyzer

## Quand Utiliser
- Comprendre la distribution des profits par régime
- Vérifier guard007 (regime mismatch) avant validation
- Avant de décider de filtrer un régime (ATTENTION: SIDEWAYS = 79.5% profit)
- Débugger une stratégie qui performe mal dans un régime
- Alex demande une analyse de régime

## Prérequis
- Fichier trades avec timestamps dans `outputs/`
- Données OHLC pour calculer les régimes
- Python avec pandas, numpy

## Contexte Critique

⚠️ **ATTENTION CRITIQUE** ⚠️
```
SIDEWAYS génère 79.5% du profit total dans BTC baseline.
NE JAMAIS filtrer SIDEWAYS sans test empirique approfondi.
```

## Instructions

### Étape 1: Définir les Régimes
```python
import pandas as pd
import numpy as np

def compute_regime(close: pd.Series, lookback: int = 50) -> pd.Series:
    """
    BULL: close > high_50 * 0.95 (dans les 5% du plus haut)
    BEAR: close < low_50 * 1.05 (dans les 5% du plus bas)
    SIDEWAYS: entre les deux
    """
    high_50 = close.rolling(lookback).max()
    low_50 = close.rolling(lookback).min()
    
    from_high = (close / high_50) - 1
    from_low = (close / low_50) - 1
    
    regime = pd.Series('SIDEWAYS', index=close.index)
    regime[from_high > -0.05] = 'BULL'
    regime[from_low < 0.05] = 'BEAR'
    
    # CRITICAL: shift to avoid look-ahead!
    return regime.shift(1)
```

### Étape 2: Attribuer les Régimes aux Trades
```python
def assign_regime_to_trades(trades: pd.DataFrame, regime: pd.Series) -> pd.DataFrame:
    """
    IMPORTANT: Utiliser ENTRY time, PAS exit time!
    Utiliser exit time = look-ahead bias!
    """
    # S'assurer que entry_time est datetime
    trades['entry_time'] = pd.to_datetime(trades['entry_time'])
    
    # Mapper le régime sur entry_time
    trades['regime'] = trades['entry_time'].map(regime)
    
    return trades
```

### Étape 3: Analyser par Régime
```python
def analyze_by_regime(trades: pd.DataFrame) -> pd.DataFrame:
    """Calcule les métriques par régime."""
    
    def compute_sharpe(returns):
        if len(returns) < 2:
            return 0
        return returns.mean() / returns.std() * np.sqrt(252) if returns.std() > 0 else 0
    
    results = []
    total_pnl = trades['pnl'].sum()
    
    for regime in ['BULL', 'BEAR', 'SIDEWAYS']:
        regime_trades = trades[trades['regime'] == regime]
        
        if len(regime_trades) == 0:
            continue
            
        results.append({
            'regime': regime,
            'trades': len(regime_trades),
            'total_pnl': regime_trades['pnl'].sum(),
            'sharpe': compute_sharpe(regime_trades['pnl']),
            'win_rate': (regime_trades['pnl'] > 0).mean(),
            'avg_pnl': regime_trades['pnl'].mean(),
            'contribution_pct': regime_trades['pnl'].sum() / total_pnl * 100 if total_pnl != 0 else 0
        })
    
    return pd.DataFrame(results)
```

### Étape 4: Vérifier Guard007
```python
def check_guard007(regime_analysis: pd.DataFrame) -> dict:
    """
    Guard007: Maximum 1 régime avec Sharpe négatif
    """
    negative_regimes = regime_analysis[regime_analysis['sharpe'] < 0]
    n_negative = len(negative_regimes)
    
    return {
        'pass': n_negative <= 1,
        'negative_regimes': n_negative,
        'details': negative_regimes[['regime', 'sharpe']].to_dict('records') if n_negative > 0 else []
    }

# Utilisation
regime_stats = analyze_by_regime(trades)
guard007 = check_guard007(regime_stats)

print(f"Guard007: {'✅ PASS' if guard007['pass'] else '❌ FAIL'}")
print(f"Régimes à Sharpe négatif: {guard007['negative_regimes']}")
```

### Étape 5: Visualiser la Distribution
```python
# Afficher les résultats
regime_stats = analyze_by_regime(trades)
print(regime_stats.to_string(index=False))

# Format attendu:
# regime  trades  total_pnl  sharpe  win_rate  contribution_pct
# BULL       89       2.34    1.42      0.58             14.9
# BEAR       42       0.87    0.91      0.52              5.5
# SIDEWAYS  285      12.48    2.31      0.67             79.5
```

### Étape 6: Interpréter les Résultats

| Situation | Interprétation | Action |
|-----------|----------------|--------|
| SIDEWAYS > 60% profit | Normal, stratégie trend-following | Ne PAS filtrer |
| BEAR Sharpe < 0 | Attendu, stratégie long-only | Acceptable si 1 seul régime |
| 2+ régimes Sharpe < 0 | Guard007 FAIL | Investiguer, probablement BLOCKED |
| BULL Sharpe < 0 | Problème signal | Revoir indicateurs |

## Output Attendu

```csv
regime,trades,total_pnl,sharpe,win_rate,contribution_pct
BULL,89,2.34,1.42,0.58,14.9
BEAR,42,0.87,0.91,0.52,5.5
SIDEWAYS,285,12.48,2.31,0.67,79.5
```

## Anti-patterns INTERDITS

| Anti-pattern | Pourquoi c'est dangereux |
|--------------|--------------------------|
| `regime = get_regime_at(exit_time)` | Look-ahead bias |
| `signal = indicator` (sans .shift(1)) | Look-ahead bias |
| Filtrer SIDEWAYS sans test | Perte de 79.5% du profit potentiel |
| Ignorer BEAR Sharpe négatif | Normal pour long-only |

## Troubleshooting

| Problème | Solution |
|----------|----------|
| Guard007 FAIL (2+ régimes négatifs) | Probablement overfit, tester autre displacement |
| SIDEWAYS contribution < 50% | Vérifier calcul régime, lookback |
| Tous régimes positifs | Suspect, vérifier look-ahead |
| Trades sans régime assigné | Vérifier mapping entry_time |

## Escalade
- Si guard007 FAIL → Utiliser skill `displacement-rescue`
- Si doute sur filtrage régime → @Alex arbitrage
- Si contribution SIDEWAYS anormale → Investiguer avant décision
