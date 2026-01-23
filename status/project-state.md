# Project State — FINAL TRIGGER v2

**Derniere mise a jour:** 2026-01-22 23:30 @Jordan

***

## Status Global

| Metrique | Valeur |
|----------|--------|
| Phase | Revalidation post-fix TP |
| Assets PROD | 6 (BTC, ETH, JOE, OSMO, MINA, AVAX) |
| Assets en attente | ~14 |
| Assets exclus | 21+ |
| Bug critique | RESOLU (TP progression) |

***

## PROD (7/7 Guards PASS)

| Asset | Mode | Disp | Sharpe | WFE | Trades |
|:------|:-----|:-----|:-------|:----|:-------|
| BTC | baseline | 52 | 2.14 | >0.6 | 416 |
| ETH | medium_distance_volume | 52 | 2.09 | 0.82 | 57 |
| JOE | baseline | 26 | 5.03 | 1.44 | 63 |
| OSMO | baseline | 65 | 3.18 | 0.77 | 57 |
| MINA | baseline | 78 | 1.76 | 0.61 | 78 |
| AVAX | medium_distance_volume | 52 | 3.52 | 0.94 | 96 |

***

## EN ATTENTE

### P0 (Urgent)
- [✅] AVAX — **PRODUCTION** (7/7 guards PASS avec medium_distance_volume, WFE 0.94)
- [🔄] UNI — **EN COURS** test `moderate` (guard002 variance 10.27% baseline)
- [❌] HBAR — **FAIL** medium_distance_volume (4/7 guards FAIL, variants proposés)

### P1
- [ ] DOT, SHIB, NEAR — baseline TP enforced
- [ ] OP — disp=78 TP enforced
- [ ] DOGE — disp=26 TP enforced

### P2
- [ ] AR, EGLD, CELO, ANKR — baseline

### P3
- [ ] YGG, ARKM, STRK, METIS, AEVO — debug guard errors

***

## EXCLUS (Definitif)

SEI, CAKE, AXS, RUNE, TON, SOL, AAVE, HYPE, ATOM, ARB, LINK, INJ, TIA,
HOOK, ALICE, HMSTR, LOOM, APT, EIGEN, ONDO, ICP

**Nouveau (2026-01-22):** ICP exclu — overfitting severe (OOS Sharpe -1.04, WFE -0.13)

***

## Blockers

| Asset | Blocker | Resolution |
|-------|---------|------------|
| UNI | guard002 variance 10.27% > 10% | **EN COURS:** Test `moderate` ou `d78` |
| HBAR | 4/7 guards FAIL (sens 11.49%, CI 0.30, top10 41%, stress1 0.62) | Variants proposés: d26, d78, ou autres filters |

***

## Decisions

| Date | Decision | Rationale | Par |
|:-----|:---------|:----------|:----|
| 2026-01-22 | TP progression enforced par defaut | Bug invalidait tous les resultats | @Casey |
| 2026-01-22 | ETH mode medium_distance_volume | WFE 0.82 vs 0.52 baseline | @Sam |
| 2026-01-22 | ICP exclu definitivement | Overfitting severe, OOS Sharpe negatif | @Casey |
| 2026-01-22 | HBAR test medium_distance_volume | Scan OK mais guards 4/7 FAIL, tester mode ETH winner | @Casey |
| 2026-01-22 | AVAX ajouté en PROD | 7/7 guards PASS avec medium_distance_volume (WFE 0.94) | @Jordan |
| 2026-01-22 | UNI test moderate | guard002 variance 10.27% baseline, tester filter mode | @Jordan |
| 2026-01-22 | HBAR variants proposés | d26, d78, ou autres filters après échec medium_distance_volume | @Jordan |
