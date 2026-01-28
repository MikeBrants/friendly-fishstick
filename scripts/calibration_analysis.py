#!/usr/bin/env python3
"""
Calibration Data Analysis Script
Extracts holding period, dataset info, and returns format for CSCV calibration.
"""

import pandas as pd
import numpy as np
from pathlib import Path

print("=" * 80)
print("CALIBRATION DATA ANALYSIS")
print("=" * 80)

# 1. Holding Period Analysis
print("\n1. HOLDING PERIOD ANALYSIS")
print("-" * 80)
trades_files = list(Path('outputs').glob('*trades*.csv'))
print(f"Found {len(trades_files)} trades files")

trades_files = [f for f in trades_files if f.stat().st_size > 0]
print(f"Non-empty files: {len(trades_files)}")

hp_results = []
for tf in trades_files[:10]:  # Analyze up to 10 files
    try:
        t = pd.read_csv(tf)
        
        # Try different column name patterns
        if 'exit_bar' in t.columns and 'entry_bar' in t.columns:
            hp = t['exit_bar'] - t['entry_bar']
            hp_results.extend(hp.tolist())
            print(f"  {tf.name}: {len(hp)} trades (bar-based)")
        elif 'exit_time' in t.columns and 'entry_time' in t.columns:
            # Calculate holding period in hours (1H bars)
            t['entry_time'] = pd.to_datetime(t['entry_time'])
            t['exit_time'] = pd.to_datetime(t['exit_time'])
            hp_hours = (t['exit_time'] - t['entry_time']).dt.total_seconds() / 3600
            hp_results.extend(hp_hours.tolist())
            print(f"  {tf.name}: {len(hp_hours)} trades (time-based, {hp_hours.mean():.1f}h avg)")
        else:
            print(f"  {tf.name}: No entry/exit columns found")
    except Exception as e:
        print(f"  {tf.name}: Error - {e}")

if hp_results:
    hp_arr = np.array(hp_results)
    print(f"\nTotal trades analyzed: {len(hp_arr)}")
    print(f"P50 (median): {np.median(hp_arr):.0f} bars")
    print(f"P95: {np.percentile(hp_arr, 95):.0f} bars")
    print(f"P99: {np.percentile(hp_arr, 99):.0f} bars")
    print(f"Min: {hp_arr.min():.0f}, Max: {hp_arr.max():.0f}")
    print(f"Mean: {hp_arr.mean():.0f}, Std: {hp_arr.std():.0f}")
else:
    print("No valid trades data found")

# 2. Dataset Analysis
print("\n2. DATASET ANALYSIS")
print("-" * 80)
ohlcv = list(Path('data').glob('*1h*.parquet'))
print(f"Found {len(ohlcv)} 1H parquet files")

if ohlcv:
    df = pd.read_parquet(ohlcv[0])
    print(f"File: {ohlcv[0].name}")
    print(f"Total bars: {len(df):,}")
    print(f"Period: {df.index.min()} -> {df.index.max()}")
    duration_days = (df.index.max() - df.index.min()).days
    print(f"Duration: {duration_days} days (~{duration_days/365:.1f} years)")
    print(f"Columns: {list(df.columns)}")
else:
    print("No 1H parquet files found")

# 3. Returns Format Analysis
print("\n3. RETURNS FORMAT ANALYSIS")
print("-" * 80)
npy = list(Path('outputs').glob('*returns_matrix*.npy'))
print(f"Found {len(npy)} returns matrix files")

if npy:
    r = np.load(npy[0])
    print(f"File: {npy[0].name}")
    print(f"Shape: {r.shape} (trials x bars)")
    print(f"Total elements: {r.size:,}")
    
    # Analyze first trial
    nz_first = np.count_nonzero(r[0])
    print(f"\nFirst trial analysis:")
    print(f"  Non-zero: {nz_first}/{r.shape[1]} ({100*nz_first/r.shape[1]:.1f}%)")
    
    # Analyze multiple trials
    n_trials_to_check = min(10, r.shape[0])
    nz_per_trial = [np.count_nonzero(r[i]) for i in range(n_trials_to_check)]
    print(f"\nSample of {n_trials_to_check} trials:")
    print(f"  Mean non-zero per trial: {np.mean(nz_per_trial):.0f}")
    print(f"  Std non-zero per trial: {np.std(nz_per_trial):.0f}")
    print(f"  Min: {np.min(nz_per_trial):.0f}, Max: {np.max(nz_per_trial):.0f}")
    
    # Overall sparsity
    total_nz = np.count_nonzero(r)
    sparsity = 100 * total_nz / r.size
    print(f"\nOverall sparsity: {sparsity:.2f}% non-zero")
    
    # Determine format
    avg_nonzero_pct = np.mean([100 * nz / r.shape[1] for nz in nz_per_trial])
    if avg_nonzero_pct < 30:
        format_type = "Bar-level (sparse, ~5-20% non-zero)"
    else:
        format_type = "Trade-level (dense, ~100% non-zero)"
    
    print(f"\nFormat: {format_type}")
    print(f"  T = {r.shape[1]} bars")
    print(f"  Average non-zero: ~{avg_nonzero_pct:.1f}%")
else:
    print("No returns matrix files found")

# Summary
print("\n" + "=" * 80)
print("CALIBRATION TEMPLATE")
print("=" * 80)
print("""
CALIBRATION REQUEST
==================

1. Holding Period (1H bars):
   - P50: {:.0f} bars
   - P95: {:.0f} bars
   - P99: {:.0f} bars
   
2. Holdout Final:
   - [ ] Pas de holdout prévu
   - [ ] Holdout prévu: __ mois
   
3. Returns Format:
   - [{}] Bar-level (T = total bars, ~5-20% non-zero)
   - [{}] Trade-level (N = nombre trades, ~100% non-zero)
   
4. Dataset:
   - Total bars: {:,}
   - Periode: {} -> {}
""".format(
    np.median(hp_arr) if hp_results else 0,
    np.percentile(hp_arr, 95) if hp_results else 0,
    np.percentile(hp_arr, 99) if hp_results else 0,
    "X" if npy and avg_nonzero_pct < 30 else " ",
    "X" if npy and avg_nonzero_pct >= 30 else " ",
    len(df) if ohlcv else 0,
    df.index.min() if ohlcv else "N/A",
    df.index.max() if ohlcv else "N/A"
))

print("\n" + "=" * 80)
