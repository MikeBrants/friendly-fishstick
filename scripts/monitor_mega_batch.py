"""Monitor PR#20 MEGA BATCH progress in real-time."""
import time
import glob
from pathlib import Path
from datetime import datetime
import sys

def check_progress():
    """Check current progress of mega batch."""
    pattern = "outputs/pr20_batch_complete*_scan_*.csv"
    files = glob.glob(pattern)
    
    if not files:
        return 0, None
    
    latest = max(files, key=lambda p: Path(p).stat().st_mtime)
    
    try:
        import pandas as pd
        df = pd.read_csv(latest)
        
        total = len(df)
        success = (df['status'] == 'SUCCESS').sum()
        
        return total, {
            'file': Path(latest).name,
            'total': total,
            'success': success,
            'fail': total - success,
            'pass_rate': success / total * 100 if total > 0 else 0,
            'mean_sharpe': df['oos_sharpe'].mean(),
            'mean_wfe': df['wfe_pardo'].mean(),
            'assets': df[['asset', 'status', 'oos_sharpe', 'wfe_pardo']].to_dict('records')
        }
    except Exception as e:
        return 0, None

def main():
    """Monitor loop."""
    target = 18
    print("="*80)
    print("PR#20 MEGA BATCH MONITOR")
    print("="*80)
    print(f"\nTarget: {target} assets")
    print("Checking every 10 minutes...\n")
    print("Press Ctrl+C to stop\n")
    
    try:
        while True:
            now = datetime.now().strftime('%H:%M:%S UTC')
            completed, data = check_progress()
            
            if completed == 0:
                print(f"[{now}] Waiting for first output... (0/{target})")
            elif data:
                pct = (completed / target) * 100
                print(f"\n[{now}] Progress: {completed}/{target} ({pct:.0f}%)")
                print(f"  PASS: {data['success']}, FAIL: {data['fail']} ({data['pass_rate']:.0f}% pass rate)")
                print(f"  Mean Sharpe: {data['mean_sharpe']:.2f}, Mean WFE: {data['mean_wfe']:.2f}")
                
                if completed >= target:
                    print("\n" + "="*80)
                    print("MEGA BATCH COMPLETE!")
                    print("="*80)
                    print("\nRun full analysis:")
                    print("  python scripts/analyze_pr20_consolidated.py")
                    break
            
            time.sleep(600)  # 10 minutes
            
    except KeyboardInterrupt:
        print("\n\nMonitoring stopped by user.")
        sys.exit(0)

if __name__ == "__main__":
    main()
