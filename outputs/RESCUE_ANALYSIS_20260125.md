# RESCUE ANALYSIS — 25 JAN 2026

## 🎯 OBJECTIF
Sauver les assets FAIL via tests ciblés: displacement grid, filtres, ADX

---

## ❌ AR avec d78 — FALSE HOPE (6/8 Guards PASS)

### AR Displacement Grid Results

| Displacement | OOS Sharpe | WFE | Trades | Status |
|--------------|------------|-----|--------|--------|
| d78 | 3.38 → 2.08 | 1.79 → 1.10 | 32 | FAIL (guards) |
| d52 (baseline) | 1.25 | 0.36 | 38 | FAIL |
| d26 | -1.16 | -0.45 | 40 | FAIL |

**Note**: Variance entre test grid (3.38) et pipeline full (2.08) = 60 trials différents, seed différent

### AR Guards Results (6/8 PASS)

| Guard | Valeur | Seuil | Status |
|-------|--------|-------|--------|
| guard001 (MC p-value) | 0.001 | < 0.05 | ✅ |
| **guard002 (Sensitivity)** | **23.99%** | **< 10%** | ❌ |
| guard003 (Bootstrap CI) | 1.38 | > 1.0 | ✅ |
| guard005 (Top10 trades) | 30.93% | < 40% | ✅ |
| guard006 (Stress1) | 1.63 | > 1.0 | ✅ |
| guard007 (Regime) | 0.0% | < 1% | ✅ |
| WFE | 1.10 | > 0.6 | ✅ |
| **Trades OOS** | **32** | **> 50** | ❌ |

**Verdict**: AR BLOCKED (2 failures critiques)
1. **Sensibilité paramètres**: 23.99% >> 10% (guard002 FAIL)
2. **Trade count**: 32 < 50 minimum (structurel avec d78)

**Explication**: Le displacement d78 améliore le WFE mais crée deux problèmes:
- Réduit le sample size (32 trades insuffisant)
- Augmente la sensibilité aux paramètres (23.99% de variance)

**Leçon**: WFE élevé seul ne garantit pas la robustesse. Guards détectent overfitting caché.

---

## ⚠️ OSMO: Amélioration mais insuffisant

### OSMO Displacement Grid Results

| Displacement | OOS Sharpe | WFE | Trades | Status |
|--------------|------------|-----|--------|--------|
| d78 (best) | 1.47 | 0.38 | 57 | FAIL |
| d52 (baseline) | 0.18 | 0.05 | 54 | FAIL |
| d26 | -2.30 | -0.50 | 114 | FAIL |

**Amélioration**: WFE +660% (0.05 → 0.38), mais toujours < 0.6

**Verdict**: OSMO reste BLOCKED. WFE max = 0.38 avec d78, insuffisant

---

## 📊 METIS: Baseline = Vol-Profile

### METIS Test Results

| Config | OOS Sharpe | WFE | Trades | Status |
|--------|------------|-----|--------|--------|
| Baseline | 1.80 | 0.60 | 87 | FAIL (trades < 60 min) |
| Vol-Profile | 1.80 | 0.60 | 87 | FAIL (identique) |

**Conclusion**: Les filtres vol-profile n'apportent rien sur METIS. Problème = trade count insuffisant

**Verdict**: METIS reste BLOCKED (87 trades < 60 min OOS)

---

## 🆕 NOUVEAUX ASSETS TESTÉS

### ADA — PARTIAL SUCCESS (4/7 Guards PASS) ⚠️

| Métrique | Valeur | Critère | Status |
|----------|--------|---------|--------|
| OOS Sharpe | 1.92 | > 1.0 | ✅ |
| WFE | 0.61 | > 0.6 | ✅ |
| Trades | 90 | > 60 | ✅ |
| Displacement | 52 | Standard | ✅ |

**Config**: SL=2.5, TP1=2.5, TP2=4.5, TP3=10.0, Tenkan=9, Kijun=33

**Guards Results (4/7 PASS)**:
- ✅ guard001 (MC p-value): 0.0 < 0.05
- ❌ guard002 (Sensitivity): 19.38% > 10%
- ❌ guard003 (Bootstrap CI): 0.79 < 1.0
- ✅ guard005 (Top10 trades): 30.17% < 40%
- ❌ guard006 (Stress1): 0.95 < 1.0
- ✅ guard007 (Regime): 0.0% < 1%
- ✅ WFE: 0.61 > 0.6

**Verdict**: ADA FAIL (nécessite 7/7 guards). Sensibilité paramètres trop élevée (19.38%)

**Action**: Test avec filtres ou displacement alternatif pour réduire sensibilité

### FIL — IRONIC FAIL (6/7 Guards PASS but WFE FAIL) 🤔

| Métrique | Valeur | Critère | Status |
|----------|--------|---------|--------|
| OOS Sharpe | -0.22 | > 1.0 | ❌ |
| WFE | -0.06 | > 0.6 | ❌ |
| Trades | 56 | > 60 | ❌ |

**Guards Results (6/7 PASS)**:
- ✅ guard001 (MC p-value): 0.0 < 0.05
- ✅ guard002 (Sensitivity): 7.27% < 10%
- ✅ guard003 (Bootstrap CI): 1.71 > 1.0
- ✅ guard005 (Top10 trades): 16.31% < 40%
- ✅ guard006 (Stress1): 1.57 > 1.0
- ✅ guard007 (Regime): ~0.0% < 1%
- ❌ WFE: -0.06 < 0.6 (NÉGATIF!)

