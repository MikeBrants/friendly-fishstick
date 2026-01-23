# Phase 1 Re-screening — RESET COMPLET

**Date:** 24 janvier 2026 02:55 UTC
**Context:** ⚠️ **TOUS LES RÉSULTATS ANTÉRIEURS SONT INVALIDES** (bug Optuna non-déterministe)

---

## 🚨 STATUT: RESET COMPLET REQUIS

### Problème Identifié
- **Optuna TPESampler**: Configuration incorrecte jusqu'au 24/01/2026
- **Impact**: TOUS les résultats (PROD, EXCLUS, PENDING) sont non-reproductibles
- **Solution**: Fix implémenté (`hashlib.md5`, `multivariate=True`, `constant_liar=True`)
- **Conséquence**: ⚠️ **RE-SCREENING OBLIGATOIRE pour TOUS les assets**

### Assets Affectés
- ✅ **15 PROD actuels** → RE-SCREENING requis (params trouvés avec bug)
- ❌ **31+ EXCLUS** → RE-SCREENING requis (décisions basées sur résultats faux)
- ⏸️ **PENDING** → RE-SCREENING requis

**VERDICT:** Repartir à zéro avec système reproductible vérifié.

---

## 📋 STRATÉGIE DE RE-SCREENING

### Phase 0: Reset des Statuts
**Tous les assets retournent en statut "À TESTER"**

**Ancien PROD (15):** BTC, ETH, JOE, OSMO, MINA, AVAX, AR, ANKR, DOGE, OP, DOT, NEAR, SHIB, METIS, YGG  
**Ancien EXCLUS (sélection):** SOL, AAVE, HYPE, ATOM, ARB, LINK, INJ, TIA, RUNE, AXS, CAKE, SEI, TON, HBAR, IMX, EGLD, ICP  
**Nouveaux candidats:** PEPE, ILV, GALA, SAND, MANA, MATIC, BCH, VET, MKR, GRT, ALGO, FTM, RENDER, etc.

---

## 🎯 BATCH PLAN (Total: ~60 assets)

### Batch 1: PROD PRIORITY (15 assets) — URGENT ⭐⭐⭐
**Re-valider les anciens "PROD" en premier (référence baseline)**

```bash
python scripts/run_full_pipeline.py \
  --assets BTC ETH JOE OSMO MINA AVAX AR ANKR DOGE OP DOT NEAR SHIB METIS YGG \
  --workers 10 \
  --trials-atr 200 \
  --trials-ichi 200 \
  --enforce-tp-progression \
  --output-prefix phase1_reset_batch1_prod
```

**Durée estimée:** 45-60 min  
**Attendu:** 10-12 SUCCESS (les meilleurs devraient re-passer)

---

### Batch 2: HIGH CAP PRIORITY (15 assets) — URGENT ⭐⭐⭐
**Top 20 cryptos (haute priorité stratégique)**

```bash
python scripts/run_full_pipeline.py \
  --assets SOL ADA XRP BNB TRX LTC MATIC ATOM LINK UNI ARB OP_ALT HBAR ICP ALGO \
  --workers 10 \
  --trials-atr 200 \
  --trials-ichi 200 \
  --enforce-tp-progression \
  --output-prefix phase1_reset_batch2_highcap
```

**Note:** Certains étaient EXCLU, mais avec bug Optuna, les résultats anciens ne sont pas fiables.

**Durée estimée:** 45 min  
**Attendu:** 3-5 SUCCESS

---

### Batch 3: DEFI + L2 (10 assets) — PRIORITY ⭐⭐
**Protocoles DeFi et L2 scaling**

```bash
python scripts/run_full_pipeline.py \
  --assets AAVE MKR CRV SUSHI RUNE INJ TIA SEI ARB_DUP CAKE \
  --workers 10 \
  --trials-atr 200 \
  --trials-ichi 200 \
  --enforce-tp-progression \
  --output-prefix phase1_reset_batch3_defi
```

**Durée estimée:** 30 min  
**Attendu:** 2-3 SUCCESS

---

### Batch 4: GAMING + MEME (10 assets) — PRIORITY ⭐⭐
**Gaming, Metaverse, Meme tokens**

```bash
python scripts/run_full_pipeline.py \
  --assets PEPE ILV GALA SAND MANA ENJ FLOKI WIF RONIN AXS \
  --workers 10 \
  --trials-atr 200 \
  --trials-ichi 200 \
  --enforce-tp-progression \
  --output-prefix phase1_reset_batch4_gaming_meme
```

**Durée estimée:** 30 min  
**Attendu:** 2-3 SUCCESS

---

### Batch 5: INFRA + STORAGE (10 assets) — PRIORITY ⭐
**Infrastructure, Storage, Oracles**

```bash
python scripts/run_full_pipeline.py \
  --assets FIL GRT THETA VET RENDER FTM EGLD KAVA CFX ROSE \
  --workers 10 \
  --trials-atr 200 \
  --trials-ichi 200 \
  --enforce-tp-progression \
  --output-prefix phase1_reset_batch5_infra
```

**Durée estimée:** 30 min  
**Attendu:** 1-2 SUCCESS

---

## 📊 CRITÈRES PHASE 1 (Screening Souples)

