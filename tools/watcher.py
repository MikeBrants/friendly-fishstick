"""
WATCHER Multi-Agent v3.2 — FINAL TRIGGER v2
Track par hash + Auto-fix + Auto-download

Fixes v3.2:
- Hash des tâches pour éviter les doublons (persiste entre redémarrages)
- Ignore timestamp de Casey, utilise l'heure de détection
- Auto-fix syntaxe virgules → espaces
- Auto-download données manquantes
- Skip assets EXCLU

Usage:
    python tools/watcher.py
"""

import time
import re
import subprocess
import sys
import hashlib
from pathlib import Path
from datetime import datetime

# === CONFIG ===
ROOT = Path(__file__).parent.parent
COMMS = ROOT / "comms"
STATUS = ROOT / "status"
DATA = ROOT / "data"
TOOLS = ROOT / "tools"

CASEY_FILE = COMMS / "casey-quant.md"
JORDAN_FILE = COMMS / "jordan-dev.md"
SAM_FILE = COMMS / "sam-qa.md"
PROJECT_STATE = STATUS / "project-state.md"
SEEN_TASKS_FILE = TOOLS / ".watcher_seen_tasks.txt"

POLL_INTERVAL = 30
PYTHON_EXE = sys.executable
DOWNLOAD_SCRIPT = ROOT / "scripts" / "download_data.py"


# === UTILS ===
def now():
    return datetime.now().strftime("%H:%M")


def today():
    return datetime.now().strftime("%Y-%m-%d")


def file_hash(path):
    if not path.exists():
        return None
    return hashlib.md5(path.read_bytes()).hexdigest()


def append_to_file(path, content):
    if not path.exists():
        path.write_text(f"# {path.stem}\n\n## Historique\n\n", encoding="utf-8")
    
    text = path.read_text(encoding="utf-8")
    marker = "## Historique"
    if marker in text:
        parts = text.split(marker, 1)
        insert_point = parts[1].find("\n\n")
        if insert_point == -1:
            insert_point = len(parts[1])
        new_text = parts[0] + marker + parts[1][:insert_point] + "\n\n" + content + parts[1][insert_point:]
        path.write_text(new_text, encoding="utf-8")
    else:
        with open(path, "a", encoding="utf-8") as f:
            f.write("\n\n" + content)


# === HASH SYSTEM (NOUVEAU v3.2) ===

def get_task_hash(task_body):
    """Génère un hash unique pour une tâche basé sur son contenu."""
    return hashlib.md5(task_body.strip().encode()).hexdigest()[:16]


def get_seen_task_hashes():
    """Charge les hashes des tâches déjà vues."""
    if not SEEN_TASKS_FILE.exists():
        return set()
    
    content = SEEN_TASKS_FILE.read_text(encoding="utf-8")
    return set(line.strip() for line in content.splitlines() if line.strip())


def mark_task_as_seen(task_hash):
    """Marque une tâche comme vue."""
    with open(SEEN_TASKS_FILE, "a", encoding="utf-8") as f:
        f.write(f"{task_hash}\n")


def clear_old_hashes(max_entries=500):
    """Nettoie le fichier si trop d'entrées (garde les 500 dernières)."""
    if not SEEN_TASKS_FILE.exists():
        return
    
    lines = SEEN_TASKS_FILE.read_text(encoding="utf-8").splitlines()
    if len(lines) > max_entries:
        # Garde les plus récentes
        SEEN_TASKS_FILE.write_text("\n".join(lines[-max_entries:]) + "\n", encoding="utf-8")
        print(f"[{now()}] [WATCHER] Cleaned hash file ({len(lines)} → {max_entries})")


# === AUTO-FIX COMMANDES ===

