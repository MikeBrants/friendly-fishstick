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

## [22:48] [RUN_START] @Jordan -> @Sam

**Task ref:** [22:45] [TASK] @Casey -> @Jordan (HBAR medium_distance_volume)
**Asset:** HBAR
**Mode:** medium_distance_volume
**Displacement:** Auto (52 par défaut)
**Command:** 
```bash
python scripts/run_full_pipeline.py \
  --assets HBAR \
  --workers 6 \
  --trials-atr 150 \
  --trials-ichi 150 \
  --enforce-tp-progression \
  --optimization-mode medium_distance_volume \
  --skip-download \
  --run-guards
```
**Status:** Running
**Duration:** En cours
**Outputs:** En attente
**Next:** @Sam valide les guards une fois terminé

