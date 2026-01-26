#!/usr/bin/env python3
"""Phase 3A Displacement Rescue for failed assets.

This script attempts to rescue assets that failed baseline validation
by testing different Ichimoku displacement values (d26, d52, d78).

Usage:
    python scripts/run_phase3a_rescue.py --assets OSMO AR METIS
    python scripts/run_phase3a_rescue.py --assets OSMO --displacements 26 52 78
"""

import argparse
import subprocess
import sys
from pathlib import Path
from datetime import datetime
import json

PROJECT_ROOT = Path(__file__).parent.parent

# Assets that need rescue (from project-state.md)
RESCUE_CANDIDATES = {
    "OSMO": {"reason": "Sharpe 0.68, WFE 0.19", "priority": 1},
    "AR": {"reason": "WFE 0.39, Trades 41", "priority": 2},
    "METIS": {"reason": "WFE 0.48", "priority": 3},
}

# Standard Ichimoku displacement values
DEFAULT_DISPLACEMENTS = [26, 52, 78]

# Validation thresholds
THRESHOLDS = {
    "wfe_min": 0.6,
    "sharpe_min": 0.8,
    "trades_min": 40,  # Conservative mode
}


def run_optimization_for_displacement(
    asset: str,
    displacement: int,
    trials: int = 300,
    workers: int = 1
) -> dict:
    """Run optimization for a specific displacement value."""
    
    print(f"\n{'='*60}")
    print(f"RESCUE: {asset} with displacement={displacement}")
    print(f"{'='*60}")
    
    # Build command
    cmd = [
        sys.executable,
        str(PROJECT_ROOT / "scripts" / "run_full_pipeline.py"),
        "--assets", asset,
        "--optimization-mode", "baseline",
        "--trials-atr", str(trials),
        "--trials-ichi", str(trials),
        "--displacement", str(displacement),
        "--run-guards",
        "--workers", str(workers),
    ]
    
    print(f"Command: {' '.join(cmd)}")
    print(f"Started: {datetime.now().strftime('%H:%M:%S')}")
    
    # Execute
    try:
        result = subprocess.run(
            cmd,
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=7200  # 2 hour timeout
        )
        
        if result.returncode == 0:
            print(f"✅ Optimization completed successfully")
            return {
                "asset": asset,
                "displacement": displacement,
                "status": "completed",
                "stdout": result.stdout[-2000:] if result.stdout else "",
            }
        else:
            print(f"❌ Optimization failed with return code {result.returncode}")
            return {
                "asset": asset,
                "displacement": displacement,
                "status": "failed",
                "error": result.stderr[-1000:] if result.stderr else "Unknown error",
            }
            
    except subprocess.TimeoutExpired:
        print(f"⏰ Optimization timed out after 2 hours")
        return {
            "asset": asset,
            "displacement": displacement,
            "status": "timeout",
        }
    except Exception as e:
        print(f"❌ Error: {e}")
        return {
            "asset": asset,
            "displacement": displacement,
            "status": "error",
            "error": str(e),
        }


def find_latest_output(asset: str, displacement: int) -> Path | None:
    """Find the latest output file for an asset/displacement combo."""
    output_dir = PROJECT_ROOT / "outputs"
    
    # Pattern: rescue_{asset}_d{displacement}_*.csv or similar
    patterns = [
        f"rescue_{asset}_d{displacement}_*.csv",
        f"{asset}_d{displacement}_*.csv",
        f"{asset}_displacement_{displacement}_*.csv",
    ]
    
    for pattern in patterns:
        files = list(output_dir.glob(pattern))
        if files:
            return max(files, key=lambda p: p.stat().st_mtime)
    
    return None


def parse_results(output_file: Path) -> dict | None:
    """Parse optimization results from CSV."""
    try:
        import pandas as pd
        df = pd.read_csv(output_file)
        
        if df.empty:
            return None
        
        # Get best result (usually first row or row with best Sharpe)
        if "sharpe_oos" in df.columns:
            best = df.loc[df["sharpe_oos"].idxmax()]
        else:
            best = df.iloc[0]
        
        return {
            "sharpe_oos": best.get("sharpe_oos", best.get("sharpe", None)),
            "wfe": best.get("wfe_pardo", best.get("wfe", None)),
            "trades_oos": best.get("trades_oos", best.get("trades", None)),
            "all_pass": best.get("all_pass", None),
            "params": {
                "sl_mult": best.get("sl_mult", None),
                "tp1_mult": best.get("tp1_mult", None),
                "tp2_mult": best.get("tp2_mult", None),
                "tp3_mult": best.get("tp3_mult", None),
                "tenkan": best.get("tenkan", None),
                "kijun": best.get("kijun", None),
            }
        }
    except Exception as e:
        print(f"Error parsing {output_file}: {e}")
        return None


def evaluate_rescue(results: dict) -> str:
    """Evaluate if rescue was successful."""
    if not results:
        return "NO_DATA"
    
    sharpe = results.get("sharpe_oos")
    wfe = results.get("wfe")
    trades = results.get("trades_oos")
    all_pass = results.get("all_pass")
    
    if all_pass == True or all_pass == "True":
        return "PASS"
    
    if sharpe is None or wfe is None:
        return "INCOMPLETE"
    
    if sharpe >= THRESHOLDS["sharpe_min"] and wfe >= THRESHOLDS["wfe_min"]:
        if trades is None or trades >= THRESHOLDS["trades_min"]:
            return "LIKELY_PASS"
        else:
            return "LOW_TRADES"
    
    if wfe < THRESHOLDS["wfe_min"]:
        return "FAIL_WFE"
    if sharpe < THRESHOLDS["sharpe_min"]:
        return "FAIL_SHARPE"
    
    return "FAIL"


