"""Analyze consolidated PR#20 results across all batches."""
import pandas as pd
import glob
from pathlib import Path

print("="*80)
print("PR#20 CONSOLIDATED RESULTS")
print("="*80 + "\n")

# Collect all batch results
all_dfs = []
for batch_num in [1, 2, 3]:
    files = glob.glob(f"outputs/pr20_batch{batch_num}*_scan_*.csv")
    if files:
        latest = max(files, key=lambda p: Path(p).stat().st_mtime)
        df = pd.read_csv(latest)
        all_dfs.append(df)

if not all_dfs:
    print("No PR#20 results found!")
    exit(1)

# Consolidate
consolidated = pd.concat(all_dfs, ignore_index=True)
consolidated = consolidated.drop_duplicates(subset=['asset'], keep='last')

# Overall stats
total = len(consolidated)
success = (consolidated['status'] == 'SUCCESS').sum()
pass_rate = success / total * 100

print(f"Total Assets: {total}")
print(f"Successful: {success} ({pass_rate:.0f}%)")
print(f"Failed: {total - success}")
print(f"\nMean Sharpe: {consolidated['oos_sharpe'].mean():.2f}")
print(f"Mean WFE: {consolidated['wfe_pardo'].mean():.2f}")
print(f"Mean Trades: {consolidated['oos_trades'].mean():.0f}")

# Pre-PR#19 comparison
baselines = {
    'SHIB': {'sharpe': 5.67, 'wfe': 2.27},
    'DOT': {'sharpe': 4.82, 'wfe': 1.74},
    'TIA': {'sharpe': 5.16, 'wfe': 1.36},
    'NEAR': {'sharpe': 4.26, 'wfe': 1.69},
    'DOGE': {'sharpe': 3.88, 'wfe': 1.55},
    'ANKR': {'sharpe': 3.48, 'wfe': 0.86},
    'ETH': {'sharpe': 3.22, 'wfe': 1.22},
    'JOE': {'sharpe': 3.16, 'wfe': 0.73},
    'YGG': {'sharpe': 3.11, 'wfe': 0.78},
    'MINA': {'sharpe': 2.58, 'wfe': 1.13},
    'CAKE': {'sharpe': 2.46, 'wfe': 0.81},
    'RUNE': {'sharpe': 2.42, 'wfe': 0.61}
}

print("\n" + "="*80)
print("PRE vs POST PR#19 COMPARISON")
print("="*80)
print(f"\n{'Asset':<8} {'Post Sharpe':>11} {'Pre Sharpe':>10} {'Change':>8} {'Status':>8}")
print("-"*60)

for _, row in consolidated.iterrows():
    asset = row['asset']
    if asset in baselines:
        pre = baselines[asset]['sharpe']
        post = row['oos_sharpe']
        change = ((post - pre) / pre) * 100
        status = "PASS" if row['status'] == 'SUCCESS' else "FAIL"
        
        print(f"{asset:<8} {post:>11.2f} {pre:>10.2f} {change:>7.1f}% {status:>8}")

print("\n" + "="*80)

# Export
output_path = "outputs/PR20_CONSOLIDATED_RESULTS.csv"
consolidated.to_csv(output_path, index=False)
print(f"\n[OK] Exported: {output_path}\n")
