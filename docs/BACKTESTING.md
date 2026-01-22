# Backtesting Dossier - FINAL TRIGGER v2

This file is the single source of truth for all backtesting results, issues, and next steps.
`docs/HANDOFF.md` stays short and links here.

## Scope
- Multi-asset scans, displacement grids, and full pipeline runs
- Guard results and anomaly investigations
- Issues, challenges, and analysis notes
- Next steps and recommended reruns

## Current status snapshot (2026-01-22)
- ETH revalidation (disp=52, TP enforced): SUCCESS (OOS Sharpe 3.87, WFE 2.36) but guard002 variance 12.96% -> guards fail
- AVAX/UNI revalidation (disp=52): FAIL (WFE < 0.6)
- SEI revalidation (disp=52): FAIL (OOS Sharpe < 1.0, WFE < 0.6)
- CAKE revalidation (disp=26): SUCCESS (OOS Sharpe 2.73, WFE 0.73) but guard002 variance 20.70% -> guards fail
- Legacy snapshot (2026-01-21): production validated (scan) BTC/ETH/XRP/AVAX/UNI/SUI/SEI; production validated (full guards) BTC/ETH/AVAX/UNI/SEI (SUI excluded); 13 assets guards PASS=AR/EGLD/CELO/ANKR; anomaly check for HOOK/ALICE/HMSTR (trades < 60 and/or data < 10000 bars)

Key outputs (2026-01-22):
- `outputs/multiasset_scan_20260122_1319.csv` (CAKE disp=26)
- `outputs/multiasset_guards_summary_20260122_131934.csv` (CAKE guards)
- `outputs/multiasset_scan_20260122_1322.csv` (ETH/AVAX/UNI/SEI)
- `outputs/multiasset_guards_summary_20260122_132234.csv` (ETH/AVAX/UNI/SEI guards)

## Pipeline status (2026-01-22)

| Batch | Assets | Status |
|:------|:-------|:-------|
| Displacement d26 | JOE, CAKE | JOE PASS (pre-fix); CAKE SUCCESS but guards fail (variance 20.70%) |
| Displacement d65 | OSMO | PASS (57 trades accepted) |
| Displacement d78 | MINA, RUNE, TON | MINA PASS; RUNE/TON FAIL |
| Displacement d39 | AXS | FAIL (excluded) |
| Core P0 | ETH, AVAX, UNI, SEI | RUN DONE: ETH SUCCESS but guards fail (variance 12.96%); AVAX/UNI WFE<0.6; SEI OOS Sharpe<1.0 |
| Winners P1.1 | DOT, SHIB, NEAR | Pending after core re-opt |
| Disp P1.2 | OP, DOGE | Pending after core re-opt |
| Guard-passed P1.3 | AR, EGLD, CELO, ANKR | Pending after P1.1/P1.2 |

Filter grid (ETH): DONE. Best mode = medium_distance_volume (all_pass True, sens_var 3.95%, OOS Sharpe 2.09, WFE 0.82, trades 57). Outputs: `outputs/filter_grid_results_ETH_20260122_1917.csv`, `outputs/filter_grid_summary_ETH_20260122_1917.csv`.

Key outputs (2026-01-21):
- `outputs/multiasset_guards_summary_20260121_201821.csv`
- `outputs/anomaly_investigation_20260121_205300.csv`

## Recent runs and outputs

### Revalidation reruns (TP enforcement, 2026-01-22)
- CAKE disp=26: SUCCESS (OOS Sharpe 2.73, WFE 0.73) but guards fail on variance (20.70%).
  Outputs: `outputs/multiasset_scan_20260122_1319.csv`, `outputs/multiasset_guards_summary_20260122_131934.csv`
