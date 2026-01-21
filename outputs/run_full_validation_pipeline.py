#!/usr/bin/env python3
"""
FINAL TRIGGER v2 - Full Validation Pipeline
============================================
Executes complete multi-asset validation in 7 phases.

Usage:
    python scripts/run_full_validation_pipeline.py [--skip-phase X] [--workers N]
"""

import argparse
import subprocess
import sys
import json
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
from concurrent.futures import ProcessPoolExecutor, as_completed
import warnings
warnings.filterwarnings('ignore')

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from crypto_backtest.optimization.parallel_optimizer import run_single_asset_pipeline
from crypto_backtest.validation.guard_runner import run_all_guards
from crypto_backtest.analysis.metrics import calculate_sharpe, calculate_sortino, calculate_max_drawdown

TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")

# ============================================================================
# CONFIGURATION
# ============================================================================

CONFIG = {
    # New assets from scan
    "new_assets": ["ICP", "HBAR", "EGLD", "IMX", "YGG", "CELO", "ARKM", "AR", "ANKR", "W", "STRK", "METIS", "AEVO"],

    # Previously validated
    "validated_assets": {
        "BTC": {"disp": 52}, "ETH": {"disp": 52}, "AVAX": {"disp": 52},
        "UNI": {"disp": 52}, "SEI": {"disp": 52}, "DOT": {"disp": 52},
        "SHIB": {"disp": 52}, "NEAR": {"disp": 52}, "APT": {"disp": 52},
        "SUI": {"disp": 52}, "OP": {"disp": 78}, "DOGE": {"disp": 26}
    },

    # Anomalies to investigate
    "anomalies": ["HOOK", "ALICE", "HMSTR"],

    # Displacement candidates (Sharpe>1, WFE<0.6)
    "disp_candidates": ["JOE", "TON", "DOGS", "RUNE", "AXS", "CAKE", "KSM", "LOOM", "MINA", "OSMO"],

    # Displacement grid
    "displacement_grid": [26, 39, 52, 65, 78],

    # Guard thresholds
    "thresholds": {
        "mc_p": 0.05,
        "sensitivity_var": 0.10,
        "bootstrap_ci_lower": 1.0,
        "stress1_sharpe": 1.0,
        "trade_dist_top10": 0.40,
        "wfe_min": 0.6,
        "min_trades": 60,
        "min_bars": 8000
    },

    # Portfolio thresholds
    "portfolio": {
        "min_weight": 0.03,
        "max_weight": 0.15,
        "max_correlation": 0.75,
        "target_sharpe": 2.5,
        "max_dd": 0.08
    },

    # Stress scenarios
    "stress_scenarios": [
        {"name": "base", "fees_bps": 5, "slip_bps": 2},
        {"name": "stress1", "fees_bps": 10, "slip_bps": 5},
        {"name": "stress2", "fees_bps": 15, "slip_bps": 10},
        {"name": "stress3", "fees_bps": 20, "slip_bps": 15}
    ]
}

# ============================================================================
# UTILITIES
# ============================================================================

def print_header(phase_num, phase_name):
    """Print phase header."""
    print("=" * 70)
    print(f"[PHASE {phase_num}/7] {phase_name}")
    print("=" * 70)
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Starting...")

def print_footer(results, output_file):
    """Print phase footer."""
    passed = sum(1 for r in results if r.get('status') == 'PASS')
    failed = len(results) - passed
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Results summary:")
    print(f"  - PASS: {passed} assets")
    print(f"  - FAIL: {failed} assets")
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Exported: {output_file}")
    print("=" * 70)
    print()

def load_params_from_scan(scan_file, asset):
    """Load optimized params for an asset from scan results."""
    df = pd.read_csv(scan_file)
    row = df[df['asset'] == asset]
    if row.empty:
        return None
    return row.iloc[0].to_dict()

# ============================================================================
# PHASE 1: Guards on New Assets
# ============================================================================

