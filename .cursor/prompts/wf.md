# Workflow Orchestré — Raccourci Cursor

## Usage rapide
Dans Cursor: `@wf.md` puis "go" ou numéro de tâche

---

## Commandes

| Tape | Action |
|------|--------|
| `go` | Status complet + prochaine action |
| `0` | TASK 0: WFE Audit (BLOQUANT) |
| `1` | TASK 1: PBO Implementation |
| `2` | TASK 2: CPCV Implementation |
| `3` | TASK 3: Regime Guards (indicatifs) |
| `tests` | Créer tests unitaires manquants |
| `pr` | Résumé PRs + conflits |

---

## go

```
1. cat status/project-state.md
2. Résume en 5 points max
3. Identifie le PREMIER blocker
4. Propose la commande exacte à exécuter
```

---

## 0 — WFE Audit

```
Fichier: reports/wfe-audit-2026-01-25.md

Analyse crypto_backtest/optimization/walk_forward.py:120
- Le calcul utilise-t-il returns ou Sharpe?
- Pourquoi multiplication par 100?
- Compare avec définition Pardo (OOS_Sharpe / IS_Sharpe)

Output: diagnostic + recommandation FIX/KEEP
```

---

## 1 — PBO

```
Fichier: crypto_backtest/validation/pbo.py (existe déjà)

Actions:
1. Valider le code stub existant
2. Créer tests/validation/test_pbo.py
3. Tester sur ETH, SHIB, DOT

Seuils: <0.15 PASS | 0.15-0.30 MARGINAL | >0.30 FAIL
```

---

## 2 — CPCV

```
Fichier: crypto_backtest/validation/cpcv.py (existe déjà)

Actions:
1. Valider le code stub existant
2. Créer tests/validation/test_cpcv.py
3. Comparer avec Walk-Forward actuel
```

---

## 3 — Regime Guards

```
Fichiers à créer:
- crypto_backtest/analysis/regime_detector.py
- crypto_backtest/validation/indicative_guards.py
- tests/test_regime_detector.py

IMPORTANT: blocks_validation=False TOUJOURS

Voir: docs/REGIME_AWARE_GUARDS_IMPLEMENTATION.md
```

---

## tests

```
Fichiers manquants:
- tests/validation/test_pbo.py
- tests/validation/test_cpcv.py
- tests/test_regime_detector.py
- tests/test_indicative_guards.py

Template:
import pytest
from crypto_backtest.validation.X import Y

def test_Y_basic():
    result = Y(...)
    assert result...
```

---

## pr

```
1. gh pr list
2. Pour chaque PR ouverte: status, conflits, reviewers
3. Recommande l'ordre de merge
```

---

## Règles

- TOUJOURS lire project-state.md AVANT toute action
- TOUJOURS mettre à jour comms/[agent].md APRÈS complétion
- Format commit: `feat|fix|docs: description courte`
- Si doute → demander plutôt que deviner
