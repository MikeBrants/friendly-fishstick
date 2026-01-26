"""Example entrypoint for running a walk-forward backtest."""

from __future__ import annotations

from crypto_backtest.data.fetcher import DataFetcher, FetchRequest
from crypto_backtest.optimization.walk_forward import WalkForwardAnalyzer, WalkForwardConfig
from crypto_backtest.strategies.final_trigger import FinalTriggerStrategy
from crypto_backtest.examples.optimize_final_trigger import get_param_space


def main() -> None:
    fetcher = DataFetcher("binance")
    request = FetchRequest(symbol="BTC/USDT", timeframe="1h")
    data = fetcher.fetch_ohlcv(request)
    if "timestamp" in data.columns:
        data = data.set_index("timestamp")

    analyzer = WalkForwardAnalyzer(WalkForwardConfig())
    param_space = get_param_space(mode="quick")

    result = analyzer.analyze(data, FinalTriggerStrategy, param_space)
    print(f"Combined Sharpe: {result.combined_metrics.get('sharpe_ratio', 0.0):.2f}")
    print(f"Return Efficiency: {result.return_efficiency:.1%}")
    print(f"WFE (Pardo): {result.wfe_pardo:.2f}")
    print(f"Degradation: {result.degradation_pct:.1f}%")


if __name__ == "__main__":
    main()
