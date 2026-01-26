#!/usr/bin/env python
"""Run regime analysis on specified assets.

Usage:
    python scripts/run_regime_analysis.py --assets ETH BTC SHIB
    python scripts/run_regime_analysis.py --assets ETH --export-stats
    python scripts/run_regime_analysis.py --all-prod
"""

import argparse
import sys
from pathlib import Path

import pandas as pd

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from crypto_backtest.analysis.regime_v3 import (
    CryptoRegimeAnalyzer,
    generate_regime_report,
)

# Production assets from project-state.md
PROD_ASSETS = [
    "SHIB", "DOT", "TIA", "NEAR", "DOGE", "ANKR", "ETH",
    "JOE", "YGG", "MINA", "CAKE", "RUNE", "EGLD", "AVAX",
]


def load_asset_data(asset: str) -> pd.DataFrame:
    """Load OHLCV data for an asset."""
    # Try multiple data paths
    data_paths = [
        project_root / f"data/{asset}USDT_1h.parquet",
        project_root / f"data/{asset}_USDT_1h.parquet",
        project_root / f"data/{asset.lower()}_usdt_1h.parquet",
    ]

    for path in data_paths:
        if path.exists():
            df = pd.read_parquet(path)
            # Ensure required columns
            required = ["open", "high", "low", "close"]
            if all(c in df.columns for c in required):
                return df
            # Try lowercase
            df.columns = df.columns.str.lower()
            if all(c in df.columns for c in required):
                return df

    raise FileNotFoundError(f"No data found for {asset}. Tried: {data_paths}")


def analyze_single_asset(
    asset: str, export_stats: bool = False, export_report: bool = False
) -> dict:
    """Run regime analysis on a single asset."""
    print(f"\n{'='*60}")
    print(f"Analyzing {asset}...")
    print(f"{'='*60}")

    try:
        df = load_asset_data(asset)
        print(f"Loaded {len(df)} bars")
    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        return {"asset": asset, "error": str(e)}

    # Run analysis
    analyzer = CryptoRegimeAnalyzer(use_hmm=True, n_hmm_regimes=3, lookback=200)
    regimes = analyzer.fit_and_classify(df)
    stats = analyzer.get_regime_stats()

    # Print summary
    print(f"\n--- REGIME DISTRIBUTION ---")
    print(f"\nTrend Regimes:")
    for regime, pct in sorted(stats["trend_distribution"].items(), key=lambda x: -x[1]):
        print(f"  {regime:15s}: {pct*100:5.1f}%")

    print(f"\nVolatility Regimes:")
    for regime, pct in sorted(stats["vol_distribution"].items(), key=lambda x: -x[1]):
        print(f"  {regime:15s}: {pct*100:5.1f}%")

    print(f"\nCrypto Regimes (Wyckoff):")
    for regime, pct in sorted(stats["crypto_distribution"].items(), key=lambda x: -x[1]):
        print(f"  {regime:15s}: {pct*100:5.1f}%")

    print(f"\n--- SUMMARY ---")
    print(f"  Mean Regime Stability: {stats['mean_stability']:.1f} bars")
    print(f"  % Favorable for Long:  {stats['pct_favorable_long']:.1f}%")
    print(f"  Mean Composite Score:  {stats['mean_composite_score']:.3f}")

    # Export if requested
    if export_stats:
        output_dir = project_root / "outputs" / "regime_analysis"
        output_dir.mkdir(parents=True, exist_ok=True)

        # Save regimes CSV
        csv_path = output_dir / f"{asset}_regimes.csv"
        regimes.to_csv(csv_path)
        print(f"\nExported: {csv_path}")

    if export_report:
        output_dir = project_root / "reports"
        output_dir.mkdir(parents=True, exist_ok=True)

        report_path = output_dir / f"regime_analysis_{asset}_{pd.Timestamp.now().strftime('%Y%m%d')}.md"
        report = generate_regime_report(df, asset, str(report_path))
        print(f"Generated report: {report_path}")

    return {"asset": asset, "stats": stats, "regimes": regimes}


def main():
    parser = argparse.ArgumentParser(description="Run crypto regime analysis")
    parser.add_argument(
        "--assets",
        nargs="+",
        help="Assets to analyze (e.g., ETH BTC SHIB)",
    )
    parser.add_argument(
        "--all-prod",
        action="store_true",
        help="Analyze all production assets",
    )
    parser.add_argument(
        "--export-stats",
        action="store_true",
        help="Export regime classifications to CSV",
    )
    parser.add_argument(
        "--export-report",
        action="store_true",
        help="Generate markdown analysis report",
    )

    args = parser.parse_args()

    # Determine assets to analyze
    if args.all_prod:
        assets = PROD_ASSETS
    elif args.assets:
        assets = [a.upper() for a in args.assets]
    else:
        print("ERROR: Specify --assets or --all-prod")
        parser.print_help()
        sys.exit(1)

    print(f"\n{'#'*60}")
    print(f"# CRYPTO REGIME ANALYSIS v3")
    print(f"# Assets: {', '.join(assets)}")
    print(f"{'#'*60}")

    # Analyze each asset
    results = []
    for asset in assets:
        result = analyze_single_asset(
            asset,
            export_stats=args.export_stats,
            export_report=args.export_report,
        )
        results.append(result)

    # Summary table
    print(f"\n\n{'='*60}")
    print("SUMMARY TABLE")
    print(f"{'='*60}")
    print(f"\n{'Asset':8s} | {'Favorable%':10s} | {'Stability':10s} | {'Score':8s}")
    print("-" * 45)

    for r in results:
        if "error" in r:
            print(f"{r['asset']:8s} | ERROR: {r['error'][:30]}")
        else:
            s = r["stats"]
            print(
                f"{r['asset']:8s} | {s['pct_favorable_long']:10.1f}% | {s['mean_stability']:10.1f} | {s['mean_composite_score']:8.3f}"
            )

    print(f"\n✅ Analysis complete for {len(results)} assets")


if __name__ == "__main__":
    main()