- ETH/AVAX/UNI/SEI disp=52: ETH SUCCESS (OOS Sharpe 3.87, WFE 2.36) but guard002 variance 12.96%; AVAX/UNI WFE < 0.6; SEI OOS Sharpe < 1.0 and WFE < 0.6.
  Outputs: `outputs/multiasset_scan_20260122_1322.csv`, `outputs/multiasset_guards_summary_20260122_132234.csv`

### Top 50 (two batches, excluding BTC/ETH/AVAX/UNI/SEI)
- PASS: DOT, SHIB, NEAR, SUI, APT
- FAIL: SOL, XRP, BNB, ADA, DOGE, LINK, MATIC, LTC, ATOM, XLM, FIL, ARB, OP, INJ, RENDER, FET, TAO, PEPE, WIF, BONK, AAVE, MKR, CRV, SNX, SAND
Outputs:
- `outputs/multiasset_scan_20260121_1619.csv`
- `outputs/multiasset_scan_20260121_1626.csv`

### OP displacement
- Full run disp=78: OOS Sharpe 2.48, WFE 1.66, trades 90
- Guards: all pass (p=0.0000, sens var=5.34%, CI lower=2.01, stress1 sharpe=1.73)
Outputs:
- `outputs/displacement_grid_OP_20260121_173045.csv`
- `outputs/op_fullrun_disp78_20260121_174550.csv`
- `outputs/multiasset_guards_summary_20260121_175759.csv`

### Displacement grid (near-threshold FAIL set)
Results summary:
- SOL best=52 (no gain)
- DOGE best=26 (+2.18 Sharpe vs 52)
- LINK best=39 (+1.36 Sharpe vs 52)
Output: `outputs/displacement_grid_summary_20260121_175713.csv`

### Displacement grid batch3 (run 20260121_210728)
Best displacement by asset:
- AXS=39, CAKE=26, JOE=26, KSM=26, MINA=78, OSMO=65, RUNE=78, TON=78
Output:
- `outputs/displacement_grid_batch3_20260121_210728.csv`
- `outputs/displacement_grid_batch3_summary_20260121_210728.csv`

### Full runs with fixed displacement (latest)
- `outputs/multiasset_scan_20260121_2111.csv` (disp=26): CAKE PASS, JOE PASS, KSM FAIL (WFE 0.57)
- `outputs/multiasset_scan_20260121_2130.csv` (disp=39): AXS PASS
- Guards:
  - `outputs/multiasset_guards_summary_20260121_211152.csv` (CAKE/JOE/KSM)
  - `outputs/multiasset_guards_summary_20260121_213038.csv` (AXS)

## TP progression audit and enforcement
- Audit run across CSV outputs found 519 TP progression errors
  - Summary: `outputs/tp_progression_errors_summary_20260121_215436.csv`
  - Full list: `outputs/tp_progression_errors_20260121_215436.csv`
- Enforcement is now default-on in:
  - `crypto_backtest/optimization/parallel_optimizer.py`
  - `scripts/run_full_pipeline.py`
  - `scripts/run_displacement_grid.py`
- Override: `--no-enforce-tp-progression`
- Note: Older outputs (ex: `outputs/multiasset_scan_20260121_2111.csv`, `outputs/multiasset_scan_20260121_2130.csv`) include non-progressive TP ladders and should be rerun.

## Optimization mode defaults (baseline vs moderate)
Policy:
- Baseline is the default for initial runs.
- Moderate is the default choice when you decide to re-optimize (non-baseline).
- Conservative is a last-resort option for severe overfit.

MODERATE filter config (default for re-optimization choice):
- use_mama_kama_filter: OFF
- use_distance_filter: ON
- use_volume_filter: ON (A/D Line or OBV)
- use_regression_cloud: ON
- use_kama_oscillator: ON
- use_ichimoku_filter: ON (external Ichimoku bias)
- ichi5in1_strict: OFF (Light mode, 3 bearish conditions)
- use_transition_mode: OFF (State mode)

Baseline is used unless you explicitly select moderate or conservative:
- `--optimization-mode moderate`
- `--optimization-mode conservative`

