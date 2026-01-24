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

### ❌ OPTION INITIALE (INCORRECTE): BLOCKED Immédiat
**Erreur:** Recommandation initiale violait le workflow rescue  
**Problème:** Skip Phase 3A (displacement) et Phase 4 (filter grid)  
**Corrigé:** Voir section "WORKFLOW RESCUE" ci-dessous

---

### ✅ OPTION CORRECTE: WORKFLOW RESCUE (Obligatoire)

Selon `docs/WORKFLOW_MULTI_ASSET_SCREEN_VALIDATE_PROD.md`:

**Phase 3A: Displacement Rescue (OBLIGATOIRE)**
```bash
# Test d26
python scripts/run_full_pipeline.py \
  --assets TIA --fixed-displacement 26 \
  --trials-atr 300 --trials-ichi 300 \
  --enforce-tp-progression --run-guards --workers 1

# Test d78  
python scripts/run_full_pipeline.py \
  --assets TIA --fixed-displacement 78 \
  --trials-atr 300 --trials-ichi 300 \
  --enforce-tp-progression --run-guards --workers 1
```

**Durée:** 4-6h (2-3h par displacement)  
**Probabilité succès:** 40-50% (d26 ou d78 peuvent stabiliser paramètres)

**Si Phase 3A échoue → Phase 4: Filter Grid (12 configs)**

**SEULEMENT après Phase 3A + Phase 4 épuisées → EXCLU définitif**

---

## 📋 DÉCISION CORRIGÉE

**Verdict:** ✅ **PHASE 3A RESCUE REQUIRED** (Workflow standard)

**Rationale:**
1. TIA a Sharpe exceptionnel (5.16) → Asset prioritaire
2. Échec limité à guard002 (sensitivity) → Displacement peut résoudre
3. Workflow rescue non épuisé → Tentatives obligatoires
4. Never skip rescue pour asset haute performance

**Action:**
1. ✅ Assigner @Jordan Phase 3A (d26 + d78)
2. ⏳ Si Phase 3A FAIL → Phase 4 (filter grid)
3. ❌ Si Phase 4 FAIL → EXCLU définitif (workflow épuisé)

**Plan détaillé:** Voir `TIA_RESCUE_PLAN.md`

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
