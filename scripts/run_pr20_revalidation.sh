#!/bin/bash
# PR#20 Revalidation Script - Pragmatic Plan
# Created: 26 Jan 2026, 23:15 UTC
# Agent: Jordan (Dev)

set -e  # Exit on error

echo "================================================================================"
echo "  PR#20 REVALIDATION - 12 PROD ASSETS + OSMO RESCUE"
echo "================================================================================"
echo ""
echo "Estimated duration: 16-18h"
echo "Start: $(date)"
echo ""

# Create output directory for this run
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
RUN_ID="pr20_${TIMESTAMP}"
mkdir -p "outputs/pr20_logs"
LOG_FILE="outputs/pr20_logs/${RUN_ID}.log"

echo "Logging to: $LOG_FILE"
echo "" | tee -a "$LOG_FILE"

# =============================================================================
# PHASE 1: PROD BATCH REVALIDATION
# =============================================================================

echo "================================================================================" | tee -a "$LOG_FILE"
echo "PHASE 1: PROD REVALIDATION (12 assets)" | tee -a "$LOG_FILE"
echo "================================================================================" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

# --- Batch 1: Top Performers (High WFE) ---
echo "[$(date +%H:%M:%S)] Starting Batch 1: SHIB DOT TIA NEAR" | tee -a "$LOG_FILE"
python scripts/run_full_pipeline.py \
    --assets SHIB DOT TIA NEAR \
    --optimization-mode baseline \
    --trials-atr 300 \
    --trials-ichi 300 \
    --run-guards \
    --workers 1 \
    --output-prefix pr20_batch1 2>&1 | tee -a "$LOG_FILE"

echo "[$(date +%H:%M:%S)] Batch 1 complete" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

# Check Batch 1 results
echo "Analyzing Batch 1 results..." | tee -a "$LOG_FILE"
python -c "
import pandas as pd
import glob

files = glob.glob('outputs/pr20_batch1_*guards_summary*.csv')
if files:
    df = pd.read_csv(sorted(files)[-1])
    passed = df[df.get('all_hard_pass', False) == True]
    print(f'Batch 1: {len(passed)}/4 assets passed hard guards')
    if len(passed) < 3:
        print('⚠️ WARNING: Less than 75% pass rate - consider stopping')
        exit(1)
else:
    print('⚠️ No results found')
    exit(1)
" | tee -a "$LOG_FILE"

if [ $? -ne 0 ]; then
    echo "❌ Batch 1 had issues - stopping" | tee -a "$LOG_FILE"
    exit 1
fi

# --- Batch 2: Mid Performers ---
echo "[$(date +%H:%M:%S)] Starting Batch 2: DOGE ANKR ETH JOE" | tee -a "$LOG_FILE"
python scripts/run_full_pipeline.py \
    --assets DOGE ANKR ETH JOE \
    --optimization-mode baseline \
    --trials-atr 300 \
    --trials-ichi 300 \
    --run-guards \
    --workers 1 \
    --output-prefix pr20_batch2 2>&1 | tee -a "$LOG_FILE"

echo "[$(date +%H:%M:%S)] Batch 2 complete" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

# --- Batch 3: Lower Performers ---
echo "[$(date +%H:%M:%S)] Starting Batch 3: YGG MINA CAKE RUNE" | tee -a "$LOG_FILE"
python scripts/run_full_pipeline.py \
    --assets YGG MINA CAKE RUNE \
    --optimization-mode baseline \
    --trials-atr 300 \
    --trials-ichi 300 \
    --run-guards \
    --workers 1 \
    --output-prefix pr20_batch3 2>&1 | tee -a "$LOG_FILE"

echo "[$(date +%H:%M:%S)] Batch 3 complete" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

# =============================================================================
# PHASE 2: REGIME STRESS TEST
# =============================================================================

echo "================================================================================" | tee -a "$LOG_FILE"
echo "PHASE 2: REGIME STRESS TEST" | tee -a "$LOG_FILE"
echo "================================================================================" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