**Verdict**: FIL BLOCKED — Ironie: passe 6/7 guards mais WFE négatif = reverse overfit (OOS < 0, IS > 0)

**Explication**: FIL dégrade fortement IS→OOS (WFE=-0.06), les guards détectent la robustesse statistique mais la performance réelle est inexistante

---

## 📈 SYNTHÈSE RESCUE

### Assets RESCUED ✅

**AUCUN** — Tous les tests ont échoué la validation complète

### Assets BLOCKED ❌

| Asset | Best Config | WFE | Trades | Guards | Raison | Verdict |
|-------|-------------|-----|--------|--------|--------|---------|
| AR | d78 | 1.10 | 32 | 6/8 | Sensibilité 24% + trades < 50 | DEFINITIF |
| OSMO | d78 | 0.38 | 57 | N/A | Overfit sévère | DEFINITIF |
| METIS | Baseline/Vol | 0.60 | 87 | N/A | Trade count < 60 min | DEFINITIF |
| FIL | Baseline | -0.06 | 56 | 6/7 | Reverse overfit (WFE négatif) | DEFINITIF |
| OP | ADX>30 | 2.04 | **6** | N/A | Sample size ridiculement bas | DEFINITIF |
| ADA | Baseline | 0.61 | 90 | 4/7 | Sensibilité params 19% > 10% | Rescue possible (filtres/disp)

### OP — ADX Filter Test (PARADOXE) 🤔

| ADX Threshold | IS Sharpe | OOS Sharpe | WFE | OOS Trades | Status |
|---------------|-----------|------------|-----|------------|--------|
| Baseline (none) | 3.07 | 0.90 | **0.29** | 90 | FAIL |
| 20.0 | 3.70 | -0.20 | -0.05 | 33 | WORSE |
| 25.0 | 1.84 | 3.44 | 1.86 | 12 | WFE PASS, trades FAIL |
| **30.0** | 1.30 | 2.64 | **2.04** | **6** | WFE PASS, **trades FAIL** |

**Paradoxe ADX**: WFE passe de 0.29 → 2.04 (+600%) avec ADX>30, MAIS seulement 6 trades OOS (< 60 min)

**Explication**: ADX>30 = filtre extrêmement sélectif
- Garde uniquement les meilleurs trades (trending fort)
- WFE excellent mais sample size insignifiant
- **Résultat non exploitable** (6 trades = 0 significativité statistique)

**Verdict**: OP reste BLOCKED. ADX améliore WFE mais détruit sample size.

**Learning**: Les filtres trop stricts créent des "cherry-picked" backtests non généralisables

---

## 🔍 INSIGHTS DÉCOUVERTS

### 1. Displacement Sensitivity (HIGH IMPACT)

**AR Case Study**: 
- d52 → WFE=0.36 (FAIL)
- d78 → WFE=1.79 (PASS)
- Delta: +400%

**Règle empirique**:
- Majeurs (BTC, ETH): d52
- L2/Infrastructure (AR, OP, ARB): **d78**
- Meme/Fast (DOGE, SHIB): d26
- Cosmos (OSMO): d65-78 (mais insuffisant ici)

### 2. Vol-Profile Filters = Neutre sur METIS

Les filtres adaptatifs vol-profile n'améliorent pas METIS. Le problème est structurel (low sample).

### 3. Trade Count = Hard Constraint

METIS WFE=0.60 mais 87 trades < 60 min → FAIL
ADA WFE=0.61 avec 90 trades > 60 min → PASS

**Minimum viable**: 60 trades OOS (statistiquement significatif)

---

## 🎯 ACTIONS IMMÉDIATES

### Priority 1 — Guards Validation

```bash
# AR avec d78 (WFE=1.79, très prometteur)
python scripts/run_guards_multiasset.py --assets AR --fixed-displacement 78 --workers 1

# ADA baseline (WFE=0.61, standard)
python scripts/run_guards_multiasset.py --assets ADA --workers 1
```

### Priority 2 — Attendre Test B

OP + ADX en cours, ETA ~5 min

---

## 📊 BILAN GLOBAL

| Statut | Count | Assets |
|--------|-------|--------|
| RESCUE POSSIBLE | 1 | ADA (4/7 guards, sensibilité 19%) |
| BLOCKED DEFINITIF | 5 | AR, OSMO, METIS, FIL, OP |

**ROI Rescue Mission**: 0 succès, 1 candidat potentiel (ADA), 5 échecs définitifs

**Taux de réussite**: 0% (0/6 validés), 16% si ADA rescué

**Leçons clés**:
1. **WFE élevé ≠ robustesse**: AR avait WFE=1.79 mais FAIL guards (sensibilité 24%, trades < 50)
2. **Filtres stricts = cherry-picking**: OP ADX améliore WFE +600% mais tue sample (6 trades)
3. **Guards sont essentiels**: Détectent overfitting caché même avec WFE > 1.0

---

**Timestamp**: 2026-01-25 20:15 UTC
**Author**: AI Agent (Jordan-dev role)
