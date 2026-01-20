# Handoff — FINAL TRIGGER v2 Backtest System

**Dernière MAJ**: 20 janvier 2026

**📋 Plan Complet**: Voir [claude.md](../claude.md) à la racine du projet

---

## 🎯 Objectif

Convertir l'indicateur TradingView "FINAL TRIGGER v2 - State/Transition + A/D Line + Ichi Light" en Python avec système de backtest professionnel, walk-forward analysis et optimisation bayésienne.

---

## ✅ État Actuel (82% complété)

### Architecture Implémentée

```
crypto_backtest/
├── config/settings.py           ✅ Paramètres globaux
├── data/
│   ├── fetcher.py               ✅ CCXT multi-exchange
│   ├── storage.py               ✅ Cache Parquet
│   └── preprocessor.py          ✅ Nettoyage données
├── indicators/
│   ├── mama_fama_kama.py        ✅ MESA Adaptive MA (compute_alpha aligné Pine)
│   ├── ichimoku.py              ✅ 17 cond bull + 3 cond bear Light
│   ├── five_in_one.py           ✅ 5 filtres avec toggles
│   └── atr.py                   ✅ ATR pour SL/TP
├── strategies/
│   ├── base.py                  ✅ Interface abstraite
│   └── final_trigger.py         ✅ Puzzle + Grace logic
├── engine/
│   ├── backtest.py              ✅ Moteur vectorisé
│   ├── execution.py             ✅ Fees/slippage
│   └── position_manager.py      ✅ Multi-TP (50/30/20) + trailing
├── optimization/
│   ├── bayesian.py              ✅ Optuna TPE
│   └── walk_forward.py          ✅ Walk-forward analysis
├── analysis/
│   ├── metrics.py               ✅ Sharpe, Sortino, Calmar, etc.
│   ├── visualization.py         ✅ Plotly charts
│   └── validation.py            ✅ Compare Pine vs Python
└── examples/
    ├── run_backtest.py          ✅ Demo principal
    ├── compare_signals.py       ✅ Validation Pine
    └── optimize_final_trigger.py ✅ Optim demo
```

### Tests
- **17 tests passent** (`pytest -v`)
- Couverture: indicateurs, backtest, position manager

---

## 🧩 Validation Pine (FINAL LONG/SHORT)

Le script `tests/compare_signals.py` compare désormais les signaux Python
à `FINAL LONG` / `FINAL SHORT` et génère les entrées via le pipeline
`FinalTriggerStrategy` (Ichimoku externe + 5in1 Light + Puzzle/Grace).

### Fichiers ajoutés/modifiés
- `tests/compare_signals.py` (comparaison FINAL LONG/SHORT + debug trend)
- `data/BYBIT_BTCUSDT-60.csv` (dataset TradingView)

### Résultats
- `python tests/compare_signals.py --file data/BYBIT_BTCUSDT-60.csv --warmup 150` : 100% match FINAL LONG/SHORT.
- Backtest local exporté sur `crypto_backtest/BYBIT_BTCUSDT, 60 (1).csv` (fichiers dans `outputs/`).

---

## 🔧 Configuration Par Défaut (Alignée Pine)

### ⚠️ FILTRES ACTIFS (IMPORTANT)

**NOIR SUR BLANC**: Seuls **2 filtres Ichimoku** sont actifs avec la config par défaut :

1. **Ichimoku Externe** (Puzzle) - 17 conditions bullish, 3 conditions bearish Light
2. **Ichimoku 5-in-1** (Five-in-One) - Seul filtre actif dans le système 5-in-1

**TOUS les autres filtres sont DÉSACTIVÉS** :
- ❌ MAMA/KAMA filter (`use_mama_kama_filter = False`)
- ❌ Distance filter (`use_distance_filter = False`)
- ❌ Volume filter (`use_volume_filter = False`)
- ❌ Regression Cloud (`use_regression_cloud = False`)
- ❌ KAMA Oscillator (`use_kama_oscillator = False`)

