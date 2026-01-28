"""
Calculate PBO for Batch 2 and Batch 3 assets.

Usage:
    python scripts/calc_pbo_batch23.py
"""

import json
import sys
import numpy as np
from pathlib import Path
from datetime import datetime

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Import PBO function
from crypto_backtest.validation.cpcv import calculate_pbo

# Assets
BATCH2_ASSETS = ['EGLD', 'AVAX', 'BTC', 'SOL']
BATCH3_ASSETS = ['HBAR', 'TON', 'SUSHI', 'CRV', 'ONE', 'SEI', 'AXS', 'AAVE', 'ZIL', 'GALA']

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
        output_path = Path("outputs") / f"{asset}_pbo_{run_id}.json"
        
        result = {
            "guard": "pbo",
            "pass": pbo_value < THRESHOLD_PASS,
            "pbo": round(pbo_value, 4),
            "threshold": THRESHOLD_PASS,
            "interpretation": interpretation,
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
    print("PBO CALCULATION - BATCH 2 & 3")
    print("=" * 80)
    
    all_assets = BATCH2_ASSETS + BATCH3_ASSETS
    results = []
    
    print(f"\n[INFO] Processing {len(all_assets)} assets")
    print(f"[INFO] Thresholds: PASS < {THRESHOLD_PASS}, QUARANTINE < {THRESHOLD_QUARANTINE}, EXCLU >= {THRESHOLD_QUARANTINE}")
    print("=" * 80)
    
    for asset in all_assets:
        # Find most recent returns matrix
        pattern = f"outputs/returns_matrix_{asset}_*.npy"
        import glob
        files = sorted(glob.glob(pattern))
        
        if not files:
            print(f"[SKIP] {asset}: No returns matrix found")
            results.append({
                'asset': asset,
                'pbo': None,
                'verdict': 'NO_DATA',
                'interpretation': 'Returns matrix not found',
                'file': None,
                'status': 'SKIP'
            })
            continue
        
        returns_file = files[-1]  # Most recent
        print(f"\n[CALC] {asset}...")
        result = calc_pbo_for_asset(asset, returns_file)
        results.append(result)
        
        if result['status'] == 'OK':
            marker = {
                'PASS': '[OK]',
                'QUARANTINE': '[!]',
                'EXCLU': '[X]'
            }.get(result['verdict'], '[?]')
            print(f"  {marker} PBO: {result['pbo']:.4f} -> {result['verdict']}")
            print(f"  {result['interpretation']}")
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    pass_count = sum(1 for r in results if r['verdict'] == 'PASS')
    quarantine_count = sum(1 for r in results if r['verdict'] == 'QUARANTINE')
    exclu_count = sum(1 for r in results if r['verdict'] == 'EXCLU')
    
    print(f"\nTotal: {len(results)} assets")
    print(f"  PASS:       {pass_count}")
    print(f"  QUARANTINE: {quarantine_count}")
    print(f"  EXCLU:      {exclu_count}")
    
    if pass_count > 0:
        pass_assets = [r['asset'] for r in results if r['verdict'] == 'PASS']
        print(f"\n[OK] PASS: {', '.join(pass_assets)}")
    
    if quarantine_count > 0:
        q_assets = [r['asset'] for r in results if r['verdict'] == 'QUARANTINE']
        print(f"\n[!] QUARANTINE: {', '.join(q_assets)}")
    
    if exclu_count > 0:
        exclu_assets = [r['asset'] for r in results if r['verdict'] == 'EXCLU']
        print(f"\n[X] EXCLU: {', '.join(exclu_assets)}")
    
    print("\n" + "=" * 80)
    print("[OK] PBO calculation complete")
    print("=" * 80)
    print(f"\nNext: python scripts/consolidate_pbo_results.py")

if __name__ == "__main__":
    main()
