# V4.2 Batch Pilot - 4 Assets in Parallel
# Assets: DOT, SHIB, ANKR, BTC
# Estimated time: ~10 minutes

Write-Host "=== V4.2 BATCH PILOT - Starting 4 assets in parallel ===" -ForegroundColor Cyan
Write-Host "Assets: DOT, SHIB, ANKR, BTC" -ForegroundColor Yellow
Write-Host "Run ID: v4.2_batch01" -ForegroundColor Yellow
Write-Host ""

# Start all 4 in background
Write-Host "[1/4] Starting DOT..." -ForegroundColor Green
Start-Process -NoNewWindow python -ArgumentList "scripts/orchestrator_v4_2.py --asset DOT --run-id v4.2_batch01 --family A" -RedirectStandardOutput "logs/dot_v4.2.log" -RedirectStandardError "logs/dot_v4.2.err"

Write-Host "[2/4] Starting SHIB..." -ForegroundColor Green
Start-Process -NoNewWindow python -ArgumentList "scripts/orchestrator_v4_2.py --asset SHIB --run-id v4.2_batch01 --family A" -RedirectStandardOutput "logs/shib_v4.2.log" -RedirectStandardError "logs/shib_v4.2.err"

Write-Host "[3/4] Starting ANKR..." -ForegroundColor Green
Start-Process -NoNewWindow python -ArgumentList "scripts/orchestrator_v4_2.py --asset ANKR --run-id v4.2_batch01 --family A" -RedirectStandardOutput "logs/ankr_v4.2.log" -RedirectStandardError "logs/ankr_v4.2.err"

Write-Host "[4/4] Starting BTC..." -ForegroundColor Green
Start-Process -NoNewWindow python -ArgumentList "scripts/orchestrator_v4_2.py --asset BTC --run-id v4.2_batch01 --family A" -RedirectStandardOutput "logs/btc_v4.2.log" -RedirectStandardError "logs/btc_v4.2.err"

Write-Host ""
Write-Host "All processes started. Waiting for completion..." -ForegroundColor Cyan
Write-Host ""

# Wait for all to complete (~10 min)
# Check every 60s if outputs exist
$iteration = 0
while (-not (
  (Test-Path "runs/v4_2/DOT/v4.2_batch01/archive/summary.json") -and
  (Test-Path "runs/v4_2/SHIB/v4.2_batch01/archive/summary.json") -and
  (Test-Path "runs/v4_2/ANKR/v4.2_batch01/archive/summary.json") -and
  (Test-Path "runs/v4_2/BTC/v4.2_batch01/archive/summary.json")
)) {
  $iteration++
  $elapsed = $iteration * 60
  Write-Host "[${elapsed}s] Waiting for completion... (check #${iteration})" -ForegroundColor Yellow

  # Show which assets are done
  if (Test-Path "runs/v4_2/DOT/v4.2_batch01/archive/summary.json") { Write-Host "  ✓ DOT done" -ForegroundColor Green }
  if (Test-Path "runs/v4_2/SHIB/v4.2_batch01/archive/summary.json") { Write-Host "  ✓ SHIB done" -ForegroundColor Green }
  if (Test-Path "runs/v4_2/ANKR/v4.2_batch01/archive/summary.json") { Write-Host "  ✓ ANKR done" -ForegroundColor Green }
  if (Test-Path "runs/v4_2/BTC/v4.2_batch01/archive/summary.json") { Write-Host "  ✓ BTC done" -ForegroundColor Green }

  Start-Sleep 60
}

Write-Host ""
Write-Host "=== ALL PROCESSES COMPLETE ===" -ForegroundColor Cyan
Write-Host ""

# Report results
Write-Host "=== RESULTS SUMMARY ===" -ForegroundColor Cyan
Write-Host ""

foreach ($asset in @("DOT","SHIB","ANKR","BTC")) {
  Write-Host "--- $asset ---" -ForegroundColor Yellow

  $guardsPath = "runs/v4_2/$asset/v4.2_batch01/guards/guards.json"
  $portfolioPath = "runs/v4_2/$asset/v4.2_batch01/portfolio/portfolio.json"
  $baselinePath = "runs/v4_2/$asset/v4.2_batch01/baseline/baseline_best.json"

  if ((Test-Path $guardsPath) -and (Test-Path $portfolioPath) -and (Test-Path $baselinePath)) {
    try {
      $result = python -c @"
import json
g = json.load(open('$guardsPath'))
p = json.load(open('$portfolioPath'))
b = json.load(open('$baselinePath'))
wfe = b.get('wfe', 'N/A')
wfe_str = f'{wfe:.2f}' if isinstance(wfe, (int, float)) else str(wfe)
print(f'Guards: {g[\"passed\"]} | Portfolio: {p[\"passed\"]} | WFE: {wfe_str}')
"@
      Write-Host "  $result" -ForegroundColor White
    } catch {
      Write-Host "  ERROR: Failed to parse results" -ForegroundColor Red
    }
  } else {
    Write-Host "  ERROR: Missing output files" -ForegroundColor Red
  }
  Write-Host ""
}

Write-Host "=== BATCH PILOT COMPLETE ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "Log files: logs/*_v4.2.log" -ForegroundColor Gray
Write-Host "Results: runs/v4_2/{ASSET}/v4.2_batch01/" -ForegroundColor Gray
