# Phase 4 Regime Stress Test — TIER 1 Assets (PowerShell)
# Validates SIDEWAYS Sharpe > 0 criterion

Write-Host "=== Phase 4: Regime Stress Test — TIER 1 Assets ===" -ForegroundColor Cyan
Write-Host "Date: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
Write-Host ""

$assets = @("SOL", "AVAX", "ETH", "BTC", "AXS")
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"

foreach ($asset in $assets) {
    Write-Host "Testing $asset — SIDEWAYS regime..." -ForegroundColor Yellow
    
    $outputFile = "outputs/tier1_sideways_${asset}_${timestamp}.csv"
    
    python scripts/run_regime_stress_test.py `
        --asset $asset `
        --regimes SIDEWAYS `
        --output $outputFile
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ $asset SIDEWAYS test complete" -ForegroundColor Green
    } else {
        Write-Host "❌ $asset SIDEWAYS test FAILED" -ForegroundColor Red
    }
    Write-Host ""
}

Write-Host "=== Regime Stress Test Complete ===" -ForegroundColor Cyan
Write-Host "Results: outputs/tier1_sideways_*"
