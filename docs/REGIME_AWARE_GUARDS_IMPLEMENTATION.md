# 📋 INSTRUCTIONS AGENT: Implémentation Regime-Aware Guards (Mode Indicatif)

**Date**: 26 janvier 2026  
**Assigné à**: Alex (Lead Quant)  
**Contexte**: Suite audit WFE — 7 assets avec WFE > 1.0 nécessitent validation régime  
**Priorité**: 🟡 MOYENNE (amélioration analyse, non-bloquant)  
**Branche**: `feature/regime-aware-guards-indicative`

---

## ⚠️ MODE INDICATIF

**IMPORTANT**: Les guards 008 et 009 sont en **mode indicatif uniquement**.

- Ils **NE BLOQUENT PAS** la validation 7/7
- Ils apparaissent dans les rapports avec un flag ⚠️
- Ils servent à **informer** et **ajuster les attentes** (sizing, Sharpe attendu)
- Après 2-3 cycles de validation, on décidera s'ils deviennent éliminatoires

---

## 🎯 OBJECTIFS

1. **Détecter les régimes** (BULL/BEAR/SIDEWAYS) automatiquement
2. **Calculer le régime dominant** par window IS et OOS
3. **Appliquer des haircuts informatifs** aux métriques quand OOS est favorable
4. **Ajouter 2 guards indicatifs** (guard008: wfe_suspicious, guard009: regime_bias)
5. **Intégrer au pipeline existant** sans casser les runs en cours

---

## 📦 GUARD 008: WFE Suspicious

### Question posée
"Est-ce que le ratio OOS/IS est anormalement élevé ou bas ?"

### Formule
```
WFE = Performance OOS ÷ Performance IS
```

### Seuils
| WFE | Interprétation | Verdict |
|-----|----------------|--------|
| < 0.4 | OOS très inférieur à IS → **overfitting probable** | ⚠️ FLAG |
| 0.4 - 2.0 | Range normal | ✅ OK |
| > 2.0 | OOS surperforme IS → **suspect** | ⚠️ FLAG |

### Exemples actuels (project-state.md)
- SHIB: WFE = 2.27 → ⚠️ FLAG "suspect"
- ETH: WFE = 1.22 → ✅ OK
- OSMO: WFE = 0.19 → ⚠️ FLAG "overfit"

### Implémentation
```python
def guard_wfe_suspicious(
    wfe: float,
    threshold_high: float = 2.0,
    threshold_low: float = 0.4
) -> dict:
    """
    Guard 008: Détecte les WFE anormaux (INDICATIF UNIQUEMENT).
    
    Returns:
        Dict avec 'flagged', 'value', 'message', 'blocks_validation': False
    """
    flagged = wfe < threshold_low or wfe > threshold_high
    
    if wfe > threshold_high:
        verdict = 'SUSPECT_HIGH'
        message = f'WFE {wfe:.2f} > {threshold_high} — OOS surperforme anormalement'
    elif wfe < threshold_low:
        verdict = 'SUSPECT_LOW'
        message = f'WFE {wfe:.2f} < {threshold_low} — Probable overfitting'
    else:
        verdict = 'OK'
        message = f'WFE {wfe:.2f} dans range acceptable [{threshold_low}, {threshold_high}]'
    
    return {
        'guard_id': 'guard008',
        'name': 'wfe_suspicious',
        'flagged': flagged,
        'value': wfe,
        'verdict': verdict,
        'message': message,
        'blocks_validation': False  # MODE INDICATIF
    }
```

---

## 📦 GUARD 009: Regime Bias

### Question posée
"Est-ce que la bonne performance OOS vient juste d'un marché favorable ?"

### Logique en 3 étapes

1. **Identifier le régime de chaque période**:
   - IS (entraînement): BULL, BEAR, ou SIDEWAYS ?
   - OOS (test): BULL, BEAR, ou SIDEWAYS ?

2. **Détecter le mismatch favorable**:
   - Si IS = BEAR/SIDEWAYS et OOS = BULL → ⚠️ FLAG
   - La stratégie optimisée en contexte difficile, testée en contexte facile

3. **Calculer le Sharpe ajusté (informatif)**:
   | Régime OOS | Haircut | Sharpe ajusté |
   |------------|---------|---------------|
   | BULL | ×0.65 | Sharpe brut × 0.65 |
   | SIDEWAYS | ×1.0 | Pas de changement |
   | BEAR | ×1.25 | Bonus (contexte difficile) |

