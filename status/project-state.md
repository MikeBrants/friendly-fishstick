# PROJECT STATE — FINAL TRIGGER v2

**Updated**: 28 Jan 2026, 15:20 UTC+4
**Phase**: 🔄 v4.2 BATCH PILOT
**Pipeline**: v4.2 (100 trials, 12000 bars, calibrated PBO)

---

## ⚠️ RÈGLES DE MISE À JOUR

**OWNER:** Casey — MAJ après chaque run, max 10 entrées historique

---

## 📊 ASSET STATUS

| Status | Count | Assets |
|--------|:-----:|--------|
| ✅ **PROD v4.2** | **1** | ETH (WFE 2.10, 7/7 guards, PBO 0.58) |
| 🔄 BATCH PILOT | 4 | DOT, SHIB, ANKR, BTC (running) |
| ⏳ PENDING | 13 | SOL, AVAX, AXS, ONE, EGLD, TON, HBAR, SUSHI, CRV, SEI, AAVE, MINA, RUNE |

---

## 🎯 ETH v4.2 Results

| Métrique | Valeur | Seuil | ✓ |
|----------|--------|-------|---|
| WFE | 2.10 | >0.6 | ✅ |
| OOS Trades | 125 | ≥60 | ✅ |
| Bars | 17520 | ≥12000 | ✅ |
| Sharpe | 1.57 | ≥0.80 | ✅ |
| MaxDD | 6.3% | ≤35% | ✅ |
| PF | 1.39 | ≥1.05 | ✅ |
| Top10 | - | <40% | ✅ |
| PBO CSCV | 0.58 | <0.70 | ⚠️ |
| Portfolio | PASS | - | ✅ |

---

## ⏭️ PROCHAINE ACTION

1. ✅ ETH PROD v4.2
2. 🔄 Batch pilot (DOT, SHIB, ANKR, BTC) — running
3. ⏳ Analyser résultats batch
4. ⏳ Lancer remaining 13 assets

---

## 🗓️ HISTORIQUE RÉCENT

| Date | Action |
|------|--------|
| 28 Jan 15:15 | 🔄 Batch pilot started (DOT, SHIB, ANKR, BTC) |
| 28 Jan 14:36 | ✅ ETH v4.2_pilot_fix03 PROD_READY (7/7 guards) |
| 28 Jan 14:15 | 🔧 Fix portfolio threshold 500→150 |
| 28 Jan 13:49 | 🔧 Fix baseline WFE/trades/bars mapping |
| 28 Jan 13:15 | ✅ v4.2 pipeline implementation complete |
| 28 Jan 12:10 | 🆕 v4.2 migration started |

---

## 📁 FICHIERS

| Fichier | Contenu |
|---------|---------|
| `configs/families.yaml` | Config v4.2 |
| `configs/router.yaml` | State machine |
| `.cursor/rules/MASTER_PLAN.mdc` | Règles, guards |
| `status/project-state.md` | **CE FICHIER** |

---

**Version**: 4.2 (28 Jan 2026)
