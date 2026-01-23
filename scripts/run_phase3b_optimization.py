"""
Phase 3B: Displacement Grid Optimization for PROD Winners

Objectif: Améliorer les winners avec un displacement alternatif.

Principe:
- Teste d26, d52, d78 sur chaque winner PROD
- Compare Sharpe OOS et WFE vs baseline actuel
- Garde le meilleur si amélioration > 10% ET toujours 7/7 PASS

Usage:
    python scripts/run_phase3b_optimization.py --workers 4
    python scripts/run_phase3b_optimization.py --assets BTC ETH --workers 4
"""
from __future__ import annotations

import argparse
import sys
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Optional

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent))

from crypto_backtest.config.asset_config import ASSET_CONFIG


def get_prod_assets() -> list[str]:
    """Récupère tous les assets PROD depuis asset_config.py"""
    return list(ASSET_CONFIG.keys())


def get_asset_baseline(asset: str) -> tuple[int, str]:
    """Récupère le displacement et filter_mode actuels d'un asset"""
    if asset not in ASSET_CONFIG:
        raise ValueError(f"Asset {asset} not found in ASSET_CONFIG")
    config = ASSET_CONFIG[asset]
    displacement = config.get("displacement", 52)
    filter_mode = config.get("filter_mode", "baseline")
    return displacement, filter_mode


def run_optimization_with_displacement(
    asset: str,
    displacement: int,
    filter_mode: str,
    trials_atr: int,
    trials_ichi: int,
    workers: int,
) -> Optional[str]:
    """
    Lance l'optimisation pour un asset avec un displacement fixe.
    Retourne le chemin du fichier scan généré si l'optimisation réussit et contient des résultats valides.
    Les guards sont lancés seulement si l'optimisation réussit ET contient des résultats valides.
    """
    print(f"  [{asset}] Testing displacement {displacement} with mode {filter_mode}...")
    
    # ÉTAPE 1: Optimisation (sans guards)
    cmd = [
        sys.executable,
        str(Path(__file__).parent / "run_full_pipeline.py"),
        "--assets",
        asset,
        "--fixed-displacement",
        str(displacement),
        "--optimization-mode",
        filter_mode,
        "--trials-atr",
        str(trials_atr),
        "--trials-ichi",
        str(trials_ichi),
        "--enforce-tp-progression",
        # PAS de --run-guards ici - on les lancera seulement si optimisation réussit
        "--workers",
        str(workers),
        "--output-prefix",
        f"phase3b_{asset}_d{displacement}",
        "--skip-download",  # Assume data already downloaded
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"  [{asset}] ERROR: Optimization failed for d{displacement}")
        print(f"  {result.stderr[:500]}")
        return None
    
    # ÉTAPE 2: Vérifie que le scan existe et contient des résultats valides
    from glob import glob
    scan_files = sorted(
        glob(f"outputs/phase3b_{asset}_d{displacement}_multiasset_scan_*.csv")
    )
    
    scan_path = None
    if scan_files:
        scan_path = scan_files[-1]
    else:
        # Fallback: cherche le dernier scan pour cet asset
        scan_files = sorted(glob("outputs/multiasset_scan_*.csv"))
        if scan_files:
            scan_path = scan_files[-1]
    
    if not scan_path or not Path(scan_path).exists():
        print(f"  [{asset}] ERROR: No scan file found for d{displacement}")
        return None
    
    # Vérifie que le scan contient l'asset avec des résultats valides
    try:
        df = pd.read_csv(scan_path)
        asset_df = df[df["asset"] == asset]
        
        if asset_df.empty:
            print(f"  [{asset}] ERROR: Asset not found in scan results for d{displacement}")
            return None
        
        # Vérifie que les résultats sont valides (au moins un Sharpe OOS valide)
        valid_results = asset_df[
            (asset_df["oos_sharpe"].notna()) & 
            (asset_df["oos_sharpe"] != 0)
        ]
        
        if valid_results.empty:
            print(f"  [{asset}] ERROR: No valid results in scan for d{displacement}")
            return None
    except Exception as e:
        print(f"  [{asset}] ERROR: Failed to read scan file: {e}")
        return None
    
    # ÉTAPE 3: Lance les guards seulement si optimisation réussie et scan valide
    print(f"  [{asset}] Optimization successful for d{displacement}, running guards...")
    
    guard_cmd = [
        sys.executable,
        str(Path(__file__).parent / "run_guards_multiasset.py"),
        "--assets",
        asset,
        "--params-file",
        scan_path,
        "--workers",
        str(workers),
        "--summary-output",
        str(Path("outputs") / f"phase3b_{asset}_d{displacement}_guards_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"),
    ]
    
    guard_result = subprocess.run(guard_cmd, capture_output=True, text=True)
    
    if guard_result.returncode != 0:
        print(f"  [{asset}] WARNING: Guards failed for d{displacement} (but optimization succeeded)")
        print(f"  {guard_result.stderr[:500]}")
        # On retourne quand même le scan_path car l'optimisation a réussi
    
    return scan_path


