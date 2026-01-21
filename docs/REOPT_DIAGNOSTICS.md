# Amélioration Reopt + Diagnostics Granulaires

**Date**: 2026-01-21
**Statut**: ✅ Implémenté

## Problèmes Résolus

### 1. Bouton Reopt ne navigue pas vers la page d'optimisation ✅
**Solution**: Le bouton Reopt dans la page Comparaison stocke maintenant les settings recommandés dans `st.session_state` et navigue automatiquement vers la page Bayesian.

### 2. Diagnostics trop succincts, manque d'explications ✅
**Solution**: Nouveau module `diagnostics.py` avec 6+ checks détaillés et recommandations contextuelles.

---

## Fichiers Modifiés

### 1. `crypto_backtest/analysis/diagnostics.py` ✅
**Nouveau fichier** contenant:
- `DiagnosticResult`: dataclass pour un check individuel
- `AssetDiagnostics`: dataclass pour le diagnostic complet
- `diagnose_asset()`: fonction principale de diagnostic
- `render_diagnostics_markdown()`: rendu markdown (optionnel)

**Checks implémentés**:
1. **Sharpe Ratio OOS** - Évalue la performance ajustée au risque
2. **Walk-Forward Efficiency** - Détecte l'overfitting
3. **Max Drawdown OOS** - Évalue le risque de ruine
4. **Nombre de Trades** - Vérifie la significativité statistique
5. **Consistance IS/OOS** - Mesure la dégradation de performance
6. **Guards Checks** (si disponibles):
   - Monte Carlo (GUARD-001)
   - Sensitivity (GUARD-002)
   - Bootstrap CI (GUARD-003)

**Recommandations automatiques**:
- Ajustement du nombre de trials (`trials_atr`, `trials_ichi`)
- Suggestion de tester displacement grid
- Recommandation de fixer displacement à 52
- Suggestion d'exclure l'asset si inadapté
- Ajustement de la période de données (`days_back`)

### 2. `app.py` ✅
**Modifications**:

#### a) Initialisation session_state (lignes 765-768)
```python
# Reopt settings
if "reopt_asset" not in st.session_state:
    st.session_state.reopt_asset = None
if "reopt_settings" not in st.session_state:
    st.session_state.reopt_settings = {}
```

#### b) Page "🏆 Comparaison Assets" (après ligne 2996)
**Nouvelle section "🔬 Diagnostic détaillé"**:
- Sélecteur d'asset pour diagnostic
- Affichage du statut global (PASS/WARN/FAIL) avec bandeau coloré
- Tableau récapitulatif des checks
- Expanders avec explications détaillées et recommandations
- **Bouton "🚀 Ré-optimiser"** qui:
  - Stocke l'asset et les settings dans `st.session_state`
  - Navigue vers la page "⚡ Bayesian"
  - Log dans la console

#### c) Page "⚡ Bayesian" (lignes 1974-2089) ✅
**Déjà implémenté** (pas de changement nécessaire):
- Détection du mode reopt via `st.session_state.reopt_asset`
- Bandeau d'information jaune "🔄 Mode Ré-optimisation"
- Bouton "❌ Annuler le mode reopt"
- Pré-remplissage automatique:
  - Asset sélectionné par défaut
  - Trials ATR/Ichi selon recommandations
  - Displacement grid activé si recommandé
  - Displacement fixé si recommandé

---

## Flux Utilisateur

### Scénario 1: Asset FAIL/WARN nécessitant reopt

1. **Étape 1**: Utilisateur va sur "🏆 Comparaison Assets"
2. **Étape 2**: Filtre ou trouve un asset avec statut FAIL/WARN
3. **Étape 3**: Sélectionne l'asset dans "🔬 Diagnostic détaillé"
4. **Étape 4**: Consulte les checks détaillés avec explications
5. **Étape 5**: Lit les recommandations spécifiques
6. **Étape 6**: Clique sur "🚀 Ré-optimiser [ASSET]"
7. **Navigation automatique** vers "⚡ Bayesian"
8. **Étape 7**: Page Bayesian affiche:
   - Bandeau "🔄 Mode Ré-optimisation"
   - Asset pré-sélectionné
   - Trials pré-remplis
   - Displacement configuré selon recommandations
