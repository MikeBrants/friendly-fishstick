# PBO CSCV Integration Guide

## Quick Start

### 1. Replace existing pbo.py

```bash
# Backup current implementation
cp crypto_backtest/validation/pbo.py crypto_backtest/validation/pbo_legacy.py

# Copy new implementation
cp pbo_cscv.py crypto_backtest/validation/pbo_cscv.py
```

### 2. Update guard imports

In `crypto_backtest/validation/guards.py` (or wherever guards are called):

```python
# OLD
from crypto_backtest.validation.pbo import guard_pbo

# NEW
from crypto_backtest.validation.pbo_cscv import guard_pbo_cscv as guard_pbo
```

### 3. Run analysis on existing data

```bash
# You already have returns matrices saved!
python pbo_cscv.py outputs/returns_matrix_ETH_run123.npy --full --plot outputs/pbo_eth.png
```

---

## Usage Examples

### Basic CSCV PBO

```python
import numpy as np
from crypto_backtest.validation.pbo_cscv import cscv_pbo

# Load your existing returns matrix
returns = np.load("outputs/returns_matrix_ETH_run123.npy")
print(f"Shape: {returns.shape}")  # (n_trials, n_bars)

# Run CSCV
result = cscv_pbo(returns, n_folds=16, purge_gap=24)

print(f"PBO: {result['pbo']:.3f}")        # 0.423
print(f"Pass: {result['pass']}")           # True (if < 0.50)
print(f"λ median: {result['lambda_median']:.3f}")
print(f"Degradation: {result['degradation']:.2f}x")
```

### Full Analysis (PBO + DSR)

```python
from crypto_backtest.validation.pbo_cscv import full_overfitting_analysis

result = full_overfitting_analysis(returns)

print(f"PBO: {result['pbo']['pbo']:.3f} → {'PASS' if result['pbo']['pass'] else 'FAIL'}")
print(f"DSR: {result['dsr']['dsr']:.3f} (p={result['dsr']['dsr_pvalue']:.4f})")
print(f"Risk Level: {result['risk_level']}")  # LOW / MEDIUM / HIGH
print(f"Combined: {'PASS' if result['combined_pass'] else 'FAIL'}")
```

### Integration with Guards

```python
from crypto_backtest.validation.pbo_cscv import guard_pbo_cscv

# Drop-in replacement for existing guard_pbo
def run_guard_8_pbo(returns_matrix):
    result = guard_pbo_cscv(returns_matrix, n_splits=16, threshold=0.50)
    
    return {
        "guard_id": "GUARD-008",
        "name": "PBO (CSCV)",
        "pass": result["pass"],
        "value": result["pbo"],
        "threshold": 0.50,
        "method": result["method"],  # "CSCV"
    }
```

---

## Key Differences from Old Implementation

| Aspect | Old (`guard_pbo`) | New (`cscv_pbo`) |
|--------|-------------------|------------------|
| Method | Trial pairs | Symmetric data partitions |
| What's tested | "Which trial wins?" | "Does best IS trial perform OOS?" |
| Folds | None (uses trials as splits) | 16 folds of actual data |
| Paths | C(n_trials, 2) | C(16, 8) = 12,870 |
| Leakage prevention | None | Purge gap (24 bars) |
| Output | Single PBO score | PBO + λ distribution + degradation |

---

## CLI Commands

```bash
# Basic analysis
python pbo_cscv.py outputs/returns_matrix_ETH_run123.npy

# With plot
python pbo_cscv.py outputs/returns_matrix_ETH_run123.npy --plot outputs/pbo_eth.png

# Full analysis (includes DSR)
python pbo_cscv.py outputs/returns_matrix_ETH_run123.npy --full

# Custom configuration
python pbo_cscv.py outputs/returns_matrix_ETH_run123.npy \
    --folds 16 \
    --purge 48 \
    --threshold 0.45 \
    --output outputs/pbo_result_eth.json
```

---

## Interpreting Results

### PBO Score
- **< 0.30**: Low overfitting risk ✅
- **0.30 - 0.50**: Moderate risk ⚠️
- **> 0.50**: High overfitting risk ❌

### λ (Lambda) Distribution
- **λ > 0.5**: Best IS trial ranked above median OOS (good)
- **λ < 0.5**: Best IS trial ranked below median OOS (overfit)
- **Median λ near 0.5**: Random performance
- **Median λ > 0.7**: Strong evidence of real edge

### Degradation Ratio
- **~1.0**: OOS matches IS (ideal)
- **0.5 - 0.8**: Typical degradation
- **< 0.5**: Severe overfitting

### DSR (Deflated Sharpe Ratio)
- **DSR > 0 with p < 0.05**: Significant edge after haircut
- **DSR < 0**: Expected max Sharpe exceeds observed (overfit)
- **Haircut**: How much Sharpe was "lost" to multiple testing

---

## Batch Analysis Script

```python
"""Run CSCV on all saved returns matrices."""

import glob
import json
from pathlib import Path
import numpy as np
from crypto_backtest.validation.pbo_cscv import full_overfitting_analysis

results = []

for filepath in glob.glob("outputs/returns_matrix_*.npy"):
    asset = Path(filepath).stem.split("_")[2]  # Extract asset name
    
    returns = np.load(filepath)
    result = full_overfitting_analysis(returns)
    
    results.append({
        "asset": asset,
        "pbo": result["pbo"]["pbo"],
        "pbo_pass": result["pbo"]["pass"],
        "dsr": result["dsr"]["dsr"],
        "dsr_pass": result["dsr"]["pass"],
        "risk_level": result["risk_level"],
        "combined_pass": result["combined_pass"],
    })
    
    print(f"{asset}: PBO={result['pbo']['pbo']:.3f} | "
          f"DSR={result['dsr']['dsr']:.3f} | "
          f"Risk={result['risk_level']}")

# Save summary
with open("outputs/pbo_cscv_summary.json", "w") as f:
    json.dump(results, f, indent=2)
```

---

## Expected Output Format

```json
{
  "pbo": 0.423,
  "pass": true,
  "lambda_distribution": [0.65, 0.72, 0.48, ...],
  "lambda_median": 0.61,
  "lambda_mean": 0.58,
  "n_paths": 12870,
  "n_trials": 200,
  "n_bars": 35040,
  "degradation": 0.72,
  "details": {
    "n_folds": 16,
    "purge_gap": 24,
    "threshold": 0.50,
    "lambda_std": 0.18,
    "lambda_q25": 0.45,
    "lambda_q75": 0.73
  }
}
```

---

## Streamlit Dashboard Integration

Add to your existing Guards page:

```python
# In pages/guards.py or similar

import streamlit as st
from crypto_backtest.validation.pbo_cscv import cscv_pbo, plot_lambda_distribution

st.subheader("🎯 PBO Analysis (True CSCV)")

if st.button("Run CSCV PBO"):
    returns_matrix = load_returns_matrix(selected_asset, run_id)
    
    with st.spinner("Running CSCV (12,870 paths)..."):
        result = cscv_pbo(returns_matrix)
    
    col1, col2, col3 = st.columns(3)
    col1.metric("PBO Score", f"{result['pbo']:.3f}", 
                delta="PASS" if result['pass'] else "FAIL",
                delta_color="normal" if result['pass'] else "inverse")
    col2.metric("λ Median", f"{result['lambda_median']:.3f}")
    col3.metric("Degradation", f"{result['degradation']:.2f}x")
    
    # Plot
    fig = plot_lambda_distribution(result)
    st.pyplot(fig)
```
