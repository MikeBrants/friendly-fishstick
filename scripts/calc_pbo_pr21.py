#!/usr/bin/env python3
"""
Calculate PBO for PR#21 assets (100 trials) using their returns matrices.

For ETH: Use existing CHALLENGER PBO
For others: Calculate from PR#21 returns_matrix files
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

# PR#21 assets (9 SUCCESS from scan)
PR21_ASSETS = ['ETH', 'EGLD', 'TON', 'HBAR', 'SUSHI', 'CRV', 'MINA', 'YGG', 'CAKE']

# PR#20 baseline (300T) for comparison
PR20_BASELINE = {
    'EGLD': 0.6667,
    'TON': 0.6667,
    'HBAR': 0.8667,
    'SUSHI': 0.7333,
    'CRV': 0.9333,
    'MINA': 0.7023,
    'YGG': 0.8413,
    'CAKE': 0.9821,
    'ETH': None  # Use CHALLENGER result
}

# CHALLENGER 100T results (already calculated)
CHALLENGER_100T = {
    'ETH': 0.1333,
    'BTC': 0.9333,
    'SOL': 0.3333,
    'AVAX': 0.1333
}

# PBO Thresholds
THRESHOLD_PASS = 0.50
THRESHOLD_QUARANTINE = 0.70

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
        output_path = Path("outputs") / f"{asset}_pbo_pr21_100t_{run_id}.json"
        
        result = {
            "guard": "pbo",
            "pass": pbo_value < THRESHOLD_PASS,
            "pbo": round(pbo_value, 4),
            "threshold": THRESHOLD_PASS,
            "interpretation": interpretation,
            "trials": 100,
            "source": "pr21_100trials",
            "n_combinations": returns.shape[0] if returns.ndim >= 2 else len(returns),
        }
        
        with open(output_path, 'w') as f:
            json.dump(result, f, indent=2)
        
        return {
            'asset': asset,
            'pbo': pbo_value,
            'verdict': verdict,
            'file': output_path.name,
            'status': 'OK'
        }
        
    except Exception as e:
        print(f"[ERROR] {asset}: {e}")
        return {
            'asset': asset,
            'pbo': None,
            'verdict': 'ERROR',
            'file': None,
            'status': 'ERROR'
        }

def main():
    """Main execution."""
    print("=" * 80)
    print("PR#21 PBO CALCULATION & CONSOLIDATION")
    print("100 Trials - Final Validation")
    print("=" * 80)
    
    results = []
    
    print(f"\n[INFO] Processing {len(PR21_ASSETS)} PR#21 assets")
    print("=" * 80)
    
    for asset in PR21_ASSETS:
        # Check if CHALLENGER result exists
        if asset in CHALLENGER_100T:
            print(f"\n[CACHED] {asset} - Using CHALLENGER result")
            pbo_100T = CHALLENGER_100T[asset]
            verdict = get_verdict(pbo_100T)
            print(f"  [OK] PBO: {pbo_100T:.4f} -> {verdict}")
            
            results.append({
                'asset': asset,
                'pbo_100T': pbo_100T,
                'pbo_300T': PR20_BASELINE.get(asset),
                'verdict_100T': verdict,
                'verdict_300T': get_verdict(PR20_BASELINE[asset]) if PR20_BASELINE.get(asset) else 'N/A',
                'source': 'CHALLENGER',
                'status': 'OK'
            })
            continue
        
        # Find PR#21 returns matrix (timestamp: 20260127_200936)
        pattern = f"outputs/returns_matrix_{asset}_20260127_200936.npy"
        files = glob.glob(pattern)
        
        if not files:
            print(f"\n[SKIP] {asset}: No PR#21 returns matrix found")
            results.append({
                'asset': asset,
                'pbo_100T': None,
                'pbo_300T': PR20_BASELINE.get(asset),
                'verdict_100T': 'NO_DATA',
                'verdict_300T': get_verdict(PR20_BASELINE[asset]) if PR20_BASELINE.get(asset) else 'N/A',
                'source': None,
                'status': 'SKIP'
            })
            continue
        
        returns_file = files[0]
        print(f"\n[CALC] {asset} (PR#21 100T)...")
        result = calc_pbo_for_asset(asset, returns_file)
        
        if result['status'] == 'OK':
            pbo_100T = result['pbo']
            pbo_300T = PR20_BASELINE.get(asset)
            verdict_100T = result['verdict']
            verdict_300T = get_verdict(pbo_300T) if pbo_300T is not None else 'N/A'
            
            marker = {
                'PASS': '[OK]',
                'QUARANTINE': '[!]',
                'EXCLU': '[X]'
            }.get(verdict_100T, '[?]')
            
            print(f"  {marker} PBO (100T): {pbo_100T:.4f} -> {verdict_100T}")
            
            if pbo_300T is not None:
                delta = pbo_100T - pbo_300T
                delta_pct = (delta / pbo_300T) * 100
                improvement = "IMPROVED" if delta < 0 else "DEGRADED"
                color_marker = "[+]" if delta < 0 else "[-]"
                print(f"      PBO (300T): {pbo_300T:.4f} -> {verdict_300T}")
                print(f"      {color_marker} Delta: {delta:+.4f} ({delta_pct:+.1f}%) - {improvement}")
            
            results.append({
                'asset': asset,
                'pbo_100T': pbo_100T,
                'pbo_300T': pbo_300T,
                'verdict_100T': verdict_100T,
                'verdict_300T': verdict_300T,
                'source': 'PR21',
                'status': 'OK'
            })
    
    # Summary
    print("\n" + "=" * 80)
    print("PR#21 PBO CONSOLIDATION SUMMARY")
    print("=" * 80)
    
    valid_results = [r for r in results if r['status'] == 'OK']
    
    print(f"\nTotal assets: {len(valid_results)}/{len(PR21_ASSETS)}")
    
    # Count verdicts for 100T
    pass_100T = sum(1 for r in valid_results if r['verdict_100T'] == 'PASS')
    quarantine_100T = sum(1 for r in valid_results if r['verdict_100T'] == 'QUARANTINE')
    exclu_100T = sum(1 for r in valid_results if r['verdict_100T'] == 'EXCLU')
    
    print("\n[100 TRIALS PR#21]")
    print(f"  PASS:       {pass_100T}/{len(valid_results)} ({pass_100T/len(valid_results)*100:.1f}%)")
    print(f"  QUARANTINE: {quarantine_100T}/{len(valid_results)} ({quarantine_100T/len(valid_results)*100:.1f}%)")
    print(f"  EXCLU:      {exclu_100T}/{len(valid_results)} ({exclu_100T/len(valid_results)*100:.1f}%)")
    
    # List by verdict
    if pass_100T > 0:
        pass_assets = [r['asset'] for r in valid_results if r['verdict_100T'] == 'PASS']
        print(f"\n[OK] PASS: {', '.join(pass_assets)}")
    
    if quarantine_100T > 0:
        q_assets = [r['asset'] for r in valid_results if r['verdict_100T'] == 'QUARANTINE']
        print(f"\n[!] QUARANTINE: {', '.join(q_assets)}")
    
    if exclu_100T > 0:
        exclu_assets = [r['asset'] for r in valid_results if r['verdict_100T'] == 'EXCLU']
        print(f"\n[X] EXCLU: {', '.join(exclu_assets)}")
    
    # Comparison with 300T
    valid_300T = [r for r in valid_results if r.get('pbo_300T') is not None]
    if valid_300T:
        print("\n[COMPARISON WITH 300T BASELINE]")
        improvements = [r for r in valid_300T if r['pbo_100T'] < r['pbo_300T']]
        degradations = [r for r in valid_300T if r['pbo_100T'] > r['pbo_300T']]
        unchanged = [r for r in valid_300T if r['pbo_100T'] == r['pbo_300T']]
        
        print(f"  Improved: {len(improvements)}/{len(valid_300T)}")
        print(f"  Degraded: {len(degradations)}/{len(valid_300T)}")
        print(f"  Unchanged: {len(unchanged)}/{len(valid_300T)}")
        
        if improvements:
            avg_improvement = np.mean([((r['pbo_300T'] - r['pbo_100T']) / r['pbo_300T'] * 100) 
                                       for r in improvements])
            print(f"\n  Average improvement: {avg_improvement:.1f}%")
    
    print("\n" + "=" * 80)
    print("[OK] PR#21 PBO analysis complete")
    print("=" * 80)

if __name__ == "__main__":
    main()
