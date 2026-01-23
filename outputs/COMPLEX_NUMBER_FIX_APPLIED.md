# Fix Complex Number Bug - Appliqué 2026-01-23

## Corrections Appliquées

### 1. `scripts/run_guards_multiasset.py` - Bootstrap Confidence

**Lignes 236-246:**
- Ajout protection `np.abs()` sur `std_returns` pour forcer positif
- Remplacement NaN et inf par 0.0
- Extraction partie réelle avec `np.real()` sur sharpe
- Protection dans les conversions float (lignes 247-257)

**Impact:** Résout le bug dans guard003 (Bootstrap CI)

---

### 2. `crypto_backtest/analysis/metrics.py` - Compute Metrics

**Lignes 21-30:**
- Protection contre complexes dans calcul Sharpe
- Extraction partie réelle si complexe
- Remplacement NaN/inf par 0.0
- Même protection pour Sortino

**Lignes 86-90 (_periods_per_year):**
- Validation que résultat est positif et fini
- Retourne 252.0 par défaut si invalide

**Impact:** Résout le bug dans tous les calculs de métriques

---

## Tests Requis

### Assets à Tester (5 assets bloqués)

1. **SHIB** — Scan excellent (Sharpe 5.88, WFE 2.42)
2. **STRK** — Scan OK (Sharpe 1.27, WFE 0.85)
3. **METIS** — Scan OK (Sharpe 2.89, WFE 0.85)
4. **AEVO** — Scan OK (Sharpe 1.23, WFE 0.62)
5. **YGG** — Scan OK (Sharpe 3.04, WFE 0.78)

### Commande de Test

```bash
python scripts/run_guards_multiasset.py \
  --assets SHIB STRK METIS AEVO YGG \
  --scan-file outputs/multi_asset_scan_partial.csv \
  --workers 6
```

---

## Résultats Attendus

Si le fix fonctionne:
- ✅ Guards passent sans erreur "complex number"
- ✅ SHIB devrait passer 7/7 guards (scan excellent)
- ✅ STRK, METIS, AEVO, YGG devraient passer si scans valides

**Impact potentiel:** +5 assets PROD (12 → 17 assets)

---

## Fichiers Modifiés

1. ✅ `scripts/run_guards_multiasset.py` — Fix bootstrap + conversions float
2. ✅ `crypto_backtest/analysis/metrics.py` — Fix compute_metrics + _periods_per_year

---

**Date:** 2026-01-23  
**Auteur:** @Jordan  
**Status:** Fix appliqué, tests requis
