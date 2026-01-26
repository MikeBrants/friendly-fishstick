#!/usr/bin/env python3
"""Run Regime Analysis v3 on all PROD assets.

This script validates the new regime analysis system on the 14 production-ready
assets to verify SIDEWAYS profit distribution and regime stability.

Usage:
    python scripts/run_regime_prod_analysis.py --all-prod --export-report
    python scripts/run_regime_prod_analysis.py --assets ETH SHIB DOT
"""

import argparse
import sys
from pathlib import Path
from datetime import datetime
import warnings

warnings.filterwarnings("ignore")

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
import numpy as np

# PROD assets list (14 validated assets)
PROD_ASSETS = [
    "SHIB", "DOT", "TIA", "NEAR", "DOGE", "ANKR", "ETH",
    "JOE", "YGG", "MINA", "CAKE", "RUNE", "EGLD", "AVAX"
]

# WFE-based tiers for context
WFE_TIERS = {
    "SHIB": "extreme",
    "DOT": "extreme",
    "TIA": "moderate",
    "MINA": "moderate",
    "ETH": "moderate",
    "NEAR": "normal",
    "DOGE": "normal",
    "ANKR": "normal",
    "JOE": "normal",
    "YGG": "normal",
    "CAKE": "normal",
    "RUNE": "normal",
    "EGLD": "normal",
    "AVAX": "normal",
}


def load_ohlcv_data(asset: str) -> pd.DataFrame:
    """Load OHLCV data for an asset."""
    data_path = PROJECT_ROOT / "data" / f"{asset}_USDT_1h.parquet"
    
    if not data_path.exists():
        # Try alternative path
        data_path = PROJECT_ROOT / "data" / f"{asset}USDT_1h.parquet"
    
    if not data_path.exists():
        raise FileNotFoundError(f"Data file not found for {asset}")
    
    df = pd.read_parquet(data_path)
    
    # Ensure required columns
    required_cols = ["open", "high", "low", "close", "volume"]
    df.columns = df.columns.str.lower()
    
    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"Missing required column: {col}")
    
    return df


def analyze_single_asset(asset: str, use_hmm: bool = True) -> dict:
    """Run regime analysis on a single asset."""
    try:
        from crypto_backtest.analysis.regime_v3 import CryptoRegimeAnalyzer
    except ImportError:
        print(f"Warning: regime_v3 module not found, using fallback analysis")
        return analyze_single_asset_fallback(asset)
    
    print(f"\n{'='*60}")
    print(f"Analyzing: {asset} (WFE Tier: {WFE_TIERS.get(asset, 'unknown')})")
    print(f"{'='*60}")
    
    # Load data
    df = load_ohlcv_data(asset)
    print(f"Loaded {len(df)} bars")
    
    # Initialize analyzer
    analyzer = CryptoRegimeAnalyzer(use_hmm=use_hmm)
    
    # Fit and classify
    regimes = analyzer.fit_and_classify(df)
    
    # Calculate statistics
    stats = {
        "asset": asset,
        "total_bars": len(df),
        "wfe_tier": WFE_TIERS.get(asset, "unknown"),
    }
    
    # Trend regime distribution
    if "trend_regime" in regimes.columns:
        trend_dist = regimes["trend_regime"].value_counts(normalize=True) * 100
        for regime, pct in trend_dist.items():
            stats[f"trend_{regime.lower()}"] = round(pct, 2)
        
        # Calculate SIDEWAYS percentage (key metric)
        sideways_pct = trend_dist.get("SIDEWAYS", 0)
        stats["sideways_pct"] = round(sideways_pct, 2)
    
    # Volatility regime distribution
    if "volatility_regime" in regimes.columns:
        vol_dist = regimes["volatility_regime"].value_counts(normalize=True) * 100
        for regime, pct in vol_dist.items():
            stats[f"vol_{regime.lower()}"] = round(pct, 2)
    
    # Crypto regime distribution
    if "crypto_regime" in regimes.columns:
        crypto_dist = regimes["crypto_regime"].value_counts(normalize=True) * 100
        for regime, pct in crypto_dist.items():
            stats[f"crypto_{regime.lower()}"] = round(pct, 2)
    
    # Regime stability (average consecutive bars in same regime)
    if "trend_regime" in regimes.columns:
        regime_changes = (regimes["trend_regime"] != regimes["trend_regime"].shift(1)).sum()
        if regime_changes > 0:
            stability = len(regimes) / regime_changes
        else:
            stability = len(regimes)
        stats["regime_stability_bars"] = round(stability, 1)
    
    # Composite score statistics
    if "composite_score" in regimes.columns:
        stats["mean_composite_score"] = round(regimes["composite_score"].mean(), 3)
        stats["favorable_pct"] = round((regimes["composite_score"] > 0).mean() * 100, 1)
    
    # Print summary
    print(f"\n--- Results for {asset} ---")
    print(f"SIDEWAYS %: {stats.get('sideways_pct', 'N/A')}%")
    print(f"Regime Stability: {stats.get('regime_stability_bars', 'N/A')} bars")
    print(f"Favorable for Long: {stats.get('favorable_pct', 'N/A')}%")
    
    return stats


