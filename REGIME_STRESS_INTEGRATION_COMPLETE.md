# Regime Stress Test Integration — COMPLETE

**Date**: 26 janvier 2026, 17:00 UTC  
**Owner**: Casey (Orchestrator)  
**Status**: ✅ **COMPLETE** — Phase 2B intégrée au pipeline

---

## Modifications Effectuées

### 1. Pipeline FINAL TRIGGER v2 : 6 → 7 Phases ⚡

**Nouvelle Phase 2B ajoutée:**

| Phase | Nom | Criteres/Output |
|-------|-----|-----------------|
| 0 | Download | `data/*.parquet` |
| 1 | Screening | 200 trials, guards OFF, WFE>0.5, Sharpe>0.8, Trades>50 |
| 2 | Validation | 300 trials, 7 guards ON -> WINNERS + PENDING |
| **2B** | **Regime Stress** | **MARKDOWN + SIDEWAYS test -> PASS/EXCLU** ⚡ NEW |
| 3A | Rescue | PENDING: d26/d52/d78, 8/8 PASS -> WINNERS |
| 3B | Optimization | WINNERS: d26/d52/d78, +10% ET 8/8 PASS -> remplace |
| 4 | Filter Rescue | PENDING: baseline → moderate → conservative |
| 5 | Production | `asset_config.py` + `project-state.md` |

---

### 2. Guards System : 7 → 8 Guards ⚡

**Nouveau guard008 ajouté:**

| Guard | ID | Seuil | Critique |
|-------|:---|-------|----------|
| WFE (Walk-Forward Efficiency) | - | >=0.6 | OUI |
| Monte Carlo p-value | guard001 | <0.05 | OUI |
| Sensitivity variance | guard002 | <15% | OUI |
| Bootstrap CI lower bound | guard003 | >1.0 | OUI |
| Top 10 trades contribution | guard005 | <40% | OUI |
| Stress1 Sharpe | guard006 | >1.0 | OUI |
| Regime mismatch | guard007 | <1% | OUI |
| **Regime Stress (SIDEWAYS)** | **guard008** | **Sharpe > 0** | **OUI** ⚡ NEW |

**GATE**: 8/8 PASS obligatoire avant tout merge.

---

### 3. Arbre de Décision — Ajout Branche Regime Stress

```
Quel guard FAIL?
├── WFE < 0.6 ──────────> Tester autre displacement
├── MC p > 0.05 ────────> Plus de donnees ou trials
├── Sensitivity > 15% ──> Filter Rescue (baseline → moderate → conservative)
├── Top10 > 40% ────────> Donnees insuffisantes
├── **Regime Stress FAIL** ─> EXCLU ou position réduite (Casey decide)
│     ├── SIDEWAYS Sharpe < -1.0 ──> EXCLU définitif
│     └── SIDEWAYS Sharpe [-1, 0] ──> Position 0.5× ou EXCLU
└── Autre ──────────────> BLOCKED, documenter raison
```

---

### 4. Section GUARD-008 Complète (global-quant.mdc)

**Critères:**
| Régime | PASS | REVIEW | FAIL |
|--------|------|--------|------|
| MARKDOWN | Trades < 10 OR Sharpe ≥ 0 | Sharpe ∈ [-1, 0) sur >10 trades | Sharpe < -1.0 sur >10 trades |
| SIDEWAYS | Sharpe > 0 | Sharpe ∈ [-0.5, 0] | Sharpe < -0.5 |

**Commandes:**
```bash
# Test single asset
python scripts/run_regime_stress_test.py --asset ETH --regime SIDEWAYS

# Test all PROD assets
python scripts/run_regime_stress_test.py --all-assets --regime SIDEWAYS
```

**Cas exclus (26 Jan 2026):**
- EGLD: SIDEWAYS Sharpe -4.59 → EXCLU
- AVAX: SIDEWAYS Sharpe -0.36 → EXCLU

---

## Impact Portfolio

### Avant Integration
- Assets PROD: 14
- Mean Sharpe: 3.17
- Progress: 70% du goal (14/20)

### Après Integration
- Assets PROD: **12** (EGLD, AVAX exclus)
- Mean Sharpe: **3.35** (amélioration après exclusion)
- Progress: **60%** du goal (12/20)

### Assets PROD Validés (12)

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

---

## Fichiers Modifiés

### Configuration
1. `.cursor/rules/MASTER_PLAN.mdc`
   - Phase 2B ajoutée dans WORKFLOW STANDARD
   - Guards table: 7 → 8 guards (guard008 ajouté)
   - Arbre de décision: branche Regime Stress ajoutée
   - Assets PROD: 14 → 12 (EGLD/AVAX exclus)
   - Priorités actuelles mises à jour
   - Métriques de succès mises à jour

2. `.cursor/rules/global-quant.mdc`
   - Guards table: 7 → 8 guards
   - Section GUARD-008 complète (critères, commandes, cas exclus)

3. `.cursor/rules/workflow.mdc`
   - Pipeline: 6 → 7 phases
   - Phase 2B ajoutée
   - Commandes Phase 2B ajoutées

### Documentation
4. `crypto_backtest/config/scan_assets.py`
   - EXCLUDED_ASSETS: EGLD, AVAX ajoutés

5. `comms/casey-quant.md`
   - Section CRITICAL UPDATE ajoutée
   - Décision EGLD/AVAX documentée

6. `status/project-state.md`
   - Category 1: 14 → 12 assets
   - EGLD/AVAX marqués EXCLUDED

7. `ETAT_ACTUEL_20260126.md`
   - Portfolio mis à jour (12 assets)
   - Mean Sharpe: 3.35

---

## Commit & Push

**Commit 1**: `d934f0e` - "fix: exclude EGLD and AVAX from PROD (Regime Stress FAIL)"  
**Commit 2**: `0b70ea6` - "feat: integrate regime stress test as Phase 2B (guard008)"

**Push**: réussi vers `origin/main`

---

## Prochaines Étapes

### Phase 2B Application

**Pour tous nouveaux assets PASS Phase 2:**
1. Exécuter regime stress test (MARKDOWN + SIDEWAYS)
2. Valider Sharpe > 0 sur SIDEWAYS (critique)
3. Sam valide les résultats
4. Casey verdict: PASS/REVIEW/FAIL

### Assets Actuels

**12 assets PROD validés** avec 8/8 guards (incluant Regime Stress)

**Confiance:**
- Tous les assets survivent SIDEWAYS (Sharpe > 0)
- Stratégie évite naturellement MARKDOWN
- Portfolio robuste aux changements de régime

---

## Référence

**Reports:**
- `outputs/STRESS_TEST_REPORT_20260126.md` — Résultats complets
- `REGIME_DATA_CORRECTION_20260126.md` — Correction données obsolètes

**Script:**
- `scripts/run_regime_stress_test.py` — TASK 3 deliverable

---

**Créé**: 26 janvier 2026, 17:00 UTC  
**Status**: ✅ INTEGRATION COMPLETE — Pipeline upgraded to 7 phases with guard008
