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

## [22:45] [SUPERVISION ACTIVE] @Casey

**Cycle HBAR - Supervision en cours**

**Etat actuel:**
- ✅ Tache assignee: [22:45] HBAR avec mode `medium_distance_volume`
- ⏳ @Jordan: Pas de run documente dans `comms/jordan-dev.md`
- ⏳ @Sam: En attente dans `comms/sam-qa.md` (message [23:15])

**Contexte:**
- Scan baseline recent (22:22:31): HBAR SUCCESS (Sharpe 1.28, WFE 0.63)
- Guards baseline (00:57:03): 4/7 FAIL (sens 13%, bootstrap 0.53, stress1 0.72)
- Objectif: Tester `medium_distance_volume` pour reduire sensitivity sous 10%

**Workflow attendu:**
1. @Jordan execute commande → documente `[RUN_COMPLETE]` dans `jordan-dev.md`
2. @Sam valide 7 guards → documente `[VALIDATION]` dans `sam-qa.md`
3. @Casey rend verdict final (PROD/BLOCKED/RETEST)

**Mode supervision:** Relire `comms/*.md` apres chaque update jusqu'au verdict final

**Timeout:** 60 min max (jusqu'a 23:45)

---

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

