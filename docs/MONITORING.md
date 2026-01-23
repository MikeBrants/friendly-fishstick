# 🔍 Process Monitoring

Système de monitoring pour surveiller les scripts Python en cours d'exécution et leur utilisation des ressources.

## Options

### Option 1: Dashboard Streamlit (Recommandé)

Intégré directement dans le dashboard principal:

```bash
streamlit run app.py
```

Puis cliquez sur **"🔍 Monitor Processes"** dans la sidebar (section "🔧 Système").

**Fonctionnalités:**
- ✅ Auto-refresh configurable (2s, 5s, 10s)
- ✅ Vue système (CPU, RAM, Disk)
- ✅ Liste des processus Python avec détails
- ✅ Code couleur par utilisation CPU/Memory
- ✅ Commande complète pour chaque processus

### Option 2: Script Standalone (Terminal)

Pour un monitoring en ligne de commande:

```bash
# Monitoring continu (rafraîchit toutes les 2 secondes)
python scripts/monitor_processes.py

# Avec intervalle personnalisé
python scripts/monitor_processes.py --interval 5

# Sauvegarder dans un fichier JSON
python scripts/monitor_processes.py --output monitor.json
```

**Exemple de sortie:**
```
📊 System Monitor - 2026-01-23 10:30:45
================================================================================

💻 System Resources:
  CPU: 45.2% (8 cores)
  RAM: 12.3GB / 16.0GB (76.8%)
  Disk: 250.5GB / 500.0GB (50.1%)

🐍 Python Processes (3):
--------------------------------------------------------------------------------
PID      Script                     CPU%     Memory (MB)  Runtime      Status    
--------------------------------------------------------------------------------
12345    run_full_pipeline.py       25.3     512.5        1h 23m       running   
12346    optimize_final_trigger.py  15.7     256.2        45m          running   
12347    run_guards_multiasset.py   8.2      128.1        12m          running   
```

## Outils Alternatifs (si besoin)

### Glances (Recommandé pour monitoring système complet)

```bash
# Installation
pip install glances

# Lancer
glances
```

**Avantages:**
- Monitoring système complet (CPU, RAM, Disk, Network, GPU)
- Interface TUI interactive
- Support multi-plateforme

### htop (Linux/Mac)

```bash
# Installation (Ubuntu/Debian)
sudo apt install htop

# Lancer
htop
```

**Note:** Windows nécessite WSL ou un port alternatif.

### Task Manager (Windows natif)

Sur Windows, le Gestionnaire des tâches (`Ctrl+Shift+Esc`) offre déjà un bon monitoring.

## Ce qui est monitoré

### Processus Python détectés
- ✅ Scripts `.py` en cours d'exécution
- ✅ PID, nom du script, commande complète
- ✅ CPU % (utilisation par processus)
- ✅ Memory (MB) - RAM utilisée
- ✅ Runtime - durée d'exécution
- ✅ Status - running, sleeping, etc.

### Exclusions automatiques
- ❌ Le script de monitoring lui-même
- ❌ Streamlit (pour éviter les boucles)
- ❌ Autres processus système Python

## Cas d'usage

### 1. Vérifier qu'un script tourne toujours

```bash
python scripts/monitor_processes.py | grep "run_full_pipeline"
```

### 2. Identifier les scripts gourmands en CPU

Le dashboard Streamlit colore automatiquement:
- 🔴 Rouge: CPU > 50%
- 🟡 Jaune: CPU > 20%
- 🟢 Vert: CPU < 20%

### 3. Surveiller la mémoire

Utile pour détecter les fuites mémoire ou les scripts qui consomment trop de RAM.

### 4. Vérifier le runtime

Pour savoir depuis combien de temps un script tourne (utile pour les optimisations longues).

## Dépannage

### "Aucun processus Python détecté"

- Vérifiez que des scripts Python sont bien en cours d'exécution
- Le monitor exclut automatiquement streamlit et lui-même

### "psutil not found"

```bash
pip install psutil
```

### Performance du dashboard

Si le dashboard Streamlit devient lent avec l'auto-refresh:
- Désactivez l'auto-refresh
- Augmentez l'intervalle (5s ou 10s)
- Utilisez le script standalone à la place

## Notes Techniques

- Le monitoring utilise `psutil` pour accéder aux informations système
- Sur Windows, certains processus peuvent nécessiter des droits administrateur
- Le CPU % est calculé sur un intervalle court (0.1s) pour éviter la latence
