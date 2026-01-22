# Project State — FINAL TRIGGER v2

**Dernière mise à jour:** 2026-01-22 21:00 @Casey

***

## 📊 Status Global

| Métrique | Valeur |
|----------|--------|
| Phase | Revalidation post-fix TP |
| Assets PROD | 5 (BTC, ETH, JOE, OSMO, MINA) |
| Assets en attente | 15 |
| Assets exclus | 20+ |
| Bug critique | ✅ RÉSOLU (TP progression) |

***

## ✅ PROD (7/7 Guards PASS)

| Asset | Mode | Disp | Sharpe | WFE |
|:------|:-----|:-----|:-------|:----|
| BTC | baseline | 52 | 2.14 | >0.6 |
| ETH | medium_distance_volume | 52 | 2.09 | 0.82 |
| JOE | baseline | 26 | 5.03 | 1.44 |
| OSMO | baseline | 65 | 3.18 | 0.77 |
| MINA | baseline | 78 | 1.76 | 0.61 |

***

## ⏳ EN ATTENTE

### P0 (Urgent)
- [ ] AVAX — medium_distance_volume (@Jordan)
- [ ] UNI — medium_distance_volume (@Jordan)

### P1
- [ ] DOT, SHIB, NEAR — baseline TP enforced
- [ ] OP — disp=78 TP enforced
- [ ] DOGE — disp=26 TP enforced

### P2
- [ ] AR, EGLD, CELO, ANKR — baseline

### P3
- [ ] YGG, ARKM, STRK, METIS, AEVO — debug guard errors

***

## ❌ EXCLUS (Définitif)

SEI, CAKE, AXS, RUNE, TON, SOL, AAVE, HYPE, ATOM, ARB, LINK, INJ, TIA,
HOOK, ALICE, HMSTR, LOOM, APT, EIGEN, ONDO

***

## 🚧 Blockers

_Aucun blocker actuel_

***

## 📝 Décisions

| Date | Décision | Rationale | Par |
|:-----|:---------|:----------|:----|
| 2026-01-22 | TP progression enforced par défaut | Bug invalidait tous les résultats | @Casey |
| 2026-01-22 | ETH mode medium_distance_volume | WFE 0.82 vs 0.52 baseline | @Sam |