### Configuration Complète

```python
# FinalTriggerParams defaults
use_mama_kama_filter = False      # ❌ OFF - MAMA/KAMA ignorés
require_fama_between = False      # ❌ OFF
strict_lock_5in1_last = False     # ❌ OFF
grace_bars = 1                    # ✅ 1 bar grace window

# FiveInOneConfig defaults
use_distance_filter = False       # ❌ OFF
use_volume_filter = False         # ❌ OFF
use_regression_cloud = False      # ❌ OFF
use_kama_oscillator = False       # ❌ OFF
use_ichimoku_filter = True        # ✅ ON - SEUL FILTRE 5IN1 ACTIF
ichi5in1_strict = False           # Light mode (3 cond bear)
use_transition_mode = False       # State mode (pas Transition)
```

### Logique Simplifiée Effective

1. **Ichimoku Externe** → Donne le biais directionnel (`ichi_long_active` / `ichi_short_active`)
2. **5-in-1 = Ichimoku Light uniquement** → Signal quand `allBull` / `allBear` (state mode)
3. **Puzzle** → Combine les deux Ichimoku + grace window 1 bar
4. **Entry** → Génère SL/TP1/TP2/TP3 basés sur ATR

### Paramètres Réellement Actifs

Avec cette config, les **SEULS paramètres ayant un impact** sur les signaux sont:

| Catégorie | Paramètres | Impact |
|-----------|------------|--------|
| **ATR SL/TP** | `sl_mult`, `tp1_mult`, `tp2_mult`, `tp3_mult` | ⭐⭐⭐ MAJEUR (performance) |
| **Ichimoku Externe** | `tenkan`, `kijun`, `displacement` | ⭐⭐ Modéré (timing signaux) |
| **Ichimoku 5-in-1** | `tenkan_5`, `kijun_5`, `displacement_5` | ⭐⭐ Modéré (validation) |
| **Grace** | `grace_bars` | ⭐ Mineur (0 ou 1) |

**Tous les autres paramètres** (MAMA/KAMA lengths, fast/slow periods, etc.) n'ont **AUCUN EFFET** car les filtres correspondants sont désactivés.

---

## 📋 Checklist

### Complété
- [x] Scanner le repo et confirmer la structure
- [x] Poser l'ossature des modules/fichiers
- [x] Implémenter la couche data (fetcher/cache/preprocess)
- [x] Indicateurs core + tests unitaires de base
- [x] Aligner MAMA/FAMA/KAMA sur `computeAlpha()` MESA (alpha/beta dynamiques)
- [x] Stratégie Final Trigger + moteur de backtest + position manager multi-TP
- [x] Rendre l'ordre intra-bar et le sizing configurables + tests associés
- [x] Aligner compounding avec coûts + scénarios backtest multi-legs
- [x] Tests `sizing_mode="equity"` (compounding net of costs)
- [x] Ajouter métriques/visualisation + optimisation (Bayesian, walk-forward)
- [x] Ajouter un outil de comparaison des signaux Pine vs Python
- [x] Fix FutureWarning: `Hour.delta` deprecated dans `metrics.py`
- [x] Fix: BayesianOptimizer convertit correctement dict → dataclass
- [x] Aligner defaults Python sur config Pine utilisateur
- [x] Sizing basé sur le risque (`risk_per_trade`) + export backtest CSV
- [x] Autoriser réentrée sur la bougie de sortie (backtest)

### À Faire
- [ ] Valider cohérence signaux vs Pine sur CSV 2000+ bougies
- [ ] Inspecter `compare_report.csv` pour isoler divergences résiduelles
- [ ] Ajouter tests unitaires pour `optimize_final_trigger.py`
- [ ] Créer `optimization/overfitting_guard.py` (Deflated Sharpe, PBO)
- [ ] Documenter le workflow d'optimisation dans README
- [ ] Notebook tutoriel optimisation