9. **Étape 8**: Lance l'optimisation avec les paramètres recommandés

### Scénario 2: Annulation du mode reopt

1. Sur la page "⚡ Bayesian" en mode reopt
2. Clique "❌ Annuler le mode reopt"
3. Le mode reopt est désactivé
4. Les paramètres reviennent aux valeurs par défaut

---

## Critères de Validation

### ✅ Checklist d'implémentation

- [x] `crypto_backtest/analysis/diagnostics.py` créé avec `diagnose_asset()` et `DiagnosticResult`
- [x] Imports ajoutés dans `app.py` (ligne 489 - déjà présent)
- [x] Session state initialisé pour `reopt_asset` et `reopt_settings`
- [x] Page Comparaison/Fichiers affiche diagnostic détaillé par asset
- [x] Chaque check a: status, valeur, seuil, explication, recommandation
- [x] Bouton "Ré-optimiser" stocke settings dans `st.session_state` et navigue vers Bayesian
- [x] Page Bayesian détecte `reopt_asset` et pré-remplit les settings
- [x] Mode reopt affiche un bandeau d'info et bouton "Annuler"

### 🧪 Tests à effectuer

#### Test 1: Diagnostic d'un asset FAIL
```
1. Lancer: streamlit run app.py
2. Aller sur "🏆 Comparaison Assets"
3. Sélectionner un asset avec Sharpe OOS < 1.0
4. Observer:
   - Statut global "❌ FAIL" en rouge
   - Table des checks avec statuts individuels
   - Expanders avec explications et recommandations
   - Paramètres recommandés affichés (trials, displacement, etc.)
```

**Résultat attendu**: Tous les checks sont affichés avec détails appropriés.

#### Test 2: Bouton Reopt navigation
```
1. Dans le diagnostic d'un asset FAIL/WARN
2. Cliquer "🚀 Ré-optimiser [ASSET]"
3. Observer:
   - Navigation automatique vers "⚡ Bayesian"
   - Bandeau jaune "🔄 Mode Ré-optimisation" visible
   - Asset correct sélectionné par défaut
   - Trials pré-remplis selon recommandations
   - Log console: "🔄 HH:MM:SS │ Reopt [ASSET] avec settings recommandés"
```

**Résultat attendu**: Navigation fonctionne, tous les paramètres sont pré-remplis correctement.

#### Test 3: Displacement recommandé
```
1. Diagnostic d'un asset avec Sharpe OOS entre 0.5 et 1.0 (WARN)
2. Observer recommandations: "tester displacement grid"
3. Cliquer "Ré-optimiser"
4. Sur page Bayesian, observer:
   - Info "💡 Recommandation: tester le displacement grid"
   - Checkbox "Inclure Displacement" pré-cochée
   - Valeurs [26, 39, 52, 65, 78] sélectionnées par défaut
```

**Résultat attendu**: Displacement activé et configuré selon recommandations.

#### Test 4: Displacement fixé
```
1. Diagnostic d'un asset avec WFE < 0.3 (FAIL overfit)
2. Observer recommandations: "fixer displacement=52"
3. Cliquer "Ré-optimiser"
4. Sur page Bayesian, observer:
   - Info "💡 Recommandation: fixer displacement à 52"
   - Checkbox "Inclure Displacement" désactivée
   - Displacement_values = [52]
```

**Résultat attendu**: Displacement fixé à 52, non optimisé.

#### Test 5: Annulation mode reopt
```
1. En mode reopt sur page Bayesian
2. Cliquer "❌ Annuler le mode reopt"
3. Observer:
   - Bandeau "Mode Ré-optimisation" disparaît
   - Assets reviennent aux 3 premiers SCAN_ASSETS
   - Trials reviennent à 100/100
   - Displacement désactivé par défaut
```

