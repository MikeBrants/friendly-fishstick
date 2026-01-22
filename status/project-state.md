# Project State — FINAL TRIGGER v2

**Dernière mise à jour:** 2026-01-22

## ✅ PROD

Assets validés et en production (7/7 guards passés).

| Asset | Date Validation | Guards | Notes |
|-------|----------------|--------|-------|
| **BTC** | Baseline | 7/7 | Baseline validé (params manuels historiques) |
| **AVAX** | 2026-01-22 | 7/7 | Post-fix validation ✅ |

## ⏳ EN ATTENTE

Assets en attente de validation ou revalidation.

| Asset | Status | Raison |
|-------|--------|--------|
| ETH | ⚠️ A REVALIDER | TP enforced: SUCCESS (OOS Sharpe 3.87, WFE 2.36) but guard002 variance 12.96% |
| SEI | ⚠️ A REVALIDER | TP enforced: OOS Sharpe < 1.0, WFE < 0.6 |
| CAKE (disp=26) | ⚠️ A REVALIDER | SUCCESS (OOS Sharpe 2.73, WFE 0.73) but guard002 variance 20.70% |
| OP (disp=78) | ⚠️ À REVALIDER | Guards OK mais params pré-fix |
| DOGE (disp=26) | ⚠️ À REVALIDER | Guards OK mais params pré-fix |
| DOT, SHIB, NEAR | ⚠️ À REVALIDER | Scan PASS mais pré-fix |
| AR, EGLD, CELO, ANKR | ⚠️ À REVALIDER | Guards PASS mais pré-fix |

## 🚫 BLOCKED

Assets bloqués avec raisons documentées.

| Asset | Date | Raison du blocage | Guards Status |
|-------|------|-------------------|---------------|
| **UNI** | 2026-01-22 | guard002 Sensitivity 10.27% ❌ (dépasse le seuil) + WFE 0.42 ❌ (sous le seuil minimum) | 5/7 PASS |

**Détails UNI:**
- guard001 MC p: ✅ 0.0000
- guard002 Sensitivity: ❌ 10.27% (seuil dépassé)
- guard003 Bootstrap CI: ✅ 1.22
- guard005 Top10: ✅ 26.67%
- guard006 Stress1: ✅ 1.35
- guard007 Regime: ✅ 0.00%
- WFE: ❌ 0.42 (sous le seuil minimum)
- TP Check: ✅ 4.00 < 6.50 < 9.00

**Action requise:** Réoptimisation nécessaire pour améliorer guard002 Sensitivity et WFE.

