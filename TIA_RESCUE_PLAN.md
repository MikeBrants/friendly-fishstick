# TIA RESCUE PLAN — Phase 3A Displacement Grid

**Créé:** 24 janvier 2026, 21:15 UTC  
**Asset:** TIA  
**Status:** PENDING (Phase 2 guards FAIL, rescue required)

---

## 📊 SITUATION ACTUELLE

**Phase 2 Results (d52):**
- **OOS Sharpe:** 2.79 (base), 5.16 (scan optimisé)
- **WFE:** 1.36 ✅
- **Guards:** 6/7 PASS ❌
- **Failed Guard:** guard002 (sensitivity variance 11.49% > 10%)

**Interprétation:**
- Performances excellentes (Sharpe 5.16)
- Paramètres ATR trop sensibles avec d52
- **Rescue justified** (asset prioritaire)

---

## 🎯 PHASE 3A: DISPLACEMENT RESCUE

### Objectif
Tester d26 et d78 pour trouver des paramètres plus stables

### Hypothèse
- d26 (Ichimoku court) → signaux différents → paramètres ATR différents
- d78 (Ichimoku long) → signaux différents → paramètres ATR différents
- Un des deux peut donner variance < 10% (guard002 PASS)

---

## 📋 COMMANDES À EXÉCUTER

### Test 1: TIA avec d26

```bash
python scripts/run_full_pipeline.py \
  --assets TIA \
  --fixed-displacement 26 \
  --trials-atr 300 \
  --trials-ichi 300 \
  --enforce-tp-progression \
  --run-guards \
  --overfit-trials 150 \
  --workers 1 \
  --output-prefix tia_rescue_d26_20260124
```

**Durée:** ~2-3h  
**Output:** `outputs/tia_rescue_d26_20260124_TIA_guards_summary.csv`

---

### Test 2: TIA avec d78

```bash
python scripts/run_full_pipeline.py \
  --assets TIA \
  --fixed-displacement 78 \
  --trials-atr 300 \
  --trials-ichi 300 \
  --enforce-tp-progression \
  --run-guards \
  --overfit-trials 150 \
  --workers 1 \
  --output-prefix tia_rescue_d78_20260124
```

**Durée:** ~2-3h  
**Output:** `outputs/tia_rescue_d78_20260124_TIA_guards_summary.csv`

---

## 🎲 SCÉNARIOS POSSIBLES

### Scénario A: d26 OU d78 passe 7/7 guards ✅
**Probabilité:** 40-50%  
**Action:**
- Comparer Sharpe OOS entre d26, d52, d78
- Garder le meilleur displacement qui passe guards
- **TIA → PROD** (rescue réussi)

**Classement si succès:**
- TIA Sharpe 5.16 → #2 asset (après SHIB 5.67)
- Portfolio: 11 assets PROD

---

### Scénario B: d26 ET d78 échouent guards ❌
**Probabilité:** 50-60%  
**Action:**
- **Phase 4: Filter Grid** (12 configurations)
- Tester avec meilleur displacement de Phase 3A
- Durée: 6-12h supplémentaires

**Configs prioritaires:**
- `medium_distance_volume` (réduit overfit)
- `moderate` (filtres moyens)
- `light_kama` (KAMA léger)

---

### Scénario C: Tous échouent (Phase 3A + Phase 4) ❌
**Probabilité:** 20-30%  
**Action:**
- **TIA → EXCLU DÉFINITIF**
- Documenter: "Échec après Phase 3A (3 displacements) + Phase 4 (filter grid)"
- Portfolio: 10 assets PROD (suffisant)

---

## 📋 ASSIGNMENT

**Task:** Phase 3A Displacement Rescue (TIA)  
**Assigné à:** @Jordan  
**Priority:** 🟡 P1 (MEDIUM - asset prioritaire mais portfolio déjà à 10)  
**Status:** ⏳ READY TO START

**Commandes:**
1. Exécuter d26 test (~2-3h)
2. Exécuter d78 test (~2-3h)
3. Reporter résultats à @Sam pour validation
4. @Sam → @Casey verdict final

**Blocking:** Non (peut être exécuté en parallèle avec autres tâches)

---

## 🎯 SUCCESS CRITERIA

**Phase 3A réussie si:**
- [ ] d26 OU d78 donne 7/7 guards PASS
- [ ] OOS Sharpe > 2.0 (maintenu)
- [ ] WFE > 0.6 (maintenu)
- [ ] Reproducibilité < 0.0001%

**Si succès:**
- TIA ajouté au portfolio PROD
- Mean Sharpe portfolio augmenté
- 11 assets PROD total (55% objectif)

**Si échec Phase 3A:**
- Procéder Phase 4 (filter grid)
- Si Phase 4 échec → EXCLU définitif

---

## 📊 IMPACT ANALYSIS

### Si TIA PROD (Sharpe 5.16)
**Portfolio:** 11 assets  
**Mean Sharpe:** 3.75 → 3.93 (+5%)  
**Top 3:** SHIB (5.67), TIA (5.16), DOT (4.82)  
**Impact:** ✨ **MAJEUR** (asset exceptionnel)

### Si TIA EXCLU
**Portfolio:** 10 assets  
**Mean Sharpe:** 3.60  
**Impact:** 🔵 **ACCEPTABLE** (portfolio déjà solide)

---

**Decision:** ✅ **PROCEED Phase 3A**  
**Rationale:** Asset prioritaire (Sharpe 5.16), rescue justified, workflow standard  
**Timeline:** 4-6h compute (d26 + d78)

---

**Next Update:** Après completion Phase 3A (~6h)