---

## 🔴 Problèmes Connus

### 1. Warmup Indicateurs MESA
Les indicateurs MAMA/FAMA/KAMA nécessitent ~200-300 bougies pour converger. Les premiers signaux peuvent diverger du Pine pendant cette période.

**Solution**: Ignorer les 300 premières bougies dans les comparaisons.

### 2. barstate.isconfirmed
Pine vérifie `barstate.isconfirmed` avant de générer des signaux. Python n'a pas cet équivalent explicite.

**Impact**: En backtest historique, toutes les bougies sont "confirmées". En live, attention à la dernière bougie.

---

## 📊 Décisions Techniques

| Décision | Raison |
|----------|--------|
| Reproduction fidèle logique Pine | Éviter écarts de signaux |
| Manager multi-TP avec trailing | Refléter comportement visuel Pine |
| MAMA/FAMA/KAMA via `computeAlpha()` MESA | Coller au Pine (alpha/beta dynamiques) |
| Coûts appliqués à la sortie (net_pnl) | Compounding cohérent en mode `equity` |
| Param space standardisé `base_params` + `search_space` | Optuna compatible |
| Exports CSV comparaison dans repo | Traçabilité des écarts |
| Filtres modulaires avec toggles | Flexibilité pour tester configs |
| Defaults alignés sur la config Pine | Light + State, filtre MAMA/KAMA désactivé |
| Sizing risk-based (`risk_per_trade`) | Risque fixe par trade, notional ajusté au stop |
| Réentrée sur bougie de sortie | Permet d'enchaîner les signaux sans attente |

---

## 🚀 Commandes Utiles

```bash
# Tests
pytest -v

# Comparer signaux Pine vs Python
python crypto_backtest/examples/compare_signals.py

# Demo optimisation (10 trials)
python crypto_backtest/examples/optimize_final_trigger.py

# Optimisation Ichimoku (Tenkan/Kijun)
python optimize_ichimoku.py

# Walk-forward analysis
python walk_forward_analysis.py

# Backtest simple
python crypto_backtest/examples/run_backtest.py

# Backtest CSV local (export via script simple)
python crypto_backtest/examples/simple_backtest.py --file data/BYBIT_BTCUSDT-60.csv --warmup 150
```

---

## 🎯 Optimisation SL/TP (20 janvier 2026)

### Résultats Optimisation Bayésienne (50 trials)

**Dataset**: Binance BTCUSDT 1h, 2 ans (17,320 bars après warmup)

**Paramètres optimisés**: Uniquement les 4 ratios ATR SL/TP (tous les autres paramètres aux valeurs par défaut)

| Config | SL | TP1 | TP2 | TP3 | Return | Sharpe | Max DD | Win Rate |
|--------|-----|-----|-----|-----|--------|--------|--------|----------|
| **Défaut** | 3.0 | 2.0 | 6.0 | 10.0 | -6.44% | -0.14 | -9.2% | 33.6% |
| **Optimisé** | 3.75 | 3.75 | 9.0 | 7.0 | +10.76% | 1.43 | -2.9% | 40.9% |
| **Amélioration** | +25% | +87% | +50% | -30% | **+17.2pp** | **+1.57** | **-6.3pp** | **+7.3pp** |

### Insights Clés

1. **TP1 beaucoup plus haut (3.75)** = Laisse courir les profits au lieu de prendre trop tôt
2. **SL plus large (3.75)** = Moins de faux stops, meilleure win rate
3. **TP2 plus loin (9.0)** = Capture les grands mouvements
4. **TP3 réduit (7.0)** = Le runner est rarement atteint, autant le rapprocher

### Impact Mesurable

