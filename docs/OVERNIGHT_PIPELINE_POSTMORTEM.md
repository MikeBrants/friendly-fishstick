# Overnight Pipeline Post-Mortem

**Date:** 2026-01-24  
**Pipeline:** run_overnight_reset.ps1  
**Issue:** Doublons en Phase 2 (chaque asset validé 2×)

---

## 🔍 Analyse du Problème

### **Cause Root:**

Le script `run_full_pipeline.py` génère **2 fichiers CSV identiques** par run:

```
outputs/
├── phase1_reset_batch1_prod_multiasset_scan_20260124_034427.csv     (4598 bytes)
└── phase1_reset_batch1_prod_multi_asset_scan_20260124_034427.csv   (4598 bytes)
                                        ^^^^ underscore ajouté
```

Ces deux fichiers contiennent **exactement les mêmes données** (confirmé: taille identique, contenu identique).

### **Propagation du Bug:**

Le script PowerShell `run_overnight_reset.ps1` (ligne 167) lit **tous** les fichiers:

```powershell
$scan_files = Get-ChildItem -Path "outputs" -Filter "*phase1_reset*.csv" | 
    Where-Object { $_.LastWriteTime -gt (Get-Date).AddHours(-4) }
```

**Sans déduplication** (ligne 173-180):

```powershell
$success_assets = @()
foreach ($file in $scan_files) {
    foreach ($line in $content) {
        if ($line -match "^([A-Z]+),SUCCESS") {
            $success_assets += $matches[1]  # ❌ Pas de dédoublonnage
        }
    }
}
```

**Résultat:**
- 7 assets SUCCESS dans Batch 1 → lus dans 2 fichiers → **14 entrées** dans `$success_assets`
- Phase 2 valide ces 14 entrées → chaque asset validé **2 fois** (Run 1 + Run 2 × 2)

---

## 📊 Impact

### **Positif (Inattendu):**

✅ **Données de reproducibilité enrichies:**
- Au lieu de 2 runs (Run 1 + Run 2), nous avons **4 runs** par asset
- **Confiance statistique accrue** sur la stabilité des paramètres
- Peut détecter des variations subtiles (si Run 1a ≠ Run 1b)

✅ **Détection précoce de non-déterminisme:**
- Si les 2 premières exécutions donnent des résultats différents → bug immédiat

### **Négatif:**

❌ **Temps d'exécution doublé:**
- Phase 2 attendue: ~3h (15 assets × 2 runs × 6 min)
- Phase 2 réelle: **~6h** (30 validations au lieu de 15)
- Pipeline total: 12h30 au lieu de 6h

❌ **Ressources CPU gaspillées:**
- 2× plus de trials Optuna (~600 trials par asset au lieu de 300)
- Coût cloud/électricité (si applicable)

❌ **Log pollué:**
- Doublons dans les SUCCESS (voir ligne 104-140 du log: ETH, JOE, ANKR, etc. × 2)
- Difficile de distinguer les runs légitimes

---

## ✅ Solutions Implémentées

### **1. Script Corrigé: `run_overnight_reset_fixed.ps1`**

**Changements:**

1. **Filtrage des fichiers** (ligne 165):
```powershell
# AVANT
$scan_files = Get-ChildItem -Path "outputs" -Filter "*phase1_reset*.csv"

# APRÈS
$scan_files = Get-ChildItem -Path "outputs" -Filter "*phase1_reset*multiasset_scan*.csv" | 
    Where-Object { $_.Name -notmatch "multi_asset_scan" }
```

2. **Déduplication explicite** (ligne 186):
```powershell
# Ajouté après la boucle de parsing
$success_assets = $success_assets | Select-Object -Unique
```

### **2. Fix Permanent dans `run_full_pipeline.py`**

**Recommandation:** Modifier le script Python pour ne générer qu'**un seul fichier CSV**.

**Localisation du bug:** `crypto_backtest/optimization/parallel_optimizer.py`, ligne ~1180:

```python
# Probablement quelque chose comme:
output_file_1 = f"multiasset_scan_{timestamp}.csv"
output_file_2 = f"multi_asset_scan_{timestamp}.csv"  # ❌ Doublon inutile
```

**Action:** Supprimer la génération du deuxième fichier.

---

## 📈 Résultats du Pipeline Overnight

### **Phase 1: Re-Screening (04:40 complété)**

| Batch | Assets | SUCCESS | FAIL | Taux |
|:------|:-------|:--------|:-----|:-----|
| 1. Anciens PROD | 15 | 7 | 8 | 47% |
| 2. High Cap | 15 | 1 | 14 | 7% |
| 3. DeFi + L2 | 10 | 6 | 4 | 60% |
| 4. Gaming | 10 | 0 | 10 | 0% |
| 5. Infra | 10 | 1 | 9 | 10% |
| **TOTAL** | **60** | **15** | **45** | **25%** |

**Assets SUCCESS (dédupliqués):**
- ETH, JOE, ANKR, DOGE, DOT, NEAR, SHIB (Batch 1)
- HBAR (Batch 2)
- CRV, SUSHI, RUNE, TIA, CAKE, TON (Batch 3)
- EGLD (Batch 5)

### **Phase 2: Validation (93% complété à 15:52)**

**Validations complétées:** 14/15 assets
- 28 runs au lieu de 14 (doublons)
- TIA Run 2 en cours
- EGLD en attente

---

## 🎯 Actions Recommandées

### **Immédiat:**

1. **Laisser finir le pipeline actuel** (~30 min restant)
   - TIA Run 2 + EGLD Run 1 + Run 2

2. **Analyser reproducibilité** avec les doublons:
   ```bash
   # Comparer les 4 runs pour chaque asset
   python scripts/compare_reproducibility_extended.py --phase2-results
   ```

3. **Validation guards (@Sam):**
   - Vérifier 7/7 guards PASS pour les 15 assets
   - Confirmer reproducibilité sur les 4 runs (variance < 1%)

### **Futur:**

4. **Utiliser le script corrigé:**
   ```powershell
   # Au lieu de:
   .\scripts\run_overnight_reset.ps1
   
   # Utiliser:
   .\scripts\run_overnight_reset_fixed.ps1
   ```

5. **Fix permanent dans Python:**
   - Investiguer `parallel_optimizer.py` pour éliminer le doublon de fichier
   - PR + tests unitaires

6. **Monitoring amélioré:**
   - Ajouter un check de déduplication dans le script PowerShell
   - Alerte si `$success_assets.Count ≠ ($success_assets | Select-Object -Unique).Count`

---

## 📝 Lessons Learned

1. **Toujours dédupliquer les listes** en shell scripting
2. **Un seul fichier output par run** (principe KISS)
3. **Les bugs peuvent avoir des side-effects positifs** (4 runs = meilleure confiance)
4. **Valider les assumptions** (pourquoi 2 fichiers CSV identiques ?)

---

## ✅ Verdict

**Impact global:** Mineur ⚠️
- Pipeline fonctionnel malgré le bug
- Temps doublé mais données enrichies
- Fix trivial pour les prochains runs

**Priorité fix:** **P2** (non-bloquant, mais à corriger)

---

**Auteur:** Jordan (Agent Dev)  
**Reviewer:** Casey (Quant Lead)  
**Status:** DOCUMENTÉ, FIX READY
