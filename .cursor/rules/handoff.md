# Procédures de Handoff - FINAL TRIGGER v2

## Handoff Data → Optimization

### Prérequis
- ✅ Données téléchargées dans `data/`
- ✅ Fichier `status/data_agent.json` avec `status: "ready"`
- ✅ Validation qualité données OK

### Actions
1. Optimization Agent lit `status/data_agent.json`
2. Vérifie présence fichiers CSV dans `data/`
3. Crée `comms/optimization_started_{asset}_{timestamp}.json`
4. Lance optimisation
5. Met à jour `status/optimization_agent.json`

### Checklist
- [ ] Fichier CSV existe dans `data/`
- [ ] Nombre de bars >= 8000
- [ ] Pas de gaps majeurs dans les données
- [ ] Timezone UTC

---

## Handoff Optimization → Validation

### Prérequis
- ✅ Scan complet terminé
- ✅ Fichier `outputs/multiasset_scan_*.csv` créé
- ✅ Status = "SUCCESS" ou "FAIL" avec raison

### Actions
1. Validation Agent détecte nouveau scan CSV
2. Lit les paramètres optimaux
3. Crée `comms/validation_request_{asset}_{timestamp}.json`
4. Lance les 7 guards
5. Génère `outputs/multiasset_guards_summary_*.csv`
6. Met à jour `status/validation_agent.json`

### Checklist
- [ ] Scan file existe et est valide
- [ ] Status = "SUCCESS" (sinon skip guards)
- [ ] OOS trades >= 60
- [ ] OOS Sharpe >= 1.0 (sinon skip guards)

---

## Handoff Validation → Analysis

### Prérequis
- ✅ Guards terminés
- ✅ Fichier `outputs/multiasset_guards_summary_*.csv` créé
- ✅ Tous les guards exécutés (même si FAIL)

### Actions
1. Analysis Agent détecte nouveau guards summary
2. Lit scan + guards results
3. Exécute diagnostics
4. Génère recommandations
5. Crée `outputs/ANALYSIS_{asset}_{timestamp}.md`
6. Met à jour `status/analysis_agent.json`

### Checklist
- [ ] Guards summary existe
- [ ] Scan file correspondant existe
- [ ] Tous les guards ont des résultats (pas de NaN)

---

## Handoff Analysis → Production

### Prérequis
- ✅ Analysis terminée
- ✅ Recommandation = "production" ou "deploy"
- ✅ Tous guards PASS
- ✅ WFE > 0.6
- ✅ Variance < 10%

### Actions
1. Production Agent lit `status/analysis_agent.json`
2. Vérifie `recommendation: "production"`
3. Lit paramètres optimaux depuis scan
4. Génère Pine Script TradingView
5. Met à jour `crypto_backtest/config/asset_config.py`
6. Crée `outputs/pine_plan.csv`
7. Met à jour `status/production_agent.json`

### Checklist
- [ ] Tous guards PASS
- [ ] WFE >= 0.6
- [ ] OOS Sharpe >= 1.0
- [ ] Variance < 10%
- [ ] Paramètres validés (TP progression OK)

---

## Handoff Analysis → Re-Optimization

### Prérequis
- ✅ Analysis terminée
- ✅ Recommandation = "reoptimize"
- ✅ Raison identifiée (variance, WFE, etc.)

### Actions
1. Analysis Agent crée `comms/reopt_request_{asset}_{timestamp}.json`
2. Spécifie filter mode recommandé (MODERATE/CONSERVATIVE)
3. Optimization Agent lit la requête
4. Re-optimise avec nouveau filter mode
5. Retour au workflow standard

### Checklist
- [ ] Raison de reopt claire
- [ ] Filter mode recommandé justifié
- [ ] Paramètres précédents sauvegardés
- [ ] Comparaison avant/après possible

---

## Handoff Multi-Asset Batch

### Prérequis
- ✅ Liste d'assets définie
- ✅ Priorités assignées (P0, P1, P2)

### Actions
1. Optimization Agent traite assets par batch
2. Pour chaque asset :
   - Optimization → Validation → Analysis
   - Si FAIL → Reopt si recommandé
3. Analysis Agent agrège résultats
4. Génère rapport batch
5. Production Agent déploie assets validés

### Checklist
- [ ] Batch size raisonnable (6-8 assets max)
- [ ] Workers configurés correctement
- [ ] Outputs timestampés pour éviter collisions
- [ ] Logs centralisés

---

## Documentation Handoff

Chaque handoff doit être documenté dans :
- `docs/HANDOFF.md` - État global
- `docs/BACKTESTING.md` - Résultats détaillés
- `status/{agent}_agent.json` - État agent
- `comms/` - Messages échangés

### Template Handoff Note

```markdown
## Handoff {From} → {To} - {Asset} - {Date}

**From**: {agent_name}
**To**: {agent_name}
**Asset**: {asset}
**Timestamp**: {timestamp}

**Context**:
- Previous status: {status}
- Reason: {reason}

**Actions Taken**:
- {action_1}
- {action_2}

**Results**:
- {result_1}
- {result_2}

**Next Steps**:
- {next_step_1}
- {next_step_2}
```
