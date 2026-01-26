# 📊 Guide d'Analyse des Régimes — FINAL TRIGGER v2

**Version**: 1.0  
**Date**: 26 janvier 2026  
**Auteur**: Analyse post-audit WFE  
**Statut**: 🟢 PRODUCTION REFERENCE

---

## 📋 Table des Matières

1. [Executive Summary](#executive-summary)
2. [Définitions des Régimes](#définitions-des-régimes)
3. [Matrice de Performance par Régime](#matrice-de-performance-par-régime)
4. [Analyse des 14 Assets PROD](#analyse-des-14-assets-prod)
5. [Period Effect & Biais Identifiés](#period-effect--biais-identifiés)
6. [Guidelines de Trading](#guidelines-de-trading)
7. [Recommandations Opérationnelles](#recommandations-opérationnelles)
8. [Monitoring & Alertes](#monitoring--alertes)

---

## Executive Summary

### Constats Clés (26 Jan 2026)

| Découverte | Impact | Action |
|------------|--------|--------|
| **ACCUMULATION domine à 82-86%** | OOS period = bull market | Attendre validation bear |
| **13/14 assets score négatif** | Edge conditionnel au régime | Position sizing adaptatif |
| **ETH seul score positif** | Asset de référence | Surpondérer ETH |
| **MARKDOWN = 6-14% seulement** | Aucune validation bear | Stress test CRITIQUE |
| **WFE > 1.0 sur 7 assets** | Period effect confirmé | Dégradation live 40-60% |

### Verdict Global

```
┌─────────────────────────────────────────────────────────────────┐
│  ⚠️  STRATÉGIE VALIDÉE MAIS REGIME-DÉPENDANTE                   │
│                                                                 │
│  • Edge CONFIRMÉ en ACCUMULATION/SIDEWAYS                       │
│  • Edge INCONNU en MARKDOWN/CAPITULATION                        │
│  • Déploiement PRUDENT recommandé jusqu'à validation bear       │
└─────────────────────────────────────────────────────────────────┘
```

---

## Définitions des Régimes

### Trend Regimes (6 états)

| Régime | Définition | Caractéristiques |
|--------|------------|------------------|
| **STRONG_BULL** | ADX > 25, +DI > -DI, price > EMA | Trend haussier fort, momentum positif |
| **WEAK_BULL** | ADX < 25, +DI > -DI | Hausse molle, consolidation haussière |
| **SIDEWAYS** | ADX < 20, range-bound | Range, mean-reversion favorable |
| **WEAK_BEAR** | ADX < 25, -DI > +DI | Baisse molle, consolidation baissière |
| **STRONG_BEAR** | ADX > 25, -DI > +DI, price < EMA | Trend baissier fort, capitulation |
| **REVERSAL** | Changement de direction détecté | Transition entre régimes |

### Volatility Regimes (4 états)

| Régime | Définition | Trading Implication |
|--------|------------|---------------------|
| **COMPRESSED** | ATR < ATR_MA * 0.8 | Breakout imminent, TP serré |
| **NORMAL** | 0.8 < ATR/ATR_MA < 1.2 | Conditions standard |
| **ELEVATED** | 1.2 < ATR/ATR_MA < 1.5 | SL élargi, taille réduite |
| **EXTREME** | ATR > ATR_MA * 1.5 | Risk-off ou taille mini |

### Crypto-Specific Regimes (Wyckoff - 6 états)

| Régime | Phase Wyckoff | Description | Action Recommandée |
|--------|---------------|-------------|-------------------|
| **ACCUMULATION** | Phase A-C | Smart money accumule, range | ✅ FAVORABLE — Entrer sur breakout |
| **MARKUP** | Phase D-E | Hausse avec volume | ✅ FAVORABLE — Suivre le trend |
| **DISTRIBUTION** | Phase A-C (top) | Smart money distribue | ⚠️ PRUDENCE — Réduire exposition |
| **MARKDOWN** | Phase D-E (bear) | Baisse avec volume | 🔴 DANGER — Stop & reverse ou flat |
| **CAPITULATION** | Selling climax | Panic selling, volume spike | 🔴 DANGER — Cash ou hedge |
| **RECOVERY** | Spring/Test | Rebond post-capitulation | ⚠️ PRUDENCE — Confirmation requise |

---

## Matrice de Performance par Régime

### Distribution Observée (17,520 barres, 2 ans)

#### Par Asset — Trend Regimes (%)

| Asset | SIDEWAYS | WEAK_BULL | WEAK_BEAR | STRONG_BULL | STRONG_BEAR | REVERSAL |
|-------|----------|-----------|-----------|-------------|-------------|----------|
| **ETH** | **38.96** | 20.19 | 17.83 | 10.70 | 11.11 | 1.22 |
| **AVAX** | **35.02** | 16.91 | 18.42 | 13.60 | 15.11 | 0.95 |
| **EGLD** | **34.76** | 18.52 | 18.41 | 12.12 | 15.35 | 0.84 |
| **DOT** | 29.07 | 20.82 | 21.98 | 12.67 | 14.06 | 1.41 |
| **TIA** | 27.74 | 17.48 | 20.71 | 13.84 | 18.47 | 1.76 |
| **NEAR** | 27.01 | 19.46 | 21.87 | 15.11 | 15.07 | 1.47 |
| **CAKE** | 27.01 | 21.18 | 22.09 | 13.01 | 14.06 | 2.63 |
| **RUNE** | 26.62 | 18.86 | 21.48 | 13.90 | 15.40 | 3.74 |
| **MINA** | 18.79 | 23.32 | 23.92 | 12.51 | 15.49 | 5.98 |
| **YGG** | 18.51 | 21.30 | 23.90 | 15.01 | 16.70 | 4.58 |
| **JOE** | 18.50 | 22.21 | 23.50 | 14.13 | 15.69 | 5.96 |
| **DOGE** | 17.67 | 23.30 | 23.62 | 13.22 | 13.74 | 8.45 |
| **ANKR** | 17.03 | 24.90 | 25.03 | 11.03 | 12.59 | 9.42 |
| **SHIB** | 16.91 | 24.17 | 26.07 | 10.59 | 12.09 | 10.16 |

**Observation**: ETH, AVAX, EGLD sont les plus "range-friendly" (>34% SIDEWAYS).

#### Par Asset — Crypto Regimes Wyckoff (%)

| Asset | ACCUMULATION | MARKDOWN | MARKUP | CAPITULATION | DISTRIBUTION | RECOVERY |
|-------|--------------|----------|--------|--------------|--------------|----------|
| **ETH** | **86.19** | 6.07 | 7.52 | 0.13 | 0.07 | 0.02 |
| **SHIB** | 85.45 | 9.06 | 5.13 | 0.17 | 0.09 | 0.11 |
| **ANKR** | 84.75 | 10.19 | 4.61 | 0.26 | 0.10 | 0.10 |
| **DOT** | 84.13 | 9.03 | 6.35 | 0.33 | 0.14 | 0.03 |
| **DOGE** | 83.81 | 9.12 | 6.52 | 0.37 | 0.10 | 0.09 |
| **EGLD** | 83.67 | 10.24 | 5.41 | 0.29 | 0.27 | 0.13 |
| **CAKE** | 83.50 | 9.36 | 6.34 | 0.43 | 0.19 | 0.18 |
| **AVAX** | 82.69 | 9.87 | 6.84 | 0.38 | 0.14 | 0.07 |
| **MINA** | 82.54 | 11.57 | 5.30 | 0.41 | 0.06 | 0.13 |
| **JOE** | 82.55 | 11.32 | 5.37 | 0.54 | 0.11 | 0.13 |
| **RUNE** | 81.71 | 10.58 | 6.60 | 0.73 | 0.23 | 0.15 |
| **NEAR** | 81.01 | 11.01 | 7.12 | 0.47 | 0.27 | 0.12 |
| **YGG** | 80.27 | 12.35 | 6.27 | 0.72 | 0.19 | 0.20 |
| **TIA** | 78.88 | 14.32 | 5.68 | 0.51 | 0.38 | 0.23 |

**Alerte Critique**: ACCUMULATION = 78-86% → **Biais massif vers conditions favorables**.

---

## Analyse des 14 Assets PROD

### Classement par Score Composite

| Rank | Asset | Score | WFE Tier | Sideways% | Favorable% | Verdict |
|:----:|-------|-------|----------|-----------|------------|---------|
| 🥇 | **ETH** | **+0.010** | Moderate | 38.96% | 52.0% | ✅ RÉFÉRENCE |
| 2 | DOGE | -0.008 | Normal | 17.67% | 48.3% | ✅ Solide |
| 3 | CAKE | -0.011 | Normal | 27.01% | 48.4% | ✅ Solide |
| 4 | NEAR | -0.013 | Normal | 27.01% | 47.4% | ✅ Solide |
| 5 | ANKR | -0.014 | Normal | 17.03% | 47.5% | ✅ Solide |
| 6 | AVAX | -0.014 | Normal | 35.02% | 47.2% | ✅ Solide |
| 7 | JOE | -0.016 | Normal | 18.50% | 46.9% | ✅ Acceptable |
| 8 | RUNE | -0.017 | Normal | 26.62% | 46.2% | ✅ Acceptable |
| 9 | DOT | -0.018 | **Extreme** | 29.07% | 46.3% | ⚠️ Period-sensitive |
| 10 | YGG | -0.018 | Normal | 18.51% | 46.6% | ✅ Acceptable |
| 11 | SHIB | -0.023 | **Extreme** | 16.91% | 45.5% | ⚠️ Period-sensitive |
| 12 | EGLD | -0.025 | Normal | 34.76% | 45.8% | ✅ Acceptable |
| 13 | MINA | -0.025 | Moderate | 18.79% | 45.7% | ⚠️ Légèrement fragile |
| 14 | TIA | **-0.041** | Moderate | 27.74% | 42.5% | 🔴 Plus fragile |

### Interprétation des Scores

```
Score Composite = f(trend_alignment, volatility_fit, wyckoff_phase, regime_stability)

> 0     : Conditions actuelles FAVORABLES à la stratégie
0 à -0.02: Conditions NEUTRES, edge marginal
< -0.02 : Conditions DÉFAVORABLES, dépendance au period effect
```

### Catégorisation Finale

#### Tier 1 — Assets Robustes (score > -0.015)
```
ETH, DOGE, CAKE, NEAR, ANKR, AVAX
```
- Edge démontré même en conditions neutres
- Position sizing: **100% de l'allocation cible**

#### Tier 2 — Assets Acceptables (-0.015 > score > -0.025)
```
JOE, RUNE, YGG, EGLD
```
- Edge conditionnel au régime
- Position sizing: **75% de l'allocation cible**

#### Tier 3 — Assets Fragiles (score < -0.025 OU WFE extreme)
```
DOT, SHIB, MINA, TIA
```
- Forte dépendance au period effect
- Position sizing: **50% de l'allocation cible**
- Monitoring renforcé

---

## Period Effect & Biais Identifiés

### Analyse Temporelle

```
┌─────────────────────────────────────────────────────────────────────┐
│                    TIMELINE DU DATASET (2 ans)                       │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Jan 2024              Avr 2025              Jan 2026               │
│     │                     │                     │                   │
│     ├─────── IS (63%) ────┼─────── OOS (37%) ───┤                   │
│     │                     │                     │                   │
│     │   Mixed/Bear        │   Bull/Accumulation │                   │
│     │   Score: négatif    │   Score: positif    │                   │
│     │                     │                     │                   │
└─────────────────────────────────────────────────────────────────────┘
```

### Biais Quantifiés

| Biais | Mesure | Impact |
|-------|--------|--------|
| **Accumulation Dominance** | 82.5% moyen | Stratégie long-only favorisée artificiellement |
| **Markdown Sous-représenté** | 6-14% seulement | **AUCUNE validation bear market** |
| **WFE > 1.0** | 7/14 assets | OOS plus favorable que IS |
| **Volatilité Compressée** | 52% moyen | Breakouts faciles, peu de whipsaws |

### Conséquences pour le Live

| Scénario | Probabilité | Impact Performance |
|----------|-------------|-------------------|
| Régime reste ACCUMULATION | 40% | ✅ Conforme au backtest |
| Shift vers MARKUP (bull fort) | 20% | ✅ Probablement meilleur |
| Shift vers SIDEWAYS | 20% | ⚠️ -10 à -20% vs backtest |
| Shift vers MARKDOWN | 15% | 🔴 **-40 à -60% vs backtest** |
| Shift vers CAPITULATION | 5% | 🔴 **Potentiellement négatif** |

---

## Guidelines de Trading

### Règle 1: Position Sizing par Régime

```python
def calculate_position_size(base_size, regime, asset_tier):
    """
    Ajuster la taille de position selon régime et tier de l'asset.
    """
    regime_multipliers = {
        'ACCUMULATION': 1.0,    # Conditions validées
        'MARKUP': 1.0,          # Trend favorable
        'SIDEWAYS': 0.8,        # Légèrement réduit
        'DISTRIBUTION': 0.5,    # Prudence
        'MARKDOWN': 0.25,       # Minimal
        'CAPITULATION': 0.0,    # FLAT
    }
    
    tier_multipliers = {
        'Tier1': 1.0,   # ETH, DOGE, CAKE, NEAR, ANKR, AVAX
        'Tier2': 0.75,  # JOE, RUNE, YGG, EGLD
        'Tier3': 0.50,  # DOT, SHIB, MINA, TIA
    }
    
    return base_size * regime_multipliers[regime] * tier_multipliers[asset_tier]
```

### Règle 2: Filtres d'Entrée par Régime

| Régime Détecté | Action | Justification |
|----------------|--------|---------------|
| ACCUMULATION | ✅ Trade normal | Validé backtest |
| MARKUP | ✅ Trade normal, trailing stop | Trend favorable |
| SIDEWAYS | ✅ Trade avec TP resserré | Range = TP plus proche |
| DISTRIBUTION | ⚠️ Entrées long DÉSACTIVÉES | Risque de breakdown |
| MARKDOWN | 🔴 FLAT ou short uniquement | Non validé |
| CAPITULATION | 🔴 FLAT obligatoire | Volatilité extrême |

### Règle 3: Stop Loss Dynamique par Volatilité

```python
def calculate_stop_loss(base_sl_atr, volatility_regime):
    """
    Ajuster SL selon régime de volatilité.
    """
    vol_adjustments = {
        'COMPRESSED': 0.8,   # SL serré, breakout imminent
        'NORMAL': 1.0,       # SL standard
        'ELEVATED': 1.3,     # SL élargi
        'EXTREME': 1.5,      # SL très large ou skip trade
    }
    return base_sl_atr * vol_adjustments[volatility_regime]
```

### Règle 4: Maximum Concurrent Exposure

| Régime Global Marché | Max Assets Simultanés | Max Exposure |
|---------------------|----------------------|--------------|
| ACCUMULATION dominant | 14 (tous) | 100% |
| Mixed | 10 | 75% |
| DISTRIBUTION détectée (>20% assets) | 5 | 50% |
| MARKDOWN détecté (>20% assets) | 2 | 25% |
| CAPITULATION (BTC) | 0 | 0% (CASH) |

---

## Recommandations Opérationnelles

### Court Terme (Immédiat)

| # | Action | Priorité | Owner |
|---|--------|----------|-------|
| 1 | **Stress test MARKDOWN isolé** | 🔴 CRITIQUE | Jordan |
| 2 | Implémenter position sizing par tier | 🔴 HIGH | Jordan |
| 3 | Ajouter régime actuel dans dashboard | 🟡 MEDIUM | Jordan |
| 4 | Créer alerte Telegram si MARKDOWN > 30% | 🟡 MEDIUM | Jordan |

### Moyen Terme (1-2 semaines)

| # | Action | Priorité | Owner |
|---|--------|----------|-------|
| 5 | CPCV avec 15 combinaisons (Issue #17) | 🔴 HIGH | Alex |
| 6 | Regime-stratified walk-forward | 🔴 HIGH | Alex |
| 7 | Synthetic bear injection test | 🟡 MEDIUM | Alex |
| 8 | Multi-period validation (34 windows) | 🟡 MEDIUM | Jordan |

### Long Terme (1 mois+)

| # | Action | Priorité | Owner |
|---|--------|----------|-------|
| 9 | Auto-adaptation sizing live par régime | 🟡 MEDIUM | TBD |
| 10 | Hedge automatique si MARKDOWN détecté | 🟢 LOW | TBD |
| 11 | Stratégie short pour MARKDOWN | 🟢 LOW | Alex |

---

## Monitoring & Alertes

### Dashboard Régime Temps Réel

```
┌─────────────────────────────────────────────────────────────────┐
│                    REGIME MONITOR — LIVE                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  BTC Regime:  [ACCUMULATION] ✅     Confidence: 87%             │
│  ETH Regime:  [SIDEWAYS] ✅         Confidence: 72%             │
│                                                                 │
│  Portfolio Regime Distribution:                                 │
│  ████████████████████░░░░ ACCUMULATION 68%                     │
│  ████░░░░░░░░░░░░░░░░░░░░ MARKDOWN 14%                         │
│  ███░░░░░░░░░░░░░░░░░░░░░ SIDEWAYS 12%                         │
│  ██░░░░░░░░░░░░░░░░░░░░░░ MARKUP 6%                            │
│                                                                 │
│  ⚠️  ALERT: MARKDOWN > 15% — Consider reducing exposure         │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Seuils d'Alerte

| Condition | Niveau | Action Automatique |
|-----------|--------|-------------------|
| MARKDOWN > 15% portfolio | ⚠️ WARNING | Notification Telegram |
| MARKDOWN > 25% portfolio | 🔴 CRITICAL | Réduire taille 50% |
| MARKDOWN > 40% portfolio | 🔴 EMERGENCY | FLAT all positions |
| BTC en CAPITULATION | 🔴 EMERGENCY | FLAT immédiat |
| Volatilité EXTREME > 30% assets | ⚠️ WARNING | Réduire taille 25% |

### Métriques de Suivi

```python
# Calculer quotidiennement
daily_metrics = {
    'regime_distribution': count_regimes(portfolio),
    'weighted_composite_score': calc_weighted_score(positions),
    'markdown_exposure': sum(pos for pos in positions if regime == 'MARKDOWN'),
    'regime_stability_mean': mean(stability_scores),
    'regime_shift_detected': detect_shift(last_24h),
}

# Alerter si
if daily_metrics['weighted_composite_score'] < -0.03:
    alert("Composite score dégradé — régime défavorable")
    
if daily_metrics['regime_shift_detected']:
    alert(f"Shift de régime détecté: {old_regime} → {new_regime}")
```

---

## Annexes

### A. Commandes Utiles

```bash
# Analyser régime actuel
python scripts/run_regime_analysis.py --assets ETH --current-only

# Stress test sur régime isolé
python scripts/run_regime_stress_test.py --asset ETH --regime MARKDOWN

# Rapport complet 14 assets
python scripts/run_regime_analysis.py --assets SHIB DOT TIA NEAR DOGE ANKR ETH JOE YGG MINA CAKE RUNE EGLD AVAX
```

### B. Fichiers de Référence

| Fichier | Description |
|---------|-------------|
| `outputs/regime_analysis/*.csv` | Régime barre par barre (4MB/asset) |
| `reports/regime_v3_prod_analysis_*.csv` | Résumé consolidé |
| `reports/regime_analysis_*_20260126.md` | Rapports individuels |
| `crypto_backtest/analysis/regime_v3.py` | Module d'analyse |

### C. Références Académiques

| Source | Concept |
|--------|---------|
| López de Prado (2018) | Regime-aware backtesting |
| Ang & Timmermann (2012) | Regime switching models |
| Mulvey & Liu (2016) | Regime-based portfolio allocation |
| Nystrup et al. (2017) | Regime detection via HMM |

---

## Changelog

| Date | Version | Changement |
|------|---------|------------|
| 2026-01-26 | 1.0 | Création initiale post-audit WFE |

---

*Document généré suite à l'analyse régime v3 du 26 janvier 2026. Objectif: fournir des guidelines opérationnelles pour gérer le period effect identifié.*
