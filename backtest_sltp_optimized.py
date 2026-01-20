"""Backtest with optimized SL/TP ratios only."""

import pandas as pd
from crypto_backtest.strategies.final_trigger import FinalTriggerStrategy, FinalTriggerParams
from crypto_backtest.indicators.five_in_one import FiveInOneConfig
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

def run_backtest(params_name: str, sl_mult: float, tp1_mult: float, tp2_mult: float, tp3_mult: float):
    """Run backtest with specified SL/TP parameters."""
    data = load_binance_data(warmup=200)

    # All other params at DEFAULT
    five_in_one = FiveInOneConfig(
        use_distance_filter=False,
        use_volume_filter=False,
        use_regression_cloud=False,
        use_kama_oscillator=False,
        use_ichimoku_filter=True,
        ichi5in1_strict=False,
        use_transition_mode=False,
    )

    params = FinalTriggerParams(
        grace_bars=1,
        use_mama_kama_filter=False,
        require_fama_between=False,
        strict_lock_5in1_last=False,
        sl_mult=sl_mult,
        tp1_mult=tp1_mult,
        tp2_mult=tp2_mult,
        tp3_mult=tp3_mult,
        five_in_one=five_in_one,
    )

    strategy = FinalTriggerStrategy(params)

    config = BacktestConfig(
        initial_capital=10000.0,
        fees_bps=5.0,
        slippage_bps=2.0,
        sizing_mode="fixed",
    )

    backtester = VectorizedBacktester(config)
    result = backtester.run(data, strategy)

    # Compute metrics
    n_trades = len(result.trades)
    if n_trades > 0:
        final_equity = result.equity_curve.iloc[-1]
        total_return = (final_equity / config.initial_capital - 1) * 100
        metrics = compute_metrics(result.equity_curve, result.trades)

        winners = result.trades[result.trades["pnl"] > 0]
        losers = result.trades[result.trades["pnl"] < 0]

        return {
            "name": params_name,
            "trades": n_trades,
            "return": total_return,
            "final_equity": final_equity,
            "sharpe": metrics.get('sharpe_ratio', 0),
            "sortino": metrics.get('sortino_ratio', 0),
            "max_dd": metrics.get('max_drawdown', 0),
            "win_rate": metrics.get('win_rate', 0),
            "profit_factor": metrics.get('profit_factor', 0),
            "winners": len(winners),
            "losers": len(losers),
            "avg_win": winners['pnl'].mean() if len(winners) > 0 else 0,
            "avg_loss": losers['pnl'].mean() if len(losers) > 0 else 0,
        }
    return None

def main():
    print("=" * 70)
    print("SL/TP OPTIMIZATION - COMPARISON")
    print("=" * 70)

    # Test 3 configurations
    configs = [
        ("Default", 3.0, 2.0, 6.0, 10.0),
        ("Optimized SL/TP", 3.75, 3.75, 9.0, 7.0),
    ]

    results = []
    for name, sl, tp1, tp2, tp3 in configs:
        print(f"\nRunning backtest: {name}")
        print(f"  SL/TP: {sl}/{tp1}/{tp2}/{tp3}")
        result = run_backtest(name, sl, tp1, tp2, tp3)
        if result:
            results.append(result)

    # Print comparison table
    print("\n" + "=" * 70)
    print("RESULTS COMPARISON")
    print("=" * 70)

    print(f"\n{'Metric':<20} {'Default':<20} {'Optimized SL/TP':<20} {'Change':<15}")
    print("-" * 70)

    metrics = ['return', 'sharpe', 'max_dd', 'win_rate', 'profit_factor', 'trades']

    for metric in metrics:
        default_val = results[0][metric]
        optimized_val = results[1][metric]

        if metric == 'return' or metric == 'max_dd' or metric == 'win_rate':
            default_str = f"{default_val:.2f}%"
            optimized_str = f"{optimized_val:.2f}%"
            change = optimized_val - default_val
            change_str = f"{change:+.2f}pp"
        elif metric == 'trades':
            default_str = f"{int(default_val)}"
            optimized_str = f"{int(optimized_val)}"
            change = int(optimized_val) - int(default_val)
            change_str = f"{change:+d}"
        else:
            default_str = f"{default_val:.2f}"
            optimized_str = f"{optimized_val:.2f}"
            change = optimized_val - default_val
            change_str = f"{change:+.2f}"

        print(f"{metric:<20} {default_str:<20} {optimized_str:<20} {change_str:<15}")

    print("\n" + "=" * 70)
    print("DETAILED RESULTS")
    print("=" * 70)

    for result in results:
        print(f"\n{result['name']}:")
        print(f"  Total return: {result['return']:+.2f}%")
        print(f"  Final equity: ${result['final_equity']:,.2f}")
        print(f"  Sharpe: {result['sharpe']:.2f}")
        print(f"  Sortino: {result['sortino']:.2f}")
        print(f"  Max DD: {result['max_dd']:.1%}")
        print(f"  Win Rate: {result['win_rate']:.1%}")
        print(f"  Profit Factor: {result['profit_factor']:.2f}")
        print(f"  Trades: {result['trades']} ({result['winners']}W / {result['losers']}L)")
        print(f"  Avg win: ${result['avg_win']:,.2f}")
        print(f"  Avg loss: ${result['avg_loss']:,.2f}")

    print("\n" + "=" * 70)

if __name__ == "__main__":
    main()
