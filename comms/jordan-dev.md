# Runs Backtest - @Jordan

Ce fichier contient les logs des runs executes par Jordan.

---

## Format Message

```
## [HH:MM] [ACTION] @Jordan -> @Agent
**Task ref:** [lien vers tache Casey]
**Asset:** XXX
**Mode:** baseline | medium_distance_volume
**Displacement:** 26 | 52 | 65 | 78
**Command:** <commande complete>
**Status:** Running | Complete | Failed
**Duration:** X min
**Outputs:**
- outputs/multiasset_scan_YYYYMMDD_HHMMSS.csv
- outputs/guards/XXX_guard_results.json
**Erreurs:** [si applicable]
**Next:** @Sam valide les guards
```

### Actions possibles
- `[RUN_START]` — Debut d'execution
- `[RUN_COMPLETE]` — Run termine avec succes
- `[RUN_FAILED]` — Run echoue
- `[WAITING]` — En attente d'une tache

---

## Historique

<!-- Les messages les plus recents en haut -->

## [23:10] [PHASE_0_COMPLETE] @Jordan -> @Casey

**Task ref:** Plan d'attaque validation multi-asset (Phase 0)
**Actions complétées:**
1. ✅ Corrigé `asset_config.py`: ETH TP progressifs (tp1=4.75, tp2=7.0, tp3=10.0) depuis filter grid
2. ✅ Téléchargé données AVAX et UNI (17,520 bars chacun)

**Prochaines étapes:**
- P0.1: AVAX avec `medium_distance_volume` (WFE 0.52 en baseline)
- P0.2: UNI avec `moderate` ou `d78` (guard002 variance 10.27%)

---

## [23:10] [RUN_START] @Jordan -> @Sam

**Task ref:** Plan d'attaque P0.1 - AVAX medium_distance_volume
**Asset:** AVAX
**Mode:** medium_distance_volume
**Displacement:** Auto (52 par défaut)
**Command:** 
```bash
python scripts/run_full_pipeline.py \
  --assets AVAX \
  --workers 6 \
  --trials-atr 150 \
  --trials-ichi 150 \
  --enforce-tp-progression \
  --optimization-mode medium_distance_volume \
  --skip-download \
  --run-guards
```
**Status:** Running
**Duration:** En cours
**Outputs:** En attente
**Next:** @Sam valide les guards une fois terminé

## [23:06] [RUN_COMPLETE] @Jordan -> @Sam

**Task ref:** [22:45] [TASK] @Casey -> @Jordan (HBAR medium_distance_volume)
**Asset:** HBAR
**Mode:** medium_distance_volume
**Displacement:** 52 (auto-détecté)
**Command:** 
```bash
python scripts/run_full_pipeline.py \
  --assets HBAR \
  --workers 6 \
  --trials-atr 150 \
  --trials-ichi 150 \
  --enforce-tp-progression \
  --optimization-mode medium_distance_volume \
  --run-guards
```
**Status:** Complete (scan + guards terminés)
**Duration:** ~13 min (download + optimize + guards)
**Outputs:**
- Scan: `outputs/multiasset_scan_20260122_225614.csv`
- Guards: `outputs/HBAR_validation_report_20260122_222238.txt` (dernier à 23:03:41)
**Résultats scan:**
- Status: SUCCESS
- OOS Sharpe: 1.28
- WFE: 0.63
- OOS Trades: 107
- Params: sl=1.5, tp1=2.5, tp2=6.5, tp3=10.0, tenkan=7, kijun=20, displacement=52
**Résultats guards (dernier rapport 222238):**
- Guard001 (MC p-value): 0.01 → PASS ✅
- Guard002 (Sensitivity): 11.49% → FAIL ❌ (>10%)
- Guard003 (Bootstrap CI): 0.30 → FAIL ❌ (<1.0)
- Guard005 (Top10 trades): 41.05% → FAIL ❌ (>40%)
- Guard006 (Stress1 Sharpe): 0.62 → FAIL ❌ (<1.0)
- Guard007 (Regime mismatch): 0.00% → PASS ✅
- WFE: 0.63 → PASS ✅
- **ALL PASS: NO** (4/7 guards FAIL)
**Note:** Les guards montrent encore des échecs similaires au baseline (sensitivity 11.49% vs 13% baseline, légère amélioration mais toujours >10%). Le mode medium_distance_volume n'a pas résolu les problèmes de guards.
**Next:** @Sam valide les guards et détermine si un autre variant est nécessaire ou si HBAR doit être BLOCKED

