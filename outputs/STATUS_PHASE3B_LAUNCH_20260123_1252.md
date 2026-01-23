# Phase 3B Launch - ETH & JOE - 2026-01-23 12:52

## Status

**Command:**
```bash
python scripts/run_phase3b_optimization.py --assets ETH JOE --workers 8
```

**PID:** 10636  
**Status:** 🟢 Running (background)  
**Lancé:** 12:52

---

## Configuration

### Assets
- **ETH:** Baseline d52, mode medium_distance_volume, Sharpe 2.09
- **JOE:** Baseline d26, mode baseline, Sharpe 5.03

### Displacements à Tester

**ETH:**
- d26 (fast)
- d52 (baseline actuel)
- d78 (slow)

**JOE:**
- d26 (baseline actuel)
- d52 (medium)
- d78 (slow)

**Total:** 2 assets × 3 displacements = 6 optimizations + 6 guard suites

---

## Paramètres

- **Trials ATR:** 150 (réduit de 300)
- **Trials Ichimoku:** 150 (réduit de 300)
- **Workers:** 8
- **Garde-fou WFE:** Activé (early exit si WFE < 0)

---

## Durée Estimée

**Par displacement:**
- Optimisation: ~10-15 min (150+150 trials)
- Guards: ~5-10 min
- **Total:** ~15-25 min par displacement

**Total run:**
- 6 displacements × 20 min = **~2h** (avec 8 workers en parallèle)

---

## Critères de Succès

Pour chaque displacement:
1. **WFE > 0** (garde-fou détecte si négatif)
2. **Sharpe OOS > baseline** (ou proche)
3. **Amélioration > 10%** vs baseline
4. **7/7 guards PASS**

**Recommandation:** UPDATE si amélioration >10% + guards PASS, sinon KEEP baseline

---

## Monitoring

**Fichiers à surveiller:**
- `outputs/phase3b_ETH_d{26|52|78}_multiasset_scan_*.csv`
- `outputs/phase3b_JOE_d{26|52|78}_multiasset_scan_*.csv`
- `outputs/phase3b_ETH_d{26|52|78}_guards_summary_*.csv`
- `outputs/phase3b_JOE_d{26|52|78}_guards_summary_*.csv`

**Terminal:** `terminals/593205.txt`

---

## Prochaines Actions

1. ⏳ Attendre completion (~2h)
2. ⏭️ Analyser résultats (WFE, Sharpe, guards)
3. ⏭️ Comparer vs baseline
4. ⏭️ Recommandations UPDATE/KEEP

---

**Date:** 2026-01-23 12:52  
**Next Check:** 14:00 (après ~1h)
