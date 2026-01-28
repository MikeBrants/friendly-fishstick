"""
Calculate PBO for CHALLENGER 100-trials pipeline and compare with baseline 300-trials.

Usage:
    python scripts/calc_pbo_challenger.py
"""

import json
import sys
import glob
import numpy as np
from pathlib import Path
from datetime import datetime

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Import PBO function
from crypto_backtest.validation.cpcv import calculate_pbo

# Assets
CHALLENGER_ASSETS = ['BTC', 'ETH', 'SOL', 'AVAX']

# PBO Thresholds
THRESHOLD_PASS = 0.50
THRESHOLD_QUARANTINE = 0.70

# Baseline 300T PBO values
BASELINE_300T = {
    'BTC': 0.9333,
    'SOL': 0.7333,
    'AVAX': 0.7333,
    'ETH': None  # Not tested in baseline
}

def get_verdict(pbo_value):
    """Determine verdict from PBO value."""
    if pbo_value < THRESHOLD_PASS:
        return "PASS"
    elif pbo_value < THRESHOLD_QUARANTINE:
        return "QUARANTINE"
    else:
        return "EXCLU"

def get_interpretation(pbo_value):
    """Get interpretation text."""
    if pbo_value < 0.30:
        return "LOW - Strong evidence against overfitting"
    elif pbo_value < 0.50:
        return "ACCEPTABLE - Moderate confidence"
    elif pbo_value < 0.70:
        return "ELEVATED - Overfitting concerns"
    else:
        return "CRITICAL - Best IS params almost certainly overfit"

def calc_pbo_for_asset(asset, returns_file):
    """Calculate PBO for a single asset."""
    try:
        # Load returns matrix
        returns = np.load(returns_file)
        
        # Calculate PBO
        pbo_value = float(calculate_pbo(returns))
        
        # Determine verdict
        verdict = get_verdict(pbo_value)
        interpretation = get_interpretation(pbo_value)
        
        # Save JSON
        run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = Path("outputs") / f"{asset}_pbo_challenger100_{run_id}.json"
        
        result = {
            "guard": "pbo",
            "pass": pbo_value < THRESHOLD_PASS,
            "pbo": round(pbo_value, 4),
            "threshold": THRESHOLD_PASS,
            "interpretation": interpretation,
            "trials": 100,
            "n_combinations": returns.shape[0] if returns.ndim >= 2 else len(returns),
        }
        
        with open(output_path, 'w') as f:
            json.dump(result, f, indent=2)
        
        return {
            'asset': asset,
            'pbo': pbo_value,
            'verdict': verdict,
            'interpretation': interpretation,
            'file': output_path.name,
            'status': 'OK'
        }
        
    except Exception as e:
        print(f"[ERROR] {asset}: {e}")
        return {
            'asset': asset,
            'pbo': None,
            'verdict': 'ERROR',
            'interpretation': str(e),
            'file': None,
            'status': 'ERROR'
        }