| Métrique | Seuil | Notes |
|----------|-------|-------|
| WFE | > 0.5 | Filtrage grossier |
| Sharpe OOS | > 0.8 | Ordre de grandeur |
| Trades OOS | > 50 | Statistiquement suffisant |

**Ces critères sont INDICATIFS seulement** (workers=10, résultats approximatifs).

---

## 🎯 WORKFLOW POST-SCREENING

### Étape 1: Identifier les SUCCESS (Phase 1)
Après chaque batch, identifier les assets avec:
- WFE > 0.5
- Sharpe OOS > 0.8
- Trades OOS > 50

### Étape 2: Phase 2 Validation (workers=1)
Pour chaque SUCCESS de Phase 1:

```bash
python scripts/run_full_pipeline.py \
  --assets [ASSET] \
  --workers 1 \
  --trials-atr 300 \
  --trials-ichi 300 \
  --enforce-tp-progression \
  --run-guards
```

**Répéter 2x (Run 1, Run 2)** → Vérifier reproducibilité à 100%.

### Étape 3: Guards Validation (7/7 PASS)
- WFE > 0.6
- Sharpe OOS > 1.0
- MC p-value < 0.05
- Sensitivity < 10%
- Bootstrap CI lower > 1.0
- Top10 trades < 40%
- Stress1 Sharpe > 1.0
- Regime mismatch < 1%

### Étape 4: Production
Si 7/7 guards PASS + reproducibilité 100% → **PROD**

---

## 📈 OBJECTIFS

| Objectif | Cible |
|----------|-------|
| Phase 1 total assets | 60 |
| Phase 1 SUCCESS estimé | 15-20 (25-30%) |
| Phase 2 Validation | 15-20 |
| Phase 2 SUCCESS (7/7 guards) | 10-15 |
| **PROD FINAL** | **20+** |

---

## ⏱️ TIMING ESTIMÉ

| Batch | Assets | Durée | Total |
|-------|--------|-------|-------|
| Batch 1 (PROD) | 15 | 45 min | 0h45 |
| Batch 2 (High Cap) | 15 | 45 min | 1h30 |
| Batch 3 (DeFi) | 10 | 30 min | 2h00 |
| Batch 4 (Gaming) | 10 | 30 min | 2h30 |
| Batch 5 (Infra) | 10 | 30 min | 3h00 |
| **TOTAL Phase 1** | **60** | **3h00** | |

**Phase 2 Validation (15 assets x 2 runs x 60 min):** ~30h (parallélisable par asset)

---

## 🚀 COMMANDE RECOMMANDÉE (START NOW)

### Option 1: Batch 1 PROD Only (baseline de référence)
```bash
python scripts/run_full_pipeline.py \
  --assets BTC ETH JOE OSMO MINA AVAX AR ANKR DOGE OP DOT NEAR SHIB METIS YGG \
  --workers 10 \
  --trials-atr 200 \
  --trials-ichi 200 \
  --enforce-tp-progression \
  --output-prefix phase1_reset_batch1_prod
```

### Option 2: Batch 1 + Batch 2 (30 assets, pipeline overnight)
```bash
# Batch 1
python scripts/run_full_pipeline.py \
  --assets BTC ETH JOE OSMO MINA AVAX AR ANKR DOGE OP DOT NEAR SHIB METIS YGG \
  --workers 10 \
  --trials-atr 200 \
  --trials-ichi 200 \
  --enforce-tp-progression \
  --output-prefix phase1_reset_batch1_prod

# Batch 2 (enchainer après Batch 1)
python scripts/run_full_pipeline.py \
  --assets SOL ADA XRP BNB TRX LTC MATIC ATOM LINK UNI ARB HBAR ICP ALGO FTM \
  --workers 10 \
  --trials-atr 200 \
  --trials-ichi 200 \
  --enforce-tp-progression \
  --output-prefix phase1_reset_batch2_highcap
```

---

## 📝 NOTES IMPORTANTES

1. **Pas de sentiment**: Les anciens PROD peuvent FAIL au re-test, les anciens EXCLUS peuvent SUCCESS
2. **Sample size**: Certains assets avaient échoué sur critères fondamentaux (données insuffisantes, low liquidity) → ceux-là peuvent rester EXCLUS
3. **Displacement**: Pour Phase 1, utiliser d52 par défaut. Phase 3A testera d26/d78 si besoin
4. **Filtres**: Phase 1 = baseline (pas de filtres). Phase 4 testera filter modes si besoin

---

## ❌ ASSETS À EXCLURE DÉFINITIVEMENT (Sans Re-test)

**Raisons techniques fondamentales** (pas liées au bug Optuna):

- **HOOK, ALICE, HMSTR, LOOM**: Données insuffisantes (< 8000 bars)
- **APT, EIGEN, ONDO**: Outliers / low sample
- **PIXEL**: Trades < 50 (problème structurel)

**Tous les autres EXCLUS méritent un re-test.**

---

## 🎯 VERDICT CASEY

**Décision:** RESET COMPLET — Re-screening obligatoire pour TOUS les assets  
**Priorité 1:** Batch 1 (15 anciens PROD) — baseline de référence  
**Priorité 2:** Batch 2 (15 High Cap) — expansion portfolio  
**Timeline:** Phase 1 complète = 3h, Phase 2 Validation = 1-2 semaines

**Système reproductible vérifié ✅** — Prêt pour re-screening déterministe.
