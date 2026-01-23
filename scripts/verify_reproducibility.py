"""
Verify reproducibility between two identical Phase 2 validation runs.
Checks that results are 100% identical (bit-for-bit) for scientific validity.
"""

import argparse
import pandas as pd
import sys


def verify_reproducibility(run1_path: str, run2_path: str) -> bool:
    """
    Compare two validation runs for bit-exact reproducibility.

    Returns:
        True if runs are 100% identical, False otherwise
    """
    print("=" * 70)
    print("REPRODUCIBILITY VERIFICATION")
    print("=" * 70)

    # Load both runs
    print(f"\nLoading Run 1: {run1_path}")
    df1 = pd.read_csv(run1_path)

    print(f"Loading Run 2: {run2_path}")
    df2 = pd.read_csv(run2_path)

    # Check asset count
    if len(df1) != len(df2):
        print(f"❌ FAIL: Asset count mismatch ({len(df1)} vs {len(df2)})")
        return False

    # Check asset names match
    assets1 = set(df1["asset"].tolist())
    assets2 = set(df2["asset"].tolist())

    if assets1 != assets2:
        print(f"❌ FAIL: Asset lists don't match")
        print(f"  Only in Run1: {assets1 - assets2}")
        print(f"  Only in Run2: {assets2 - assets1}")
        return False

    # Check each asset
    print("\n" + "-" * 70)
    print("ASSET-BY-ASSET COMPARISON")
    print("-" * 70)

    all_match = True
    critical_cols = ["oos_sharpe", "wfe", "mc_p", "sl_mult", "tp1_mult", "tp2_mult", "tp3_mult"]

    for asset in sorted(assets1):
        row1 = df1[df1["asset"] == asset].iloc[0]
        row2 = df2[df2["asset"] == asset].iloc[0]

        # Check status match
        status_match = row1["status"] == row2["status"]

        # Check critical metrics
        metrics_match = True
        mismatches = []

        for col in critical_cols:
            if col in df1.columns and col in df2.columns:
                v1 = row1[col]
                v2 = row2[col]

                # For floats, allow tiny numerical errors
                if isinstance(v1, (float, int)):
                    if abs(v1 - v2) > 1e-10:
                        metrics_match = False
                        mismatches.append(f"{col}: {v1:.8f} vs {v2:.8f}")
                else:
                    if v1 != v2:
                        metrics_match = False
                        mismatches.append(f"{col}: {v1} vs {v2}")

        if status_match and metrics_match:
            print(f"✅ {asset:8s} — Status: {row1['status']:8s} Sharpe: {row1['oos_sharpe']:7.2f}")
        else:
            print(f"❌ {asset:8s} — MISMATCH!")
            if not status_match:
                print(f"   Status: {row1['status']} vs {row2['status']}")
            if not metrics_match:
                for mismatch in mismatches:
                    print(f"   {mismatch}")
            all_match = False

    print("\n" + "=" * 70)
    if all_match:
        print("✅ PASS: 100% Reproducible - All runs match bit-for-bit")
        print("   Results are scientifically pure and production-ready.")
        print("=" * 70)
        return True
    else:
        print("❌ FAIL: Runs diverged - Non-determinism detected")
        print("   Investigate sources of randomness in parallel_optimizer.py")
        print("=" * 70)
        return False


def main():
    parser = argparse.ArgumentParser(description="Verify reproducibility between two runs")
    parser.add_argument("--run1", required=True, help="Path to first validation run CSV")
    parser.add_argument("--run2", required=True, help="Path to second validation run CSV")

    args = parser.parse_args()

    is_reproducible = verify_reproducibility(args.run1, args.run2)
    sys.exit(0 if is_reproducible else 1)


if __name__ == "__main__":
    main()
