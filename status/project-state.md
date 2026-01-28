# FINAL TRIGGER v2 — Project State

**Last Updated:** 2026-01-28
**Pipeline Version:** v4.3
**Status:** ? OPERATIONAL

***

## ?? Current State

### Pipeline v4.3 — Complete

| Component | Status | Notes |
|:----------|:------:|:------|
| `configs/families.yaml` | ? | Policy v4.3 + polish_oos |
| `configs/router.yaml` | ? | POLISH_OOS state + transitions |
| `scripts/regime_stats.py` | ? | Side-aware + z-score + stability |
| `scripts/polish_oos.py` | ? | Sign test 8/10, M=5 candidates |
| `scripts/guards.py` | ? | + lookahead guard |
| `scripts/artifacts.py` | ? | v4_3 paths centralisés |
| `scripts/state_machine.py` | ? | Support legacy + new schema |
| `scripts/orchestrator_v4_3.py` | ? | All handlers wired |
| `scripts/checklist_v4_3.py` | ? | Audit tool |
| `scripts/generate_mock_data.py` | ? | End-to-end test data |

### v4.3 Key Features

1. **Polish OOS** — Compare A vs A+Gate(B) on CSCV folds before upgrade
2. **Side-Aware Regime** — ?_long and ?_short calculated separately
3. **Z-Score Validation** — Statistical significance (z = 1.65)
4. **Stability Windows** — 3/4 windows must show same pattern
5. **Lookahead Guard** — Detect regime lookahead bias

### Anti-Overfit Measures v4.3

| Rule | Threshold | Purpose |
|:-----|:----------|:--------|
| Sign test | 8/10 folds | Statistical significance |
| M candidates | 5, =3 agree | Robustness |
| Effect size | ? Sharpe = 0.05 | No DOF for marginal gain |
| Stability | 3/4 windows | Not temporal artifact |
| n per bucket | =80 trades | Sufficient data |

***

## ?? Run History

| Date | Asset | Run ID | Family | Result | Notes |
|:-----|:------|:-------|:------:|:------:|:------|
| 2026-01-28 | ETH | v4.3_test | A | DRY-RUN | Pipeline validation |

***

## ?? Commands

```bash
# Dry run
python scripts/orchestrator_v4_3.py --asset ETH --run-id v4.3_001 --dry-run

# Generate mock data
python scripts/generate_mock_data.py --asset ETH --run-id mock_001

# Full run with mock data
python scripts/generate_mock_data.py --asset ETH --run-id v4.3_001
python scripts/orchestrator_v4_3.py --asset ETH --run-id v4.3_001

# Checklist audit
python scripts/checklist_v4_3.py --asset ETH --run-id v4.3_001

# Run tests
pytest scripts/tests/test_v4_3_integration.py -v
```

***

## ?? Artifacts Structure

```
runs/v4_3/<ASSET>/<RUN_ID>/
+-- screening/
¦   +-- screen_long.json
¦   +-- screen_short.json
+-- coupling/
¦   +-- coupled_candidates.json
+-- baseline/
¦   +-- baseline_best.json
¦   +-- trades.parquet
¦   +-- ohlcv.parquet
+-- regime/
¦   +-- regime_stats.json
+-- polish_oos/
¦   +-- decision.json
+-- guards/
¦   +-- guards.json
+-- pbo/
¦   +-- pbo_proxy.json
¦   +-- pbo_cscv.json
¦   +-- cscv_folds.json
+-- portfolio/
¦   +-- portfolio.json
+-- archive/
    +-- summary.json
```

***

## ?? Agent Ownership

| Agent | Files | Responsibility |
|:------|:------|:---------------|
| **Casey** | `project-state.md` | State tracking, orchestration |
| **Alex** | `families.yaml`, `MASTER_PLAN.mdc` | Quant rules, thresholds |
| **Jordan** | `scripts/*.py` | Implementation |
| **Sam** | `tests/*.py`, `guards.py` | QA, validation |

***

## ?? Next Actions

1. [ ] Run full pipeline on real ETH data
2. [ ] Validate Polish OOS activation rate (target: 10-30%)
3. [ ] Backtest comparison v4.2 vs v4.3
4. [ ] Enable holdout (10%) for gold standard
