# /loop — Boucle Autonome Multi-Agent

Exécute le workflow en boucle jusqu'à complétion ou blocker.

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
Dans `comms/[agent].md`, ajoute :

```markdown
## [DATE] [HEURE] UTC — [NOM TÂCHE]

**Status**: TODO → DONE
**Output**: [fichiers créés/modifiés]
**Summary**: [résumé en 2-3 lignes]
**Next**: [prochaine tâche ou agent]
```

### 7. Boucler
Retourne à l'étape 1.

---

## Conditions d'arrêt

Stop la boucle si :
- ✅ Toutes les tâches sont DONE
- 🚫 Un BLOCKER est rencontré (demande intervention humaine)
- 🔢 5 tâches complétées (safety limit — relance /loop pour continuer)
- ❌ Erreur non récupérable

---

## Output après chaque tâche

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ DONE: [Nom de la tâche]
   Agent: [Alex/Jordan/Sam]
   Output: [fichier créé]
   Updated: comms/[agent].md
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
Tâches complétées: X
Fichiers modifiés: [liste]
Status: [DONE / BLOCKED / LIMIT]

Prochaine action recommandée:
→ [action ou "Relance /loop pour continuer"]
═══════════════════════════════════════
```

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

## Exemple de run

```
/loop

→ Lecture status/project-state.md...
→ Scan comms/*.md...
→ Prochaine tâche: "WFE Audit" (Alex, 🔴🔴🔴 BLOQUANT)

[Lance subagent Alex]
...
[Alex termine]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ DONE: WFE Audit
   Agent: Alex
   Output: reports/wfe-audit-2026-01-26.md
   Updated: comms/alex-lead.md
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⏭️  NEXT: PBO Implementation (Alex)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

→ Prochaine tâche: "PBO Implementation" (Alex, 🔴🔴)

[Lance subagent Alex]
...
```
