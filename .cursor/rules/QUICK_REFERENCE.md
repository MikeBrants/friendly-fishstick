# Quick Reference — Fichiers à MAJ

## 🟢 Fichiers LUS AUTOMATIQUEMENT (Guidelines)

Ces fichiers sont chargés par Cursor au début de chaque session. **MAJ quand vous changez des règles/seuils.**

| Fichier | Quand MAJ |
|---------|-----------|
| `.cursor/rules/MASTER_PLAN.mdc` | Changement stratégie/priorités |
| `.cursor/rules/global-quant.mdc` | Nouveau asset PROD, changement seuils |
| `CLAUDE.md` | Changements majeurs (features, bugs critiques) |

---

## 🟡 Fichiers à MAJ MANUELLEMENT (Statut)

Ces fichiers servent de journal d'activité. **MAJ après chaque action.**

| Fichier | Quand MAJ | Format |
|---------|-----------|--------|
| `status/project-state.md` | Changement d'état (PROD/exclus) | Tableaux |
| `comms/casey-quant.md` | Tâche assignée/verdict | `[HH:MM] [ACTION]` |
| `comms/jordan-dev.md` | Run terminé | `[RUN_COMPLETE]` |
| `comms/sam-qa.md` | Guards validés | Tableau 7 guards |

---

## ⚡ Workflow Rapide

### Nouvel Asset Validé
1. `comms/sam-qa.md` → `[VALIDATION]` (7/7 PASS)
2. `status/project-state.md` → Ajouter dans PROD
3. `.cursor/rules/global-quant.mdc` → Ajouter dans tableau

### Asset Exclu
1. `comms/sam-qa.md` → `[VALIDATION]` (X/7 FAIL)
2. `status/project-state.md` → Ajouter dans EXCLUS
3. `.cursor/rules/global-quant.mdc` → Ajouter dans liste exclus

### Changement de Seuil
1. `.cursor/rules/global-quant.mdc` → Nouveau seuil
2. `.cursor/rules/MASTER_PLAN.mdc` → Règles absolues

---

## 📍 Source de Vérité

**`status/project-state.md`** = Source de vérité unique pour l'état global

**`.cursor/rules/global-quant.mdc`** = Source de vérité pour assets PROD/exclus

---

Voir `docs/FILES_UPDATE_GUIDE.md` pour détails complets.