def fix_command_syntax(command):
    """Corrige les problèmes de syntaxe courants."""
    command = command.replace("\\\n", " ").replace("  ", " ").strip()
    
    def fix_assets(match):
        flag = match.group(1)
        assets_str = match.group(2)
        assets_fixed = assets_str.replace(",", " ")
        return f"{flag} {assets_fixed}"
    
    command = re.sub(r'(--assets?)\s+([A-Z,]+)', fix_assets, command)
    command = re.sub(r'\s+', ' ', command).strip()
    
    return command


def extract_assets_from_command(command):
    """Extrait la liste des assets depuis une commande."""
    match = re.search(r'--assets?\s+([A-Z\s,]+?)(?:\s+--|$)', command)
    if match:
        assets_str = match.group(1)
        assets = re.findall(r'[A-Z]{2,10}', assets_str)
        return assets
    return []


# === AUTO-DOWNLOAD DONNÉES ===

def check_data_exists(asset):
    """Vérifie si les données existent pour un asset."""
    patterns = [
        DATA / f"{asset}USDT_1h.parquet",
        DATA / f"{asset}_USDT_1h.parquet",
        DATA / f"Binance_{asset}_1h.parquet",
        DATA / f"{asset.lower()}usdt_1h.parquet",
    ]
    
    for pattern in patterns:
        if pattern.exists():
            return True
    
    if DATA.exists():
        for f in DATA.glob(f"*{asset}*"):
            if f.suffix in ['.parquet', '.csv']:
                return True
    
    return False


def download_missing_data(assets):
    """Télécharge les données manquantes."""
    missing = [a for a in assets if not check_data_exists(a)]
    
    if not missing:
        return True, [], []
    
    print(f"[{now()}] [@Jordan via WATCHER] 📥 Downloading: {', '.join(missing)}")
    
    if not DOWNLOAD_SCRIPT.exists():
        print(f"[{now()}] [@Jordan via WATCHER] ⚠️ download_data.py not found")
        return False, [], missing
    
    try:
        cmd = [PYTHON_EXE, str(DOWNLOAD_SCRIPT), "--assets"] + missing
        
        result = subprocess.run(
            cmd,
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            timeout=300
        )
        
        downloaded = [a for a in missing if check_data_exists(a)]
        failed = [a for a in missing if not check_data_exists(a)]
        
        if downloaded:
            print(f"[{now()}] [@Jordan via WATCHER] ✅ Downloaded: {', '.join(downloaded)}")
        if failed:
            print(f"[{now()}] [@Jordan via WATCHER] ❌ Failed: {', '.join(failed)}")
        
        return len(failed) == 0, downloaded, failed
        
    except subprocess.TimeoutExpired:
        print(f"[{now()}] [@Jordan via WATCHER] ⏱️ Download timeout")
        return False, [], missing
    except Exception as e:
        print(f"[{now()}] [@Jordan via WATCHER] ❌ Download error: {e}")
        return False, [], missing


# === PROTECTIONS ===

def get_excluded_assets():
    """Lit project-state.md et retourne les assets EXCLU."""
    if not PROJECT_STATE.exists():
        return set()
    
    content = PROJECT_STATE.read_text(encoding="utf-8")
    exclus_match = re.search(r"## EXCLUS.*?\n\n(.*?)(?=\n##|\n\*\*\*|$)", content, re.DOTALL)
    if not exclus_match:
        return set()
    
    assets = re.findall(r'\b([A-Z]{2,10})\b', exclus_match.group(1))
    return set(assets)


def should_skip_asset(asset, excluded_assets):
    """Vérifie si un asset doit être skippé."""
    if asset in excluded_assets:
        return True, f"Asset {asset} est EXCLU"
    return False, ""


def write_skip_log(task, reason):
    content = f"""## [{now()}] [SKIP] @Jordan

**Task ref:** [{task.get('original_timestamp', '??:??')}] Casey TASK
**Asset:** {task['asset']}
**Mode:** {task.get('mode', 'baseline')}
**Displacement:** {task.get('displacement', 'auto')}
**Raison:** ⏭️ {reason}

---
"""
    append_to_file(JORDAN_FILE, content)
    print(f"[{now()}] [@Jordan via WATCHER] ⏭️ SKIP {task['asset']}: {reason}")


