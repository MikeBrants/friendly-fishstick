# Workflow Multi-Agent - FINAL TRIGGER v2

## Workflow Standard (Nouvel Asset)

```
1. Data Agent
   └─> Download OHLCV
   └─> Validate data quality
   └─> Write status/data_agent.json

2. Optimization Agent
   └─> Optimize ATR params (100 trials)
   └─> Optimize Ichimoku params (100 trials)
   └─> Walk-forward validation
   └─> Write outputs/multiasset_scan_*.csv
   └─> Write status/optimization_agent.json

3. Validation Agent
   └─> Run 7 guards
   └─> Check all thresholds
   └─> Write outputs/multiasset_guards_summary_*.csv
   └─> Write status/validation_agent.json

4. Analysis Agent
   └─> Diagnose results
   └─> Generate recommendations
   └─> Write outputs/ANALYSIS_*.md
   └─> Write status/analysis_agent.json

5. Production Agent (si validation OK)
   └─> Final validation
   └─> Generate Pine Script
   └─> Update asset_config.py
   └─> Write outputs/pine_plan.csv
   └─> Write status/production_agent.json
```

---

## Workflow Re-Optimisation (Asset FAIL)

```
1. Analysis Agent
   └─> Diagnose failure reasons
   └─> Recommend filter mode (MODERATE/CONSERVATIVE)
   └─> Write comms/reopt_request_{asset}.json

2. Optimization Agent
   └─> Read comms/reopt_request_{asset}.json
   └─> Re-optimize with recommended filter mode
   └─> Write outputs/multiasset_scan_*.csv

3. Validation Agent
   └─> Re-run guards
   └─> Validate improvements

4. Analysis Agent
   └─> Compare before/after
   └─> Update recommendations
```

---

## Workflow Displacement Grid

```
1. Analysis Agent
   └─> Identify borderline assets (WFE 0.3-0.6)
   └─> Write comms/displacement_grid_request.json

2. Optimization Agent
   └─> Grid search [26, 39, 52, 65, 78]
   └─> Write outputs/displacement_grid_*.csv

3. Analysis Agent
   └─> Find best displacement
   └─> Write comms/fullrun_request.json

4. Optimization Agent
   └─> Full run with best displacement
   └─> Write outputs/multiasset_scan_*.csv

5. Validation Agent
   └─> Run guards on winner
```

---

## Workflow Filter Grid (Guard002 Variance)

```
1. Analysis Agent
   └─> Identify high variance assets (ETH, CAKE)
   └─> Write comms/filter_grid_request.json

2. Optimization Agent
   └─> Grid search all filter modes
   └─> Write outputs/filter_grid_results_*.csv

3. Analysis Agent
   └─> Analyze results
   └─> Identify best mode (all guards pass)
   └─> Write comms/final_validation_request.json

4. Optimization Agent
   └─> Final run with best filter mode
   └─> Write outputs/multiasset_scan_*.csv

5. Validation Agent
   └─> Final guards validation
```

---

## Handoff Points

### Data → Optimization
- Trigger: `status/data_agent.json` avec `status: "ready"`
- Input: Fichiers CSV dans `data/`
- Output: `comms/optimization_ready.json`

### Optimization → Validation
- Trigger: `outputs/multiasset_scan_*.csv` créé
- Input: Scan results CSV
- Output: `comms/validation_request.json`

### Validation → Analysis
- Trigger: `outputs/multiasset_guards_summary_*.csv` créé
- Input: Guards summary CSV
- Output: `comms/analysis_request.json`

### Analysis → Production
- Trigger: `status/analysis_agent.json` avec `recommendation: "production"`
- Input: Analysis report
- Output: `comms/production_request.json`

---

## États des Agents

Chaque agent maintient son état dans `status/{agent}_agent.json` :

```json
{
  "agent": "optimization",
  "status": "running" | "completed" | "failed",
  "current_task": "ATR optimization",
  "asset": "ETH",
  "progress": 0.65,
  "started_at": "2026-01-22T18:00:00Z",
  "completed_at": null,
  "error": null
}
```
