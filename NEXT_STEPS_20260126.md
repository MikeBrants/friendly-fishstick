# Next Steps — 26 janvier 2026

**Last Updated**: 26 janvier 2026, 07:00 UTC  
**Status**: 🟡 MULTIPLE WORKSTREAMS — Prioritization Required

---

## 🔴 BLOQUANT — WFE Audit (TASK 0 Alex)

### Contexte
7 assets PROD montrent WFE > 1.0 (statistiquement suspect):
- SHIB: 2.27, DOT: 1.74, NEAR: 1.69, DOGE: 1.55, TIA: 1.36, ETH: 1.22, MINA: 1.13

**WFE > 1.0 = OOS performs BETTER than IS** — quasi-impossible sans:
1. Period effect (OOS = bull market)
2. Survivorship bias
3. Calculation error

### Action Requise
**Owner**: Alex (Lead Quant)  
**Deliverable**: `reports/wfe-audit-2026-01-25.md`  
**Status**: 🔴 TODO — **BLOQUANT** (aucune décision PROD avant completion)

**Questions à Auditer:**
1. Le calcul WFE est-il correct? (comparer avec Robert Pardo standard)
2. Y a-t-il un biais temporel? (IS contient plus de bull markets?)
3. Les WFE > 2.0 sont-ils réalistes?

**Référence**: `comms/alex-lead.md` (TASK 0)

---

## 🔴 CRITIQUE — PBO/CPCV Implementation (TASK 1-2 Alex)

### Contexte
Le système actuel manque de validation anti-overfitting complète:
- DSR existe mais n'est pas le vrai PBO
- CPCV (Combinatorially Symmetric Cross-Validation) non implémenté

### Actions Requises

#### TASK 1: PBO Implementation
**Owner**: Alex  
**Fichier**: `crypto_backtest/validation/pbo.py` (stub existe)  
**Status**: 🔴 TODO

**Méthodologie**:
1. Diviser données en S sous-ensembles (ex: S=16)
2. Former toutes combinaisons C(S, S/2) de training sets
3. Pour chaque combo: identifier "best" strategy sur IS, mesurer rang OOS
4. PBO = proportion de combos où rang OOS < médiane

**Seuils proposés**:
- PBO < 0.30: PASS (low overfitting risk)
- PBO 0.30-0.50: WARN (moderate risk)
- PBO > 0.50: FAIL (high overfitting risk)

#### TASK 2: CPCV Implementation
**Owner**: Alex  
**Fichier**: `crypto_backtest/validation/cpcv.py` (stub existe)  
**Status**: 🔴 TODO

**Usage**: Complément au PBO pour validation robustesse

**Référence**: `comms/alex-lead.md` (TASK 1-2)

---

## 🟡 PRIORITÉ — Phase 3A Rescue (3 assets FAIL)

### Assets Requérant Rescue

| Asset | Fail Reason | Action | Duration | Success Rate |
|-------|-------------|--------|----------|--------------|
| **OSMO** | Sharpe 0.68, WFE 0.19 | Displacement rescue (d26, d78) | 2-3h | 30-40% |
| **AR** | WFE 0.39, Trades 41 | Displacement rescue (d26, d78) | 2-3h | 20-30% |
| **METIS** | WFE 0.48 | Displacement rescue (d26, d78) | 2-3h | 30-40% |

**Note**: OP exclu définitif (Sharpe 0.03, WFE 0.01 — rescue unlikely)

### Commande Rescue
```bash
# OSMO
python scripts/run_full_pipeline.py \
  --assets OSMO \
  --fixed-displacement 26 \
  --trials-atr 300 \
  --trials-ichi 300 \
  --enforce-tp-progression \
  --run-guards \
  --workers 1

# Si d26 FAIL, tester d78
python scripts/run_full_pipeline.py \
  --assets OSMO \
  --fixed-displacement 78 \
  --trials-atr 300 \
  --trials-ichi 300 \
  --enforce-tp-progression \
  --run-guards \
  --workers 1
```

**Référence**: `docs/WORKFLOW_MULTI_ASSET_SCREEN_VALIDATE_PROD.md` (Phase 3A)

---

## 🟢 OPTIONNEL — Phase 1 Batch 2 Screening

### Contexte
Batch 1 (25 Jan): 0/15 assets PASS
- ADA: 4/7 guards FAIL (variance 19.38%)
- FIL: Overfitting révélé (Phase 1: 1.98 Sharpe → Phase 2: -0.22 Sharpe)

### Assets Proposés (Tier 3/4)
VET, MKR, ALGO, FTM, SAND, MANA, GALA, FLOW, THETA, CHZ, ZIL, APE, RNDR, LDO, BLUR (15)

### Améliorations Recommandées
1. **200 trials** en Phase 1 (pas 150) pour réduire false positives
2. **Pre-screen data quality** (check total_bars > 15,000)
3. **Focus assets** avec caractéristiques trend-following

