# Next Steps — FINAL TRIGGER v2

**Date:** 2026-01-23 13:30  
**État actuel:** 15 assets PROD / Objectif: 20+ assets PROD (75% progression)  
**Dernière MAJ:** Fix V6 réussi (METIS + YGG PROD), Phase 3B arrêté

---

## 🎯 Priorité P0 — Blocages Critiques

### 1. Fix Bug "Complex Numbers" V6 — ✅ RÉSOLU

**Assets affectés:** STRK, METIS, AEVO, YGG  
**Symptôme:** Scans OK (Sharpe/WFE bons) mais guards FAIL avec erreur `float() argument must be a string or a real number, not 'complex'`  
**Impact:** 4 assets avec potentiel bloqués

**✅ Fix V6 RÉUSSI (2026-01-23 12:15):**
- **METIS:** 7/7 guards PASS ✅ → Sharpe 2.69, WFE 0.85
- **YGG:** 7/7 guards PASS ✅ → Sharpe 2.98, WFE 0.78
- **STRK:** EXCLU (sensitivity 12.5% > 10%, bootstrap CI 0.56 < 1.0)
- **AEVO:** EXCLU (sensitivity 15.0% > 10%)

**Fix V6 Appliqué (2026-01-23 11:45):**

✅ **Protection à la source dans `metrics.py`:**
- Fonctions `_safe_float()`, `_force_real_series()`, `_safe_std()`
- Protection dans `compute_metrics()` à la source
- Cache Python nettoyé (problème principal)

✅ **Résultat:** +2 assets PROD (13 → 15 assets, 75% objectif)

**Fichiers modifiés:**
- `crypto_backtest/analysis/metrics.py` — Protection à la source
- `scripts/run_guards_multiasset.py` — Protections supplémentaires

**Leçon:** Cache Python était le vrai problème, pas le code lui-même.

---

### 2. HBAR — Phase 3A Rescue (Displacement d78)

**État:** d26 FAIL (Sharpe 0.30, WFE 0.11)  
**Potentiel:** Asset important, pattern similaire à MINA (d78, Sharpe 1.76)

**Actions:**

```bash
# Phase 3A: Tester displacement d78 (après échec d26)
python scripts/run_full_pipeline.py \
  --assets HBAR \
  --fixed-displacement 78 \
  --trials-atr 150 \
  --trials-ichi 150 \
  --enforce-tp-progression \
  --run-guards \
  --workers 4
```

**Workflow:** Phase 3A Rescue → Si FAIL → EXCLU

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

### 5. Fix Complex Number Bug V6 — ✅ RÉSOLU

**Fichiers modifiés:**
- ✅ `crypto_backtest/analysis/metrics.py` — Protection à la source (`_safe_float()`, `_force_real_series()`, `_safe_std()`)
- ✅ `scripts/run_guards_multiasset.py` — Protections supplémentaires

**Solution appliquée:**

```python
# Protection à la source dans metrics.py
def _safe_float(value: Any, default: float = 0.0) -> float:
    """Convert value to float, handling complex numbers, NaN, and inf."""
    # ... (gère complexes, NaN, inf, None)

def _force_real_series(s: pd.Series) -> pd.Series:
    """Force Series to be real-valued."""
    if s.dtype == complex or any(isinstance(x, complex) for x in s.head(100)):
        return pd.Series(np.real(s.values), index=s.index)
    return s

# Utilisée dans compute_metrics() à la source
equity = _force_real_series(equity)
returns = _force_real_series(returns)
sharpe = _safe_float(mean_returns / std_returns) * np.sqrt(periods_per_year)
```

**Status:** ✅ RÉSOLU — Cache Python nettoyé + protection à la source. +2 assets PROD (METIS, YGG).

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
- [x] d26 testé → FAIL (Sharpe 0.30, WFE 0.11)
- [ ] d78 à tester (pattern MINA)
- [ ] Meilleur variant documenté

### Phase 3B — Displacement Grid Optimization
- [x] Fix Unicode appliqué (emojis remplacés)
- [x] Trials réduits 300→150 (anti-overfitting)
- [x] Garde-fou WFE négatif ajouté
- [x] **ARRÊTÉ** — Dégradation systématique des baselines (BTC, ETH)
- [x] Leçons documentées (re-optimisation ≠ amélioration)

### Phase 4 — Filter Grid (Complex Number Bug)
- [x] Fix V6 appliqué (protection à la source dans metrics.py)
- [x] ✅ METIS: Tests guards réussis (7/7 guards PASS)
- [x] ✅ YGG: Tests guards réussis (7/7 guards PASS)
- [x] ✅ METIS + YGG: Ajoutés en PROD (asset_config.py + project-state.md)
- [x] STRK, AEVO: EXCLU (sensitivity > 10%)

### Phase 5 — Production
- [x] `asset_config.py` à jour (15 assets PROD)
- [x] `status/project-state.md` à jour (15 assets PROD)
- [x] Nouveaux assets PROD documentés (METIS, YGG validés)

---

## 🎯 Objectifs Immédiats (Cette Semaine)

1. **✅ METIS + YGG débloqués** → Fix V6 réussi, 7/7 guards PASS (+2 assets PROD)
2. **✅ Phase 3B arrêté** → Dégradation systématique identifiée, baselines gardés
3. **⏭️ HBAR d78** → Phase 3A Rescue (après échec d26)
4. **⏭️ Screening nouveaux assets** → Phase 1 pour 5-10 nouveaux assets (objectif 20+)
5. **⏭️ Portfolio construction** → Analyse corrélations 15 assets PROD

**Résultat attendu:** 20+ assets PROD (objectif Q1)

**Progression actuelle:** 15 assets PROD (75% de l'objectif) ⬆️ +2

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
