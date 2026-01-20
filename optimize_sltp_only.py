"""Ultra-focused optimization - SL/TP ratios ONLY."""

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
    print("SL/TP OPTIMIZATION ONLY")
    print("=" * 70)

    # Load data
    print("\nLoading data...")
    data = load_binance_data(warmup=200)
    print(f"Data loaded: {len(data)} bars (after warmup)")
    print(f"Date range: {data.index[0]} to {data.index[-1]}")

    # Base params - EVERYTHING at defaults
    BASE_PARAMS = {
        "grace_bars": 1,  # DEFAULT
        "use_mama_kama_filter": False,  # DEFAULT
        "require_fama_between": False,  # DEFAULT
        "strict_lock_5in1_last": False,  # DEFAULT
        "mama_fast_limit": 0.5,  # DEFAULT
        "mama_slow_limit": 0.05,  # DEFAULT
        "kama_length": 20,  # DEFAULT
        "atr_length": 14,  # DEFAULT
        "sl_mult": 3.0,   # Will be optimized
        "tp1_mult": 2.0,  # Will be optimized
        "tp2_mult": 6.0,  # Will be optimized
        "tp3_mult": 10.0, # Will be optimized
        # Ichimoku at DEFAULT
        "ichimoku": {
            "tenkan": 9,
            "kijun": 26,
            "displacement": 52,
        },
        # Five-in-One at DEFAULT
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

    # ONLY SL/TP ratios to optimize
    SEARCH_SPACE = {
        "sl_mult": {"type": "float", "low": 1.5, "high": 5.0, "step": 0.25},
        "tp1_mult": {"type": "float", "low": 1.0, "high": 4.0, "step": 0.25},
        "tp2_mult": {"type": "float", "low": 4.0, "high": 10.0, "step": 0.5},
        "tp3_mult": {"type": "float", "low": 6.0, "high": 15.0, "step": 0.5},
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
    print(f"Search space: {len(SEARCH_SPACE)} parameters (SL/TP only)")
    print("\nParameters being optimized:")
    for key in SEARCH_SPACE.keys():
        print(f"  - {key}")

    print("\nALL OTHER parameters at DEFAULT values:")
    print("  - Ichimoku: tenkan=9, kijun=26, displacement=52")
    print("  - Five-in-One: fast_period=7, slow_period=19, ad_norm_period=50")
    print("  - grace_bars=1")
    print("  - use_mama_kama_filter=False")

    # Run optimization
    n_trials = 50
    print(f"\nRunning Bayesian optimization ({n_trials} trials)...")
    print("This should be very fast (~2-3 min)...\n")

    optimizer = BayesianOptimizer()
    result = optimizer.optimize(
        data=data,
        strategy_class=FinalTriggerStrategy,
        param_space=param_space,
        n_trials=n_trials,
    )

    # Print results
    print("\n" + "=" * 70)
    print("SL/TP OPTIMIZATION RESULTS")
    print("=" * 70)

    print(f"\nBest {param_space['objective']}: {result.best_score:.4f}")
    print(f"\nOptimal SL/TP ratios:")
    for key, value in sorted(result.best_params.items()):
        default_val = BASE_PARAMS.get(key, "N/A")
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
    print(f"Default SL/TP (3.0/2.0/6.0/10.0): Sharpe = -0.14")
    print(f"Optimized SL/TP only:              Sharpe = {result.best_score:.2f}")
    improvement = ((result.best_score / -0.14 - 1) * 100) if result.best_score > 0 else 0
    print(f"Improvement:                       {improvement:+.0f}%")
    print("=" * 70)

    # Save results
    output_file = "outputs/optimization_sltp_only.txt"
    Path("outputs").mkdir(exist_ok=True)
    with open(output_file, "w") as f:
        f.write(f"SL/TP OPTIMIZATION ONLY (4 parameters)\n")
        f.write(f"Best {param_space['objective']}: {result.best_score:.4f}\n\n")
        f.write("Optimal SL/TP ratios:\n")
        for key, value in sorted(result.best_params.items()):
            default_val = BASE_PARAMS.get(key, "N/A")
            f.write(f"  {key}: {value} (default: {default_val})\n")
        f.write("\nAll other parameters at DEFAULT values\n")

    print(f"\nResults saved to: {output_file}")

if __name__ == "__main__":
    main()