### Classification des régimes
```python
class MarketRegime(Enum):
    BULL = "BULL"         # Return annualisé > +20%
    BEAR = "BEAR"         # Return annualisé < -20%
    SIDEWAYS = "SIDEWAYS" # Entre -20% et +20%
    UNKNOWN = "UNKNOWN"
```

### Implémentation
```python
def guard_regime_bias(
    is_regime: str,
    oos_regime: str,
    wfe: float,
    oos_sharpe: float,
    wfe_threshold: float = 1.5,
    min_adjusted_sharpe: float = 1.5
) -> dict:
    """
    Guard 009: Détecte le biais de régime favorable (INDICATIF UNIQUEMENT).
    
    Returns:
        Dict avec régimes, Sharpe ajusté, flag, 'blocks_validation': False
    """
    # Identifier mismatch favorable
    favorable_mismatch = (
        is_regime in ['BEAR', 'SIDEWAYS'] and
        oos_regime == 'BULL'
    )
    
    # Calculer haircut
    haircuts = {'BULL': 0.65, 'SIDEWAYS': 1.0, 'BEAR': 1.25, 'UNKNOWN': 1.0}
    haircut = haircuts.get(oos_regime, 1.0)
    adjusted_sharpe = oos_sharpe * haircut
    
    # Flag si mismatch favorable ET WFE élevé
    flagged = favorable_mismatch and wfe > wfe_threshold
    
    if flagged:
        message = (f"Favorable regime mismatch (IS={is_regime}, OOS={oos_regime}) "
                   f"with high WFE {wfe:.2f}. Adjusted Sharpe: {adjusted_sharpe:.2f}")
    else:
        message = f"No concerning regime bias (IS={is_regime}, OOS={oos_regime})"
    
    return {
        'guard_id': 'guard009',
        'name': 'regime_bias',
        'flagged': flagged,
        'is_regime': is_regime,
        'oos_regime': oos_regime,
        'wfe': wfe,
        'raw_sharpe': oos_sharpe,
        'adjusted_sharpe': adjusted_sharpe,
        'haircut_applied': haircut,
        'message': message,
        'blocks_validation': False  # MODE INDICATIF
    }
```

---

## 📁 STRUCTURE DES FICHIERS À CRÉER

```
crypto_backtest/
├── analysis/
│   └── regime_detector.py          # NOUVEAU - Détection régimes
├── validation/
│   └── indicative_guards.py        # NOUVEAU - Guards 008/009 indicatifs
scripts/
└── regime_analysis_v2.py           # NOUVEAU - Script analyse régimes
tests/
└── test_regime_detector.py         # NOUVEAU - Tests unitaires
```

---

## 📦 CODE COMPLET: regime_detector.py