## Issues and challenges
- Guard errors (complex numbers): YGG, ARKM, STRK, METIS, AEVO in `outputs/multiasset_guards_summary_20260121_201821.csv`.
  Likely from metrics or data anomalies; needs targeted debug.
- Guard002 variance > 10% still blocks CAKE (20.70%) and ETH (12.96%) after TP enforcement reruns.
- Console encoding: `parallel_optimizer.py` prints unicode arrows/checks; when console is cp1252, it can crash.
  Workaround: run with `chcp 65001` and `PYTHONIOENCODING=utf-8`.
- Output overwrites: Some scans share the same timestamp (ex: `multiasset_scan_20260121_1759.csv` overwritten).
  Use `RunManager` or add higher-resolution timestamps to avoid collisions.
- Data length / trade count issues:
  - LOOM and HMSTR have short history
  - HOOK/ALICE/HMSTR often fail due to trades < 60

## Next steps (recommended)
1. Apply ETH winner mode `medium_distance_volume` to AVAX/UNI, then re-run guards.
2. Re-run ETH/CAKE with `--optimization-mode moderate` (TP enforced) to target guard002 variance < 10%.
3. Re-opt AVAX/UNI/SEI (moderate or conservative) to improve WFE > 0.6.
4. Rerun assets with non-progressive TP outputs using default enforcement:
   - AXS (disp=39), CAKE/KSM (disp=26), any other winners you plan to keep
4. Run full pipelines for displacement winners not yet validated:
   - MINA disp=78, OSMO disp=65, RUNE disp=78, TON disp=78
5. Re-run guards for new winners after updated full runs.
6. Build `outputs/all_validated_assets.csv`, then run portfolio construction + stress test + final report.
7. Investigate guard errors for YGG/ARKM/STRK/METIS/AEVO (data quality or metric bug).

## Codex prompt - full re-validation pipeline (TP progression)
ASCII-only copy/paste prompt for rerunning the full pipeline with TP progression enforcement.

````text
# CODEX PROMPT - FINAL TRIGGER v2 Full Re-Validation Pipeline

```markdown
# CODEX: FINAL TRIGGER v2 - Complete Re-Validation Pipeline

## CRITICAL CONTEXT
Previous scans are INVALID - TP progression constraint (TP1 < TP2 < TP3, gap >= 0.5 ATR) was NOT enforced.
ALL optimization results must be regenerated with `--enforce-tp-progression` flag.

## Environment
- Repo: MikeBrants/friendly-fishstick (local clone)
- Machine: i7-11800H 8c/32GB
- Python: 3.11+ with crypto_backtest package
- Data: data/Binance_*_1h.csv (local, 2 years)

## Pre-Flight Checks
```bash
# 1. Verify TP progression constraint is in code
grep -r "tp1.*tp2.*tp3" crypto_backtest/optimization/bayesian.py

# 2. Check disk space (need ~20GB free)
df -h | grep -E "/$|Avail"

# 3. Verify data files exist for target assets
ls data/Binance_{ICP,HBAR,EGLD,IMX,YGG,CELO,ARKM,AR,ANKR,W,STRK,METIS,AEVO}USDT_1h.* 2>/dev/null | wc -l
```

---

## PHASE 0: Re-Optimize 13 New Assets WITH TP Progression
Duration: ~45min | Workers: 6

Assets: ICP, HBAR, EGLD, IMX, YGG, CELO, ARKM, AR, ANKR, W, STRK, METIS, AEVO

```bash
python scripts/run_full_pipeline.py \
  --assets ICP HBAR EGLD IMX YGG CELO ARKM AR ANKR W STRK METIS AEVO \
  --workers 6 \
  --trials-atr 100 \
  --trials-ichi 100 \
  --enforce-tp-progression \
  --skip-download
```

Validation after Phase 0:
```python
import pandas as pd
from glob import glob

