# FINAL TRIGGER v2 — Quant Trading System

**Last Updated**: 25 janvier 2026, 17:00 UTC
**Version**: 2.1 (Post-Audit)

---

## ⚠️ CRITICAL AUDIT FINDINGS (25 Jan 2026)

### WFE > 1.0 — Statistical Anomaly Detected

An external quant audit identified a **major concern**: 7 assets show WFE > 1.0

| Asset | WFE | Issue |
|-------|-----|-------|
| SHIB | **2.27** | OOS 2.27× better than IS |
| DOT | **1.74** | Statistically improbable |
| NEAR | **1.69** | Statistically improbable |
| DOGE | **1.55** | Statistically improbable |
| TIA | **1.36** | Statistically improbable |
| ETH | **1.22** | Statistically improbable |
| MINA | **1.13** | Borderline |

**WFE > 1.0 means OOS performs BETTER than IS** — this is statistically quasi-impossible without:
1. Period effect (OOS = bull market)
2. Survivorship bias
3. Data leakage (ruled out by audit)
4. Calculation error (ruled out by audit)

**Status**: INVESTIGATION REQUIRED before any production deployment

### Audit Results
- ✅ WFE formula: CORRECT (`oos_sharpe / is_sharpe`)
- ✅ IS/OOS split: NO OVERLAP
- ✅ Indicator shifts: MOSTLY OK
- ⚠️ Entry at close: OPTIMISTIC (should be next open)
- 🔴 Period effect: HIGHLY PROBABLE (OOS = recent data = potential bull run)

---

## 📁 Project Structure

### Source of Truth
```
status/project-state.md     # ALWAYS READ FIRST — Current state
comms/casey-quant.md        # Task coordination
comms/jordan-dev.md         # Run logs
comms/sam-qa.md             # Guard results
comms/alex-lead.md          # Research tasks (UPDATED 25 Jan)
```

### Rules & Configuration
```
.cursor/rules/MASTER_PLAN.mdc       # Master plan (always loaded)
.cursor/rules/global-quant.mdc      # Quant rules
.cursor/rules/agents/               # Agent-specific rules
config/filter_modes.py              # 3 filter modes
```

### Core Code
```
crypto_backtest/
├── config/
│   ├── asset_config.py             # Production asset configs
│   └── scan_assets.py              # Search spaces, thresholds
├── indicators/
│   ├── ichimoku.py                 # Ichimoku (17 bull / 3 bear Light)
│   ├── five_in_one.py              # 5 combinable filters (KAMA fixed)
│   ├── mama_fama_kama.py           # MESA Adaptive MA
│   └── atr.py                      # ATR for SL/TP
├── strategies/
│   └── final_trigger.py            # Main strategy (Puzzle + Grace)
├── engine/
│   ├── backtest.py                 # Vectorized backtester
│   └── position_manager.py         # Multi-TP (50/30/20) + trailing
├── optimization/
│   └── parallel_optimizer.py       # Optuna + joblib parallel
├── validation/
│   ├── deflated_sharpe.py          # DSR ✅ DONE
│   ├── overfitting.py              # PSR + DSR report
│   ├── pbo.py                      # PBO 🔴 TODO
│   └── cpcv.py                     # CPCV 🔴 TODO
└── analysis/
    ├── metrics.py                  # Sharpe, Sortino, etc.
    └── regime.py                   # Regime analysis
```

### Scripts
```
scripts/
├── run_full_pipeline.py            # Full pipeline (Phase 1-5)
├── run_filter_rescue.py            # Phase 4 filter cascade
├── run_guards_multiasset.py        # 7 guards execution
├── audit_wfe_period_effect.py      # 🔴 TODO — Period effect test
└── portfolio_construction.py       # Portfolio optimization
```

---

## 👥 Multi-Agent System

