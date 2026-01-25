# Alex Lead Quant — Communications

**Last Updated**: 26 janvier 2026, 02:45 UTC

---

## 🆕 NOUVELLE TÂCHE ASSIGNÉE (26 Jan 2026)

### Task: Implémentation Regime-Aware Guards (Mode Indicatif)

**Priorité**: 🟡 MOYENNE  
**Branche**: `feature/regime-aware-guards-indicative`  
**Instructions complètes**: `docs/REGIME_AWARE_GUARDS_IMPLEMENTATION.md`

#### Résumé

Implémenter 2 nouveaux guards en **mode indicatif** (ne bloquent pas la validation 7/7):

1. **Guard 008 - WFE Suspicious**
   - Détecte WFE anormaux (< 0.4 ou > 2.0)
   - Flag informatif, pas éliminatoire

2. **Guard 009 - Regime Bias**
   - Détecte mismatch favorable (IS=bear/sideways, OOS=bull)
   - Calcule Sharpe ajusté avec haircut
   - Flag informatif pour sizing/attentes

#### Fichiers à créer

- `crypto_backtest/analysis/regime_detector.py`
- `crypto_backtest/validation/indicative_guards.py`
- `tests/test_regime_detector.py`
- `tests/test_indicative_guards.py`
- `scripts/regime_analysis_v2.py`

#### Contraintes importantes

⚠️ **MODE INDICATIF**: Ces guards ne doivent PAS bloquer la validation  
⚠️ `blocks_validation=False` TOUJOURS  
⚠️ Apparaissent dans rapports avec flag ⚠️ mais n'affectent pas `all_pass`

#### Timeline estimée

- Jours 1-2: `regime_detector.py` + tests
- Jour 3: `indicative_guards.py`
- Jour 4: Intégration pipeline
- Jour 5: Validation sur 7 assets WFE > 1.0

---

## 📋 TÂCHES ACTIVES

| Task | Status | Description |
|------|--------|-------------|
| **Regime-Aware Guards** | 🆕 ASSIGNED | Guards 008/009 indicatifs |
| DSR Integration | ✅ DONE | `validation/deflated_sharpe.py` |
| Variance Reduction | 🔴 TODO | Réduire <10% (ETH 12.96%, CAKE 10.76%) |
| GitHub Repos Scan | 🟡 TODO | zipline, vectorbt, freqtrade |

---

## 📊 VARIANCE REDUCTION RESEARCH (En attente)

**Objectif**: Réduire variance sous 10% pour gros assets

**Pistes à explorer**:
1. Regime-aware WF splits — Splits stratifiés par régime
2. Parameter averaging — Moyenner top N trials (BMA)
3. Regularization Optuna — Pénalité variance dans objective
4. Reduced trial count — 50-75 trials au lieu de 300

**Status**: En attente — prioriser Regime-Aware Guards d'abord

---

## 📝 NOTES

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

---

## 📬 COMMUNICATION

**Pour signaler complétion**: Mettre à jour ce fichier avec `[TASK COMPLETE]`  
**Pour questions**: Ajouter section `## QUESTIONS` ci-dessous  
**Pour blockers**: Ajouter section `## BLOCKERS` ci-dessous
