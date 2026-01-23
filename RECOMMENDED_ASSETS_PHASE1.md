# Assets Recommandés pour Phase 1 Re-screening

**Date:** 24 janvier 2026
**Context:** Système reproductible vérifié, prêt pour Phase 1 avec workers=10

---

## 📊 État Actuel

### ✅ PROD (15 assets) — FROZEN
BTC, ETH, JOE, OSMO, MINA, AVAX, AR, ANKR, DOGE, OP, DOT, NEAR, SHIB, METIS, YGG

### ❌ EXCLUS (31+ assets) — Ne pas retester
SEI, CAKE, AXS, RUNE, TON, SOL, AAVE, HYPE, ATOM, ARB, LINK, INJ, TIA, HOOK, ALICE, HMSTR, LOOM, APT, EIGEN, ONDO, ICP, ARKM, EGLD, UNI, STRK, AEVO, HBAR, IMX, BNB, XRP, ADA, TRX, LTC, XLM

---

## 🎯 Assets Prioritaires (Batch 1 — 20 assets)

### Groupe A: Phase 1 Batch 3 à RE-TESTER (10 assets)
**Raison:** Résultats anciens non-reproductibles, méritent re-test avec système deterministic

| Asset | Old Result | Category | Priority |
|-------|------------|----------|----------|
| **PEPE** | Sharpe 1.09, WFE 0.37 (old FAIL) | Meme | ⭐⭐⭐ |
| **ILV** | Sharpe 1.97, WFE 0.57 (old FAIL) | Gaming | ⭐⭐⭐ |
| **GALA** | Sharpe -0.11 (old FAIL) | Gaming | ⭐⭐ |
| **SAND** | Sharpe 1.24, WFE 0.47 (old FAIL) | Metaverse | ⭐⭐ |
| **MANA** | Sharpe 1.27, WFE 0.58 (old FAIL) | Metaverse | ⭐⭐ |
| **FIL** | Sharpe -0.30 (old FAIL) | Storage | ⭐ |
| **THETA** | Sharpe 0.18 (old FAIL) | Streaming | ⭐ |
| **CHZ** | Sharpe 0.95 (old FAIL) | Fan Token | ⭐ |
| **CRV** | Sharpe 0.89 (old FAIL) | DeFi | ⭐ |
| **SUSHI** | Sharpe 1.58, WFE 0.41 (old FAIL) | DeFi | ⭐⭐ |

### Groupe B: Top 50 Non-testés (10 assets)
**Raison:** Assets du Top 50 jamais testés avec système reproductible

| Asset | Category | Market Cap Tier | Priority |
|-------|----------|-----------------|----------|
| **MATIC** (POL) | L2 Scaling | Tier 2 | ⭐⭐⭐ |
| **BCH** | Bitcoin Fork | Tier 2 | ⭐⭐ |
| **VET** | Supply Chain | Tier 3 | ⭐⭐ |
| **MKR** | DeFi | Tier 3 | ⭐⭐⭐ |
| **GRT** | Indexing | Tier 3 | ⭐⭐ |
| **SUI** | L1 (EXCLU old) | Tier 3 | ⭐ (re-test?) |
| **ALGO** | L1 | Tier 3 | ⭐⭐ |
| **FTM** | L1 | Tier 3 | ⭐⭐ |
| **FLOW** | NFT Platform | Tier 4 | ⭐ |
| **RENDER** | GPU Network | Tier 4 | ⭐⭐ |

---

## 🚀 Assets Bonus (Batch 2 — 15 assets)

### High Potential / Trending
| Asset | Category | Notes |
|-------|----------|-------|
| **WIF** | Meme | Old FAIL mais populaire |
| **BONK** | Meme | Pas encore testé |
| **JUP** | DEX | Solana ecosystem |
| **W** | Bridge | Wormhole |
| **PYTH** | Oracle | Pas encore testé |
| **JTO** | Staking | Jito on Solana |
| **WLD** | AI | Worldcoin |

### Gaming/Metaverse
| Asset | Category | Notes |
|-------|----------|-------|
| **ENJ** | Gaming NFT | Old FAIL, re-test |
| **FLOKI** | Gaming Meme | Old FAIL, re-test |
| **RONIN** | Gaming Chain | Old FAIL, re-test |
| **PIXEL** | Gaming | Old FAIL (trades < 50) |

### Infra/L1
| Asset | Category | Notes |
|-------|----------|-------|
| **KAVA** | DeFi Platform | Old FAIL, re-test |
| **CFX** | L1 | Old FAIL, re-test |
| **ROSE** | Privacy L1 | Old FAIL, re-test |
| **EOS** | L1 | Jamais testé |

---

## 📋 Commande Recommandée (Batch 1)

### Option 1: Prioritaire (10 assets — 30 min)
```bash
python scripts/run_full_pipeline.py \
  --assets PEPE ILV GALA SAND MANA MATIC BCH VET MKR GRT \
  --workers 10 \
  --trials-atr 200 \
  --trials-ichi 200 \
  --enforce-tp-progression \
  --output-prefix phase1_rescreening_batch1_v1
```

### Option 2: Complet (20 assets — 45 min)
```bash
python scripts/run_full_pipeline.py \
  --assets PEPE ILV GALA SAND MANA FIL THETA CHZ CRV SUSHI \
           MATIC BCH VET MKR GRT ALGO FTM FLOW RENDER SUI \
  --workers 10 \
  --trials-atr 200 \
  --trials-ichi 200 \
  --enforce-tp-progression \
  --output-prefix phase1_rescreening_batch1_v2
```

---

## 🎯 Critères Phase 1 (Screening souples)

| Métrique | Seuil | Notes |
|----------|-------|-------|
| WFE | > 0.5 | Filtrage grossier |
| Sharpe OOS | > 0.8 | Ordre de grandeur |
| Trades OOS | > 50 | Statistiquement suffisant |

**Attendu:** 4-5 SUCCESS par 20 assets (~20-25% success rate)

---

## ⚠️ Assets à ÉVITER

**Ne PAS re-tester** (déjà EXCLU après multiples tentatives):
- SOL, AAVE, HYPE, ATOM, ARB, LINK, INJ, TIA (EXCLU Tier 1-2)
- HBAR, IMX (variants épuisés)
- BNB, XRP, ADA, TRX, LTC, XLM (Phase 1 old FAIL)
- UNI (moderate mode FAIL)

---

## 📊 Stratégie de Batching

**Batch 1** (prioritaire): PEPE, ILV, MATIC, MKR + 6 autres high-potential
**Batch 2** (si Batch 1 < 4 SUCCESS): Bonus + Gaming/Metaverse
**Batch 3** (expansion): Assets hors Top 50 (JOE, OSMO, MINA patterns)

**Objectif:** Trouver 5+ nouveaux assets pour atteindre 20+ PROD total
