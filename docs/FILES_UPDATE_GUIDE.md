# Guide des Fichiers à Mettre à Jour

**Dernière MAJ:** 2026-01-22

Ce document explique quels fichiers sont **lus automatiquement** par Cursor au début de chaque session, et lesquels doivent être **mis à jour manuellement** lors de modifications.

---

## 📖 Fichiers LUS AUTOMATIQUEMENT (Guidelines Persistantes)

Ces fichiers sont chargés par Cursor au début de chaque session et servent de **règles/guidelines persistantes**. Ils doivent être mis à jour quand vous changez des règles, seuils, ou workflows.

### Fichiers `alwaysApply: true` (toujours chargés)

| Fichier | Description | Quand MAJ |
|---------|-------------|-----------|
| `.cursor/rules/MASTER_PLAN.mdc` | Plan maître, vision, priorités, arbres de décision | Changement de stratégie, nouvelles priorités |
| `.cursor/rules/global-quant.mdc` | Règles quantitatives (guards, seuils, assets PROD) | Nouveau asset PROD, changement de seuils |
| `CLAUDE.md` | Plan principal du projet, état actuel, architecture | Changements majeurs (features, bugs critiques) |

### Fichiers `alwaysApply: false` (chargés à la demande)

Ces fichiers sont chargés uniquement quand vous mentionnez explicitement l'agent correspondant :

| Fichier | Agent | Quand MAJ |
|---------|-------|-----------|
| `.cursor/rules/casey-orchestrator.mdc` | Casey | Changement de workflow orchestration |
| `.cursor/rules/jordan-backtest.mdc` | Jordan | Changement de workflow backtest |
| `.cursor/rules/sam-guards.mdc` | Sam | Changement de workflow validation |

**Note:** Même si `alwaysApply: false`, ces fichiers sont référencés dans les règles principales et doivent être cohérents.

---

## ✏️ Fichiers à METTRE À JOUR MANUELLEMENT

Ces fichiers servent de **journal d'activité** et de **source de vérité dynamique**. Ils doivent être mis à jour à chaque avancement ou modification.

### 1. Fichiers de Statut (MAJ fréquente)

#### `status/project-state.md` — **Source de vérité principale**
- **Quand MAJ:** À chaque changement d'état (nouvel asset PROD, exclusion, blocker résolu)
- **Par qui:** Vous (ou Casey si système multi-agent actif)
- **Contenu:**
  - Assets PROD avec métriques
  - Assets en attente (P0, P1, P2, P3)
  - Assets exclus avec raison
  - Blockers actuels
  - Décisions importantes avec date

**Exemple de MAJ:**
```markdown
## PROD (7/7 Guards PASS)

| Asset | Mode | Disp | Sharpe | WFE | Trades |
|:------|:-----|:-----|:-------|:----|:-------|
| BTC | baseline | 52 | 2.14 | >0.6 | 416 |
| ETH | medium_distance_volume | 52 | 2.09 | 0.82 | 57 |
| **HBAR** | **medium_distance_volume** | **52** | **1.85** | **0.71** | **89** | ← NOUVEAU
```

#### `comms/casey-quant.md` — Tâches et verdicts
- **Quand MAJ:** À chaque assignation de tâche ou verdict
- **Par qui:** Vous (ou Casey)
- **Format:** Messages avec timestamp `[HH:MM]`

#### `comms/jordan-dev.md` — Exécution des runs
- **Quand MAJ:** À chaque run (début, fin, erreur)
- **Par qui:** Vous (ou Jordan)
- **Format:** `[RUN_START]`, `[RUN_COMPLETE]`, `[RUN_FAILED]`

#### `comms/sam-qa.md` — Validations guards
- **Quand MAJ:** Après chaque validation des 7 guards
- **Par qui:** Vous (ou Sam)
- **Format:** Tableau des 7 guards avec PASS/FAIL

### 2. Fichiers de Documentation (MAJ périodique)

#### `docs/HANDOFF.md` — Résumé exécutif
- **Quand MAJ:** Après chaque cycle complet (asset validé ou exclu)
- **Par qui:** Vous
- **Contenu:** Résultats globaux, next steps, métriques de succès

#### `docs/BACKTESTING.md` — Résultats détaillés
- **Quand MAJ:** Après chaque batch d'assets validés
- **Par qui:** Vous
- **Contenu:** Résultats détaillés par asset, comparaisons

#### `docs/WORKFLOW_MULTI_ASSET_SCREEN_VALIDATE_PROD.md` — Workflow 3 phases
- **Quand MAJ:** Si le workflow change
- **Par qui:** Vous
- **Contenu:** Processus complet de validation

---

## 🔄 Workflow de Mise à Jour Recommandé

### Scénario 1: Nouvel Asset Validé (7/7 Guards PASS)

```
1. ✅ Run terminé → MAJ `comms/jordan-dev.md` [RUN_COMPLETE]
2. ✅ Guards validés → MAJ `comms/sam-qa.md` [VALIDATION] (7/7 PASS)
3. ✅ Vérification → MAJ `status/project-state.md` (ajouter dans PROD)
4. ✅ Règles → MAJ `.cursor/rules/global-quant.mdc` (tableau assets PROD)
5. (Optionnel) → MAJ `CLAUDE.md` si changement majeur
```

### Scénario 2: Asset Exclu (Guards FAIL)