```python
"""
Regime detection for crypto markets.

Régimes définis:
- BULL: Return annualisé > +20%
- BEAR: Return annualisé < -20%
- SIDEWAYS: Entre -20% et +20%

Méthode: Rolling return sur fenêtre glissante + classification.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional

import numpy as np
import pandas as pd


class MarketRegime(Enum):
    """Market regime classification."""
    BULL = "BULL"
    BEAR = "BEAR"
    SIDEWAYS = "SIDEWAYS"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class RegimeConfig:
    """Configuration for regime detection."""
    bull_threshold: float = 0.20      # > +20% annualisé = BULL
    bear_threshold: float = -0.20     # < -20% annualisé = BEAR
    lookback_days: int = 30           # Rolling window pour return
    min_periods: int = 7              # Minimum de jours pour calculer
    trading_days_per_year: int = 365  # Crypto = 365 (24/7)


@dataclass
class RegimeResult:
    """Result of regime detection for a period."""
    regime: MarketRegime
    confidence: float
    annualized_return: float
    volatility: float
    start_date: pd.Timestamp
    end_date: pd.Timestamp
    
    def to_dict(self) -> dict:
        return {
            'regime': self.regime.value,
            'confidence': round(self.confidence, 3),
            'annualized_return': round(self.annualized_return, 4),
            'volatility': round(self.volatility, 4),
            'start_date': str(self.start_date),
            'end_date': str(self.end_date)
        }


class RegimeDetector:
    """
    Détecte le régime de marché basé sur les returns.
    
    Usage:
        detector = RegimeDetector()
        regime = detector.detect_regime(price_data)
        regimes_series = detector.detect_regimes_rolling(price_data)
    """
    
    def __init__(self, config: Optional[RegimeConfig] = None):
        self.config = config or RegimeConfig()
    
    def detect_regime(self, data: pd.DataFrame, 
                      price_col: str = 'close') -> RegimeResult:
        """
        Détecte le régime dominant pour une période complète.
        """
        if data.empty or len(data) < self.config.min_periods:
            return RegimeResult(
                regime=MarketRegime.UNKNOWN,
                confidence=0.0,
                annualized_return=0.0,
                volatility=0.0,
                start_date=data.index.min() if not data.empty else pd.NaT,
                end_date=data.index.max() if not data.empty else pd.NaT
            )
        
        prices = data[price_col]
        total_return = (prices.iloc[-1] / prices.iloc[0]) - 1
        
        days = (data.index[-1] - data.index[0]).days
        if days <= 0:
            days = 1
        annualized_return = (1 + total_return) ** (self.config.trading_days_per_year / days) - 1
        
        daily_returns = prices.pct_change().dropna()
        volatility = daily_returns.std() * np.sqrt(self.config.trading_days_per_year)
        
        regime, confidence = self._classify_regime(annualized_return)
        
        return RegimeResult(
            regime=regime,
            confidence=confidence,
            annualized_return=annualized_return,
            volatility=volatility,
            start_date=data.index.min(),
            end_date=data.index.max()
        )
    
    def detect_regimes_rolling(self, data: pd.DataFrame,
                                price_col: str = 'close') -> pd.Series:
        """
        Détecte les régimes sur une fenêtre glissante.
        """
        prices = data[price_col]
        lookback = self.config.lookback_days
        
        rolling_return = prices.pct_change(periods=lookback).fillna(0)
        annualized = (1 + rolling_return) ** (self.config.trading_days_per_year / lookback) - 1
        
        regimes = pd.Series(index=data.index, dtype=object)
        regimes[annualized > self.config.bull_threshold] = MarketRegime.BULL
        regimes[annualized < self.config.bear_threshold] = MarketRegime.BEAR
        regimes[(annualized >= self.config.bear_threshold) & 
                (annualized <= self.config.bull_threshold)] = MarketRegime.SIDEWAYS
        regimes = regimes.fillna(MarketRegime.UNKNOWN)
        
        return regimes
    
    def get_regime_distribution(self, data: pd.DataFrame,
                                 price_col: str = 'close') -> dict[str, float]:
        """
        Calcule la distribution des régimes sur une période.
        """
        regimes = self.detect_regimes_rolling(data, price_col)
        
        total = len(regimes)
        if total == 0:
            return {'BULL': 0.0, 'BEAR': 0.0, 'SIDEWAYS': 0.0, 'UNKNOWN': 1.0}
        
        distribution = {}
        for regime in MarketRegime:
            count = (regimes == regime).sum()
            distribution[regime.value] = round(count / total, 4)
        
        return distribution
    
    def _classify_regime(self, annualized_return: float) -> tuple[MarketRegime, float]:
        """Classifie et calcule la confiance."""
        bull_t = self.config.bull_threshold
        bear_t = self.config.bear_threshold
        
        if annualized_return > bull_t:
            confidence = min(1.0, (annualized_return - bull_t) / bull_t)
            return MarketRegime.BULL, confidence
        elif annualized_return < bear_t:
            confidence = min(1.0, (bear_t - annualized_return) / abs(bear_t))
            return MarketRegime.BEAR, confidence
        else:
            distance_to_edge = min(abs(annualized_return - bull_t), 
                                   abs(annualized_return - bear_t))
            confidence = distance_to_edge / bull_t
            return MarketRegime.SIDEWAYS, confidence


def detect_regime_for_period(data: pd.DataFrame, 
                              start: pd.Timestamp, 
                              end: pd.Timestamp,
                              price_col: str = 'close') -> RegimeResult:
    """Helper pour détecter le régime d'une période spécifique."""
    period_data = data[(data.index >= start) & (data.index < end)]
    detector = RegimeDetector()
    return detector.detect_regime(period_data, price_col)
```

---

## 📦 CODE COMPLET: indicative_guards.py