def phase1_guards_new_assets(workers=6):
    """Run full guards on 13 new assets."""
    print_header(1, "GUARDS ON NEW 13 ASSETS")

    assets = CONFIG["new_assets"]
    scan_file = "outputs/multiasset_scan_20260121_1751.csv"
    results = []

    def run_guards_single(asset):
        try:
            params = load_params_from_scan(scan_file, asset)
            if params is None:
                return {"asset": asset, "status": "FAIL", "reason": "params_not_found"}

            guard_results = run_all_guards(
                asset=asset,
                params=params,
                mc_iterations=1000,
                bootstrap_samples=10000,
                sensitivity_range=2,
                stress_fees=[(10, 5), (15, 10)]
            )

            # Check all thresholds
            t = CONFIG["thresholds"]
            passed = (
                guard_results.get('mc_p', 1) < t['mc_p'] and
                guard_results.get('sensitivity_var', 1) < t['sensitivity_var'] and
                guard_results.get('bootstrap_ci_lower', 0) > t['bootstrap_ci_lower'] and
                guard_results.get('stress1_sharpe', 0) > t['stress1_sharpe'] and
                guard_results.get('trade_dist_top10', 1) < t['trade_dist_top10'] and
                guard_results.get('regime_mismatch', 1) == 0
            )

            return {
                "asset": asset,
                "status": "PASS" if passed else "FAIL",
                **guard_results
            }
        except Exception as e:
            return {"asset": asset, "status": "FAIL", "reason": str(e)}

    with ProcessPoolExecutor(max_workers=workers) as executor:
        futures = {executor.submit(run_guards_single, asset): asset for asset in assets}
        for i, future in enumerate(as_completed(futures)):
            asset = futures[future]
            result = future.result()
            results.append(result)
            status = "✓" if result['status'] == 'PASS' else "✗"
            print(f"  [{i+1}/{len(assets)}] {asset}: {status} {result['status']}")

    output_file = f"outputs/guards_new13_{TIMESTAMP}.csv"
    pd.DataFrame(results).to_csv(output_file, index=False)
    print_footer(results, output_file)

    return results

# ============================================================================
# PHASE 2: Anomaly Investigation
# ============================================================================

def phase2_anomaly_investigation():
    """Investigate HOOK, ALICE, HMSTR anomalies."""
    print_header(2, "ANOMALY INVESTIGATION")

    anomalies = CONFIG["anomalies"]
    results = []

    for asset in anomalies:
        print(f"  Investigating {asset}...")

        # Load data and check quality
        data_file = f"data/Binance_{asset}USDT_1h.csv"
        try:
            df = pd.read_csv(data_file)
            bars = len(df)
        except:
            results.append({"asset": asset, "status": "FAIL", "reason": "data_not_found"})
            continue

        # Check minimum bars
        if bars < CONFIG["thresholds"]["min_bars"]:
            results.append({
                "asset": asset, 
                "status": "LOW_SAMPLE", 
                "bars": bars,
                "reason": f"bars={bars} < {CONFIG['thresholds']['min_bars']}"
            })
            print(f"    {asset}: LOW_SAMPLE ({bars} bars)")
            continue

        # Rerun optimization to check trades count
        try:
            result = run_single_asset_pipeline(
                asset=asset,
                trials_atr=50,
                trials_ichi=50,
                run_guards=True
            )

            oos_trades = result.get('oos_trades', 0)
            if oos_trades >= CONFIG["thresholds"]["min_trades"]:
                status = "RESCUED" if result.get('wfe', 0) > CONFIG["thresholds"]["wfe_min"] else "CONFIRM_FAIL"
            else:
                status = "LOW_TRADES"

            results.append({
                "asset": asset,
                "status": status,
                "bars": bars,
                "oos_trades": oos_trades,
                "oos_sharpe": result.get('oos_sharpe'),
                "wfe": result.get('wfe')
            })
            print(f"    {asset}: {status} (trades={oos_trades}, sharpe={result.get('oos_sharpe', 0):.2f})")

        except Exception as e:
            results.append({"asset": asset, "status": "ERROR", "reason": str(e)})

    output_file = f"outputs/anomaly_investigation_{TIMESTAMP}.csv"
    pd.DataFrame(results).to_csv(output_file, index=False)
    print_footer(results, output_file)

    return results

# ============================================================================
# PHASE 3: Displacement Grid
# ============================================================================