# === PARSERS ===

def extract_pending_tasks(casey_content, seen_hashes, excluded_assets):
    """
    Extrait les [TASK] non encore vues de casey-quant.md.
    Utilise le hash pour détecter les doublons.
    """
    task_pattern = r"## \[(\d{2}:\d{2})\] \[TASK\] @Casey -> @Jordan\n(.*?)(?=\n## \[|$)"
    tasks = re.findall(task_pattern, casey_content, re.DOTALL)
    
    parsed = []
    skipped_seen = 0
    
    for original_timestamp, body in tasks:
        # Hash basé sur le contenu
        task_hash = get_task_hash(body)
        
        # Skip silencieux si déjà vu
        if task_hash in seen_hashes:
            skipped_seen += 1
            continue
        
        cmd_match = re.search(r"```bash\n(.*?)\n```", body, re.DOTALL)
        if not cmd_match:
            continue
        
        raw_command = cmd_match.group(1).strip()
        fixed_command = fix_command_syntax(raw_command)
        
        # Extrait assets
        assets_list = extract_assets_from_command(fixed_command)
        
        if assets_list:
            asset = assets_list[0]
            all_assets = assets_list
        else:
            asset_match = re.search(r"\*\*Asset[s]?:\*\* (.+)", body)
            if asset_match:
                asset = asset_match.group(1).split(",")[0].strip()
                all_assets = [a.strip() for a in asset_match.group(1).split(",")]
            else:
                asset = "UNKNOWN"
                all_assets = []
        
        # Mode
        mode_match = re.search(r"\*\*(?:Mode|Variant):\*\* (.+)", body)
        if mode_match:
            mode = mode_match.group(1).strip()
        else:
            cmd_mode_match = re.search(r"--optimization-mode\s+(\w+)", fixed_command)
            mode = cmd_mode_match.group(1) if cmd_mode_match else "baseline"
        
        # Displacement
        disp_match = re.search(r"--fixed-displacement\s+(\d+)", fixed_command)
        displacement = disp_match.group(1) if disp_match else "auto"
        
        parsed.append({
            "timestamp": now(),  # Heure de détection (pas Casey)
            "original_timestamp": original_timestamp,
            "task_hash": task_hash,
            "asset": asset,
            "all_assets": all_assets,
            "command": fixed_command,
            "raw_command": raw_command,
            "mode": mode,
            "displacement": displacement,
            "raw_body": body
        })
    
    if skipped_seen > 0:
        print(f"[{now()}] [WATCHER] Ignored {skipped_seen} already-seen task(s)")
    
    return parsed


# === ACTIONS ===

def run_command(task):
    """Exécute la commande corrigée."""
    command = task["command"]
    cmd_parts = command.split()
    
    print(f"[@Jordan via WATCHER] Executing: {' '.join(cmd_parts[:8])}...")
    
    start_time = time.time()
    try:
        result = subprocess.run(
            cmd_parts,
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            timeout=3600
        )
        duration = int((time.time() - start_time) / 60)
        success = result.returncode == 0
        output = result.stdout if success else result.stderr
        return success, output, duration
    except subprocess.TimeoutExpired:
        return False, "TIMEOUT after 1 hour", 60
    except Exception as e:
        return False, str(e), 0


