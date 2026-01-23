# Plan: Système de Backtest Pro pour "FINAL TRIGGER v2"

**Derniere MAJ**: 23 janvier 2026

## Objectif
Convertir l'indicateur TradingView "FINAL TRIGGER v2 - State/Transition + A/D Line + Ichi Light" en Python et créer un système de backtest professionnel avec walk-forward analysis et optimisation bayésienne.

## Etat Actuel: 24 janvier 2026 - Reproducibility Crisis Identified & Fixed

**Tests**: 17 tests passent (`pytest -v`)
**Validation**: 100% match FINAL LONG/SHORT vs Pine Script (apres warmup)

### 🚨 CRITICAL BUG FOUND & FIXED
**Issue**: Parallel optimization (workers > 1) with Optuna TPESampler was **non-deterministic**
- Numpy RNG not seeded globally
- Python random module not seeded
- Optuna TPESampler seeds hardcoded to 42 (collisions in parallel)
- Monte Carlo p-values non-reproductible

**Impact**: All Phase 1 Screening results (350+ assets) were **scientifically unreliable**

**Solution Applied**: Option B Strategy (see REPRODUCIBILITY_STRATEGY.md)
- Phase 1: Fast screening with workers=10 (filtre grossier)
- Phase 2: Strict validation with workers=1 (reproductible)
- Phase 3: Multi-seed robustness (optional, ultra-rigorous)

**Current Status**:
- ✅ Reproducibility fixes applied to parallel_optimizer.py
- ✅ New REPRODUCIBILITY_STRATEGY.md created
- ⏳ Phase 1 Screening candidates identified
- 🔄 Phase 2 Validation (workers=1) starting soon

## Résumé du Code Pine Script (1223 lignes)

**Architecture de la stratégie:**
1. **MAMA/FAMA/KAMA** - MESA Adaptive Moving Average avec Hilbert Transform
2. **Ichimoku Externe** - Donne le biais directionnel (17 conditions bullish, 3 bearish)
3. **5-in-1 Filter** - 5 sous-filtres combinés avec toggles individuels
4. **Puzzle + Grace Logic** - Système de validation avec fenêtre de grâce 1 bar
5. **ATR Multi-TP** - SL + 3 niveaux TP avec trailing (50%/30%/20%)

**Configuration par défaut (alignée sur Pine):**
- `use_mama_kama_filter = False` (OFF)
- `use_ichimoku_filter = True` (ON - SEUL FILTRE ACTIF)
- `ichi5in1_strict = False` (Light - 3 cond bearish)
- `use_transition_mode = False` (State mode)
- `grace_bars = 1`

---

## Architecture du Projet

```
crypto_backtest/
├── config/
│   ├── __init__.py
│   └── settings.py              # Paramètres globaux (fees, exchanges)
├── data/
│   ├── __init__.py
│   ├── fetcher.py               # CCXT multi-exchange
│   ├── storage.py               # Cache Parquet
│   └── preprocessor.py          # Nettoyage données
├── indicators/
│   ├── __init__.py
│   ├── base.py                  # Interface abstraite
│   ├── mama_fama_kama.py        # MESA Adaptive MA + Hilbert Transform
│   ├── ichimoku.py              # Système Ichimoku complet
│   ├── five_in_one.py           # Distance, OBV, RegCloud, KAMA Osc
│   └── atr.py                   # ATR pour SL/TP
├── strategies/
│   ├── __init__.py
│   ├── base.py                  # Classe abstraite Strategy
│   └── final_trigger.py         # Stratégie FINAL TRIGGER complète
├── engine/
│   ├── __init__.py
│   ├── backtest.py              # Moteur vectorisé
│   ├── execution.py             # Simulation fees/slippage
│   └── position_manager.py      # Gestion multi-TP (50%/30%/20%)
├── optimization/
│   ├── __init__.py
│   ├── walk_forward.py          # Walk-forward analysis
│   ├── bayesian.py              # Optuna TPE
│   └── overfitting_guard.py     # Deflated Sharpe, PBO
├── analysis/
│   ├── __init__.py
│   ├── metrics.py               # Sharpe, Sortino, Calmar, etc.
│   └── visualization.py         # Plotly charts
├── requirements.txt
└── examples/
    └── run_backtest.py          # Script principal
```

---

## Dashboard Streamlit (`app.py`)