def analyze_single_asset_fallback(asset: str) -> dict:
    """Fallback analysis without regime_v3 module."""
    print(f"\n{'='*60}")
    print(f"Analyzing (fallback): {asset}")
    print(f"{'='*60}")
    
    df = load_ohlcv_data(asset)
    
    # Simple regime detection based on SMA
    close = df["close"]
    sma_50 = close.rolling(50).mean()
    sma_200 = close.rolling(200).mean()
    
    # Calculate ADX-like metric
    high = df["high"]
    low = df["low"]
    tr = pd.concat([
        high - low,
        (high - close.shift(1)).abs(),
        (low - close.shift(1)).abs()
    ], axis=1).max(axis=1)
    atr = tr.rolling(14).mean()
    
    # Simple regime classification
    bullish = (close > sma_50) & (sma_50 > sma_200)
    bearish = (close < sma_50) & (sma_50 < sma_200)
    sideways = ~bullish & ~bearish
    
    total = len(df)
    stats = {
        "asset": asset,
        "total_bars": total,
        "wfe_tier": WFE_TIERS.get(asset, "unknown"),
        "sideways_pct": round(sideways.sum() / total * 100, 2),
        "trend_bull": round(bullish.sum() / total * 100, 2),
        "trend_bear": round(bearish.sum() / total * 100, 2),
        "regime_stability_bars": "N/A (fallback)",
    }
    
    print(f"SIDEWAYS %: {stats['sideways_pct']}%")
    print(f"BULL %: {stats['trend_bull']}%")
    print(f"BEAR %: {stats['trend_bear']}%")
    
    return stats


def run_prod_analysis(assets: list, use_hmm: bool = True, export: bool = True) -> pd.DataFrame:
    """Run regime analysis on multiple assets."""
    results = []
    
    print("\n" + "="*80)
    print("REGIME ANALYSIS v3 — PROD ASSETS VALIDATION")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Assets: {len(assets)}")
    print("="*80)
    
    for asset in assets:
        try:
            stats = analyze_single_asset(asset, use_hmm=use_hmm)
            results.append(stats)
        except Exception as e:
            print(f"\n❌ Error analyzing {asset}: {e}")
            results.append({
                "asset": asset,
                "error": str(e),
                "wfe_tier": WFE_TIERS.get(asset, "unknown"),
            })
    
    # Create summary DataFrame
    df_results = pd.DataFrame(results)
    
    # Print summary table
    print("\n" + "="*80)
    print("SUMMARY — REGIME DISTRIBUTION")
    print("="*80)
    
    # Key columns for summary
    summary_cols = ["asset", "wfe_tier", "sideways_pct", "regime_stability_bars", "favorable_pct"]
    available_cols = [c for c in summary_cols if c in df_results.columns]
    
    print("\n" + df_results[available_cols].to_string(index=False))
    
    # Calculate aggregate statistics
    if "sideways_pct" in df_results.columns:
        valid_sideways = df_results["sideways_pct"].dropna()
        print(f"\n--- AGGREGATE STATS ---")
        print(f"Mean SIDEWAYS %: {valid_sideways.mean():.1f}%")
        print(f"Min SIDEWAYS %: {valid_sideways.min():.1f}%")
        print(f"Max SIDEWAYS %: {valid_sideways.max():.1f}%")
        
        # Check threshold (was 79.5% historically)
        target = 70.0
        passing = (valid_sideways >= target).sum()
        print(f"\nAssets with SIDEWAYS >= {target}%: {passing}/{len(valid_sideways)}")
    
    # Export results
    if export:
        output_dir = PROJECT_ROOT / "reports"
        output_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = output_dir / f"regime_v3_prod_analysis_{timestamp}.csv"
        df_results.to_csv(output_path, index=False)
        print(f"\n✅ Results exported to: {output_path}")
        
        # Generate markdown report
        report_path = output_dir / f"regime_v3_prod_analysis_{timestamp}.md"
        generate_markdown_report(df_results, report_path)
        print(f"✅ Report exported to: {report_path}")
    
    return df_results


