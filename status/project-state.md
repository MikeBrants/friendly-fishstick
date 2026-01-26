# PROJECT STATE - FINAL TRIGGER v2 Backtest System

**Last Updated**: 26 janvier 2026, 19:27 UTC
**Phase**: 🔴 **RESET COMPLET** — PR#19 Bug Fix → Revalidation from Scratch
**Status**: ⚠️ **0 PROD ASSETS** — All 26 assets pending revalidation

---

## 🔴 CRITICAL: PIPELINE RESET (PR#20)

### Executive Summary

**ALL PREVIOUS RESULTS ARE INVALIDATED** due to PR#19 SHORT signal bug discovery.

The 5-in-1 filter had hardcoded TS5/KS5 params instead of per-asset optimized values. This means:
- All LONG-only backtests were biased (SHORTs filtered incorrectly)
- Previous "PROD" assets must be re-tested with correct SHORT signals
- Ex-EXCLUDED assets may now be valid with proper SHORT entries

### Impact Matrix

| Category | Before | After | Change |
|----------|--------|-------|--------|
| **PROD** | 12 assets | **0** | All invalidated |
| **PENDING** | 0 | **26** | Full pool |
| **BLOCKED** | 14 | **0** | All reintegrated |

### 26 Assets to Retest

```
SHIB DOT TIA NEAR DOGE ANKR ETH JOE YGG MINA CAKE RUNE
EGLD AVAX HBAR TON SUSHI CRV BTC ONE SEI AXS SOL AAVE ZIL GALA
```

### Asset Reintegration Reasons

| Category | Assets | Reason |
|----------|--------|--------|
| Ex-PROD (12) | SHIB, DOT, TIA, NEAR, DOGE, ANKR, ETH, JOE, YGG, MINA, CAKE, RUNE | Results invalid (LONG-only bias) |
| Ex-EXCLUDED Regime | EGLD, AVAX | May be OK with SHORTs in SIDEWAYS |
| Ex-FAILED Guards | HBAR, TON, SUSHI, CRV | May pass with more trades from SHORTs |
| Ex-FAILED WFE | BTC, ONE | WFE may change with SHORT entries |
| Ex-EXHAUSTED | SEI, AXS, SOL, AAVE, ZIL, GALA | Must retest from scratch |

---

## 📋 PIPELINE v3 — 6 PHASES (POST-PR#19)

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                     PIPELINE FINAL TRIGGER v2 — VERSION COMPLÈTE                 │
└─────────────────────────────────────────────────────────────────────────────────┘

Phase 0          Phase 1         Phase 2          Phase 2B         Phase 3
DATA             SCREENING       VALIDATION       REGIME STRESS    RESCUE
   │                 │               │                │               │
   ▼                 ▼               ▼                ▼               ▼
┌──────┐       ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│Data  │──────▶│200 trials│───▶│300 trials│───▶│MARKDOWN  │───▶│Disp d26/ │
│Valid │       │workers=4 │    │workers=1 │    │SIDEWAYS  │    │d52/d78   │
└──────┘       └──────────┘    └──────────┘    └──────────┘    └──────────┘
                    │               │                │               │
                    ▼               ▼                ▼               ▼
              ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
              │WFE>0.5   │    │7 Guards  │    │Sharpe≥0  │    │7/7 PASS? │
              │Sharpe>0.8│    │PBO<0.50  │    │SIDEWAYS  │    │          │
              │Trades>50 │    │DSR>85%   │    │          │    │          │
              │SHORT 25% │    │CPCV OK   │    └──────────┘    └──────────┘
              └──────────┘    │PSR>95%   │
                              └──────────┘
                                              
Phase 4              Phase 5              Phase 6
PINE PARITY          PORTFOLIO            PRODUCTION
     │                   │                    │
     ▼                   ▼                    ▼
