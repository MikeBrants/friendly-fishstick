# PROJECT STATE — FINAL TRIGGER v2

**Updated**: 28 Jan 2026, 10:39 UTC
**Phase**: 🆕 v4.2 FRESH START
**Pipeline**: v4.2 (100 trials, 12000 bars, calibrated CSCV PBO)

> **Source of Truth:** This file reflects the current state
> **Commands:** See `docs/WORKFLOW_PIPELINE.md`
> **Params:** See `.cursor/rules/MASTER_PLAN.mdc`

---

## 📊 ASSET STATUS

| Status | Count | Assets |
|--------|:-----:|--------|
| ⏳ PENDING | 18 | All assets to reprocess with v4.2 |
| �
 PROD | 0 | - |
| 🔴 EXCLU | 0 | - |

### Assets à Traiter (18)

**Tier 1 Priority (8):**
```
BTC SOL AVAX AXS DOT SHIB ANKR
```

**Tier 2 Secondary (10):**
```
ONE EGLD TON HBAR SUSHI CRV SEI AAVE MINA RUNE
```

---

## 🎯 v4.2 PIPELINE OVERVIEW

### Key Changes from v4.1

| Feature | v4.1 | v4.2 |
|---------|:----:|:----:|
| Trials | 300 | **100** |
| Min Bars | 8000 | **12000** |
| PBO Method | Standard | **CSCV** |
| Config System | Hardcoded | **YAML families** |
| Reproducibility | Issues | **Verified** |

### Pipeline Phases

```
Phase 0: Data Download (12000+ bars)
  ↓
Phase 1: Screening (100 trials, seed 42)
  ↓
Phase 2: Guards Validation (7 hard guards + PBO CSCV)
  ↓
Phase 3: Regime Stress (SIDEWAYS Sharpe > 0)
  ↓
Phase 4: Portfolio Correlation (< 0.5)
  ↓
Phase 5: Production Config (asset_config.py)
```

### Success Criteria

| Guard | Threshold | Critical |
|-------|:---------:|:--------:|
| PBO CSCV | < 0.50 | �
 |
| WFE Pardo | > 0.60 | �
 |
| Sensitivity | < 15% | �
 |
| Bootstrap CI | > 1.0 | �
 |
| Monte Carlo | p < 0.05 | �
 |
| Top10 Trades | < 40% | �
 |
| Min Trades OOS | ≥ 60 | �
 |

---

## 🎯 PROCHAINE ACTION

1. 🟡 **Pilot ETH** — Validate complete pipeline
2. ⏳ Batch Tier 1 (7 assets) — After ETH validation
3. ⏳ Batch Tier 2 (10 assets) — After Tier 1 complete
4. ⏳ Portfolio Assembly — Cross-correlation check

### Commands

```bash
# Step 1: Pilot ETH
python scripts/orchestrator_v4_2.py --asset ETH --run-id pilot_eth

# Step 2: Batch Tier 1
python scripts/orchestrator_v4_2.py \
  --assets BTC SOL AVAX AXS DOT SHIB ANKR \
  --run-id tier1_batch

# Step 3: Guards + PBO
python scripts/run_guards_v4_2.py --run-id pilot_eth
python scripts/pbo_v4_2.py --run-id pilot_eth
```

---

## 🗓️ HISTORIQUE

| Date | Action |
|------|--------|
| 28 Jan 14:00 | 🆕 v4.2 Pipeline deployed — FRESH START |
| 28 Jan 13:15 | v4.1 finalized — 5 PROD assets (ETH/AVAX/SOL/YGG/AXS) |
| 28 Jan 10:30 | PR#21 complete — 100T validation successful |
| 27 Jan 19:23 | Plan A SUCCESS — Challenger recovers SOL/AVAX |

---

## 📁 KEY FILES

| File | Purpose |
|------|---------|
| `status/project-state.md` | **This file** — Current state |
| `configs/families.yaml` | Asset family configurations |
| `configs/router.yaml` | Family routing rules |
| `crypto_backtest/v4/screening.py` | v4.2 screening engine |
| `scripts/orchestrator_v4_2.py` | Main pipeline orchestrator |
| `scripts/pbo_v4_2.py` | CSCV PBO calculator |

---

## 🤖 AGENTS

| Agent | Focus |
|-------|-------|
| **Casey** | Orchestration, priorities |
| **Jordan** | Pipeline execution |
| **Sam** | Guards validation |
| **Alex** | Architecture, params |

---

**Version**: 4.2.0 (28 Jan 2026)
**Status**: READY FOR TIER 1 BATCH
