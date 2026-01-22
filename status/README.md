# Status Multi-Agent

Ce dossier contient l'état actuel de chaque agent du système multi-agent.

## Fichiers de Statut

- `data_agent.json` - État de l'agent de données
- `optimization_agent.json` - État de l'agent d'optimisation
- `validation_agent.json` - État de l'agent de validation
- `analysis_agent.json` - État de l'agent d'analyse
- `production_agent.json` - État de l'agent de production

## Format Standard

```json
{
  "agent": "optimization",
  "status": "running" | "completed" | "failed" | "idle",
  "current_task": "ATR optimization for ETH",
  "asset": "ETH",
  "progress": 0.65,
  "started_at": "2026-01-22T18:00:00Z",
  "completed_at": null,
  "last_update": "2026-01-22T18:30:00Z",
  "outputs": {
    "scan_file": "outputs/multiasset_scan_20260122_1322.csv"
  },
  "error": null
}
```

## Mise à Jour

Chaque agent met à jour son fichier de statut :
- Au démarrage d'une tâche
- Pendant l'exécution (progress)
- À la fin (completed/failed)

## Consultation

Pour connaître l'état du système :
```bash
Get-Content status/*.json | ConvertFrom-Json
```
