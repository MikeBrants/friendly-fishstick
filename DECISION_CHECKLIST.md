# DECISION CHECKLIST — Éviter Erreurs de Processus

**Créé:** 24 janvier 2026, 21:10 UTC  
**Raison:** Éviter violation du workflow (ex: TIA bloqué sans rescue)

---

## ⚠️ AVANT TOUTE DÉCISION DE BLOCAGE

### Checklist Obligatoire (Casey)

- [ ] **1. Lire le workflow**
  ```
  cat docs/WORKFLOW_MULTI_ASSET_SCREEN_VALIDATE_PROD.md
  grep -A 20 "Phase 3A\|Phase 4\|PENDING" docs/WORKFLOW_MULTI_ASSET_SCREEN_VALIDATE_PROD.md
  ```

- [ ] **2. Vérifier position dans workflow**
  - Asset vient de quelle phase? (1, 2, 3A, 3B, 4)
  - Quelles phases restent à tenter?
  - Workflow rescue épuisé? (Phase 3A + Phase 4)

- [ ] **3. Consulter historique asset**
  ```
  grep "ASSET_NAME" outputs/*_scan_*.csv | tail -5
  grep "ASSET_NAME" outputs/*_guards_*.csv | tail -5
  ```

- [ ] **4. Vérifier raison échec**
  - Guard spécifique? (guard001-007)
  - Multiple guards?
  - Structurel (WFE, trades) ou paramètres (sensitivity)?

- [ ] **5. Évaluer priorité asset**
  - Sharpe OOS > 3.0? → Haute priorité rescue
  - Sharpe OOS 2.0-3.0? → Priorité moyenne
  - Sharpe OOS < 2.0? → Priorité basse (skip rescue si 10+ assets PROD)

---

## 🔄 WORKFLOW RESCUE (Phase 3A → Phase 4)

### Phase 3A: Displacement Rescue

**Quand:** Asset échoue Phase 2 (guards FAIL)

**Action:**
```bash
# Tester d26
python scripts/run_full_pipeline.py \
  --assets [ASSET] \
  --fixed-displacement 26 \
  --trials-atr 300 \
  --trials-ichi 300 \
  --enforce-tp-progression \
  --run-guards \
  --workers 1 \
  --output-prefix rescue_d26_[ASSET]

# Tester d78
python scripts/run_full_pipeline.py \
  --assets [ASSET] \
  --fixed-displacement 78 \
  --trials-atr 300 \
  --trials-ichi 300 \
  --enforce-tp-progression \
  --run-guards \
  --workers 1 \
  --output-prefix rescue_d78_[ASSET]
```

**Durée:** 4-6h (2-3h par displacement)

**Décision après Phase 3A:**
- Si 1+ displacement PASS 7/7 → **PROD** (rescue réussi) ✅
- Si tous FAIL → **Phase 4** (filter grid)

---

### Phase 4: Filter Grid

**Quand:** Phase 3A épuisée (3 displacements testés, tous FAIL)

**Action:**
```bash
python scripts/run_filter_grid.py \
  --asset [ASSET] \
  --displacement [BEST_FROM_3A] \
  --workers 1 \
  --output-prefix filter_grid_[ASSET]
```

**Configs testées:** 12 (baseline → moderate → conservative)

**Durée:** 6-12h selon nombre de configs

**Décision après Phase 4:**
- Si 1+ config PASS 7/7 → **PROD** (rescue réussi) ✅
- Si tous FAIL → **EXCLU DÉFINITIF** ❌

---

## 🚫 QUAND BLOQUER IMMÉDIATEMENT (Exceptions)

**SKIP rescue uniquement si:**

1. **Données insuffisantes** (< 50 trades OOS après optimization)
2. **Asset low-priority** ET **10+ assets PROD existants** ET **compute limité**
3. **Structural issue** (WFE < 0.3, Sharpe < 0.8 même avec optimization)
4. **Utilisateur demande explicitement** de skip rescue

**Sinon:** Toujours tenter Phase 3A minimum

---

## 📋 TEMPLATE DÉCISION (Après Échec Guards)

```markdown
## DECISION: [ASSET] Guards FAIL - Rescue Strategy

**Context:**
- Asset: [ASSET]
- Phase actuelle: Phase 2 (validation)
- Guards results: X/7 PASS
- Failed guards: [liste]
- OOS Sharpe: X.XX
- WFE: X.XX

**Checklist:**
- [x] Workflow consulté (WORKFLOW_MULTI_ASSET_SCREEN_VALIDATE_PROD.md)
- [x] Position confirmée: Post-Phase 2, pre-Phase 3A
- [x] Historique vérifié (outputs/*.csv)
- [x] Raison échec identifiée: [guard002 sensitivity, etc.]
- [x] Priorité évaluée: [Haute/Moyenne/Basse]

**Decision:** PROCEED Phase 3A (Displacement Rescue)

**Rationale:**
- [Sharpe élevé / Asset prioritaire / etc.]
- Workflow rescue non épuisé
- Probabilité succès: [X%]

**Action:**
1. Assigner @Jordan Phase 3A (d26 + d78)
2. Durée estimée: 4-6h
3. Décision après: PROD si PASS, Phase 4 si FAIL
```

---

## 🎯 EXEMPLES

### ✅ CORRECT: TIA (Sharpe 5.16, guard002 FAIL)

```markdown
**Decision:** Phase 3A rescue (d26 + d78)
**Raison:** Sharpe exceptionnel (5.16), seul guard002 FAIL, rescue justifié
**Next:** Phase 4 si Phase 3A FAIL
```

### ❌ INCORRECT: Bloquer TIA immédiatement

```markdown
**Decision:** BLOCKED définitif
**Erreur:** Skip Phase 3A + Phase 4 → Violation workflow
**Impact:** Asset potentiellement #2 perdu sans tentative rescue
```

---

**Utilisé par:** Casey (Orchestrator)  
**Maintenu par:** User  
**Version:** 1.0