Interface visuelle complète pour piloter les backtests sans ligne de commande.

**Fonctionnalités**:
- **Dashboard** — Vue d'ensemble (données, optimisations, guards)
- **Download OHLCV** — Téléchargement données (Top 50 cryptos par tiers)
- **Comparateur Pine** — Compare signaux Python vs Pine Script
- **Bayesian** — Optimisation bayésienne (ATR + Ichimoku + Displacement)
- **Displacement Grid** — Grid search displacement isolé [26-78]
- **Guards** — Tests de robustesse (7 guards: Monte Carlo, WFE, Bootstrap, etc.)
- **Comparaison Assets** — Tri/filtre des résultats multi-asset
- **Portfolio Builder** — Corrélations + auto-sélection assets décorrélés
- **Visualisation** — Graphiques Plotly interactifs (equity curves, heatmaps)

**Design**: Dark Trading Theme
- Fond noir (#0E1117), accent cyan (#00D4FF)
- Gradient cards, glow buttons, styled tabs
- Navigation par boutons avec session_state

**Usage**:
```bash
streamlit run app.py
# Accès: http://localhost:8501
```

**Changelog**:
- 2026-01-21: Fix navigation sidebar (radio → session_state buttons)
- 2026-01-20: Première version complète (~2300 lignes)

---

## Phase 1: Setup & Data Layer

### 1.1 Dépendances (`requirements.txt`)
```
pandas>=2.0.0
numpy>=1.24.0
ccxt>=4.0.0
numba>=0.58.0
optuna>=4.0.0
pydantic>=2.0.0
plotly>=5.18.0
scipy>=1.11.0
quantstats>=0.0.62
pyarrow>=14.0.0
python-dotenv>=1.0.0
rich>=13.0.0
pytest>=7.4.0
```

### 1.2 Data Fetcher (`data/fetcher.py`)
- Classe `DataFetcher` utilisant CCXT
- Support Binance, Bybit, OKX via interface unifiée
- Pagination automatique pour historique long
- Cache local en Parquet pour éviter re-téléchargement

### 1.3 Preprocessor (`data/preprocessor.py`)
- Validation des données (gaps, outliers)
- Normalisation timezone UTC
- Split train/test avec gap de sécurité

---

## Phase 2: Conversion des Indicateurs

### 2.1 MAMA/FAMA/KAMA (`indicators/mama_fama_kama.py`)

**Éléments Pine Script à convertir:**
```python
# Hilbert Transform
def hilbert_transform(x: np.ndarray) -> np.ndarray:
    """0.0962*x + 0.5769*x[2] - 0.5769*x[4] - 0.0962*x[6]"""

# MESA Period computation
def compute_mesa_period(src: pd.Series) -> pd.Series:
    """Calcul adaptatif de la période MESA"""

# MAMA/FAMA
def compute_mama_fama(src: pd.Series, fast_limit: float, slow_limit: float):
    """
    mama = a * src + (1-a) * mama[1]
    fama = b * mama + (1-b) * fama[1]
    """

# KAMA avec ER
def compute_kama(src: pd.Series, length: int) -> pd.Series:
    """KAMA basé sur Efficiency Ratio"""
```

**Paramètres optimisables:**
- `len` (défaut: 20)
- `requireFamaBetween` (bool)

### 2.2 Ichimoku (`indicators/ichimoku.py`)

**Fonctions à implémenter:**
```python
def donchian(high: pd.Series, low: pd.Series, length: int) -> pd.Series:
    """(highest + lowest) / 2"""

class Ichimoku:
    def __init__(self, tenkan: int = 9, kijun: int = 26, displacement: int = 52):
        pass

    def compute(self, data: pd.DataFrame) -> pd.DataFrame:
        """Retourne Tenkan, Kijun, KumoA, KumoB"""

    def all_bullish(self, close: pd.Series) -> pd.Series:
        """Condition bullish complète (17 conditions)"""

    def all_bearish(self, close: pd.Series) -> pd.Series:
        """Condition bearish complète"""
```

**Paramètres optimisables:**
- `TS_D1` (9), `KS_D1` (26), `displacement` (52)

### 2.3 Five-in-One Filter (`indicators/five_in_one.py`)

**5 sous-filtres:**

```python
class FiveInOneFilter:
    def __init__(self, config: FiveInOneConfig):
        pass

    # 1. Distance Filter - KAMA multi-périodes
    def distance_filter(self, ohlc4: pd.Series) -> pd.Series:
        """18 KAMAs (5,10,15...100), calcul distance moyenne"""

    # 2. Volume Filter (A/D Line OU OBV classique)
    def ad_line_filter(self, high, low, close, volume) -> pd.Series:
        """
        A/D Line (Chaikin): MFM = ((close-low) - (high-close)) / (high-low)
        Normalisé sur adNormPeriod, avec slope sur 3 bars
        Bull: adNorm > 0.1 AND adSlope > 0
        """

    def obv_filter(self, close: pd.Series, volume: pd.Series) -> pd.Series:
        """OBV classique + EMA(3,9,21), signal bull/bear"""

    # 3. Regression Cloud
    def regression_cloud_filter(self, close: pd.Series) -> pd.Series:
        """
        Slopes sur 8 périodes (10,20,50,100,200,300,400,500)
        cloudLine = SMA(100) + regTotalDistance * 0.1
        """

    # 4. KAMA Oscillator
    def kama_oscillator(self, close: pd.Series) -> pd.Series:
        """KAMA normalisé [-0.5, 0.5]"""

    # 5. Ichimoku 5in1 (Strict vs Light)
    def ichimoku_5_filter(self, data: pd.DataFrame, strict: bool) -> pd.Series:
        """
        Strict: 17 conditions bullish, 17 conditions bearish
        Light: 3 conditions bearish seulement (close < KumoA[25], < KumoB[25], < KumoB)
        """

    def compute_combined(self, data: pd.DataFrame, transition_mode: bool) -> pd.Series:
        """
        Combine les 5 filtres selon config
        Si transition_mode: exige changement d'état (not prevAllBull/Bear)
        """
```

**Paramètres optimisables:**
- `fast_period` (7), `slow_period` (19), `er_period` (8)
- `norm_period` (50), `useNorm` (bool)
- `adNormPeriod` (50) - pour A/D Line
- `useADLine` (bool) - A/D Line vs OBV
- `ichi5in1Strict` (bool) - Strict vs Light
- `useTransitionMode` (bool) - State vs Transition
- Toggles pour chaque filtre

---

## Phase 3: Stratégie FINAL TRIGGER

### 3.1 Logic Core (`strategies/final_trigger.py`)

```python
class FinalTriggerStrategy(BaseStrategy):
    """
    Logique Puzzle + Grace:
    1. Ichimoku donne le biais directionnel (ichi_long_active/short_active)
    2. MAMA/KAMA donne la confirmation (cond_mk_long/short)
    3. 5in1 donne le timing (bullishSignal_close)
    4. Grace window permet 1 bar de délai si conditions presque OK
    """

    def __init__(self, params: FinalTriggerParams):
        self.params = params

    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Retourne DataFrame avec colonnes:
        - signal: 1 (long), -1 (short), 0 (neutral)
        - entry_price, sl_price, tp1_price, tp2_price, tp3_price
        - qty_split: [0.50, 0.30, 0.20]
        """
```

### 3.2 Position Manager (`engine/position_manager.py`)

**Gestion multi-TP spécifique:**
```python
class MultiTPPositionManager:
    """
    Gère les 3 ordres par trade:
    - Order 1: 50% du capital, TP1 (2R)
    - Order 2: 30% du capital, TP2 (6R)
    - Order 3: 20% du capital, TP3 runner (10R)

    Trailing logic:
    - Après TP1: SL → Breakeven (entry)
    - Après TP2: SL → TP1
    """
```

---

## Phase 4: Moteur de Backtest

### 4.1 Backtest Engine (`engine/backtest.py`)

```python
class VectorizedBacktester:
    def __init__(self, config: BacktestConfig):
        self.config = config  # fees, slippage, capital

    def run(self, data: pd.DataFrame, strategy: BaseStrategy) -> BacktestResult:
        """
        1. Génère signaux vectorisés
        2. Simule positions avec multi-TP
        3. Applique fees/slippage
        4. Calcule equity curve
        """
```

### 4.2 Métriques (`analysis/metrics.py`)

**Métriques calculées:**
- Total Return, Annual Return (CAGR)
- Sharpe Ratio, Sortino Ratio, Calmar Ratio
- Max Drawdown (% et durée)
- Win Rate, Profit Factor
- Expectancy (R-multiple moyen)
- VaR 95%, CVaR 95%
- Stats par heure UTC (6 blocs de 4h)
- Stats par jour de semaine

---

## Phase 5: Walk-Forward Analysis

### 5.1 Implementation (`optimization/walk_forward.py`)

```python
class WalkForwardAnalyzer:
    def __init__(self, config: WalkForwardConfig):
        self.in_sample_days = 180   # 6 mois training
        self.out_of_sample_days = 30  # 1 mois test
        self.optimizer = BayesianOptimizer()

    def analyze(self, data, strategy_class, param_space) -> WalkForwardResult:
        """
        Pour chaque fenêtre:
        1. Optimise sur in-sample
        2. Teste sur out-of-sample (non vu)
        3. Combine tous les OOS pour performance réelle
        """
```

**Métriques de robustesse:**
- Degradation Ratio (OOS/IS performance)
- Efficiency Ratio (% performance retenue)
- Parameter Stability (variation des params optimaux)

### 5.2 Optimisation Bayésienne (`optimization/bayesian.py`)

```python
class BayesianOptimizer:
    """Utilise Optuna TPE pour exploration efficace"""

    def optimize(self, data, strategy_class, param_space, n_trials=100):
        # Définit l'espace de recherche
        # Exécute n_trials avec pruning
        # Retourne meilleurs params + importance
```

**Paramètres à optimiser pour FINAL TRIGGER v2:**

| Paramètre | Range | Type | Description |
|-----------|-------|------|-------------|
| len (MAMA) | 10-50 | int | Période MAMA |
| TS_D1 | 5-15 | int | Tenkan-sen Ichimoku |
| KS_D1 | 20-35 | int | Kijun-sen Ichimoku |
| fast_period | 5-15 | int | 5in1 Fast Period |
| slow_period | 15-30 | int | 5in1 Slow Period |
| adNormPeriod | 20-100 | int | A/D Line normalisation |
| slMult | 1.5-5.0 | float | SL en multiples ATR |
| tp1Mult | 1.0-4.0 | float | TP1 en multiples ATR |
| tp2Mult | 4.0-10.0 | float | TP2 en multiples ATR |
| tp3Mult | 6.0-15.0 | float | TP3 Runner en multiples ATR |
| graceBars | 0-1 | int | Fenêtre de grâce |

**Toggles binaires (combinatoires):**
| Toggle | Défaut | Impact |
|--------|--------|--------|
| useADLine | true | A/D Line vs OBV classique |
| ichi5in1Strict | true | 17 cond vs 3 cond bearish |
| useTransitionMode | true | Exige changement d'état |
| requireFamaBetween | false | FAMA entre MAMA et KAMA |
| strictLock_5in1Last | false | 5in1 doit être dernier signal |

---

## Phase 6: Vérification & Tests

### 6.1 Tests Unitaires
```bash
pytest tests/ -v
```

- `test_indicators.py`: Vérifier MAMA/KAMA/Ichimoku vs valeurs Pine Script
- `test_backtest.py`: Vérifier calculs P&L corrects
- `test_metrics.py`: Vérifier formules Sharpe/Sortino

### 6.2 Validation End-to-End

```python
# examples/run_backtest.py

from data.fetcher import DataFetcher
from strategies.final_trigger import FinalTriggerStrategy
from optimization.walk_forward import WalkForwardAnalyzer

# 1. Fetch data
fetcher = DataFetcher("binance")
data = fetcher.fetch_ohlcv("BTC/USDT", "1h", days=365*2)

# 2. Run walk-forward
analyzer = WalkForwardAnalyzer()
result = analyzer.analyze(data, FinalTriggerStrategy, PARAM_SPACE)

# 3. Print results
print(f"Combined Sharpe: {result.combined_metrics['sharpe_ratio']:.2f}")
print(f"Efficiency Ratio: {result.efficiency_ratio:.1f}%")
print(f"Degradation: {result.degradation_ratio:.2%}")
```

---

## État d'Implémentation

| Étape | Fichiers | Statut |
|-------|----------|--------|
| 1 | `requirements.txt`, `config/settings.py` | ✅ Complété |
| 2 | `data/fetcher.py`, `data/storage.py`, `data/preprocessor.py` | ✅ Complété |
| 3 | `indicators/mama_fama_kama.py` | ✅ Complété (compute_alpha aligné Pine) |
| 4 | `indicators/ichimoku.py` | ✅ Complété (17 bull + 3 bear Light) |
| 5 | `indicators/five_in_one.py` | ✅ Complété (5 filtres avec toggles) |
| 6 | `indicators/atr.py` | ✅ Complété |
| 7 | `strategies/final_trigger.py` | ✅ Complété (Puzzle + Grace) |
| 8 | `engine/backtest.py`, `position_manager.py` | ✅ Complété (Multi-TP + trailing) |
| 9 | `engine/execution.py` | ✅ Complété (fees/slippage) |
| 10 | `analysis/metrics.py`, `visualization.py` | ✅ Complété |
| 11 | `analysis/validation.py` | ✅ Complété |
| 12 | `optimization/bayesian.py`, `walk_forward.py` | ✅ Complété |
| 13 | `examples/run_backtest.py`, `simple_backtest.py` | ✅ Complété |
| 14 | `examples/compare_signals.py` | ✅ Complété |
| 15 | `examples/optimize_final_trigger.py` | ✅ Complété |

---

## Librairies Clés

- **pandas/numpy**: Calculs vectorisés
- **numba**: JIT pour indicateurs complexes (Hilbert Transform)
- **ccxt**: API exchanges unifiée
- **optuna**: Optimisation bayésienne TPE
- **quantstats**: Métriques financières
- **plotly**: Visualisation interactive

---

## Notes pour Débutant

1. **Chaque fichier est commenté** avec explications détaillées
2. **Exemples inclus** dans `examples/`
3. **Tests pour valider** chaque composant
4. **Architecture modulaire**: modifier un indicateur sans toucher au reste

---

## Configuration Choisie

- **Timeframe principal**: 1h
- **Directions**: LONG + SHORT (bidirectionnel)
- **Source données**: CCXT multi-exchange (Binance, Bybit, etc.)

### Configuration Indicateurs (défaut utilisateur)
```
useMamaKamaFilter = OFF      # Pas de filtre MAMA > KAMA
useDistanceFilter = OFF      # Pas de Distance Filter
useObvFilter = OFF           # Pas de Volume Filter
  └─ useADLine = ON          # (mais A/D Line prête si besoin)
useRegCloudFilter = OFF      # Pas de Regression Cloud
useKamaFilter = OFF          # Pas de KAMA Oscillator
ichimokuFilter = ON          # ✅ SEUL FILTRE ACTIF
  └─ ichi5in1Strict = OFF    # Version Light (3 conditions bearish)
useTransitionMode = OFF      # Mode State (pas Transition)
```

**Logique simplifiée résultante:**
1. Ichimoku externe donne le biais (ichi_long_active / ichi_short_active)
2. 5in1 = Ichimoku Light seul → signal quand allBull/allBear (state mode)
3. Puzzle combine les deux + grace window
4. Entry génère SL/TP1/TP2/TP3 basés sur ATR

---

## Modes de Filtrage KAMA

Le système propose 3 configurations de filtres pour gérer le trade-off performance vs overfit:

### BASELINE (Initial Optimization)
Configuration minimale utilisée pour l'optimisation initiale:
- ❌ MAMA/KAMA Filter (OFF)
- ❌ Distance Filter (OFF)
- ❌ Volume Filter (OFF)
- ❌ Regression Cloud (OFF)
- ❌ KAMA Oscillator (OFF)
- ✅ Ichimoku Filter (ON - seul actif)
- ❌ Ichi Strict Mode (Light - 3 conditions bearish)

**Usage**: Première optimisation pour identifier le potentiel de l'asset sans restrictions.

### MODERATE (Default Reopt) ⭐
**Configuration par défaut pour la ré-optimisation**, équilibre entre performance et robustesse:
- ❌ MAMA/KAMA Filter (OFF - per user preference)
- ✅ Distance Filter (ON)
- ✅ Volume Filter (ON - A/D Line)
- ✅ Regression Cloud (ON - per user preference)
- ✅ KAMA Oscillator (ON)
- ✅ Ichimoku Filter (ON)
- ❌ Ichi Strict Mode (Light - per user preference)

**Usage**: Recommandé pour tous les assets en phase de ré-optimisation. Réduit l'overfit sans dégrader excessivement la performance.

**Résultats DOGE**: Tests comparatifs montrent que l'application de filtres n'améliore pas toujours la performance:
- BASELINE (0 filtres): Sharpe 1.75, 459 trades
- CONSERVATIVE (5 filtres): Sharpe 1.41, 348 trades (-19% Sharpe)

### CONSERVATIVE (Severe Overfit Only)
Configuration maximale pour assets avec overfit sévère (WFE < 0.3):
- ✅ MAMA/KAMA Filter (ON)
- ✅ Distance Filter (ON)
- ✅ Volume Filter (ON)
- ✅ Regression Cloud (ON)
- ✅ KAMA Oscillator (ON)
- ✅ Ichimoku Filter (ON)
- ✅ Ichi Strict Mode (17 bull + 17 bear conditions)

**Usage**: Uniquement pour assets montrant des signes sévères d'overfit (WFE très faible, forte dégradation IS→OOS).

### Système de Recommandation

Le module `crypto_backtest/analysis/diagnostics.py` analyse automatiquement:
- Sharpe OOS, WFE, Max DD, Trade Count
- Dégradation IS→OOS
- Résultats guards (Monte Carlo, Sensitivity, Bootstrap)

**Recommandation automatique**:
- **MODERATE** (défaut) si WFE ≥ 0.3 et pas de multi-failures
- **CONSERVATIVE** si WFE < 0.3 ou overfit sévère détecté

---

## Checklist de Progression

### ✅ Complété

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
- [x] Système de diagnostics granulaires avec 6+ checks (Sharpe, WFE, DD, etc.)
- [x] Interface Reopt dans Streamlit avec navigation automatique + pre-fill settings
- [x] Tests comparatifs KAMA filters sur DOGE (BASELINE vs CONSERVATIVE)
- [x] Configurations de filtres MODERATE/CONSERVATIVE/BASELINE documentées
- [x] Recommandations automatiques de config filter dans diagnostics.py
- [x] MODERATE filter config comme défaut pour ré-optimisations

### 🔄 À Faire (Priorité)

- [ ] Tester MODERATE config sur assets FAIL pour valider amélioration WFE
- [ ] Valider cohérence signaux vs Pine sur CSV 2000+ bougies
- [ ] Inspecter `compare_report.csv` pour isoler divergences résiduelles
- [ ] Ajouter tests unitaires pour `optimize_final_trigger.py`
- [ ] Créer `optimization/overfitting_guard.py` (Deflated Sharpe, PBO)
- [ ] Documenter le workflow d'optimisation dans README
- [ ] Notebook tutoriel optimisation

---

## Problèmes Connus

### 1. Warmup Indicateurs MESA
Les indicateurs MAMA/FAMA/KAMA nécessitent ~200-300 bougies pour converger. Les premiers signaux peuvent diverger du Pine pendant cette période.

**Solution**: Ignorer les 300 premières bougies dans les comparaisons (flag `--warmup 150`).

### 2. barstate.isconfirmed
Pine vérifie `barstate.isconfirmed` avant de générer des signaux. Python n'a pas cet équivalent explicite.

**Impact**: En backtest historique, toutes les bougies sont "confirmées". En live, attention à la dernière bougie.

---

## Décisions Techniques

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
| 3 modes de filtrage (BASELINE/MODERATE/CONSERVATIVE) | Trade-off performance vs overfit adapté au contexte |
| MODERATE comme défaut reopt | Tests DOGE montrent que plus de filtres ≠ meilleure performance |
| Diagnostics granulaires avec recommandations auto | Guide reopt avec contexte (trials, displacement, filter mode) |

---

## Commandes Utiles

```bash
# Dashboard Streamlit (interface visuelle)
streamlit run app.py

# Tests
pytest -v

# Pipeline complet: download → optimize → cluster
python scripts/run_full_pipeline.py --workers 8

# Optimisation multi-asset avec guards
python scripts/run_guards_multiasset.py --assets BTC ETH AVAX UNI SEI --workers 4

# Analyse corrélations portfolio
python scripts/portfolio_correlation.py

# Comparer signaux Pine vs Python
python tests/compare_signals.py --file data/BYBIT_BTCUSDT-60.csv --warmup 150

# Demo optimisation (10 trials)
python crypto_backtest/examples/optimize_final_trigger.py

# Backtest simple
python crypto_backtest/examples/run_backtest.py
```

---

## Prochaines Étapes Prioritaires

1. ✅ ~~**Dashboard Streamlit**~~: Interface visuelle complète (DONE)
2. ✅ ~~**Displacement Grid Optimization**~~: Intégré dans le workflow 6 phases (Phase 3A/3B)
3. **Live Trading Connector**: Implémenter connecteur exchange pour trading live
4. **Documentation README**: Workflow complet et guide utilisateur
5. **Tests E2E supplémentaires**: Validation signaux sur datasets étendus

---

## Fichiers Clés (Mise à Jour 24 janvier 2026)

| Fichier | Description | Priorité |
|---------|-------------|----------|
| [REPRODUCIBILITY_STRATEGY.md](REPRODUCIBILITY_STRATEGY.md) | **LIRE EN PREMIER** — Stratégie Option B (workers parallèles vs séquentiel) | 🔴 CRÍTICA |
| [comms/PHASE1_PHASE2_INSTRUCTIONS.md](comms/PHASE1_PHASE2_INSTRUCTIONS.md) | Instructions concrètes pour Jordan (Phase 1) et Sam (Phase 2) | 🔴 CRÍTICA |
| [docs/WORKFLOW_MULTI_ASSET_SCREEN_VALIDATE_PROD.md](docs/WORKFLOW_MULTI_ASSET_SCREEN_VALIDATE_PROD.md) | Workflow 6 phases UPDATED avec Option B | ✅ ACTIVE |
| [app.py](app.py) | Dashboard Streamlit principal (~2300 lignes) | ✅ ACTIVE |
| [docs/HANDOFF.md](docs/HANDOFF.md) | **OBSOLETE** — ne plus utiliser | ❌ DEPRECATED |
| [crypto_backtest/config/asset_config.py](crypto_backtest/config/asset_config.py) | Config production (params optimaux par asset) |
| [crypto_backtest/config/scan_assets.py](crypto_backtest/config/scan_assets.py) | Top 50 cryptos (tiers) + critères de validation |
| [crypto_backtest/strategies/final_trigger.py](crypto_backtest/strategies/final_trigger.py) | Main strategy (Puzzle + Grace logic) |
| [crypto_backtest/indicators/ichimoku.py](crypto_backtest/indicators/ichimoku.py) | Ichimoku externe (17 bull / 3 bear Light) |
| [crypto_backtest/indicators/five_in_one.py](crypto_backtest/indicators/five_in_one.py) | 5 combinable filters |
| [crypto_backtest/engine/backtest.py](crypto_backtest/engine/backtest.py) | Vectorized backtest engine |
| [crypto_backtest/engine/position_manager.py](crypto_backtest/engine/position_manager.py) | Multi-TP (50/30/20) + trailing SL |
| [crypto_backtest/optimization/parallel_optimizer.py](crypto_backtest/optimization/parallel_optimizer.py) | Optimisation parallèle multi-asset (joblib) |
| [crypto_backtest/analysis/cluster_params.py](crypto_backtest/analysis/cluster_params.py) | K-means clustering des paramètres optimaux |
| [crypto_backtest/analysis/diagnostics.py](crypto_backtest/analysis/diagnostics.py) | Diagnostics granulaires + recommandations reopt (6+ checks) |
| [crypto_backtest/validation/conservative_reopt.py](crypto_backtest/validation/conservative_reopt.py) | Configs filtres (BASELINE/MODERATE/CONSERVATIVE) + reopt |
| [scripts/run_full_pipeline.py](scripts/run_full_pipeline.py) | Pipeline complet (download → optimize → cluster) |
| [scripts/portfolio_correlation.py](scripts/portfolio_correlation.py) | Analyse corrélations et drawdowns concurrents |
| [tests/compare_signals.py](tests/compare_signals.py) | Pine vs Python signal validation |
| [outputs/pine_plan_fullguards.csv](outputs/pine_plan_fullguards.csv) | Plan Pine pour assets validés (full guards) |

---

## Estimation de Complexité

- **Indicateurs**: ~600 lignes (MAMA/Hilbert + 5in1 complet)
- **Stratégie**: ~250 lignes (Puzzle + Grace logic)
- **Backtest engine**: ~350 lignes (Multi-TP + trailing)
- **Optimization**: ~400 lignes (Walk-forward + Bayesian)
- **Total**: ~1600 lignes de code Python (COMPLÉTÉ)
