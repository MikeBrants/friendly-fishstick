# Jordan (Developer) — Task Log

**Last Updated:** 25 janvier 2026, 02:05 UTC  
**Status:** 🔴 NEW ASSIGNMENT — TIA/CAKE Update

---

## 🚨 P0 ASSIGNMENT — TIA/CAKE Asset Config Update

**From:** Casey (Orchestrator)  
**Date:** 25 janvier 2026, 02:00 UTC  
**Priority:** P0 (immediate)

### TASK SUMMARY

**Update `crypto_backtest/config/asset_config.py` for TIA and CAKE:**
- Reclassify from "Phase 4 rescue" to "Phase 2 PASS baseline"
- Use Phase 2 baseline optimization params (NOT Phase 4)
- Displacement: d52 (baseline)
- Filter Mode: baseline (no filters)

### CONTEXT

**PR#8 Impact:** Guard002 threshold updated 10% → 15%

**TIA:**
- Variance: 11.49% → PASS avec seuil 15%
- Phase 2 baseline: 7/7 guards PASS
- Phase 4 rescue était un false positive (seuil 10%)

**CAKE:**
- Variance: 10.76% → PASS avec seuil 15%
- Phase 2 baseline: 7/7 guards PASS
- Phase 4 rescue était un false positive (seuil 10%)

**Référence:** `TIA_CAKE_RECLASSIFICATION.md`

---

## 📋 TASK DETAILS

### 1. Locate Phase 2 Baseline Results

**Find original scan results:**
```bash
# Look for Phase 2 baseline scan with TIA/CAKE
ls -la outputs/multiasset_scan_*20260124*.csv
grep -E "TIA|CAKE" outputs/multiasset_scan_*.csv
```

**Expected columns:**
- asset, oos_sharpe, wfe, displacement, optimization_mode
- ATR params: sl_mult, tp1_mult, tp2_mult, tp3_mult
- Ichimoku params: tenkan, kijun
- Guard002: variance_pct (should be ~11.49% for TIA, ~10.76% for CAKE)

### 2. Extract Baseline Parameters

**TIA Phase 2 Baseline:**
```python
"TIA": {
    # Meta
    "displacement": 52,
    "optimization_mode": "baseline",
    "phase": "Phase 2 PASS",
    "validated_date": "2026-01-24",
    
    # Performance
    "oos_sharpe": [EXTRACT_FROM_SCAN],
    "wfe": [EXTRACT_FROM_SCAN],
    "variance_pct": 11.49,
    
    # ATR Params (Phase 2 baseline)
    "sl_mult": [EXTRACT],
    "tp1_mult": [EXTRACT],
    "tp2_mult": [EXTRACT],
    "tp3_mult": [EXTRACT],
    
    # Ichimoku Params (Phase 2 baseline)
    "tenkan": [EXTRACT],
    "kijun": [EXTRACT],
    
    # Filters (baseline = all OFF)
    "use_mama_kama_filter": False,
    "use_distance_filter": False,
    "use_volume_filter": False,
    "use_reg_cloud_filter": False,
    "use_kama_filter": False,
    "ichi5in1_strict": False,
}
```

**CAKE Phase 2 Baseline:**
```python
"CAKE": {
    # Meta
    "displacement": 52,
    "optimization_mode": "baseline",
    "phase": "Phase 2 PASS",
    "validated_date": "2026-01-24",
    
    # Performance
    "oos_sharpe": [EXTRACT_FROM_SCAN],
    "wfe": [EXTRACT_FROM_SCAN],
    "variance_pct": 10.76,
    
    # ATR Params (Phase 2 baseline)
    "sl_mult": [EXTRACT],
    "tp1_mult": [EXTRACT],
    "tp2_mult": [EXTRACT],
    "tp3_mult": [EXTRACT],
    
    # Ichimoku Params (Phase 2 baseline)
    "tenkan": [EXTRACT],
    "kijun": [EXTRACT],
    
    # Filters (baseline = all OFF)
    "use_mama_kama_filter": False,
    "use_distance_filter": False,
    "use_volume_filter": False,
    "use_reg_cloud_filter": False,
    "use_kama_filter": False,
    "ichi5in1_strict": False,
}
```

