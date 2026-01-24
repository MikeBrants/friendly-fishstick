#!/usr/bin/env python3
"""
Filter Rescue Pipeline - FINAL TRIGGER v2

Workflow simplifié: baseline → moderate → conservative
- Évite le data mining des 12 combinaisons arbitraires
- Max 3 tests par asset (correction statistique OK)
- Seuil sensitivity relevé à 15%

Usage:
    python scripts/run_filter_rescue.py ASSET
    python scripts/run_filter_rescue.py ETH
    python scripts/run_filter_rescue.py AVAX --trials 200
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from datetime import datetime
from glob import glob
from pathlib import Path

import pandas as pd

# Ordre de cascade des modes
MODES = ['baseline', 'moderate', 'conservative']


def run_mode(asset: str, mode: str, workers: int, trials: int) -> dict:
    """Run pipeline for a single mode and collect results."""
    print(f"\n{'='*60}")
    print(f"  {asset} — Testing mode: {mode.upper()}")
    print(f"{'='*60}")
    
    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_prefix = f"rescue_{asset}_{mode}_{run_id}"
    
    cmd = [
        sys.executable,
        str(Path(__file__).parent / "run_full_pipeline.py"),
        "--assets", asset,
        "--workers", str(workers),
        "--trials-atr", str(trials),
        "--trials-ichi", str(trials),
        "--enforce-tp-progression",
        "--optimization-mode", mode,
        "--skip-download",
        "--run-guards",
        "--output-prefix", output_prefix,
    ]
    
    print(f"Command: {' '.join(cmd)}")
    result = subprocess.run(cmd, check=False)
    
    # Collecter résultats
    try:
        scan_files = sorted(glob(f"outputs/{output_prefix}_multiasset_scan_*.csv"))
        guards_files = sorted(glob(f"outputs/{output_prefix}_guards_summary_*.csv"))
        
        if not scan_files or not guards_files:
            return {
                "mode": mode,
                "status": "ERROR",
                "error": "Missing output files",
                "all_pass": False,
            }
        
        scan = pd.read_csv(scan_files[-1])
        guards = pd.read_csv(guards_files[-1])
        
        scan_row = scan[scan["asset"] == asset]
        guard_row = guards[guards["asset"] == asset]
        
        if scan_row.empty or guard_row.empty:
            return {
                "mode": mode,
                "status": "ERROR", 
                "error": f"Asset {asset} not found in results",
                "all_pass": False,
            }
        
        scan_row = scan_row.iloc[0]
        guard_row = guard_row.iloc[0]
        
        return {
            "mode": mode,
            "status": "SUCCESS" if result.returncode == 0 else "PIPELINE_ERROR",
            "oos_sharpe": round(float(scan_row.get("oos_sharpe", 0.0)), 2),
            "wfe": round(float(scan_row.get("wfe", 0.0)), 2),
            "oos_trades": int(scan_row.get("oos_trades", 0)),
            "sensitivity": round(float(guard_row.get("guard002_variance_pct", 0.0)), 2),
            "guard002_pass": bool(guard_row.get("guard002_pass", False)),
            "all_pass": bool(guard_row.get("all_pass", False)),
            "scan_file": scan_files[-1],
            "guards_file": guards_files[-1],
            "error": None,
        }
    except Exception as e:
        return {
            "mode": mode,
            "status": "ERROR",
            "error": str(e),
            "all_pass": False,
        }


def main():
    parser = argparse.ArgumentParser(
        description="Filter Rescue Pipeline - cascade baseline → moderate → conservative"
    )
    parser.add_argument("asset", type=str, help="Asset symbol (e.g., ETH, AVAX)")
    parser.add_argument("--workers", type=int, default=1, help="Number of workers (default: 1 for reproducibility)")
    parser.add_argument("--trials", type=int, default=300, help="Trials per optimization (default: 300)")
    args = parser.parse_args()
    
    asset = args.asset.upper()
    results = []
    winner_mode = None
    
    print("=" * 60)
    print(f"FILTER RESCUE PIPELINE - {asset}")
    print(f"Modes: {' → '.join(MODES)}")
    print(f"Workers: {args.workers}, Trials: {args.trials}")
    print("=" * 60)
    
    for mode in MODES:
        result = run_mode(asset, mode, args.workers, args.trials)
        results.append(result)
        
        if result.get("error"):
            print(f"\n⚠️  {asset} ERROR with mode {mode}: {result['error']}")
            if mode != 'conservative':
                print(f"   → Trying next mode...")
            continue
        
        # Afficher résumé
        print(f"\n{'─'*40}")
        print(f"Mode: {mode.upper()}")
        print(f"  Sharpe OOS: {result.get('oos_sharpe', 'N/A')}")
        print(f"  WFE: {result.get('wfe', 'N/A')}")
        print(f"  Trades OOS: {result.get('oos_trades', 'N/A')}")
        print(f"  Sensitivity: {result.get('sensitivity', 'N/A')}%")
        print(f"  Guard002 PASS: {result.get('guard002_pass', False)}")
        print(f"  ALL GUARDS PASS: {result.get('all_pass', False)}")
        
        # Si PASS, on arrête
        if result.get("all_pass"):
            winner_mode = mode
            print(f"\n{'='*60}")
            print(f"✅ {asset} VALIDATED with mode: {mode.upper()}")
            print(f"{'='*60}")
            print(f"   Sharpe: {result['oos_sharpe']:.2f}")
            print(f"   WFE: {result['wfe']:.2f}")
            print(f"   Trades: {result['oos_trades']}")
            print(f"   Sensitivity: {result['sensitivity']:.1f}%")
            break
        else:
            print(f"\n❌ {asset} FAILED with mode: {mode}")
            if mode != 'conservative':
                print(f"   → Trying next mode...")
    
    # Si aucun mode n'a passé
    if winner_mode is None:
        print(f"\n{'='*60}")
        print(f"🚫 {asset} EXCLUDED — Failed all 3 modes")
        print(f"{'='*60}")
        print("Recommendation: Asset should be EXCLUDED from PROD")
    
    # Export résultats
    df = pd.DataFrame(results)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"outputs/filter_rescue_{asset}_{timestamp}.csv"
    df.to_csv(output_file, index=False)
    print(f"\nResults saved to: {output_file}")
    
    # Résumé final
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    for r in results:
        status = "✅ PASS" if r.get("all_pass") else "❌ FAIL"
        sens = f"{r.get('sensitivity', 'N/A')}%" if r.get('sensitivity') is not None else "ERROR"
        print(f"  {r['mode']:15} | {status} | Sensitivity: {sens}")
    
    if winner_mode:
        print(f"\n🏆 Winner: {winner_mode.upper()}")
        return 0
    else:
        print(f"\n🚫 No winner - Asset EXCLUDED")
        return 1


if __name__ == "__main__":
    sys.exit(main())