def run_rescue_campaign(
    assets: list,
    displacements: list,
    trials: int = 300,
    workers: int = 1,
    dry_run: bool = False
) -> dict:
    """Run full rescue campaign for multiple assets."""
    
    print("\n" + "="*80)
    print("PHASE 3A DISPLACEMENT RESCUE")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Assets: {assets}")
    print(f"Displacements: {displacements}")
    print(f"Trials per run: {trials}")
    print("="*80)
    
    all_results = {}
    
    for asset in assets:
        asset = asset.upper()
        all_results[asset] = {}
        
        candidate_info = RESCUE_CANDIDATES.get(asset, {})
        print(f"\n📦 Asset: {asset}")
        print(f"   Reason for rescue: {candidate_info.get('reason', 'Unknown')}")
        
        best_result = None
        best_displacement = None
        best_sharpe = -999
        
        for disp in displacements:
            if dry_run:
                print(f"   [DRY RUN] Would test d{disp}")
                continue
            
            # Run optimization
            run_result = run_optimization_for_displacement(
                asset=asset,
                displacement=disp,
                trials=trials,
                workers=workers
            )
            
            all_results[asset][f"d{disp}"] = run_result
            
            # Find and parse output
            output_file = find_latest_output(asset, disp)
            if output_file:
                parsed = parse_results(output_file)
                if parsed:
                    verdict = evaluate_rescue(parsed)
                    all_results[asset][f"d{disp}"]["parsed"] = parsed
                    all_results[asset][f"d{disp}"]["verdict"] = verdict
                    
                    # Track best
                    sharpe = parsed.get("sharpe_oos", -999)
                    if sharpe and sharpe > best_sharpe:
                        best_sharpe = sharpe
                        best_result = parsed
                        best_displacement = disp
        
        # Summary for asset
        if best_result:
            print(f"\n   🏆 Best result for {asset}: d{best_displacement}")
            print(f"      Sharpe: {best_result.get('sharpe_oos', 'N/A')}")
            print(f"      WFE: {best_result.get('wfe', 'N/A')}")
            print(f"      Verdict: {evaluate_rescue(best_result)}")
            all_results[asset]["best"] = {
                "displacement": best_displacement,
                "result": best_result,
                "verdict": evaluate_rescue(best_result)
            }
    
    # Final summary
    print("\n" + "="*80)
    print("RESCUE CAMPAIGN SUMMARY")
    print("="*80)
    
    rescued = []
    failed = []
    
    for asset, data in all_results.items():
        best = data.get("best", {})
        verdict = best.get("verdict", "NO_DATA")
        
        if verdict in ["PASS", "LIKELY_PASS"]:
            rescued.append(asset)
            print(f"✅ {asset}: RESCUED (d{best.get('displacement')})")
        else:
            failed.append(asset)
            print(f"❌ {asset}: NOT RESCUED ({verdict})")
    
    print(f"\nRescued: {len(rescued)}/{len(assets)}")
    print(f"Failed: {len(failed)}/{len(assets)}")
    
    # Save results
    output_dir = PROJECT_ROOT / "outputs"
    output_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = output_dir / f"phase3a_rescue_results_{timestamp}.json"
    
    with open(results_file, "w") as f:
        # Convert to serializable format
        serializable = {}
        for asset, data in all_results.items():
            serializable[asset] = {}
            for k, v in data.items():
                if isinstance(v, dict):
                    serializable[asset][k] = {kk: str(vv) if not isinstance(vv, (int, float, str, bool, type(None), dict, list)) else vv for kk, vv in v.items()}
                else:
                    serializable[asset][k] = str(v)
        json.dump(serializable, f, indent=2, default=str)
    
    print(f"\n📄 Results saved to: {results_file}")
    
    return all_results


def main():
    parser = argparse.ArgumentParser(
        description="Phase 3A Displacement Rescue for failed assets"
    )
    parser.add_argument(
        "--assets",
        nargs="+",
        default=list(RESCUE_CANDIDATES.keys()),
        help="Assets to rescue (default: OSMO AR METIS)"
    )
    parser.add_argument(
        "--displacements",
        nargs="+",
        type=int,
        default=DEFAULT_DISPLACEMENTS,
        help="Displacement values to test (default: 26 52 78)"
    )
    parser.add_argument(
        "--trials",
        type=int,
        default=300,
        help="Number of optimization trials (default: 300)"
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=1,
        help="Number of parallel workers (default: 1 for determinism)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without executing"
    )
    
    args = parser.parse_args()
    
    results = run_rescue_campaign(
        assets=[a.upper() for a in args.assets],
        displacements=args.displacements,
        trials=args.trials,
        workers=args.workers,
        dry_run=args.dry_run
    )
    
    print("\n" + "="*80)
    print("✅ PHASE 3A RESCUE COMPLETE")
    print("="*80)


if __name__ == "__main__":
    main()