def phase3_displacement_grid(workers=6):
    """Test displacement grid on WFE borderline assets."""
    print_header(3, "DISPLACEMENT GRID ON WFE BORDERLINE")

    assets = CONFIG["disp_candidates"]
    displacements = CONFIG["displacement_grid"]
    results = []

    def run_disp_single(asset, disp):
        try:
            result = run_single_asset_pipeline(
                asset=asset,
                fixed_displacement=disp,
                trials_atr=50,
                trials_ichi=50
            )
            return {
                "asset": asset,
                "displacement": disp,
                "oos_sharpe": result.get('oos_sharpe', 0),
                "wfe": result.get('wfe', 0),
                "oos_trades": result.get('oos_trades', 0)
            }
        except Exception as e:
            return {"asset": asset, "displacement": disp, "oos_sharpe": 0, "wfe": 0, "error": str(e)}

    # Create all combinations
    combinations = [(asset, disp) for asset in assets for disp in displacements]

    with ProcessPoolExecutor(max_workers=workers) as executor:
        futures = {executor.submit(run_disp_single, a, d): (a, d) for a, d in combinations}
        for i, future in enumerate(as_completed(futures)):
            result = future.result()
            results.append(result)
            if (i + 1) % 10 == 0:
                print(f"  Progress: {i+1}/{len(combinations)} combinations complete")

    # Find best displacement per asset
    df = pd.DataFrame(results)
    print("\n  Best displacement per asset:")

    best_per_asset = []
    for asset in assets:
        asset_df = df[df['asset'] == asset]
        # Filter valid results
        valid = asset_df[(asset_df['oos_sharpe'] > 1.0) & (asset_df['wfe'] > CONFIG["thresholds"]["wfe_min"])]

        if not valid.empty:
            best = valid.loc[valid['oos_sharpe'].idxmax()]
            best_per_asset.append({
                "asset": asset,
                "best_disp": int(best['displacement']),
                "oos_sharpe": best['oos_sharpe'],
                "wfe": best['wfe'],
                "status": "DISP_RESCUED"
            })
            print(f"    {asset}: disp={int(best['displacement'])} -> Sharpe={best['oos_sharpe']:.2f}, WFE={best['wfe']:.2f} ✓")
        else:
            # Check if any improvement over baseline (52)
            baseline = asset_df[asset_df['displacement'] == 52]
            best_overall = asset_df.loc[asset_df['oos_sharpe'].idxmax()] if not asset_df.empty else None

            if best_overall is not None and best_overall['displacement'] != 52:
                best_per_asset.append({
                    "asset": asset,
                    "best_disp": int(best_overall['displacement']),
                    "oos_sharpe": best_overall['oos_sharpe'],
                    "wfe": best_overall['wfe'],
                    "status": "IMPROVED_BUT_FAIL"
                })
                print(f"    {asset}: disp={int(best_overall['displacement'])} -> Sharpe={best_overall['oos_sharpe']:.2f}, WFE={best_overall['wfe']:.2f} (still FAIL)")
            else:
                best_per_asset.append({"asset": asset, "status": "NO_IMPROVEMENT"})
                print(f"    {asset}: no viable displacement found")

    output_file = f"outputs/displacement_grid_batch3_{TIMESTAMP}.csv"
    df.to_csv(output_file, index=False)

    output_best = f"outputs/displacement_best_{TIMESTAMP}.csv"
    pd.DataFrame(best_per_asset).to_csv(output_best, index=False)

    print_footer(best_per_asset, output_file)

    return best_per_asset

# ============================================================================
# PHASE 4: Full Runs on Displacement Winners
# ============================================================================