### 3. Update asset_config.py

**File:** `crypto_backtest/config/asset_config.py`

**Action:**
1. Locate TIA and CAKE entries
2. Replace with Phase 2 baseline params (above)
3. Remove any Phase 4 rescue references
4. Add comment: `# Reclassified from Phase 4 to Phase 2 post-PR#8 (guard002 threshold 15%)`

### 4. Validate Changes

**Checklist:**
- [ ] TIA displacement = 52
- [ ] CAKE displacement = 52
- [ ] optimization_mode = "baseline" (NOT filter mode)
- [ ] All filter flags = False
- [ ] variance_pct matches (11.49%, 10.76%)
- [ ] ATR params from Phase 2 scan
- [ ] Ichimoku params from Phase 2 scan

---

## 🔧 COMMANDS REFERENCE

### Locate Phase 2 Results
```bash
# Find Phase 2 scan with TIA/CAKE
cd outputs
grep -l "TIA\|CAKE" multiasset_scan_*20260124*.csv | head -5

# Extract TIA params
grep "TIA" multiasset_scan_[TIMESTAMP].csv

# Extract CAKE params
grep "CAKE" multiasset_scan_[TIMESTAMP].csv
```

### Validate asset_config.py
```python
# Test import
from crypto_backtest.config.asset_config import ASSET_CONFIGS

# Check TIA
print(ASSET_CONFIGS["TIA"]["displacement"])  # Should be 52
print(ASSET_CONFIGS["TIA"]["optimization_mode"])  # Should be "baseline"

# Check CAKE
print(ASSET_CONFIGS["CAKE"]["displacement"])  # Should be 52
print(ASSET_CONFIGS["CAKE"]["optimization_mode"])  # Should be "baseline"
```

---

## 📊 EXPECTED OUTCOME

**Before (Phase 4 rescue):**
```python
"TIA": {
    "optimization_mode": "medium_distance_volume",  # Phase 4
    "use_distance_filter": True,
    "use_volume_filter": True,
    # ...
}
```

**After (Phase 2 baseline):**
```python
"TIA": {
    "optimization_mode": "baseline",  # Phase 2
    "use_distance_filter": False,
    "use_volume_filter": False,
    "variance_pct": 11.49,  # PASS with 15% threshold
    # ...
}
```

---

## ✅ COMPLETION CRITERIA

**Task Complete When:**
1. ✅ Phase 2 baseline results located
2. ✅ TIA params extracted and updated
3. ✅ CAKE params extracted and updated
4. ✅ asset_config.py modified and saved
5. ✅ Import validation passes
6. ✅ Commit pushed with message: `fix(asset-config): reclassify TIA/CAKE to Phase 2 baseline post-PR#8`

**Notify:**
- Casey: Task complete
- Sam: Ready for validation

---

## 📁 REFERENCE

**Documents:**
- `TIA_CAKE_RECLASSIFICATION.md` — Full context
- `comms/casey-quant.md` — Assignment details
- `PR8_COMPLETE_SUMMARY.md` — PR#8 background

**Files to Modify:**
- `crypto_backtest/config/asset_config.py` (primary)

**Files to Reference:**
- `outputs/multiasset_scan_*20260124*.csv` (Phase 2 results)
- `outputs/phase2_guards_backfill_summary_20260124.csv` (guards validation)

---

## 🎯 NEXT STEPS

1. **Immediate:** Extract Phase 2 params from scan CSV
2. **Update:** Modify asset_config.py
3. **Validate:** Test import and params
4. **Commit:** Push changes with clear message
5. **Notify:** Casey + Sam (ready for validation)

---

**Status:** 🔴 ASSIGNED — AWAITING EXECUTION  
**Priority:** P0 (blocking portfolio construction)  
**ETA:** ASAP (within 1 hour)
