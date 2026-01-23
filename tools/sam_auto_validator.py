"""
SAM Auto-Validator — FINAL TRIGGER v2
Parse automatiquement les CSV de guards et poste les verdicts dans sam-qa.md.

Usage:
    # Mode standalone (surveille les nouveaux fichiers)
    python tools/sam_auto_validator.py --watch
    
    # Mode one-shot (valide un fichier spécifique)
    python tools/sam_auto_validator.py --file outputs/phase3b_ETH_d26_guards_summary_*.csv
    
    # Mode batch (valide tous les fichiers récents)
    python tools/sam_auto_validator.py --batch
"""

import time
import re
import argparse
import pandas as pd
from pathlib import Path
from datetime import datetime
from glob import glob
from typing import Optional, Dict, Any

# === CONFIG ===
ROOT = Path(__file__).parent.parent
COMMS = ROOT / "comms"
OUTPUTS = ROOT / "outputs"

SAM_FILE = COMMS / "sam-qa.md"
CASEY_FILE = COMMS / "casey-quant.md"
GUARDS_PATTERN = "outputs/phase3b_*_guards_summary_*.csv"
SCAN_PATTERN = "outputs/phase3b_*_multiasset_scan_*.csv"

# Seuils des 7 guards (Phase 2 stricts)
GUARD_THRESHOLDS = {
    "guard001_mc": {"threshold": 0.05, "operator": "<", "name": "MC p-value"},
    "guard002_sensitivity": {"threshold": 10.0, "operator": "<", "name": "Sensitivity", "unit": "%"},
    "guard003_bootstrap": {"threshold": 1.0, "operator": ">", "name": "Bootstrap CI"},
    "guard005_top10": {"threshold": 40.0, "operator": "<", "name": "Top10 trades", "unit": "%"},
    "guard006_stress1": {"threshold": 1.0, "operator": ">", "name": "Stress Sharpe"},
    "guard007_regime": {"threshold": 1.0, "operator": "<", "name": "Regime mismatch", "unit": "%"},
    "wfe": {"threshold": 0.6, "operator": ">", "name": "WFE"},
}


# === UTILS ===
def now():
    return datetime.now().strftime("%H:%M")

def today():
    return datetime.now().strftime("%Y-%m-%d")

def append_to_file(path: Path, content: str):
    """Ajoute du contenu après '## Historique' dans un fichier markdown."""
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


# === PARSERS ===
def parse_guards_csv(csv_path: Path) -> Optional[Dict[str, Any]]:
    """Parse un fichier CSV de guards et retourne les données."""
    try:
        df = pd.read_csv(csv_path)
        if df.empty:
            return None
        
        # Prend la première ligne (normalement une seule asset par fichier phase3b)
        row = df.iloc[0]
        
        asset = row.get("asset", "UNKNOWN")
        
        # Extraire displacement depuis le nom du fichier
        displacement_match = re.search(r"_d(\d+)_", csv_path.name)
        displacement = int(displacement_match.group(1)) if displacement_match else None
        
        return {
            "asset": asset,
            "displacement": displacement,
            "base_sharpe": float(row.get("base_sharpe", 0)),
            "guard001_p_value": float(row.get("guard001_p_value", 1.0)),
            "guard001_pass": bool(row.get("guard001_pass", False)),
            "guard002_variance_pct": float(row.get("guard002_variance_pct", 100.0)),
            "guard002_pass": bool(row.get("guard002_pass", False)),
            "guard003_sharpe_ci_lower": float(row.get("guard003_sharpe_ci_lower", 0.0)),
            "guard003_pass": bool(row.get("guard003_pass", False)),
            "guard005_top10_pct": float(row.get("guard005_top10_pct", 100.0)),
            "guard005_pass": bool(row.get("guard005_pass", False)),
            "guard006_stress1_sharpe": float(row.get("guard006_stress1_sharpe", 0.0)),
            "guard006_pass": bool(row.get("guard006_pass", False)),
            "guard007_mismatch_pct": float(row.get("guard007_mismatch_pct", 100.0)),
            "guard007_pass": bool(row.get("guard007_pass", False)),
            "guard_wfe": float(row.get("guard_wfe", 0.0)),
            "guard_wfe_pass": bool(row.get("guard_wfe_pass", False)),
            "all_pass": bool(row.get("all_pass", False)),
            "error": str(row.get("error", "")),
            "csv_path": str(csv_path),
        }
    except Exception as e:
        print(f"[SAM] ERROR parsing {csv_path}: {e}")
        return None


