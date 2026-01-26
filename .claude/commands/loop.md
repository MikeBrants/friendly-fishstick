# /loop — Boucle Autonome Multi-Agent

Exécute le workflow en boucle jusqu'à complétion ou blocker.

## Usage

```
/loop          → 5 tâches max (défaut, safe)
/loop 10       → 10 tâches max
/loop max      → Pas de limite (jusqu'à DONE ou BLOCKER)
```

**Argument reçu**: $ARGUMENTS

---

## Interprétation de $ARGUMENTS

| Valeur | Limite |
|--------|--------|
| (vide) | 5 tâches |
| `5` | 5 tâches |
| `10` | 10 tâches |
| `max` ou `unlimited` | Pas de limite |
| Autre nombre | Ce nombre |

---

## Étapes

### 1. Lire l'état
```bash
cat status/project-state.md
cat comms/casey-quant.md
```

### 2. Scanner les tâches
Lis tous les fichiers `comms/*.md` et extrait :
- Tâches avec status TODO ou INPROGRESS
- Leur priorité (🔴🔴🔴 > 🔴🔴 > 🔴 > 🟡)
- L'agent assigné

### 3. Sélectionner la prochaine tâche
Critères de sélection (dans l'ordre) :
1. Status BLOQUANT → traiter en premier
2. Priorité la plus haute
3. Pas de dépendance non résolue

### 4. Identifier l'agent
| Domaine | Agent | Fichier |
|---------|-------|---------|
| Orchestration, décisions | Casey | comms/casey-quant.md |
| Quant, recherche, PBO, WFE | Alex | comms/alex-lead.md |
| Code, tests, intégration | Jordan | comms/jordan-dev.md |
| Validation, guards, QA | Sam | comms/sam-qa.md |

### 5. Lancer le subagent
```
Lance subagent [AGENT] avec les instructions de comms/[agent].md
Tâche: [NOM DE LA TÂCHE]
```

### 6. Mettre à jour après complétion

#### 6a. Fichier agent `comms/[agent].md`
```markdown
## [DATE] [HEURE] UTC — [NOM TÂCHE]

**Status**: TODO → DONE
**Output**: [fichiers créés/modifiés]
**Summary**: [résumé en 2-3 lignes]
**Next**: [prochaine tâche ou agent]
```

#### 6b. Fichier global `status/project-state.md`
Met à jour la section correspondante :
- Si tâche Alex → section `## Alex Tasks`
- Si nouvel asset PROD → section `## Production Assets`
- Si nouveau fichier créé → section `## Recent Changes`

Format d'ajout dans project-state.md :
```markdown
### Recent Activity
- [DATE] ✅ [TÂCHE] (Agent: [nom]) → [output]
```

### 7. Incrémenter compteur et vérifier limite
```
tasks_completed += 1
if tasks_completed >= LIMIT:
    STOP avec status "LIMIT"
```

### 8. Boucler
Retourne à l'étape 1.

---

## Conditions d'arrêt

Stop la boucle si :
- ✅ Toutes les tâches sont DONE
- 🚫 Un BLOCKER est rencontré (demande intervention humaine)
- 🔢 Limite atteinte (5, 10, ou custom)
- ❌ Erreur non récupérable

---

## Output après chaque tâche

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ DONE: [Nom de la tâche] (X/LIMIT)
   Agent: [Alex/Jordan/Sam]
   Output: [fichier créé]
   Updated: 
     - comms/[agent].md
     - status/project-state.md
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⏭️  NEXT: [Prochaine tâche] ([Agent])
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## Output final

```
═══════════════════════════════════════
🏁 LOOP TERMINÉE
═══════════════════════════════════════
Tâches complétées: X / LIMIT
Fichiers modifiés: 
  - comms/alex-lead.md
  - comms/jordan-dev.md
  - status/project-state.md
Status: [DONE / BLOCKED / LIMIT]

Prochaine action recommandée:
→ [action ou "Relance /loop pour continuer"]
═══════════════════════════════════════
```

---

## Fichiers à mettre à jour

| Quand | Fichier | Quoi |
|-------|---------|------|
| Après CHAQUE tâche | `comms/[agent].md` | Détails de la tâche |
| Après CHAQUE tâche | `status/project-state.md` | Recent Activity + sections pertinentes |
| Si nouvel asset PROD | `status/project-state.md` | Section Production Assets |
| Si code modifié | `status/project-state.md` | Section Recent Changes |

---

## Agents disponibles

### Alex (Lead Quant)
- WFE audit, calculs statistiques
- PBO, CPCV, DSR
- Recherche, analyse de papers
- Fichier: `comms/alex-lead.md`

### Jordan (Developer)
- Écriture de code Python
- Tests unitaires
- Intégration pipeline
- Fichier: `comms/jordan-dev.md`

### Sam (QA)
- Validation des guards
- Tests d'intégration
- Verdicts PASS/FAIL
- Fichier: `comms/sam-qa.md`

### Casey (Orchestrator)
- Priorisation
- Décisions architecture
- Coordination inter-agents
- Fichier: `comms/casey-quant.md`

---

## Exemples

### /loop (défaut = 5)
```
/loop

→ Limite: 5 tâches
→ Lecture status/project-state.md...
...
🏁 LOOP TERMINÉE (5/5) - Status: LIMIT
→ Relance /loop pour continuer
```

### /loop 10
```
/loop 10

→ Limite: 10 tâches
→ Lecture status/project-state.md...
...
```

### /loop max
```
/loop max

→ Limite: AUCUNE (jusqu'à DONE ou BLOCKER)
⚠️  Mode sans limite activé
→ Lecture status/project-state.md...
...
🏁 LOOP TERMINÉE - Status: DONE (toutes tâches complétées)
```
