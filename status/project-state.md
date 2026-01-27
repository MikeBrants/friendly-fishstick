# PROJECT STATE — FINAL TRIGGER v2

**Updated**: 27 Jan 2026, 19:08 UTC+4
**Phase**: 🔴 **CONTINGENCY MODE — Plan A en cours**
**Status**: 12/18 EXCLU PBO, 1 PROD (AXS), 3 QUARANTINE

> Pour les paramètres → `.cursor/rules/MASTER_PLAN.mdc`  
> Pour les commandes → `docs/WORKFLOW_PIPELINE.md`

---

## ⚠️ RÈGLES DE MISE À JOUR

**CE FICHIER CHANGE SOUVENT** — Mettre à jour:
- Après chaque Phase complétée
- Quand un asset change de status (PENDING → PROD ou → EXCLU)
- Max 1× par jour sauf urgence

**FORMAT OBLIGATOIRE:**
- Header "Updated" : toujours mettre à jour la date
- Assets : listes simples, pas de tableaux détaillés
- Historique : garder **max 10 entrées** (supprimer les plus anciennes)

**OWNER:** Casey (Orchestrateur) — Seul autorisé à modifier ce fichier

---

## 🚨 ALERTE CRITIQUE — OVERFITTING SYSTÉMIQUE

**Résultat PR#20 Batch 1-3** : 12/18 assets EXCLU pour PBO ≥0.70

| Verdict | Count | Assets |
|---------|:-----:|--------|
| ✅ PROD | 1 | AXS (PBO 0.33) |
| ⚠️ QUARANTINE | 3 | EGLD, TON, ONE |
| 🔴 EXCLU PBO | 12 | CAKE, RUNE, MINA, YGG, SOL, AVAX, BTC, HBAR, SUSHI, CRV, SEI, AAVE |
| 🔴 EXCLU Sharpe<0 | 2 | GALA, ZIL |
| ⏸️ NON TRAITÉS | 8 | SHIB, DOT, TIA, NEAR, DOGE, ANKR, ETH, JOE |

**Cause probable** : 300 trials → n_combinations = 12 870 → overfit systémique

---

## 📊 ASSET STATUS

### ✅ PROD (1)

```
AXS (PBO 0.33, Sharpe 1.21, 7/7 guards PASS)
```

### ⚠️ QUARANTINE (3)

```
EGLD (PBO 0.50-0.70, à revalider)
TON (PBO 0.50-0.70, à revalider)
ONE (PBO 0.50-0.70, à revalider)
```

### ❌ EXCLU (14)

```
PBO ≥0.70: CAKE RUNE MINA YGG SOL AVAX BTC HBAR SUSHI CRV SEI AAVE
Sharpe OOS <0: GALA ZIL
```

### ⏸️ NON TRAITÉS (8)

```
SHIB DOT TIA NEAR DOGE ANKR ETH JOE
```

---

## 🎯 PLAN DE CONTINGENCY

### Plan A — Challenger 100 Trials (EN COURS)

```
Hypothèse: Réduire trials 300→100 diminue overfit
Assets: BTC ETH SOL AVAX
Critère succès: ≥2/4 PBO <0.50
ETA: ~4h
```

### Plan B — Contraindre Bounds Optuna (SI Plan A FAIL)

```
Bounds: tenkan 9-26, kijun 20-52, atr_mult 1.0-3.0
Fichier: scripts/optuna_config.py
```

### Plan C — Diagnostic Long/Short (SI Plan A+B FAIL)

```
Issue: #30
Phases: C1 (sélection) → C2 (diagnostic) → C3 (optim séparée) → C4 (régime) → C5 (validation)
Assets: ETH BTC AVAX AXS (contrôle)
Hypothèse: Paramétrage unifié Long/Short détruit performance
```

---

## 🎯 PHASE ACTUELLE

| Phase | Status | Détails |
|-------|--------|--------|
| 0 Data | ✅ Done | 26 assets téléchargés |
| 1 Screening | ✅ Done | 26/26 complete |
| 2 Validation | ✅ Done | 18/18 PBO calculé |
| **CONTINGENCY** | 🔴 **Plan A** | 100 trials challenger |
| 3-6 | ⏸️ Blocked | Dépend résultat Plan A/B/C |

---

## 📈 PROGRESSION

| Métrique | Cible | Actuel |
|----------|-------|--------|
| Assets PROD | 3-5 | **1** (AXS) |
| Plan A Status | 4 assets | ⏳ En attente lancement |
| Contingency | Plan C ready | Issue #30 créée |

---

## ⏭️ PROCHAINE ACTION

```bash
# Plan A — Lancer maintenant
python scripts/run_full_pipeline.py \
  --assets BTC ETH SOL AVAX \
  --trials-atr 100 --trials-ichi 100 \
  --seed 42 --workers 1 --run-guards \
  --output-prefix challenger_100trials
```

**Après Plan A** :
- Si ≥2/4 PBO <0.50 → Adopter 100 trials standard
- Si 0-1/4 PBO <0.50 → Lancer Plan B (bounds)
- Si Plan B FAIL → Lancer Plan C (Issue #30)

---

## 🗓️ HISTORIQUE RÉCENT

| Date | Action |
|------|--------|
| 27 Jan 19:08 | 📋 Issue #30 créée — Plan C Contingency Long/Short |
| 27 Jan 17:25 | 🔴 Résultats finaux: 12/18 EXCLU, 1 PROD (AXS), 3 QUARANTINE |
| 27 Jan 13:26 | Batch 1 PBO Complete — CAKE/RUNE/MINA EXCLU |
| 27 Jan 10:20 | PR#20 MEGA BATCH Analysis |
| 27 Jan 08:32 | ✅ PR#20 MEGA BATCH Complete (18 assets) |
| 26 Jan 20:45 | ✅ Issue #17 COMPLETE — Regime-Stratified WF |
| 26 Jan 19:27 | PR#20 merged — Reset 0 PROD |

---

## 🔗 ISSUES ACTIVES

| Issue | Titre | Priorité |
|:-----:|-------|:--------:|
| #30 | Plan C Contingency Long/Short | 🔴 HIGH |
| #29 | Architecture Dual-Params | 🟡 MEDIUM |
| #28 | Ensemble Top-K configs | 🟡 MEDIUM |
| #27 | PBO par direction | 🟡 MEDIUM |
| #25 | PR#20 Finalization | 🔴 HIGH |

---

## 🤖 AGENTS

| Agent | Focus actuel |
|-------|-------------|
| **Casey** | Supervision Plan A, décision escalade |
| **Jordan** | Exécution challenger 100 trials |
| **Sam** | Analyse PBO challenger |
| **Alex** | Review Plan C si nécessaire |

---

## 📁 FICHIERS

| Fichier | Contenu |
|---------|--------|
| `.cursor/rules/MASTER_PLAN.mdc` | Params, guards, règles |
| `docs/WORKFLOW_PIPELINE.md` | Commandes par phase |
| `status/project-state.md` | **CE FICHIER** (état) |
| `outputs/*_pbo_*.json` | Résultats PBO par asset |

---

**Version**: 2.3 (27 Jan 2026)
