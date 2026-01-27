#!/bin/bash

# PR#20 MEGA BATCH Re-validation with PBO Fix
# Re-runs 18 assets with proper returns_matrix tracking for PBO calculation

echo "=================================="
echo "PR#20 MEGA BATCH RE-RUN (with PBO)"
echo "=================================="
echo "Starting: $(date)"

cd /c/Users/Arthur/friendly-fishstick

# Batch 1: YGG, MINA, CAKE, RUNE (Priority PROD assets)
echo ""
echo "=== BATCH 1: Priority PROD Assets ==="
python scripts/run_full_pipeline.py \
  --assets YGG MINA CAKE RUNE \
  --optimization-mode baseline \
  --trials-atr 300 --trials-ichi 300 \
  --run-guards --workers 1 \
  --output-prefix pr20_fixed_batch1

# Batch 2: EGLD, AVAX, BTC, SOL (Major assets)
echo ""
echo "=== BATCH 2: Major Assets ==="
python scripts/run_full_pipeline.py \
  --assets EGLD AVAX BTC SOL \
  --optimization-mode baseline \
  --trials-atr 300 --trials-ichi 300 \
  --run-guards --workers 1 \
  --output-prefix pr20_fixed_batch2

# Batch 3: HBAR, TON, SUSHI, CRV, ONE, SEI, AXS, AAVE, ZIL, GALA (Candidates)
echo ""
echo "=== BATCH 3: Candidate Assets ==="
python scripts/run_full_pipeline.py \
  --assets HBAR TON SUSHI CRV ONE SEI AXS AAVE ZIL GALA \
  --optimization-mode baseline \
  --trials-atr 300 --trials-ichi 300 \
  --run-guards --workers 1 \
  --output-prefix pr20_fixed_batch3

echo ""
echo "=================================="
echo "PR#20 Re-validation Complete!"
echo "Completed: $(date)"
echo "=================================="