def main():
    """Main execution."""
    print("=" * 80)
    print("CHALLENGER PBO CALCULATION & COMPARISON")
    print("100 trials vs 300 trials baseline")
    print("=" * 80)
    
    results = []
    
    print(f"\n[INFO] Processing {len(CHALLENGER_ASSETS)} assets (100 trials)")
    print(f"[INFO] Thresholds: PASS < {THRESHOLD_PASS}, QUARANTINE < {THRESHOLD_QUARANTINE}, EXCLU >= {THRESHOLD_QUARANTINE}")
    print("=" * 80)
    
    for asset in CHALLENGER_ASSETS:
        # Find most recent CHALLENGER returns matrix
        pattern = f"outputs/returns_matrix_{asset}_20260127_172257.npy"
        files = glob.glob(pattern)
        
        if not files:
            # Fallback to any recent file
            pattern = f"outputs/returns_matrix_{asset}_*.npy"
            files = sorted(glob.glob(pattern))
        
        if not files:
            print(f"\n[SKIP] {asset}: No returns matrix found")
            results.append({
                'asset': asset,
                'pbo_100T': None,
                'pbo_300T': BASELINE_300T.get(asset),
                'verdict_100T': 'NO_DATA',
                'verdict_300T': get_verdict(BASELINE_300T[asset]) if BASELINE_300T.get(asset) else 'N/A',
                'delta': None,
                'status': 'SKIP'
            })
            continue
        
        returns_file = files[-1]  # Most recent
        print(f"\n[CALC] {asset} (100 trials)...")
        result = calc_pbo_for_asset(asset, returns_file)
        
        if result['status'] == 'OK':
            pbo_100T = result['pbo']
            pbo_300T = BASELINE_300T.get(asset)
            
            verdict_100T = result['verdict']
            verdict_300T = get_verdict(pbo_300T) if pbo_300T is not None else 'N/A'
            
            # Calculate delta
            if pbo_300T is not None:
                delta = pbo_100T - pbo_300T
                delta_pct = (delta / pbo_300T) * 100
            else:
                delta = None
                delta_pct = None
            
            marker = {
                'PASS': '[OK]',
                'QUARANTINE': '[!]',
                'EXCLU': '[X]'
            }.get(verdict_100T, '[?]')
            
            print(f"  {marker} PBO (100T): {pbo_100T:.4f} -> {verdict_100T}")
            if pbo_300T is not None:
                print(f"      PBO (300T): {pbo_300T:.4f} -> {verdict_300T}")
                if delta is not None:
                    improvement = "IMPROVED" if delta < 0 else "DEGRADED"
                    color_marker = "[+]" if delta < 0 else "[-]"
                    print(f"      {color_marker} Delta: {delta:+.4f} ({delta_pct:+.1f}%) - {improvement}")
            else:
                print(f"      PBO (300T): Not tested")
            
            results.append({
                'asset': asset,
                'pbo_100T': pbo_100T,
                'pbo_300T': pbo_300T,
                'verdict_100T': verdict_100T,
                'verdict_300T': verdict_300T,
                'delta': delta,
                'delta_pct': delta_pct,
                'status': 'OK'
            })
    
    # Summary
    print("\n" + "=" * 80)
    print("COMPARISON SUMMARY: 100T vs 300T")
    print("=" * 80)
    
    valid_results = [r for r in results if r['status'] == 'OK']
    
    print(f"\nTotal assets: {len(valid_results)}")
    
    # Count verdicts for 100T
    pass_100T = sum(1 for r in valid_results if r['verdict_100T'] == 'PASS')
    quarantine_100T = sum(1 for r in valid_results if r['verdict_100T'] == 'QUARANTINE')
    exclu_100T = sum(1 for r in valid_results if r['verdict_100T'] == 'EXCLU')
    
    # Count verdicts for 300T (excluding N/A)
    valid_300T = [r for r in valid_results if r['pbo_300T'] is not None]
    pass_300T = sum(1 for r in valid_300T if r['verdict_300T'] == 'PASS')
    quarantine_300T = sum(1 for r in valid_300T if r['verdict_300T'] == 'QUARANTINE')
    exclu_300T = sum(1 for r in valid_300T if r['verdict_300T'] == 'EXCLU')
    
    print("\n[100 TRIALS]")
    print(f"  PASS:       {pass_100T}/{len(valid_results)} ({pass_100T/len(valid_results)*100:.1f}%)")
    print(f"  QUARANTINE: {quarantine_100T}/{len(valid_results)} ({quarantine_100T/len(valid_results)*100:.1f}%)")
    print(f"  EXCLU:      {exclu_100T}/{len(valid_results)} ({exclu_100T/len(valid_results)*100:.1f}%)")
    
    if valid_300T:
        print("\n[300 TRIALS BASELINE]")
        print(f"  PASS:       {pass_300T}/{len(valid_300T)} ({pass_300T/len(valid_300T)*100:.1f}%)")
        print(f"  QUARANTINE: {quarantine_300T}/{len(valid_300T)} ({quarantine_300T/len(valid_300T)*100:.1f}%)")
        print(f"  EXCLU:      {exclu_300T}/{len(valid_300T)} ({exclu_300T/len(valid_300T)*100:.1f}%)")
    
    # Improvement analysis
    improvements = [r for r in results if r.get('delta') is not None and r['delta'] < 0]
    degradations = [r for r in results if r.get('delta') is not None and r['delta'] > 0]
    
    if improvements:
        print(f"\n[+] IMPROVED ({len(improvements)} assets):")
        for r in improvements:
            print(f"  {r['asset']:6s}: {r['pbo_300T']:.4f} -> {r['pbo_100T']:.4f} ({r['delta']:+.4f}, {r['delta_pct']:+.1f}%)")
    
    if degradations:
        print(f"\n[-] DEGRADED ({len(degradations)} assets):")
        for r in degradations:
            print(f"  {r['asset']:6s}: {r['pbo_300T']:.4f} -> {r['pbo_100T']:.4f} ({r['delta']:+.4f}, {r['delta_pct']:+.1f}%)")
    
    # Verdict changes
    verdict_upgrades = [r for r in valid_300T if r['verdict_300T'] != 'PASS' and r['verdict_100T'] == 'PASS']
    verdict_downgrades = [r for r in valid_300T if r['verdict_300T'] == 'PASS' and r['verdict_100T'] != 'PASS']
    
    if verdict_upgrades:
        print(f"\n[VERDICT UPGRADES] {len(verdict_upgrades)} assets:")
        for r in verdict_upgrades:
            print(f"  {r['asset']:6s}: {r['verdict_300T']} -> {r['verdict_100T']}")
    
    if verdict_downgrades:
        print(f"\n[VERDICT DOWNGRADES] {len(verdict_downgrades)} assets:")
        for r in verdict_downgrades:
            print(f"  {r['asset']:6s}: {r['verdict_300T']} -> {r['verdict_100T']}")
    
    # Hypothesis verdict
    print("\n" + "=" * 80)
    print("HYPOTHESIS VERDICT")
    print("=" * 80)
    
    if len(improvements) > len(degradations):
        print("\n[+] HYPOTHESIS CONFIRMED")
        print(f"    {len(improvements)}/{len(valid_300T)} assets improved PBO with 100 trials")
        print(f"    Average improvement: {np.mean([r['delta_pct'] for r in improvements]):.1f}%")
        print("\n[RECOMMENDATION] Consider rerunning ALL assets with 100 trials")
    elif len(improvements) == len(degradations):
        print("\n[=] HYPOTHESIS INCONCLUSIVE")
        print(f"    Equal improvements ({len(improvements)}) and degradations ({len(degradations)})")
        print("\n[RECOMMENDATION] Investigate other factors (filter modes, regime bias)")
    else:
        print("\n[-] HYPOTHESIS REJECTED")
        print(f"    Only {len(improvements)}/{len(valid_300T)} assets improved")
        print(f"    {len(degradations)} assets degraded")
        print("\n[RECOMMENDATION] Investigate other causes of high PBO")
    
    print("\n" + "=" * 80)
    print("[OK] CHALLENGER PBO analysis complete")
    print("=" * 80)

if __name__ == "__main__":
    main()