# Find all assets that passed Phase 1
PHASE1_PASS=$(python -c "
import pandas as pd
import glob

files = glob.glob('outputs/pr20_*_guards_summary_*.csv')
dfs = [pd.read_csv(f) for f in files]
df = pd.concat(dfs) if dfs else pd.DataFrame()

if not df.empty:
    passing = df[df.get('all_hard_pass', False) == True]['asset'].unique()
    print(' '.join(passing))
else:
    print('')
")

if [ -z "$PHASE1_PASS" ]; then
    echo "❌ No assets passed Phase 1 - skipping regime stress test" | tee -a "$LOG_FILE"
    exit 1
fi

echo "[$(date +%H:%M:%S)] Testing regime stress for: $PHASE1_PASS" | tee -a "$LOG_FILE"

python scripts/run_regime_stress_test.py \
    --assets $PHASE1_PASS \
    --regimes SIDEWAYS \
    --output outputs/pr20_regime_stress_${TIMESTAMP}.csv 2>&1 | tee -a "$LOG_FILE"

echo "[$(date +%H:%M:%S)] Regime stress test complete" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

# =============================================================================
# PHASE 3: OSMO RESCUE TEST
# =============================================================================

echo "================================================================================" | tee -a "$LOG_FILE"
echo "PHASE 3: OSMO RESCUE TEST (d26, d78)" | tee -a "$LOG_FILE"
echo "================================================================================" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

for disp in 26 78; do
    echo "[$(date +%H:%M:%S)] Testing OSMO with displacement=$disp" | tee -a "$LOG_FILE"
    python scripts/run_full_pipeline.py \
        --assets OSMO \
        --displacement $disp \
        --trials-atr 300 \
        --trials-ichi 300 \
        --run-guards \
        --workers 1 \
        --output-prefix pr20_osmo_d${disp} 2>&1 | tee -a "$LOG_FILE"
    
    echo "[$(date +%H:%M:%S)] OSMO d$disp complete" | tee -a "$LOG_FILE"
done

echo "" | tee -a "$LOG_FILE"

# =============================================================================
# PHASE 4: ANALYSIS & REPORT
# =============================================================================

echo "================================================================================" | tee -a "$LOG_FILE"
echo "PHASE 4: ANALYSIS & REPORT GENERATION" | tee -a "$LOG_FILE"
echo "================================================================================" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

echo "[$(date +%H:%M:%S)] Generating comprehensive report..." | tee -a "$LOG_FILE"

python -c "
import pandas as pd
import glob
from datetime import datetime

# Load all results
scan_files = sorted(glob.glob('outputs/pr20_*_multiasset_scan_*.csv'))
guards_files = sorted(glob.glob('outputs/pr20_*_guards_summary_*.csv'))
stress_files = glob.glob('outputs/pr20_regime_stress_*.csv')

if not scan_files or not guards_files:
    print('ERROR: No results files found')
    exit(1)

scan_df = pd.concat([pd.read_csv(f) for f in scan_files], ignore_index=True)
guards_df = pd.concat([pd.read_csv(f) for f in guards_files], ignore_index=True)

# Merge results
results = scan_df.merge(guards_df, on='asset', how='left')

# Summary stats
print('\n=== PR#20 REVALIDATION SUMMARY ===\n')
print(f'Total assets tested: {len(results)}')
print(f'Assets passing hard guards: {(results.get(\"all_hard_pass\", False) == True).sum()}')
print(f'Mean OOS Sharpe: {results[\"oos_sharpe\"].mean():.2f}')
print(f'Mean WFE: {results[\"wfe_pardo\"].mean():.2f}')

# CRITICAL: Check SHORT signal ratio
if 'short_trades' in results.columns and 'oos_trades' in results.columns:
    results['short_ratio'] = results['short_trades'] / results['oos_trades']
    print(f'Mean SHORT ratio: {results[\"short_ratio\"].mean():.1%}')
    no_shorts = (results['short_ratio'] == 0).sum()
    if no_shorts > 0:
        print(f'⚠️ WARNING: {no_shorts} assets have 0% SHORT signals')

# Save consolidated report
results.to_csv('outputs/PR20_CONSOLIDATED_RESULTS.csv', index=False)
print(f'\nResults saved to: outputs/PR20_CONSOLIDATED_RESULTS.csv')

# Top performers
print('\n=== TOP 5 PERFORMERS ===')
top5 = results.nlargest(5, 'oos_sharpe')[['asset', 'oos_sharpe', 'wfe_pardo', 'oos_trades']]
print(top5.to_string(index=False))

# Assets that need attention
print('\n=== ASSETS NEEDING ATTENTION ===')
failed = results[results.get('all_hard_pass', True) == False]
if len(failed) > 0:
    print(failed[['asset', 'oos_sharpe', 'wfe_pardo', 'fail_reason']].to_string(index=False))
else:
    print('None - all assets passed!')

" | tee -a "$LOG_FILE"

# =============================================================================
# COMPLETION
# =============================================================================

echo "" | tee -a "$LOG_FILE"
echo "================================================================================" | tee -a "$LOG_FILE"
echo "PR#20 REVALIDATION COMPLETE" | tee -a "$LOG_FILE"
echo "================================================================================" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"
echo "End: $(date)" | tee -a "$LOG_FILE"
echo "Log file: $LOG_FILE" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"
echo "Next steps:" | tee -a "$LOG_FILE"
echo "1. Review outputs/PR20_CONSOLIDATED_RESULTS.csv" | tee -a "$LOG_FILE"
echo "2. Update project-state.md with new metrics" | tee -a "$LOG_FILE"
echo "3. Document any failed assets" | tee -a "$LOG_FILE"
echo "4. Create PR#20 summary report" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"