def load_scan_results(scan_path: str, asset: str) -> Optional[dict]:
    """Charge les résultats d'optimisation depuis un fichier scan"""
    if not scan_path or not Path(scan_path).exists():
        return None
    
    df = pd.read_csv(scan_path)
    asset_df = df[df["asset"] == asset]
    
    if asset_df.empty:
        return None
    
    # Prend la meilleure ligne (meilleur Sharpe OOS)
    best_row = asset_df.loc[asset_df["oos_sharpe"].idxmax()]
    
    return {
        "oos_sharpe": float(best_row.get("oos_sharpe", 0)),
        "wfe": float(best_row.get("wfe", 0)),
        "oos_trades": int(best_row.get("oos_trades", 0)),
        "max_dd": float(best_row.get("max_dd", 0)),
    }


def load_guards_results(asset: str, displacement: int) -> Optional[dict]:
    """Charge les résultats des guards depuis le fichier summary"""
    from glob import glob
    
    guard_files = sorted(
        glob(f"outputs/phase3b_{asset}_d{displacement}_*_guards_summary_*.csv")
    )
    
    if not guard_files:
        return None
    
    df = pd.read_csv(guard_files[-1])
    asset_df = df[df["asset"] == asset]
    
    if asset_df.empty:
        return None
    
    row = asset_df.iloc[0]
    
    # Vérifie les 7 guards
    guards_pass = {
        "guard001_mc": bool(row.get("guard001_pass", False)),
        "guard002_sensitivity": bool(row.get("guard002_pass", False)),
        "guard003_bootstrap": bool(row.get("guard003_pass", False)),
        "guard005_top10": bool(row.get("guard005_pass", False)),
        "guard006_stress1": bool(row.get("guard006_pass", False)),
        "guard007_regime": bool(row.get("guard007_pass", False)),
        "wfe": bool(row.get("wfe_pass", False)),
    }
    
    all_pass = all(guards_pass.values())
    
    return {
        "all_guards_pass": all_pass,
        "guards_detail": guards_pass,
        "mc_pvalue": float(row.get("mc_pvalue", 1.0)),
        "sensitivity_var": float(row.get("sensitivity_var", 100.0)),
        "bootstrap_ci_lower": float(row.get("bootstrap_ci_lower", 0.0)),
    }


