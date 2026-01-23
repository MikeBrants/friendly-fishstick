# Intégration Watcher + Sam Auto-Validator

## Architecture Complète

```
┌──────────────────┐     watch      ┌──────────────────┐
│  casey-quant.md  │ ─────────────▶ │    WATCHER.py    │
│   (nouvelles     │                │  (tourne 24/7)   │
│    [TASK])       │                └────────┬─────────┘
└──────────────────┘                         │
                                             │ détecte [TASK]
                                             ▼
                              ┌──────────────────────────┐
                              │  Lance le script Python  │
                              │  (subprocess)            │
                              └──────────────┬───────────┘
                                             │
                    ┌────────────────────────┼────────────────────────┐
                    ▼                        ▼                        ▼
          ┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
          │ jordan-dev.md   │     │ sam_auto_        │     │ sam-qa.md       │
          │ [RUN_START]     │     │ validator.py    │     │ [VALIDATION]    │
          │ [RUN_COMPLETE]  │────▶│ (parse CSV)     │────▶│ PASS/FAIL       │
          └─────────────────┘     └─────────────────┘     └─────────────────┘
```

## Workflow Automatique

1. **Casey** écrit une `[TASK]` dans `comms/casey-quant.md`
2. **Watcher** détecte la nouvelle tâche (poll toutes les 30s)
3. **Watcher** écrit `[RUN_START]` dans `jordan-dev.md`
4. **Watcher** exécute la commande (subprocess, timeout 1h)
5. **Watcher** écrit `[RUN_COMPLETE]` dans `jordan-dev.md`
6. **Watcher** déclenche `sam_auto_validator.py --batch`
7. **Sam Auto-Validator** parse le CSV de guards (`outputs/phase3b_*_guards_summary_*.csv`)
8. **Sam Auto-Validator** trouve le scan CSV correspondant pour métriques OOS
9. **Sam Auto-Validator** valide les 7 guards selon seuils stricts
10. **Sam Auto-Validator** poste `[VALIDATION]` dans `sam-qa.md` avec verdict PASS/FAIL

## Fichiers Créés

| Fichier | Description |
|---------|-------------|
| `tools/watcher.py` | Watcher principal qui surveille casey-quant.md |
| `tools/sam_auto_validator.py` | Module de validation automatique des guards |
| `tools/README.md` | Documentation d'utilisation |
| `tools/INTEGRATION.md` | Ce fichier (architecture et workflow) |

## Utilisation

### Lancer le watcher (recommandé)

```powershell
# Terminal séparé
cd C:\Users\Arthur\friendly-fishstick
python tools/watcher.py
```

Le watcher va automatiquement :
- Détecter les nouvelles tâches
- Exécuter les commandes
- Déclencher la validation Sam automatiquement

### Lancer Sam Auto-Validator seul

```powershell
# Mode watch (surveille les nouveaux fichiers)
python tools/sam_auto_validator.py --watch

# Mode batch (valide tous les fichiers récents)
python tools/sam_auto_validator.py --batch

# Valide un fichier spécifique
python tools/sam_auto_validator.py --file outputs/phase3b_ETH_d26_guards_summary_*.csv
```

## Format des Verdicts

Le module Sam génère des rapports complets dans `sam-qa.md` :

```markdown
## [HH:MM] [VALIDATION] @Sam -> @Casey

**Asset:** ETH
**Run ref:** [14:30] [RUN_COMPLETE] @Jordan -> @Sam
**Date run:** 2026-01-23 14:30:00 (post-fix TP ✅)
**Mode:** baseline
**Displacement:** 26

### Guards Check (7/7 requis)

| Guard | Seuil | Valeur | Status |
|-------|-------|--------|--------|
| MC p-value | < 0.05 | 0.031 | ✅ PASS |
| Sensitivity | < 10% | 8.5% | ✅ PASS |
| Bootstrap CI | > 1.0 | 1.23 | ✅ PASS |
| Top10 trades | < 40% | 25.3% | ✅ PASS |
| Stress Sharpe | > 1.0 | 1.15 | ✅ PASS |
| Regime mismatch | < 1% | 0.5% | ✅ PASS |
| WFE | > 0.6 | 0.82 | ✅ PASS |

### Métriques OOS

- Sharpe: **2.09** ✅ (> 1.0 requis)
- MaxDD: **-2.5%**
- Trades: 57 ✅ (> 60 requis)
- Profit Factor: 1.45
- IS Sharpe: 2.55 (dégradation: 0.82x)
- WFE: 0.82 ✅

### Verdict

**Status:** 7/7 PASS
**Recommendation:** PROD
**Next:** @Casey rend verdict final
```

## Seuils des 7 Guards

| Guard | Seuil | Description |
|-------|-------|-------------|
| guard001 | MC p-value < 0.05 | Monte Carlo permutation test |
| guard002 | Sensitivity < 10% | Variance des paramètres |
| guard003 | Bootstrap CI > 1.0 | Intervalle de confiance Sharpe |
| guard005 | Top10 trades < 40% | Distribution des trades |
| guard006 | Stress Sharpe > 1.0 | Stress test (fees/slippage) |
| guard007 | Regime mismatch < 1% | Analyse de régime |
| WFE | WFE > 0.6 | Walk-Forward Efficiency |

## Détection des Fichiers

### Guards CSV
- Pattern: `outputs/phase3b_{asset}_d{displacement}_guards_summary_*.csv`
- Exemple: `outputs/phase3b_ETH_d26_guards_summary_20260123_135217.csv`

### Scan CSV
- Pattern: `outputs/phase3b_{asset}_d{displacement}_multiasset_scan_*.csv`
- Utilisé pour extraire OOS Sharpe, WFE, MaxDD, etc.

## Gestion des Erreurs

- Si le watcher ne trouve pas `sam_auto_validator.py`, il écrit une demande de validation manuelle
- Si le scan CSV n'est pas trouvé, les métriques OOS sont marquées comme N/A
- Si un guard CSV est invalide, l'erreur est loggée et le fichier est ignoré

## Prochaines Améliorations

1. **TP Progression Check** : Vérifier automatiquement que TP1 < TP2 < TP3 avec gaps >= 0.5
2. **Mode Detection** : Extraire automatiquement le mode (baseline, medium_distance_volume, etc.) depuis le scan
3. **Jordan Run Ref** : Lier automatiquement la validation au `[RUN_COMPLETE]` correspondant
4. **Dashboard Streamlit** : Interface visuelle pour monitorer le watcher en temps réel