- **Return**: De **perdant (-6.44%)** à **gagnant (+10.76%)**
- **Sharpe Ratio**: De **négatif (-0.14)** à **solide (1.43)**
- **Max Drawdown**: Réduit de **71%** (-9.2% → -2.9%)
- **Profit Factor**: De **0.86** (perdant) à **1.33** (gagnant)
- **Trades**: 425 au lieu de 575 (sélectivité accrue)

### Conclusion

Les **ratios SL/TP sont LE facteur clé de performance**. L'optimisation a montré que:
- Avec les paramètres par défaut + SL/TP optimisés → **Sharpe 1.43**
- Avec 14 paramètres optimisés (incluant Ichimoku, 5in1, etc.) → **Sharpe 1.61**

**Différence**: Seulement +0.18 de Sharpe pour 10 paramètres additionnels, confirmant que **SL/TP >> tout le reste**.

---

## 🎯 Optimisation Ichimoku (Tenkan/Kijun) — 20 janvier 2026

### Résultats (50 trials, SL/TP fixés à 3.75/3.75/9.0/7.0)

**Best Sharpe**: 2.1352

**Paramètres optimaux**:
- `ichimoku.tenkan`: 13 (défaut: 9)
- `ichimoku.kijun`: 34 (défaut: 26)
- `five_in_one.tenkan_5`: 12 (défaut: 9)
- `five_in_one.kijun_5`: 21 (défaut: 26)

### Comparaison

- **SL/TP optimisés + Ichimoku défaut**: Sharpe 1.43
- **SL/TP + Ichimoku optimisés**: Sharpe 2.14
- **Gain**: +0.71

**Output**: `outputs/optimization_ichimoku_results.txt`

---

## 📁 Fichiers Clés

| Fichier | Description |
|---------|-------------|
| `indicators/mama_fama_kama.py` | MESA Adaptive MA avec Hilbert Transform |
| `indicators/five_in_one.py` | 5 filtres combinables (Distance, Volume, RegCloud, KAMA Osc, Ichi5in1) |
| `indicators/ichimoku.py` | Ichimoku externe (17 cond bull, 3 cond bear Light) |
| `strategies/final_trigger.py` | Stratégie complète Puzzle + Grace |
| `engine/position_manager.py` | Gestion multi-TP (50/30/20) + trailing SL |
| `optimization/bayesian.py` | Optimisation Optuna TPE |
| `examples/compare_signals.py` | Validation signaux Pine vs Python |
| `walk_forward_analysis.py` | Script WFA (IS/OOS) avec optimisation SL/TP |

---

## 📈 Paramètres Optimisables

| Paramètre | Range | Type | Description |
|-----------|-------|------|-------------|
| `kama_length` | 10-50 | int | Période MAMA/KAMA |
| `tenkan` | 5-15 | int | Tenkan-sen Ichimoku |
| `kijun` | 20-35 | int | Kijun-sen Ichimoku |
| `sl_mult` | 1.5-5.0 | float | SL en multiples ATR |
| `tp1_mult` | 1.0-4.0 | float | TP1 en multiples ATR |
| `tp2_mult` | 4.0-10.0 | float | TP2 en multiples ATR |
| `tp3_mult` | 6.0-15.0 | float | TP3 Runner en multiples ATR |
| `grace_bars` | 0-1 | int | Fenêtre de grâce |

**Toggles binaires:**
- `use_mama_kama_filter`, `require_fama_between`, `strict_lock_5in1_last`
- `use_distance_filter`, `use_volume_filter`, `use_ad_line`
- `use_regression_cloud`, `use_kama_oscillator`
- `use_ichimoku_filter`, `ichi5in1_strict`, `use_transition_mode`

---

## 🎯 Next Steps Prioritaires

1. **Exporter CSV TradingView** avec 2000+ bougies et signaux Pine
2. **Lancer `compare_signals.py`** et vérifier 100% match après warmup
3. **Créer test E2E** validant signaux sur données réelles
4. **Documenter workflow** dans README principal