| Agent | Role | Focus | Comm File |
|-------|------|-------|-----------|
| **Casey** | Orchestrator | Coordination, verdicts, prioritization | `comms/casey-quant.md` |
| **Jordan** | Dev/Backtest | Run execution, code, PRs | `comms/jordan-dev.md` |
| **Sam** | QA/Guards | 7 guards validation, PASS/FAIL | `comms/sam-qa.md` |
| **Alex** | Lead Quant | Research, experiments, new features | `comms/alex-lead.md` |

---

## 🔄 Pipeline (6 Phases)

| Phase | Name | Trials | Guards | Criteria |
|-------|------|--------|--------|----------|
| 0 | Download | - | - | `data/*.parquet` |
| 1 | Screening | 200 | OFF | WFE>0.5, Sharpe>0.8, Trades>50 |
| 2 | Validation | 300 | 7/7 ON | WFE>0.6, Sharpe>1.0, 7/7 PASS |
| 3A | Rescue Disp | 300 | 7/7 ON | d26/d52/d78 displacement variants |
| 3B | Optim Disp | 300 | 7/7 ON | +10% improvement required |
| 4 | Filter Rescue | 300 | 7/7 ON | baseline → moderate → conservative |
| 5 | Production | - | - | `asset_config.py` update |

### Filter System v2 (3 modes)
| Mode | Filters | Trades OOS | WFE |
|------|---------|------------|-----|
| `baseline` | ichimoku only | ≥60 | ≥0.6 |
| `moderate` | 5 filters | ≥50 | ≥0.6 |
| `conservative` | 7 filters | ≥40 | ≥0.55 |

### Obsolete Modes (DO NOT USE)
- ❌ `medium_distance_volume`
- ❌ `light_*`, `medium_*` variants

---

## 🛡️ Validation Framework

### 7 Guards System
| Guard | Metric | Threshold | Status |
|-------|--------|-----------|--------|
| guard001 | WFE | > 0.6 | ✅ Active |
| guard002 | Sensitivity | < 15% | ✅ Active (was 10%) |
| guard003 | Bootstrap CI | lower > 1.0 | ✅ Active |
| guard004 | Monte Carlo p | < 0.05 | ✅ Active |
| guard005 | Top10 Concentration | < 40% | ✅ Active |
| guard006 | Trades OOS | > 60 | ✅ Active |
| guard007 | Bars IS | > 8000 | ✅ Active |

### Overfitting Detection
| Metric | Status | File |
|--------|--------|------|
| **PSR** (Probabilistic Sharpe) | ✅ DONE | `validation/overfitting.py` |
| **DSR** (Deflated Sharpe) | ✅ DONE | `validation/deflated_sharpe.py` |
| **PBO** (Probability of Backtest Overfitting) | 🔴 TODO | `validation/pbo.py` |
| **CPCV** (Combinatorial Purged CV) | 🔴 TODO | `validation/cpcv.py` |

### DSR Thresholds
| DSR | Verdict |
|-----|---------|
| > 95% | STRONG — Edge significant |
| 85-95% | MARGINAL — Acceptable with other guards |
| < 85% | FAIL — Likely overfitting |

---

## 📊 Current Status (25 Jan 2026)

### Production Assets (14 validated — UNDER REVIEW)
| Rank | Asset | Sharpe | WFE | Mode | Status |
|:----:|-------|--------|-----|------|--------|
| 1 | SHIB | 5.67 | 2.27 | baseline | ⚠️ WFE suspect |
| 2 | TIA | 5.16 | 1.36 | baseline | ⚠️ WFE suspect |
| 3 | DOT | 4.82 | 1.74 | baseline | ⚠️ WFE suspect |
| 4 | NEAR | 4.26 | 1.69 | baseline | ⚠️ WFE suspect |
| 5 | DOGE | 3.88 | 1.55 | baseline | ⚠️ WFE suspect |
| 6 | ANKR | 3.48 | 0.86 | baseline | ✅ OK |
| 7 | ETH | 3.22 | 1.22 | baseline | ⚠️ WFE suspect |
| 8 | JOE | 3.16 | 0.73 | baseline | ✅ OK |
| 9 | YGG | 3.11 | 0.78 | baseline | ✅ OK |
| 10 | MINA | 2.58 | 1.13 | baseline | ⚠️ WFE suspect |
| 11 | CAKE | 2.46 | 0.81 | baseline | ✅ OK |
| 12 | RUNE | 2.42 | 0.61 | baseline | ✅ OK |
| 13 | EGLD | 2.13 | 0.69 | baseline | ✅ OK |
| 14 | AVAX | 2.00 | 0.66 | moderate | ✅ OK |

