# Skills - Procédures FINAL TRIGGER v2

Ce dossier contient les **Skills** (procédures how-to) pour le pipeline quant.

**Emplacement:** `.cursor/skills/` (project-level, conforme Agent Skills spec)

## Skills Disponibles

| Skill | Description | Phase | Quand l'utiliser |
|-------|-------------|-------|------------------|
| `guards-runner` | Exécute les 7 guards de validation | Phase 2 | Après backtest, avant PROD |
| `displacement-rescue` | Teste d26/d52/d65/d78 variants | Phase 3A | Quand guards FAIL |
| `filter-grid` | Teste 12 combinaisons filtres | Phase 4 | Après échec Phase 3A |
| `pine-generator` | Génère Pine Script TradingView | Phase 5 | Après validation 7/7 PASS |
| `regime-analyzer` | Analyse BULL/BEAR/SIDEWAYS | Debug | Pour comprendre la performance |

## Workflow Rescue (OBLIGATOIRE)

```
Phase 2: Validation
    ↓ guards FAIL
Phase 3A: Displacement Rescue (skill: displacement-rescue)
    ↓ si FAIL
Phase 4: Filter Grid (skill: filter-grid)
    ↓ si FAIL
EXCLU DÉFINITIF (justifié car workflow épuisé)
```

**JAMAIS bloquer un asset sans épuiser le workflow rescue!**

---

## Skills vs Rules

| Aspect | Skills (`.cursor/skills/`) | Rules (`.cursor/rules/`) |
|--------|----------------------------|--------------------------|
| **Fichier** | `SKILL.md` | `*.mdc` |
| **Routing** | `description` (mots-clés) | `globs` (patterns fichiers) |
| **Usage** | Procédures "comment faire" | Contraintes "tu dois toujours" |
| **Chargement** | Dynamique (agent décide) | Automatique (pattern match) |
| **Coût tokens** | Payé seulement si utilisé | Payé si `alwaysApply` ou match |

## Invocation

L'agent charge automatiquement un skill quand sa `description` matche la tâche en cours.

Tu peux aussi demander explicitement:
> "Utilise le skill guards-runner pour valider BTC"
> "Lance le displacement rescue pour AVAX"

---

## ⚠️ MAINTENANCE OBLIGATOIRE

### Vérification à chaque changement de pipeline

**IMPORTANT:** À chaque modification du pipeline (stratégie, guards, workflow), vérifier si les skills doivent être mis à jour:

| Changement | Skills à mettre à jour |
|------------|------------------------|
| Seuils guards | `guards-runner`, `.cursor/rules/agents/sam-qa.mdc` |
| Nouvelle commande/script | Skill correspondant, `jordan-dev.mdc` |
| Nouveau filter mode | `filter-grid` |
| Changement Pine | `pine-generator` |
| Nouveau guard | `guards-runner`, `global-quant.mdc`, `MASTER_PLAN.mdc` |
| Changement workflow | `workflow.mdc`, `WORKFLOW_ENFORCEMENT.mdc`, skills concernés |

### Checklist post-commit stratégie

```markdown
## Après chaque commit stratégie/pipeline

- [ ] Seuils changés? → màj skills + rules
- [ ] Commandes changées? → màj skills
- [ ] Workflow changé? → màj MASTER_PLAN + workflow.mdc + skills
- [ ] Guards changés? → màj guards-runner + global-quant
- [ ] Descriptions skills toujours pertinentes?
```

### Pourquoi c'est important

Les skills et rules sont la **documentation exécutable** du pipeline. Si elles divergent du code:
- L'agent donnera des instructions obsolètes
- Les seuils de validation seront incorrects
- Les commandes échoueront

**Règle:** Tout changement de pipeline = vérification skills/rules dans le même PR.

---

## Référence Rapide

### Seuils Guards (mise à jour: 25-JAN-2026)

| Guard | Seuil | Critique |
|-------|-------|----------|
| WFE | ≥0.6 | OUI |
| MC p-value | <0.05 | OUI |
| Sensitivity | <15% | OUI |
| Bootstrap CI | >1.0 | OUI |
| Top10 trades | <40% | OUI |
| Stress Sharpe | >1.0 | OUI |
| Regime mismatch | ≤1 | OUI |
| OOS Trades | ≥60 | OUI |
| OOS Sharpe | >1.0 | target >2.0 |

### Commandes Clés

```bash
# Phase 2: Validation
python scripts/run_full_pipeline.py --assets ASSET \
  --workers 1 --trials-atr 300 --trials-ichi 300 \
  --enforce-tp-progression --run-guards

# Phase 3A: Displacement Rescue
python scripts/run_full_pipeline.py --assets ASSET \
  --fixed-displacement 26 --workers 1 \
  --trials-atr 300 --trials-ichi 300 \
  --enforce-tp-progression --run-guards

# Phase 4: Filter Grid
python scripts/run_full_pipeline.py --assets ASSET \
  --optimization-mode medium_distance_volume \
  --workers 1 --enforce-tp-progression --run-guards
```

### Displacement par Type Asset

| Type | Displacement | Exemples |
|------|--------------|----------|
| Meme/Fast | 26 | DOGE, JOE, SHIB |
| Standard | 52 | BTC, ETH |
| Custom | 65 | OSMO |
| Slow/L2 | 78 | OP, MINA |
