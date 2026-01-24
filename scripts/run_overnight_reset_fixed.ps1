# OVERNIGHT RESET PIPELINE (FIXED - No duplicates)
# Phase 1 Re-screening: 60 assets, 5 batches (~3h)
# Auto-validation: SUCCESS assets → Phase 2 (workers=1)

$ErrorActionPreference = "Continue"
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$logfile = "outputs\overnight_log_$timestamp.txt"

function Log-Message {
    param($message)
    $time = Get-Date -Format "HH:mm:ss"
    $log = "[$time] $message"
    Write-Host $log
    Add-Content -Path $logfile -Value $log
}

Log-Message "=== OVERNIGHT RESET PIPELINE START ==="
Log-Message "Timestamp: $timestamp"
Log-Message "Total assets: 60 (5 batches)"
Log-Message "Estimated duration: 3-4h"

# ==============================================================================
# PHASE 1: RE-SCREENING (5 Batches)
# ==============================================================================

Log-Message ""
Log-Message "=========================================="
Log-Message "BATCH 1: Anciens PROD (15 assets) - PRIORITAIRE"
Log-Message "=========================================="
python scripts/run_full_pipeline.py `
  --assets BTC ETH JOE OSMO MINA AVAX AR ANKR DOGE OP DOT NEAR SHIB METIS YGG `
  --workers 10 `
  --trials-atr 200 `
  --trials-ichi 200 `
  --enforce-tp-progression `
  --output-prefix phase1_reset_batch1_prod

if ($LASTEXITCODE -eq 0) {
    Log-Message "✅ Batch 1 COMPLETE"
} else {
    Log-Message "❌ Batch 1 FAILED (exit code: $LASTEXITCODE)"
}

Start-Sleep -Seconds 10

Log-Message ""
Log-Message "=========================================="
Log-Message "BATCH 2: High Cap (15 assets)"
Log-Message "=========================================="
python scripts/run_full_pipeline.py `
  --assets SOL ADA XRP BNB TRX LTC MATIC ATOM LINK UNI ARB HBAR ICP ALGO FTM `
  --workers 10 `
  --trials-atr 200 `
  --trials-ichi 200 `
  --enforce-tp-progression `
  --output-prefix phase1_reset_batch2_highcap

if ($LASTEXITCODE -eq 0) {
    Log-Message "✅ Batch 2 COMPLETE"
} else {
    Log-Message "❌ Batch 2 FAILED (exit code: $LASTEXITCODE)"
}

Start-Sleep -Seconds 10

Log-Message ""
Log-Message "=========================================="
Log-Message "BATCH 3: DeFi + L2 (10 assets)"
Log-Message "=========================================="
python scripts/run_full_pipeline.py `
  --assets AAVE MKR CRV SUSHI RUNE INJ TIA SEI CAKE TON `
  --workers 10 `
  --trials-atr 200 `
  --trials-ichi 200 `
  --enforce-tp-progression `
  --output-prefix phase1_reset_batch3_defi

if ($LASTEXITCODE -eq 0) {
    Log-Message "✅ Batch 3 COMPLETE"
} else {
    Log-Message "❌ Batch 3 FAILED (exit code: $LASTEXITCODE)"
}

Start-Sleep -Seconds 10

Log-Message ""
Log-Message "=========================================="
Log-Message "BATCH 4: Gaming + Meme (10 assets)"
Log-Message "=========================================="
python scripts/run_full_pipeline.py `
  --assets PEPE ILV GALA SAND MANA ENJ FLOKI WIF RONIN AXS `
  --workers 10 `
  --trials-atr 200 `
  --trials-ichi 200 `
  --enforce-tp-progression `
  --output-prefix phase1_reset_batch4_gaming

if ($LASTEXITCODE -eq 0) {
    Log-Message "✅ Batch 4 COMPLETE"
} else {
    Log-Message "❌ Batch 4 FAILED (exit code: $LASTEXITCODE)"
}

Start-Sleep -Seconds 10

Log-Message ""
Log-Message "=========================================="
Log-Message "BATCH 5: Infra + Storage (10 assets)"
Log-Message "=========================================="
python scripts/run_full_pipeline.py `
  --assets FIL GRT THETA VET RENDER EGLD KAVA CFX ROSE STRK `
  --workers 10 `
  --trials-atr 200 `
  --trials-ichi 200 `
  --enforce-tp-progression `
  --output-prefix phase1_reset_batch5_infra

if ($LASTEXITCODE -eq 0) {
    Log-Message "✅ Batch 5 COMPLETE"
} else {
    Log-Message "❌ Batch 5 FAILED (exit code: $LASTEXITCODE)"
}

# ==============================================================================
# PHASE 1: SUMMARY
# ==============================================================================

Log-Message ""
Log-Message "=========================================="
Log-Message "PHASE 1 RE-SCREENING COMPLETE"
Log-Message "=========================================="