def evaluate_displacement(
    asset: str,
    displacement: int,
    filter_mode: str,
    baseline_sharpe: float,
    baseline_wfe: float,
    trials_atr: int,
    trials_ichi: int,
    workers: int,
) -> dict:
    """
    Teste un displacement et retourne les résultats avec évaluation.
    """
    print(f"\n[{asset}] Testing displacement {displacement}...")
    
    # Lance optimisation
    scan_path = run_optimization_with_displacement(
        asset=asset,
        displacement=displacement,
        filter_mode=filter_mode,
        trials_atr=trials_atr,
        trials_ichi=trials_ichi,
        workers=workers,
    )
    
    if not scan_path:
        return {
            "asset": asset,
            "displacement": displacement,
            "status": "FAILED",
            "error": "Optimization failed",
        }
    
    # Charge résultats optimisation
    opt_results = load_scan_results(scan_path, asset)
    if not opt_results:
        return {
            "asset": asset,
            "displacement": displacement,
            "status": "FAILED",
            "error": "No optimization results",
        }
    
    # Garde-fou: WFE négatif = overfitting détecté
    wfe_value = opt_results.get("wfe", 0)
    if wfe_value < 0:
        print(f"  [{asset}] WARNING: WFE négatif ({wfe_value:.2f}) = overfitting détecté")
        return {
            "asset": asset,
            "displacement": displacement,
            "status": "OVERFITTING",
            "wfe": wfe_value,
            "oos_sharpe": opt_results.get("oos_sharpe", 0),
            "error": "WFE < 0 indicates overfitting",
        }
    
    # Charge résultats guards
    guards_results = load_guards_results(asset, displacement)
    
    # Calcule amélioration vs baseline
    improvement_pct = (
        (opt_results["oos_sharpe"] - baseline_sharpe) / baseline_sharpe * 100
        if baseline_sharpe > 0
        else 0
    )
    
    # Critère de remplacement: amélioration > 10% ET 7/7 guards PASS
    meets_criteria = (
        improvement_pct > 10.0
        and guards_results
        and guards_results["all_guards_pass"]
    )
    
    return {
        "asset": asset,
        "displacement": displacement,
        "filter_mode": filter_mode,
        "oos_sharpe": opt_results["oos_sharpe"],
        "wfe": opt_results["wfe"],
        "oos_trades": opt_results["oos_trades"],
        "max_dd": opt_results["max_dd"],
        "baseline_sharpe": baseline_sharpe,
        "baseline_wfe": baseline_wfe,
        "improvement_pct": improvement_pct,
        "all_guards_pass": guards_results["all_guards_pass"] if guards_results else False,
        "meets_criteria": meets_criteria,
        "status": "PASS" if meets_criteria else "FAIL",
        "scan_path": scan_path,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Phase 3B: Displacement Grid Optimization for PROD Winners"
    )
    parser.add_argument(
        "--assets",
        nargs="+",
        default=None,
        help="Specific assets to optimize (default: all PROD assets)",
    )
    # Phase 3B: 150 trials (vs 300 Phase 2) pour éviter overfitting
    # sur assets avec baseline déjà optimisé. Augmenter seulement si
    # WFE reste >0.6 et amélioration <5%.
    parser.add_argument(
        "--trials-atr",
        type=int,
        default=150,
        help="Number of ATR optimization trials (default: 150)",
    )
    parser.add_argument(
        "--trials-ichi",
        type=int,
        default=150,
        help="Number of Ichimoku optimization trials (default: 150)",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=8,
        help="Number of parallel workers (default: 8)",
    )
    parser.add_argument(
        "--displacements",
        nargs="+",
        type=int,
        default=[26, 52, 78],
        help="Displacements to test (default: 26 52 78)",
    )
    args = parser.parse_args()
    
    # Récupère assets PROD
    if args.assets:
        assets = args.assets
        # Vérifie que tous les assets sont dans PROD
        prod_assets = get_prod_assets()
        invalid = [a for a in assets if a not in prod_assets]
        if invalid:
            print(f"ERROR: Assets not in PROD: {invalid}")
            print(f"Available PROD assets: {prod_assets}")
            return
    else:
        assets = get_prod_assets()
    
    print("=" * 70)
    print("PHASE 3B: DISPLACEMENT GRID OPTIMIZATION")
    print(f"Started: {datetime.now().isoformat()}")
    print("=" * 70)
    print(f"Assets: {', '.join(assets)}")
    print(f"Displacements to test: {args.displacements}")
    print(f"Trials: ATR={args.trials_atr}, Ichi={args.trials_ichi}")
    print(f"Workers: {args.workers}")
    print("=" * 70)
    
    all_results = []
    summary = []
    
    for asset in assets:
        print(f"\n{'='*70}")
        print(f"Processing: {asset}")
        print(f"{'='*70}")
        
        # Récupère baseline
        baseline_disp, filter_mode = get_asset_baseline(asset)
        print(f"Baseline: displacement={baseline_disp}, mode={filter_mode}")
        
        # Charge baseline metrics depuis asset_config ou scan récent
        # Pour simplifier, on va optimiser aussi le baseline pour avoir les métriques
        baseline_results = evaluate_displacement(
            asset=asset,
            displacement=baseline_disp,
            filter_mode=filter_mode,
            baseline_sharpe=0.0,  # Sera mis à jour après
            baseline_wfe=0.0,
            trials_atr=args.trials_atr,
            trials_ichi=args.trials_ichi,
            workers=args.workers,
        )
        
        if baseline_results.get("status") == "FAILED":
            print(f"[{asset}] ERROR: Baseline optimization failed, skipping")
            continue
        
        baseline_sharpe = baseline_results["oos_sharpe"]
        baseline_wfe = baseline_results["wfe"]
        
        print(f"\n[{asset}] Baseline metrics:")
        print(f"  Sharpe OOS: {baseline_sharpe:.2f}")
        print(f"  WFE: {baseline_wfe:.2f}")
        print(f"  Guards: {'PASS' if baseline_results['all_guards_pass'] else 'FAIL'}")
        
        baseline_results["baseline_sharpe"] = baseline_sharpe
        baseline_results["baseline_wfe"] = baseline_wfe
        baseline_results["improvement_pct"] = 0.0
        all_results.append(baseline_results)
        
        # Teste autres displacements
        other_displacements = [d for d in args.displacements if d != baseline_disp]
        
        best_result = baseline_results
        best_displacement = baseline_disp
        
        for disp in other_displacements:
            result = evaluate_displacement(
                asset=asset,
                displacement=disp,
                filter_mode=filter_mode,
                baseline_sharpe=baseline_sharpe,
                baseline_wfe=baseline_wfe,
                trials_atr=args.trials_atr,
                trials_ichi=args.trials_ichi,
                workers=args.workers,
            )
            
            all_results.append(result)
            
            if result.get("status") == "PASS":
                print(f"\n[{asset}] [PASS] Displacement {disp} PASSES criteria:")
                print(f"  Sharpe: {result['oos_sharpe']:.2f} (improvement: {result['improvement_pct']:.1f}%)")
                print(f"  WFE: {result['wfe']:.2f}")
                print(f"  Guards: PASS")
                
                # Garde le meilleur (meilleur Sharpe)
                if result["oos_sharpe"] > best_result["oos_sharpe"]:
                    best_result = result
                    best_displacement = disp
            else:
                print(f"\n[{asset}] [FAIL] Displacement {disp} FAILS criteria:")
                if not result.get("all_guards_pass"):
                    print(f"  Guards: FAIL")
                if result.get("improvement_pct", 0) <= 10.0:
                    print(f"  Improvement: {result.get('improvement_pct', 0):.1f}% (need >10%)")
        
        # Résumé par asset
        summary.append({
            "asset": asset,
            "current_displacement": baseline_disp,
            "current_sharpe": baseline_sharpe,
            "current_wfe": baseline_wfe,
            "best_displacement": best_displacement,
            "best_sharpe": best_result["oos_sharpe"],
            "best_wfe": best_result["wfe"],
            "improvement_pct": best_result["improvement_pct"] if best_displacement != baseline_disp else 0.0,
            "recommendation": "KEEP" if best_displacement == baseline_disp else "UPDATE",
        })
        
        print(f"\n[{asset}] Summary:")
        print(f"  Current: d{baseline_disp} (Sharpe {baseline_sharpe:.2f})")
        print(f"  Best: d{best_displacement} (Sharpe {best_result['oos_sharpe']:.2f})")
        if best_displacement != baseline_disp:
            print(f"  [PASS] RECOMMENDATION: Update to d{best_displacement}")
        else:
            print(f"  [PASS] RECOMMENDATION: Keep current d{baseline_disp}")
    
    # Export résultats
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    results_df = pd.DataFrame(all_results)
    results_path = Path("outputs") / f"displacement_optimization_{timestamp}.csv"
    results_df.to_csv(results_path, index=False)
    print(f"\n{'='*70}")
    print(f"Results exported: {results_path}")
    
    summary_df = pd.DataFrame(summary)
    summary_path = Path("outputs") / f"displacement_optimization_summary_{timestamp}.csv"
    summary_df.to_csv(summary_path, index=False)
    print(f"Summary exported: {summary_path}")
    
    # Affiche résumé final
    print(f"\n{'='*70}")
    print("FINAL SUMMARY")
    print(f"{'='*70}")
    print(summary_df.to_string(index=False))
    
    updates = summary_df[summary_df["recommendation"] == "UPDATE"]
    if not updates.empty:
        print(f"\n[PASS] Assets to update: {len(updates)}")
        for _, row in updates.iterrows():
            print(f"  {row['asset']}: d{row['current_displacement']} → d{row['best_displacement']} "
                  f"(+{row['improvement_pct']:.1f}% Sharpe)")
    else:
        print("\n[PASS] No updates recommended - all assets already optimal")
    
    print(f"\nFinished: {datetime.now().isoformat()}")


if __name__ == "__main__":
    main()
