# CHALLENGER PIPELINE - 100 Trials Experiment

**Objectif**: Tester si réduire les trials (300→100) diminue l'overfitting PBO

## Hypothèse

Le PBO élevé (66% EXCLU sur 18 assets avec 300 trials) pourrait être causé par:
- Trop de trials → plus de chances de trouver des paramètres overfittés par chance
- Réduire à 100 trials = réduire l'espace de recherche = moins d'overfitting potentiel

## Configuration

| Parameter | Value |
|-----------|-------|
| Assets | BTC, ETH, SOL, AVAX |
| Trials ATR | 100 |
| Trials Ichimoku | 100 |
| Workers | 1 (sequential, reproducible) |
| Guards | ON (7 guards + PBO) |
| Output Prefix | `challenger_100trials` |
| Seed | N/A (argument not supported) |

## Baseline Comparison (300 trials)

| Asset | Sharpe OOS | WFE | PBO | PBO Verdict |
|-------|------------|-----|-----|-------------|
| BTC | -0.18 | 0.01 | **0.9333** | EXCLU |
| ETH | 3.22 | 1.22 | N/A | Not tested (Batch 1) |
| SOL | 3.25 | 1.10 | **0.7333** | EXCLU |
| AVAX | 2.16 | 0.92 | **0.7333** | EXCLU |

**Hypothèse**: Avec 100 trials, PBO devrait diminuer significativement

## Execution Timeline

| Time | Event |
|------|-------|
| 2026-01-27 13:21:27 UTC | Pipeline started (PID: 215804) |
| 2026-01-27 13:23:00 UTC | Process confirmed active |
| - | Downloading data / initializing |

## ETA

- **4 assets × 100 trials each** = 400 total trials
- **Workers = 1** (sequential)
- **Est. 2-3 hours** total
- **Per asset**: ~30-45 min

## Expected Completion

~2026-01-27 15:30-16:30 UTC

## Monitoring

```bash
# Check progress
python scripts/monitor_challenger.py

# Check terminal output
Get-Content "C:\Users\wybra\.cursor\projects\c-Users-Arthur-friendly-fishstick\terminals\197266.txt" | Select-Object -Last 50

# Check process
Get-Process -Id 215804
```

## Next Steps (Post-Completion)

1. Calculate PBO for 4 assets
2. Compare PBO values: 100 trials vs 300 trials
3. Analyze if hypothesis confirmed (lower PBO)
4. Decide: 
   - If PBO improves → rerun ALL assets with 100 trials
   - If no improvement → investigate other causes (filter modes, regime bias, etc.)

---

**Status**: 🔄 RUNNING
**Last Updated**: 2026-01-27 13:24 UTC
