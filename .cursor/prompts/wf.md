# Workflow Dynamique — Raccourci Cursor

## Usage
Dans Cursor: `@wf.md` puis une commande

---

## Commandes

| Tape | Action |
|------|--------|
| `go` | Lis project-state.md → status + prochaine action |
| `tasks` | Liste TOUTES les tâches depuis comms/*.md |
| `[nom]` | Exécute la tâche nommée (ex: "wfe audit") |
| `next` | Identifie et lance la prochaine tâche non-DONE |
| `tests` | Crée tests manquants |
| `pr` | Résumé PRs GitHub |

---

## go

```
ÉTAPES OBLIGATOIRES:
1. cat status/project-state.md
2. cat comms/casey-quant.md (si existe)
3. Résume en 5 points max le status actuel
4. Identifie le PREMIER item BLOQUANT ou TODO
5. Propose la commande exacte à exécuter
```

---

## tasks

```
ÉTAPES OBLIGATOIRES:
1. Lis TOUS les fichiers comms/*.md
2. Extrait chaque tâche avec son status (TODO/INPROGRESS/DONE/BLOCKED)
3. Affiche en tableau:

| Agent | Task | Status | Priority |
|-------|------|--------|----------|
| alex  | WFE Audit | TODO | 🔴🔴🔴 |
| alex  | PBO | TODO | 🔴🔴 |
| ...   | ... | ... | ... |

4. Indique laquelle est la prochaine à faire
```

---

## next

```
ÉTAPES OBLIGATOIRES:
1. Exécute "tasks" mentalement
2. Trouve la première tâche:
   - Status = TODO ou INPROGRESS
   - Priority = la plus haute (🔴🔴🔴 > 🔴🔴 > 🔴 > 🟡)
   - Non bloquée par une autre
3. Charge les instructions depuis le fichier comms/ correspondant
4. Exécute la tâche
5. Met à jour comms/[agent].md avec le résultat
```

---

## [nom de tâche]

```
Exemple: @wf.md wfe audit

ÉTAPES:
1. Cherche "wfe audit" dans comms/*.md
2. Trouve les instructions détaillées
3. Exécute selon les specs
4. Met à jour le fichier comms/ avec DONE ou BLOCKED
```

---

## tests

```
1. find tests/ -name "test_*.py"
2. Lis comms/*.md pour identifier les modules créés
3. Pour chaque module sans test → crée le test
4. Template pytest standard
```

---

## pr

```
1. Liste les PRs ouvertes (gh pr list ou lecture GitHub)
2. Pour chaque: status, conflits, fichiers modifiés
3. Recommande l'ordre de merge
```

---

## RÈGLES CRITIQUES

1. **TOUJOURS** lire les fichiers source — ne jamais supposer
2. **TOUJOURS** mettre à jour comms/*.md après une action
3. **JAMAIS** hardcoder les tâches — elles viennent des fichiers
4. Format commit: `feat|fix|docs: description`
5. Si doute → demander

---

## Fichiers sources de vérité

| Fichier | Contenu |
|---------|---------|
| `status/project-state.md` | État global du projet |
| `comms/casey-quant.md` | Tâches orchestrateur |
| `comms/alex-lead.md` | Tâches lead quant |
| `comms/jordan-dev.md` | Tâches dev |
| `comms/sam-qa.md` | Tâches QA |

**Ces fichiers sont la SOURCE DE VÉRITÉ — pas ce prompt.**
