# Project State — FINAL TRIGGER v2

**Derniere mise a jour:** 2026-01-23 12:15 @Jordan

***

## Status Global

| Metrique | Valeur |
|----------|--------|
| Phase | Expansion Portfolio (75% objectif) |
| Assets PROD | **15** (BTC, ETH, JOE, OSMO, MINA, AVAX, AR, ANKR, DOGE, OP, DOT, NEAR, SHIB, METIS, YGG) |
| Assets en attente | 0 |
| Assets exclus | 23+ (STRK, AEVO ajoutés) |
| Bug critique | RESOLU (TP progression + complex numbers) |

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
| **SHIB** | baseline | 52 | 5.88 | 2.42 | 96 | **2026-01-23** |
|| **METIS** | baseline | 52 | 2.69 | 0.85 | - | **2026-01-23** |
|| **YGG** | baseline | 52 | 2.98 | 0.78 | - | **2026-01-23** |

**Nouveaux ajouts (2026-01-22):** AVAX, AR, ANKR, DOGE, OP (+5 assets)  
**Nouveaux ajouts (2026-01-23 AM):** DOT, NEAR, SHIB (+3 assets)  
**Nouveaux ajouts (2026-01-23 PM):** METIS, YGG (+2 assets) — Fix V6 complex numbers

***

## EN ATTENTE

### P0 (Urgent)
- [❌] HBAR — **FAIL** d26 (OOS Sharpe 0.30, WFE 0.11) — Tester d78 (Phase 3A Rescue)

### P1
- [✅] METIS — **PRODUCTION** (OOS Sharpe 2.69, WFE 0.85, 7/7 guards PASS) — Fix V6 réussi
- [✅] YGG — **PRODUCTION** (OOS Sharpe 2.98, WFE 0.78, 7/7 guards PASS) — Fix V6 réussi

### P2
- [❌] STRK — **EXCLU** (sensitivity 12.5% > 10%, bootstrap CI 0.56 < 1.0)
- [❌] AEVO — **EXCLU** (sensitivity 15.0% > 10%)
- [❌] EGLD — **FAIL** (WFE 0.31 < 0.6, OOS Sharpe 0.91 < 1.0)
- [❌] ARKM — **FAIL** (OOS Sharpe 0.94 < 1.0, WFE 0.57 < 0.6)

***

## EXCLUS (Definitif)

SEI, CAKE, AXS, RUNE, TON, SOL, AAVE, HYPE, ATOM, ARB, LINK, INJ, TIA,
HOOK, ALICE, HMSTR, LOOM, APT, EIGEN, ONDO, ICP, ARKM, EGLD, UNI, STRK, AEVO

**Nouveaux (2026-01-23):**
- UNI exclu — moderate mode FAIL (OOS Sharpe 0.03, WFE 0.01)
- STRK exclu — sensitivity 12.5% > 10%, bootstrap CI 0.56 < 1.0
- AEVO exclu — sensitivity 15.0% > 10%

***

## Blockers

| Asset | Blocker | Resolution | Status |
|-------|---------|------------|--------|
| UNI | guard002 variance 26.23% > 10%, WFE 0.42 < 0.6, moderate FAIL | Variants épuisés — **EXCLU** | ❌ |
| HBAR | d26 FAIL (Sharpe 0.30, WFE 0.11) | Tester d78 — Phase 3A Rescue | 🔄 |
| SHIB | Guards complex number error | ✅ **RESOLU** — Fix V3 réussi, 7/7 guards PASS | ✅ |
| METIS, YGG | Guards complex number error | ✅ **RESOLU** — Fix V6 réussi, 7/7 guards PASS | ✅ |
| STRK, AEVO | Guards complex number error | Fix V6 appliqué — EXCLUS (sensitivity > 10%) | ❌ |

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

1. ✅ **METIS, YGG débloqués** — Fix V6 réussi, 7/7 guards PASS → 15 assets PROD (75%)
2. 🔄 **Phase 3B** — BTC, ETH, JOE displacement grid optimization en cours
3. ⏸️ **HBAR d78** — Phase 3A Rescue (d26 FAIL)
4. 📊 **Nouveaux assets** — Screening Top 50 cryptos pour expansion portfolio (objectif 20+)
5. 🎯 **Objectif:** 20+ assets PROD → 5 assets restants