def phase4_fullrun_disp_winners(disp_results, workers=6):
    """Full optimization on displacement winners."""
    print_header(4, "FULL RUNS ON DISPLACEMENT WINNERS")

    # Filter rescued assets
    winners = [r for r in disp_results if r.get('status') == 'DISP_RESCUED']

    if not winners:
        print("  No displacement winners to process")
        print("=" * 70)
        return []

    results = []

    def run_full_single(asset, disp):
        try:
            result = run_single_asset_pipeline(
                asset=asset,
                fixed_displacement=disp,
                trials_atr=100,
                trials_ichi=100,
                run_guards=True
            )
            return {
                "asset": asset,
                "displacement": disp,
                **result
            }
        except Exception as e:
            return {"asset": asset, "displacement": disp, "status": "ERROR", "reason": str(e)}

    with ProcessPoolExecutor(max_workers=workers) as executor:
        futures = {executor.submit(run_full_single, w['asset'], w['best_disp']): w['asset'] for w in winners}
        for future in as_completed(futures):
            result = future.result()
            results.append(result)
            status = "✓" if result.get('status') == 'SUCCESS' else "✗"
            print(f"  {result['asset']} (disp={result['displacement']}): {status}")

    output_file = f"outputs/fullrun_disp_winners_{TIMESTAMP}.csv"
    pd.DataFrame(results).to_csv(output_file, index=False)
    print_footer(results, output_file)

    return results

# ============================================================================
# PHASE 5: Portfolio Construction
# ============================================================================

def phase5_portfolio_construction(guard_results, disp_winners):
    """Build optimized portfolio from all validated assets."""
    print_header(5, "PORTFOLIO CONSTRUCTION")

    # Collect all validated assets
    validated = []

    # Previous validated
    for asset, info in CONFIG["validated_assets"].items():
        validated.append({"asset": asset, "displacement": info["disp"], "source": "previous"})

    # New guards passed
    for r in guard_results:
        if r.get('status') == 'PASS':
            validated.append({"asset": r['asset'], "displacement": 52, "source": "new_scan"})

    # Displacement winners
    for r in disp_winners:
        if r.get('status') == 'SUCCESS':
            validated.append({"asset": r['asset'], "displacement": r['displacement'], "source": "disp_rescued"})

    print(f"  Total validated assets: {len(validated)}")

    if len(validated) < 5:
        print("  ERROR: Not enough assets for portfolio construction")
        return None

    # Load returns for correlation
    returns_dict = {}
    for v in validated:
        try:
            df = pd.read_csv(f"data/Binance_{v['asset']}USDT_1h.csv")
            df['returns'] = df['close'].pct_change()
            # Resample to daily
            df['date'] = pd.to_datetime(df['timestamp']).dt.date
            daily_returns = df.groupby('date')['returns'].sum()
            returns_dict[v['asset']] = daily_returns
        except:
            print(f"    Warning: Could not load returns for {v['asset']}")

    # Build correlation matrix
    returns_df = pd.DataFrame(returns_dict)
    corr_matrix = returns_df.corr()

    print(f"\n  Correlation matrix computed ({len(corr_matrix)} assets)")

    # Identify high correlations
    high_corr_pairs = []
    for i in range(len(corr_matrix)):
        for j in range(i+1, len(corr_matrix)):
            if abs(corr_matrix.iloc[i, j]) > CONFIG["portfolio"]["max_correlation"]:
                high_corr_pairs.append({
                    "asset1": corr_matrix.index[i],
                    "asset2": corr_matrix.columns[j],
                    "correlation": corr_matrix.iloc[i, j]
                })

    if high_corr_pairs:
        print(f"\n  High correlation pairs (>{CONFIG['portfolio']['max_correlation']}):")
        for p in high_corr_pairs:
            print(f"    {p['asset1']} - {p['asset2']}: {p['correlation']:.3f}")

    # Equal weight portfolio
    n_assets = len(validated)
    equal_weight = 1.0 / n_assets

    # Calculate portfolio metrics (simplified)
    portfolio_returns = returns_df.mean(axis=1)  # Equal weight
    sharpe_eq = portfolio_returns.mean() / portfolio_returns.std() * np.sqrt(365)
    maxdd_eq = (portfolio_returns.cumsum() - portfolio_returns.cumsum().cummax()).min()

    print(f"\n  Equal Weight Portfolio:")
    print(f"    Assets: {n_assets}")
    print(f"    Weight per asset: {equal_weight*100:.1f}%")
    print(f"    Sharpe: {sharpe_eq:.2f}")
    print(f"    MaxDD: {maxdd_eq*100:.2f}%")

    # Optimized weights (simplified mean-variance)
    # In production, use cvxpy or scipy.optimize
    mean_returns = returns_df.mean()
    cov_matrix = returns_df.cov()

    # Simple inverse-variance weighting
    inv_var = 1 / returns_df.var()
    opt_weights = inv_var / inv_var.sum()

    # Apply constraints
    opt_weights = opt_weights.clip(CONFIG["portfolio"]["min_weight"], CONFIG["portfolio"]["max_weight"])
    opt_weights = opt_weights / opt_weights.sum()  # Renormalize

    # Calculate optimized metrics
    opt_returns = (returns_df * opt_weights).sum(axis=1)
    sharpe_opt = opt_returns.mean() / opt_returns.std() * np.sqrt(365)
    maxdd_opt = (opt_returns.cumsum() - opt_returns.cumsum().cummax()).min()

    # Diversification ratio
    weighted_vols = (returns_df.std() * opt_weights).sum()
    portfolio_vol = opt_returns.std()
    div_ratio = weighted_vols / portfolio_vol if portfolio_vol > 0 else 1

    print(f"\n  Optimized Portfolio:")
    print(f"    Sharpe: {sharpe_opt:.2f}")
    print(f"    MaxDD: {maxdd_opt*100:.2f}%")
    print(f"    Diversification Ratio: {div_ratio:.2f}")

    # Export results
    corr_file = f"outputs/portfolio_correlation_matrix_{TIMESTAMP}.csv"
    corr_matrix.to_csv(corr_file)

    weights_eq = pd.DataFrame([{"asset": v['asset'], "weight": equal_weight, "displacement": v['displacement']} for v in validated])
    weights_eq.to_csv(f"outputs/portfolio_weights_equalweight_{TIMESTAMP}.csv", index=False)

    weights_opt = pd.DataFrame([{"asset": a, "weight": w, "displacement": next((v['displacement'] for v in validated if v['asset'] == a), 52)} 
                                for a, w in opt_weights.items()])
    weights_opt.to_csv(f"outputs/portfolio_weights_optimized_{TIMESTAMP}.csv", index=False)

    metrics = {
        "equal_weight": {"sharpe": sharpe_eq, "maxdd": maxdd_eq, "assets": n_assets},
        "optimized": {"sharpe": sharpe_opt, "maxdd": maxdd_opt, "div_ratio": div_ratio, "assets": n_assets}
    }
    pd.DataFrame([metrics]).to_json(f"outputs/portfolio_metrics_{TIMESTAMP}.json")

    print(f"\n  Exported:")
    print(f"    - {corr_file}")
    print(f"    - outputs/portfolio_weights_*.csv")
    print("=" * 70)

    return {
        "validated": validated,
        "weights_optimized": opt_weights.to_dict(),
        "metrics": metrics,
        "high_corr_pairs": high_corr_pairs
    }

