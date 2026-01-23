# 🌙 OVERNIGHT PIPELINE PLAN

**Date:** 24 janvier 2026  
**Mode:** Fully Automated  
**Durée estimée:** 3-6h (selon nombre de SUCCESS)

---

## 📋 Pipeline Complet

### Phase 1: Re-screening (60 assets, ~3h)
**5 batches séquentiels avec `workers=10`**

| Batch | Assets | Durée | Description |
|-------|--------|-------|-------------|
| 1 | 15 | 45 min | BTC, ETH, JOE, OSMO, MINA, AVAX, AR, ANKR, DOGE, OP, DOT, NEAR, SHIB, METIS, YGG |
| 2 | 15 | 45 min | SOL, ADA, XRP, BNB, TRX, LTC, MATIC, ATOM, LINK, UNI, ARB, HBAR, ICP, ALGO, FTM |
| 3 | 10 | 30 min | AAVE, MKR, CRV, SUSHI, RUNE, INJ, TIA, SEI, CAKE, TON |
| 4 | 10 | 30 min | PEPE, ILV, GALA, SAND, MANA, ENJ, FLOKI, WIF, RONIN, AXS |
| 5 | 10 | 30 min | FIL, GRT, THETA, VET, RENDER, EGLD, KAVA, CFX, ROSE, STRK |

**Critères:** WFE > 0.5, Sharpe OOS > 0.8, Trades > 50

### Phase 2: Auto-Validation (SUCCESS assets, ~2-3h)
**Pour chaque asset SUCCESS de Phase 1:**
1. **Run 1** → Optuna 300 trials, `workers=1`, guards
2. **Run 2** → Répéter pour vérifier reproducibilité
3. **Durée par asset:** 10-12 min x 2 = 20-24 min

**Estimation:**
- Si 15 SUCCESS → 15 x 24 min = 6h supplémentaires
- Si 10 SUCCESS → 10 x 24 min = 4h supplémentaires
- Si 5 SUCCESS → 5 x 24 min = 2h supplémentaires

---

## 🚀 Commandes de Lancement

### Option 1: PowerShell (Windows)
```powershell
cd C:\Users\Arthur\friendly-fishstick
.\scripts\run_overnight_reset.ps1
```

### Option 2: Bash (Linux/Mac)
```bash
cd ~/friendly-fishstick
chmod +x scripts/run_overnight_reset.sh
./scripts/run_overnight_reset.sh
```

---

## 📊 Outputs Attendus

### Phase 1 (Re-screening)
```
outputs/multiasset_scan_*_phase1_reset_batch1_prod.csv
outputs/multiasset_scan_*_phase1_reset_batch2_highcap.csv
outputs/multiasset_scan_*_phase1_reset_batch3_defi.csv
outputs/multiasset_scan_*_phase1_reset_batch4_gaming.csv
outputs/multiasset_scan_*_phase1_reset_batch5_infra.csv
```

**Contenu:** Asset, STATUS (SUCCESS/FAIL), Sharpe OOS, WFE, Trades, etc.

### Phase 2 (Validation)
```
outputs/*_phase2_validation_[ASSET]_run1*.csv
outputs/*_phase2_validation_[ASSET]_run2*.csv
outputs/*_phase2_validation_[ASSET]_run1_guards_summary*.csv
outputs/*_phase2_validation_[ASSET]_run2_guards_summary*.csv
```

**Contenu:** Params optimaux, guards results, reproducibility check

### Log Global
```
outputs/overnight_log_[timestamp].txt
```

**Contenu:** Timeline complète, status de chaque batch, erreurs, résumé final

---

## 📈 Résultats Attendus

### Phase 1 (Screening)
| Métrique | Estimation |
|----------|-----------|
| Assets testés | 60 |
| SUCCESS attendus | 15-20 (~25-30%) |
| FAIL attendus | 40-45 (~70-75%) |

**Distribution probable:**
- Batch 1 (anciens PROD): 10-12 SUCCESS
- Batch 2 (High Cap): 3-5 SUCCESS
- Batch 3-5 (DeFi/Gaming/Infra): 2-3 SUCCESS

### Phase 2 (Validation)
| Métrique | Estimation |
|----------|-----------|
| Assets validés | 15-20 (Run 1 + Run 2) |
| Reproducibilité 100% | 15-20 (tous) |
| Guards 7/7 PASS | 10-15 (~65-75%) |
| **PROD FINAL** | **10-15 assets** |

---

## ⚙️ Configuration Auto

### Script Features
✅ **Auto-retry:** Continue même si un asset fail  
✅ **Logging:** Tout est tracé dans `overnight_log_*.txt`  
✅ **Auto-validation:** Lance Phase 2 pour SUCCESS automatiquement  
✅ **Reproducibility:** Run 1 + Run 2 pour chaque SUCCESS  
✅ **Guards:** Exécute tous les guards automatiquement  
✅ **Summary:** Rapport final avec metrics agrégées

