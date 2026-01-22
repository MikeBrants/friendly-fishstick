# Communication Multi-Agent

Ce dossier contient tous les messages échangés entre les agents du système multi-agent.

## Structure

Les messages sont organisés par type :
- `*_request_*.json` - Requêtes entre agents
- `*_response_*.json` - Réponses aux requêtes
- `*_notification_*.json` - Notifications d'événements

## Conventions

- Format: JSON
- Nommage: `{action}_{type}_{asset}_{timestamp}.json`
- Timestamp: Format ISO 8601 (YYYYMMDD_HHMMSS)

## Exemples

- `optimization_request_ETH_20260122_180000.json`
- `validation_response_ETH_20260122_180500.json`
- `data_ready_notification_20260122_170000.json`

## Nettoyage

Les messages anciens (> 7 jours) peuvent être archivés ou supprimés pour éviter l'encombrement.
