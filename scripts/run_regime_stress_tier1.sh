#!/bin/bash
# Phase 4 Regime Stress Test — TIER 1 Assets (Top 5 PROD)
# Validates SIDEWAYS Sharpe > 0 criterion

echo "=== Phase 4: Regime Stress Test — TIER 1 Assets ==="
echo "Date: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

ASSETS=("SOL" "AVAX" "ETH" "BTC" "AXS")

for asset in "${ASSETS[@]}"; do
    echo "Testing $asset — SIDEWAYS regime..."
    python scripts/run_regime_stress_test.py \
        --asset "$asset" \
        --regime SIDEWAYS \
        --output-prefix "tier1_sideways"
    
    if [ $? -eq 0 ]; then
        echo "✅ $asset SIDEWAYS test complete"
    else
        echo "❌ $asset SIDEWAYS test FAILED"
    fi
    echo ""
done

echo "=== Regime Stress Test Complete ==="
echo "Results: outputs/tier1_sideways_*"
