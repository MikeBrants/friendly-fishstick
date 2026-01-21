"""
Full Pipeline: Download -> Optimize -> Cluster -> Export
CODEX MULTI-ASSET-005 implementation

Usage:
    # Full pipeline (download + optimize + cluster)
    python scripts/run_full_pipeline.py --workers 8

    # Skip download if data already present
    python scripts/run_full_pipeline.py --skip-download --workers 8

    # Specific assets only
    python scripts/run_full_pipeline.py --assets HYPE AVAX SUI --workers 4
"""
import sys
import subprocess
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import argparse
from datetime import datetime


def main():
    parser = argparse.ArgumentParser(description="Multi-Asset Scan Pipeline (CODEX-005)")
    parser.add_argument(
        "--skip-download",
        action="store_true",
        help="Skip data download step"
    )
    parser.add_argument(
        "--skip-optimize",
        action="store_true",
        help="Skip optimization step (use existing scan results)"
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=None,
        help="Number of parallel workers (default: CPU count)"
    )
    parser.add_argument(
        "--assets",
        nargs="+",
        default=None,
        help="Specific assets to scan (default: all SCAN_ASSETS)"
    )
    parser.add_argument(
        "--scan-only",
        action="store_true",
        help="Only scan new alts (exclude BTC/ETH/XRP from download)"
    )
    parser.add_argument(
        "--trials-atr",
        type=int,
        default=100,
        help="Number of ATR optimization trials"
    )
    parser.add_argument(
        "--trials-ichi",
        type=int,
        default=100,
        help="Number of Ichimoku optimization trials"
    )
    parser.add_argument(
        "--enforce-tp-progression",
        action="store_true",
        dest="enforce_tp_progression",
        help="Enforce TP1 < TP2 < TP3 with minimum gap (default: on)"
    )
    parser.add_argument(
        "--no-enforce-tp-progression",
        action="store_false",
        dest="enforce_tp_progression",
        help="Allow non-progressive TP levels"
    )
    parser.add_argument(
        "--fixed-displacement",
        type=int,
        default=None,
        help="Fix Ichimoku displacement (and 5in1) to this value",
    )
    parser.add_argument(
        "--scan-results",
        type=str,
        default=None,
        help="Path to existing scan results (for clustering only)"
    )
    parser.add_argument(
        "--clusters",
        type=int,
        default=None,
        help="Force number of clusters (default: auto-detect)"
    )
    parser.add_argument(
        "--run-guards",
        action="store_true",
        help="Run guards after optimization using scan results",
    )
    parser.add_argument(
        "--guards-workers",
        type=int,
        default=None,
        help="Workers for guard runs (default: min(CPU-1, assets))",
    )
    parser.set_defaults(enforce_tp_progression=True)
    args = parser.parse_args()

    from crypto_backtest.config.scan_assets import SCAN_ASSETS
    optimize_assets = args.assets or SCAN_ASSETS

    timestamp = datetime.now().strftime("%Y%m%d_%H%M")

    print("=" * 70)
    print("MULTI-ASSET SCAN PIPELINE (CODEX-005)")
    print(f"Started: {datetime.now().isoformat()}")
    print("=" * 70)

    scan_path = args.scan_results

    # =========================================================================
    # STEP 1: Download Data
    # =========================================================================
    if not args.skip_download and not args.skip_optimize:
        print("\n" + "=" * 70)
        print("[STEP 1/3] DOWNLOADING OHLCV DATA")
        print("=" * 70)

        from scripts.download_data import download_all
        from crypto_backtest.config.scan_assets import SCAN_ASSETS, ALL_ASSETS

        if args.scan_only:
            download_assets = args.assets or SCAN_ASSETS
        else:
            download_assets = args.assets or ALL_ASSETS

        download_all(
            assets=download_assets,
            output_dir="data",
            days_back=730,
            format="parquet"
        )
    else:
        print("\n[STEP 1/3] Skipping download (--skip-download or --skip-optimize)")

    # =========================================================================
    # STEP 2: Parallel Optimization
    # =========================================================================
    if not args.skip_optimize:
        print("\n" + "=" * 70)
        print("[STEP 2/3] RUNNING PARALLEL OPTIMIZATION")
        print("=" * 70)

        from crypto_backtest.optimization.parallel_optimizer import run_parallel_scan

        scan_df = run_parallel_scan(
            assets=optimize_assets,
            data_dir="data",
            n_workers=args.workers,
            n_trials_atr=args.trials_atr,
            n_trials_ichi=args.trials_ichi,
            enforce_tp_progression=args.enforce_tp_progression,
            fixed_displacement=args.fixed_displacement,
        )

        # Find the most recent scan file
        from glob import glob
        scan_files = sorted(glob("outputs/multiasset_scan_*.csv"))
        if scan_files:
            scan_path = scan_files[-1]
    else:
        print("\n[STEP 2/3] Skipping optimization (--skip-optimize)")
        if not scan_path:
            # Find most recent scan results
            from glob import glob
            scan_files = sorted(glob("outputs/multiasset_scan_*.csv"))
            if scan_files:
                scan_path = scan_files[-1]
                print(f"Using existing scan results: {scan_path}")
            else:
                print("ERROR: No scan results found. Run without --skip-optimize first.")
                return

    # =========================================================================
    # STEP 3: Cluster Analysis
    # =========================================================================
    print("\n" + "=" * 70)
    print("[STEP 3/3] RUNNING CLUSTER ANALYSIS")
    print("=" * 70)

    if scan_path:
        from crypto_backtest.analysis.cluster_params import run_full_analysis
        cluster_info = run_full_analysis(scan_path, args.clusters)
    else:
        print("ERROR: No scan results available for clustering.")
        cluster_info = {}

    # =========================================================================
    # FINAL SUMMARY
    # =========================================================================
    print("\n" + "=" * 70)
    print("PIPELINE COMPLETE")
    print("=" * 70)

    # List output files
    from glob import glob

    print("\nOutput Files:")
    scan_files = sorted(glob("outputs/multiasset_scan_*.csv"))
    if scan_files:
        print(f"  - {scan_files[-1]} (scan results)")

    cluster_files = sorted(glob("outputs/cluster_analysis_*.json"))
    if cluster_files:
        print(f"  - {cluster_files[-1]} (cluster JSON)")

    config_files = sorted(glob("crypto_backtest/config/cluster_params_*.py"))
    if config_files:
        print(f"  - {config_files[-1]} (cluster config)")

    if Path("crypto_backtest/config/cluster_params.py").exists():
        print(f"  - crypto_backtest/config/cluster_params.py (latest config)")

    loss_files = sorted(glob("outputs/cluster_param_loss_*.csv"))
    if loss_files:
        print(f"  - {loss_files[-1]} (param loss)")

    # Stats
    if cluster_info:
        success_count = sum(1 for c in cluster_info.get("clusters", {}).values() for _ in c.get("assets", []))
        cluster_count = cluster_info.get("n_clusters", 0)
        silhouette = cluster_info.get("silhouette_score", 0)

        print(f"\nStats:")
        print(f"  - Assets scanned: {success_count}")
        print(f"  - Clusters found: {cluster_count}")
        print(f"  - Silhouette score: {silhouette:.3f}")

    print(f"\nFinished: {datetime.now().isoformat()}")

    if args.run_guards and scan_path:
        print("\n" + "=" * 70)
        print("[POST] RUNNING GUARDS")
        print("=" * 70)
        guard_workers = args.guards_workers or min(6, len(optimize_assets))
        guard_cmd = [
            sys.executable,
            str(Path(__file__).parent / "run_guards_multiasset.py"),
            "--assets",
            *optimize_assets,
            "--params-file",
            scan_path,
            "--workers",
            str(guard_workers),
        ]
        subprocess.run(guard_cmd, check=False)


if __name__ == "__main__":
    main()