```python
"""
Indicative guards for regime-aware validation.

These guards are INFORMATIONAL ONLY and do NOT block validation.
They appear in reports with a flag but don't affect the 7/7 PASS status.

Guards:
- guard008: WFE Suspicious (detects abnormal WFE values)
- guard009: Regime Bias (detects favorable regime mismatch)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class IndicativeGuardResult:
    """Result from an indicative guard."""
    guard_id: str
    name: str
    flagged: bool
    value: float
    message: str
    details: dict
    blocks_validation: bool = False  # ALWAYS False for indicative guards
    
    def to_dict(self) -> dict:
        return {
            'guard_id': self.guard_id,
            'name': self.name,
            'flagged': self.flagged,
            'value': self.value,
            'message': self.message,
            'details': self.details,
            'blocks_validation': self.blocks_validation
        }


def guard_wfe_suspicious(
    wfe: float,
    threshold_high: float = 2.0,
    threshold_low: float = 0.4
) -> IndicativeGuardResult:
    """
    Guard 008: Détecte les WFE anormaux (INDICATIF UNIQUEMENT).
    
    Args:
        wfe: Walk-Forward Efficiency
        threshold_high: Seuil au-dessus duquel suspect (default 2.0)
        threshold_low: Seuil en-dessous duquel overfit (default 0.4)
        
    Returns:
        IndicativeGuardResult (blocks_validation=False)
    """
    flagged = wfe < threshold_low or wfe > threshold_high
    
    if wfe > threshold_high:
        verdict = 'SUSPECT_HIGH'
        message = f'⚠️ WFE {wfe:.2f} > {threshold_high} — OOS surperforme anormalement (investiguer régime)'
    elif wfe < threshold_low:
        verdict = 'SUSPECT_LOW'
        message = f'⚠️ WFE {wfe:.2f} < {threshold_low} — Probable overfitting'
    else:
        verdict = 'OK'
        message = f'✅ WFE {wfe:.2f} dans range acceptable [{threshold_low}, {threshold_high}]'
    
    return IndicativeGuardResult(
        guard_id='guard008',
        name='wfe_suspicious',
        flagged=flagged,
        value=wfe,
        message=message,
        details={
            'verdict': verdict,
            'threshold_high': threshold_high,
            'threshold_low': threshold_low
        },
        blocks_validation=False
    )


def guard_regime_bias(
    is_regime: str,
    oos_regime: str,
    wfe: float,
    oos_sharpe: float,
    wfe_threshold: float = 1.5,
    min_adjusted_sharpe: float = 1.5
) -> IndicativeGuardResult:
    """
    Guard 009: Détecte le biais de régime favorable (INDICATIF UNIQUEMENT).
    
    Args:
        is_regime: Régime dominant période IS (BULL/BEAR/SIDEWAYS)
        oos_regime: Régime dominant période OOS
        wfe: Walk-Forward Efficiency
        oos_sharpe: Sharpe ratio OOS brut
        wfe_threshold: Seuil WFE pour flag si mismatch (default 1.5)
        min_adjusted_sharpe: Sharpe minimum après haircut (default 1.5)
        
    Returns:
        IndicativeGuardResult avec Sharpe ajusté (blocks_validation=False)
    """
    # Haircuts par régime OOS
    haircuts = {
        'BULL': 0.65,      # Performance gonflée par momentum
        'SIDEWAYS': 1.0,   # Régime neutre
        'BEAR': 1.25,      # Performance sous-estimée (contexte difficile)
        'UNKNOWN': 1.0
    }
    
    haircut = haircuts.get(oos_regime, 1.0)
    adjusted_sharpe = oos_sharpe * haircut
    
    # Identifier mismatch favorable
    favorable_mismatch = (
        is_regime in ['BEAR', 'SIDEWAYS'] and
        oos_regime == 'BULL'
    )
    
    # Flag si mismatch favorable ET WFE élevé
    flagged = favorable_mismatch and wfe > wfe_threshold
    
    if flagged:
        message = (f"⚠️ Favorable regime mismatch (IS={is_regime} → OOS={oos_regime}) "
                   f"avec WFE élevé {wfe:.2f}. Sharpe ajusté: {adjusted_sharpe:.2f} "
                   f"(haircut {haircut:.0%})")
    elif favorable_mismatch:
        message = (f"ℹ️ Regime mismatch détecté (IS={is_regime} → OOS={oos_regime}) "
                   f"mais WFE {wfe:.2f} acceptable. Sharpe ajusté: {adjusted_sharpe:.2f}")
    else:
        message = f"✅ Pas de biais régime concernant (IS={is_regime}, OOS={oos_regime})"
    
    return IndicativeGuardResult(
        guard_id='guard009',
        name='regime_bias',
        flagged=flagged,
        value=adjusted_sharpe,
        message=message,
        details={
            'is_regime': is_regime,
            'oos_regime': oos_regime,
            'wfe': wfe,
            'raw_sharpe': oos_sharpe,
            'adjusted_sharpe': adjusted_sharpe,
            'haircut_applied': haircut,
            'favorable_mismatch': favorable_mismatch
        },
        blocks_validation=False
    )


def run_indicative_guards(
    wfe: float,
    oos_sharpe: float,
    is_regime: str = 'UNKNOWN',
    oos_regime: str = 'UNKNOWN'
) -> dict:
    """
    Exécute tous les guards indicatifs.
    
    Args:
        wfe: Walk-Forward Efficiency
        oos_sharpe: Sharpe ratio OOS
        is_regime: Régime dominant IS
        oos_regime: Régime dominant OOS
        
    Returns:
        Dict avec résultats des 2 guards + summary
    """
    guard008 = guard_wfe_suspicious(wfe)
    guard009 = guard_regime_bias(is_regime, oos_regime, wfe, oos_sharpe)
    
    any_flagged = guard008.flagged or guard009.flagged
    
    return {
        'guard008_wfe_suspicious': guard008.to_dict(),
        'guard009_regime_bias': guard009.to_dict(),
        'any_flagged': any_flagged,
        'adjusted_sharpe': guard009.details['adjusted_sharpe'],
        'blocks_validation': False,  # TOUJOURS False
        'summary': (
            f"{'⚠️ FLAGS DETECTED' if any_flagged else '✅ No flags'}. "
            f"Adjusted Sharpe: {guard009.details['adjusted_sharpe']:.2f}"
        )
    }
```

