"""Local storage for market data (Parquet cache)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd


@dataclass(frozen=True)
class CacheKey:
    exchange: str
    symbol: str
    timeframe: str


class ParquetStore:
    """Simple Parquet cache for OHLCV data."""

    def __init__(self, root_dir: str) -> None:
        self.root_dir = Path(root_dir)

    def load(self, key: CacheKey) -> pd.DataFrame | None:
        """Load cached data if available."""
        path = self._path_for_key(key)
        if not path.exists():
            return None
        return pd.read_parquet(path)

    def save(self, key: CacheKey, data: pd.DataFrame) -> None:
        """Persist data to the cache."""
        path = self._path_for_key(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        data.to_parquet(path, index=False)

    def _path_for_key(self, key: CacheKey) -> Path:
        safe_symbol = key.symbol.replace("/", "_")
        filename = f"{safe_symbol}-{key.timeframe}.parquet"
        return self.root_dir / key.exchange / filename
