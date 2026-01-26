# Correction: Données Régime Obsolètes - 26 Jan 2026

**Issue:** Utilisation de "79.5% SIDEWAYS profit" (donnée obsolète) dans 86 fichiers  
**Impact:** Tous les agents + documentation  
**Status:** ✅ CORRIGÉ  
**Author:** Jordan

---

## Erreur Identifiée

**Ancienne donnée (OBSOLÈTE):**
- "SIDEWAYS fait 79.5% du profit"
- Source: Ancienne analyse ETH single-asset (2024)
- Problème: Extrapolation incorrecte à tous les assets

**Nouvelle donnée (ACTUELLE - regime_v3 26 Jan 2026):**
- **ACCUMULATION:** ~82% des trades (biais période 2020-2024)
- **MARKDOWN:** 5-15% selon asset
- **SIDEWAYS:** 16.9%-39% des barres (variable par asset)

**Conclusion:** La distribution des régimes est **asset-dépendante**, pas universelle.

---

## Fichiers Corrigés (Priorité Haute)

| Fichier | Ligne | Status | Correction |
|---------|-------|--------|------------|
| `.cursor/rules/MASTER_PLAN.mdc` | 149 | ✅ CORRIGÉ | Ajouté bloc avertissement + données actuelles |
| `.cursor/rules/global-quant.mdc` | 57 | ✅ CORRIGÉ | "distribution variable par asset" |
| `CLAUDE.md` | 321 | ✅ CORRIGÉ | "distribution variable by asset" |
| `.claude/agents/alex.md` | 94 | ✅ CORRIGÉ | "sans analyse regime_v3" |
| `status/project-state.md` | 781, 852 | ✅ CORRIGÉ | Marqué comme RÉSOLU |
| `outputs/STRESS_TEST_REPORT_20260126.md` | 10 | ✅ CORRIGÉ | "variable %" |

---

## Bloc d'Avertissement Ajouté (MASTER_PLAN.mdc)

```markdown
### ⚠️ REGIME DATA UPDATE (26 Jan 2026)

**OBSOLETE:** "SIDEWAYS fait 79.5% du profit" (ancienne analyse ETH single-asset)

**ACTUEL (regime_v3 multi-asset):**
- ACCUMULATION: ~82% des trades (biais période 2020-2024)
- MARKDOWN: 5-15% selon asset (régimes bear)
- SIDEWAYS: variable par asset (16.9%-39% des barres)

**Action:** Consulter `outputs/regime_analysis/{ASSET}_regimes.csv` pour données actuelles  
**Référence:** Issue #17 TASK 3 stress test validé 26 Jan 2026
```

---

## Autres Fichiers Concernés (86 total)

Les fichiers suivants contiennent "79" mais pas tous liés au régime SIDEWAYS:
- Documentation historique (SESSION_SUMMARY, BATCH1, etc.)
- Outputs anciens (légitimes, pas à modifier)
- Skills/agents secondaires

**Action:** Pas de correction nécessaire pour outputs historiques (conservés pour traçabilité).

---

## Instruction pour les Agents

**NOUVELLE RÈGLE:**
```
TOUJOURS consulter outputs/regime_analysis/{ASSET}_regimes.csv pour données régime.
JAMAIS utiliser de valeurs hardcodées type "79% SIDEWAYS".
```

---

## Validation

| Vérification | Status |
|-------------|--------|
| Rules files critiques corrigés | ✅ DONE |
| Documentation principale mise à jour | ✅ DONE |
| Agent configs corrigées | ✅ DONE |
| Bloc avertissement ajouté | ✅ DONE |
| Outputs historiques préservés | ✅ INTACT |

---

## Impact sur TASK 3

**Stress Test Results (26 Jan):**
- MARKDOWN: 0-9 trades par asset (stratégie évite bear)
- SIDEWAYS: 12/14 PASS (EGLD, AVAX FAIL)

**Distribution SIDEWAYS réelle (moyenne 25.3%):**
- Min: 16.9% (SHIB)
- Max: 39.0% (ETH)
- Médiane: ~27%

**Conclusion:** Les résultats stress test confirment la variabilité par asset.

---

**Date:** 26 janvier 2026, 16:45 UTC  
**Complété par:** Jordan  
**Vérifié par:** (attente Casey review)