### Pending Rescue
- OSMO, AR, METIS — baseline failed, need Phase 3A

### Excluded
- OP: Sharpe 0.03, WFE 0.01 — severe fail

---

## 🔴 Priority Tasks (Post-Audit)

### BLOCKING — Must Complete Before Production

| # | Task | Owner | Effort | Status |
|---|------|-------|--------|--------|
| 0 | **Audit WFE Period Effect** | Alex | 1-2h | 🔴 TODO |
| 1 | **Implement PBO** | Alex | 3-4h | 🔴 TODO |
| 2 | **Implement CPCV** | Alex | 2-3h | 🟡 TODO |

### Normal Priority
| # | Task | Owner | Status |
|---|------|-------|--------|
| 3 | Phase 3A Rescue (OSMO, AR, METIS) | Jordan | ⏸️ HOLD |
| 4 | Variance Reduction Research | Alex | 🟡 DEPRIORITIZED |
| 5 | GitHub Repos Analysis | Alex | 🟡 TODO |

---

## 🧪 Critical Fixes Applied

### Reproducibility Fix (24 Jan 2026)
**Problem**: Optuna with workers > 1 was non-deterministic
**Solution**:
- Hashlib-based deterministic seeds per asset
- Explicit reseeding before each optimization
- `constant_liar=True` for parallel safety

```python
# crypto_backtest/optimization/parallel_optimizer.py
import hashlib
asset_hash = int(hashlib.md5(asset.encode()).hexdigest(), 16) % 10000
unique_seed = SEED + asset_hash
```

### KAMA Bug Fix (24 Jan 2026)
**Problem**: KAMA oscillator formula was wrong vs Pine Script
**File**: `crypto_backtest/indicators/five_in_one.py`
**Impact**: Modes using KAMA must be retested

### Guard002 Threshold (25 Jan 2026)
**Change**: Sensitivity threshold 10% → 15%
**Rationale**: 18% of assets were false positives
**Impact**: TIA, CAKE reclassified as PASS

---

## 📚 References

### Papers
- Bailey & López de Prado (2014) — "The Deflated Sharpe Ratio"
- Bailey et al. (2015) — "The Probability of Backtest Overfitting"
- Bailey & López de Prado (2012) — "The Sharpe Ratio Efficient Frontier"

### External Repos
| Repo | Focus | Priority |
|------|-------|----------|
| `hudson-and-thames/mlfinlab` | PBO, CPCV, DSR | 🔴 HIGH |
| `stefan-jansen/machine-learning-for-trading` | Walk-forward CV | 🔴 HIGH |
| `polakowo/vectorbt` | Vectorized backtesting | 🟡 MEDIUM |
| `freqtrade/freqtrade` | Crypto strategies | 🟡 MEDIUM |

### Book
- "Advances in Financial Machine Learning" — Marcos López de Prado
  - Chapter 11: The Dangers of Backtesting
  - Chapter 12: Backtesting through Cross-Validation

---

## 🖥️ Commands

### Validation (workers=1 REQUIRED)
```bash
python scripts/run_full_pipeline.py --assets ETH \
  --optimization-mode baseline \
  --trials-atr 300 --trials-ichi 300 \
  --run-guards --workers 1
```

