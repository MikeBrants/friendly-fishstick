# Alex Lead — Communications

## 2026-01-26 — TÂCHES CONSOLIDÉES POST-MERGE

### FROM: Casey (Orchestrator)
### TO: Alex (Lead Quant)
### STATUS: TODO — MULTI-TASK
### PRIORITY: 🔴🔴🔴 CRITIQUE

---

## 📋 TÂCHES ACTIVES

| # | Task | Priority | Status | Blocking |
|---|------|----------|--------|----------|
| 0 | WFE Period Effect Audit | 🔴🔴🔴 BLOQUANT | TODO | Oui |
| 1 | PBO Implementation | 🔴🔴 CRITIQUE | TODO | Non |
| 2 | CPCV Implementation | 🔴 HIGH | TODO | Non |
| 3 | **Regime-Aware Guards (INDICATIF)** | 🟡 MEDIUM | 🆕 ASSIGNED | Non |
| 4 | Variance Reduction | ⬜ DÉPRIORITISÉ | HOLD | Non |
| 5 | GitHub Repos Analysis | 🟡 MEDIUM | TODO | Non |

---

## TASK 0: Audit WFE Period Effect 🚨 BLOQUANT

### Statut: BLOQUANT — Aucune décision PROD tant que non résolu

### Problème Identifié

Le calcul actuel de WFE dans `crypto_backtest/optimization/walk_forward.py:120` est suspect:

```python
efficiency_ratio = _ratio(mean_oos_return, mean_is_return) * 100.0
```

**Issues potentielles:**
1. **Utilise les returns** au lieu des Sharpe ratios (WFE classique = OOS_Sharpe / IS_Sharpe)
2. **Multiplication par 100** → Valeurs gonflées (ex: WFE 2.36 pour ETH semble trop haut)
3. **Period effect**: Les fenêtres IS (180d) vs OOS (30d) ont des régimes différents

### Questions à Auditer

1. **Le calcul WFE est-il correct?** Comparer avec la définition standard (Robert Pardo)
2. **Y a-t-il un biais temporel?** Les IS contiennent-ils systématiquement plus de bull markets?
3. **Les WFE > 2.0 sont-ils réalistes?** (ETH: 2.36, SHIB: 2.27) — Normalement WFE < 1.0 est attendu

### Deliverable

Créer fichier: `reports/wfe-audit-2026-01-25.md`

---

## TASK 1: Implémenter PBO (Probability of Backtest Overfitting) 🔴 CRITIQUE

### Statut: CRITIQUE — Nécessaire pour validation statistique