---

## [23:27] [RUN_COMPLETE] @Jordan -> @Sam

**Task ref:** Plan d'attaque P0.1 - AVAX medium_distance_volume
**Asset:** AVAX
**Mode:** medium_distance_volume
**Displacement:** 52 (auto-détecté)
**Command:** 
```bash
python scripts/run_full_pipeline.py \
  --assets AVAX \
  --workers 6 \
  --trials-atr 150 \
  --trials-ichi 150 \
  --enforce-tp-progression \
  --optimization-mode medium_distance_volume \
  --skip-download \
  --run-guards
```
**Status:** Complete ✅
**Duration:** ~17 min (optimize + guards)
**Outputs:**
- Scan: `outputs/multiasset_scan_20260122_232727.csv`
- Guards: `outputs/AVAX_validation_report_20260122_232731.txt`
- Guards Summary: `outputs/multiasset_guards_summary_20260122_232731.csv`
**Résultats scan:**
- Status: SUCCESS ✅
- OOS Sharpe: **3.52** (excellent, >2.0)
- WFE: **0.94** (>0.6 ✅)
- OOS Trades: 96 (>60 ✅)
- Params: sl=2.75, tp1=1.5, tp2=7.5, tp3=9.5, tenkan=7, kijun=32, displacement=52
**Résultats guards:**
- Guard001 (MC p-value): 0.00 → PASS ✅
- Guard002 (Sensitivity): **6.00%** → PASS ✅ (<10%)
- Guard003 (Bootstrap CI): 1.52 → PASS ✅ (>1.0)
- Guard005 (Top10 trades): 26.73% → PASS ✅ (<40%)
- Guard006 (Stress1 Sharpe): 1.40 → PASS ✅ (>1.0)
- Guard007 (Regime mismatch): 0.00% → PASS ✅
- WFE: 0.94 → PASS ✅
- **ALL PASS: YES** ✅✅✅ (7/7 guards PASS)
**Verdict:** 🏆 **PRODUCTION READY** - AVAX passe tous les guards avec `medium_distance_volume` (vs WFE 0.52 en baseline)
**Next:** @Sam valide et @Casey met à jour project-state.md

---

## [23:30] [RUN_START] @Jordan -> @Sam

**Task ref:** Plan d'attaque P0.2 - UNI moderate
**Asset:** UNI
**Mode:** moderate
**Displacement:** Auto (52 par défaut)
**Command:** 
```bash
python scripts/run_full_pipeline.py \
  --assets UNI \
  --workers 6 \
  --trials-atr 150 \
  --trials-ichi 150 \
  --enforce-tp-progression \
  --optimization-mode moderate \
  --skip-download \
  --run-guards
```
**Raison:** Baseline avait guard002 variance 10.27% (>10%) et WFE 0.56 (<0.6). Test du mode `moderate` pour réduire la variance.
**Status:** Running
**Duration:** En cours
**Outputs:** En attente
**Next:** @Sam valide les guards une fois terminé

---

## [23:30] [VARIANTS_PROPOSED] @Jordan -> @Casey

**Task ref:** Plan d'attaque - Variants HBAR
**Asset:** HBAR
**Problème:** 4/7 guards FAIL avec `medium_distance_volume` (guard002: 11.49%, guard003: 0.30, guard005: 41.05%, guard006: 0.62)
**Variants proposés:** Document créé `outputs/HBAR_VARIANTS_PROPOSAL.md`

**Recommandation prioritaire:**
1. **d26 (fast displacement)** — Pattern similaire à JOE, plus de trades = meilleure distribution
2. **d78 (slow displacement)** — Pattern similaire à MINA, robustesse accrue
3. **light_distance/volume** — Dernier recours si displacements échouent

**Next:** @Casey décide quel variant tester en premier

---

## [23:07] [WAITING] @Jordan

**Status:** En attente de nouvelle tâche
**Dernière tâche complétée:** 
- ✅ [23:27] AVAX medium_distance_volume (7/7 guards PASS - PRODUCTION READY)
- ❌ [23:06] HBAR medium_distance_volume (4/7 guards FAIL)
**Prochaine action:** Surveiller `comms/casey-quant.md` pour nouvelles tâches (UNI P0.2?)

