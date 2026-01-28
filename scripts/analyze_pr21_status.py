#!/usr/bin/env python3
"""Analyze PR#21 pipeline status and PBO results."""

import pandas as pd
import numpy as np

print("=" * 80)
print("PR#21 DETAILED STATUS REPORT")
print("=" * 80)

# Load data
scan = pd.read_csv('outputs/pr21_100trials_multiasset_scan_20260127_200936.csv')
guards = pd.read_csv('outputs/pr21_100trials_guards_pbo_final.csv')

# 1. Optimization Status
print("\n[1] OPTIMIZATION PHASE")
print("-" * 80)
success = scan[scan['status'] == 'SUCCESS']
fail = scan[scan['status'] == 'FAIL']
print(f"Status: COMPLETE (14/14 assets)")
print(f"Success: {len(success)}/14 ({len(success)/14*100:.0f}%)")
print(f"Fail: {len(fail)}/14 ({len(fail)/14*100:.0f}%)")

print("\nSuccess Assets:")
print(success[['asset', 'oos_sharpe', 'wfe_pardo', 'oos_trades']].to_string(index=False))

print("\nFail Assets:")
print(fail[['asset', 'fail_reason', 'oos_sharpe', 'wfe_pardo']].to_string(index=False))

# 2. Guards Status
print("\n[2] GUARDS VALIDATION")
print("-" * 80)
all_pass = guards[guards['all_pass'] == 'True']
print(f"All Guards PASS: {len(all_pass)}/{len(guards)} assets")
if len(all_pass) > 0:
    print(f"Assets: {', '.join(all_pass['asset'].tolist())}")

# 3. PBO Analysis
print("\n[3] PBO ANALYSIS (100 Trials)")
print("-" * 80)
pbo_assets = guards[guards['guard008_pbo'].notna() & (guards['guard008_pbo'] != '')]
print(f"Assets with PBO values: {len(pbo_assets)}")

if len(pbo_assets) > 0:
    print("\nPBO Values:")
    for _, row in pbo_assets.iterrows():
        pbo = float(row['guard008_pbo'])
        if pbo < 0.50:
            verdict = "PASS"
        elif pbo < 0.70:
            verdict = "QUARANTINE"
        else:
            verdict = "EXCLU"
        print(f"  {row['asset']:6s}: PBO={pbo:.4f} -> {verdict}")
    
    print("\nSummary:")
    pass_count = len(pbo_assets[pbo_assets['guard008_pbo'].astype(float) < 0.50])
    q_count = len(pbo_assets[(pbo_assets['guard008_pbo'].astype(float) >= 0.50) & 
                              (pbo_assets['guard008_pbo'].astype(float) < 0.70)])
    exclu_count = len(pbo_assets[pbo_assets['guard008_pbo'].astype(float) >= 0.70])
    print(f"  PASS (<0.50): {pass_count}")
    print(f"  QUARANTINE (0.50-0.70): {q_count}")
    print(f"  EXCLU (>0.70): {exclu_count}")

# 4. Comparison with PR#20 baseline (if available)
print("\n[4] COMPARISON WITH PR#20 (300 Trials)")
print("-" * 80)
pr20_baseline = {
    'TON': 0.6667, 'HBAR': 0.8667, 'EGLD': 0.6667, 'CRV': 0.9333,
    'SUSHI': 0.7333, 'CAKE': 0.9821, 'MINA': 0.7023, 'ETH': None,
    'YGG': 0.8413
}

if len(pbo_assets) > 0:
    print("\nPBO Comparison (300T vs 100T):")
    for _, row in pbo_assets.iterrows():
        asset = row['asset']
        pbo_100 = float(row['guard008_pbo'])
        pbo_300 = pr20_baseline.get(asset)
        
        if pbo_300 is not None:
            delta = pbo_100 - pbo_300
            delta_pct = (delta / pbo_300) * 100 if pbo_300 != 0 else 0
            change = "IMPROVED" if delta < 0 else ("DEGRADED" if delta > 0 else "NO CHANGE")
            print(f"  {asset:6s}: {pbo_300:.4f} -> {pbo_100:.4f} ({delta:+.4f}, {delta_pct:+.1f}%) - {change}")
        else:
            print(f"  {asset:6s}: N/A -> {pbo_100:.4f} (NEW TEST)")

# 5. Final Summary
print("\n[5] FINAL SUMMARY")
print("-" * 80)
print(f"Optimization: {len(success)}/14 SUCCESS")
print(f"Guards: {len(all_pass)}/9 PASS (all guards)")
print(f"PBO: {len(pbo_assets)} assets tested")
if len(pbo_assets) > 0:
    pbo_pass = len(pbo_assets[pbo_assets['guard008_pbo'].astype(float) < 0.50])
    print(f"  PBO PASS: {pbo_pass}/{len(pbo_assets)}")

print("\n" + "=" * 80)
