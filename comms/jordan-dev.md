# Runs Backtest - @Jordan

Ce fichier contient les logs des runs executes par Jordan.

---

## Format Message

```
## [HH:MM] [ACTION] @Jordan -> @Agent
**Task ref:** [lien vers tache Casey]
**Asset:** XXX
**Mode:** baseline | medium_distance_volume
**Displacement:** 26 | 52 | 65 | 78
**Command:** <commande complete>
**Status:** Running | Complete | Failed
**Duration:** X min
**Outputs:**
- outputs/multiasset_scan_YYYYMMDD_HHMMSS.csv
- outputs/guards/XXX_guard_results.json
**Erreurs:** [si applicable]
**Next:** @Sam valide les guards
```

### Actions possibles
- `[RUN_START]` — Debut d'execution
- `[RUN_COMPLETE]` — Run termine avec succes
- `[RUN_FAILED]` — Run echoue
- `[WAITING]` — En attente d'une tache

---

## Historique

<!-- Les messages les plus recents en haut -->

