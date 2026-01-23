# Check Data Availability for Overnight Pipeline

$required_assets = @(
    # Batch 1 (15)
    "BTC", "ETH", "JOE", "OSMO", "MINA", "AVAX", "AR", "ANKR", "DOGE", "OP", "DOT", "NEAR", "SHIB", "METIS", "YGG",
    # Batch 2 (15)
    "SOL", "ADA", "XRP", "BNB", "TRX", "LTC", "MATIC", "ATOM", "LINK", "UNI", "ARB", "HBAR", "ICP", "ALGO", "FTM",
    # Batch 3 (10)
    "AAVE", "MKR", "CRV", "SUSHI", "RUNE", "INJ", "TIA", "SEI", "CAKE", "TON",
    # Batch 4 (10)
    "PEPE", "ILV", "GALA", "SAND", "MANA", "ENJ", "FLOKI", "WIF", "RONIN", "AXS",
    # Batch 5 (10)
    "FIL", "GRT", "THETA", "VET", "RENDER", "EGLD", "KAVA", "CFX", "ROSE", "STRK"
)

Write-Host "=== DATA AVAILABILITY CHECK ===" -ForegroundColor Cyan
Write-Host "Total assets required: $($required_assets.Count)" -ForegroundColor Cyan
Write-Host ""

$available = @()
$missing = @()

foreach ($asset in $required_assets) {
    $file = "data\${asset}_1H.parquet"
    if (Test-Path $file) {
        $size = (Get-Item $file).Length / 1KB
        $available += $asset
        Write-Host "✅ $asset ($([math]::Round($size, 0)) KB)" -ForegroundColor Green
    } else {
        $missing += $asset
        Write-Host "❌ $asset - MISSING" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "=== SUMMARY ===" -ForegroundColor Cyan
Write-Host "Available: $($available.Count) / $($required_assets.Count)" -ForegroundColor Green
Write-Host "Missing: $($missing.Count)" -ForegroundColor Red

if ($missing.Count -gt 0) {
    Write-Host ""
    Write-Host "Missing assets:" -ForegroundColor Yellow
    foreach ($asset in $missing) {
        Write-Host "  - $asset" -ForegroundColor Yellow
    }
    
    Write-Host ""
    Write-Host "Download command:" -ForegroundColor Cyan
    Write-Host "python scripts/download_data.py --assets $($missing -join ' ')" -ForegroundColor White
    
    Write-Host ""
    Write-Host "⚠️  DOWNLOAD REQUIRED BEFORE OVERNIGHT LAUNCH" -ForegroundColor Yellow
} else {
    Write-Host ""
    Write-Host "🟢 ALL DATA AVAILABLE - READY TO LAUNCH OVERNIGHT PIPELINE" -ForegroundColor Green
}
