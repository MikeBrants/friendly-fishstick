# Project State — FINAL TRIGGER v2

**Derniere mise a jour:** 2026-01-22 22:30 @Casey

***

## Status Global

| Metrique | Valeur |
|----------|--------|
| Phase | Revalidation post-fix TP |
| Assets PROD | 5 (BTC, ETH, JOE, OSMO, MINA) |
| Assets en attente | ~15 |
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

***

## EN ATTENTE

### P0 (Urgent)
- [ ] AVAX — medium_distance_volume (BLOCKER: data manquante, run download first)
- [ ] UNI — medium_distance_volume (BLOCKER: data manquante, run download first)
- [ ] HBAR — scan SUCCESS (Sharpe 1.28, WFE 0.63) mais guards FAIL (sens 13%, stress1 0.72)

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
| AVAX | Data manquante | `python scripts/download_data.py --assets AVAX` |
| UNI | Data manquante | `python scripts/download_data.py --assets UNI` |
| HBAR | sens 13% > 10%, stress1 0.72 < 1.0 | Tester filter grid ou autre displacement |

***

## Decisions

| Date | Decision | Rationale | Par |
|:-----|:---------|:----------|:----|
| 2026-01-22 | TP progression enforced par defaut | Bug invalidait tous les resultats | @Casey |
| 2026-01-22 | ETH mode medium_distance_volume | WFE 0.82 vs 0.52 baseline | @Sam |
| 2026-01-22 | ICP exclu definitivement | Overfitting severe, OOS Sharpe negatif | @Casey |
| 2026-01-22 | HBAR en attente filter grid | Scan OK mais guards 5/7 | @Sam |
