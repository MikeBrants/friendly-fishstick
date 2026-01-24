# Skills - Procédures FINAL TRIGGER v2

Ce dossier contient les **Skills** (procédures how-to) pour le pipeline quant.

## Skills Disponibles

| Skill | Description | Quand l'utiliser |
|-------|-------------|------------------|
| `guards-runner` | Exécute les 7 guards de validation | Après backtest, avant PROD |
| `displacement-rescue` | Phase 3A - teste d26/d52/d78 | Quand guards FAIL |
| `filter-grid` | Phase 4 - teste 12 combinaisons filtres | Après échec Phase 3A |
| `pine-generator` | Génère Pine Script TradingView | Après validation 7/7 PASS |
| `regime-analyzer` | Analyse BULL/BEAR/SIDEWAYS | Pour comprendre la performance |

## Skills vs Rules

| Aspect | Skills (`SKILL.md`) | Rules (`.mdc`) |
|--------|---------------------|----------------|
| **Emplacement** | `skills/*/SKILL.md` | `.cursor/rules/*.mdc` |
| **Routing** | `description` (mots-clés) | `globs` (patterns fichiers) |
| **Usage** | Procédures "comment faire" | Contraintes "tu dois toujours" |
| **Chargement** | Dynamique (agent décide) | Automatique (pattern match) |

## Invocation

L'agent charge automatiquement un skill quand sa `description` matche la tâche en cours.

Tu peux aussi demander explicitement :
> "Utilise le skill guards-runner pour valider BTC"

---

## ⚠️ MAINTENANCE OBLIGATOIRE

### Vérification à chaque changement de pipeline

**IMPORTANT:** À chaque modification du pipeline (stratégie, guards, workflow), vérifier si les skills doivent être mis à jour :

1. **Changement de seuils** → Mettre à jour les tableaux dans :
   - `guards-runner/SKILL.md`
   - `.cursor/rules/agents/sam-qa.mdc`
   - `.cursor/rules/agents/alex-lead.mdc`

2. **Nouvelle commande/script** → Mettre à jour :
   - Le skill correspondant (guards-runner, displacement-rescue, etc.)
   - `.cursor/rules/agents/jordan-dev.mdc`

3. **Nouveau filter mode** → Mettre à jour :
   - `filter-grid/SKILL.md`

4. **Changement Pine Script** → Mettre à jour :
   - `pine-generator/SKILL.md`

5. **Nouveau guard** → Mettre à jour :
   - `guards-runner/SKILL.md`
   - `.cursor/rules/global-quant.mdc`
   - `.cursor/rules/MASTER_PLAN.mdc`

### Checklist post-commit stratégie

```markdown
## Après chaque commit stratégie/pipeline

- [ ] Vérifier si seuils ont changé → màj skills + rules
- [ ] Vérifier si commandes ont changé → màj skills
- [ ] Vérifier si workflow a changé → màj MASTER_PLAN + workflow.mdc
- [ ] Vérifier si guards ont changé → màj guards-runner + rules agents
- [ ] Tester que les descriptions des skills sont toujours pertinentes
```

### Pourquoi c'est important

Les skills et rules sont la **documentation exécutable** du pipeline. Si elles divergent du code :
- L'agent donnera des instructions obsolètes
- Les seuils de validation seront incorrects
- Les commandes échoueront

**Règle:** Tout changement de pipeline = vérification skills/rules dans le même PR.
