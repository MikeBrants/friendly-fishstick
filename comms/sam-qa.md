# Validations Guards - @Sam

Ce fichier contient les validations des 7 guards par Sam.

---

## Format Message

```
## [HH:MM] [ACTION] @Sam -> @Casey
**Asset:** XXX
**Run ref:** [lien vers run Jordan]
**Date run:** YYYY-MM-DD (post-fix TP)

### Guards Check (7/7 requis)

| Guard | Seuil | Valeur | Status |
|-------|-------|--------|--------|
| guard001 MC p-value | < 0.05 | X.XX | PASS/FAIL |
| guard002 Sensitivity | < 10% | X.X% | PASS/FAIL |
| guard003 Bootstrap CI | > 1.0 | X.XX | PASS/FAIL |
| guard005 Top10 trades | < 40% | X.X% | PASS/FAIL |
| guard006 Stress Sharpe | > 1.0 | X.XX | PASS/FAIL |
| guard007 Regime mismatch | < 1% | X.X% | PASS/FAIL |
| WFE | > 0.6 | X.XX | PASS/FAIL |

### Metriques OOS
- Sharpe: X.XX
- MaxDD: X.X%
- Trades: XX

### Verifications
- [ ] TP progression: tp1 < tp2 < tp3, gaps >= 0.5
- [ ] Date post-fix (>= 2026-01-22 12H00)
- [ ] Pas de Sharpe suspect (> 4.0)

### Verdict
**Status:** 7/7 PASS | X/7 FAIL
**Raison si FAIL:** ...
**Recommendation:** PROD | BLOCKED | RETEST avec [variant]
**Next:** @Casey rend verdict final
```

### Actions possibles
- `[VALIDATION]` — Validation complete
- `[WAITING]` — En attente d'un run
- `[RECHECK]` — Re-validation demandee

---

## Historique

<!-- Les messages les plus recents en haut -->

## [23:15] [WAITING] @Sam

**Status:** En attente de run documenté par @Jordan

**Tâche assignée:** HBAR avec mode `medium_distance_volume` (task ref: [22:45] dans casey-quant.md)

**Observations:**
- Scan récent (22:22:31) montre HBAR SUCCESS (Sharpe 1.28, WFE 0.63) mais mode non confirmé
- Guards précédents (00:57:03) montrent 4/7 FAIL:
  - guard002: FAIL (sensitivity 13.01% > 10%)
  - guard003: FAIL (bootstrap CI 0.53 < 1.0)
  - guard006: FAIL (stress1 0.72 < 1.0)
- Jordan n'a pas encore documenté de run dans `comms/jordan-dev.md`
- Dernier scan: `multiasset_scan_20260122_222418.csv` (22:24:18)
- Dernier guards summary: `multiasset_guards_summary_20260122_181338.csv` (18:13:38)

**Action:** Relire `comms/jordan-dev.md` après 30s pour vérifier updates

**Next:** Dès qu'un `[RUN_COMPLETE]` apparaît pour HBAR, valider les 7 guards avec checklist complète

