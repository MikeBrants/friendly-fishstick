"""Example: Full param_space for FinalTrigger v2 optimization.

This file defines a comprehensive parameter space for Bayesian optimization
of the FinalTrigger strategy, including all numerical ranges and boolean toggles.
"""

from crypto_backtest.engine.backtest import BacktestConfig
from crypto_backtest.indicators.five_in_one import FiveInOneConfig
from crypto_backtest.indicators.ichimoku import IchimokuConfig
from crypto_backtest.optimization.bayesian import BayesianOptimizer
from crypto_backtest.strategies.final_trigger import FinalTriggerParams, FinalTriggerStrategy


# =============================================================================
# BASE PARAMS: Default configuration (user's current setup)
# =============================================================================
BASE_PARAMS = {
    # Core strategy params
    "grace_bars": 1,
    "use_mama_kama_filter": False,  # OFF in user config
    "require_fama_between": False,
    "strict_lock_5in1_last": False,
    "mama_fast_limit": 0.5,
    "mama_slow_limit": 0.05,
    "kama_length": 20,
    # ATR-based SL/TP
    "atr_length": 14,
    "sl_mult": 3.0,
    "tp1_mult": 2.0,
    "tp2_mult": 6.0,
    "tp3_mult": 10.0,
    # Ichimoku external (Puzzle)
    "ichimoku": {
        "tenkan": 9,
        "kijun": 26,
        "displacement": 52,
    },
    # Five-in-One filter
    "five_in_one": {
        "fast_period": 7,
        "slow_period": 19,
        "er_period": 8,
        "norm_period": 50,
        "use_norm": True,
        "ad_norm_period": 50,
        "use_ad_line": True,
        "ichi5in1_strict": False,  # Light mode (3 cond) in user config
        "use_transition_mode": False,  # State mode in user config
        "use_distance_filter": False,
        "use_volume_filter": False,
        "use_regression_cloud": False,
        "use_kama_oscillator": False,
        "use_ichimoku_filter": True,  # Only active filter
        "tenkan_5": 9,
        "kijun_5": 26,
        "displacement_5": 52,
    },
}


# =============================================================================
# SEARCH SPACE: Ranges and toggles for optimization
# =============================================================================
SEARCH_SPACE_FULL = {
    # --- ATR SL/TP (most impactful) ---
    "sl_mult": {"type": "float", "low": 1.5, "high": 5.0, "step": 0.25},
    "tp1_mult": {"type": "float", "low": 1.0, "high": 4.0, "step": 0.25},
    "tp2_mult": {"type": "float", "low": 4.0, "high": 10.0, "step": 0.5},
    "tp3_mult": {"type": "float", "low": 6.0, "high": 15.0, "step": 0.5},
    # --- MAMA/KAMA params ---
    "kama_length": {"type": "int", "low": 10, "high": 50},
    "mama_fast_limit": {"type": "float", "low": 0.3, "high": 0.7, "step": 0.05},
    "mama_slow_limit": {"type": "float", "low": 0.01, "high": 0.1, "step": 0.01},
    # --- Ichimoku external ---
    "ichimoku.tenkan": {"type": "int", "low": 5, "high": 15},
    "ichimoku.kijun": {"type": "int", "low": 20, "high": 35},
    "ichimoku.displacement": {"type": "int", "low": 40, "high": 65},
    # --- Five-in-One numeric params ---
    "five_in_one.fast_period": {"type": "int", "low": 5, "high": 15},
    "five_in_one.slow_period": {"type": "int", "low": 15, "high": 30},
    "five_in_one.ad_norm_period": {"type": "int", "low": 20, "high": 100},
    # --- Grace bars ---
    "grace_bars": {"type": "categorical", "choices": [0, 1]},
}

