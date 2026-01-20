# FINAL TRIGGER v2 — Backtest System

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Status](https://img.shields.io/badge/status-Phase%202%20Complete-green.svg)](docs/HANDOFF.md)
[![Sharpe](https://img.shields.io/badge/Sharpe-2.13-brightgreen.svg)](instructions.md)

> Système de backtest professionnel pour **FINAL TRIGGER v2** — Implémentation Python de l'indicateur TradingView avec walk-forward analysis et optimisation bayésienne.

---

## 📈 Résultats Actuels (Phase 2 Complétée)

| Métrique | Baseline | Current | Δ |
|----------|----------|---------|---|
| **Return** | -6.44% | **+15.69%** | +22.13pp |
| **Sharpe** | -0.80 | **2.13** | +2.93 |
| **Max DD** | -9.2% | **-2.85%** | +6.35pp |
| **Win Rate** | 33.6% | **43.51%** | +9.9pp |
| **Profit Factor** | 0.86 | **1.54** | +0.68 |
| **Trades** | - | 416 | - |
| **Expectancy** | - | +$3.77/trade | - |
| **Recovery Factor** | - | 5.50 | - |

---

## 🎯 Objectif

Convertir l'indicateur TradingView "FINAL TRIGGER v2 - State/Transition + A/D Line + Ichi Light" (1223 lignes Pine Script) en Python avec :
- Backtest vectorisé haute performance
- Walk-forward analysis
- Optimisation bayésienne (Optuna)
- Validation Pine vs Python

---

## ⚙️ Configuration Active (Default)

> **IMPORTANT**: Seuls 2 filtres sont actifs dans la configuration par défaut.

| Paramètre | Valeur | Description |
|-----------|--------|-------------|
| `use_ichimoku_filter` | **TRUE** | Ichimoku Externe (17 bull / 3 bear Light) |
| `use_5in1_ichi_light` | **TRUE** | Ichi Light dans le 5-in-1 Filter |
| `use_mama_kama_filter` | FALSE | MAMA/FAMA/KAMA désactivé |
| `use_transition_mode` | FALSE | Mode transition désactivé |
| Autres filtres 5in1 | FALSE | Distance, Volume, AD Line, Regression, KAMA Osc |

### Paramètres Optimaux (Phase 2)

```yaml
ATR:
  sl_atr_mult: 3.75
  tp_atr_mult: 3.75
  trailing_start: 9.0
  trailing_step: 7.0

Ichimoku General:
  tenkan: 13
  kijun: 34
  displacement: 52

Ichimoku 5in1:
  tenkan_5: 12
  kijun_5: 21
  displacement_5: 52
```

### Pipeline de Signaux

```
Ichimoku External (17/3) → ichi_long_active / ichi_short_active
        ↓
Ichi Light (5in1) → allBull / allBear → bullish_signal / bearish_signal  
        ↓
Puzzle + Grace → trigger_long = (bullish_signal AND ichi_long_active) OR pending_grace
        ↓
ATR → SL / TP1 / TP2 / TP3
```

---

## 📊 Composants Implémentés

| Composant | Status | Description |
|-----------|--------|-------------|
| **Ichimoku Externe** | ✅ Actif | State machine biais directionnel (13/34) |
| **Ichi Light (5in1)** | ✅ Actif | Filtre Ichimoku simplifié (12/21) |
| **Puzzle + Grace** | ✅ Implémenté | Validation avec fenêtre 1 bar |
| **ATR Multi-TP** | ✅ Implémenté | SL + 3 TP (50%/30%/20%) + trailing |
| MAMA/FAMA/KAMA | ⚪ Inactif | Disponible mais désactivé |
| Autres 5in1 | ⚪ Inactif | Distance, Volume, AD, Regression, KAMA Osc |

---

## 🏗️ Structure du Projet

```
crypto_backtest/
├── config/settings.py          # Paramètres globaux
├── data/
│   ├── fetcher.py              # CCXT multi-exchange
│   ├── storage.py              # Cache Parquet
│   └── preprocessor.py         # Nettoyage données
├── indicators/
│   ├── ichimoku.py             # Ichimoku (13/34) ✅ ACTIF
│   ├── five_in_one.py          # Ichi Light (12/21) ✅ ACTIF
│   └── mama_fama_kama.py       # MESA Adaptive MA (inactif)
├── strategies/
│   └── final_trigger.py        # Logique principale
└── engine/
    ├── backtest.py             # Moteur vectorisé
    └── position_manager.py     # Multi-TP + trailing SL
```

---

## ⚡ Quick Start

### Installation

```bash
pip install -r requirements.txt
```

### Lancer un backtest

```bash
python backtest_optimized.py
```

### Optimisation

```bash
python optimize_ichimoku.py
```

---

## 🚀 Phases du Projet

| Phase | Status | Description |
|-------|--------|-------------|
| Phase 1 | ✅ | ATR TP/SL Optimization (Sharpe: 1.43) |
| Phase 2 | ✅ | Ichimoku Optimization (Sharpe: 2.13) |
| Phase 3 | 🔴 P0 | Walk-Forward OOS Validation |
| Phase 4 | 🔴 P0 | Sensitivity Analysis |
| Phase 5 | 🟠 P1 | Multi-Timeframe Validation |
| Phase 6 | 🟡 P2 | Displacement Optimization |

---

## 📚 Documentation

- **[instructions.md](instructions.md)** — Prompt Agent Comet + instructions GPT Codex
- **[claude.md](claude.md)** — Plan détaillé et spécifications techniques
- **[docs/HANDOFF.md](docs/HANDOFF.md)** — Documentation technique complète

---

## 🧪 Tests

```bash
pytest -v
```

---

## 📄 License

MIT