# FINAL TRIGGER v2 — Backtest System

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Status](https://img.shields.io/badge/status-82%25%20complete-green.svg)](docs/HANDOFF.md)

> Système de backtest professionnel pour **FINAL TRIGGER v2** — Implémentation Python de l'indicateur TradingView avec walk-forward analysis et optimisation bayésienne.

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

### Pipeline de Signaux Simplifié

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
| **Ichimoku Externe** | ✅ Actif | State machine biais directionnel |
| **Ichi Light (5in1)** | ✅ Actif | Filtre Ichimoku simplifié |
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
│   ├── ichimoku.py             # Ichimoku (17 bull + 3 bear) ✅ ACTIF
│   ├── five_in_one.py          # Ichi Light uniquement ✅ ACTIF
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

### Optimisation (10 trials)

```bash
python crypto_backtest/examples/optimize_final_trigger.py --trials 10
```

### Valider signaux Pine vs Python

```bash
python tests/compare_signals.py --file data/your_export.csv --warmup 150
```

---

## 📁 Fichiers Clés

| Fichier | Description |
|---------|-------------|
| `crypto_backtest/strategies/final_trigger.py` | Stratégie principale (Puzzle + Grace) |
| `crypto_backtest/indicators/ichimoku.py` | Ichimoku externe (17 bull / 3 bear) |
| `crypto_backtest/indicators/five_in_one.py` | Ichi Light (seul filtre 5in1 actif) |
| `crypto_backtest/engine/backtest.py` | Moteur de backtest vectorisé |
| `crypto_backtest/engine/position_manager.py` | Multi-TP (50/30/20) + trailing SL |
| `tests/compare_signals.py` | Validation Pine vs Python |

---

## 🧪 Tests

```bash
pytest -v
```

---

## 📚 Documentation

- **[claude.md](claude.md)** — Plan détaillé et spécifications techniques
- **[docs/HANDOFF.md](docs/HANDOFF.md)** — Documentation technique complète, issues connues et prochaines étapes

---

## 🚀 Next Steps

1. ✅ Exporter CSV TradingView avec 2000+ bougies et signaux Pine
2. ⏳ Lancer `compare_signals.py` et vérifier 100% match après warmup
3. ⏳ Créer test E2E validant signaux sur données réelles
4. ⏳ Walk-forward analysis complète

---

## 📄 License

MIT