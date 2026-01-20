"""Optimize Ichimoku parameters (tenkan/kijun) with optimized SL/TP fixed."""

import pandas as pd
from pathlib import Path

from crypto_backtest.strategies.final_trigger import FinalTriggerStrategy
from crypto_backtest.optimization.bayesian import BayesianOptimizer
from crypto_backtest.engine.backtest import BacktestConfig

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
    print("=" * 70)
    print("ICHIMOKU OPTIMIZATION (Tenkan/Kijun only)")
    print("=" * 70)

    # Load data
    print("\nLoading data...")
    data = load_binance_data(warmup=200)
    print(f"Data loaded: {len(data)} bars (after warmup)")
    print(f"Date range: {data.index[0]} to {data.index[-1]}")

    # Base params with OPTIMIZED SL/TP fixed
    BASE_PARAMS = {
        "grace_bars": 1,
        "use_mama_kama_filter": False,
        "require_fama_between": False,
        "strict_lock_5in1_last": False,
        "mama_fast_limit": 0.5,
        "mama_slow_limit": 0.05,
        "kama_length": 20,
        "atr_length": 14,
        # OPTIMIZED SL/TP - FIXED
        "sl_mult": 3.75,
        "tp1_mult": 3.75,
        "tp2_mult": 9.0,
        "tp3_mult": 7.0,
        # Ichimoku - tenkan/kijun to optimize, displacement FIXED
        "ichimoku": {
            "tenkan": 9,       # Will be optimized
            "kijun": 26,       # Will be optimized
            "displacement": 52,  # FIXED
        },
        # Five-in-One
        "five_in_one": {
            "fast_period": 7,
            "slow_period": 19,
            "er_period": 8,
            "norm_period": 50,
            "use_norm": True,
            "ad_norm_period": 50,
            "use_ad_line": True,
            "ichi5in1_strict": False,
            "use_transition_mode": False,
            "use_distance_filter": False,
            "use_volume_filter": False,
            "use_regression_cloud": False,
            "use_kama_oscillator": False,
            "use_ichimoku_filter": True,
            "tenkan_5": 9,       # Will be optimized
            "kijun_5": 26,       # Will be optimized
            "displacement_5": 52,  # FIXED
        },
    }

    # Search space: 4 Ichimoku parameters only
    SEARCH_SPACE = {
        # Ichimoku Externe
        "ichimoku.tenkan": {"type": "int", "low": 5, "high": 15},
        "ichimoku.kijun": {"type": "int", "low": 20, "high": 35},

        # Ichimoku 5-in-1
        "five_in_one.tenkan_5": {"type": "int", "low": 5, "high": 15},
        "five_in_one.kijun_5": {"type": "int", "low": 20, "high": 35},
    }

    param_space = {
        "base_params": BASE_PARAMS,
        "search_space": SEARCH_SPACE,
        "objective": "sharpe_ratio",
        "direction": "maximize",
        "backtest_config": BacktestConfig(
            initial_capital=10000.0,
            fees_bps=5.0,
            slippage_bps=2.0,
            sizing_mode="fixed",
            intrabar_order="stop_first",
        ),
    }

    print(f"\nOptimizing: {param_space['objective']}")
    print(f"Search space: {len(SEARCH_SPACE)} parameters")
    print("\nParameters being optimized:")
    for key in SEARCH_SPACE.keys():
        print(f"  - {key}")

    print("\nParameters FIXED:")
    print(f"  - SL/TP: {BASE_PARAMS['sl_mult']}/{BASE_PARAMS['tp1_mult']}/{BASE_PARAMS['tp2_mult']}/{BASE_PARAMS['tp3_mult']} (optimized)")
    print(f"  - ichimoku.displacement: 52")
    print(f"  - five_in_one.displacement_5: 52")

    # Run optimization
    n_trials = 50
    print(f"\nRunning Bayesian optimization ({n_trials} trials)...")
    print("Estimated time: ~3-4 minutes...\n")

    optimizer = BayesianOptimizer()
    result = optimizer.optimize(
        data=data,
        strategy_class=FinalTriggerStrategy,
        param_space=param_space,
        n_trials=n_trials,
    )

    # Print results
    print("\n" + "=" * 70)
    print("ICHIMOKU OPTIMIZATION RESULTS")
    print("=" * 70)

    print(f"\nBest {param_space['objective']}: {result.best_score:.4f}")
    print(f"\nOptimal Ichimoku parameters:")
    for key, value in sorted(result.best_params.items()):
        default_val = None
        if key == "ichimoku.tenkan":
            default_val = 9
        elif key == "ichimoku.kijun":
            default_val = 26
        elif key == "five_in_one.tenkan_5":
            default_val = 9
        elif key == "five_in_one.kijun_5":
            default_val = 26
        print(f"  {key}: {value} (default: {default_val})")

    # Show parameter importance
    if hasattr(result, 'param_importance') and result.param_importance:
        print("\nParameter Importance:")
        sorted_importance = sorted(
            result.param_importance.items(),
            key=lambda x: x[1],
            reverse=True
        )
        for param, importance in sorted_importance:
            print(f"  {param}: {importance:.3f}")

    print("\n" + "=" * 70)
    print("COMPARISON")
    print("=" * 70)
    print(f"SL/TP optimized only (Ichi default): Sharpe = 1.43")
    print(f"SL/TP + Ichimoku optimized:          Sharpe = {result.best_score:.2f}")
    improvement = result.best_score - 1.43
    print(f"Improvement from Ichimoku tuning:    {improvement:+.2f}")
    print("=" * 70)

    # Save results
    output_file = "outputs/optimization_ichimoku_results.txt"
    Path("outputs").mkdir(exist_ok=True)
    with open(output_file, "w") as f:
        f.write(f"ICHIMOKU OPTIMIZATION (4 parameters: tenkan/kijun)\n")
        f.write(f"SL/TP fixed at optimized values: 3.75/3.75/9.0/7.0\n\n")
        f.write(f"Best {param_space['objective']}: {result.best_score:.4f}\n\n")
        f.write("Optimal Ichimoku parameters:\n")
        for key, value in sorted(result.best_params.items()):
            f.write(f"  {key}: {value}\n")
        f.write("\nFixed parameters:\n")
        f.write("  displacement: 52\n")
        f.write("  displacement_5: 52\n")

    print(f"\nResults saved to: {output_file}")

    return result.best_params

if __name__ == "__main__":
    best_params = main()