def write_jordan_run_start(task, command_was_fixed=False, data_was_downloaded=False):
    fixes_applied = []
    if command_was_fixed:
        fixes_applied.append("Syntaxe commande corrigée")
    if data_was_downloaded:
        fixes_applied.append(f"Données téléchargées: {', '.join(task.get('downloaded_assets', []))}")
    
    fixes_section = ""
    if fixes_applied:
        fixes_section = f"\n**Auto-fixes:** " + " | ".join(fixes_applied)
    
    content = f"""## [{now()}] [RUN_START] @Jordan -> @Sam

**Task ref:** [{task['original_timestamp']}] Casey TASK
**Asset:** {task['asset']}
**All assets:** {', '.join(task.get('all_assets', [task['asset']]))}
**Mode:** {task['mode']}
**Displacement:** {task['displacement']}
**Command:**
```bash
{task['command']}
```
**Status:** 🟢 Running{fixes_section}

---
"""
    append_to_file(JORDAN_FILE, content)
    print(f"[@Jordan via WATCHER] Written RUN_START for {task['asset']}")


def write_jordan_run_complete(task, success, output, duration):
    status = "RUN_COMPLETE" if success else "RUN_FAILED"
    emoji = "✅" if success else "❌"
    
    sharpe_match = re.search(r"OOS Sharpe[:\s]+([0-9.-]+)", output)
    wfe_match = re.search(r"WFE[:\s]+([0-9.-]+)", output)
    
    metrics = ""
    if sharpe_match or wfe_match:
        metrics = f"\n**Résultats:** Sharpe={sharpe_match.group(1) if sharpe_match else 'N/A'}, WFE={wfe_match.group(1) if wfe_match else 'N/A'}"
    
    error_section = ""
    if not success and output:
        error_lines = output.strip().split('\n')[:5]
        error_section = f"\n**Erreur:**\n```\n{chr(10).join(error_lines)}\n```"
    
    content = f"""## [{now()}] [{status}] @Jordan -> @Sam

**Asset:** {task['asset']}
**Mode:** {task['mode']}
**Displacement:** {task['displacement']}
**Status:** {emoji} {'Complete' if success else 'Failed'}
**Duration:** {duration} min{metrics}{error_section}

---
"""
    append_to_file(JORDAN_FILE, content)
    print(f"[@Jordan via WATCHER] Written {status} for {task['asset']}")


def notify_casey(task, success, output, duration):
    status = "✅ Complete" if success else "❌ Failed"
    
    sharpe_match = re.search(r"OOS Sharpe[:\s]+([0-9.-]+)", output)
    wfe_match = re.search(r"WFE[:\s]+([0-9.-]+)", output)
    
    content = f"""## [{now()}] [UPDATE] @Jordan -> @Casey

**Task:** [{task['original_timestamp']}] {task['asset']} {task['mode']}
**Status:** {status}
**Duration:** {duration} min
**Sharpe:** {sharpe_match.group(1) if sharpe_match else 'N/A'}
**WFE:** {wfe_match.group(1) if wfe_match else 'N/A'}

---
"""
    append_to_file(CASEY_FILE, content)


def trigger_sam_validation(task):
    validator_path = ROOT / "tools" / "sam_auto_validator.py"
    if validator_path.exists():
        print(f"[WATCHER] Triggering Sam auto-validator...")
        try:
            subprocess.run(
                [PYTHON_EXE, str(validator_path), "--batch"],
                cwd=str(ROOT),
                capture_output=True,
                text=True,
                timeout=60
            )
            print(f"[@Jordan via WATCHER] ✅ Sam validation done")
        except Exception as e:
            print(f"[@Jordan via WATCHER] ⚠️ Sam error: {e}")


# === MAIN LOOP ===