# Aggregate all Phase 1 results
# FIX: Filter to only multiasset_scan (not multi_asset_scan) to avoid duplicates
$scan_files = Get-ChildItem -Path "outputs" -Filter "*phase1_reset*multiasset_scan*.csv" | 
    Where-Object { $_.LastWriteTime -gt (Get-Date).AddHours(-4) -and $_.Name -notmatch "multi_asset_scan" }

Log-Message ""
Log-Message "Phase 1 Result Files:"
foreach ($file in $scan_files) {
    Log-Message "  - $($file.Name) ($($file.Length) bytes)"
}

# Parse SUCCESS assets
Log-Message ""
Log-Message "Analyzing Phase 1 SUCCESS assets..."

$success_assets = @()
foreach ($file in $scan_files) {
    $content = Get-Content $file.FullName | Select-Object -Skip 1
    foreach ($line in $content) {
        if ($line -match "^([A-Z]+),SUCCESS") {
            $asset = $matches[1]
            $success_assets += $asset
        }
    }
}

# FIX: Deduplicate assets (in case of any remaining duplicates)
$success_assets = $success_assets | Select-Object -Unique

Log-Message "SUCCESS assets (deduplicated):"
foreach ($asset in $success_assets) {
    Log-Message "  ✅ $asset"
}

$success_count = $success_assets.Count
Log-Message ""
Log-Message "=========================================="
Log-Message "PHASE 1 SUMMARY"
Log-Message "=========================================="
Log-Message "Total assets tested: 60"
Log-Message "SUCCESS: $success_count assets (deduplicated)"
Log-Message "SUCCESS rate: $([math]::Round($success_count / 60 * 100, 1))%"
Log-Message ""

# ==============================================================================
# PHASE 2: VALIDATION (Auto-start for SUCCESS assets)
# ==============================================================================

if ($success_count -gt 0) {
    Log-Message "=========================================="
    Log-Message "PHASE 2: AUTO-VALIDATION START"
    Log-Message "=========================================="
    Log-Message "Assets to validate: $success_count"
    Log-Message ""
    
    foreach ($asset in $success_assets) {
        Log-Message ""
        Log-Message "===================="
        Log-Message "Validating: $asset (Run 1)"
        Log-Message "===================="
        
        python scripts/run_full_pipeline.py `
          --assets $asset `
          --workers 1 `
          --trials-atr 300 `
          --trials-ichi 300 `
          --enforce-tp-progression `
          --run-guards `
          --output-prefix "phase2_validation_${asset}_run1"
        
        if ($LASTEXITCODE -eq 0) {
            Log-Message "✅ $asset Run 1 COMPLETE"
            
            # Run 2 (reproducibility check)
            Log-Message ""
            Log-Message "===================="
            Log-Message "Validating: $asset (Run 2 - Reproducibility)"
            Log-Message "===================="
            
            python scripts/run_full_pipeline.py `
              --assets $asset `
              --workers 1 `
              --trials-atr 300 `
              --trials-ichi 300 `
              --enforce-tp-progression `
              --run-guards `
              --output-prefix "phase2_validation_${asset}_run2"
            
            if ($LASTEXITCODE -eq 0) {
                Log-Message "✅ $asset Run 2 COMPLETE - Check reproducibility manually"
            } else {
                Log-Message "❌ $asset Run 2 FAILED"
            }
            
        } else {
            Log-Message "❌ $asset Run 1 FAILED - skipping Run 2"
        }
        
        Start-Sleep -Seconds 5
    }
    
    Log-Message ""
    Log-Message "=========================================="
    Log-Message "PHASE 2 VALIDATION COMPLETE"
    Log-Message "=========================================="
    Log-Message "Validated: $success_count assets (Run 1 + Run 2)"
    Log-Message "Next: Compare Run 1 vs Run 2 for reproducibility"
    Log-Message "Then: Analyze guards results (7/7 PASS required)"
    
} else {
    Log-Message "⚠️  No SUCCESS assets from Phase 1 - skipping Phase 2"
}

# ==============================================================================
# FINAL SUMMARY
# ==============================================================================

$end_time = Get-Date
$duration = $end_time - (Get-Date $timestamp)

Log-Message ""
Log-Message "=========================================="
Log-Message "OVERNIGHT PIPELINE COMPLETE"
Log-Message "=========================================="
Log-Message "Start: $timestamp"
Log-Message "End: $(Get-Date -Format 'yyyyMMdd_HHmmss')"
Log-Message "Duration: $($duration.Hours)h $($duration.Minutes)m"
Log-Message ""
Log-Message "Phase 1: 60 assets tested, $success_count SUCCESS"
Log-Message "Phase 2: $success_count assets validated (Run 1 + Run 2)"
Log-Message ""
Log-Message "Next steps:"
Log-Message "1. Review log: $logfile"
Log-Message "2. Compare Run 1 vs Run 2 (reproducibility)"
Log-Message "3. Analyze guards (7/7 PASS)"
Log-Message "4. Update status/project-state.md with PROD assets"
Log-Message ""
Log-Message "✅ PIPELINE COMPLETE"