# Load latest scan
scan = pd.read_csv(sorted(glob("outputs/multiasset_scan_*.csv"))[-1])

# CHECK TP PROGRESSION
for _, row in scan.iterrows():
    tp1, tp2, tp3 = row['tp1_mult'], row['tp2_mult'], row['tp3_mult']
    valid = (tp1 < tp2 < tp3) and (tp2 - tp1 >= 0.5) and (tp3 - tp2 >= 0.5)
    status = "OK" if valid else "INVALID"
    print(f"{row['asset']}: TP1={tp1:.2f} < TP2={tp2:.2f} < TP3={tp3:.2f} {status}")

# Summary
print(f"\nPASS: {len(scan[scan['status']=='PASS'])} | FAIL: {len(scan[scan['status']=='FAIL'])}")
```

Export: `outputs/multiasset_scan_YYYYMMDD_HHMM.csv`

---

## PHASE 1: Guards on Re-Optimized Assets
Duration: ~30min | Workers: 6

Run 7 guards on ALL assets that passed Phase 0:

```bash
# Get latest scan file
SCAN_FILE=$(ls -t outputs/multiasset_scan_*.csv | head -1)

# Extract PASS assets
PASS_ASSETS=$(python -c "import pandas as pd; df=pd.read_csv('$SCAN_FILE'); print(' '.join(df[df['status']=='PASS']['asset'].tolist()))")

# Run guards
python scripts/run_guards_multiasset.py \
  --assets $PASS_ASSETS \
  --params-file $SCAN_FILE \
  --workers 6
```

Guard Thresholds:
| Guard | Check | Threshold |
|-------|-------|-----------|
| GUARD-001 | Monte Carlo p-value | < 0.05 |
| GUARD-002 | Sensitivity variance | < 10% |
| GUARD-003 | Bootstrap Sharpe CI lower | > 1.0 |
| GUARD-005 | Top 10 trades concentration | < 40% |
| GUARD-006 | Stress1 (10/5 bps) Sharpe | > 1.0 |
| GUARD-007 | Regime mismatch | < 1% |

Export: `outputs/multiasset_guards_summary_YYYYMMDD_HHMMSS.csv`

---

## PHASE 2: Anomaly Investigation
Duration: ~15min

Investigate assets with suspicious metrics (high Sharpe but marked FAIL):
- HOOK: OOS Sharpe=5.39, WFE=1.52
- ALICE: OOS Sharpe=3.67, WFE=2.01
- HMSTR: OOS Sharpe=2.65, WFE=1.13

```python
import pandas as pd
from glob import glob

scan = pd.read_csv(sorted(glob("outputs/multiasset_scan_*.csv"))[-1])
anomalies = ['HOOK', 'ALICE', 'HMSTR']

print("=" * 70)
print("ANOMALY INVESTIGATION")
print("=" * 70)

for asset in anomalies:
    row = scan[scan['asset'] == asset]
    if row.empty:
        print(f"{asset}: NOT IN SCAN - need to run optimization first")
        continue

    row = row.iloc[0]
    oos_trades = row.get('oos_trades', 0)
    is_sharpe = row.get('is_sharpe', 0)
    oos_sharpe = row.get('oos_sharpe', 0)
    wfe = row.get('wfe', 0)

    # Check data quality
    data_file = f"data/Binance_{asset}USDT_1h.csv"
    try:
        df = pd.read_csv(data_file)
        bars = len(df)
    except:
        bars = 0

    # Diagnose
    issues = []
    if oos_trades < 60:
        issues.append(f"LOW_TRADES ({oos_trades})")
    if bars < 8000:
        issues.append(f"LOW_BARS ({bars})")
    if is_sharpe > 4.0 and wfe > 1.5:
        issues.append("OUTLIER_DEPENDENT (IS Sharpe too high)")
    if oos_sharpe > 4.0:
        issues.append("OOS_OUTLIER (suspiciously high)")

    verdict = "RESCUE" if len(issues) == 0 else "EXCLUDE"
    print(f"{asset}: OOS_Sharpe={oos_sharpe:.2f}, WFE={wfe:.2f}, Trades={oos_trades}, Bars={bars}")
    print(f"  Issues: {issues if issues else 'None'}")
    print(f"  Verdict: {verdict}")
    print()