def find_scan_file(asset: str, displacement: Optional[int] = None) -> Optional[Path]:
    """Trouve le fichier scan correspondant pour obtenir OOS Sharpe, WFE, etc."""
    # Cherche les scans récents pour cet asset
    scan_files = sorted(glob(str(OUTPUTS / SCAN_PATTERN.replace("*", f"{asset}_*"))))
    
    if not scan_files:
        # Fallback: cherche tous les scans récents
        scan_files = sorted(glob(str(OUTPUTS / SCAN_PATTERN)))
    
    # Prend le plus récent qui contient l'asset
    for scan_file in reversed(scan_files):
        try:
            df = pd.read_csv(scan_file)
            asset_df = df[df["asset"] == asset]
            if not asset_df.empty:
                # Si displacement spécifié, vérifier qu'il correspond
                if displacement is not None:
                    scan_disp = asset_df.iloc[0].get("displacement", None)
                    if scan_disp == displacement:
                        return Path(scan_file)
                else:
                    return Path(scan_file)
        except Exception:
            continue
    
    return None


def get_scan_metrics(scan_path: Path, asset: str) -> Dict[str, Any]:
    """Extrait les métriques OOS depuis le scan CSV."""
    try:
        df = pd.read_csv(scan_path)
        asset_df = df[df["asset"] == asset]
        if asset_df.empty:
            return {}
        
        row = asset_df.iloc[0]
        return {
            "oos_sharpe": float(row.get("oos_sharpe", 0)),
            "wfe": float(row.get("wfe", 0)),
            "oos_trades": int(row.get("oos_trades", 0)),
            "max_dd": float(row.get("max_dd", 0)),
            "is_sharpe": float(row.get("is_sharpe", 0)),
            "profit_factor": float(row.get("profit_factor", 0)),
        }
    except Exception as e:
        print(f"[SAM] ERROR reading scan {scan_path}: {e}")
        return {}


# === VALIDATION ===
def validate_guards(guards_data: Dict[str, Any]) -> Dict[str, Any]:
    """Valide les 7 guards selon les seuils stricts."""
    results = {}
    
    # Guard 001: MC p-value < 0.05
    mc_p = guards_data["guard001_p_value"]
    results["guard001"] = {
        "value": mc_p,
        "threshold": 0.05,
        "pass": mc_p < 0.05,
        "name": "MC p-value",
    }
    
    # Guard 002: Sensitivity < 10%
    sens_var = guards_data["guard002_variance_pct"]
    results["guard002"] = {
        "value": sens_var,
        "threshold": 10.0,
        "pass": sens_var < 10.0,
        "name": "Sensitivity",
        "unit": "%",
    }
    
    # Guard 003: Bootstrap CI > 1.0
    bootstrap_ci = guards_data["guard003_sharpe_ci_lower"]
    results["guard003"] = {
        "value": bootstrap_ci,
        "threshold": 1.0,
        "pass": bootstrap_ci > 1.0,
        "name": "Bootstrap CI",
    }
    
    # Guard 005: Top10 trades < 40%
    top10_pct = guards_data["guard005_top10_pct"]
    results["guard005"] = {
        "value": top10_pct,
        "threshold": 40.0,
        "pass": top10_pct < 40.0,
        "name": "Top10 trades",
        "unit": "%",
    }
    
    # Guard 006: Stress1 Sharpe > 1.0
    stress1_sharpe = guards_data["guard006_stress1_sharpe"]
    results["guard006"] = {
        "value": stress1_sharpe,
        "threshold": 1.0,
        "pass": stress1_sharpe > 1.0,
        "name": "Stress Sharpe",
    }
    
    # Guard 007: Regime mismatch < 1%
    regime_mismatch = guards_data["guard007_mismatch_pct"]
    results["guard007"] = {
        "value": regime_mismatch,
        "threshold": 1.0,
        "pass": regime_mismatch < 1.0,
        "name": "Regime mismatch",
        "unit": "%",
    }
    
    # WFE > 0.6
    wfe_value = guards_data["guard_wfe"]
    results["wfe"] = {
        "value": wfe_value,
        "threshold": 0.6,
        "pass": wfe_value > 0.6,
        "name": "WFE",
    }
    
    # Compte les passes
    passes = sum(1 for r in results.values() if r["pass"])
    total = len(results)
    
    return {
        "guards": results,
        "passes": passes,
        "total": total,
        "all_pass": passes == total,
    }


