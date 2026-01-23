# WATCHER Multi-Agent — FINAL TRIGGER v2

Watcher automatique qui surveille `comms/casey-quant.md` et orchestre l'exécution des tâches par Jordan et Sam.

## Architecture

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
          │ jordan-dev.md   │     │   sam-qa.md     │     │ project-state   │
          │ [RUN_START]     │     │ [VALIDATION]    │     │ MAJ auto        │
          │ [RUN_COMPLETE]  │     │ PASS/FAIL       │     │                 │
          └─────────────────┘     └─────────────────┘     └─────────────────┘
```

## Installation

Le watcher est déjà prêt à l'emploi, aucune installation supplémentaire requise.

## Utilisation

### 1. Lancer le watcher

Dans un terminal séparé (pour qu'il tourne en arrière-plan) :

```powershell
cd C:\Users\Arthur\friendly-fishstick
python tools/watcher.py
```

Le watcher va :
- Surveiller `comms/casey-quant.md` toutes les 30 secondes
- Détecter les nouvelles `[TASK]` assignées par Casey à Jordan
- Exécuter automatiquement les commandes
- Écrire les logs dans `comms/jordan-dev.md`
- Déclencher Sam pour validation une fois terminé

### 2. Arrêter le watcher

Appuyer sur `Ctrl+C` dans le terminal où tourne le watcher.

## Fonctionnement

### Détection des tâches

Le watcher parse `casey-quant.md` pour trouver les sections :
```markdown
## [HH:MM] [TASK] @Casey -> @Jordan
**Asset:** XXX
**Command:**
```bash
python scripts/run_full_pipeline.py ...
```
```

### Exécution automatique

1. **Détection** : Nouvelle `[TASK]` détectée
2. **RUN_START** : Écrit dans `jordan-dev.md` avec timestamp
3. **Exécution** : Lance la commande en subprocess (timeout 1h)
4. **RUN_COMPLETE/FAILED** : Écrit le résultat avec métriques extraites
5. **Validation** : Si succès, déclenche Sam dans `sam-qa.md`

### Métriques extraites

Le watcher essaie d'extraire automatiquement :
- OOS Sharpe
- WFE (Walk-Forward Efficiency)

Ces métriques sont ajoutées dans le log `[RUN_COMPLETE]`.

## Configuration

Variables dans `watcher.py` :

```python
POLL_INTERVAL = 30  # secondes entre chaque check
TIMEOUT = 3600      # 1h max par commande
```

## Logs

Tous les logs sont écrits dans :
- `comms/jordan-dev.md` : RUN_START, RUN_COMPLETE, RUN_FAILED
- `comms/sam-qa.md` : VALIDATION_PENDING (déclenché automatiquement)

Format standardisé selon les conventions du projet.

## Dépannage

### Le watcher ne détecte pas les nouvelles tâches

1. Vérifier que `comms/casey-quant.md` existe et contient des `[TASK]`
2. Vérifier le format : doit être `## [HH:MM] [TASK] @Casey -> @Jordan`
3. Vérifier que la commande est dans un bloc ````bash`

### La commande échoue

- Le watcher écrit `[RUN_FAILED]` avec l'erreur dans `jordan-dev.md`
- Vérifier les logs pour identifier le problème
- Le watcher continue de surveiller même après une erreur

### Timeout après 1h

- Les commandes longues (>1h) sont interrompues
- Augmenter `TIMEOUT` dans le code si nécessaire

## Sam Auto-Validator

Le module `sam_auto_validator.py` parse automatiquement les CSV de guards et poste les verdicts dans `sam-qa.md`.

### Utilisation

```powershell
# Mode watch (surveille les nouveaux fichiers)
python tools/sam_auto_validator.py --watch

# Mode batch (valide tous les fichiers récents non traités)
python tools/sam_auto_validator.py --batch

# Valide un fichier spécifique
python tools/sam_auto_validator.py --file outputs/phase3b_ETH_d26_guards_summary_*.csv
```

### Intégration avec le watcher

Le watcher appelle automatiquement `sam_auto_validator.py --batch` après chaque `[RUN_COMPLETE]` pour valider les guards et poster le verdict.

### Format du verdict

Le module génère un rapport complet dans `sam-qa.md` avec :
- Tableau des 7 guards (PASS/FAIL)
- Métriques OOS (Sharpe, MaxDD, Trades, WFE)
- Vérifications additionnelles (TP progression, Sharpe suspect)
- Verdict final (PASS/FAIL) et recommandation (PROD/BLOCKED)

## Prochaines améliorations possibles

1. **Dashboard Streamlit** : Interface visuelle pour monitorer le watcher
2. **Notifications** : Alertes email/Slack quand une tâche est terminée
3. **Retry logic** : Réessayer automatiquement en cas d'échec temporaire
