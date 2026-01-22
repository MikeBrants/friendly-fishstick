# Communication - Casey (Quant Orchestrator)

## Messages Actifs

### [22:30] [ASSIGNATION] @Casey -> @Jordan

**Priorite P0:**

1. **AVAX + UNI** — Download data puis rerun medium_distance_volume
   ```bash
   python scripts/download_data.py --assets AVAX UNI
   python scripts/run_full_pipeline.py \
     --assets AVAX UNI \
     --workers 6 \
     --trials-atr 150 \
     --trials-ichi 150 \
     --enforce-tp-progression \
     --optimization-mode medium_distance_volume \
     --run-guards
   ```

2. **HBAR** — Filter grid pour reduire sensitivity (13% -> <10%)
   ```bash
   python scripts/run_filter_grid.py --asset HBAR
   ```

**Status attendu:** Resultats scan + guards dans comms/jordan-dev.md

---

### [22:00] [VERDICT] @Casey

| Asset | Status | Rationale |
|-------|--------|-----------|
| ICP | EXCLU | Overfitting severe (OOS Sharpe -1.04, WFE -0.13) |
| HBAR | PENDING | Scan OK, guards 5/7 (sens 13%, stress1 0.72) |
| ARKM | EXCLU | OOS Sharpe -0.93, WFE 0.39 |
| YGG | EXCLU | WFE 0.56 < 0.6 |
| CELO | EXCLU | OOS Sharpe 0.48, WFE 0.23 |
| AR | PENDING | Excellent metrics mais trades 47 < 50 |

**Action:** @Jordan tester AR avec plus de trials ou timeframe plus long

---

***

## Archive

### [21:33] AVAX/UNI rerun — BLOCKER data manquante
- Pipeline echoue avec "No data found for AVAX/UNI in data"
- Resolution: executer download_data.py avant pipeline
