# External References — Backtesting & Quant Documentation

**Date:** 24 janvier 2026  
**Purpose:** Documentation officielle des frameworks de backtesting et analyse quantitative

---

## 📚 QuantConnect

**Description:** Platform de backtesting et live trading avec API complète

### Documentation
- [QuantConnect Docs v2](https://www.quantconnect.com/docs/v2)
- [Cloud Platform Backtesting](https://www.quantconnect.com/docs/v2/cloud-platform/backtesting)
- [LEAN CLI Backtesting Deployment](https://www.quantconnect.com/docs/v2/lean-cli/backtesting/deployment)
- [LEAN CLI API Reference](https://www.quantconnect.com/docs/v2/lean-cli/api-reference/lean-backtest)

**Pertinence:** Architecture cloud, API backtesting, deployment strategies

---

## 📈 Backtrader

**Description:** Framework Python pour backtesting et trading algorithmique

### Documentation
- [Backtrader Documentation](https://www.backtrader.com/docu/)
- [GitHub Docs Repository](https://github.com/backtrader/backtrader-docs)

**Pertinence:** Indicators API, strategy patterns, position management

---

## 📊 Empyrical

**Description:** Librairie de métriques financières par Quantopian (obsolète mais référence)

### Documentation
- [Empyrical Documentation](https://quantopian.github.io/empyrical/)
- [GitHub Repository](https://github.com/quantopian/empyrical)

**Pertinence:** Sharpe ratio, Sortino, Calmar, drawdown analysis, risk metrics

**Note:** Quantopian fermé en 2020, mais empyrical reste une référence pour les métriques

---

## ⚡ VectorBT

**Description:** Framework vectorisé ultra-rapide pour backtesting

### Documentation
- [VectorBT Documentation](https://vectorbt.dev/documentation/)
- [GitHub Repository](https://github.com/polakowo/vectorbt)

**Pertinence:** Vectorisation, performance optimization, parallel backtesting, portfolio analysis

**Use Case:** Inspiration pour notre moteur vectorisé (`engine/backtest.py`)

---

## 📉 QuantStats

**Description:** Librairie de métriques et visualisation pour portfolios

### Documentation
- [GitHub Repository](https://github.com/ranaroussi/quantstats)
- [Releases](https://github.com/ranaroussi/quantstats/releases)

**Pertinence:** Portfolio analytics, risk metrics, HTML reports, tearsheet generation

**Use Case:** Actuellement utilisé dans `analysis/metrics.py`

---

## 🎓 MLFinLab

**Description:** Machine Learning pour finance par Hudson & Thames

### Documentation
- [GitHub Repository](https://github.com/hudson-and-thames/mlfinlab)
- [MLFinLab Documentation](https://hudsonthames.org/mlfinlab/)

**Pertinence:** Feature engineering, labeling methods, portfolio optimization, risk models

**Use Case:** Techniques avancées pour `optimization/` et feature engineering

---

## 🎯 Utilisation dans le Projet

### Métriques (`analysis/metrics.py`)
**Références:**
- Empyrical: Sharpe, Sortino, Calmar formulas
- QuantStats: Portfolio metrics, drawdown analysis

### Backtesting Engine (`engine/backtest.py`)
**Références:**
- VectorBT: Vectorisation patterns
- Backtrader: Position management, order execution

### Optimization (`optimization/`)
**Références:**
- MLFinLab: Walk-forward analysis, overfitting guards
- QuantConnect: Parameter optimization strategies

### Validation (`validation/`)
**Références:**
- MLFinLab: Deflated Sharpe Ratio, PBO (Probability of Backtest Overfitting)
- Empyrical: Risk-adjusted returns

---

## 📖 Best Practices Référencées

### Walk-Forward Analysis
- **Source:** QuantConnect, MLFinLab
- **Implementation:** `optimization/walk_forward.py`
- **Pattern:** Rolling window, in-sample/out-of-sample split

### Overfitting Guards
- **Source:** MLFinLab (Deflated Sharpe, PBO)
- **Implementation:** `optimization/overfitting_guard.py` (planned)
- **Métriques:** Combinatorial purging, cross-validation

### Position Management
- **Source:** Backtrader
- **Implementation:** `engine/position_manager.py`
- **Pattern:** Multi-TP (50%/30%/20%), trailing SL

### Risk Metrics
- **Source:** Empyrical, QuantStats
- **Implementation:** `analysis/metrics.py`
- **Métriques:** Sharpe, Sortino, Calmar, VaR, CVaR

---

## 🔗 Liens Rapides

| Framework | Type | GitHub | Docs | Status |
|-----------|------|--------|------|--------|
| QuantConnect | Platform | [Link](https://github.com/QuantConnect/Lean) | [Link](https://www.quantconnect.com/docs/v2) | ✅ Active |
| Backtrader | Library | [Link](https://github.com/mementum/backtrader) | [Link](https://www.backtrader.com/docu/) | ✅ Mature |
| Empyrical | Metrics | [Link](https://github.com/quantopian/empyrical) | [Link](https://quantopian.github.io/empyrical/) | ⚠️ Archived |
| VectorBT | Vectorized | [Link](https://github.com/polakowo/vectorbt) | [Link](https://vectorbt.dev/documentation/) | ✅ Active |
| QuantStats | Analytics | [Link](https://github.com/ranaroussi/quantstats) | N/A | ✅ Active |
| MLFinLab | ML Finance | [Link](https://github.com/hudson-and-thames/mlfinlab) | [Link](https://hudsonthames.org/mlfinlab/) | ✅ Active |

---

## 📝 Notes d'Implémentation

### Inspirations Actuelles
1. **VectorBT:** Notre moteur vectorisé (`engine/backtest.py`) s'inspire de leur approche
2. **QuantStats:** Utilisé directement dans `analysis/metrics.py`
3. **Empyrical:** Formules de Sharpe/Sortino/Calmar alignées sur leurs standards

### À Implémenter
1. **MLFinLab Guards:**
   - Deflated Sharpe Ratio
   - Probability of Backtest Overfitting (PBO)
   - Combinatorial Purged Cross-Validation

2. **QuantConnect Patterns:**
   - Parameter optimization avec constraints
   - Multi-asset portfolio allocation

3. **Backtrader Features:**
   - Order types avancés (limit, stop-limit)
   - Commission models plus sophistiqués

---

## 🎓 Lectures Recommandées

### Livres Référencés
1. **"Advances in Financial Machine Learning"** - Marcos López de Prado
   - Source: MLFinLab patterns
   - Topics: Labeling, feature engineering, backtesting pitfalls

2. **"Quantitative Trading"** - Ernest P. Chan
   - Source: Walk-forward analysis, position sizing
   - Topics: Mean reversion, momentum strategies

3. **"Evidence-Based Technical Analysis"** - David Aronson
   - Source: Statistical significance, data snooping
   - Topics: Hypothesis testing, multiple testing corrections

### Papers Référencés
1. **"The Deflated Sharpe Ratio"** - Bailey & López de Prado (2014)
2. **"The Probability of Backtest Overfitting"** - Bailey et al. (2015)
3. **"Optimal Sharpe Ratio and Multi-Period Portfolio Selection"** - Cvitanić et al. (2008)

---

## 🔄 Mises à Jour

### 2026-01-24
- ✅ Documentation QuantConnect v2 ajoutée
- ✅ Backtrader docs repository ajouté
- ✅ Empyrical (archived) référencé
- ✅ VectorBT documentation ajoutée
- ✅ QuantStats releases trackées
- ✅ MLFinLab documentation ajoutée

### Prochaines Actions
- [ ] Implémenter Deflated Sharpe Ratio (MLFinLab)
- [ ] Ajouter PBO calculation (MLFinLab)
- [ ] Créer HTML reports (QuantStats patterns)
- [ ] Optimiser vectorisation (VectorBT patterns)

---

**Dernière mise à jour:** 24 janvier 2026, 13:35 UTC
