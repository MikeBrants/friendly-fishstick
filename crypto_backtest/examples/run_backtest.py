"""Example entrypoint for running a walk-forward backtest."""

from __future__ import annotations

from crypto_backtest.data.fetcher import DataFetcher, FetchRequest
from crypto_backtest.optimization.walk_forward import WalkForwardAnalyzer, WalkForwardConfig
from crypto_backtest.strategies.final_trigger import FinalTriggerStrategy, FinalTriggerParams


def main() -> None:
    fetcher = DataFetcher("binance")
    request = FetchRequest(symbol="BTC/USDT", timeframe="1h")
    data = fetcher.fetch_ohlcv(request)

    analyzer = WalkForwardAnalyzer(WalkForwardConfig())
    params = FinalTriggerParams()

    result = analyzer.analyze(data, FinalTriggerStrategy, params)
    print(f"Combined Sharpe: {result.combined_metrics.get('sharpe_ratio', 0.0):.2f}")
    print(f"Efficiency Ratio: {result.efficiency_ratio:.1f}%")
    print(f"Degradation: {result.degradation_ratio:.2%}")


if __name__ == "__main__":
    main()
