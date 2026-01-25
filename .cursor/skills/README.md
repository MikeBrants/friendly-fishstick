# Skills - FINAL TRIGGER v2

Ce dossier contient les **Skills** (procédures how-to) pour le pipeline quant.

**Emplacement:** `.cursor/skills/` (project-level)

---

## Architecture: Skills vs Rules

Les procédures du pipeline sont couvertes par les **rules `.mdc`** des agents qui sont chargées automatiquement via `globs` matching:

| Rule | Agent | Couvre |
|------|-------|--------|
| `sam-qa.mdc` | Sam | 7 guards, validation, workflow rescue |
| `jordan-dev.mdc` | Jordan | Phases 2/3A/3B/4, commandes, patterns code |
| `casey-orchestrator.mdc` | Casey | Coordination, verdicts, assignations |

**Résultat:** Les skills redondants ont été supprimés pour éviter la duplication et les désynchronisations.

---

## Skill Disponible

| Skill | Description | Quand l'utiliser |
|-------|-------------|------------------|
| `regime-analyzer` | Analyse BULL/BEAR/SIDEWAYS avec code Python | Debug performance, vérifier guard007 |

### regime-analyzer

**Fichier:** `.cursor/skills/regime-analyzer/SKILL.md`

Contient du code Python unique pour:
- `compute_regime()` - Calcule le régime de marché
- `assign_regime_to_trades()` - Attribue les régimes aux trades (entry_time, pas exit!)
- `analyze_by_regime()` - Métriques par régime
- `check_guard007()` - Vérifie le guard régime mismatch

**Usage:** Demander "analyse les régimes pour BTC" ou "vérifie guard007"

---

## Référence Rapide

### Seuils Guards (25-JAN-2026)

| Guard | Seuil | Critique |
|-------|-------|----------|
| WFE | ≥0.6 | OUI |
| MC p-value | <0.05 | OUI |
| Sensitivity | <15% | OUI |
| Bootstrap CI | >1.0 | OUI |
| Top10 trades | <40% | OUI |
| Stress Sharpe | >1.0 | OUI |
| Regime mismatch | ≤1 | OUI |
| OOS Trades | ≥60 | OUI |
| OOS Sharpe | >1.0 | target >2.0 |

### Commandes Clés

```bash
# Phase 2: Validation
python scripts/run_full_pipeline.py --assets ASSET \
  --workers 1 --trials-atr 300 --trials-ichi 300 \
  --enforce-tp-progression --run-guards

# Phase 3A: Displacement Rescue
python scripts/run_full_pipeline.py --assets ASSET \
  --fixed-displacement 26 --workers 1 \
  --trials-atr 300 --trials-ichi 300 \
  --enforce-tp-progression --run-guards

# Phase 4: Filter Rescue (3 modes: baseline → moderate → conservative)
python scripts/run_filter_rescue.py ASSET --trials 300 --workers 1
```

### Displacement par Type Asset

| Type | Displacement | Exemples |
|------|--------------|----------|
| Meme/Fast | 26 | DOGE, JOE, SHIB |
| Standard | 52 | BTC, ETH |
| Custom | 65 | OSMO |
| Slow/L2 | 78 | OP, MINA |
