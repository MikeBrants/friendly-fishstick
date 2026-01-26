# Workflow Orchestré — Raccourci Cursor

## Usage
`@wf.md [commande]`

---

## Commandes

| Tape | Action |
|------|--------|
| `go` | Status + prochaine action |
| `tasks` | Liste toutes les tâches |
| `next` | Exécute la prochaine tâche TODO |
| `done [task]` | Marque une tâche DONE |

---

## RÈGLE CRITIQUE — MISE À JOUR FICHIERS

**APRÈS CHAQUE ACTION**, tu DOIS mettre à jour le fichier de l'agent concerné :

| Agent | Fichier à modifier |
|-------|-------------------|
| Casey | `comms/casey-quant.md` |
| Alex | `comms/alex-lead.md` |
| Jordan | `comms/jordan-dev.md` |
| Sam | `comms/sam-qa.md` |

### Format de mise à jour

```markdown
## [DATE] [HEURE] — [ACTION]

**Task**: [nom de la tâche]
**Status**: TODO → INPROGRESS / INPROGRESS → DONE / BLOCKED
**Output**: [fichier créé ou modifié]
**Next**: [prochaine étape ou agent suivant]
```

---

## go

```
1. cat status/project-state.md
2. cat comms/casey-quant.md (orchestrateur)
3. Résume en 5 points:
   - Tâches DONE
   - Tâches INPROGRESS
   - Tâches TODO (priorité haute)
   - Blockers
   - Prochaine action recommandée
4. Indique QUEL AGENT doit agir et QUEL FICHIER regarder
```

---

## tasks

```
1. Lis TOUS les fichiers comms/*.md
2. Extrait chaque tâche avec agent assigné

| Agent | Task | Status | Fichier |
|-------|------|--------|---------|
| alex | WFE Audit | TODO | comms/alex-lead.md |
| alex | PBO | TODO | comms/alex-lead.md |
| jordan | Tests PBO | TODO | comms/jordan-dev.md |
| sam | Validation | TODO | comms/sam-qa.md |

3. Indique la prochaine tâche et SON FICHIER
```

---

## next

```
1. Identifie la prochaine tâche TODO (priorité max)
2. Identifie l'AGENT assigné
3. Charge les règles: @.cursor/rules/agents/[agent].mdc
4. Exécute la tâche
5. ⚠️ OBLIGATOIRE: Met à jour comms/[agent].md avec:
   - Status: INPROGRESS ou DONE
   - Output: fichiers créés
   - Timestamp
6. Affiche: "→ Regarde comms/[agent].md pour le résultat"
```

---

## done [task]

```
1. Trouve la tâche dans comms/*.md
2. Change son status → DONE
3. Ajoute timestamp et résumé
4. Identifie la tâche suivante
5. Affiche: "✅ [task] DONE dans comms/[agent].md → Next: [suivante]"
```

---

## Mapping Agent → Responsabilités

| Agent | Domaine | Tâches typiques |
|-------|---------|-----------------|
| **Casey** | Orchestration | Priorisation, décisions, coordination |
| **Alex** | Lead Quant | WFE audit, PBO, CPCV, recherche |
| **Jordan** | Dev | Code, tests, intégration pipeline |
| **Sam** | QA | Validation guards, tests, verdicts |

---

## Exemple complet

```
Toi: @wf.md next

Cursor:
1. Prochaine tâche: "WFE Audit" (alex, 🔴🔴🔴)
2. Charge @.cursor/rules/agents/alex-lead.mdc
3. Exécute: analyse walk_forward.py:120...
4. Crée: reports/wfe-audit-2026-01-26.md
5. Met à jour comms/alex-lead.md:
   
   ## 2026-01-26 10:52 — WFE AUDIT
   **Status**: TODO → DONE
   **Output**: reports/wfe-audit-2026-01-26.md
   **Finding**: WFE utilise returns au lieu de Sharpe
   **Next**: Jordan pour fix walk_forward.py

6. Affiche: "→ Regarde comms/alex-lead.md pour détails"
```

---

## Fichiers sources

| Fichier | Rôle |
|---------|------|
| `status/project-state.md` | État global |
| `comms/casey-quant.md` | Tâches orchestrateur |
| `comms/alex-lead.md` | Tâches lead quant |
| `comms/jordan-dev.md` | Tâches dev |
| `comms/sam-qa.md` | Tâches QA |

**Ces fichiers sont MIS À JOUR après chaque action.**
