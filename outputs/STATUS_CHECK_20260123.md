# Status Check - 2026-01-23

## Résumé Exécutif

**Assets PROD:** 12 (BTC, ETH, JOE, OSMO, MINA, AVAX, AR, ANKR, DOGE, OP, DOT, NEAR) ⬆️ +2

**Guards en cours:** 6 assets (DOT, SHIB, NEAR, STRK, METIS, AEVO)

**Problèmes identifiés:**
1. DOT/NEAR: Guards passent mais WFE "n/a" dans les rapports
2. SHIB/STRK/METIS/AEVO: Erreur "complex number" persiste malgré fix timezone
3. UNI: EXCLU (moderate mode FAIL)

---

## Résultats Détaillés

### ✅ DOT - PRODUCTION READY (7/7 Guards PASS)

**Scan (multi_asset_scan_partial.csv, ligne 383):**
- Status: SUCCESS ✅
- OOS Sharpe: **4.58** (>2.0 ✅)
- WFE: **2.58** (>0.6 ✅)
- OOS Trades: 96 (>60 ✅)
- Params: sl=2.5, tp1=5.0, tp2=5.5, tp3=10.0, tenkan=12, kijun=21, displacement=52

**Guards:**
- Guard001 (MC p-value): 0.00 → PASS ✅
- Guard002 (Sensitivity): 3.25% → PASS ✅
- Guard003 (Bootstrap CI): 1.68 → PASS ✅
- Guard005 (Top10 trades): 21.27% → PASS ✅
- Guard006 (Stress1 Sharpe): 1.47 → PASS ✅
- Guard007 (Regime mismatch): 0.00% → PASS ✅
- Guard-WFE: **2.58** → PASS ✅ (WFE trouvé dans scan)

**Verdict:** 🏆 **PRODUCTION READY** - 7/7 guards PASS + WFE 2.58

---

### ✅ NEAR - PRODUCTION READY (7/7 Guards PASS)

**Scan (multi_asset_scan_partial.csv, ligne 389):**
- Status: SUCCESS ✅
- OOS Sharpe: **3.20** (>2.0 ✅)
- WFE: **1.59** (>0.6 ✅)
- OOS Trades: 72 (>60 ✅)
- Params: sl=5.0, tp1=3.25, tp2=9.0, tp3=9.5, tenkan=8, kijun=32, displacement=52

**Guards:**
- Guard001 (MC p-value): 0.003 → PASS ✅
- Guard002 (Sensitivity): 9.84% → PASS ✅ (<10%)
- Guard003 (Bootstrap CI): 1.11 → PASS ✅
- Guard005 (Top10 trades): 26.68% → PASS ✅
- Guard006 (Stress1 Sharpe): 1.43 → PASS ✅
- Guard007 (Regime mismatch): 0.00% → PASS ✅
- Guard-WFE: **1.59** → PASS ✅ (WFE trouvé dans scan)

**Verdict:** 🏆 **PRODUCTION READY** - 7/7 guards PASS + WFE 1.59

---

### ⚠️ SHIB - Scan SUCCESS mais Guards FAIL (Complex Number Error)

**Scan (multi_asset_scan_partial.csv, ligne 390):**
- Status: SUCCESS ✅
- OOS Sharpe: **5.88** (excellent, >2.0 ✅)
- WFE: **2.42** (>0.6 ✅)
- OOS Trades: 96 (>60 ✅)
- Params: sl=1.5, tp1=4.75, tp2=6.0, tp3=8.0, tenkan=19, kijun=25, displacement=52

**Guards:**
- **Erreur:** `float() argument must be a string or a real number, not 'complex'`
- **Status:** Guards échouent à cause de l'erreur technique
- **Fix timezone appliqué mais erreur persiste**

**Verdict:** ⚠️ Scan excellent mais guards bloqués par bug technique. Investigation requise.

---

### ❌ STRK, METIS, AEVO - Erreur Complex Number

**Même erreur que SHIB:** `float() argument must be a string or a real number, not 'complex'`

**Scans (selon project-state.md):**
- STRK: OOS Sharpe 1.27, WFE 0.85 ✅
- METIS: OOS Sharpe 2.89, WFE 0.85 ✅
- AEVO: OOS Sharpe 1.23, WFE 0.62 ✅

**Action requise:** Fix timezone n'a pas résolu le problème - investigation requise

---

### ❌ UNI - EXCLU

**Moderate mode FAIL:**
- OOS Sharpe: -0.83 (< 1.0)
- WFE: 0.01 (< 0.6)
- Guard002 variance: 35.33% (> 10%)
- Guard003 CI: -1.14 (< 1.0)
- Guard005 Top10: 113.36% (> 40%) - **ANOMALIE**

**Verdict:** Variants épuisés — EXCLU définitivement

---

## Actions Prioritaires

### P0 (Urgent)

1. ✅ **DOT/NEAR ajoutés en PROD** — WFE vérifiés (2.58 et 1.59)
   - Mettre à jour `project-state.md` et `asset_config.py`
   - DOT: 7/7 guards PASS + WFE 2.58
   - NEAR: 7/7 guards PASS + WFE 1.59

2. **Investigation bug complex number (SHIB, STRK, METIS, AEVO)**
   - Vérifier où l'erreur se produit exactement
   - Le fix timezone n'a pas résolu le problème
   - Peut-être dans les calculs de guards (bootstrap, monte carlo?)
   - SHIB a un excellent scan (Sharpe 5.88, WFE 2.42) mais bloqué par le bug

### P1

3. **YGG investigation** — complex number error persistant
4. **HBAR variants** — tester d26, d78 si disponible

---

## Fichiers à Vérifier

- `outputs/multiasset_scan_20260123_065153.csv` — WFE DOT/NEAR
- `scripts/run_guards_multiasset.py` — Où se produit l'erreur complex number
- `crypto_backtest/optimization/parallel_optimizer.py` — Fix timezone appliqué

---

**Date:** 2026-01-23  
**Auteur:** @Jordan  
**Prochaine action:** Vérifier WFE DOT/NEAR dans scan CSV
