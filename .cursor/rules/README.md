# Multi-Agent Rules

Ce dossier contient les règles de coordination pour le système multi-agent du projet FINAL TRIGGER v2.

## Structure

- `agent-roles.md` - Définition des rôles et responsabilités de chaque agent
- `workflow.md` - Workflow de coordination entre agents
- `communication.md` - Protocoles de communication
- `handoff.md` - Procédures de handoff entre agents

## Agents

1. **Data Agent** - Gestion des données (download, preprocessing)
2. **Optimization Agent** - Optimisation des paramètres (ATR, Ichimoku, displacement)
3. **Validation Agent** - Validation et guards (Monte Carlo, sensitivity, bootstrap)
4. **Analysis Agent** - Analyse des résultats et diagnostics
5. **Production Agent** - Déploiement et monitoring en production
