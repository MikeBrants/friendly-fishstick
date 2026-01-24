---
name: regime-analyzer
description: Analyse les régimes de marché (BULL/BEAR/SIDEWAYS) et leur impact sur les performances de trading pour éviter le filtering de SIDEWAYS.
---

# Regime Analyzer

## Quand Utiliser
- Utiliser cette skill pour analyser la performance par régime de marché
- Cette skill est utile pour comprendre d'où vient le profit
- Utiliser pour vérifier guard007 (regime mismatch)
- Utiliser pour éviter de filtrer SIDEWAYS (79.5% du profit)

## Définition des Régimes

```python
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
    
    return regime.shift(1)  # CRITICAL: shift to avoid look-ahead
```

## Attribution aux Trades

```python
def assign_regime_to_trades(trades: pd.DataFrame, regime: pd.Series) -> pd.DataFrame:
    """
    IMPORTANT: Utiliser ENTRY time, pas exit time!
    """
    trades['regime'] = trades['entry_time'].map(regime)
    return trades
```

## Analyse par Régime

```python
def analyze_by_regime(trades: pd.DataFrame) -> pd.DataFrame:
    results = []
    for regime in ['BULL', 'BEAR', 'SIDEWAYS']:
        regime_trades = trades[trades['regime'] == regime]
        results.append({
            'regime': regime,
            'trades': len(regime_trades),
            'total_pnl': regime_trades['pnl'].sum(),
            'sharpe': compute_sharpe(regime_trades['pnl']),
            'win_rate': (regime_trades['pnl'] > 0).mean(),
            'contribution_pct': regime_trades['pnl'].sum() / trades['pnl'].sum() * 100
        })
    return pd.DataFrame(results)
```

## ATTENTION CRITIQUE

```
SIDEWAYS génère 79.5% du profit total dans BTC baseline.
NE JAMAIS filtrer SIDEWAYS sans test empirique.
```

## Output Format

```csv
regime,trades,total_pnl,sharpe,win_rate,contribution_pct
BULL,89,2.34,1.42,0.58,14.9
BEAR,42,0.87,0.91,0.52,5.5
SIDEWAYS,285,12.48,2.31,0.67,79.5
```

## Guard007: Regime Mismatch

```python
def check_regime_mismatch(regime_analysis: pd.DataFrame) -> bool:
    negative_regimes = (regime_analysis['sharpe'] < 0).sum()
    return negative_regimes <= 1  # PASS si max 1 régime négatif
```

## Règles importantes
1. **Toujours utiliser `.shift(1)`** pour éviter look-ahead sur le régime
2. **Utiliser ENTRY time** pour attribution, PAS exit time
3. **Ne pas filtrer SIDEWAYS** sans validation empirique