### Commande
```bash
python scripts/run_full_pipeline.py \
  --assets VET MKR ALGO FTM SAND MANA GALA FLOW THETA CHZ ZIL APE RNDR LDO BLUR \
  --workers 10 \
  --trials-atr 200 \
  --trials-ichi 200 \
  --skip-guards \
  --output-prefix phase1_batch2_20260126
```

**Duration**: 20-30 min  
**Expected**: 2-3 PASS (15-20% pass rate)

**Référence**: `SESSION_SUMMARY_20260125.md` (Option A)

---

## 🟢 OPTIONNEL — Regime Test (Assets PROD)

### Contexte
Suite aux changements majeurs (bug KAMA corrigé, seuil sensitivity 15%, ETH baseline):
- **Anciens résultats de régime sont OBSOLÈTES**
- Distribution profits par régime (BULL/BEAR/SIDEWAYS) inconnue
- Ratio 79.5% SIDEWAYS profit doit être re-vérifié

### Action Requise
Re-run regime analysis sur tous les assets PROD avec nouveaux paramètres

**Assets à tester**: SHIB, DOT, NEAR, DOGE, ANKR, ETH, JOE, YGG, MINA, CAKE, RUNE, EGLD, AVAX (13)

### Commande
```bash
python scripts/regime_analysis_v2.py \
  --assets SHIB DOT NEAR DOGE ANKR ETH JOE YGG MINA CAKE RUNE EGLD AVAX
```

**Impact Potentiel**:
- Si distribution régime change → re-calibrer filtres
- Si SIDEWAYS n'est plus dominant → revoir stratégie
- Si mismatch augmente → certains assets pourraient être rétrogradés

**Référence**: `status/project-state.md` (section "REGIME TEST REQUIS")

---

## 📊 PORTFOLIO STATUS ACTUEL

### Assets PROD Validés (14)
1. SHIB: 5.67 Sharpe, 2.27 WFE ✅
2. TIA: 5.16 Sharpe, 1.36 WFE ✅
3. DOT: 4.82 Sharpe, 1.74 WFE ✅
4. NEAR: 4.26 Sharpe, 1.69 WFE ✅
5. DOGE: 3.88 Sharpe, 1.55 WFE ✅
6. ANKR: 3.48 Sharpe, 0.86 WFE ✅
7. ETH: 3.22 Sharpe, 1.22 WFE ✅
8. JOE: 3.16 Sharpe, 0.73 WFE ✅
9. YGG: 3.11 Sharpe, 0.78 WFE ✅
10. MINA: 2.58 Sharpe, 1.13 WFE ✅
11. CAKE: 2.46 Sharpe, 0.81 WFE ✅
12. RUNE: 2.42 Sharpe, 0.61 WFE ✅
13. EGLD: 2.13 Sharpe, 0.69 WFE ✅
14. AVAX: 2.00 Sharpe, 0.66 WFE ✅

**Mean Sharpe**: 3.17  
**Progress**: 70% of 20+ goal (14/20)

---

## 🎯 RECOMMANDATION PRIORISATION

### Option 1: Focus Validation (RECOMMENDED)
**Priority Order**:
1. 🔴 **WFE Audit** (Alex TASK 0) — BLOQUANT
2. 🔴 **PBO/CPCV** (Alex TASK 1-2) — CRITIQUE
3. 🟡 **Phase 3A Rescue** (OSMO, AR, METIS) — Après validation
4. 🟢 **Batch 2 Screening** — Si temps disponible
5. 🟢 **Regime Test** — Low priority

**Rationale**: 
- WFE Audit bloque toute décision PROD
- PBO/CPCV nécessaire pour validation scientifique
- Rescue peut attendre validation complète

### Option 2: Parallel Workstreams
**Alex**: WFE Audit + PBO/CPCV (research)  
**Jordan**: Phase 3A Rescue (execution)  
**Casey**: Orchestration + Batch 2 planning

**Rationale**: 
- Maximise utilisation ressources
- Alex (research) ≠ Jordan (execution) — pas de conflit

---

## 📋 DECISIONS PENDING

1. ⏳ **Prioritization**: Option 1 (sequential) ou Option 2 (parallel)?
2. ⏳ **WFE Audit**: Commencer immédiatement ou attendre?
3. ⏳ **Rescue Timing**: Avant ou après WFE Audit?
4. ⏳ **Batch 2**: Lancer maintenant ou attendre Batch 1 analysis complète?

---

## 📁 FILES REFERENCE

- `status/project-state.md` — Current state (14 PROD assets)
- `comms/alex-lead.md` — Alex tasks (TASK 0-2)
- `comms/casey-quant.md` — Orchestration priorities
- `SESSION_SUMMARY_20260125.md` — Batch 1 results
- `docs/WORKFLOW_MULTI_ASSET_SCREEN_VALIDATE_PROD.md` — Workflow reference

---

**Created**: 26 janvier 2026, 07:00 UTC  
**Author**: Casey (Orchestrator)  
**Status**: 🟡 AWAITING USER DECISION
