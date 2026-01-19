# friendly-fishstick

Backtest system for **FINAL TRIGGER v2** — Python implementation of the TradingView indicator.

---

## 🎯 Simplified Logic (Default Config)

With the default configuration (`use_mama_kama_filter=False`, `use_ichimoku_filter=True`, all other 5in1 filters OFF, `use_transition_mode=False`), the signal pipeline is:

| Step | Component | Role |
|------|-----------|------|
| 1 | **Ichimoku External** | State machine → `ichi_long_active` / `ichi_short_active` |
| 2 | **5in1 (Ichi Light only)** | `allBull` / `allBear` in state mode → `bullish_signal` / `bearish_signal` |
| 3 | **Puzzle + Grace** | `trigger_long` = (5in1 bull AND ichi_long_active) OR pending_grace |
| 4 | **ATR** | Generates SL / TP1 / TP2 / TP3 on entry |

**Result:** Entry signals (`FINAL LONG` / `FINAL SHORT`) match 100% with Pine Script export after warmup.

---

## 🚀 Quick Start

### 1. Run a Backtest

```bash
python crypto_backtest/examples/run_backtest.py
```

Or in Python:

```python
import pandas as pd
from crypto_backtest.strategies.final_trigger import FinalTriggerStrategy, FinalTriggerParams
from crypto_backtest.engine.backtest import BacktestEngine

# Load your OHLCV data
data = pd.read_csv("data/BYBIT_BTCUSDT-60.csv")
data = data[["open", "high", "low", "close"]].copy()
data["volume"] = 0.0  # if missing

# Run backtest
strategy = FinalTriggerStrategy(FinalTriggerParams())
engine = BacktestEngine(strategy)
results = engine.run(data)
```

### 2. Validate Signals vs Pine

```bash
python tests/compare_signals.py --file data/BYBIT_BTCUSDT-60.csv --warmup 150
```

Expected output:
```
FINAL LONG match: 100.0%
FINAL SHORT match: 100.0%
```

### 3. Run Optimization

```bash
python crypto_backtest/examples/optimize_final_trigger.py
```

---

## ⚙️ Default Configuration (Aligned with Pine)

```python
# FinalTriggerParams defaults
use_mama_kama_filter = False      # Pine: OFF
require_fama_between = False      # Pine: OFF
strict_lock_5in1_last = False     # Pine: OFF
grace_bars = 1                    # Pine: 1

# FiveInOneConfig defaults
use_distance_filter = False       # Pine: OFF
use_volume_filter = False         # Pine: OFF
use_regression_cloud = False      # Pine: OFF
use_kama_oscillator = False       # Pine: OFF
use_ichimoku_filter = True        # Pine: ON ← ONLY ACTIVE FILTER
ichi5in1_strict = False           # Pine: OFF (Light = 3 bear conditions)
use_transition_mode = False       # Pine: OFF (State mode)
```

---

## 📋 Optimization Workflow

1. **Prepare OHLCV data** (CSV/Parquet) with UTC timestamps
2. **Run the demo optimizer:**
   ```bash
   python crypto_backtest/examples/optimize_final_trigger.py
   ```
3. **Customize the param space:**
   - Edit `get_param_space()` in `crypto_backtest/examples/optimize_final_trigger.py`
   - Modes: `quick`, `full`, `toggles`
4. **Validate signals vs Pine** (when CSV export is available):
   ```bash
   python tests/compare_signals.py --file data/your_export.csv --warmup 150
   ```

---

## 📁 Key Files

| File | Description |
|------|-------------|
| `crypto_backtest/strategies/final_trigger.py` | Main strategy (Puzzle + Grace logic) |
| `crypto_backtest/indicators/ichimoku.py` | Ichimoku external (17 bull / 3 bear Light) |
| `crypto_backtest/indicators/five_in_one.py` | 5 combinable filters |
| `crypto_backtest/engine/backtest.py` | Vectorized backtest engine |
| `crypto_backtest/engine/position_manager.py` | Multi-TP (50/30/20) + trailing SL |
| `tests/compare_signals.py` | Pine vs Python signal validation |

---

## 🧪 Tests

```bash
pytest -v
```

---

## 📖 Full Documentation

See [docs/HANDOFF.md](docs/HANDOFF.md) for complete technical documentation, known issues, and next steps.
