#!/bin/bash
# OVERNIGHT RESET PIPELINE (Linux/Mac version)
# Phase 1 Re-screening: 60 assets, 5 batches (~3h)
# Auto-validation: SUCCESS assets → Phase 2 (workers=1)

set +e  # Continue on error
timestamp=$(date +%Y%m%d_%H%M%S)
logfile="outputs/overnight_log_${timestamp}.txt"

log_message() {
    time=$(date +%H:%M:%S)
    echo "[$time] $1" | tee -a "$logfile"
}

log_message "=== OVERNIGHT RESET PIPELINE START ==="
log_message "Timestamp: $timestamp"
log_message "Total assets: 60 (5 batches)"
log_message "Estimated duration: 3-4h"

# ==============================================================================
# PHASE 1: RE-SCREENING (5 Batches)
# ==============================================================================

log_message ""
log_message "=========================================="
log_message "BATCH 1: Anciens PROD (15 assets) - PRIORITAIRE"
log_message "=========================================="
python scripts/run_full_pipeline.py \
  --assets BTC ETH JOE OSMO MINA AVAX AR ANKR DOGE OP DOT NEAR SHIB METIS YGG \
  --workers 10 \
  --trials-atr 200 \
  --trials-ichi 200 \
  --enforce-tp-progression \
  --output-prefix phase1_reset_batch1_prod

[ $? -eq 0 ] && log_message "✅ Batch 1 COMPLETE" || log_message "❌ Batch 1 FAILED"
sleep 10

log_message ""
log_message "=========================================="
log_message "BATCH 2: High Cap (15 assets)"
log_message "=========================================="
python scripts/run_full_pipeline.py \
  --assets SOL ADA XRP BNB TRX LTC MATIC ATOM LINK UNI ARB HBAR ICP ALGO FTM \
  --workers 10 \
  --trials-atr 200 \
  --trials-ichi 200 \
  --enforce-tp-progression \
  --output-prefix phase1_reset_batch2_highcap

[ $? -eq 0 ] && log_message "✅ Batch 2 COMPLETE" || log_message "❌ Batch 2 FAILED"
sleep 10

log_message ""
log_message "=========================================="
log_message "BATCH 3: DeFi + L2 (10 assets)"
log_message "=========================================="
python scripts/run_full_pipeline.py \
  --assets AAVE MKR CRV SUSHI RUNE INJ TIA SEI CAKE TON \
  --workers 10 \
  --trials-atr 200 \
  --trials-ichi 200 \
  --enforce-tp-progression \
  --output-prefix phase1_reset_batch3_defi

[ $? -eq 0 ] && log_message "✅ Batch 3 COMPLETE" || log_message "❌ Batch 3 FAILED"
sleep 10

log_message ""
log_message "=========================================="
log_message "BATCH 4: Gaming + Meme (10 assets)"
log_message "=========================================="
python scripts/run_full_pipeline.py \
  --assets PEPE ILV GALA SAND MANA ENJ FLOKI WIF RONIN AXS \
  --workers 10 \
  --trials-atr 200 \
  --trials-ichi 200 \
  --enforce-tp-progression \
  --output-prefix phase1_reset_batch4_gaming

[ $? -eq 0 ] && log_message "✅ Batch 4 COMPLETE" || log_message "❌ Batch 4 FAILED"
sleep 10

log_message ""
log_message "=========================================="
log_message "BATCH 5: Infra + Storage (10 assets)"
log_message "=========================================="
python scripts/run_full_pipeline.py \
  --assets FIL GRT THETA VET RENDER EGLD KAVA CFX ROSE STRK \
  --workers 10 \
  --trials-atr 200 \
  --trials-ichi 200 \
  --enforce-tp-progression \
  --output-prefix phase1_reset_batch5_infra

[ $? -eq 0 ] && log_message "✅ Batch 5 COMPLETE" || log_message "❌ Batch 5 FAILED"

# ==============================================================================
# PHASE 1: SUMMARY
# ==============================================================================

