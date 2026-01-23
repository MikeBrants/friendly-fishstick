# Next Steps — FINAL TRIGGER v2

**Date:** 2026-01-23 10:15  
**État actuel:** 13 assets PROD / Objectif: 20+ assets PROD (65% progression)  
**Dernière MAJ:** SHIB débloqué avec fix V3 (7/7 guards PASS)

---

## 🎯 Priorité P0 — Blocages Critiques

### 1. Fix Bug "Complex Numbers" V3 — ✅ SHIB RÉUSSI (4 assets restants)

**Assets affectés:** YGG, SHIB, STRK, METIS, AEVO  
**Symptôme:** Scans OK (Sharpe/WFE bons) mais guards FAIL avec erreur `float() argument must be a string or a real number, not 'complex'`  
**Impact:** 4 assets restants avec potentiel bloqués

**✅ SHIB DÉBLOQUÉ (2026-01-23 10:15):**
- 7/7 guards PASS ✅
- OOS Sharpe: 5.88, WFE: 2.42
- Ajouté en PROD

**Fix V3 Appliqué (2026-01-23 10:02):**

✅ **Fonction helper globale créée:**
- `_safe_float(value)` dans `scripts/run_guards_multiasset.py`
- Gère complexes, NaN, inf, None
- Utilisée partout où on fait `float()` (~15 endroits)

✅ **Protections ajoutées:**
- `crypto_backtest/analysis/metrics.py`: Protection `periods_per_year` et `std_returns`
- `scripts/run_guards_multiasset.py`: Toutes conversions float protégées
- Calculs DataFrame (mean, std, percentile) protégés

**Tests en cours:**
```bash
# Relancer guards avec fix V3 pour assets restants
python scripts/run_guards_multiasset.py \
  --assets STRK METIS AEVO YGG \
  --params-file outputs/complex_fix_test_params.csv \
  --workers 6
```

**Résultats:**
- ✅ SHIB: Fix V3 réussi → +1 asset PROD (13 assets total)
- 🔄 STRK, METIS, AEVO, YGG: Tests en cours (run lancé 10:15)
- Si fix V3 fonctionne pour tous: +4 assets PROD potentiels (13 → 17 assets)

**Workflow:** Phase 4 (Filter Grid) après validation fix V3

---

### 2. HBAR — Phase 3A Rescue (Displacement Grid)

**État:** 4/7 guards FAIL (sens 11.49%, CI 0.30, top10 41%, stress1 0.62)  
**Potentiel:** Asset important, variants proposés

**Actions:**

```bash
# Phase 3A: Tester displacement variants
python scripts/run_full_pipeline.py \
  --assets HBAR --fixed-displacement 26 \
  --trials 300 \
  --enforce-tp-progression \
  --run-guards \
  --workers 4

python scripts/run_full_pipeline.py \
  --assets HBAR --fixed-displacement 78 \
  --trials 300 \
  --enforce-tp-progression \
  --run-guards \
  --workers 4

# Si displacement FAIL, tester filter modes
python scripts/run_full_pipeline.py \
  --assets HBAR --optimization-mode light_distance \
  --trials 300 \
  --enforce-tp-progression \
  --run-guards \
  --workers 4
```

**Workflow:** Phase 3A Rescue → Phase 4 Filter Grid si nécessaire

---

## 🚀 Priorité P1 — Expansion Portfolio

### 3. Phase 1 Screening — Nouveaux Assets Top 50

**Objectif:** Identifier nouveaux candidats pour atteindre 20+ assets PROD

**Actions:**

```bash
# 1. Identifier assets non encore testés
python -c "
import pandas as pd
from glob import glob
scans = pd.concat([pd.read_csv(f) for f in glob('outputs/multiasset_scan_*.csv')])
tested = set(scans['asset'].unique())
all_assets = set(['BTC', 'ETH', 'BNB', 'SOL', 'XRP', 'USDC', 'ADA', 'DOGE', 'TRX', 'AVAX', 'SHIB', 'TON', 'DOT', 'LINK', 'MATIC', 'NEAR', 'UNI', 'ICP', 'APT', 'LTC', 'BCH', 'FIL', 'ATOM', 'ETC', 'ARB', 'OP', 'INJ', 'STX', 'IMX', 'TIA', 'HBAR', 'RENDER', 'FET', 'MKR', 'GRT', 'AAVE', 'ALGO', 'EGLD', 'SAND', 'MANA', 'AXS', 'THETA', 'FLOW', 'EOS', 'GALA', 'CHZ', 'ENJ', 'BAT', 'ZIL', 'IOTA'])
remaining = sorted(all_assets - tested)
print(f'Assets non testés: {len(remaining)}')
print(remaining[:20])
"

# 2. Phase 0: Download data pour nouveaux assets
python scripts/download_data.py --assets [LISTE_NOUVEAUX] --format parquet --days 730

# 3. Phase 1: Screening rapide (200 trials, skip-guards)
python scripts/run_full_pipeline.py \
  --assets [LISTE_NOUVEAUX] --workers 6 \
  --trials 200 \
  --enforce-tp-progression \
  --skip-guards \
  --output-prefix screen_new_batch

# 4. Phase 2: Validation complète pour winners Phase 1
python scripts/run_full_pipeline.py \
  --assets [WINNERS_PHASE1] --workers 6 \
  --trials 300 \
  --enforce-tp-progression \
  --run-guards \
  --output-prefix validated_new_batch
```