```
1. ✅ Guards validés → MAJ `comms/sam-qa.md` [VALIDATION] (X/7 FAIL)
2. ✅ Exclusion → MAJ `status/project-state.md` (ajouter dans EXCLUS)
3. ✅ Règles → MAJ `.cursor/rules/global-quant.mdc` (liste assets exclus)
```

### Scénario 3: Changement de Seuil/Guard

```
1. ✅ Décision → MAJ `.cursor/rules/global-quant.mdc` (nouveau seuil)
2. ✅ Documentation → MAJ `.cursor/rules/MASTER_PLAN.mdc` (règles absolues)
3. ✅ Plan → MAJ `CLAUDE.md` (section problèmes connus si applicable)
```

### Scénario 4: Nouvelle Feature ou Bug Critique Résolu

```
1. ✅ Code modifié → Tests passent
2. ✅ Documentation → MAJ `CLAUDE.md` (état actuel, checklist)
3. ✅ (Optionnel) → MAJ `docs/HANDOFF.md` si impact majeur
```

---

## 📋 Checklist Rapide

### Après chaque run/validation
- [ ] `comms/jordan-dev.md` ou `comms/sam-qa.md` (selon l'étape)
- [ ] `status/project-state.md` (si changement d'état)

### Après chaque cycle complet (asset validé/exclu)
- [ ] `status/project-state.md` (PROD/EXCLUS)
- [ ] `.cursor/rules/global-quant.mdc` (tableaux assets)
- [ ] (Optionnel) `docs/HANDOFF.md`

### Après changement de règle/seuil
- [ ] `.cursor/rules/global-quant.mdc` (seuils)
- [ ] `.cursor/rules/MASTER_PLAN.mdc` (règles absolues)
- [ ] `CLAUDE.md` (si changement majeur)

### Après nouvelle feature/bug critique
- [ ] `CLAUDE.md` (état actuel, checklist)
- [ ] (Optionnel) `docs/HANDOFF.md`

---

## 🎯 Priorités de Mise à Jour

| Priorité | Fichier | Fréquence | Impact |
|----------|---------|-----------|--------|
| **P0** | `status/project-state.md` | Immédiat | Source de vérité |
| **P0** | `.cursor/rules/global-quant.mdc` | Immédiat | Lue automatiquement |
| **P1** | `comms/*.md` | Après chaque action | Traçabilité |
| **P2** | `CLAUDE.md` | Changements majeurs | Documentation principale |
| **P3** | `docs/*.md` | Périodique | Documentation détaillée |

---

## ⚠️ Points Importants

1. **Un seul agent/fichier à la fois** : Un seul agent écrit dans son propre fichier `comms/*.md` (anti-race condition)

2. **Source de vérité unique** : `status/project-state.md` est LA source de vérité pour l'état global

3. **Cohérence** : Les fichiers de règles (`.cursor/rules/*.mdc`) doivent être cohérents entre eux

4. **Timestamps** : Toujours inclure des timestamps dans `comms/*.md` pour traçabilité

5. **Git** : Les fichiers `comms/*.md` et `status/*.md` sont dans `.gitignore` par défaut (voir `.gitignore` ligne 14-16). Si vous voulez les versionner, retirez-les du `.gitignore`.

---

## 🔍 Vérification Rapide

Pour vérifier que tout est à jour :

```bash
# Vérifier cohérence assets PROD
grep -r "PROD" status/project-state.md .cursor/rules/global-quant.mdc

# Vérifier dernière MAJ
grep "Derniere MAJ\|Derniere mise a jour" status/project-state.md CLAUDE.md

# Vérifier timestamps récents dans comms
ls -lt comms/*.md | head -5
```

---

## 📝 Template de MAJ Rapide

### Pour `status/project-state.md` :

```markdown
## PROD (7/7 Guards PASS)

| Asset | Mode | Disp | Sharpe | WFE | Trades |
|:------|:-----|:-----|:-------|:----|:-------|
| BTC | baseline | 52 | 2.14 | >0.6 | 416 |
| ETH | medium_distance_volume | 52 | 2.09 | 0.82 | 57 |
| **NOUVEAU_ASSET** | **mode** | **disp** | **sharpe** | **wfe** | **trades** |
```

### Pour `.cursor/rules/global-quant.mdc` :

```markdown
| BTC | baseline | 52 | 2.14 | >0.6 | 416 | ✅ PROD |
| ETH | medium_distance_volume | 52 | 2.09 | 0.82 | 57 | ✅ PROD |
| **NOUVEAU_ASSET** | **mode** | **disp** | **sharpe** | **wfe** | **trades** | ✅ PROD |
```

---

## ❓ Questions Fréquentes

**Q: Dois-je mettre à jour tous les fichiers à chaque modification ?**
R: Non, seulement ceux impactés. Voir checklist rapide ci-dessus.

**Q: Les fichiers `comms/*.md` sont-ils versionnés ?**
R: Par défaut non (dans `.gitignore`). Si vous voulez les versionner, retirez-les du `.gitignore`.

**Q: Que faire si je modifie du code mais pas de documentation ?**
R: Si c'est un bug fix mineur, pas besoin de MAJ docs. Si c'est une feature majeure ou un bug critique, MAJ `CLAUDE.md`.

**Q: Comment savoir quels fichiers sont obsolètes ?**
R: Vérifiez les timestamps dans les en-têtes (`Derniere MAJ`, `Derniere mise a jour`) et comparez avec vos dernières modifications.
