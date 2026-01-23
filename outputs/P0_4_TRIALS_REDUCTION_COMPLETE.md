# P0.4 - Réduction Trials Phase 3B (Anti-Overfitting) - COMPLÉTÉ ✅

**Date:** 2026-01-23 12:50  
**Fichier:** `scripts/run_phase3b_optimization.py`

## Problème Identifié

**BTC Phase 3B avec 300+300 trials:**
- Baseline PROD: Sharpe 2.14, WFE >0.6 ✅
- Phase 3B d52: Sharpe -0.45, WFE -0.09 ❌
- Phase 3B d26: Sharpe 0.77, WFE -0.66 ❌

**Cause:** Overfitting massif avec 300+300 trials sur assets déjà optimisés.

---

## Modifications Appliquées

### 1. Réduction Trials Par Défaut

**Lignes 322-330:**
```python
# Phase 3B: 150 trials (vs 300 Phase 2) pour éviter overfitting
# sur assets avec baseline déjà optimisé. Augmenter seulement si
# WFE reste >0.6 et amélioration <5%.
parser.add_argument(
    "--trials-atr",
    type=int,
    default=150,  # AVANT: 300
    help="Number of ATR optimization trials (default: 150)",
)
parser.add_argument(
    "--trials-ichi",
    type=int,
    default=150,  # AVANT: 300
    help="Number of Ichimoku optimization trials (default: 150)",
)
```

### 2. Garde-Fou WFE Négatif

**Lignes 264-275:**
```python
# Garde-fou: WFE négatif = overfitting détecté
wfe_value = opt_results.get("wfe", 0)
if wfe_value < 0:
    print(f"  [{asset}] WARNING: WFE négatif ({wfe_value:.2f}) = overfitting détecté")
    return {
        "asset": asset,
        "displacement": displacement,
        "status": "OVERFITTING",
        "wfe": wfe_value,
        "oos_sharpe": opt_results.get("oos_sharpe", 0),
        "error": "WFE < 0 indicates overfitting",
    }
```

**Comportement:**
- Détecte WFE négatif immédiatement après optimisation
- Early exit avec status "OVERFITTING"
- Évite de lancer guards inutilement
- Affiche warning explicite

---

## Validation

✅ **Syntaxe Python:** Validée (`py_compile` OK)  
✅ **Garde-fou:** Implémenté avec early exit  
✅ **Commentaires:** Ajoutés pour documentation

---

## Impact

### Avant
- Trials par défaut: 300+300 = 600 trials
- Risque overfitting élevé
- Pas de détection WFE négatif

### Après
- Trials par défaut: 150+150 = 300 trials
- Risque overfitting réduit
- Détection automatique WFE négatif
- Early exit pour économiser temps

---

## Prochaines Actions

1. ✅ Fix appliqué
2. ⏭️ Tester Phase 3B avec ETH (trials 150)
3. ⏭️ Tester Phase 3B avec JOE (trials 150)
4. ⏭️ Vérifier que WFE reste positif

**Commande de test:**
```bash
python scripts/run_phase3b_optimization.py --assets ETH --workers 4
# (utilise maintenant 150+150 par défaut)
```

---

**Date:** 2026-01-23 12:50  
**Status:** ✅ PRÊT POUR TEST
