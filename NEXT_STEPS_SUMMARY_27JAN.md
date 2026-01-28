# Next Steps Summary — 27 Jan 2026

**Status**: PR#21 COMPLETE — 5 PROD assets validated

---

## ✅ Actions Complétées

### 1. MAJ project-state.md — PR#21 Classification
- **Status**: ✅ DONE
- **Changes**: 
  - Updated header: "PR#21 COMPLETE — 100 Trials Validation"
  - 5 PROD assets: SOL, AVAX, ETH, BTC, AXS
  - 3 QUARANTINE: EGLD, TON, ONE
  - 10 EXCLU (PBO ≥0.70)

### 2. MAJ MASTER_PLAN.mdc — Default Trials 300→100
- **Status**: ✅ DONE
- **Changes**:
  - Phase 2 Validation: 300 → **100 trials**
  - Phase 3 Rescue: 300 → **100 trials**
  - Version: 2.1 → 2.2 (27 Jan 2026)
- **Rationale**: PR#21 confirms 100 trials eliminates systematic overfitting (PBO: 0.73 → 0.35 avg)

---

## 📋 Actions Préparées (Scripts Créés)

### 3. Phase 4 Regime Stress — TIER 1 SIDEWAYS Test
- **Script**: `scripts/run_regime_stress_tier1.sh`
- **Assets**: SOL, AVAX, ETH, BTC, AXS
- **Criterion**: SIDEWAYS Sharpe > 0
- **Command**:
  ```bash
  bash scripts/run_regime_stress_tier1.sh
  ```
- **Expected output**: `outputs/tier1_sideways_*`

### 4. Phase 5 Portfolio — Correlation Check
- **Script**: `scripts/check_portfolio_correlations.py`
- **Assets**: 5 PROD assets (TIER 1)
- **Criterion**: Correlations < 0.5 between all pairs
- **Command**:
  ```bash
  python scripts/check_portfolio_correlations.py
  ```
- **Expected output**: `outputs/portfolio_correlations_tier1.csv`

### 5. Challenger ETH/YGG — CSCV PBO Test
- **Script**: `scripts/run_cscv_pbo_challenger.py`
- **Assets**: ETH, YGG
- **Method**: True CSCV (Combinatorial Split Cross-Validation) post PR#31
- **Command**:
  ```bash
  python scripts/run_cscv_pbo_challenger.py
  ```
- **Note**: Requires returns_matrix files for ETH/YGG
- **Expected output**: `outputs/cscv_pbo_challenger_eth_ygg.csv`

---

## 🎯 Workflow Recommandé

### Séquence Immédiate

1. **Phase 4 Regime Stress** (ETA: 30 min)
   ```bash
   bash scripts/run_regime_stress_tier1.sh
   ```
   - Valide que les 5 PROD assets ont SIDEWAYS Sharpe > 0
   - Critère PASS obligatoire pour production

2. **Phase 5 Portfolio** (ETA: 2 min)
   ```bash
   python scripts/check_portfolio_correlations.py
   ```
   - Vérifie diversification du portfolio
   - Identifie assets trop corrélés (>0.5)

3. **Validation CSCV** (ETA: 5 min, si returns_matrix disponibles)
   ```bash
   python scripts/run_cscv_pbo_challenger.py
   ```
   - Test ETH/YGG avec méthode CSCV (PR#31)
   - Compare avec PBO standard

---

## 📊 Critères de Validation

| Phase | Critère | Seuil | Action si FAIL |
|-------|---------|-------|----------------|
| **Phase 4** | SIDEWAYS Sharpe | > 0 | EXCLU ou position réduite |
| **Phase 5** | Corrélations | < 0.5 | Retirer asset le plus corrélé |
| **CSCV** | PBO (CSCV) | < 0.50 | Validation robustesse |

---

## 🔄 Si Échecs Détectés

### Phase 4 FAIL (SIDEWAYS Sharpe < 0)
- **Action**: EXCLU asset ou réduire position à 50%
- **Exemple historique**: EGLD (-4.59), AVAX (-0.36) exclus 26 Jan

### Phase 5 FAIL (Corrélation ≥ 0.5)
- **Action**: Retirer 1 asset du portfolio
- **Critère retrait**: Asset avec corrélation moyenne la plus élevée
- **Recalculer** corrélations avec portfolio réduit

### CSCV FAIL (PBO ≥ 0.50)
- **Action**: QUARANTINE ou EXCLU
- **Investigation**: Comparer PBO standard vs CSCV
- **Si divergence**: Privilégier CSCV (plus robuste)

---

## 📁 Fichiers Modifiés

| Fichier | Type | Description |
|---------|------|-------------|
| `status/project-state.md` | ✅ Updated | PR#21 status, 5 PROD assets |
| `.cursor/rules/MASTER_PLAN.mdc` | ✅ Updated | Trials 300→100, version 2.2 |
| `scripts/run_regime_stress_tier1.sh` | 🆕 Created | Phase 4 script |
| `scripts/check_portfolio_correlations.py` | 🆕 Created | Phase 5 script |
| `scripts/run_cscv_pbo_challenger.py` | 🆕 Created | CSCV test script |

---

## 📅 Timeline Suggéré

| Jour | Action | Owner |
|------|--------|-------|
| **27 Jan PM** | Phase 4 Regime Stress | Jordan |
| **27 Jan PM** | Phase 5 Portfolio | Jordan/Casey |
| **28 Jan AM** | CSCV Validation | Jordan/Alex |
| **28 Jan PM** | Final PR#22 (si tous PASS) | Casey |

---

## 🎯 Objectif Final

**Portfolio PROD Ready:**
- 5 assets validés (ou 3-4 si Phase 4/5 FAIL)
- Tous critères PASS:
  - ✅ 7/7 hard guards
  - ✅ PBO < 0.50 (100 trials)
  - ✅ SIDEWAYS Sharpe > 0
  - ✅ Corrélations < 0.5
  - ✅ CSCV PBO < 0.50 (validation robustesse)

---

**Generated**: 27 Jan 2026, 20:20 UTC  
**Version**: 1.0  
**Owner**: Casey (Orchestrator)
