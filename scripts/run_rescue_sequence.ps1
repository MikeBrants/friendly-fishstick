# RESCUE SEQUENCE — 4 Assets
# CRV (5min) → TIA (30min) → CAKE (30min) → SUSHI (3x 30min)
# Total: ~2h15-2h45

$ErrorActionPreference = "Continue"
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$logfile = "outputs\rescue_log_$timestamp.txt"

function Log-Message {
    param($message)
    $time = Get-Date -Format "HH:mm:ss"
    $log = "[$time] $message"
    Write-Host $log
    Add-Content -Path $logfile -Value $log
}

Log-Message "=== RESCUE SEQUENCE START ==="
Log-Message "4 assets: CRV, TIA, CAKE, SUSHI"
Log-Message "ETA: 2h15-2h45"
Log-Message ""

# ============================================================================
# 1. CRV — Guards Only (5 min)
# ============================================================================

Log-Message "===================="
Log-Message "1/4: CRV Guards"
Log-Message "===================="

python scripts/run_guards_multiasset.py `
  --scan-file outputs/phase1_reset_batch3_defi_multiasset_scan_20260124_041607.csv `
  --assets CRV `
  --output-prefix rescue_CRV_guards

if ($LASTEXITCODE -eq 0) {
    Log-Message "✅ CRV Guards COMPLETE"
} else {
    Log-Message "❌ CRV Guards FAILED (exit code: $LASTEXITCODE)"
}

Start-Sleep -Seconds 5

# ============================================================================
# 2. TIA — Filters Reopt (30 min)
# ============================================================================

Log-Message ""
Log-Message "===================="
Log-Message "2/4: TIA Filters Reopt"
Log-Message "===================="

python scripts/run_full_pipeline.py `
  --assets TIA `
  --optimization-mode medium_distance_volume `
  --workers 1 `
  --trials-atr 300 `
  --trials-ichi 300 `
  --enforce-tp-progression `
  --run-guards `
  --output-prefix rescue_TIA_filters

if ($LASTEXITCODE -eq 0) {
    Log-Message "✅ TIA Reopt COMPLETE"
} else {
    Log-Message "❌ TIA Reopt FAILED (exit code: $LASTEXITCODE)"
}

Start-Sleep -Seconds 5

# ============================================================================
# 3. CAKE — Filters Reopt (30-40 min)
# ============================================================================

Log-Message ""
Log-Message "===================="
Log-Message "3/4: CAKE Filters Reopt"
Log-Message "===================="

python scripts/run_full_pipeline.py `
  --assets CAKE `
  --optimization-mode medium_distance_volume `
  --workers 1 `
  --trials-atr 400 `
  --trials-ichi 400 `
  --enforce-tp-progression `
  --run-guards `
  --output-prefix rescue_CAKE_filters

if ($LASTEXITCODE -eq 0) {
    Log-Message "✅ CAKE Reopt COMPLETE"
} else {
    Log-Message "❌ CAKE Reopt FAILED (exit code: $LASTEXITCODE)"
}

Start-Sleep -Seconds 5

# ============================================================================
# 4. SUSHI — 3 Variantes (1h30 total)
# ============================================================================

Log-Message ""
Log-Message "===================="
Log-Message "4/4: SUSHI Rescue (3 variantes)"
Log-Message "===================="

# Variante 1: Conservative
Log-Message ""
Log-Message "--- SUSHI Variante 1/3: Conservative ---"

python scripts/run_full_pipeline.py `
  --assets SUSHI `
  --optimization-mode conservative `
  --workers 1 `
  --trials-atr 300 `
  --trials-ichi 300 `
  --enforce-tp-progression `
  --run-guards `
  --output-prefix rescue_SUSHI_conservative

if ($LASTEXITCODE -eq 0) {
    Log-Message "✅ SUSHI Conservative COMPLETE"
} else {
    Log-Message "❌ SUSHI Conservative FAILED"
}

Start-Sleep -Seconds 5

# Variante 2: d26 + Filters
Log-Message ""
Log-Message "--- SUSHI Variante 2/3: d26 + Filters ---"

python scripts/run_full_pipeline.py `
  --assets SUSHI `
  --fixed-displacement 26 `
  --optimization-mode medium_distance_volume `
  --workers 1 `
  --trials-atr 300 `
  --trials-ichi 300 `
  --enforce-tp-progression `
  --run-guards `
  --output-prefix rescue_SUSHI_d26_filters

if ($LASTEXITCODE -eq 0) {
    Log-Message "✅ SUSHI d26 COMPLETE"
} else {
    Log-Message "❌ SUSHI d26 FAILED"
}

Start-Sleep -Seconds 5

# Variante 3: d78 + Filters
Log-Message ""
Log-Message "--- SUSHI Variante 3/3: d78 + Filters ---"

python scripts/run_full_pipeline.py `
  --assets SUSHI `
  --fixed-displacement 78 `
  --optimization-mode medium_distance_volume `
  --workers 1 `
  --trials-atr 300 `
  --trials-ichi 300 `
  --enforce-tp-progression `
  --run-guards `
  --output-prefix rescue_SUSHI_d78_filters

if ($LASTEXITCODE -eq 0) {
    Log-Message "✅ SUSHI d78 COMPLETE"
} else {
    Log-Message "❌ SUSHI d78 FAILED"
}

# ============================================================================
# FINAL SUMMARY
# ============================================================================

$end_time = Get-Date
$start_time = Get-Date $timestamp
$duration = $end_time - $start_time

Log-Message ""
Log-Message "===================="
Log-Message "RESCUE SEQUENCE COMPLETE"
Log-Message "===================="
Log-Message "Duration: $($duration.Hours)h $($duration.Minutes)m"
Log-Message ""
Log-Message "Results:"
Log-Message "1. CRV: Check rescue_CRV_guards_summary_*.csv"
Log-Message "2. TIA: Check rescue_TIA_filters_multiasset_scan_*.csv + guards"
Log-Message "3. CAKE: Check rescue_CAKE_filters_multiasset_scan_*.csv + guards"
Log-Message "4. SUSHI: Check rescue_SUSHI_*_multiasset_scan_*.csv + guards (3 variantes)"
Log-Message ""
Log-Message "Next: Analyze guards results → Update portfolio"
Log-Message "✅ RESCUE COMPLETE"