### Phase 3A Displacement Rescue
```bash
python scripts/run_full_pipeline.py --assets ASSET \
  --fixed-displacement 26 \
  --trials-atr 300 --trials-ichi 300 \
  --run-guards --workers 1
```

### Phase 4 Filter Rescue
```bash
python scripts/run_filter_rescue.py ASSET --trials 300 --workers 1
```

### Phase 1 Screening (parallel OK)
```bash
python scripts/run_full_pipeline.py --assets ASSET_LIST \
  --workers 6 --trials-atr 100 --trials-ichi 100 --skip-guards
```

### Dashboard
```bash
streamlit run app.py
```

### Tests
```bash
pytest -v
```

---

## ⚠️ Critical Rules

### Look-Ahead Bias Prevention
- ALWAYS use `.shift(1)` on rolling features used for entry decisions
- Entry price should be `next_open`, not `current_close`
- Regime classification must use ENTRY time, not exit

### Suspicious Results
- Sharpe > 4 = SUSPECT → reconciliation required
- WFE > 2 = SUSPECT → audit period effect
- TP constraint: tp1 < tp2 < tp3 ALWAYS

### Live Degradation Expectations
- Sharpe: ×0.5-0.7 vs backtest
- MaxDD: ×2-3 vs backtest

### DO NOT
- Filter SIDEWAYS regime (79.5% of profit historically)
- Use obsolete filter modes (`medium_distance_volume`, etc.)
- Declare assets "PROD ready" without PBO validation
- Trust WFE > 1.0 without investigation

---

## 🏗️ Architecture Summary

```
┌─────────────────────────────────────────────────────────────┐
│                    FINAL TRIGGER v2                         │
├─────────────────────────────────────────────────────────────┤
│  Data Layer                                                 │
│  └── CCXT fetcher → Parquet cache → Preprocessor           │
├─────────────────────────────────────────────────────────────┤
│  Indicators                                                 │
│  ├── MAMA/FAMA/KAMA (MESA Adaptive)                        │
│  ├── Ichimoku (17 bull / 3 bear Light)                     │
│  ├── Five-in-One (5 combinable filters)                    │
│  └── ATR (SL/TP calculation)                               │
├─────────────────────────────────────────────────────────────┤
│  Strategy                                                   │
│  └── FinalTriggerStrategy (Puzzle + Grace logic)           │
├─────────────────────────────────────────────────────────────┤
│  Engine                                                     │
│  ├── VectorizedBacktester                                  │
│  └── MultiTPPositionManager (50/30/20 + trailing)          │
├─────────────────────────────────────────────────────────────┤
│  Optimization                                               │
│  ├── Bayesian (Optuna TPE)                                 │
│  └── Walk-Forward (60/20/20 split)                         │
├─────────────────────────────────────────────────────────────┤
│  Validation                                                 │
│  ├── 7 Guards (WFE, MC, Sensitivity, Bootstrap, etc.)      │
│  ├── DSR (Deflated Sharpe) ✅                              │
│  ├── PBO (Probability Backtest Overfitting) 🔴 TODO        │
│  └── CPCV (Combinatorial Purged CV) 🔴 TODO                │
└─────────────────────────────────────────────────────────────┘
```

---

## 📝 Changelog

### 25 Jan 2026 — Post-Audit Update
- Added WFE > 1.0 audit findings
- Reprioritized Alex tasks (PBO, CPCV, period effect audit)
- Updated validation framework section
- Added critical rules section
- Marked 7 assets as WFE suspect

### 25 Jan 2026 — Reset Complete
- 14 assets validated with deterministic system
- Filter System v2 deployed (3 modes)
- Guard002 threshold updated (10% → 15%)

### 24 Jan 2026 — Reproducibility Fix
- Hashlib deterministic seeds
- KAMA oscillator bug fixed
- DSR implementation complete

---

*This document is the technical reference for the FINAL TRIGGER v2 system.*
*For current operational status, see `status/project-state.md`*
