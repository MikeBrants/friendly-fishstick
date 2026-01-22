"""
Download OHLCV data for all scan assets
Uses CCXT for multi-exchange support
"""
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import ccxt
import pandas as pd
from datetime import datetime, timedelta
import time
import argparse

from crypto_backtest.config.scan_assets import ALL_ASSETS, SCAN_ASSETS, EXCHANGE_MAP


def download_asset(
    asset: str,
    timeframe: str = "1h",
    days_back: int = 730,
    output_dir: str = "data"
) -> pd.DataFrame:
    """Download OHLCV data for a single asset."""

    exchange_id = EXCHANGE_MAP.get(asset, "binance")

    try:
        exchange = getattr(ccxt, exchange_id)({"enableRateLimit": True})
    except AttributeError:
        raise ValueError(f"Unknown exchange: {exchange_id}")

    symbol = f"{asset}/USDT"

    # Calculate start timestamp
    start_date = datetime.utcnow() - timedelta(days=days_back)
    since = exchange.parse8601(start_date.isoformat())

    all_ohlcv = []
    batch_count = 0

    while True:
        try:
            ohlcv = exchange.fetch_ohlcv(symbol, timeframe, since, limit=1000)
        except Exception as e:
            print(f"    Error fetching {symbol}: {e}")
            break

        if not ohlcv:
            break

        all_ohlcv.extend(ohlcv)
        batch_count += 1

        # Progress indicator
        if batch_count % 10 == 0:
            print(f"    {asset}: {len(all_ohlcv)} bars...", end="\r")

        # Move cursor forward
        since = ohlcv[-1][0] + 1

        # Check if we've reached the end
        if len(ohlcv) < 1000:
            break

        # Respect rate limits
        time.sleep(exchange.rateLimit / 1000)

    if not all_ohlcv:
        return pd.DataFrame()

    # Create DataFrame
    df = pd.DataFrame(
        all_ohlcv,
        columns=["timestamp", "open", "high", "low", "close", "volume"]
    )
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
    df.set_index("timestamp", inplace=True)

    # Remove duplicates
    df = df[~df.index.duplicated(keep="first")]
    df = df.sort_index()

    return df


def download_all(
    assets: list = None,
    output_dir: str = "data",
    timeframe: str = "1h",
    days_back: int = 730,
    format: str = "parquet"
):
    """Download data for multiple assets."""

    assets = assets or ALL_ASSETS
    Path(output_dir).mkdir(exist_ok=True)

    print("=" * 60)
    print("DOWNLOADING OHLCV DATA")
    print(f"Assets: {len(assets)}")
    print(f"Timeframe: {timeframe}")
    print(f"Days back: {days_back}")
    print(f"Output: {output_dir}/")
    print("=" * 60)

    results = {"success": [], "failed": []}

    for i, asset in enumerate(assets, 1):
        print(f"\n[{i}/{len(assets)}] Downloading {asset}...")

        try:
            df = download_asset(asset, timeframe, days_back, output_dir)

            if df.empty:
                print(f"  [FAIL] {asset}: No data returned")
                results["failed"].append(asset)
                continue

            # Save file
            filename = f"{asset}_1H"
            if format == "parquet":
                filepath = f"{output_dir}/{filename}.parquet"
                df.to_parquet(filepath)
            else:
                filepath = f"{output_dir}/{filename}.csv"
                df.to_csv(filepath)

            # Stats
            start_date = df.index[0].strftime("%Y-%m-%d")
            end_date = df.index[-1].strftime("%Y-%m-%d")
            print(f"  [OK] {asset}: {len(df):,} bars [{start_date} -> {end_date}]")
            results["success"].append(asset)

        except Exception as e:
            print(f"  [FAIL] {asset}: {e}")
            results["failed"].append(asset)

    # Summary
    print("\n" + "=" * 60)
    print("DOWNLOAD COMPLETE")
    print("=" * 60)
    print(f"Success: {len(results['success'])} assets")
    if results["failed"]:
        print(f"Failed: {results['failed']}")

    return results


def main():
    parser = argparse.ArgumentParser(description="Download OHLCV data for assets")
    parser.add_argument(
        "--assets",
        nargs="+",
        default=None,
        help="Specific assets to download (default: all)"
    )
    parser.add_argument(
        "--scan-only",
        action="store_true",
        help="Only download SCAN_ASSETS (exclude BTC/ETH/XRP)"
    )
    parser.add_argument(
        "--days",
        type=int,
        default=730,
        help="Days of history to download (default: 730)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data",
        help="Output directory (default: data)"
    )
    parser.add_argument(
        "--format",
        choices=["parquet", "csv"],
        default="parquet",
        help="Output format (default: parquet)"
    )
    args = parser.parse_args()

    if args.scan_only:
        assets = SCAN_ASSETS
    else:
        assets = args.assets

    download_all(
        assets=assets,
        output_dir=args.output,
        days_back=args.days,
        format=args.format
    )


if __name__ == "__main__":
    main()