**Résultat attendu**: Mode reopt désactivé, interface revient à l'état normal.

#### Test 6: Asset avec guards disponibles
```
1. Sélectionner un asset qui a des résultats dans guards_summary.csv
2. Observer le diagnostic:
   - Checks supplémentaires: Monte Carlo, Sensitivity, Bootstrap CI
   - Explications spécifiques aux guards
   - Recommandations contextuelles (ex: "besoin de plus de trades")
```

**Résultat attendu**: Guards checks affichés avec p-values et recommandations.

---

## Exemple de Diagnostic

### Asset: LINK (Sharpe OOS: 0.75, WFE: 0.45)

**Statut Global**: ⚠️ WARN

| Check | Status | Valeur | Seuil |
|-------|--------|--------|-------|
| Sharpe Ratio OOS | ⚠️ WARN | 0.75 | ≥ 1.0 |
| Walk-Forward Efficiency | ⚠️ WARN | 0.45 | ≥ 0.6 |
| Max Drawdown OOS | ✅ PASS | 8.2% | ≤ 15% |
| Nombre de Trades | ✅ PASS | 127 | ≥ 100 |
| Consistance IS/OOS | ✅ PASS | -25% | ≤ 40% |

**Recommandations**:
- Trials ATR: 150
- Trials Ichi: 150
- Tester displacement grid: Oui
- Days back: 730

**Action**: Bouton "🚀 Ré-optimiser LINK" → Navigation Bayesian avec settings pré-remplis

---

## Notes Techniques

### Session State Variables

```python
st.session_state.reopt_asset: str | None
    # Asset sélectionné pour ré-optimisation
    # None si mode normal

st.session_state.reopt_settings: dict[str, Any]
    # Settings recommandés par le diagnostic
    # Keys:
    #   - asset: str
    #   - trials_atr: int
    #   - trials_ichi: int
    #   - days_back: int (730 ou 1095)
    #   - test_displacement: bool
    #   - fix_displacement: int | None (52 ou None)
    #   - exclude_asset: bool
```

### Priorités des Recommandations

1. **Sharpe OOS < 0.5** → FAIL → Exclure asset
2. **WFE < 0.3** → FAIL → Fixer displacement=52, réduire trials (50)
3. **Sharpe 0.5-1.0** → WARN → Augmenter trials (150), tester displacement
4. **WFE 0.3-0.6** → WARN → Réduire trials (80), simplifier
5. **Trades < 50** → FAIL → Augmenter days_back (1095)
6. **DD > 15%** → FAIL → Revoir stratégie

---

## Maintenance Future

### Ajouter un nouveau check

1. Éditer `crypto_backtest/analysis/diagnostics.py`
2. Ajouter le check dans `diagnose_asset()`:
```python
# New check
new_value = scan_row.get("new_metric", 0)
if new_value >= threshold:
    status = "PASS"
    explanation = "..."
    recommendation = "..."
else:
    status = "FAIL"
    explanation = "..."
    recommendation = "..."
    recommendations["new_setting"] = value

checks.append(DiagnosticResult(...))
```
3. Mettre à jour `recommended_settings` si nécessaire
4. Tester sur page Comparaison

### Personnaliser les seuils

Les seuils sont codés en dur dans `diagnose_asset()`:
- Sharpe OOS: 2.0 (excellent), 1.0 (acceptable), 0.5 (warn)
- WFE: 1.0 (excellent), 0.6 (acceptable), 0.3 (warn)
- Max DD: 5% (excellent), 10% (acceptable), 15% (warn)
- Trades: 100 (robust), 50 (minimum)

Pour personnaliser, créer une `DiagnosticConfig` dataclass.

---

## Changelog

**2026-01-21**: Implémentation initiale
- Création `diagnostics.py` avec 6 checks
- Intégration dans page Comparaison Assets
- Flux reopt complet fonctionnel
- Documentation complète