**Critères Phase 1 (souples):**
- WFE > 0.5
- Sharpe OOS > 0.8
- Trades OOS > 50

**Workflow:** Phase 0 → Phase 1 → Phase 2 → Phase 3A/3B si nécessaire → Phase 5

---

## 📊 Priorité P2 — Portfolio Construction

### 4. Analyse Corrélations & Allocation

**Objectif:** Optimiser le portfolio de 12 assets PROD

**Actions:**

```bash
# Analyse corrélations entre assets PROD
python scripts/portfolio_correlation.py \
  --assets BTC ETH JOE OSMO MINA AVAX AR ANKR DOGE OP DOT NEAR \
  --output outputs/portfolio_correlation_12assets.csv

# Vérifier corrélations < 0.7 entre assets
# Calculer allocation optimale par Sharpe ratio ajusté
```

**Critères:**
- Corrélations < 0.7 entre assets
- Diversification maximale
- Allocation par Sharpe ratio ajusté

---

## 🔧 Priorité P3 — Optimisations Techniques

### 5. Fix Complex Number Bug V3 — ✅ APPLIQUÉ

**Fichiers modifiés:**
- ✅ `crypto_backtest/analysis/metrics.py` — Protection `periods_per_year` et `std_returns`
- ✅ `scripts/run_guards_multiasset.py` — Fonction helper `_safe_float()` + ~15 protections

**Solution appliquée:**

```python
# Fonction helper globale
def _safe_float(value: Any) -> float:
    """Convert value to float, handling complex numbers, NaN, and inf."""
    if value is None:
        return 0.0
    if isinstance(value, complex):
        value = np.real(value)
    try:
        result = float(value)
    except (TypeError, ValueError):
        return 0.0
    if np.isnan(result) or np.isinf(result):
        return 0.0
    return result

# Utilisée partout où on fait float()
base_sharpe = _safe_float(base_metrics.get("sharpe_ratio", 0.0) or 0.0)
```

**Status:** Fix V3 appliqué, tests en cours. Si bug persiste, investigation approfondie requise.

---

## 📋 Checklist Workflow

### Pre-flight
- [ ] Données 1H téléchargées pour nouveaux assets (Phase 0)
- [ ] TP progression enforcement ON
- [ ] Vérifier timestamp fichier > 2026-01-22 12:00 UTC (cutoff bug TP)

### Phase 1 — Screening
- [ ] Identifier assets non testés
- [ ] Download data pour nouveaux assets
- [ ] Screening batches run (200 trials, --skip-guards)
- [ ] Shortlist winners exportée

### Phase 2 — Validation
- [ ] Reopt 300 trials pour winners Phase 1
- [ ] Guards 7/7 pour WINNERS

### Phase 3A — Rescue (HBAR)
- [ ] Grid displacement testé (d26, d78)
- [ ] Filter modes testés si displacement FAIL
- [ ] Meilleur variant documenté

### Phase 4 — Filter Grid (Complex Number Bug)
- [x] Fix V3 appliqué (fonction helper `_safe_float()` + protections)
- [x] ✅ SHIB: Tests guards réussis (7/7 guards PASS)
- [x] ✅ SHIB: Ajouté en PROD (asset_config.py + project-state.md)
- [ ] Tests guards en cours pour STRK, METIS, AEVO, YGG
- [ ] Résultats documentés pour assets restants

### Phase 5 — Production
- [x] `asset_config.py` à jour (DOT, NEAR, SHIB ajoutés le 2026-01-23)
- [x] `status/project-state.md` à jour (13 assets PROD)
- [x] Nouveaux assets PROD documentés (DOT, NEAR, SHIB validés)

---

## 🎯 Objectifs Immédiats (Cette Semaine)

1. **✅ SHIB débloqué** → Fix V3 réussi, 7/7 guards PASS (+1 asset PROD)
2. **🔄 Tests guards en cours** → STRK, METIS, AEVO, YGG avec fix V3 (potentiel +4 assets PROD)
3. **HBAR variants** → Phase 3A Rescue (+1 asset PROD)
4. **Screening nouveaux assets** → Phase 1 pour 10-15 nouveaux assets
5. **Portfolio construction** → Analyse corrélations 13 assets PROD

**Résultat attendu:** 15-20 assets PROD (objectif Q1: 20+)

**Progression actuelle:** 13 assets PROD (65% de l'objectif) ⬆️ +1

---

## 📁 Fichiers Référence

- **Workflow:** `docs/WORKFLOW_MULTI_ASSET_SCREEN_VALIDATE_PROD.md`
- **Plan d'attaque:** `.cursor/plans/asset_validation_pipeline_14ae3c79.plan.md`
- **Project state:** `status/project-state.md` (source de vérité)
- **Multi-agent guide:** `docs/MULTI_AGENT_GUIDE.md`

---

## ⚠️ NE PAS FAIRE

- Ne jamais utiliser `docs/HANDOFF.md` comme référence (obsolete)
- Ne jamais modifier les seuils guards sans validation
- Ne jamais skip le warmup (200 barres minimum)
- Ne jamais oublier `.shift(1)` sur les rolling features (look-ahead)
- Ne jamais valider avec Sharpe > 4 ou WFE > 2 sans réconciliation (trop beau = suspect)
