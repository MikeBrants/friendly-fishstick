"""Debug guards to find complex number source."""
import sys
sys.path.insert(0, '.')

import pandas as pd
import numpy as np
import traceback

from crypto_backtest.optimization.parallel_optimizer import load_data, build_strategy_params
from crypto_backtest.optimization.bayesian import _instantiate_strategy
from crypto_backtest.strategies.final_trigger import FinalTriggerStrategy
from crypto_backtest.engine.backtest import BacktestConfig, VectorizedBacktester
from crypto_backtest.analysis.metrics import compute_metrics


def check_for_complex(value, name):
    """Check if value is complex."""
    if isinstance(value, complex):
        print(f"  COMPLEX FOUND: {name} = {value}")
        return True
    if isinstance(value, np.ndarray):
        if np.iscomplexobj(value):
            print(f"  COMPLEX ARRAY FOUND: {name}")
            return True
    return False


def test_asset(asset):
    """Test a single asset for complex number issues."""
    print(f"\n=== Testing {asset} ===")
    
    # Load data
    data = load_data(asset)
    print(f"Loaded {len(data)} bars")
    print(f"Index tz: {data.index.tz}")
    
    # Build params
    params = build_strategy_params(
        sl_mult=3.0, tp1_mult=4.0, tp2_mult=5.0, tp3_mult=6.0,
        tenkan=9, kijun=26, tenkan_5=9, kijun_5=26,
        displacement=52
    )
    
    config = BacktestConfig(
        initial_capital=10000.0,
        fees_bps=5.0,
        slippage_bps=2.0,
        sizing_mode='fixed',
        intrabar_order='stop_first',
    )
    
    # Run base backtest
    strategy = _instantiate_strategy(FinalTriggerStrategy, params)
    backtester = VectorizedBacktester(config)
    result = backtester.run(data, strategy)
    
    print(f"Trades: {len(result.trades)}")
    
    # Check equity curve
    equity = result.equity_curve
    print(f"Equity start: {equity.iloc[0]}, end: {equity.iloc[-1]}")
    
    # Compute metrics step by step
    print("\n--- Metrics Debug ---")
    
    start = float(equity.iloc[0])
    end = float(equity.iloc[-1])
    print(f"start={start}, end={end}")
    check_for_complex(start, "start")
    check_for_complex(end, "end")
    
    total_return = 0.0 if start == 0 else (end / start) - 1.0
    print(f"total_return={total_return}")
    check_for_complex(total_return, "total_return")
    
    # Years
    if len(equity.index) >= 2:
        delta = equity.index[-1] - equity.index[0]
        years = delta.total_seconds() / (365.25 * 24 * 3600)
        print(f"years={years}")
        check_for_complex(years, "years")
    else:
        years = 0
    
    # CAGR - potential complex source
    if years > 0 and start > 0:
        ratio = end / start
        print(f"end/start ratio={ratio}")
        check_for_complex(ratio, "ratio")
        
        if ratio < 0:
            print("  WARNING: ratio is negative! This will cause complex CAGR")
        
        try:
            cagr = ratio ** (1 / years) - 1.0
            print(f"cagr={cagr}")
            check_for_complex(cagr, "cagr")
        except Exception as e:
            print(f"  CAGR ERROR: {e}")
    
    # Returns and Sharpe
    returns = equity.pct_change().dropna()
    print(f"returns: {len(returns)} values, mean={returns.mean()}, std={returns.std()}")
    
    # Periods per year
    from crypto_backtest.analysis.metrics import _periods_per_year
    periods = _periods_per_year(equity.index)
    print(f"periods_per_year={periods}")
    check_for_complex(periods, "periods_per_year")
    
    # Sharpe calculation
    if returns.std() != 0:
        sharpe_raw = returns.mean() / returns.std()
        print(f"sharpe_raw (before annualization)={sharpe_raw}")
        check_for_complex(sharpe_raw, "sharpe_raw")
        
        sqrt_periods = periods ** 0.5
        print(f"sqrt(periods)={sqrt_periods}")
        check_for_complex(sqrt_periods, "sqrt_periods")
        
        sharpe = sharpe_raw * sqrt_periods
        print(f"sharpe={sharpe}")
        check_for_complex(sharpe, "sharpe")
    
    # Full metrics
    print("\n--- Full Metrics ---")
    try:
        metrics = compute_metrics(equity, result.trades)
        for k, v in metrics.items():
            is_complex = check_for_complex(v, k)
            if not is_complex and not isinstance(v, dict):
                print(f"  {k}: {v}")
    except Exception as e:
        print(f"  METRICS ERROR: {e}")
        traceback.print_exc()
    
    # Bootstrap test
    print("\n--- Bootstrap Debug ---")
    if len(result.trades) > 0:
        pnls = result.trades.get('net_pnl', result.trades.get('pnl', pd.Series())).values
        print(f"PnLs: {len(pnls)}")
        
        n = len(pnls)
        rng = np.random.default_rng(42)
        indices = rng.integers(0, n, size=(100, n))
        samples = pnls[indices]
        
        returns_bs = samples / 10000.0
        mean_returns = returns_bs.mean(axis=1)
        std_returns = returns_bs.std(axis=1, ddof=0)
        
        print(f"mean_returns range: {mean_returns.min()} to {mean_returns.max()}")
        print(f"std_returns range: {std_returns.min()} to {std_returns.max()}")
        
        sharpe_bs = np.where(std_returns == 0, 0.0, mean_returns / std_returns * np.sqrt(n))
        print(f"sharpe_bs range: {sharpe_bs.min()} to {sharpe_bs.max()}")
        check_for_complex(sharpe_bs, "sharpe_bs")
        
        mean_sharpe = np.mean(sharpe_bs)
        print(f"mean(sharpe_bs)={mean_sharpe}")
        check_for_complex(mean_sharpe, "mean_sharpe")
        
        try:
            float_mean = float(mean_sharpe)
            print(f"float(mean_sharpe)={float_mean}")
        except Exception as e:
            print(f"  FLOAT ERROR: {e}")


if __name__ == '__main__':
    assets = ['YGG', 'ARKM', 'STRK']
    for asset in assets:
        try:
            test_asset(asset)
        except Exception as e:
            print(f"ERROR for {asset}: {e}")
            traceback.print_exc()
