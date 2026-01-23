# Variants Proposés pour HBAR - 2026-01-22

## État Actuel (medium_distance_volume)

**Résultats scan:**
- Status: SUCCESS ✅
- OOS Sharpe: 1.28 (acceptable, >1.0)
- WFE: 0.63 (PASS mais proche limite 0.6)
- OOS Trades: 107 (>60 ✅)
- Params: sl=1.5, tp1=2.5, tp2=6.5, tp3=10.0, tenkan=7, kijun=20, displacement=52

**Guards:**
- Guard001 (MC p-value): 0.01 → PASS ✅
- Guard002 (Sensitivity): **11.49%** → FAIL ❌ (>10%, limite)
- Guard003 (Bootstrap CI): **0.30** → FAIL ❌ (<1.0, critique)
- Guard005 (Top10 trades): **41.05%** → FAIL ❌ (>40%, limite)
- Guard006 (Stress1 Sharpe): **0.62** → FAIL ❌ (<1.0, critique)
- Guard007 (Regime mismatch): 0.00% → PASS ✅
- WFE: 0.63 → PASS ✅

**Verdict:** 4/7 guards FAIL. Le mode `medium_distance_volume` n'a pas résolu les problèmes.

---

## Variants Proposés (par ordre de priorité)

### Option 1: Displacement d26 (Fast - comme JOE) ⭐ PRIORITAIRE

**Rationale:**
- JOE (même catégorie "fast") a réussi avec d26 (Sharpe 5.03, WFE 1.44)
- HBAR pourrait bénéficier d'un displacement plus court pour plus de trades
- Réduire le risque de dépendance à quelques gros trades (guard005)

**Commande:**
```bash
python scripts/run_full_pipeline.py \
  --assets HBAR \
  --workers 6 \
  --trials-atr 150 \
  --trials-ichi 150 \
  --enforce-tp-progression \
  --fixed-displacement 26 \
  --skip-download \
  --run-guards
```

**Critères de succès:**
- Guard002 < 10%
- Guard003 > 1.0
- Guard005 < 40%
- Guard006 > 1.0
- WFE > 0.6

---

### Option 2: Displacement d78 (Slow - comme MINA)

**Rationale:**
- MINA a réussi avec d78 (Sharpe 1.76, WFE 0.61)
- Displacement plus long pourrait réduire la sensibilité (guard002)
- Moins de trades mais plus robustes

**Commande:**
```bash
python scripts/run_full_pipeline.py \
  --assets HBAR \
  --workers 6 \
  --trials-atr 150 \
  --trials-ichi 150 \
  --enforce-tp-progression \
  --fixed-displacement 78 \
  --skip-download \
  --run-guards
```

**Critères de succès:** Identiques à Option 1

---

### Option 3: Filter Mode `light_distance` ou `light_volume`

**Rationale:**
- ETH a réussi avec `medium_distance_volume` (2 filtres)
- HBAR pourrait nécessiter un seul filtre (plus léger)
- Réduire la variance sans trop sacrifier les trades

**Commande:**
```bash
# Option 3A: light_distance
python scripts/run_full_pipeline.py \
  --assets HBAR \
  --workers 6 \
  --trials-atr 150 \
  --trials-ichi 150 \
  --enforce-tp-progression \
  --optimization-mode light_distance \
  --skip-download \
  --run-guards

# Option 3B: light_volume
python scripts/run_full_pipeline.py \
  --assets HBAR \
  --workers 6 \
  --trials-atr 150 \
  --trials-ichi 150 \
  --enforce-tp-progression \
  --optimization-mode light_volume \
  --skip-download \
  --run-guards
```

**Critères de succès:** Identiques à Option 1

---

## Recommandation Finale

**Ordre d'exécution suggéré:**

1. **d26 (Option 1)** — Priorité haute
   - Pattern similaire à JOE (fast asset)
   - Plus de trades = meilleure distribution (guard005)
   - Risque modéré, gain potentiel élevé

2. **d78 (Option 2)** — Si Option 1 échoue
   - Pattern similaire à MINA (slow asset)
   - Moins de sensibilité (guard002)
   - Risque modéré

3. **light_distance/volume (Option 3)** — Dernier recours
   - Si les displacements ne fonctionnent pas
   - Tester un filtre léger
   - Risque faible mais gain incertain

**Si toutes les options échouent:** BLOCKED — HBAR ne passe pas les guards avec les variants testés.

---

## Analyse des Guards Critiques

### Guard003 (Bootstrap CI 0.30) — CRITIQUE
- **Problème:** CI lower très bas = performance non robuste
- **Solution potentielle:** Plus de trades (d26) ou meilleure distribution (filters)

### Guard006 (Stress1 Sharpe 0.62) — CRITIQUE
- **Problème:** Performance dégradée sous stress
- **Solution potentielle:** Displacement plus long (d78) pour robustesse

### Guard002 (Sensitivity 11.49%) — LIMITE
- **Problème:** Juste au-dessus de 10%
- **Solution potentielle:** Filters pour réduire la variance

### Guard005 (Top10 trades 41.05%) — LIMITE
- **Problème:** Dépendance à quelques gros trades
- **Solution potentielle:** Plus de trades (d26) pour meilleure distribution

---

**Date:** 2026-01-22 23:30  
**Auteur:** @Jordan  
**Prochaine action:** Exécuter Option 1 (d26) et évaluer les résultats