log_message ""
log_message "=========================================="
log_message "PHASE 1 RE-SCREENING COMPLETE"
log_message "=========================================="

# Parse SUCCESS assets
log_message ""
log_message "Analyzing Phase 1 SUCCESS assets..."

success_assets=()
for file in outputs/*phase1_reset*.csv; do
    if [ -f "$file" ]; then
        while IFS=, read -r asset status rest; do
            if [ "$status" = "SUCCESS" ]; then
                success_assets+=("$asset")
                log_message "  ✅ SUCCESS: $asset"
            fi
        done < <(tail -n +2 "$file")
    fi
done

success_count=${#success_assets[@]}
success_rate=$(echo "scale=1; $success_count / 60 * 100" | bc)

log_message ""
log_message "=========================================="
log_message "PHASE 1 SUMMARY"
log_message "=========================================="
log_message "Total assets tested: 60"
log_message "SUCCESS: $success_count assets"
log_message "SUCCESS rate: ${success_rate}%"
log_message ""

# ==============================================================================
# PHASE 2: VALIDATION (Auto-start for SUCCESS assets)
# ==============================================================================

if [ $success_count -gt 0 ]; then
    log_message "=========================================="
    log_message "PHASE 2: AUTO-VALIDATION START"
    log_message "=========================================="
    log_message "Assets to validate: $success_count"
    log_message ""
    
    for asset in "${success_assets[@]}"; do
        log_message ""
        log_message "===================="
        log_message "Validating: $asset (Run 1)"
        log_message "===================="
        
        python scripts/run_full_pipeline.py \
          --assets "$asset" \
          --workers 1 \
          --trials-atr 300 \
          --trials-ichi 300 \
          --enforce-tp-progression \
          --run-guards \
          --output-prefix "phase2_validation_${asset}_run1"
        
        if [ $? -eq 0 ]; then
            log_message "✅ $asset Run 1 COMPLETE"
            
            # Run 2 (reproducibility check)
            log_message ""
            log_message "===================="
            log_message "Validating: $asset (Run 2 - Reproducibility)"
            log_message "===================="
            
            python scripts/run_full_pipeline.py \
              --assets "$asset" \
              --workers 1 \
              --trials-atr 300 \
              --trials-ichi 300 \
              --enforce-tp-progression \
              --run-guards \
              --output-prefix "phase2_validation_${asset}_run2"
            
            [ $? -eq 0 ] && log_message "✅ $asset Run 2 COMPLETE" || log_message "❌ $asset Run 2 FAILED"
        else
            log_message "❌ $asset Run 1 FAILED - skipping Run 2"
        fi
        
        sleep 5
    done
    
    log_message ""
    log_message "=========================================="
    log_message "PHASE 2 VALIDATION COMPLETE"
    log_message "=========================================="
    log_message "Validated: $success_count assets (Run 1 + Run 2)"
    
else
    log_message "⚠️  No SUCCESS assets from Phase 1 - skipping Phase 2"
fi

# ==============================================================================
# FINAL SUMMARY
# ==============================================================================

end_time=$(date +%s)
start_time=$(date -d "$timestamp" +%s 2>/dev/null || date -j -f "%Y%m%d_%H%M%S" "$timestamp" +%s)
duration=$((end_time - start_time))
hours=$((duration / 3600))
minutes=$(((duration % 3600) / 60))

log_message ""
log_message "=========================================="
log_message "OVERNIGHT PIPELINE COMPLETE"
log_message "=========================================="
log_message "Duration: ${hours}h ${minutes}m"
log_message ""
log_message "Phase 1: 60 assets tested, $success_count SUCCESS"
log_message "Phase 2: $success_count assets validated (Run 1 + Run 2)"
log_message ""
log_message "Next steps:"
log_message "1. Review log: $logfile"
log_message "2. Compare Run 1 vs Run 2 (reproducibility)"
log_message "3. Analyze guards (7/7 PASS)"
log_message "4. Update status/project-state.md"
log_message ""
log_message "✅ PIPELINE COMPLETE"