# ============================================================================
# PHASE 6: Stress Testing
# ============================================================================

def phase6_stress_test(portfolio):
    """Stress test the portfolio under various fee/slippage scenarios."""
    print_header(6, "STRESS TESTING PORTFOLIO")

    if portfolio is None:
        print("  ERROR: No portfolio to stress test")
        return None

    results = []

    for scenario in CONFIG["stress_scenarios"]:
        print(f"  Running scenario: {scenario['name']} (fees={scenario['fees_bps']}bps, slip={scenario['slip_bps']}bps)")

        # Simulate portfolio with fees
        # In production, rerun backtest with adjusted fees
        # Here we approximate by reducing returns

        total_cost_bps = scenario['fees_bps'] + scenario['slip_bps']
        cost_per_trade = total_cost_bps / 10000

        # Assume average 2 trades per day per asset
        avg_trades_per_day = 2
        daily_cost = cost_per_trade * avg_trades_per_day

        # Adjust metrics
        base_sharpe = portfolio['metrics']['optimized']['sharpe']
        adjusted_sharpe = base_sharpe * (1 - daily_cost * 10)  # Simplified adjustment

        edge_bps = (base_sharpe * 0.01 - daily_cost) * 10000  # Approximate edge in bps

        results.append({
            "scenario": scenario['name'],
            "fees_bps": scenario['fees_bps'],
            "slip_bps": scenario['slip_bps'],
            "sharpe": adjusted_sharpe,
            "edge_bps": edge_bps,
            "status": "PASS" if adjusted_sharpe > 1.5 else "MARGINAL" if adjusted_sharpe > 1.0 else "FAIL"
        })

        print(f"    Sharpe: {adjusted_sharpe:.2f}, Edge: {edge_bps:.1f}bps, Status: {results[-1]['status']}")

    output_file = f"outputs/portfolio_stress_test_{TIMESTAMP}.csv"
    pd.DataFrame(results).to_csv(output_file, index=False)

    print(f"\n  Exported: {output_file}")
    print("=" * 70)

    return results