┌──────────┐       ┌──────────┐        ┌──────────┐
│Python vs │──────▶│Max Sharpe│───────▶│asset_    │
│Pine 100% │       │Risk Parity│       │config.py │
│match     │       │Min CVaR   │       │Pine.pine │
└──────────┘       └──────────┘        └──────────┘
```

### Phase Details

| Phase | Nom | Config | Critères Pass | Output |
|:-----:|-----|--------|---------------|--------|
| **0** | Data Download | 26 assets | ≥8000 bars, no gaps >4h | `data/*.parquet` |
| **1** | Screening | 200 trials, workers=4-8, guards OFF | WFE>0.5, Sharpe>0.8, Trades>50, **SHORT ratio 25-75%** | Candidats |
| **2** | Validation | 300 trials, **workers=1**, 7 guards ON | 7/7 hard guards PASS, PBO<0.50, DSR>85%, PSR>95%, CPCV OK | WINNERS + PENDING |
| **2B** | Regime Stress | MARKDOWN + SIDEWAYS test | MARKDOWN: <10 trades OR Sharpe>-2; SIDEWAYS: Sharpe≥0 | PASS/EXCLUDE |
| **3A** | Rescue Disp | PENDING: d26/d52/d78 | 7/7 PASS → WINNERS | Récupération |
| **3B** | Optim Disp | WINNERS: test +10% | 7/7 PASS ET +10% Sharpe improvement → remplace | Amélioration |
| **4** | Signal Parity | Python vs Pine | **100% match** | Validation |
| **5** | Portfolio | 4 méthodes | Max Sharpe sélectionné | Weights |
| **6** | Production | `asset_config.py` + Pine export | Frozen params | PROD |

---

## 🔬 GUARDS COMPLETS — 11 VALIDATIONS

### 7 Hard Guards (Must PASS)

| # | Guard | Métrique | Seuil | Fichier |
|:-:|-------|----------|-------|---------|
| 001 | WFE Pardo | OOS_Sharpe / IS_Sharpe | **>0.6** | `walk_forward.py` |
| 002 | Sensitivity | Variance params | **<15%** | `sensitivity.py` |
| 003 | Bootstrap CI | Lower bound | **>1.0** | `validation/bootstrap.py` |
| 004 | Monte Carlo | p-value permutation | **<0.05** | `validation/monte_carlo.py` |
| 005 | Top10 Concentration | % profit top 10 trades | **<40%** | `concentration.py` |
| 006 | Trades OOS | Nombre trades | **≥60** | pipeline |
| 007 | Bars IS | Données suffisantes | **≥8000** | pipeline |

### 4 Soft Guards (Report + Rescue if FAIL)

| # | Guard | Métrique | Seuil | Fichier |
|:-:|-------|----------|-------|---------|
| 008 | PBO | Prob. Backtest Overfit | **<0.50** | `validation/pbo.py` |
| 009 | DSR | Deflated Sharpe Ratio | **>85%** | `validation/deflated_sharpe.py` |
| 010 | CPCV | Sharpe all folds | **>0.8** | `validation/cpcv.py` |
| 011 | PSR | Probabilistic Sharpe Ratio | **>95%** | `validation/overfitting.py` |

### DSR Verdicts

| DSR | Verdict |
|-----|---------|
| > 95% | **STRONG** — Edge significatif |
| 85-95% | **MARGINAL** — Acceptable si autres guards OK |
| < 85% | **FAIL** — Probablement overfitting |

### PSR Verdicts

| PSR | Verdict |
|-----|---------|
| > 95% | **STRONG** — Sharpe statistiquement significatif |
| 90-95% | **MARGINAL** — Acceptable avec prudence |
| < 90% | **FAIL** — Sharpe peut être dû au hasard |

---

## 🔬 TESTS STATISTIQUES AVANCÉS (Phase 2)

| Test | Fichier | Seuil | Usage |
|------|---------|-------|-------|
| WFE Pardo | `walk_forward.py` | >0.6 | Walk-forward efficiency |
| PBO | `validation/pbo.py` | <0.50 | Probability Backtest Overfitting |
| CPCV | `validation/cpcv.py` | Sharpe >0.8 tous folds | Combinatorial Purged CV |
| DSR | `validation/deflated_sharpe.py` | >85% | Deflated Sharpe Ratio |
| PSR | `validation/overfitting.py` | >95% | Probabilistic Sharpe Ratio |
| Monte Carlo | `validation/monte_carlo.py` | p <0.05 | Permutation test |
| Bootstrap CI | `validation/bootstrap.py` | lower >1.0 | Confidence intervals |

### PBO Implementation

```python
# crypto_backtest/validation/pbo.py
def guard_pbo(returns_matrix: np.ndarray, n_splits: int = 10) -> dict:
    """
    Probability of Backtest Overfitting (Bailey & López de Prado)
    
    Args:
        returns_matrix: Shape (n_trials, n_periods) - returns par trial
        n_splits: Nombre de combinaisons à tester
    
    Returns:
        {"pbo": float, "pass": bool, "threshold": 0.50}
    """
    # Requires returns_matrix saved during optimization
    # File: outputs/returns_matrix_{asset}_{run_id}.npy
```

### returns_matrix Tracking (OBLIGATOIRE)

```python
# OBLIGATOIRE: Sauvegarder returns_matrix pour PBO
class ParallelOptimizer:
    def run(self):
        # ... optimization ...
        
        # ⚠️ NOUVEAU: Sauvegarder returns par trial pour PBO
        returns_matrix = np.array([trial.returns for trial in all_trials])
        np.save(f"outputs/returns_matrix_{asset}_{run_id}.npy", returns_matrix)
        
        return result
```

---

## 🔬 PHASE 2B: REGIME STRESS TESTS

### Configuration

```python
REGIME_STRESS_CONFIG = {
    "MARKDOWN": {
        "description": "Bear market periods",
        "expected_behavior": "Strategy should AVOID entries (0-10 trades)",
        "fail_criteria": {
            "trades_min": 10,  # Si >10 trades ET Sharpe < -2, FAIL
            "sharpe_threshold": -2.0
        },
        "interpretation": {
            "0-3 trades": "EXCELLENT - Strategy filters bear markets",
            "4-10 trades": "ACCEPTABLE - Minor exposure",
            ">10 trades with Sharpe<0": "CONCERN - Review filters"
        }
    },
    "SIDEWAYS": {
        "description": "Range-bound consolidation",
        "expected_behavior": "Positive or neutral performance",
        "fail_criteria": {
            "sharpe_threshold": 0.0  # Doit être ≥0
        },
        "action_on_fail": "EXCLUDE from PROD"
    }
}
```

### Critères Pass/Fail

| Régime | Condition PASS | Condition FAIL |
|--------|----------------|----------------|
| **MARKDOWN** | <10 trades OU Sharpe >-2 | >10 trades ET Sharpe <-2 |
| **SIDEWAYS** | Sharpe ≥0 | Sharpe <0 → **EXCLU** |

### Commande

```bash
python scripts/run_regime_stress_test.py \
    --assets ETH BTC SHIB DOT NEAR DOGE TIA MINA JOE ANKR CAKE RUNE \
    --regimes MARKDOWN SIDEWAYS \
    --output outputs/stress_test_{timestamp}.csv
```

---

## 🔬 PHASE 4: SIGNAL PARITY VALIDATION

### Pourquoi c'est CRITIQUE

Le bug PR#19 a montré que Python et Pine peuvent diverger. **Validation obligatoire avant PROD**.

### Script

```bash
# Phase 4: Vérifier parité signaux avant production
python scripts/validate_signal_parity.py --asset ETH --bars 1000

# Output attendu:
# Python signals: 47 LONG, 45 SHORT
# Pine signals:   47 LONG, 45 SHORT  
# ✅ PARITY: 100% match
```

### Critère

- **PASS**: 100% match
- **FAIL**: <100% → Debug obligatoire avant PROD

---

## 🔬 PHASE 5: PORTFOLIO CONSTRUCTION

### Méthodes

| Méthode | Description | Pros | Cons |
|---------|-------------|------|------|
| `equal_weight` | 1/N allocation | Simple, robuste | Ignore corrélations |
| `max_sharpe` | Maximise Sharpe ratio portfolio | Optimal théorique | Sensible aux estimations |
| `risk_parity` | Equal risk contribution | Diversification risque | Peut surpondérer low-vol |
| `min_cvar` | Minimise Conditional VaR (95%) | Focus tail risk | Conservateur |

### Commande

```bash
python scripts/portfolio_construction.py \
    --assets ETH BTC SHIB DOT NEAR DOGE TIA MINA JOE ANKR CAKE RUNE \
    --methods equal max_sharpe risk_parity min_cvar \
    --output reports/portfolio_analysis_{timestamp}.md
```

---

## 🔧 FILTER SYSTEM v2 (3 MODES)

| Mode | Filtres | Trades OOS | WFE | Usage |
|------|---------|------------|-----|-------|
| `baseline` | ichimoku only | ≥60 | ≥0.6 | Default, Phase 2 |
| `moderate` | 5 filtres | ≥50 | ≥0.6 | Si baseline FAIL guard002 |
| `conservative` | 7 filtres | ≥40 | ≥0.55 | Si moderate FAIL |

### Rescue Workflow

```
Asset FAIL baseline (sensitivity > 15%)
    │
    └─→ moderate (5 filtres)
         │
         ├─ PASS → PROD ✓
         └─ FAIL → conservative (7 filtres)
                   │
                   ├─ PASS → PROD ✓
                   └─ FAIL → EXCLU ✗
```

---

## ⚠️ PIÈGES CRITIQUES

| Piège | Impact | Solution |
|-------|--------|----------|
| Look-ahead bias | Résultats invalides | TOUJOURS `.shift(1)` sur rolling features |
| Regime timing | Bias OOS | Utiliser ENTRY time, pas exit |
| SIDEWAYS filter | Perte 79.5% profit | NE PAS filtrer SIDEWAYS |
| Sharpe >4 ou WFE >2 | Suspect overfitting | Reconciliation obligatoire |
| TP ordering | Contrainte violée | tp1 < tp2 < tp3 |
| Bug KAMA | Signaux incorrects | Corrigé 24 Jan — retester modes KAMA |
| **Bug TS5/KS5** | **SHORTs invalides** | **Corrigé PR#19 — RETEST ALL** |

---

## 📊 ASSET STATUS MATRIX

### Category 1: ⏳ PENDING REVALIDATION (26 assets)

**Status**: 🟡 **ALL MUST BE RETESTED**

| # | Asset | Previous Status | Reason for Retest |
|:-:|-------|-----------------|-------------------|
| 1 | **SHIB** | Ex-PROD | LONG-only bias |
| 2 | **DOT** | Ex-PROD | LONG-only bias |
| 3 | **TIA** | Ex-PROD | LONG-only bias |
| 4 | **NEAR** | Ex-PROD | LONG-only bias |
| 5 | **DOGE** | Ex-PROD | LONG-only bias |
| 6 | **ANKR** | Ex-PROD | LONG-only bias |
| 7 | **ETH** | Ex-PROD | LONG-only bias |
| 8 | **JOE** | Ex-PROD | LONG-only bias |
| 9 | **YGG** | Ex-PROD | LONG-only bias |
| 10 | **MINA** | Ex-PROD | LONG-only bias |
| 11 | **CAKE** | Ex-PROD | LONG-only bias |
| 12 | **RUNE** | Ex-PROD | LONG-only bias |
| 13 | **EGLD** | Ex-EXCLUDED (Regime) | May pass with SHORTs |
| 14 | **AVAX** | Ex-EXCLUDED (Regime) | May pass with SHORTs |
| 15 | **HBAR** | Ex-FAILED Guards | More trades with SHORTs |
| 16 | **TON** | Ex-FAILED Guards | More trades with SHORTs |
| 17 | **SUSHI** | Ex-FAILED Guards | More trades with SHORTs |
| 18 | **CRV** | Ex-FAILED Guards | More trades with SHORTs |
| 19 | **BTC** | Ex-FAILED WFE | WFE may change |
| 20 | **ONE** | Ex-FAILED WFE | WFE may change |
| 21 | **SEI** | Ex-EXHAUSTED | Must retest |
| 22 | **AXS** | Ex-EXHAUSTED | Must retest |
| 23 | **SOL** | Ex-EXHAUSTED | Must retest |
| 24 | **AAVE** | Ex-EXHAUSTED | Must retest |
| 25 | **ZIL** | Ex-EXHAUSTED | Must retest |
| 26 | **GALA** | Ex-EXHAUSTED | Must retest |

### Category 2: ✅ VALIDATED PROD (0 assets)

**Status**: 🔴 **EMPTY** — All pending revalidation

---

## ⏱️ TIMELINE ESTIMÉE

| Phase | Durée | Cumul |
|-------|-------|-------|
| Phase 0: Data | 15 min | 15 min |
| Phase 1: Screening (26 assets) | 4-6h | 4-6h |
| Phase 2: Validation | 6-10h | 10-16h |
| Phase 2B: Regime Stress | 2-3h | 12-19h |
| Phase 3: Rescue | 5-8h | 17-27h |
| Phase 4: Signal Parity | 1h | 18-28h |
| Phase 5: Portfolio | 30 min | 18.5-28.5h |
| Phase 6: Production | 1h | **19.5-29.5h** |

**Total estimé: 20-30h de compute**

---

## 📋 CHECKLIST COMPLÈTE

### Phase 0: Data
- [ ] 26 assets téléchargés
- [ ] ≥8000 bars par asset
- [ ] Pas de gaps >4h

### Phase 1: Screening
- [ ] 200 trials, workers=4-8
- [ ] WFE >0.5, Sharpe >0.8, Trades >50
- [ ] **SHORT ratio 25-75%** ← CRITIQUE PR#19

### Phase 2: Validation
- [ ] 300 trials, workers=1
- [ ] 7 guards hard PASS
- [ ] PBO <0.50
- [ ] DSR >85%
- [ ] PSR >95%
- [ ] CPCV all folds >0.8
- [ ] returns_matrix sauvegardé

### Phase 2B: Regime Stress
- [ ] MARKDOWN: <10 trades ou Sharpe >-2
- [ ] SIDEWAYS: Sharpe ≥0 ← Sinon EXCLU

### Phase 3: Rescue
- [ ] Displacement d26/d52/d78
- [ ] Filtres baseline→moderate→conservative

### Phase 4: Signal Parity
- [ ] Python vs Pine **100% match**

### Phase 5: Portfolio
- [ ] 4 méthodes testées
- [ ] Max Sharpe sélectionné
- [ ] Corrélations <0.5

### Phase 6: Production
- [ ] `asset_config.py` généré
- [ ] Pine Script exporté
- [ ] `project-state.md` mis à jour
- [ ] Reproductibilité vérifiée (2 runs identiques)

---

## 🔧 COMMANDES PRINCIPALES

### Validation Baseline (Phase 2)

```bash
python scripts/run_full_pipeline.py \
    --assets ETH \
    --optimization-mode baseline \
    --trials-atr 300 \
    --trials-ichi 300 \
    --run-guards \
    --workers 1
```

### Filter Rescue (Phase 3)

```bash
python scripts/run_filter_rescue.py ASSET --trials 300
```

### Regime Stress Test (Phase 2B)

```bash
python scripts/run_regime_stress_test.py \
    --assets ETH BTC SHIB \
    --regimes MARKDOWN SIDEWAYS
```

### Signal Parity (Phase 4)

```bash
python scripts/validate_signal_parity.py --asset ETH --bars 1000
```

### Batch Screening (Phase 1)

```bash
# Batch all 26 assets
for asset in SHIB DOT TIA NEAR DOGE ANKR ETH JOE YGG MINA CAKE RUNE \
             EGLD AVAX HBAR TON SUSHI CRV BTC ONE SEI AXS SOL AAVE ZIL GALA; do
    python scripts/run_full_pipeline.py \
        --assets $asset \
        --optimization-mode baseline \
        --trials-atr 200 \
        --trials-ichi 200 \
        --workers 4
done
```

---

## 🎯 AGENTS

| Agent | Rôle | Focus |
|-------|------|-------|
| **Casey** | Orchestrator | Coordination runs, priorisation, décisions pipeline |
| **Jordan** | Dev/Backtest | Exécution runs, code, PRs |
| **Sam** | QA/Guards | Validation 11 guards, verdicts PASS/FAIL |
| **Alex** | Lead Quant | Recherche, expérimentations, nouvelles features |

---

## 📁 KEY FILES

### Source of Truth
- `status/project-state.md` ← **YOU ARE HERE**
- `comms/casey-quant.md` ← Tâches
- `comms/jordan-dev.md` ← Runs
- `comms/sam-qa.md` ← Guards
- `comms/alex-lead.md` ← Recherche

### Rules
- `.cursor/rules/MASTER_PLAN.mdc`
- `.cursor/rules/global-quant.mdc`

### OBSOLÈTE
- ❌ `docs/HANDOFF.md`
- ❌ `run_filter_grid.py`

---

## 🔴 PR#19 — ROOT CAUSE

### Bug Description

Le filtre 5-in-1 utilisait des paramètres **hardcodés** pour TS5/KS5 au lieu des valeurs optimisées par asset.

```python
# AVANT (BUG) - five_in_one.py
class FiveInOneConfig:
    tenkan_5in1: int = 13  # HARDCODÉ!
    kijun_5in1: int = 20   # HARDCODÉ!

# APRÈS (FIX) - asset_config.py
def build_params_for_asset(asset: str) -> FinalTriggerParams:
    config = ASSET_CONFIGS[asset]
    return FinalTriggerParams(
        tenkan_5in1=config["tenkan_5in1"],  # Per-asset
        kijun_5in1=config["kijun_5in1"],    # Per-asset
        ...
    )
```

### Impact

- **SHORTs filtrés incorrectement** → ~50% des opportunités manquées
- **Tous les backtests LONG-biased** → Métriques invalides
- **Regime stress tests faussés** → EGLD/AVAX peut-être OK maintenant

### Fix Deployed

- **PR#19 merged**: `configs/asset_config.py` avec `build_params_for_asset()`
- **Script validation**: `scripts/validate_signal_parity.py`
- **Tests**: `tests/test_short_signal_parity.py` (8 tests)

---

## 🚨 LIVE DEPLOYMENT EXPECTATIONS

### Dégradation Attendue

| Condition | Sharpe Multiplier | MaxDD Multiplier |
|-----------|-------------------|------------------|
| Backtest → Live | ×0.5-0.7 | ×2-3 |
| Period-sensitive (WFE >1.0) | ×0.4-0.5 | ×3-4 |

### Monitoring

- Watch for regime shifts (bear markets)
- Expect higher degradation for period-sensitive assets
- Portfolio rebalancing every 30 days

---

**LAST UPDATED**: 26 janvier 2026, 19:27 UTC
**STATUS**: 🔴 **RESET IN PROGRESS** — 0/26 assets validated
**NEXT CHECKPOINT**: Phase 1 Screening (26 assets)
