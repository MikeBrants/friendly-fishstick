# PROJECT STATE — FINAL TRIGGER v2

**Updated**: 28 Jan 2026, 13:15 UTC+4
**Phase**: 🎉 **PR#21 FINALIZED — 5 PROD PORTFOLIO**
**Status**: 5 PROD (AXS/AVAX/ETH/SOL/YGG), 7 EXCLU (TIER 2+3 combined)

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

## 🎉 PR#21 FINALIZED — Portfolio of 5

**100 Trials Standard → FINAL DECISION: TIER 2 EXCLUDED**

| Status | Count | Assets | PBO Range | Decision |
|:------:|:-----:|--------|:---------:|:--------:|
| ✅ **PROD** | **5** | **AXS, AVAX, ETH, SOL, YGG** | 0.13-0.40 | PRODUCTION |
| 🔴 **EXCLU** | **7** | EGLD, SUSHI, MINA (TIER 2) + TON, HBAR, CRV, CAKE (TIER 3) | 0.53-0.93 | EXCLUDED |

**PROD Portfolio Details**:
- **ETH**: PBO 0.13 (CSCV 0.24), Sharpe 3.21, WFE 1.81, Phase 4/5/6 ✅
- **AVAX**: PBO 0.13 (Challenger), Sharpe 2.05, WFE 0.42
- **SOL**: PBO 0.33 (Challenger), Sharpe 2.96, WFE 1.27
- **YGG**: PBO 0.40 (PR#21 100T), Sharpe 3.40, WFE 0.89, **Best improvement -52.5%**
- **AXS**: PBO 0.33 (PR#20 300T), Sharpe 1.21

**TIER 2 EXCLUDED (28 Jan 2026, 13:15 UTC):**
- EGLD (PBO 0.53), SUSHI (PBO 0.60), MINA (PBO 0.53)
- Reason: Elevated overfitting risk despite guards PASS
- Decision: Conservative approach, strict PBO < 0.50 threshold

---

## 📊 ASSET STATUS

### ✅ TIER 1: PROD READY (5 assets)

```
ETH (PBO 0.13, Sharpe 3.21, WFE 1.81) — 100% validated
AVAX (PBO 0.13, Sharpe 2.05)
SOL (PBO 0.33, Sharpe 2.96)
YGG (PBO 0.40, Sharpe 3.40) — Best improvement (-52.5% vs 300T)
AXS (PBO 0.33, Sharpe 1.21)
```

### 🔴 EXCLU PR#21 (7 assets total)

**TIER 2 EXCLUDED (borderline PBO 0.53-0.60):**
```
EGLD (PBO 0.53, Sharpe 2.08) — Guards PASS but elevated risk
MINA (PBO 0.53, Sharpe 2.12) — Guards PASS but elevated risk
SUSHI (PBO 0.60, Sharpe 2.51) — Guards PASS but elevated risk
```

**TIER 3 EXCLUDED (critical PBO or guards FAIL):**

```
CAKE (PBO 0.93) — Critical overfitting
CRV (PBO 0.87) — Critical overfitting + guards FAIL
TON (PBO 0.60) — Guards FAIL (4/7)
HBAR (PBO 0.60) — Guards FAIL (5/7)
```

### ⏸️ NON TRAITÉS (9 assets)

```
SHIB DOT TIA NEAR DOGE ANKR JOE GALA ZIL
```

---

## 🎯 PR#21 — RERUN 100 TRIALS

### Commande

```bash
python scripts/run_full_pipeline.py \
  --assets BTC ETH ONE EGLD TON HBAR SUSHI CRV SEI AAVE MINA RUNE YGG CAKE \
  --trials-atr 100 --trials-ichi 100 \
  --seed 42 \
  --workers 1 \
  --run-guards \
  --output-prefix pr21_100trials
```

### Paramètres

| Param | Valeur | Note |
|-------|--------|------|
| trials | **100** | Nouveau standard |
| workers | 1 | Obligatoire Phase 2+ |
| seed | 42 | Reproductibilité |

### Durée Estimée

~5-6h pour 14 assets

---

## 🎯 PHASE ACTUELLE

| Phase | Status | Détails |
|-------|--------|--------|
| 0 Data | ✅ Done | 26 assets téléchargés |
| 1 Screening | ✅ Done | 26/26 complete |
| 2 Validation 300T | ✅ Done | 12/18 EXCLU (overfitting) |
| **Plan A Challenger** | ✅ **SUCCESS** | SOL+AVAX récupérés |
| **PR#21 100T** | 🟡 **READY** | 14 assets à lancer |
| 3-6 | ⏸️ Pending | Après PR#21 |

---

## 📈 PROGRESSION

| Métrique | Cible | Actuel |
|----------|-------|--------|
| Assets PROD | 10-15 | **5** ✅ |
| PR#21 Success Rate | >50% | 55.6% (5/9) |
| PBO Threshold | <0.50 | **STRICT** (conservative) |
| Improvement Rate | >50% | 100% (8/8 improved) |
| Assets Remaining | 9 | SHIB, DOT, TIA, NEAR, DOGE, ANKR, JOE, GALA, ZIL |

---

## ⏭️ PROCHAINE ACTION

1. ✅ ~~Valider Plan A~~ — SUCCESS
2. ✅ ~~Lancer PR#21~~ — **COMPLETE**
3. ✅ ~~Consolider PBO PR#21~~ — **COMPLETE**
4. ✅ ~~DÉCISION TIER 2~~ — **EXCLUDED** (conservative)
5. ✅ ~~MAJ asset_config.py~~ — **5 PROD finalized**
6. 🎯 **Phase 4/5 pour 4 assets** — SOL, AVAX, YGG, AXS (regime + portfolio)
7. ⏳ Test 9 assets restants (100T) — Optional expansion
8. ⏳ Déploiement production — Paper trading setup

---

## 🗓️ HISTORIQUE RÉCENT

| Date | Action |
|------|--------|
| 28 Jan 13:00 | 🎉 PR#21 COMPLETE — 5 PROD, 3 QUARANTINE, 4 EXCLU |
| 28 Jan 11:38 | ETH Phase 4/5/6 validated — SIDEWAYS 1.98, Corr 0.32 |
| 28 Jan 10:32 | PR#21 PBO Complete — 9/9 calculés, 100% improved vs 300T |
| 27 Jan 19:23 | 🟢 Plan A SUCCESS — SOL+AVAX PBO 0.13/0.33 |
| 27 Jan 17:25 | 🔴 PR#20 300T: 12/18 EXCLU (overfitting systémique) |
| 27 Jan 08:32 | ✅ PR#20 MEGA BATCH Complete (18 assets) |
| 26 Jan 20:45 | ✅ Issue #17 COMPLETE — Regime-Robust WF |

---

## 🔗 ISSUES ACTIVES

| Issue | Titre | Priorité | Status |
|:-----:|-------|:--------:|:------:|
| #30 | Plan C Contingency Long/Short | 🟡 STANDBY | Plan A success |
| #25 | PR#20 Finalization | ✅ DONE | Remplacé par PR#21 |

---

## 🤖 AGENTS

| Agent | Focus actuel |
|-------|-------------|
| **Casey** | Supervision PR#21 |
| **Jordan** | Exécution PR#21 (14 assets) |
| **Sam** | Consolidation PBO post-PR#21 |
| **Alex** | MAJ MASTER_PLAN.mdc (trials default) |

---

## 📁 FICHIERS

| Fichier | Contenu |
|---------|--------|
| `.cursor/rules/MASTER_PLAN.mdc` | Params, guards, règles |
| `docs/WORKFLOW_PIPELINE.md` | Commandes par phase |
| `status/project-state.md` | **CE FICHIER** (état) |
| `reports/CHALLENGER_PBO_COMPARISON.md` | Justification 100T |
| `outputs/*_pbo_*.json` | Résultats PBO par asset |

---

**Version**: 2.4 (27 Jan 2026)
