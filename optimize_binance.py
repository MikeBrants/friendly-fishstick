"""Optimize FinalTrigger strategy on Binance BTCUSDT 1h data."""

import pandas as pd
from pathlib import Path

from crypto_backtest.strategies.final_trigger import FinalTriggerStrategy
from crypto_backtest.optimization.bayesian import BayesianOptimizer
from crypto_backtest.examples.optimize_final_trigger import get_param_space

def load_binance_data(warmup: int = 200) -> pd.DataFrame:
    """Load Binance data with warmup."""
    df = pd.read_csv("data/Binance_BTCUSDT_1h.csv")
    df.columns = [col.strip() for col in df.columns]

    data = df[["open", "high", "low", "close"]].copy()

    if "volume" in df.columns:
        data["volume"] = df["volume"].fillna(0.0)
    else:
        data["volume"] = 0.0

    # Set timestamp as index
    if "timestamp" in df.columns:
        data.index = pd.to_datetime(df["timestamp"], utc=True)

    # Skip warmup
    data = data.iloc[warmup:]

    return data

def main():
    print("=" * 70)
    print("BAYESIAN OPTIMIZATION - Binance BTCUSDT 1h")
    print("=" * 70)

    # Load data
    print("\nLoading data...")
    data = load_binance_data(warmup=200)
    print(f"Data loaded: {len(data)} bars (after warmup)")
    print(f"Date range: {data.index[0]} to {data.index[-1]}")

    # Setup param space - mode "full" for comprehensive optimization
    print("\nSetting up parameter space (mode=full)...")
    param_space = get_param_space(
        mode="full",  # Optimize all numeric params
        objective="sharpe_ratio",
        initial_capital=10000.0,
        fees_bps=5.0,  # 0.05% fees
        slippage_bps=2.0,  # 0.02% slippage
    )

    print(f"Optimizing: {param_space['objective']}")
    print(f"Search space: {len(param_space['search_space'])} parameters")

    # Run optimization
    n_trials = 50
    print(f"\nRunning Bayesian optimization ({n_trials} trials)...")
    print("This may take 5-10 minutes...\n")

    optimizer = BayesianOptimizer()
    result = optimizer.optimize(
        data=data,
        strategy_class=FinalTriggerStrategy,
        param_space=param_space,
        n_trials=n_trials,
    )

    # Print results
    print("\n" + "=" * 70)
    print("OPTIMIZATION RESULTS")
    print("=" * 70)

    print(f"\nBest {param_space['objective']}: {result.best_score:.4f}")
    print(f"\nBest parameters:")
    for key, value in sorted(result.best_params.items()):
        print(f"  {key}: {value}")

    # Show parameter importance if available
    if hasattr(result, 'param_importance') and result.param_importance:
        print("\nParameter Importance (top 5):")
        sorted_importance = sorted(
            result.param_importance.items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]
        for param, importance in sorted_importance:
            print(f"  {param}: {importance:.3f}")

    # Show optimization history summary
    if hasattr(result, 'optimization_history') and result.optimization_history:
        hist = result.optimization_history
        best_10_pct = sorted(hist, key=lambda x: x['value'], reverse=True)[:max(1, n_trials // 10)]
        avg_top_10 = sum(x['value'] for x in best_10_pct) / len(best_10_pct)
        print(f"\nTop 10% average score: {avg_top_10:.4f}")
        print(f"Improvement vs default: {(result.best_score / -0.14 - 1) * 100:+.1f}%")

    print("\n" + "=" * 70)

    # Save results
    output_file = "outputs/optimization_binance_results.txt"
    Path("outputs").mkdir(exist_ok=True)
    with open(output_file, "w") as f:
        f.write(f"Best {param_space['objective']}: {result.best_score:.4f}\n\n")
        f.write("Best parameters:\n")
        for key, value in sorted(result.best_params.items()):
            f.write(f"  {key}: {value}\n")

    print(f"\nResults saved to: {output_file}")

if __name__ == "__main__":
    main()
