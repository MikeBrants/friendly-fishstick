"""Quick status check for PR#20 batches."""
import glob
from pathlib import Path
from datetime import datetime

print("="*80)
print("PR#20 REVALIDATION - PROGRESS CHECK")
print("="*80)
print(f"\nCurrent time: {datetime.now().strftime('%H:%M:%S UTC')}\n")

# Check all batches
for batch_num in [1, 2, 3]:
    pattern = f"outputs/pr20_batch{batch_num}*_scan_*.csv"
    files = glob.glob(pattern)
    
    if files:
        latest = max(files, key=lambda p: Path(p).stat().st_mtime)
        import pandas as pd
        df = pd.read_csv(latest)
        
        success = (df['status'] == 'SUCCESS').sum()
        total = len(df)
        
        print(f"BATCH {batch_num}: {success}/{total} PASS ({success/total*100:.0f}%)")
        print(f"  File: {Path(latest).name}")
        print(f"  Mean Sharpe: {df['oos_sharpe'].mean():.2f}")
        print(f"  Mean WFE: {df['wfe_pardo'].mean():.2f}")
        
        for _, row in df.iterrows():
            status_icon = "PASS" if row['status'] == 'SUCCESS' else "FAIL"
            print(f"    [{status_icon}] {row['asset']:6} - Sharpe {row['oos_sharpe']:.2f}, WFE {row['wfe_pardo']:.2f}")
        print()
    else:
        print(f"BATCH {batch_num}: NOT STARTED\n")

print("="*80 + "\n")