**Fichier**: `crypto_backtest/validation/pbo.py` ✅ STUB CRÉÉ (PR #12)

### Seuils

| PBO | Verdict |
|-----|---------|
| < 0.15 | ✅ PASS — Low overfitting risk |
| 0.15-0.30 | ⚠️ MARGINAL — Proceed with caution |
| > 0.30 | ❌ FAIL — High overfitting probability |

### Actions Restantes

- [ ] Valider le code stub existant
- [ ] Créer tests unitaires `tests/validation/test_pbo.py`
- [ ] Tester sur 3 assets pilotes (ETH, SHIB, DOT)

---

## TASK 2: Implémenter CPCV (Combinatorial Purged Cross-Validation)

### Statut: HIGH — Complète PBO pour validation robuste

**Fichier**: `crypto_backtest/validation/cpcv.py` ✅ STUB CRÉÉ (PR #12)

### Actions Restantes

- [ ] Valider le code stub existant
- [ ] Créer tests unitaires `tests/validation/test_cpcv.py`
- [ ] Comparer avec Walk-Forward actuel

---

## 🆕 TASK 3: Implémentation Regime-Aware Guards (Mode Indicatif)

### Statut: 🆕 ASSIGNED (26 Jan 2026)

**Priorité**: 🟡 MOYENNE  
**Branche**: `feature/regime-aware-guards-indicative`  
**Instructions complètes**: `docs/REGIME_AWARE_GUARDS_IMPLEMENTATION.md`

### Résumé

Implémenter 2 nouveaux guards en **mode indicatif** (ne bloquent pas la validation 7/7):

#### Guard 008 - WFE Suspicious
- Détecte WFE anormaux (< 0.4 ou > 2.0)
- Flag informatif, pas éliminatoire

#### Guard 009 - Regime Bias
- Détecte mismatch favorable (IS=bear/sideways, OOS=bull)
- Calcule Sharpe ajusté avec haircut
- Flag informatif pour sizing/attentes

### Haircuts par régime (Guard 009)

| Régime OOS | Haircut | Rationale |
|------------|---------|----------|
| BULL | ×0.65 | Momentum gonfle performance |
| SIDEWAYS | ×1.0 | Régime neutre |
| BEAR | ×1.25 | Contexte difficile = bonus |

### Seuils WFE (Guard 008)

- WFE < 0.4 → Probable overfitting
- WFE 0.4-2.0 → Range acceptable
- WFE > 2.0 → Suspect (investiguer régime)

### Fichiers à créer

- [ ] `crypto_backtest/analysis/regime_detector.py`
- [ ] `crypto_backtest/validation/indicative_guards.py`
- [ ] `tests/test_regime_detector.py`
- [ ] `tests/test_indicative_guards.py`
- [ ] `scripts/regime_analysis_v2.py`

### Contraintes importantes

⚠️ **MODE INDICATIF**: Ces guards ne doivent PAS bloquer la validation  
⚠️ `blocks_validation=False` TOUJOURS  
⚠️ Apparaissent dans rapports avec flag ⚠️ mais n'affectent pas `all_pass`

### Timeline estimée

- Jours 1-2: `regime_detector.py` + tests
- Jour 3: `indicative_guards.py`
- Jour 4: Intégration pipeline
- Jour 5: Validation sur 7 assets WFE > 1.0

---

## 📚 Références Obligatoires

### Papers López de Prado (À LIRE)

| Paper | Année | Relevance |
|-------|-------|----------|
| "The Probability of Backtest Overfitting" | 2014 | TASK 1 — PBO |
| "The Deflated Sharpe Ratio" | 2014 | Context DSR |
| "Advances in Financial Machine Learning" Ch.7,11 | 2018 | CPCV, Backtesting |

### Repos GitHub à Analyser

| Repo | Focus |
|------|-------|
| **mlfinlab** (Hudson & Thames) | PBO, CPCV, DSR |
| **vectorbt** | WFE, Optimization |
| **freqtrade** | Hyperopt, Validation |

---

## Deliverables Attendus

1. **`reports/wfe-audit-2026-01-25.md`** — Audit WFE (TASK 0)
2. **`tests/validation/test_pbo.py`** — Tests PBO (TASK 1)
3. **`tests/validation/test_cpcv.py`** — Tests CPCV (TASK 2)
4. **`crypto_backtest/analysis/regime_detector.py`** — Détection régimes (TASK 3)
5. **`crypto_backtest/validation/indicative_guards.py`** — Guards indicatifs (TASK 3)

---

## Format de Réponse

```
HHMM INPROGRESS alex-lead -> casey-quant: TASK [N] en cours
Fichier: [path]
Progress: [X/Y steps]
Blockers: [if any]
```

Puis:
```
HHMM DONE alex-lead -> casey-quant: TASK [N] terminé
Deliverable: [path to file]
Key Findings: [bullet points]
Recommendation: [action]
```

---

## 📬 COMMUNICATION

**Pour signaler complétion**: Mettre à jour ce fichier avec `[TASK COMPLETE]`  
**Pour questions**: Ajouter section `## QUESTIONS` ci-dessous  
**Pour blockers**: Ajouter section `## BLOCKERS` ci-dessous

---

*Dernière mise à jour: 26 janvier 2026, 04:00 UTC*
