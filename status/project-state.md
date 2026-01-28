# PROJECT STATE ? FINAL TRIGGER v2

**Updated**: 28 Jan 2026, 19:15 UTC
**Phase**: ?? v4.3 DUAL WFE GUARDS
**Pipeline**: v4.3 (100 trials, 12000 bars, dual WFE threshold)

---

## ?? RÈGLES DE MISE À JOUR

**OWNER:** Casey ? MAJ après chaque run, max 10 entrées historique

---

## ?? ASSET STATUS

| Status | Count | Assets |
|--------|:-----:|--------|
| ? **PROD v4.3** | **2** | ETH (WFE 2.10, 7/7 guards), DOT (WFE mean 1.71, median 1.02) |
| ?? **BLOCKED v4.3** | **3** | ANKR (WFE median 0.47 < 0.50), SHIB (top10), BTC (WFE mean 0.36) |
| ? PENDING | 13 | SOL, AVAX, AXS, ONE, EGLD, TON, HBAR, SUSHI, CRV, SEI, AAVE, MINA, RUNE |

**Note v4.3**: Dual WFE threshold applied (mean ? 0.60 AND median ? 0.50) for more robust period effect detection.

---

## ?? ETH v4.3 Results

| Métrique | Valeur | Seuil | ? |
|----------|--------|-------|---|
| WFE (mean) | 2.10 | ?0.6 | ? |
| WFE (median) | N/A | ?0.5 | ? |
| OOS Trades | 125 | ?60 | ? |
| Bars | 17520 | ?12000 | ? |
| Sharpe | 1.57 | ?0.80 | ? |
| MaxDD | 6.3% | ?35% | ? |
| PF | 1.39 | ?1.05 | ? |
| Top10 | - | <40% | ? |
| PBO CSCV | 0.58 | <0.70 | ?? |
| Portfolio | PASS | - | ? |

---

## ?? DOT v4.3 Results

| Métrique | Valeur | Seuil | ? |
|----------|--------|-------|---|
| WFE (mean) | 1.71 | ?0.6 | ? |
| WFE (median) | 1.02 | ?0.5 | ? |
| OOS Sharpe | 2.46 | ?0.80 | ? |
| OOS Trades | 139 | ?60 | ? |
| PBO CSCV | 0.58 | <0.70 | ?? |

---

## ?? ANKR v4.3 BLOCKED

| Métrique | Valeur | Seuil | ? |
|----------|--------|-------|---|
| WFE (mean) | 0.65 | ?0.6 | ? |
| WFE (median) | **0.47** | **?0.5** | **? FAIL** |
| OOS Sharpe | 1.89 | ?0.80 | ? |
| OOS Trades | 160 | ?60 | ? |

**Reason**: WFE median < 0.50 indicates period effect or distribution skew

---

## ?? PROCHAINE ACTION

1. ? ETH, DOT PROD v4.3
2. ?? ANKR BLOCKED (WFE median 0.47 < 0.50) - requires rescue or exclusion
3. ? Lancer remaining 13 assets avec v4.3 dual WFE guards
4. ? Analyser impact du dual WFE threshold sur dataset complet

---

## ??? HISTORIQUE RÉCENT

| Date | Action |
|------|--------|
| 28 Jan 19:15 | ?? **v4.3**: Dual WFE threshold (mean?0.60 AND median?0.50) |
| 28 Jan 19:15 | ?? ANKR reclassified: PROD_READY ? BLOCKED (WFE median 0.47) |
| 28 Jan 18:20 | ? DOT PROD_READY (WFE mean 1.71, median 1.02) |
| 28 Jan 15:15 | ?? Batch pilot complete (DOT, SHIB, ANKR, BTC) |
| 28 Jan 14:36 | ? ETH v4.2_pilot_fix03 PROD_READY (7/7 guards) |
| 28 Jan 14:15 | ?? Fix portfolio threshold 500?150 |

---

## ?? FICHIERS

| Fichier | Contenu |
|---------|---------|
| `configs/families.yaml` | Config v4.3 (dual WFE) |
| `configs/router.yaml` | State machine |
| `.cursor/rules/MASTER_PLAN.mdc` | Règles, guards |
| `status/project-state.md` | **CE FICHIER** |

---

## ?? v4.3 DUAL WFE THRESHOLD

**Rationale**: Single WFE (mean) can be skewed by period effects or extreme outliers. Dual threshold:
- **Mean ? 0.60**: Overall walk-forward efficiency
- **Median ? 0.50**: Robust to distribution skew

**Policy**: Both conditions must pass (AND logic)

**Impact**: ANKR filtered out despite mean 0.65 (median 0.47 < 0.50)

**Example**: DOT passes both (mean 1.71, median 1.02)

---

**Version**: 4.3 (28 Jan 2026)