### Parameters
- **Phase 1:** `workers=10`, 200 trials ATR, 200 trials Ichimoku
- **Phase 2:** `workers=1`, 300 trials ATR, 300 trials Ichimoku, guards ON
- **TP Progression:** Enforced par défaut (`--enforce-tp-progression`)

---

## 🔍 Monitoring Overnight

### Vérifier Progression (depuis un autre terminal)
```powershell
# Dernière ligne du log
Get-Content outputs\overnight_log_*.txt -Tail 1

# Nombre de fichiers générés
Get-ChildItem outputs\ -Filter "*phase1_reset*.csv" | Measure-Object

# Taille des fichiers (estimation progression)
Get-ChildItem outputs\ -Filter "*.csv" | Where-Object { $_.LastWriteTime -gt (Get-Date).AddHours(-1) } | Select-Object Name, Length, LastWriteTime
```

### Logs en Temps Réel
```powershell
Get-Content outputs\overnight_log_*.txt -Wait
```

---

## 📋 Checklist Pré-Lancement

### ✅ Vérifications
- [ ] Optuna fix vérifié (deterministic seeds)
- [ ] Guards config OK (mc=1000, bootstrap=10000)
- [ ] TP progression enforced
- [ ] Données Parquet disponibles (si besoin, download d'abord)
- [ ] Espace disque suffisant (~5GB pour outputs)
- [ ] Python venv activé
- [ ] Internet stable (si download data requis)

### 📊 Données Requises
**Vérifier quels assets ont déjà des données:**
```powershell
Get-ChildItem data\parquet\binance\ -Filter "*.parquet" | Select-Object Name
```

**Si données manquantes, download d'abord:**
```bash
python scripts/download_data.py --assets BTC ETH SOL ADA [...]
```

---

## 🌅 Workflow Post-Overnight

### Matin: Analyser les Résultats

**1. Lire le log:**
```powershell
Get-Content outputs\overnight_log_*.txt
```

**2. Identifier SUCCESS Phase 1:**
```powershell
Get-Content outputs\*phase1_reset*.csv | Select-String "SUCCESS"
```

**3. Vérifier Reproducibilité Phase 2:**
```bash
python scripts/verify_reproducibility.py --assets [SUCCESS_ASSETS]
```

**4. Analyser Guards:**
```powershell
Get-Content outputs\*_guards_summary*.csv | Select-String "PASS"
```

**5. Compter les PROD finaux:**
```bash
# Assets avec Run 1 = Run 2 ET 7/7 guards PASS
```

---

## 🎯 Objectif Final

**Attendu au réveil:**
- ✅ Phase 1 complète: 60 assets testés, 15-20 SUCCESS
- ✅ Phase 2 complète: 15-20 assets validés (Run 1 + Run 2)
- ✅ Reproducibilité vérifiée: 100% match
- ✅ Guards analysés: 10-15 PASS (7/7)
- ✅ **PROD prêts:** 10-15 assets validés avec système reproductible

**Next:**
- Mettre à jour `status/project-state.md`
- Mettre à jour `crypto_backtest/config/asset_config.py`
- Commit + Push résultats
- Analyser corrélations portfolio

---

## ⚠️ Troubleshooting

### Si Pipeline Interrompu
```powershell
# Trouver le dernier batch complété
Get-Content outputs\overnight_log_*.txt | Select-String "COMPLETE"

# Relancer à partir du batch suivant
python scripts/run_full_pipeline.py --assets [REMAINING_ASSETS] ...
```

### Si Mémoire Insuffisante
- Réduire `workers` de 10 à 6
- Lancer les batches manuellement un par un

### Si Download Data Fail
- Vérifier connexion Internet
- Vérifier API rate limits (Binance, etc.)
- Re-lancer download pour assets manquants

---

## 📁 Fichiers Créés

| Fichier | Description |
|---------|-------------|
| `scripts/run_overnight_reset.ps1` | Script PowerShell (Windows) |
| `scripts/run_overnight_reset.sh` | Script Bash (Linux/Mac) |
| `OVERNIGHT_PLAN.md` | Ce fichier (plan détaillé) |

**Push:** Prêt à commit + push

---

## 🚀 READY TO LAUNCH

```powershell
# Windows
cd C:\Users\Arthur\friendly-fishstick
.\scripts\run_overnight_reset.ps1

# Puis aller dormir 😴
# Réveil → Analyser outputs/overnight_log_*.txt
```

**Durée totale estimée:** 5-9h (3h Phase 1 + 2-6h Phase 2 selon SUCCESS)  
**ETA finish:** Demain matin 08h-12h (si lancement 23h)

Bonne nuit ! 🌙
