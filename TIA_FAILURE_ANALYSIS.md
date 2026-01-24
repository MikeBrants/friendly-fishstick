# TIA FAILURE ANALYSIS - 24 janvier 2026, 20:47 UTC

## ❌ VERDICT: BLOCKED (1/7 guards FAIL)

**Asset:** TIA  
**OOS Sharpe:** 2.79 (base), 5.16 (scan optimisé)  
**WFE:** 1.36  
**Status:** **BLOCKED** - Ne peut pas être PROD

---

## 📊 RÉSULTATS GUARDS

| Guard | Métrique | Valeur | Seuil | Status |
|-------|----------|--------|-------|--------|
| **guard001** | MC p-value | 0.0000 | < 0.05 | ✅ **PASS** |
| **guard002** | Sensitivity variance | **11.49%** | < 10% | ❌ **FAIL** |
| **guard003** | Bootstrap CI lower | 3.30 | > 1.0 | ✅ **PASS** |
| **guard005** | Top10 trades | 18.56% | < 40% | ✅ **PASS** |
| **guard006** | Stress1 Sharpe | 2.54 | > 1.0 | ✅ **PASS** |
| **guard007** | Regime mismatch | 0.00% | < 1% | ✅ **PASS** |
| **WFE** | Walk-forward efficiency | 1.36 | > 0.6 | ✅ **PASS** |

**Final:** 6/7 guards PASS → **ALL PASS: NO** ❌

---

## 🔍 PROBLÈME IDENTIFIÉ: Guard002 (Sensitivity Variance)

**Qu'est-ce que c'est?**
- Test la stabilité des paramètres optimisés (ATR multipliers)
- Varie les paramètres de ±5% et recalcule les métriques
- Variance > 10% = paramètres trop sensibles = overfit

**Résultat TIA:**
- **Variance observée: 11.49%** (> 10% seuil)
- Signifie que de petites variations de paramètres causent des variations importantes de Sharpe
- Indicateur d'overfitting sur les paramètres ATR

**Interprétation:**
Les excellentes performances de TIA (Sharpe 5.16) sont **trop dépendantes** des paramètres exacts. Un léger changement (±5%) dégrade significativement la performance.

---

## 🎯 IMPLICATIONS

### Impact sur Portfolio
- TIA **ne peut PAS** être ajouté au portfolio PROD
- Portfolio reste à **8 assets** (sans TIA)
- Pas de nouvel asset #2 après SHIB

### Autres Assets du Batch

**✅ PASS (2 assets):**
- **RUNE**: 2.89 Sharpe, 0.61 WFE, 7/7 guards PASS
- **EGLD**: 2.39 Sharpe, 0.66 WFE, 7/7 guards PASS

**❌ FAIL (5 assets):**
- **TIA**: guard002 FAIL (sensitivity 11.49%)
- **HBAR**: 4/7 guards FAIL (guard002, 003, 005, 006)
- **CAKE**: guard002 FAIL (sensitivity 10.76%)
- **TON**: 5/7 guards FAIL (multiple issues)
- **SUSHI**: WFE FAIL (0.406 < 0.6)

**Total Portfolio:** 8 + 2 = **10 assets PROD**

---

## 🔧 OPTIONS POUR TIA

### Option A: BLOCKED (Recommandé)
**Action:** Accepter l'échec, exclure TIA du portfolio  
**Raison:** Guard002 est critique (détecte overfit paramètres)  
**Impact:** Portfolio reste à 10 assets (suffisant)

### Option B: Re-optimization avec Filters (Risqué)
**Action:** Réoptimiser TIA avec `medium_distance_volume` filter  
**But:** Réduire overfit, améliorer stabilité paramètres  
**Risque:** Peut dégrader Sharpe significativement  
**Effort:** 2-3 heures compute

### Option C: Manual Parameter Adjustment (Non recommandé)
**Action:** Tester manuellement différents paramètres ATR  
**Raison:** Viole le principe de walk-forward validation  
**Verdict:** ❌ **NE PAS FAIRE** (cherry-picking)

---

## 📋 DÉCISION RECOMMANDÉE

**Verdict:** ✅ **OPTION A - BLOCKED**

**Rationale:**
1. Guard002 est un garde critique contre l'overfit
2. TIA montre clairement une sensibilité excessive aux paramètres
3. Nous avons déjà 10 assets PROD (objectif 55% atteint)
4. RUNE et EGLD sont passés → portefeuille s'agrandit quand même

**Action:**
- Marquer TIA comme **BLOCKED** (guard002 FAIL)
- Mettre à jour portfolio: 10 assets PROD (8 + RUNE + EGLD)
- Documenter la raison de l'exclusion
- NE PAS tenter de re-optimization (waste of compute)

---

## 📊 NOUVEAU PORTFOLIO (10 Assets)

| Rank | Asset | Sharpe | WFE | Status |
|:----:|:------|:-------|:----|:-------|
| 🥇 | SHIB | 5.67 | 2.27 | PROD |
| 🥈 | DOT | 4.82 | 1.74 | PROD |
| 🥉 | NEAR | 4.26 | 1.69 | PROD |
| 4️⃣ | DOGE | 3.88 | 1.55 | PROD |
| 5️⃣ | ANKR | 3.48 | 0.86 | PROD |
| 6️⃣ | ETH | 3.23 | 1.06 | PROD |
| 7️⃣ | ONE | 3.00 | 0.92 | PROD |
| 8️⃣ | **RUNE** 🆕 | **2.89** | **0.61** | **PROD** |
| 9️⃣ | JOE | 2.65 | 0.73 | PROD |
| 🔟 | **EGLD** 🆕 | **2.39** | **0.66** | **PROD** |

**Mean Sharpe:** 3.60  
**All WFE > 0.6:** ✅  
**All 7/7 guards PASS:** ✅

---

## 🎯 NEXT STEPS

1. ✅ **Accepter TIA échec** (guard002 est non-négociable)
2. ✅ **Valider RUNE et EGLD** (2 nouveaux assets PROD)
3. ✅ **Mettre à jour portfolio** (10 assets total)
4. ⏸️ **Phase 1 screening** (optionnel, on a déjà 50% de l'objectif)
5. 🚀 **Portfolio construction** (tester 4 méthodes avec 10 assets)

---

**Créé par:** Casey  
**Date:** 24 janvier 2026, 20:50 UTC  
**Based on:** Sam guards execution results (20:47 UTC)