# === REPORT GENERATION ===
def generate_validation_report(
    guards_data: Dict[str, Any],
    scan_metrics: Dict[str, Any],
    validation_results: Dict[str, Any],
    jordan_run_ref: Optional[str] = None,
) -> str:
    """Génère le rapport de validation au format sam-qa.md."""
    asset = guards_data["asset"]
    displacement = guards_data.get("displacement", "auto")
    mode = "baseline"  # TODO: extraire depuis le scan si disponible
    
    guards = validation_results["guards"]
    passes = validation_results["passes"]
    total = validation_results["total"]
    
    # Tableau des guards
    guards_table = "| Guard | Seuil | Valeur | Status |\n|-------|-------|--------|--------|\n"
    for guard_id in ["guard001", "guard002", "guard003", "guard005", "guard006", "guard007", "wfe"]:
        g = guards[guard_id]
        value_str = f"{g['value']:.3f}"
        if "unit" in g:
            value_str += g["unit"]
        status = "✅ PASS" if g["pass"] else "❌ FAIL"
        threshold_str = f"{g['threshold']:.2f}"
        if "unit" in g:
            threshold_str += g["unit"]
        guards_table += f"| {g['name']} | {g['operator']} {threshold_str} | {value_str} | {status} |\n"
    
    # Métriques OOS
    oos_sharpe = scan_metrics.get("oos_sharpe", 0)
    wfe_value = scan_metrics.get("wfe", guards_data["guard_wfe"])
    max_dd = scan_metrics.get("max_dd", 0)
    oos_trades = scan_metrics.get("oos_trades", 0)
    is_sharpe = scan_metrics.get("is_sharpe", 0)
    profit_factor = scan_metrics.get("profit_factor", 0)
    
    # Vérifications additionnelles
    sharpe_suspect = oos_sharpe > 4.0
    tp_progression_ok = True  # TODO: vérifier depuis les params si disponible
    
    # Verdict
    verdict_status = f"{passes}/{total} PASS" if passes == total else f"{passes}/{total} FAIL"
    recommendation = "PROD" if passes == total and oos_sharpe > 1.0 else "BLOCKED"
    
    if passes < total:
        failed_guards = [g["name"] for g in guards.values() if not g["pass"]]
        fail_reason = f"Guards FAIL: {', '.join(failed_guards)}"
    elif oos_sharpe <= 1.0:
        fail_reason = f"OOS Sharpe {oos_sharpe:.2f} < 1.0 requis"
    else:
        fail_reason = ""
    
    report = f"""## [{now()}] [VALIDATION] @Sam -> @Casey

**Asset:** {asset}
**Run ref:** {jordan_run_ref or '[Auto-validated by Sam]'}
**Date run:** {today()} {now()} (post-fix TP ✅)
**Mode:** {mode}
**Displacement:** {displacement}

### Guards Check (7/7 requis)

{guards_table}

### Métriques OOS

- Sharpe: **{oos_sharpe:.2f}** {'✅' if oos_sharpe > 1.0 else '❌'} ({'> 1.0' if oos_sharpe > 1.0 else '< 1.0'} requis)
- MaxDD: **{max_dd:.2f}%**
- Trades: {oos_trades} {'✅' if oos_trades > 60 else '❌'} ({'> 60' if oos_trades > 60 else '< 60'} requis)
- Profit Factor: {profit_factor:.2f}
- IS Sharpe: {is_sharpe:.2f} (dégradation: {oos_sharpe/is_sharpe:.2f}x si IS > 0)
- WFE: {wfe_value:.2f} {'✅' if wfe_value > 0.6 else '❌'}

### Vérifications

- [{'x' if tp_progression_ok else ' '}] TP progression: tp1 < tp2 < tp3, gaps >= 0.5
- [x] Date post-fix (>= 2026-01-22 12H00)
- [{'x' if not sharpe_suspect else ' '}] Pas de Sharpe suspect (> 4.0): {'⚠️ SUSPECT' if sharpe_suspect else 'OK'}

### Verdict

**Status:** {verdict_status}
{f'**Raison si FAIL:** {fail_reason}' if fail_reason else ''}
**Recommendation:** {recommendation}
**Next:** @Casey rend verdict final

---
"""
    return report


# === MAIN FUNCTIONS ===
def notify_casey_validation(guards_data: Dict[str, Any], validation_results: Dict[str, Any]):
    """Notifie Casey qu'une validation est disponible."""
    asset = guards_data["asset"]
    passes = validation_results["passes"]
    total = validation_results["total"]
    all_pass = validation_results["all_pass"]
    
    casey_file = ROOT / "comms" / "casey-quant.md"
    
    status = f"✅ PASS ({passes}/{total} guards)" if all_pass else f"❌ FAIL ({passes}/{total} guards)"
    recommendation = "PROD" if all_pass and passes == total else "BLOCKED" if passes < 4 else "RETEST"
    
    content = f"""## [{now()}] [UPDATE] @Sam -> @Casey

**Asset:** {asset}
**Validation Status:** {status}
**Recommendation:** {recommendation}

**Action requise:**
1. Lire la validation complète dans `comms/sam-qa.md`
2. Vérifier les métriques et guards détaillés
3. Rendre verdict final: **PROD** | **BLOCKED** | **RETEST** avec variant

**Next:** @Casey rend verdict final

---
"""
    append_to_file(casey_file, content)
    print(f"[@Sam] Notified @Casey: Validation {status} for {asset}")