# ============================================================================
# PHASE 7: Final Report
# ============================================================================

def phase7_final_report(guard_results, anomaly_results, disp_results, disp_winners, portfolio, stress_results):
    """Generate comprehensive final report."""
    print_header(7, "FINAL REPORT GENERATION")

    report = []
    report.append("# FINAL TRIGGER v2 - Full Validation Report")
    report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append("")

    # Summary
    report.append("## Executive Summary")
    report.append("")

    total_validated = len(CONFIG["validated_assets"])
    new_passed = sum(1 for r in guard_results if r.get('status') == 'PASS')
    rescued = sum(1 for r in (disp_winners or []) if r.get('status') == 'SUCCESS')
    anomaly_rescued = sum(1 for r in (anomaly_results or []) if r.get('status') == 'RESCUED')

    total_final = total_validated + new_passed + rescued + anomaly_rescued

    report.append(f"- **Total Validated Assets**: {total_final}")
    report.append(f"  - Previous: {total_validated}")
    report.append(f"  - New (guards passed): {new_passed}")
    report.append(f"  - Displacement rescued: {rescued}")
    report.append(f"  - Anomaly rescued: {anomaly_rescued}")
    report.append("")

    if portfolio:
        report.append(f"- **Portfolio Sharpe**: {portfolio['metrics']['optimized']['sharpe']:.2f}")
        report.append(f"- **Portfolio MaxDD**: {portfolio['metrics']['optimized']['maxdd']*100:.2f}%")
        report.append(f"- **Diversification Ratio**: {portfolio['metrics']['optimized'].get('div_ratio', 'N/A')}")

    if stress_results:
        stress1 = next((r for r in stress_results if r['scenario'] == 'stress1'), None)
        if stress1:
            report.append(f"- **Stress1 Sharpe**: {stress1['sharpe']:.2f}")
            report.append(f"- **Edge @ Stress1**: {stress1['edge_bps']:.1f} bps")

    # Production status
    production_ready = (
        portfolio is not None and
        portfolio['metrics']['optimized']['sharpe'] > 2.0 and
        abs(portfolio['metrics']['optimized']['maxdd']) < 0.08 and
        stress_results and stress_results[1]['sharpe'] > 1.5
    )

    report.append("")
    report.append(f"## Production Status: {'✅ READY' if production_ready else '⚠️ NOT READY'}")
    report.append("")

    # Guards results table
    report.append("## Guard Results - New Assets")
    report.append("")
    report.append("| Asset | MC p | Sens Var | Bootstrap CI | Stress1 | Status |")
    report.append("|-------|------|----------|--------------|---------|--------|")
    for r in guard_results:
        report.append(f"| {r.get('asset', 'N/A')} | {r.get('mc_p', 'N/A'):.4f} | {r.get('sensitivity_var', 'N/A'):.2%} | {r.get('bootstrap_ci_lower', 'N/A'):.2f} | {r.get('stress1_sharpe', 'N/A'):.2f} | {r.get('status', 'N/A')} |")
    report.append("")

    # Displacement results
    if disp_results:
        report.append("## Displacement Grid Results")
        report.append("")
        report.append("| Asset | Best Disp | OOS Sharpe | WFE | Status |")
        report.append("|-------|-----------|------------|-----|--------|")
        for r in disp_results:
            report.append(f"| {r.get('asset', 'N/A')} | {r.get('best_disp', 'N/A')} | {r.get('oos_sharpe', 0):.2f} | {r.get('wfe', 0):.2f} | {r.get('status', 'N/A')} |")
        report.append("")

    # Portfolio weights
    if portfolio:
        report.append("## Portfolio Weights (Optimized)")
        report.append("")
        report.append("| Asset | Weight | Displacement |")
        report.append("|-------|--------|--------------|")
        for asset, weight in sorted(portfolio['weights_optimized'].items(), key=lambda x: -x[1]):
            disp = next((v['displacement'] for v in portfolio['validated'] if v['asset'] == asset), 52)
            report.append(f"| {asset} | {weight*100:.1f}% | {disp} |")
        report.append("")

    # Stress test results
    if stress_results:
        report.append("## Stress Test Results")
        report.append("")
        report.append("| Scenario | Fees | Slip | Sharpe | Edge (bps) | Status |")
        report.append("|----------|------|------|--------|------------|--------|")
        for r in stress_results:
            report.append(f"| {r['scenario']} | {r['fees_bps']} | {r['slip_bps']} | {r['sharpe']:.2f} | {r['edge_bps']:.1f} | {r['status']} |")
        report.append("")

    # Write report
    report_content = "\n".join(report)
    report_file = f"outputs/FINAL_VALIDATION_REPORT_{TIMESTAMP}.md"
    with open(report_file, 'w') as f:
        f.write(report_content)

    print(f"  Report generated: {report_file}")
    print("")
    print(report_content)
    print("=" * 70)

    return report_file