def main():
    print(f"""
╔═══════════════════════════════════════════════════════════╗
║  WATCHER Multi-Agent v3.2 — FINAL TRIGGER v2              ║
║  Automatisation de @Jordan                                ║
║                                                           ║
║  Surveille: {CASEY_FILE.name:<43} ║
║  Poll: {POLL_INTERVAL}s                                                ║
║                                                           ║
║  Features:                                                ║
║  ✓ Hash tracking (ignore doublons, persiste)              ║
║  ✓ Auto-fix syntaxe (virgules → espaces)                  ║
║  ✓ Auto-download données manquantes                       ║
║  ✓ Skip assets EXCLU                                      ║
║                                                           ║
║  Ctrl+C pour arrêter                                      ║
╚═══════════════════════════════════════════════════════════╝
""")
    
    # Nettoie les vieux hashes au démarrage
    clear_old_hashes(max_entries=500)
    
    last_casey_hash = None
    excluded_assets = get_excluded_assets()
    print(f"[{now()}] [WATCHER] Loaded {len(excluded_assets)} excluded assets")
    
    seen_hashes = get_seen_task_hashes()
    print(f"[{now()}] [WATCHER] Loaded {len(seen_hashes)} seen task hashes")
    
    while True:
        try:
            current_hash = file_hash(CASEY_FILE)
            
            if current_hash != last_casey_hash:
                print(f"[{now()}] [WATCHER] Casey file changed, scanning...")
                last_casey_hash = current_hash
                
                # Refresh
                excluded_assets = get_excluded_assets()
                seen_hashes = get_seen_task_hashes()
                
                if not CASEY_FILE.exists():
                    time.sleep(POLL_INTERVAL)
                    continue
                
                casey_content = CASEY_FILE.read_text(encoding="utf-8")
                
                # Extract tasks (filtre déjà les vus par hash)
                pending_tasks = extract_pending_tasks(casey_content, seen_hashes, excluded_assets)
                
                if not pending_tasks:
                    print(f"[{now()}] [WATCHER] No new tasks")
                    time.sleep(POLL_INTERVAL)
                    continue
                
                print(f"[{now()}] [WATCHER] Found {len(pending_tasks)} new task(s)")
                
                for task in pending_tasks:
                    # Marque comme vu IMMÉDIATEMENT (même si skip/fail)
                    mark_task_as_seen(task["task_hash"])
                    seen_hashes.add(task["task_hash"])
                    
                    # Check si asset exclu
                    skip, reason = should_skip_asset(task["asset"], excluded_assets)
                    if skip:
                        write_skip_log(task, reason)
                        continue
                    
                    all_assets = task.get("all_assets", [task["asset"]])
                    
                    # Check si commande corrigée
                    command_was_fixed = task["command"] != task.get("raw_command", task["command"])
                    if command_was_fixed:
                        print(f"[{now()}] [@Jordan via WATCHER] 🔧 Fixed command syntax")
                    
                    # Auto-download
                    download_success, downloaded, failed = download_missing_data(all_assets)
                    
                    if failed:
                        valid_assets = [a for a in all_assets if a not in failed]
                        if not valid_assets:
                            write_skip_log(task, f"No data for: {', '.join(failed)}")
                            continue
                        
                        # Update commande sans les assets failed
                        old_assets_str = " ".join(all_assets)
                        new_assets_str = " ".join(valid_assets)
                        task["command"] = task["command"].replace(old_assets_str, new_assets_str)
                        task["all_assets"] = valid_assets
                        task["asset"] = valid_assets[0]
                        print(f"[{now()}] [@Jordan via WATCHER] ⚠️ Reduced to: {new_assets_str}")
                    
                    task["downloaded_assets"] = downloaded
                    
                    # Run
                    print(f"[{now()}] [@Jordan via WATCHER] 🚀 Processing: {task['asset']} ({task['mode']})")
                    
                    write_jordan_run_start(task, command_was_fixed, len(downloaded) > 0)
                    success, output, duration = run_command(task)
                    write_jordan_run_complete(task, success, output, duration)
                    notify_casey(task, success, output, duration)
                    
                    if success:
                        trigger_sam_validation(task)
                    
                    status_icon = "✅" if success else "❌"
                    print(f"[{now()}] [@Jordan via WATCHER] {status_icon} Done: {task['asset']}")
            
            time.sleep(POLL_INTERVAL)
            
        except KeyboardInterrupt:
            print("\n[WATCHER] Stopped by user")
            break
        except Exception as e:
            print(f"[{now()}] [WATCHER] ERROR: {e}")
            import traceback
            traceback.print_exc()
            time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    main()
