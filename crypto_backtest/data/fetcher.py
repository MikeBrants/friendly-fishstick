"""Market data fetcher using CCXT with local caching."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import pandas as pd

from .storage import CacheKey, ParquetStore


@dataclass(frozen=True)
class FetchRequest:
    symbol: str
    timeframe: str
    since: int | None = None
    limit: int | None = None


class DataFetcher:
    """Unified interface for multi-exchange OHLCV fetching."""

    def __init__(self, exchange_id: str, store: ParquetStore | None = None) -> None:
        self.exchange_id = exchange_id
        self.store = store
        self._exchange = None

    def fetch_ohlcv(self, request: FetchRequest) -> pd.DataFrame:
        """Fetch OHLCV data for a request and return a normalized DataFrame."""
        exchange = self._get_exchange()
        exchange.load_markets()

        cache_key = CacheKey(self.exchange_id, request.symbol, request.timeframe)
        cached = self.store.load(cache_key) if self.store else None

        since = request.since
        timeframe_ms = self._timeframe_ms(exchange, request.timeframe)
        if cached is not None and not cached.empty:
            cached = self._normalize(cached)
            if since is None:
                return cached
            cached_last_ms = int(cached["timestamp"].iloc[-1].value / 1_000_000)
            since = max(since, cached_last_ms + timeframe_ms)

        if since is None:
            rows = exchange.fetch_ohlcv(
                request.symbol, request.timeframe, since=None, limit=request.limit
            )
        else:
            rows = self._fetch_paginated(exchange, request, since, timeframe_ms)

        fresh = self._normalize(self._to_frame(rows))
        combined = self._combine_cached(cached, fresh)
        if self.store:
            self.store.save(cache_key, combined)
        return combined

    def fetch_ohlcv_range(self, requests: Iterable[FetchRequest]) -> pd.DataFrame:
        """Fetch and concatenate multiple requests in order."""
        frames = [self.fetch_ohlcv(request) for request in requests]
        if not frames:
            return pd.DataFrame(columns=["timestamp", "open", "high", "low", "close", "volume"])
        combined = pd.concat(frames, ignore_index=True)
        return self._normalize(combined)

    def _get_exchange(self):
        if self._exchange is not None:
            return self._exchange
        import ccxt  # Imported lazily to avoid import cost unless needed.

        try:
            exchange_class = getattr(ccxt, self.exchange_id)
        except AttributeError as exc:
            raise ValueError(f"Unsupported exchange: {self.exchange_id}") from exc

        self._exchange = exchange_class({"enableRateLimit": True})
        if not self._exchange.has.get("fetchOHLCV", False):
            raise ValueError(f"Exchange {self.exchange_id} does not support OHLCV.")
        return self._exchange

    def _fetch_paginated(self, exchange, request: FetchRequest, since: int, timeframe_ms: int):
        limit = request.limit or 1000
        now_ms = self._now_ms(exchange)
        max_bars = 200_000
        data = []
        cursor = since
        while True:
            batch = exchange.fetch_ohlcv(
                request.symbol, request.timeframe, since=cursor, limit=limit
            )
            if not batch:
                break
            data.extend(batch)
            last_ts = batch[-1][0]
            if last_ts <= cursor:
                break
            cursor = last_ts + timeframe_ms
            if cursor >= now_ms - timeframe_ms:
                break
            if len(data) >= max_bars:
                break
        return data

    def _to_frame(self, rows) -> pd.DataFrame:
        return pd.DataFrame(
            rows, columns=["timestamp", "open", "high", "low", "close", "volume"]
        )

    def _normalize(self, data: pd.DataFrame) -> pd.DataFrame:
        if data.empty:
            return data
        df = data.copy()
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms", utc=True)
        df = df.drop_duplicates(subset=["timestamp"]).sort_values("timestamp")
        return df.reset_index(drop=True)

    def _combine_cached(self, cached: pd.DataFrame | None, fresh: pd.DataFrame) -> pd.DataFrame:
        if cached is None or cached.empty:
            return fresh
        combined = pd.concat([cached, fresh], ignore_index=True)
        return self._normalize(combined)

    def _timeframe_ms(self, exchange, timeframe: str) -> int:
        seconds = exchange.parse_timeframe(timeframe)
        return int(seconds * 1000)

    def _now_ms(self, exchange) -> int:
        if hasattr(exchange, "milliseconds"):
            return exchange.milliseconds()
        return int(pd.Timestamp.utcnow().timestamp() * 1000)
