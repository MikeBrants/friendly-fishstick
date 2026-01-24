# COMMANDS — Guards Backfill pour 7 Assets Pending

**Date:** 24 janvier 2026, 19:40 UTC  
**Owner:** Jordan/Casey  
**Validator:** Sam

---

## 🎯 OBJECTIF

Exécuter les guards sur 7 assets qui ont passé Phase 1 Overnight mais dont les guards n'ont pas été générés.

---

## 📋 ASSETS À TRAITER (7)

| Asset | OOS Sharpe | WFE | Trades | Probabilité PASS |
|:------|:-----------|:----|:-------|:-----------------|
| **TIA** 🚀 | 5.16 | 1.36 | 75 | **TRÈS HAUTE** |
| **TON** | 2.54 | 1.17 | 69 | **HAUTE** |
| **CAKE** | 2.46 | 0.81 | 90 | **HAUTE** |
| **HBAR** | 2.32 | 1.03 | 114 | **HAUTE** |
| **RUNE** | 2.42 | 0.61 | 102 | **MOYENNE** |
| **EGLD** | 2.04 | 0.66 | 90 | **MOYENNE** |
| **SUSHI** | 1.90 | 0.63 | 105 | **MOYENNE** |

**Note:** CRV exclu (Sharpe 1.01 < seuil 1.0)

---

## 🚀 COMMANDE PRINCIPALE

### Option 1: Script Guards Multiasset (RECOMMANDÉ)

```bash
python scripts/run_guards_multiasset.py \
  --assets TIA HBAR CAKE TON RUNE EGLD SUSHI \
  --workers 1 \
  --output-prefix phase2_guards_backfill_20260124
```

**Durée estimée:** ~2 heures (7 assets × ~17 min)

**Outputs attendus:**
```
outputs/phase2_guards_backfill_20260124_TIA_guards_summary.csv
outputs/phase2_guards_backfill_20260124_HBAR_guards_summary.csv
outputs/phase2_guards_backfill_20260124_CAKE_guards_summary.csv
outputs/phase2_guards_backfill_20260124_TON_guards_summary.csv
outputs/phase2_guards_backfill_20260124_RUNE_guards_summary.csv
outputs/phase2_guards_backfill_20260124_EGLD_guards_summary.csv
outputs/phase2_guards_backfill_20260124_SUSHI_guards_summary.csv
```

---

### Option 2: Run Full Pipeline (SI SCRIPT GUARDS N'EXISTE PAS)

**Pour chaque asset:**

```bash
python scripts/run_full_pipeline.py \
  --assets [ASSET] \
  --workers 1 \
  --trials-atr 300 \
  --trials-ichi 300 \
  --enforce-tp-progression \
  --run-guards \
  --skip-optimization \
  --output-prefix phase2_guards_backfill_[ASSET]
```

**Note:** `--skip-optimization` utilise les params déjà optimisés (depuis scan Phase 1)

**Commandes complètes:**

```bash
# TIA (P0 - le plus prometteur)
python scripts/run_full_pipeline.py --assets TIA --workers 1 --trials-atr 300 --trials-ichi 300 --enforce-tp-progression --run-guards --skip-optimization --output-prefix phase2_guards_backfill_TIA

# HBAR (P0)
python scripts/run_full_pipeline.py --assets HBAR --workers 1 --trials-atr 300 --trials-ichi 300 --enforce-tp-progression --run-guards --skip-optimization --output-prefix phase2_guards_backfill_HBAR

# TON (P0)
python scripts/run_full_pipeline.py --assets TON --workers 1 --trials-atr 300 --trials-ichi 300 --enforce-tp-progression --run-guards --skip-optimization --output-prefix phase2_guards_backfill_TON

# CAKE (P1)
python scripts/run_full_pipeline.py --assets CAKE --workers 1 --trials-atr 300 --trials-ichi 300 --enforce-tp-progression --run-guards --skip-optimization --output-prefix phase2_guards_backfill_CAKE

# RUNE (P1)
python scripts/run_full_pipeline.py --assets RUNE --workers 1 --trials-atr 300 --trials-ichi 300 --enforce-tp-progression --run-guards --skip-optimization --output-prefix phase2_guards_backfill_RUNE

# EGLD (P1)
python scripts/run_full_pipeline.py --assets EGLD --workers 1 --trials-atr 300 --trials-ichi 300 --enforce-tp-progression --run-guards --skip-optimization --output-prefix phase2_guards_backfill_EGLD

# SUSHI (P2)
python scripts/run_full_pipeline.py --assets SUSHI --workers 1 --trials-atr 300 --trials-ichi 300 --enforce-tp-progression --run-guards --skip-optimization --output-prefix phase2_guards_backfill_SUSHI
```

---

## 📊 EXPECTED RESULTS

### Scénario Conservateur (50% PASS)
**3-4 assets PASS:**
- TIA, TON, CAKE, HBAR (haute probabilité)
- **Total PROD:** 11-12 assets

### Scénario Réaliste (60% PASS)
**4-5 assets PASS:**
- TIA, TON, CAKE, HBAR, RUNE (moyenne/haute probabilité)
- **Total PROD:** 12-13 assets

### Scénario Optimiste (80% PASS)
**5-6 assets PASS:**
- TIA, TON, CAKE, HBAR, RUNE, EGLD (tous sauf SUSHI)
- **Total PROD:** 13-14 assets

---

## ⚠️ NOTES IMPORTANTES

1. **Workers = 1 OBLIGATOIRE** (reproducibilité scientifique)
2. **CRV exclu** (Sharpe 1.01 < seuil minimum 1.0)
3. **Ordre suggéré:** TIA → TON → HBAR → CAKE → RUNE → EGLD → SUSHI (par probabilité PASS)
4. **Early stop possible:** Si TIA/TON/HBAR passent, objectif 11+ atteint

---

## 📁 VALIDATION SAM (POST-GUARDS)

**Dès guards disponibles, Sam validera:**

1. ✅ 7/7 guards PASS
2. ✅ OOS Sharpe > 1.0
3. ✅ OOS Trades > 60
4. ✅ TP progression (TP1 < TP2 < TP3, gaps ≥ 0.5)
5. ✅ Date post-fix (> 2026-01-22 12H00)
6. ✅ Pas de Sharpe suspect (< 6.0)

**Verdict par asset:** PROD ou BLOCKED  
**Documentation:** `comms/sam-qa.md`  
**Recommandation finale:** À Casey pour `status/project-state.md`

---

## 🎯 SUCCESS CRITERIA

- [ ] 7 guards exécutés (fichiers CSV générés)
- [ ] Sam validation complète (7 assets analysés)
- [ ] 3-5 assets PASS guards → 11-13 total PROD
- [ ] Documentation complète dans `comms/sam-qa.md`
- [ ] Mise à jour `status/project-state.md` avec nouveaux assets PROD

**ETA Completion:** 22h-23h UTC (si lancé à 20h)

---

**Préparé par:** Sam  
**Approuvé par:** (en attente Casey)  
**Exécution:** (en attente Jordan)
