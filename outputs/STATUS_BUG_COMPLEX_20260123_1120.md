# Status Bug Complex Number - 2026-01-23 11:20

## Résumé Exécutif

**13 assets PROD** (objectif: 20+)  
**4 assets bloqués** par bug complex number (STRK, METIS, AEVO, YGG)  
**1 asset débloqué** avec fix V3 (SHIB)

## Problème Actuel

### Symptôme
- Erreur: `float() argument must be a string or a real number, not 'complex'`
- Localisation: `[DEBUG] Monte Carlo failed for {ASSET}`
- Assets affectés: STRK, METIS, AEVO, YGG
- Asset SUCCESS: SHIB

### Comportement Observé
- Tests avec fix V4 prennent 5+ minutes (vs 9 secondes habituellement)
- Run STRK toujours en cours après 5+ minutes
- Pas de nouveau résultat produit
- Soit bloqué, soit très lent à cause du try/except qui continue malgré les erreurs

## Fixes Tentés

| Version | Actions | Résultat |
|:--------|:--------|:---------|
| V1-V2 | Timezone, bootstrap, metrics | SHIB FAIL |
| V3 | `_safe_float()` 24 utilisations | SHIB SUCCESS, autres FAIL |
| V4 | 10+ protections supplémentaires + try/except compute_metrics | En cours (5+ min, probablement bloqué) |

## Approche Alternative Recommandée

### Option A: Protection Globale NumPy (RECOMMANDÉ)

Forcer tous les arrays numpy à être réels dès leur création:

```python
# Au début de _build_random_equity_curve
def _build_random_equity_curve(...) -> np.ndarray:
    ...
    equity = np.full(n_bars, initial_capital, dtype=float)
    ...
    # À la fin, avant return
    equity = np.real(equity)  # Force réel
    return equity.astype(float)  # Force float64
```

### Option B: Skip Monte Carlo pour Assets Problématiques

Temporairement skip guard001 (Monte Carlo) pour ces 4 assets et valider avec les 6 autres guards:

```bash
python scripts/run_guards_multiasset.py \
  --assets STRK METIS AEVO YGG \
  --params-file outputs/complex_fix_test_params.csv \
  --guards sensitivity bootstrap trade_dist stress regime wfe \
  --workers 4
```

### Option C: Comparer SHIB vs STRK Equity Curves

Analyser les equity curves générées pour comprendre pourquoi SHIB fonctionne:

```python
# Générer Monte Carlo equity curves pour SHIB et STRK
# Comparer les valeurs, identifier où apparaît le complexe
```

## Recommandation Immédiate

1. **Killer le run STRK bloqué** (PID 32136)
2. **Appliquer Option A** (protection globale numpy)
3. **Tester STRK avec fix V5**
4. Si succès → tester tous les assets (STRK, METIS, AEVO, YGG)
5. Si échec → appliquer Option B (skip Monte Carlo temporairement)

## Runs en Parallèle

- **HBAR d26:** En cours (10+ minutes, normal pour optimization + guards)
- **STRK debug:** Bloqué après 5+ minutes (à killer)

## Impact

- **Si Option A fonctionne:** +4 assets PROD → 17 assets total (85% de l'objectif)
- **Si Option B (skip MC):** Validation partielle possible mais non idéale
- **Délai estimé:** 1-2h pour résoudre complètement

## Prochaines Étapes

1. Killer run STRK bloqué
2. Appliquer fix V5 (Option A - protection globale numpy)
3. Tester STRK
4. Si succès → tester tous les 4 assets
5. Documenter le fix final
6. Continuer avec HBAR et autres priorités

---

**Date:** 2026-01-23 11:20  
**Status:** Investigation en cours, fix V5 prêt à tester
