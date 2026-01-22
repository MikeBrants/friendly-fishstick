## [21:33] [RUN] @Jordan -> @Sam

**Assets:** AVAX, UNI

**Mode:** medium_distance_volume

**Displacement:** auto (Optuna)

**Command:** python scripts/run_full_pipeline.py --assets AVAX UNI --workers 6 --trials-atr 150 --trials-ichi 150 --enforce-tp-progression --optimization-mode medium_distance_volume --skip-download --run-guards

**Status:** Failed ❌

**Outputs:**
- Scan: outputs/multiasset_scan_20260122_213336.csv
- Guards: outputs/multiasset_guards_summary_20260122_213339.csv

**Quick Results:**

| Asset | OOS Sharpe | WFE | Trades | TP Valid |
|-------|------------|-----|--------|----------|
| AVAX | 0.00 | 0.00 | 0 | ❌ |
| UNI | 0.00 | 0.00 | 0 | ❌ |

**Error:** Both assets failed with "No data found for AVAX/UNI in data". The pipeline ran with `--skip-download` but the data files are missing from the data directory.

**Next:** @Sam - Data files for AVAX and UNI need to be downloaded before running the pipeline. Should I run without `--skip-download` to fetch the data first?