def generate_markdown_report(df: pd.DataFrame, output_path: Path):
    """Generate markdown report from results."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    report = f"""# Regime Analysis v3 — PROD Assets Report

**Generated**: {timestamp}  
**Assets Analyzed**: {len(df)}

---

## Summary Table

| Asset | WFE Tier | SIDEWAYS % | Stability (bars) | Favorable % |
|-------|----------|------------|------------------|-------------|
"""
    
    for _, row in df.iterrows():
        asset = row.get("asset", "N/A")
        tier = row.get("wfe_tier", "N/A")
        sideways = row.get("sideways_pct", "N/A")
        stability = row.get("regime_stability_bars", "N/A")
        favorable = row.get("favorable_pct", "N/A")
        
        report += f"| {asset} | {tier} | {sideways}% | {stability} | {favorable}% |\n"
    
    # Aggregate stats
    if "sideways_pct" in df.columns:
        valid = df["sideways_pct"].dropna()
        report += f"""
---

## Aggregate Statistics

| Metric | Value |
|--------|-------|
| Mean SIDEWAYS % | {valid.mean():.1f}% |
| Min SIDEWAYS % | {valid.min():.1f}% |
| Max SIDEWAYS % | {valid.max():.1f}% |
| Std Dev | {valid.std():.1f}% |

---

## Recommendations

"""
        
        # Check thresholds
        if valid.mean() >= 70:
            report += "✅ **SIDEWAYS distribution healthy** — Mean above 70% threshold\n"
        else:
            report += "⚠️ **SIDEWAYS distribution below target** — Consider filter adjustments\n"
    
    report += f"""
---

## Next Steps

1. Verify SIDEWAYS profit contribution matches backtest results
2. Update guard007 if regime mismatch > 20%
3. Document any significant changes from previous analysis
4. Proceed to Phase 2 (Asset Rescue) if results acceptable

---

*Report generated automatically by run_regime_prod_analysis.py*
"""
    
    with open(output_path, "w") as f:
        f.write(report)


def main():
    parser = argparse.ArgumentParser(
        description="Run Regime Analysis v3 on PROD assets"
    )
    parser.add_argument(
        "--assets",
        nargs="+",
        help="Specific assets to analyze"
    )
    parser.add_argument(
        "--all-prod",
        action="store_true",
        help="Analyze all 14 PROD assets"
    )
    parser.add_argument(
        "--no-hmm",
        action="store_true",
        help="Disable HMM, use rule-based only"
    )
    parser.add_argument(
        "--export-report",
        action="store_true",
        default=True,
        help="Export results to CSV and markdown"
    )
    
    args = parser.parse_args()
    
    if args.all_prod:
        assets = PROD_ASSETS
    elif args.assets:
        assets = [a.upper() for a in args.assets]
    else:
        print("Error: Specify --all-prod or --assets")
        sys.exit(1)
    
    use_hmm = not args.no_hmm
    
    results = run_prod_analysis(
        assets=assets,
        use_hmm=use_hmm,
        export=args.export_report
    )
    
    print("\n" + "="*80)
    print("✅ REGIME ANALYSIS COMPLETE")
    print("="*80)


if __name__ == "__main__":
    main()