```

If RESCUE verdict - re-run with guards:
```bash
python scripts/run_guards_multiasset.py \
  --assets HOOK ALICE \
  --params-file outputs/multiasset_scan_YYYYMMDD_HHMM.csv \
  --workers 2
```

---

## PHASE 3: Displacement Grid on Borderline Assets
Duration: ~60min | Workers: 6

Test displacements [26, 39, 52, 65, 78] on WFE borderline assets (0.3 < WFE < 0.6):

```bash
# Identify borderline assets from scan
BORDERLINE=$(python -c "
import pandas as pd
from glob import glob
df = pd.read_csv(sorted(glob('outputs/multiasset_scan_*.csv'))[-1])
borderline = df[(df['wfe'] > 0.3) & (df['wfe'] < 0.6)]['asset'].tolist()
print(' '.join(borderline))
")

echo "Borderline assets: $BORDERLINE"

# Run displacement grid for each
for DISP in 26 39 52 65 78; do
  echo "Testing displacement=$DISP..."
  python scripts/run_full_pipeline.py \
    --assets $BORDERLINE \
    --workers 6 \
    --trials-atr 50 \
    --trials-ichi 50 \
    --enforce-tp-progression \
    --fixed-displacement $DISP \
    --skip-download
done
```

Analyze results:
```python
import pandas as pd
from glob import glob

# Collect all displacement results
results = []
for f in sorted(glob("outputs/multiasset_scan_*.csv"))[-5:]:  # Last 5 scans
    df = pd.read_csv(f)
    results.append(df)

combined = pd.concat(results)
pivot = combined.pivot_table(
    index='asset',
    columns='displacement',
    values=['oos_sharpe', 'wfe'],
    aggfunc='first'
)
print(pivot)

# Find best displacement per asset
for asset in combined['asset'].unique():
    asset_data = combined[combined['asset'] == asset]
    best = asset_data.loc[asset_data['wfe'].idxmax()]
    if best['wfe'] >= 0.6 and best['oos_sharpe'] >= 1.0:
        print(f"OK {asset}: best_disp={best['displacement']}, WFE={best['wfe']:.2f}, Sharpe={best['oos_sharpe']:.2f}")
    else:
        print(f"FAIL {asset}: no valid displacement found")
```

---

## PHASE 4: Full Runs on Displacement Winners
Duration: ~30min | Workers: 6

For assets with optimal displacement != 52:

```bash
# Example: if DOGE best at disp=26, OP best at disp=78
python scripts/run_full_pipeline.py \
  --assets DOGE \
  --workers 6 \
  --trials-atr 100 \
  --trials-ichi 100 \
  --enforce-tp-progression \
  --fixed-displacement 26 \
  --skip-download

python scripts/run_full_pipeline.py \
  --assets OP \
  --workers 6 \
  --trials-atr 100 \
  --trials-ichi 100 \
  --enforce-tp-progression \
  --fixed-displacement 78 \
  --skip-download

# Run guards on winners
python scripts/run_guards_multiasset.py \
  --assets DOGE OP \
  --params-file outputs/multiasset_scan_LATEST.csv \
  --workers 2
```

---

## PHASE 5: Portfolio Construction
Duration: ~10min

```bash
python scripts/portfolio_correlation.py \
  --params-file outputs/pine_plan.csv \
  --min-weight 0.03 \
  --max-weight 0.15
```

Or manually:
```python
import pandas as pd
import numpy as np
from glob import glob

# Load all validated assets
guards = pd.read_csv(sorted(glob("outputs/multiasset_guards_summary_*.csv"))[-1])
validated = guards[guards['all_pass'] == True]['asset'].tolist()

print(f"Validated assets: {validated}")

# Load daily returns
returns = {}
for asset in validated:
    try:
        df = pd.read_csv(f"data/Binance_{asset}USDT_1h.csv", parse_dates=['timestamp'])
        df = df.set_index('timestamp').resample('1D').last()
        returns[asset] = df['close'].pct_change().dropna()
    except Exception as e:
        print(f"Skip {asset}: {e}")

returns_df = pd.DataFrame(returns).dropna()

# Correlation matrix
corr = returns_df.corr()
print("\nCorrelation Matrix:")
print(corr.round(2))

# Flag high correlations
for i in range(len(corr.columns)):
    for j in range(i+1, len(corr.columns)):
        if corr.iloc[i,j] > 0.75:
            print(f"WARNING: High correlation: {corr.columns[i]} - {corr.columns[j]} = {corr.iloc[i,j]:.2f}")

# Save
corr.to_csv("outputs/portfolio_correlation_matrix.csv")

# Equal-weight portfolio metrics
eq_returns = returns_df.mean(axis=1)
sharpe = eq_returns.mean() / eq_returns.std() * np.sqrt(365)
max_dd = (eq_returns.cumsum() - eq_returns.cumsum().cummax()).min()
print(f"\nEqual-Weight Portfolio: Sharpe={sharpe:.2f}, MaxDD={max_dd*100:.2f}%")
```

---

## PHASE 6: Stress Test Portfolio
Duration: ~15min

```python
scenarios = [
    ("Base", 5, 2),
    ("Stress1", 10, 5),
    ("Stress2", 15, 10),
    ("Stress3", 20, 15),
]

# Run backtest for each scenario on portfolio
# (Use existing stress test functions from run_guards_multiasset.py)

results = []
for name, fees, slip in scenarios:
    # Adjust costs and recalculate
    cost_drag = (fees + slip) / 10000 * 2 * 365  # Annual cost drag estimate
    adjusted_sharpe = base_sharpe - cost_drag * 0.5  # Rough approximation
    results.append({
        "scenario": name,
        "fees_bps": fees,
        "slip_bps": slip,
        "portfolio_sharpe": adjusted_sharpe,
        "edge_bps": fees - 5  # Buffer above base
    })

stress_df = pd.DataFrame(results)
stress_df.to_csv("outputs/portfolio_stress_test.csv", index=False)
print(stress_df)
```

---

## PHASE 7: Final Report Generation

```python
from datetime import datetime

# Collect all results
guards = pd.read_csv(sorted(glob("outputs/multiasset_guards_summary_*.csv"))[-1])
scan = pd.read_csv(sorted(glob("outputs/multiasset_scan_*.csv"))[-1])

validated = guards[guards['all_pass'] == True]
failed = guards[guards['all_pass'] == False]

# Generate report
report = f\"\"\"# FINAL TRIGGER v2 - Validation Report
Generated: {datetime.now().isoformat()}

## Executive Summary
- **Total Assets Scanned**: {len(scan)}
- **Assets Validated (7/7 Guards)**: {len(validated)}
- **Assets Failed**: {len(failed)}

## Validated Assets
| Asset | OOS Sharpe | WFE | Displacement | Status |
|-------|------------|-----|--------------|--------|
\"\"\"

for _, row in validated.iterrows():
    asset = row['asset']
    scan_row = scan[scan['asset'] == asset].iloc[0] if asset in scan['asset'].values else {}
    oos_sharpe = scan_row.get('oos_sharpe', 'N/A')
    wfe = scan_row.get('wfe', 'N/A')
    disp = scan_row.get('displacement', 52)
    report += f\"| {asset} | {oos_sharpe:.2f} | {wfe:.2f} | {disp} | PASS |\\n\"

report += f\"\"\"
## Guards Results Summary
| Asset | MC p | Sens % | Boot CI | Top10% | Stress1 | Regime | ALL |
|-------|------|--------|---------|---------|---------|--------|-----|
\"\"\"

for _, row in guards.iterrows():
    report += f\"| {row['asset']} | {row.get('guard001_p_value', 'N/A'):.3f} | {row.get('guard002_variance_pct', 'N/A'):.1f}% | {row.get('guard003_sharpe_ci_lower', 'N/A'):.2f} | {row.get('guard005_top10_pct', 'N/A'):.1f}% | {row.get('guard006_stress1_sharpe', 'N/A'):.2f} | {row.get('guard007_mismatch_pct', 'N/A'):.2f}% | {'PASS' if row['all_pass'] else 'FAIL'} |\\n\"

report += f\"\"\"
## Production Verdict
- Portfolio Sharpe: X.XX {'PASS' if True else 'FAIL'} (>2.0)
- Portfolio MaxDD: X.XX% {'PASS' if True else 'FAIL'} (<8%)
- Stress1 Sharpe: X.XX {'PASS' if True else 'FAIL'} (>1.5)
- Diversification Ratio: X.XX {'PASS' if True else 'FAIL'} (>1.3)

STATUS: PRODUCTION_READY / NOT_READY
\"\"\"

with open("outputs/FINAL_VALIDATION_REPORT.md", "w") as f:
    f.write(report)

print("Report saved to outputs/FINAL_VALIDATION_REPORT.md")
```

---

## Quick Start Command
One-liner to run Phase 0 + Phase 1:

```bash
# Re-optimize with TP progression + run guards
python scripts/run_full_pipeline.py \
  --assets ICP HBAR EGLD IMX YGG CELO ARKM AR ANKR W STRK METIS AEVO \
  --workers 6 --trials-atr 100 --trials-ichi 100 \
  --enforce-tp-progression --skip-download && \
python scripts/run_guards_multiasset.py \
  --assets $(python -c "import pandas as pd; from glob import glob; df=pd.read_csv(sorted(glob('outputs/multiasset_scan_*.csv'))[-1]); print(' '.join(df[df['status']=='PASS']['asset'].tolist()))") \
  --params-file $(ls -t outputs/multiasset_scan_*.csv | head -1) \
  --workers 6
```

## Expected Timeline
| Phase | Duration | Output |
|-------|----------|--------|
| Phase 0 | ~45min | multiasset_scan_*.csv |
| Phase 1 | ~30min | multiasset_guards_summary_*.csv |
| Phase 2 | ~15min | anomaly_investigation.csv |
| Phase 3 | ~60min | displacement_grid_*.csv |
| Phase 4 | ~30min | fullrun_disp_winners.csv |
| Phase 5 | ~10min | portfolio_*.csv |
| Phase 6 | ~15min | portfolio_stress_test.csv |
| Phase 7 | ~5min | FINAL_VALIDATION_REPORT.md |
| TOTAL | ~3.5h | - |
```
````

### Points Critiques a Verifier

| Check | Commande | Attendu |
|-------|----------|---------|
| TP Progression | `grep "tp1_mult < tp2_mult" crypto_backtest/optimization/bayesian.py` | Contrainte presente |
| Gap minimum | `grep "0.5" crypto_backtest/optimization/bayesian.py` | Gap >= 0.5 ATR |
| Fichier scan | `ls -la outputs/multiasset_scan_*.csv` | Fichier recent |
| Data 13 assets | `ls data/Binance_{ICP,HBAR}* | wc -l` | >=13 fichiers |

## Reference outputs
- Guard summaries: `outputs/multiasset_guards_summary_*.csv`
- Scan outputs: `outputs/multiasset_scan_*.csv`, `outputs/multi_asset_scan_*.csv`
- Displacement grids: `outputs/displacement_grid_*`
- Portfolio artifacts: `outputs/portfolio_*.csv`
