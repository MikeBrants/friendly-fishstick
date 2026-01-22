# Taches Quant - @Casey

Ce fichier contient les taches assignees par Casey aux autres agents.

---

## Format Message

```
## [HH:MM] [ACTION] @Casey -> @Agent
**Context:** ...
**Task:** ...
**Command:** ...
**Criteres succes:** ...
**Next:** @Agent fait X
```

### Actions possibles
- `[TASK]` — Nouvelle tache assignee
- `[DECISION]` — Verdict rendu (PROD/BLOCKED/RETEST)
- `[WAITING]` — En attente d'un autre agent
- `[CYCLE COMPLETE]` — Fin du cycle

---

## Historique

<!-- Les messages les plus recents en haut -->

## [22:45] [TASK] @Casey -> @Jordan

**Context:** HBAR a passe le scan (Sharpe 1.28, WFE 0.63) mais guards FAIL (sensitivity 13% > 10%, stress1 0.72 < 1.0). On teste avec filter grid medium_distance_volume comme pour ETH.

**Asset:** HBAR
**Variant:** medium_distance_volume (comme ETH winner)
**Hypothese:** Le filter mode reduira la sensitivity variance sous 10%

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

**Criteres succes:** 
- 7/7 guards PASS
- WFE > 0.6
- Sensitivity < 10%

**Next:** @Jordan execute, puis @Sam valide

