# Protocoles de Communication Multi-Agent

## Structure des Messages

Tous les messages entre agents sont des fichiers JSON dans `comms/`.

### Format Standard

```json
{
  "from": "analysis_agent",
  "to": "optimization_agent",
  "type": "request" | "response" | "notification",
  "timestamp": "2026-01-22T18:00:00Z",
  "request_id": "req_20260122_180000",
  "payload": {
    "action": "reoptimize",
    "asset": "ETH",
    "filter_mode": "medium_distance_volume",
    "reason": "guard002 variance 12.96% > 10%"
  }
}
```

---

## Types de Messages

### 1. Optimization Request

**Fichier** : `comms/optimization_request_{asset}_{timestamp}.json`

```json
{
  "from": "analysis_agent",
  "to": "optimization_agent",
  "type": "request",
  "action": "optimize",
  "asset": "ETH",
  "config": {
    "trials_atr": 100,
    "trials_ichi": 100,
    "enforce_tp_progression": true,
    "fixed_displacement": 52,
    "optimization_mode": "baseline"
  }
}
```

### 2. Re-Optimization Request

**Fichier** : `comms/reopt_request_{asset}_{timestamp}.json`

```json
{
  "from": "analysis_agent",
  "to": "optimization_agent",
  "type": "request",
  "action": "reoptimize",
  "asset": "ETH",
  "reason": "guard002 variance 12.96% > 10%",
  "recommendation": {
    "filter_mode": "medium_distance_volume",
    "trials_atr": 100,
    "trials_ichi": 100
  },
  "previous_results": {
    "scan_file": "outputs/multiasset_scan_20260122_1322.csv",
    "guards_file": "outputs/multiasset_guards_summary_20260122_132234.csv"
  }
}
```

### 3. Validation Request

**Fichier** : `comms/validation_request_{asset}_{timestamp}.json`

```json
{
  "from": "optimization_agent",
  "to": "validation_agent",
  "type": "request",
  "action": "run_guards",
  "asset": "ETH",
  "scan_file": "outputs/multiasset_scan_20260122_1322.csv",
  "guards": ["mc", "sensitivity", "bootstrap", "trade_dist", "stress", "regime", "wfe"]
}
```

### 4. Analysis Request

**Fichier** : `comms/analysis_request_{asset}_{timestamp}.json`

```json
{
  "from": "validation_agent",
  "to": "analysis_agent",
  "type": "request",
  "action": "analyze",
  "asset": "ETH",
  "scan_file": "outputs/multiasset_scan_20260122_1322.csv",
  "guards_file": "outputs/multiasset_guards_summary_20260122_132234.csv"
}
```

### 5. Production Request

**Fichier** : `comms/production_request_{asset}_{timestamp}.json`

```json
{
  "from": "analysis_agent",
  "to": "production_agent",
  "type": "request",
  "action": "deploy",
  "asset": "ETH",
  "config": {
    "filter_mode": "medium_distance_volume",
    "params": {
      "sl_mult": 4.5,
      "tp1_mult": 4.75,
      "tp2_mult": 7.0,
      "tp3_mult": 10.0,
      "tenkan": 15,
      "kijun": 20,
      "displacement": 52
    }
  },
  "validation": {
    "all_guards_pass": true,
    "oos_sharpe": 2.09,
    "wfe": 0.82,
    "variance": 3.95
  }
}
```

---

## Réponses

### Format de Réponse

```json
{
  "from": "optimization_agent",
  "to": "analysis_agent",
  "type": "response",
  "request_id": "req_20260122_180000",
  "status": "success" | "failed" | "in_progress",
  "result": {
    "scan_file": "outputs/multiasset_scan_20260122_1322.csv",
    "status": "SUCCESS",
    "oos_sharpe": 2.09,
    "wfe": 0.82
  },
  "error": null
}
```

---

## Notifications

### Format de Notification

```json
{
  "from": "data_agent",
  "to": "all",
  "type": "notification",
  "event": "data_ready",
  "asset": "ETH",
  "message": "Data downloaded and validated",
  "data_file": "data/Binance_ETHUSDT_1h.csv"
}
```

---

## Conventions de Nommage

- Requests: `comms/{action}_request_{asset}_{timestamp}.json`
- Responses: `comms/{action}_response_{asset}_{timestamp}.json`
- Notifications: `comms/{event}_notification_{timestamp}.json`

Exemples:
- `comms/optimization_request_ETH_20260122_180000.json`
- `comms/reopt_request_ETH_20260122_180000.json`
- `comms/validation_request_ETH_20260122_180000.json`
- `comms/data_ready_notification_20260122_180000.json`

---

## Gestion des Erreurs

En cas d'erreur, le message contient :

```json
{
  "status": "failed",
  "error": {
    "code": "INSUFFICIENT_TRADES",
    "message": "OOS trades 45 < 60 minimum",
    "details": {
      "oos_trades": 45,
      "min_required": 60
    }
  }
}
```