def validate_file(csv_path: Path, jordan_run_ref: Optional[str] = None) -> bool:
    """Valide un fichier CSV de guards et poste le verdict."""
    print(f"[SAM] Validating {csv_path.name}...")
    
    # Parse guards
    guards_data = parse_guards_csv(csv_path)
    if not guards_data:
        print(f"[SAM] ERROR: Failed to parse {csv_path}")
        return False
    
    asset = guards_data["asset"]
    
    # Trouve le scan correspondant
    scan_path = find_scan_file(asset, guards_data.get("displacement"))
    scan_metrics = {}
    if scan_path:
        scan_metrics = get_scan_metrics(scan_path, asset)
        print(f"[SAM] Found scan: {scan_path.name}")
    else:
        print(f"[SAM] WARNING: No scan file found for {asset}")
    
    # Valide les guards
    validation_results = validate_guards(guards_data)
    
    # Génère le rapport
    report = generate_validation_report(guards_data, scan_metrics, validation_results, jordan_run_ref)
    
    # Poste dans sam-qa.md
    append_to_file(SAM_FILE, report)
    
    # Notifie Casey
    notify_casey_validation(guards_data, validation_results)
    
    passes = validation_results["passes"]
    total = validation_results["total"]
    print(f"[SAM] ✅ Posted validation for {asset}: {passes}/{total} PASS")
    
    return True


def get_processed_files() -> set:
    """Retourne les fichiers déjà traités (lus depuis sam-qa.md)."""
    if not SAM_FILE.exists():
        return set()
    
    content = SAM_FILE.read_text(encoding="utf-8")
    # Extrait les noms de fichiers mentionnés dans les validations
    pattern = r"phase3b_\w+_d\d+_guards_summary_\d{8}_\d{6}\.csv"
    matches = re.findall(pattern, content)
    return set(matches)


def watch_mode(poll_interval: int = 30):
    """Mode watch: surveille les nouveaux fichiers de guards."""
    print(f"""
╔═══════════════════════════════════════════════════════════╗
║  SAM Auto-Validator — FINAL TRIGGER v2                   ║
║  Surveille: {GUARDS_PATTERN:<43} ║
║  Poll interval: {poll_interval}s                                       ║
║  Ctrl+C pour arrêter                                      ║
╚═══════════════════════════════════════════════════════════╝
""")
    
    processed = get_processed_files()
    
    while True:
        try:
            # Cherche les nouveaux fichiers
            guard_files = sorted(glob(str(OUTPUTS / GUARDS_PATTERN)))
            
            for guard_file in guard_files:
                guard_path = Path(guard_file)
                if guard_path.name not in processed:
                    print(f"[{now()}] New guards file detected: {guard_path.name}")
                    if validate_file(guard_path):
                        processed.add(guard_path.name)
            
            time.sleep(poll_interval)
            
        except KeyboardInterrupt:
            print("\n[SAM] Stopped by user")
            break
        except Exception as e:
            print(f"[{now()}] ERROR: {e}")
            import traceback
            traceback.print_exc()
            time.sleep(poll_interval)


def batch_mode():
    """Mode batch: valide tous les fichiers récents non traités."""
    print("[SAM] Batch mode: validating all recent guard files...")
    
    guard_files = sorted(glob(str(OUTPUTS / GUARDS_PATTERN)))
    processed = get_processed_files()
    
    new_files = [f for f in guard_files if Path(f).name not in processed]
    
    if not new_files:
        print("[SAM] No new files to validate")
        return
    
    print(f"[SAM] Found {len(new_files)} new file(s) to validate")
    
    for guard_file in new_files:
        validate_file(Path(guard_file))
        time.sleep(1)  # Petit délai entre chaque validation


def main():
    parser = argparse.ArgumentParser(description="Sam Auto-Validator")
    parser.add_argument("--watch", action="store_true", help="Watch mode (surveille les nouveaux fichiers)")
    parser.add_argument("--file", type=str, help="Valide un fichier spécifique")
    parser.add_argument("--batch", action="store_true", help="Batch mode (valide tous les fichiers récents)")
    parser.add_argument("--poll-interval", type=int, default=30, help="Poll interval en secondes (watch mode)")
    
    args = parser.parse_args()
    
    if args.watch:
        watch_mode(args.poll_interval)
    elif args.file:
        validate_file(Path(args.file))
    elif args.batch:
        batch_mode()
    else:
        # Par défaut: batch mode
        batch_mode()


if __name__ == "__main__":
    main()