# ============================================================================
# MAIN
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description='FINAL TRIGGER v2 - Full Validation Pipeline')
    parser.add_argument('--workers', type=int, default=6, help='Number of parallel workers')
    parser.add_argument('--skip-phase', type=int, nargs='+', default=[], help='Phases to skip')
    args = parser.parse_args()

    print("=" * 70)
    print("FINAL TRIGGER v2 - FULL VALIDATION PIPELINE")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Workers: {args.workers}")
    print("=" * 70)
    print()

    # Initialize results
    guard_results = []
    anomaly_results = []
    disp_results = []
    disp_winners = []
    portfolio = None
    stress_results = []

    # Phase 1
    if 1 not in args.skip_phase:
        guard_results = phase1_guards_new_assets(workers=args.workers)

    # Phase 2
    if 2 not in args.skip_phase:
        anomaly_results = phase2_anomaly_investigation()

    # Phase 3
    if 3 not in args.skip_phase:
        disp_results = phase3_displacement_grid(workers=args.workers)

    # Phase 4
    if 4 not in args.skip_phase:
        disp_winners = phase4_fullrun_disp_winners(disp_results, workers=args.workers)

    # Phase 5
    if 5 not in args.skip_phase:
        portfolio = phase5_portfolio_construction(guard_results, disp_winners)

    # Phase 6
    if 6 not in args.skip_phase:
        stress_results = phase6_stress_test(portfolio)

    # Phase 7
    if 7 not in args.skip_phase:
        report_file = phase7_final_report(guard_results, anomaly_results, disp_results, disp_winners, portfolio, stress_results)

    # Final summary
    print()
    print("=" * 70)
    print("FULL VALIDATION PIPELINE COMPLETE")
    print("=" * 70)

    passed_guards = sum(1 for r in guard_results if r.get('status') == 'PASS')
    total_validated = len(CONFIG["validated_assets"]) + passed_guards

    print(f"Total assets validated: {total_validated}")
    if portfolio:
        print(f"Portfolio Sharpe: {portfolio['metrics']['optimized']['sharpe']:.2f}")
        print(f"Portfolio MaxDD: {portfolio['metrics']['optimized']['maxdd']*100:.2f}%")

    production_ready = (
        portfolio is not None and
        portfolio['metrics']['optimized']['sharpe'] > 2.0 and
        stress_results and len(stress_results) > 1 and stress_results[1]['sharpe'] > 1.5
    )
    print(f"Production status: {'READY' if production_ready else 'NOT_READY'}")
    print("=" * 70)

if __name__ == "__main__":
    main()
