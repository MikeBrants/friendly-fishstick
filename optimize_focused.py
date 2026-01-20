"""Focused optimization - only parameters that actually matter."""

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
    print("FOCUSED OPTIMIZATION - Only Active Parameters")
    print("=" * 70)

    # Load data
    print("\nLoading data...")
    data = load_binance_data(warmup=200)
    print(f"Data loaded: {len(data)} bars (after warmup)")
    print(f"Date range: {data.index[0]} to {data.index[-1]}")

    # Base params with FIXED Ichimoku defaults (not optimized)
    BASE_PARAMS = {
        "grace_bars": 1,
        "use_mama_kama_filter": False,  # OFF = MAMA/KAMA params irrelevant
        "require_fama_between": False,
        "strict_lock_5in1_last": False,
        "mama_fast_limit": 0.5,  # Fixed (not used)
        "mama_slow_limit": 0.05,  # Fixed (not used)
        "kama_length": 20,  # Fixed (not used)
        "atr_length": 14,
        "sl_mult": 3.0,
        "tp1_mult": 2.0,
        "tp2_mult": 6.0,
        "tp3_mult": 10.0,
        # Ichimoku FIXED at defaults
        "ichimoku": {
            "tenkan": 9,       # NOT optimized
            "kijun": 26,       # NOT optimized
            "displacement": 52,  # NOT optimized
        },
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
            "tenkan_5": 9,
            "kijun_5": 26,
            "displacement_5": 52,
        },
    }

    # FOCUSED search space - only parameters that actually impact signals
    SEARCH_SPACE = {
        # ATR SL/TP - MOST IMPACTFUL
        "sl_mult": {"type": "float", "low": 1.5, "high": 5.0, "step": 0.25},
        "tp1_mult": {"type": "float", "low": 1.0, "high": 4.0, "step": 0.25},
        "tp2_mult": {"type": "float", "low": 4.0, "high": 10.0, "step": 0.5},
        "tp3_mult": {"type": "float", "low": 6.0, "high": 15.0, "step": 0.5},

        # Five-in-One timing params
        "five_in_one.fast_period": {"type": "int", "low": 5, "high": 15},
        "five_in_one.slow_period": {"type": "int", "low": 15, "high": 30},
        "five_in_one.ad_norm_period": {"type": "int", "low": 20, "high": 100},

        # Grace bars
        "grace_bars": {"type": "categorical", "choices": [0, 1]},
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
    print(f"Search space: {len(SEARCH_SPACE)} parameters (focused)")
    print("\nParameters being optimized:")
    for key in SEARCH_SPACE.keys():
        print(f"  - {key}")

    print("\nParameters FIXED (not optimized):")
    print("  - Ichimoku: tenkan=9, kijun=26, displacement=52")
    print("  - MAMA/KAMA: ignored (use_mama_kama_filter=False)")

    # Run optimization
    n_trials = 50
    print(f"\nRunning Bayesian optimization ({n_trials} trials)...")
    print("This should be faster (~3-5 min) with fewer parameters...\n")

    optimizer = BayesianOptimizer()
    result = optimizer.optimize(
        data=data,
        strategy_class=FinalTriggerStrategy,
        param_space=param_space,
        n_trials=n_trials,
    )

    # Print results
    print("\n" + "=" * 70)
    print("FOCUSED OPTIMIZATION RESULTS")
    print("=" * 70)

    print(f"\nBest {param_space['objective']}: {result.best_score:.4f}")
    print(f"\nBest parameters:")
    for key, value in sorted(result.best_params.items()):
        print(f"  {key}: {value}")

    # Show parameter importance if available
    if hasattr(result, 'param_importance') and result.param_importance:
        print("\nParameter Importance (ranked):")
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
    print(f"Previous optimization (14 params):  Sharpe = 1.61")
    print(f"Focused optimization (8 params):    Sharpe = {result.best_score:.2f}")
    print("=" * 70)

    # Save results
    output_file = "outputs/optimization_focused_results.txt"
    Path("outputs").mkdir(exist_ok=True)
    with open(output_file, "w") as f:
        f.write(f"FOCUSED OPTIMIZATION (8 active parameters only)\n")
        f.write(f"Best {param_space['objective']}: {result.best_score:.4f}\n\n")
        f.write("Best parameters:\n")
        for key, value in sorted(result.best_params.items()):
            f.write(f"  {key}: {value}\n")
        f.write("\nFixed parameters (not optimized):\n")
        f.write("  Ichimoku: tenkan=9, kijun=26, displacement=52\n")
        f.write("  MAMA/KAMA: ignored (use_mama_kama_filter=False)\n")

    print(f"\nResults saved to: {output_file}")

if __name__ == "__main__":
    main()
