"""
Example: Using RunManager for organized backtest outputs.

This script demonstrates how to use RunManager to keep track of
multiple backtest runs without overwriting previous results.
"""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from crypto_backtest.utils.run_manager import RunManager, Run
import pandas as pd


def example_1_create_new_run():
    """Example 1: Create a new run and save results."""
    print("=" * 60)
    print("Example 1: Creating a new run")
    print("=" * 60)

    # Create a new run
    run = RunManager.create_run(
        description="Initial BTC/ETH scan with default params",
        assets=["BTC", "ETH"],
        metadata={"config": "default", "displacement": 52}
    )

    print(f"✓ Created run: {run.run_id}")
    print(f"  Directory: {run.run_dir}")

    # Simulate scan results
    scan_df = pd.DataFrame({
        "asset": ["BTC", "ETH"],
        "oos_sharpe": [2.63, 7.12],
        "wfe": [1.23, 2.46],
        "status": ["PASS", "PASS"]
    })

    run.save_scan_results(scan_df)
    print(f"✓ Saved scan results")

    # Save optimal parameters for each asset
    btc_params = {
        "sl_atr_mult": 4.5,
        "tp_atr_mult": 4.25,
        "tenkan": 13,
        "kijun": 34,
        "displacement": 52
    }

    eth_params = {
        "sl_atr_mult": 5.0,
        "tp_atr_mult": 5.0,
        "tenkan": 7,
        "kijun": 26,
        "displacement": 52
    }

    run.save_params("BTC", btc_params)
    run.save_params("ETH", eth_params)
    print(f"✓ Saved params for BTC, ETH")

    # Simulate guards results
    guards_df = pd.DataFrame({
        "asset": ["BTC", "ETH"],
        "all_guards_pass": [True, True],
        "oos_sharpe": [2.63, 7.12],
        "wfe": [1.23, 2.46]
    })

    run.save_guards_summary(guards_df)
    print(f"✓ Saved guards summary")

    print(f"\nRun summary:")
    summary = run.get_summary()
    for key, value in summary.items():
        print(f"  {key}: {value}")

    return run.run_id


def example_2_list_and_load_runs():
    """Example 2: List all runs and load a specific one."""
    print("\n" + "=" * 60)
    print("Example 2: Listing and loading runs")
    print("=" * 60)

    # List all runs
    runs = RunManager.list_runs()
    print(f"Found {len(runs)} run(s):\n")

    for run in runs:
        summary = run.get_summary()
        print(f"  {run.run_id}")
        print(f"    Description: {summary['description']}")
        print(f"    Assets: {', '.join(summary['assets'])}")
        print(f"    Scan: {'✓' if summary['has_scan'] else '✗'}")
        print(f"    Guards: {'✓' if summary['has_guards'] else '✗'}")
        print(f"    Params: {summary['params_count']} assets")
        print()

    # Load the latest run
    if runs:
        latest = runs[0]
        print(f"Loading latest run: {latest.run_id}")

        scan_df = latest.load_scan_results()
        if scan_df is not None:
            print(f"\nScan results:")
            print(scan_df)

        params = latest.load_params("BTC")
        if params:
            print(f"\nBTC params:")
            for key, value in params.items():
                print(f"  {key}: {value}")


def example_3_compare_runs():
    """Example 3: Compare results across multiple runs."""
    print("\n" + "=" * 60)
    print("Example 3: Comparing runs")
    print("=" * 60)

    runs = RunManager.list_runs()

    if len(runs) < 2:
        print("Need at least 2 runs to compare. Skipping.")
        return

    print("Comparing BTC Sharpe across runs:\n")

    for run in runs[:3]:  # Compare top 3 most recent
        scan_df = run.load_scan_results()
        if scan_df is not None:
            btc_row = scan_df[scan_df['asset'] == 'BTC']
            if not btc_row.empty:
                sharpe = btc_row['oos_sharpe'].values[0]
                manifest = run.load_manifest()
                desc = manifest.get('description', 'No description')
                print(f"  {run.run_id}")
                print(f"    {desc}")
                print(f"    BTC Sharpe: {sharpe:.2f}\n")


def example_4_find_runs_by_asset():
    """Example 4: Find all runs that include a specific asset."""
    print("\n" + "=" * 60)
    print("Example 4: Finding runs with specific asset")
    print("=" * 60)

    asset = "BTC"
    runs = RunManager.find_runs_with_asset(asset)

    print(f"Found {len(runs)} run(s) with {asset}:\n")

    for run in runs:
        manifest = run.load_manifest()
        params = run.load_params(asset)
        print(f"  {run.run_id}")
        print(f"    {manifest.get('description', 'No description')}")
        if params:
            print(f"    Displacement: {params.get('displacement', 'N/A')}")
        print()


def example_5_workflow():
    """Example 5: Typical workflow."""
    print("\n" + "=" * 60)
    print("Example 5: Typical workflow")
    print("=" * 60)

    # Step 1: Start a new analysis
    print("\nStep 1: Create new run")
    run = RunManager.create_run(
        description="Displacement grid test [26-78]",
        assets=["BTC", "ETH", "AVAX"],
        metadata={"experiment": "displacement_grid"}
    )
    print(f"  Created: {run.run_id}")

    # Step 2: Save scan results
    print("\nStep 2: Save scan results")
    scan_df = pd.DataFrame({
        "asset": ["BTC", "ETH", "AVAX"],
        "oos_sharpe": [2.8, 7.5, 4.1],
        "wfe": [1.10, 2.50, 1.15],
        "displacement": [39, 52, 26]
    })
    run.save_scan_results(scan_df)
    print(f"  Saved scan.csv")

    # Step 3: Save params for passing assets
    print("\nStep 3: Save optimal params")
    for asset in ["BTC", "ETH", "AVAX"]:
        params = {"displacement": 52, "tenkan": 13, "kijun": 34}
        run.save_params(asset, params)
    print(f"  Saved params/ for 3 assets")

    # Step 4: Run guards
    print("\nStep 4: Save guards results")
    guards_df = pd.DataFrame({
        "asset": ["BTC", "ETH", "AVAX"],
        "all_guards_pass": [True, True, True]
    })
    run.save_guards_summary(guards_df)
    print(f"  Saved guards.csv")

    # Step 5: Review
    print("\nStep 5: Review results")
    summary = run.get_summary()
    print(f"  Run complete!")
    print(f"  - {summary['scan_assets_count']} assets scanned")
    print(f"  - {summary['guards_assets_count']} guards validated")
    print(f"  - {summary['params_count']} param sets saved")

    return run.run_id


if __name__ == "__main__":
    # Run examples
    print("\n" + "=" * 60)
    print("RunManager Usage Examples")
    print("=" * 60)

    # Clean up test runs if they exist
    import shutil
    test_dir = Path("outputs")
    if test_dir.exists():
        for d in test_dir.glob("run_*"):
            if d.is_dir():
                shutil.rmtree(d)

    # Run examples
    example_1_create_new_run()
    example_2_list_and_load_runs()
    example_5_workflow()
    example_3_compare_runs()
    example_4_find_runs_by_asset()

    print("\n" + "=" * 60)
    print("✓ All examples completed")
    print("=" * 60)
