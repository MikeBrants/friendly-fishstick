"""
Merge MATIC (old ticker) and POL (new ticker) data for Polygon
"""
import ccxt
import pandas as pd
from datetime import datetime, timedelta
import time
from pathlib import Path

def download_ohlcv(exchange, symbol, since_date, timeframe="1h"):
    """Download OHLCV data from exchange."""
    since = exchange.parse8601(since_date.isoformat())
    all_ohlcv = []
    
    print(f"Downloading {symbol}...")
    while True:
        try:
            ohlcv = exchange.fetch_ohlcv(symbol, timeframe, since, limit=1000)
        except Exception as e:
            print(f"Error: {e}")
            break
            
        if not ohlcv:
            break
            
        all_ohlcv.extend(ohlcv)
        
        if len(all_ohlcv) % 5000 == 0:
            print(f"  {len(all_ohlcv)} bars...")
            
        since = ohlcv[-1][0] + 1
        
        if len(ohlcv) < 1000:
            break
            
        time.sleep(exchange.rateLimit / 1000)
    
    if not all_ohlcv:
        return pd.DataFrame()
        
    df = pd.DataFrame(
        all_ohlcv,
        columns=["timestamp", "open", "high", "low", "close", "volume"]
    )
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
    df.set_index("timestamp", inplace=True)
    df = df[~df.index.duplicated(keep="first")]
    df = df.sort_index()
    
    return df

def main():
    # Initialize exchange
    exchange = ccxt.binance({"enableRateLimit": True})
    
    # Download MATIC (legacy, should have data until Sept 2024)
    start_date = datetime.utcnow() - timedelta(days=730)
    matic = download_ohlcv(exchange, "MATIC/USDT", start_date)
    
    if not matic.empty:
        print(f"MATIC: {len(matic)} bars [{matic.index[0]} -> {matic.index[-1]}]")
    else:
        print("MATIC: No data (expected if fully migrated)")
    
    # Download POL (new ticker, from Sept 2024)
    pol = download_ohlcv(exchange, "POL/USDT", start_date)
    
    if not pol.empty:
        print(f"POL: {len(pol)} bars [{pol.index[0]} -> {pol.index[-1]}]")
    else:
        print("POL: No data found!")
        return
    
    # Merge
    if not matic.empty:
        print("\nMerging MATIC + POL...")
        merged = pd.concat([matic, pol])
        merged = merged[~merged.index.duplicated(keep='last')]  # Keep POL if overlap
        merged = merged.sort_index()
        
        print(f"Merged: {len(merged)} bars [{merged.index[0]} -> {merged.index[-1]}]")
        
        # Check gap
        matic_end = matic.index[-1]
        pol_start = pol.index[0]
        gap = (pol_start - matic_end).total_seconds() / 3600
        print(f"Gap between MATIC end and POL start: {gap:.1f} hours")
    else:
        merged = pol
        print("Using POL only (MATIC unavailable)")
    
    # Save
    output_dir = Path("data")
    output_dir.mkdir(exist_ok=True)
    
    # Save as MATIC for backward compatibility
    merged.to_parquet(output_dir / "MATIC.parquet")
    print(f"\nSaved: data/MATIC.parquet ({len(merged)} bars)")
    
    # Also save backup
    merged.to_parquet(output_dir / "MATIC_POL_merged.parquet")
    print(f"Backup: data/MATIC_POL_merged.parquet")
    
    print("\nDone! Use MATIC in screening (merged dataset)")

if __name__ == "__main__":
    main()
