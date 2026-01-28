"""
Monitor CHALLENGER 100-trials pipeline execution.

Usage:
    python scripts/monitor_challenger.py
"""

import glob
import time
from pathlib import Path
from datetime import datetime

def check_outputs():
    """Check for challenger output files."""
    print("\n" + "=" * 80)
    print("CHALLENGER PIPELINE MONITOR")
    print("=" * 80)
    
    # Check for any output files
    patterns = [
        "outputs/*challenger*.csv",
        "outputs/*challenger*.json",
        "outputs/multi_asset_scan_partial.csv",
    ]
    
    all_files = []
    for pattern in patterns:
        all_files.extend(glob.glob(pattern))
    
    if not all_files:
        print("\n[INFO] No output files found yet")
        print("[INFO] Pipeline likely downloading data or initializing...")
        return
    
    # Sort by modification time
    all_files.sort(key=lambda x: Path(x).stat().st_mtime, reverse=True)
    
    print("\n[FILES] Recent output files:")
    for f in all_files[:10]:
        p = Path(f)
        age = time.time() - p.stat().st_mtime
        size = p.stat().st_size / 1024
        print(f"  {p.name:50s} | {size:8.1f} KB | {age:5.0f}s ago")
    
    # Check partial scan file
    partial = Path("outputs/multi_asset_scan_partial.csv")
    if partial.exists():
        print("\n[PROGRESS] Scanning multi_asset_scan_partial.csv...")
        try:
            import pandas as pd
            df = pd.read_csv(partial)
            if not df.empty:
                completed = df['asset'].nunique()
                print(f"  Assets completed: {completed}")
                print(f"  Total entries: {len(df)}")
                
                if 'sharpe_oos' in df.columns and 'wfe' in df.columns:
                    recent = df.tail(5)[['asset', 'sharpe_oos', 'wfe', 'trades_oos']]
                    print("\n  Recent results:")
                    print(recent.to_string(index=False))
        except Exception as e:
            print(f"  [WARN] Could not parse: {e}")

def main():
    """Main execution."""
    check_outputs()
    
    print("\n" + "=" * 80)
    print("[INFO] Pipeline running with:")
    print("  Assets: BTC, ETH, SOL, AVAX")
    print("  Trials: 100 ATR + 100 Ichimoku")
    print("  Workers: 1 (sequential)")
    print("  Guards: ON")
    print("  Prefix: challenger_100trials")
    print("\n[ETA] ~2-3h for 4 assets with 100 trials each")
    print("=" * 80)

if __name__ == "__main__":
    main()
