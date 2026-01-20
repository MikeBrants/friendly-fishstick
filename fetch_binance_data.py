"""Script to fetch Binance BTCUSDT 1h data and save to CSV."""

import pandas as pd
from datetime import datetime, timedelta
from crypto_backtest.data.fetcher import DataFetcher, FetchRequest
from crypto_backtest.data.storage import ParquetStore

def main():
    print("Fetching Binance BTCUSDT 1h data...")

    # Initialize fetcher with cache
    store = ParquetStore(root_dir="data/cache")
    fetcher = DataFetcher(exchange_id="binance", store=store)

    # Fetch 2 years of 1h data
    # CCXT expects timestamps in milliseconds
    since_date = datetime.now() - timedelta(days=730)  # 2 years
    since_ms = int(since_date.timestamp() * 1000)

    request = FetchRequest(
        symbol="BTC/USDT",
        timeframe="1h",
        since=since_ms,
        limit=1000
    )

    print(f"Fetching from {since_date.strftime('%Y-%m-%d')} to now...")
    df = fetcher.fetch_ohlcv(request)

    print(f"Fetched {len(df)} candles")
    print(f"Date range: {df['timestamp'].min()} to {df['timestamp'].max()}")

    # Save to CSV
    output_file = "data/Binance_BTCUSDT_1h.csv"
    df.to_csv(output_file, index=False)
    print(f"Saved to {output_file}")

    # Show first and last rows
    print("\nFirst 5 rows:")
    print(df.head())
    print("\nLast 5 rows:")
    print(df.tail())

    return df

if __name__ == "__main__":
    main()