---

## 📅 PLAN DE MISE EN WORKFLOW

### Chronologie

| Jour | Phase | Actions | Livrables |
|------|-------|---------|----------|
| **1-2** | Setup | Créer `regime_detector.py`, tests | Code + tests |
| **3** | Guards | Créer `indicative_guards.py` | Guards 008/009 |
| **4** | Intégration | Modifier `run_guards_multiasset.py` | Pipeline à jour |
| **5** | Validation | Tester sur 7 assets WFE > 1.0 | Rapport régime |

### Commande de Test

```bash
# Analyser les 7 assets suspects
python scripts/regime_analysis_v2.py \
    --assets SHIB DOT NEAR DOGE TIA MINA ETH \
    --per-window \
    --output reports/regime-analysis-indicative.md
```

### Intégration dans run_guards_multiasset.py

```python
# À ajouter dans la fonction run_guards()
from crypto_backtest.validation.indicative_guards import run_indicative_guards

# Après les 7 guards existants
indicative_results = run_indicative_guards(
    wfe=wfe,
    oos_sharpe=metrics['sharpe_ratio'],
    is_regime=is_regime,  # À calculer avec RegimeDetector
    oos_regime=oos_regime
)

# Ajouter au rapport (ne change PAS all_pass)
results['indicative_guards'] = indicative_results
```

---

## ✅ CHECKLIST

### À Implémenter

- [ ] `crypto_backtest/analysis/regime_detector.py`
- [ ] `crypto_backtest/validation/indicative_guards.py`
- [ ] `tests/test_regime_detector.py`
- [ ] `tests/test_indicative_guards.py`
- [ ] Modifier `scripts/run_guards_multiasset.py`
- [ ] `scripts/regime_analysis_v2.py`

### Validation

- [ ] Tests unitaires passent
- [ ] Guards indicatifs apparaissent dans rapport
- [ ] `blocks_validation=False` vérifié
- [ ] Sharpe ajusté calculé correctement
- [ ] Pas d'impact sur validation 7/7 existante

---

## 📎 RÉFÉRENCES

### Seuils Guards Existants (project-state.md)

| Guard | ID | Seuil | Bloquant |
|-------|:---|-------|----------|
| MC p-value | guard001 | < 0.05 | OUI |
| Sensitivity variance | guard002 | < 15% | OUI |
| Bootstrap CI lower | guard003 | > 1.0 | OUI |
| Top10 trades % | guard005 | < 40% | OUI |
| Stress1 Sharpe | guard006 | > 1.0 | OUI |
| Regime mismatch | guard007 | < 1% | OUI |
| WFE | - | > 0.6 | OUI |
| **WFE suspicious** | guard008 | 0.4 < WFE < 2.0 | **NON** |
| **Regime bias** | guard009 | (informatif) | **NON** |

### Assets avec WFE > 1.0 (à analyser en priorité)

| Asset | WFE | Sharpe | Action |
|-------|-----|--------|--------|
| SHIB | 2.27 | 5.67 | Analyser régime OOS |
| DOT | 1.74 | 4.82 | Analyser régime OOS |
| NEAR | 1.69 | 4.26 | Analyser régime OOS |
| DOGE | 1.55 | 3.88 | Analyser régime OOS |
| TIA | 1.36 | 5.16 | Analyser régime OOS |
| ETH | 1.22 | 3.22 | Analyser régime OOS |
| MINA | 1.13 | 2.58 | Analyser régime OOS |

---

**FIN DES INSTRUCTIONS**

*Assigné à: Alex (Lead Quant)*  
*Date: 26 janvier 2026*  
*Mode: INDICATIF (non-bloquant)*
