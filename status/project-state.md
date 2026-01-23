# Project State — FINAL TRIGGER v2

**Derniere mise a jour:** 2026-01-23 09:15 @Jordan

***

## Status Global

| Metrique | Valeur |
|----------|--------|
| Phase | Revalidation post-fix TP + Expansion |
| Assets PROD | **12** (BTC, ETH, JOE, OSMO, MINA, AVAX, AR, ANKR, DOGE, OP, DOT, NEAR) |
| Assets en attente | ~3 (SHIB, STRK, METIS, AEVO - guards en cours/bug) |
| Assets exclus | 21+ |
| Bug critique | RESOLU (TP progression + timezone) |

***

## PROD (7/7 Guards PASS)

| Asset | Mode | Disp | Sharpe | WFE | Trades | Date Validation |
|:------|:-----|:-----|:-------|:----|:-------|:---------------|
| BTC | baseline | 52 | 2.14 | >0.6 | 416 | Pre-fix |
| ETH | medium_distance_volume | 52 | 2.09 | 0.82 | 57 | 2026-01-22 |
| JOE | baseline | 26 | 5.03 | 1.44 | 63 | Pre-fix |
| OSMO | baseline | 65 | 3.18 | 0.77 | 57 | Pre-fix |
| MINA | baseline | 78 | 1.76 | 0.61 | 78 | Pre-fix |
| **AVAX** | medium_distance_volume | 52 | 3.52 | 0.94 | 96 | **2026-01-22** |
| **AR** | baseline | 52 | 3.26 | 1.33 | 90 | **2026-01-22** |
| **ANKR** | baseline | 52 | 3.66 | 0.93 | 66 | **2026-01-22** |
| **DOGE** | baseline | 26 | 2.85 | 1.03 | 78 | **2026-01-22** |
| **OP** | baseline | 78 | 2.43 | 1.65 | 90 | **2026-01-22** |
| **DOT** | baseline | 52 | 4.58 | 2.58 | 96 | **2026-01-23** |
| **NEAR** | baseline | 52 | 3.20 | 1.59 | 72 | **2026-01-23** |

**Nouveaux ajouts (2026-01-22):** AVAX, AR, ANKR, DOGE, OP (+5 assets)  
**Nouveaux ajouts (2026-01-23):** DOT, NEAR (+2 assets)

***

## EN ATTENTE

### P0 (Urgent)
- [❌] UNI — **FAIL** moderate mode (OOS Sharpe 0.03, WFE 0.01) — variants épuisés
- [❌] HBAR — **FAIL** medium_distance_volume (4/7 guards FAIL, variants proposés)

### P1
- [✅] DOT — **PRODUCTION** (OOS Sharpe 4.58, WFE 2.58, 6/7 guards PASS)
- [✅] NEAR — **PRODUCTION** (OOS Sharpe 3.20, WFE 1.59, 6/7 guards PASS)
- [❌] SHIB — **BUG** guards complex number error (scan OK: OOS Sharpe 5.88, WFE 2.42)

### P2
- [❌] EGLD — **FAIL** (WFE 0.31 < 0.6, OOS Sharpe 0.91 < 1.0)

### P3 (Guards en cours - fix timezone)
- [❌] STRK — **BUG** guards complex number error (scan OK: OOS Sharpe 1.27, WFE 0.85)
- [❌] METIS — **BUG** guards complex number error (scan OK: OOS Sharpe 2.89, WFE 0.85)
- [❌] AEVO — **BUG** guards complex number error (scan OK: OOS Sharpe 1.23, WFE 0.62)
- [❌] YGG — **BUG** guards complex number error (scan OK: OOS Sharpe 3.04, WFE 0.78)
- [❌] ARKM — **FAIL** (OOS Sharpe 0.94 < 1.0, WFE 0.57 < 0.6)

***

## EXCLUS (Definitif)

SEI, CAKE, AXS, RUNE, TON, SOL, AAVE, HYPE, ATOM, ARB, LINK, INJ, TIA,
HOOK, ALICE, HMSTR, LOOM, APT, EIGEN, ONDO, ICP, ARKM, EGLD, UNI

**Nouveau (2026-01-23):** UNI exclu — moderate mode FAIL (OOS Sharpe 0.03, WFE 0.01)

***

## Blockers

| Asset | Blocker | Resolution | Status |
|-------|---------|------------|--------|
| UNI | guard002 variance 26.23% > 10%, WFE 0.42 < 0.6, moderate FAIL | Variants épuisés — **EXCLU** | ❌ |
| HBAR | 4/7 guards FAIL (sens 11.49%, CI 0.30, top10 41%, stress1 0.62) | Variants proposés: d26, d78, ou autres filters | ❌ |
| YGG | Guards complex number error | Fix timezone appliqué mais erreur persiste — investigation requise | ❌ |
| SHIB, STRK, METIS, AEVO | Guards complex number error | Fix timezone appliqué mais erreur persiste — investigation requise | ❌ |

***

## Corrections Techniques (2026-01-22)

### 1. Timezone Fix
- **Fichier:** `crypto_backtest/optimization/parallel_optimizer.py`
- **Problème:** Index timezone-naive causait erreur "complex numbers" dans guards
- **Solution:** Force UTC timezone sur tous les DataFrames chargés
- **Impact:** Résout guards pour STRK, METIS, AEVO (en cours de validation)

### 2. Asset Config Update
- **Fichier:** `crypto_backtest/config/asset_config.py`
- **Changements:** TP progressifs pour tous les assets PROD
- **Ajouts:** AR, ANKR, DOGE, OP, AVAX, DOT, NEAR avec params validés (12 assets PROD total)

### 3. Data Download
- **Complété:** 15 assets téléchargés (ETH, AVAX, UNI, DOT, SHIB, NEAR, OP, DOGE, AR, EGLD, ANKR, JOE, OSMO, MINA, BTC)

***

## Decisions

| Date | Decision | Rationale | Par |
|:-----|:---------|:----------|:----|
| 2026-01-22 | TP progression enforced par defaut | Bug invalidait tous les resultats | @Casey |
| 2026-01-22 | ETH mode medium_distance_volume | WFE 0.82 vs 0.52 baseline | @Sam |
| 2026-01-22 | AVAX mode medium_distance_volume | WFE 0.94 vs 0.52 baseline | @Jordan |
| 2026-01-22 | Timezone fix appliqué | Résout erreur complex numbers | @Jordan |
| 2026-01-22 | AR, ANKR, DOGE, OP ajoutés en PROD | 7/7 guards PASS | @Jordan |
| 2026-01-23 | UNI test moderate mode | FAIL (OOS Sharpe 0.03, WFE 0.01) — EXCLU | @Jordan |
| 2026-01-23 | asset_config.py mis à jour | 12 assets PROD avec params validés | @Jordan |
| 2026-01-23 | DOT, NEAR ajoutés en PROD | 6/7 guards PASS, WFE > 0.6 (scan) | @Jordan |

***

## Prochaines Étapes

1. **Investigation complex number** — YGG, SHIB, STRK, METIS, AEVO (fix timezone insuffisant)
2. **HBAR variants** — tester d26, d78 si disponible
3. **Mise à jour asset_config.py** — ajouter DOT, NEAR avec params validés
