#!/usr/bin/env python3
"""
Download historical OHLCV data from Bybit via CCXT.

Usage:
    pip install ccxt pandas
    python scripts/download_historical_data.py

This will download ~2 years of BTC/USDT 1H data and save to data/BYBIT_BTCUSDT_1H_2Y.csv
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add project root to path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import pandas as pd

try:
    import ccxt
except ImportError:
    print("Please install ccxt: pip install ccxt")
    sys.exit(1)


def download_ohlcv(
    exchange_id: str = "bybit",
    symbol: str = "BTC/USDT",
    timeframe: str = "1h",
    days_back: int = 730,
    output_path: str | None = None,
) -> pd.DataFrame:
    """Download historical OHLCV data."""

    print(f"Initializing {exchange_id} exchange...")
    exchange_class = getattr(ccxt, exchange_id)
    exchange = exchange_class({"enableRateLimit": True})
    exchange.load_markets()

    # Calculate timestamps
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days_back)
    since_ms = int(start_date.timestamp() * 1000)
    now_ms = int(end_date.timestamp() * 1000)

    timeframe_ms = exchange.parse_timeframe(timeframe) * 1000

    print(f"Downloading {symbol} {timeframe} from {start_date.date()} to {end_date.date()}")
    print(f"Expected bars: ~{days_back * 24} bars")
    print()

    # Paginated fetch
    all_data = []
    cursor = since_ms
    limit = 1000
    batch_num = 0

    while cursor < now_ms:
        batch_num += 1
        print(f"  Batch {batch_num}: fetching from {datetime.utcfromtimestamp(cursor/1000).strftime('%Y-%m-%d %H:%M')}...", end=" ")

        try:
            batch = exchange.fetch_ohlcv(symbol, timeframe, since=cursor, limit=limit)
        except Exception as e:
            print(f"Error: {e}")
            break

        if not batch:
            print("no data")
            break

        all_data.extend(batch)
        print(f"got {len(batch)} bars")

        last_ts = batch[-1][0]
        if last_ts <= cursor:
            break
        cursor = last_ts + timeframe_ms

        if len(all_data) >= 200_000:
            print("  Max bars reached (200k)")
            break

    # Convert to DataFrame
    df = pd.DataFrame(all_data, columns=["timestamp", "open", "high", "low", "close", "volume"])
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms", utc=True)
    df = df.drop_duplicates(subset=["timestamp"]).sort_values("timestamp").reset_index(drop=True)

    print(f"\nDownloaded {len(df)} bars")
    print(f"Date range: {df['timestamp'].iloc[0]} to {df['timestamp'].iloc[-1]}")

    # Save to CSV
    if output_path is None:
        output_path = ROOT / "data" / f"{exchange_id.upper()}_{symbol.replace('/', '')}_{timeframe}_{days_back}D.csv"
    else:
        output_path = Path(output_path)

    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Export with Unix timestamp for compatibility
    df_export = df.copy()
    df_export["time"] = df_export["timestamp"].astype("int64") // 10**9
    df_export = df_export[["time", "open", "high", "low", "close", "volume"]]
    df_export.to_csv(output_path, index=False)

    print(f"Saved to {output_path}")

    return df


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Download historical OHLCV data")
    parser.add_argument("--exchange", default="bybit", help="Exchange ID (default: bybit)")
    parser.add_argument("--symbol", default="BTC/USDT", help="Trading pair (default: BTC/USDT)")
    parser.add_argument("--timeframe", default="1h", help="Timeframe (default: 1h)")
    parser.add_argument("--days", type=int, default=730, help="Days of history (default: 730 = 2 years)")
    parser.add_argument("--output", type=str, default=None, help="Output CSV path")

    args = parser.parse_args()

    download_ohlcv(
        exchange_id=args.exchange,
        symbol=args.symbol,
        timeframe=args.timeframe,
        days_back=args.days,
        output_path=args.output,
    )