# Smaller search space for quick tests
SEARCH_SPACE_QUICK = {
    "sl_mult": {"type": "float", "low": 2.0, "high": 4.0, "step": 0.5},
    "tp1_mult": {"type": "float", "low": 1.5, "high": 3.0, "step": 0.5},
    "tp2_mult": {"type": "float", "low": 5.0, "high": 8.0, "step": 1.0},
}

# Boolean toggles (explore as categorical)
SEARCH_SPACE_TOGGLES = {
    "use_mama_kama_filter": {"type": "categorical", "choices": [True, False]},
    "require_fama_between": {"type": "categorical", "choices": [True, False]},
    "five_in_one.ichi5in1_strict": {"type": "categorical", "choices": [True, False]},
    "five_in_one.use_transition_mode": {"type": "categorical", "choices": [True, False]},
    "five_in_one.use_ad_line": {"type": "categorical", "choices": [True, False]},
}


# =============================================================================
# PARAM SPACE PRESETS
# =============================================================================
def get_param_space(
    mode: str = "quick",
    objective: str = "sharpe_ratio",
    initial_capital: float = 10000.0,
    fees_bps: float = 4.0,
    slippage_bps: float = 1.0,
) -> dict:
    """Get a ready-to-use param_space dict for BayesianOptimizer.

    Args:
        mode: "quick" (SL/TP only), "full" (all numeric), "toggles" (+ booleans)
        objective: metric to optimize (sharpe_ratio, sortino_ratio, total_pnl, etc.)
        initial_capital: starting capital for backtest
        fees_bps: trading fee in basis points (4.0 = 0.04% taker)
        slippage_bps: slippage in basis points (1.0 = 0.01%)

    Returns:
        dict with base_params, search_space, objective, backtest_config
    """
    if mode == "quick":
        search_space = SEARCH_SPACE_QUICK
    elif mode == "full":
        search_space = SEARCH_SPACE_FULL
    elif mode == "toggles":
        search_space = {**SEARCH_SPACE_FULL, **SEARCH_SPACE_TOGGLES}
    else:
        raise ValueError(f"Unknown mode: {mode}")

    return {
        "base_params": BASE_PARAMS,
        "search_space": search_space,
        "objective": objective,
        "direction": "maximize",
        "backtest_config": BacktestConfig(
            initial_capital=initial_capital,
            fees_bps=fees_bps,
            slippage_bps=slippage_bps,
            sizing_mode="fixed",
            intrabar_order="stop_first",
        ),
    }


# =============================================================================
# EXAMPLE USAGE
# =============================================================================
if __name__ == "__main__":
    import pandas as pd

    # 1. Load data (replace with your actual data source)
    # data = pd.read_parquet("btc_usdt_1h.parquet")

    # For demo, create synthetic data
    print("Creating synthetic data for demo...")
    n = 5000
    dates = pd.date_range("2024-01-01", periods=n, freq="1h")
    close = 50000 + (pd.Series(range(n)).apply(lambda x: x * 0.1) +
                     pd.Series([100 * (i % 100 - 50) for i in range(n)]))
    data = pd.DataFrame({
        "open": close * 0.999,
        "high": close * 1.002,
        "low": close * 0.998,
        "close": close,
        "volume": 1000000 + pd.Series([i * 100 for i in range(n)]),
    }, index=dates)

    # 2. Get param_space
    param_space = get_param_space(mode="quick", objective="sharpe_ratio")

    # 3. Run optimization
    print("\nRunning Bayesian optimization (10 trials for demo)...")
    optimizer = BayesianOptimizer()
    result = optimizer.optimize(
        data=data,
        strategy_class=FinalTriggerStrategy,
        param_space=param_space,
        n_trials=10,
    )

    print(f"\nBest params: {result.best_params}")
    print(f"Best score: {result.best_score:.4f}")

    # 4. Reconstruct best params as dataclass
    from crypto_backtest.optimization.bayesian import _apply_overrides

    best_full_params = _apply_overrides(BASE_PARAMS, result.best_params)
    print(f"\nFull params dict: {best_full_params}")
