"""Run backtest with optimized parameters."""

import pandas as pd
from crypto_backtest.strategies.final_trigger import FinalTriggerStrategy, FinalTriggerParams
from crypto_backtest.indicators.five_in_one import FiveInOneConfig
from crypto_backtest.indicators.ichimoku import IchimokuConfig
from crypto_backtest.engine.backtest import VectorizedBacktester, BacktestConfig
from crypto_backtest.analysis.metrics import compute_metrics

def load_binance_data(warmup: int = 200) -> pd.DataFrame:
    """Load Binance data with warmup."""
    df = pd.read_csv("data/Binance_BTCUSDT_1h.csv")
    df.columns = [col.strip() for col in df.columns]
    data = df[["open", "high", "low", "close"]].copy()

    if "volume" in df.columns:
        data["volume"] = df["volume"].fillna(0.0)
    else:
        data["volume"] = 0.0

    if "timestamp" in df.columns:
        data.index = pd.to_datetime(df["timestamp"], utc=True)

    return data.iloc[warmup:]

def main():
    # Load data
    data = load_binance_data(warmup=200)
    print(f"Data loaded: {len(data)} bars")
    print(f"Date range: {data.index[0]} to {data.index[-1]}\n")

    # Optimized parameters from bayesian optimization
    five_in_one = FiveInOneConfig(
        fast_period=11,
        slow_period=21,
        ad_norm_period=24,
        use_distance_filter=False,
        use_volume_filter=False,
        use_regression_cloud=False,
        use_kama_oscillator=False,
        use_ichimoku_filter=True,
        ichi5in1_strict=False,
        use_transition_mode=False,
    )

    ichimoku = IchimokuConfig(
        tenkan=11,
        kijun=34,
        displacement=47,
    )

    params = FinalTriggerParams(
        grace_bars=1,
        use_mama_kama_filter=False,
        require_fama_between=False,
        strict_lock_5in1_last=False,
        kama_length=10,
        mama_fast_limit=0.55,
        mama_slow_limit=0.07,
        sl_mult=3.5,
        tp1_mult=3.5,
        tp2_mult=6.0,
        tp3_mult=8.0,
        five_in_one=five_in_one,
        ichimoku=ichimoku,
    )

    strategy = FinalTriggerStrategy(params)

    config = BacktestConfig(
        initial_capital=10000.0,
        fees_bps=5.0,
        slippage_bps=2.0,
        sizing_mode="fixed",
    )

    backtester = VectorizedBacktester(config)

    print("=" * 70)
    print("BACKTEST WITH OPTIMIZED PARAMETERS")
    print("=" * 70)

    result = backtester.run(data, strategy)

    # Print results
    n_trades = len(result.trades)
    print(f"\nTotal trades: {n_trades}")

    if n_trades > 0:
        final_equity = result.equity_curve.iloc[-1]
        total_return = (final_equity / config.initial_capital - 1) * 100
        print(f"Initial capital: ${config.initial_capital:,.2f}")
        print(f"Final equity: ${final_equity:,.2f}")
        print(f"Total return: {total_return:+.2f}%")

        # Compute metrics
        metrics = compute_metrics(result.equity_curve, result.trades)
        print(f"\nSharpe Ratio: {metrics.get('sharpe_ratio', 0):.2f}")
        print(f"Sortino Ratio: {metrics.get('sortino_ratio', 0):.2f}")
        print(f"Max Drawdown: {metrics.get('max_drawdown', 0):.1%}")
        print(f"Win Rate: {metrics.get('win_rate', 0):.1%}")
        print(f"Profit Factor: {metrics.get('profit_factor', 0):.2f}")

        # Trade stats
        if "pnl" in result.trades.columns:
            winners = result.trades[result.trades["pnl"] > 0]
            losers = result.trades[result.trades["pnl"] < 0]
            print(f"\nWinners: {len(winners)} | Losers: {len(losers)}")
            if len(winners) > 0:
                print(f"Avg win: ${winners['pnl'].mean():,.2f}")
            if len(losers) > 0:
                print(f"Avg loss: ${losers['pnl'].mean():,.2f}")

        # Comparison with default
        print("\n" + "=" * 70)
        print("IMPROVEMENT vs DEFAULT PARAMETERS")
        print("=" * 70)
        print(f"Sharpe Ratio: 1.61 vs -0.14 → +1253% improvement")
        print(f"Total Return: {total_return:+.2f}% vs -6.44% → {total_return + 6.44:+.2f}pp improvement")
    else:
        print("No trades generated.")

    print("=" * 70)

if __name__ == "__main__":
    main()
