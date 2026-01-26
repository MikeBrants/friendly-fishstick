#!/usr/bin/env python3
"""
Regime Stress Test - FINAL TRIGGER v2
=====================================

Backtest la strategie Ichimoku+ATR sur un regime isole.

Usage:
    python scripts/run_regime_stress_test.py --asset ETH --regime MARKDOWN
    python scripts/run_regime_stress_test.py --all-assets --regime MARKDOWN
    python scripts/run_regime_stress_test.py --all-assets --regime ACCUMULATION

Regimes supportes:
    ACCUMULATION, MARKDOWN, MARKUP, DISTRIBUTION, CAPITULATION, RECOVERY (crypto)
    SIDEWAYS, WEAK_BULL, WEAK_BEAR, STRONG_BULL, STRONG_BEAR, REVERSAL (trend)
    COMPRESSED, NORMAL, ELEVATED, EXTREME (volatility)

Issue: #17 (Regime-Robust Validation Framework)
TASK 3 - Owner: Jordan
Date: 26 janvier 2026
"""

import argparse
import sys
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from crypto_backtest.optimization.parallel_optimizer import load_data, build_strategy_params
from crypto_backtest.optimization.bayesian import _instantiate_strategy
from crypto_backtest.strategies.final_trigger import FinalTriggerStrategy
from crypto_backtest.engine.backtest import BacktestConfig, VectorizedBacktester
from crypto_backtest.config.asset_config import ASSET_CONFIG
from crypto_backtest.analysis.metrics import compute_metrics


# 14 PROD assets (from project-state.md)
PROD_ASSETS = [
    'SHIB', 'DOT', 'TIA', 'NEAR', 'DOGE', 'ANKR', 'ETH',
    'JOE', 'YGG', 'MINA', 'CAKE', 'RUNE', 'EGLD', 'AVAX'
]

# Regime types mapping
CRYPTO_REGIMES = ['ACCUMULATION', 'MARKDOWN', 'MARKUP', 'DISTRIBUTION', 'CAPITULATION', 'RECOVERY']
TREND_REGIMES = ['SIDEWAYS', 'WEAK_BULL', 'WEAK_BEAR', 'STRONG_BULL', 'STRONG_BEAR', 'REVERSAL']
VOL_REGIMES = ['COMPRESSED', 'NORMAL', 'ELEVATED', 'EXTREME']


def load_regime_data(asset: str) -> pd.DataFrame:
    """Load pre-computed regime data for an asset."""
    path = PROJECT_ROOT / f"outputs/regime_analysis/{asset}_regimes.csv"
    if not path.exists():
        raise FileNotFoundError(f"Regime data not found: {path}. Run regime analysis first.")
    
    df = pd.read_csv(path, parse_dates=['timestamp'])
    df.set_index('timestamp', inplace=True)
    return df


def get_regime_column(regime: str) -> str:
    """Determine which column to use for regime filtering."""
    if regime in CRYPTO_REGIMES:
        return 'crypto_regime'
    elif regime in TREND_REGIMES:
        return 'trend_regime'
    elif regime in VOL_REGIMES:
        return 'vol_regime'
    else:
        raise ValueError(f"Unknown regime: {regime}. Valid regimes: {CRYPTO_REGIMES + TREND_REGIMES + VOL_REGIMES}")


def filter_trades_by_regime(
    trades: pd.DataFrame,
    regime_data: pd.DataFrame,
    regime: str,
    regime_column: str
) -> pd.DataFrame:
    """
    Filter TRADES to keep only those with entry during a specific regime.
    
    CRITICAL: Uses regime at ENTRY time, not exit (anti-lookahead).
    """
    if trades.empty:
        return trades
    
    # Get entry times from trades
    entry_times = trades['entry_time']
    
    # Map entry times to regimes
    filtered_trades = []
    for idx, row in trades.iterrows():
        entry_time = row['entry_time']
        # Find nearest regime data point
        if entry_time in regime_data.index:
            entry_regime = regime_data.loc[entry_time, regime_column]
            if entry_regime == regime:
                filtered_trades.append(row)
        else:
            # Find closest regime data point before entry
            prior = regime_data.index[regime_data.index <= entry_time]
            if len(prior) > 0:
                closest = prior[-1]
                entry_regime = regime_data.loc[closest, regime_column]
                if entry_regime == regime:
                    filtered_trades.append(row)
    
    if not filtered_trades:
        return pd.DataFrame(columns=trades.columns)
    
    return pd.DataFrame(filtered_trades)


def get_asset_params(asset: str) -> Dict:
    """Extract strategy params from asset config."""
    if asset not in ASSET_CONFIG:
        raise KeyError(f"Asset {asset} not found in ASSET_CONFIG")
    
    cfg = ASSET_CONFIG[asset]
    
    return build_strategy_params(
        sl_mult=cfg['atr']['sl_mult'],
        tp1_mult=cfg['atr']['tp1_mult'],
        tp2_mult=cfg['atr']['tp2_mult'],
        tp3_mult=cfg['atr']['tp3_mult'],
        tenkan=cfg['ichimoku']['tenkan'],
        kijun=cfg['ichimoku']['kijun'],
        tenkan_5=cfg['five_in_one']['tenkan_5'],
        kijun_5=cfg['five_in_one']['kijun_5'],
        displacement=cfg.get('displacement', 52)
    )


def run_stress_test(asset: str, regime: str) -> Dict:
    """
    Execute stress test on an isolated regime.
    
    APPROACH: Run backtest on FULL data, then filter TRADES by entry regime.
    This preserves indicator continuity while isolating regime performance.
    
    Args:
        asset: Asset code (e.g., 'ETH')
        regime: Regime to test (e.g., 'MARKDOWN')
    
    Returns:
        Dict with detailed results
    """
    print(f"\n{'='*60}")
    print(f"STRESS TEST: {asset} on regime {regime}")
    print(f"{'='*60}\n")
    
    # Determine regime column
    try:
        regime_column = get_regime_column(regime)
    except ValueError as e:
        return {
            'asset': asset,
            'regime': regime,
            'status': 'ERROR',
            'reason': str(e),
            'bars': 0,
            'pct': 0
        }
    
    # Load OHLCV data
    try:
        data = load_data(asset, data_dir=str(PROJECT_ROOT / "data"))
        if data.index.tz is None:
            data.index = data.index.tz_localize('UTC')
    except Exception as e:
        return {
            'asset': asset,
            'regime': regime,
            'status': 'ERROR',
            'reason': f'Failed to load OHLCV data: {e}',
            'bars': 0,
            'pct': 0
        }
    
    total_bars = len(data)
    print(f"Total data: {total_bars} bars")
    
    # Load regime data
    try:
        regime_data = load_regime_data(asset)
        if regime_data.index.tz is None:
            regime_data.index = regime_data.index.tz_localize('UTC')
    except Exception as e:
        return {
            'asset': asset,
            'regime': regime,
            'status': 'ERROR',
            'reason': f'Failed to load regime data: {e}',
            'bars': total_bars,
            'pct': 0
        }
    
    # Count bars in target regime
    common_index = data.index.intersection(regime_data.index)
    regime_aligned = regime_data.loc[common_index]
    n_bars_regime = (regime_aligned[regime_column] == regime).sum()
    pct = n_bars_regime / total_bars * 100 if total_bars > 0 else 0
    print(f"Bars in {regime}: {n_bars_regime} ({pct:.1f}%)")
    
    # Get PROD params
    try:
        params = get_asset_params(asset)
    except KeyError as e:
        return {
            'asset': asset,
            'regime': regime,
            'status': 'ERROR',
            'reason': str(e),
            'bars': n_bars_regime,
            'pct': pct
        }
    
    # Create strategy (convert dict to dataclass)
    strategy = _instantiate_strategy(FinalTriggerStrategy, params)
    
    # Create backtester
    config = BacktestConfig(
        initial_capital=10000.0,
        fees_bps=6.0,
        slippage_bps=2.0,
        sizing_mode='fixed',
        risk_per_trade=0.01,
        intrabar_order='stop_first'
    )
    backtester = VectorizedBacktester(config)
    
    # Run backtest on FULL data
    try:
        result = backtester.run(data, strategy)
    except Exception as e:
        return {
            'asset': asset,
            'regime': regime,
            'status': 'ERROR',
            'reason': f'Backtest error: {e}',
            'bars': n_bars_regime,
            'pct': pct
        }
    
    total_trades = len(result.trades)
    print(f"Total trades (all regimes): {total_trades}")
    
    # Filter trades by entry regime
    try:
        filtered_trades = filter_trades_by_regime(
            result.trades, regime_data, regime, regime_column
        )
    except Exception as e:
        return {
            'asset': asset,
            'regime': regime,
            'status': 'ERROR',
            'reason': f'Trade filter error: {e}',
            'bars': n_bars_regime,
            'pct': pct
        }
    
    n_trades = len(filtered_trades)
    print(f"Trades in {regime}: {n_trades} ({n_trades/total_trades*100:.1f}% of total)" if total_trades > 0 else f"Trades in {regime}: 0")
    
    # Check minimum trades
    if n_trades < 5:
        return {
            'asset': asset,
            'regime': regime,
            'status': 'SKIP',
            'reason': f'Insufficient trades ({n_trades} < 5 minimum)',
            'bars': n_bars_regime,
            'pct': pct,
            'sharpe': np.nan,
            'max_dd': np.nan,
            'n_trades': n_trades,
            'win_rate': np.nan,
            'total_return': np.nan
        }
    
    # Calculate metrics on filtered trades
    try:
        # Build equity curve from filtered trades
        if 'pnl' in filtered_trades.columns:
            pnl = filtered_trades['pnl'].sum()
            wins = (filtered_trades['pnl'] > 0).sum()
            win_rate = wins / n_trades * 100 if n_trades > 0 else 0
            total_return = pnl / config.initial_capital * 100
            
            # Calculate Sharpe from trade PnLs
            trade_returns = filtered_trades['pnl'] / config.initial_capital
            mean_ret = trade_returns.mean()
            std_ret = trade_returns.std()
            sharpe = (mean_ret / std_ret * np.sqrt(252)) if std_ret > 0 else 0
            
            # Max drawdown from cumulative PnL
            cum_pnl = filtered_trades['pnl'].cumsum()
            running_max = cum_pnl.cummax()
            drawdown = running_max - cum_pnl
            max_dd = (drawdown.max() / config.initial_capital * 100) if config.initial_capital > 0 else 0
        else:
            sharpe = 0
            max_dd = 0
            win_rate = 0
            total_return = 0
    except Exception as e:
        return {
            'asset': asset,
            'regime': regime,
            'status': 'ERROR',
            'reason': f'Metrics error: {e}',
            'bars': n_bars_regime,
            'pct': pct
        }
    
    # Verdict logic
    if n_trades < 10:
        verdict = 'INCONCLUSIVE - Insufficient trades (< 10)'
        status = 'INCONCLUSIVE'
    elif sharpe < -0.5:
        verdict = 'FAIL - Strongly negative Sharpe'
        status = 'FAIL'
    elif sharpe < 0:
        verdict = 'FAIL - Negative Sharpe'
        status = 'FAIL'
    elif sharpe < 0.5:
        verdict = 'MARGINAL - Low Sharpe'
        status = 'MARGINAL'
    elif sharpe < 1.0:
        verdict = 'PASS - Acceptable Sharpe'
        status = 'PASS'
    else:
        verdict = 'PASS - Good Sharpe'
        status = 'PASS'
    
    output = {
        'asset': asset,
        'regime': regime,
        'status': status,
        'verdict': verdict,
        'bars': n_bars_regime,
        'pct': round(pct, 1),
        'sharpe': round(sharpe, 2),
        'max_dd': round(max_dd, 2),
        'n_trades': n_trades,
        'win_rate': round(win_rate, 1),
        'total_return': round(total_return, 2)
    }
    
    print(f"\nResults:")
    print(f"  Sharpe: {sharpe:.2f}")
    print(f"  Max DD: {max_dd:.2f}%")
    print(f"  Trades: {n_trades}")
    print(f"  Win Rate: {win_rate:.1f}%")
    print(f"  Return: {total_return:.2f}%")
    print(f"\n  => {verdict}")
    
    return output


def main():
    parser = argparse.ArgumentParser(
        description='Regime Stress Test - FINAL TRIGGER v2',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/run_regime_stress_test.py --asset ETH --regime MARKDOWN
  python scripts/run_regime_stress_test.py --all-assets --regime MARKDOWN
  python scripts/run_regime_stress_test.py --all-assets --regime ACCUMULATION

Regimes:
  Crypto (Wyckoff): ACCUMULATION, MARKDOWN, MARKUP, DISTRIBUTION, CAPITULATION, RECOVERY
  Trend:           SIDEWAYS, WEAK_BULL, WEAK_BEAR, STRONG_BULL, STRONG_BEAR, REVERSAL
  Volatility:      COMPRESSED, NORMAL, ELEVATED, EXTREME
        """
    )
    parser.add_argument('--asset', type=str, help='Single asset to test (e.g., ETH)')
    parser.add_argument('--all-assets', action='store_true', help='Test all 14 PROD assets')
    parser.add_argument('--regime', type=str, required=True, help='Regime to isolate (e.g., MARKDOWN)')
    parser.add_argument('--output', type=str, help='Output CSV path (optional)')
    
    args = parser.parse_args()
    
    # Validation
    if not args.asset and not args.all_assets:
        parser.error('Either --asset or --all-assets is required')
    
    if args.asset and args.all_assets:
        parser.error('Cannot use both --asset and --all-assets')
    
    # Determine assets
    if args.all_assets:
        assets = PROD_ASSETS
        print(f"Testing {len(assets)} PROD assets on regime {args.regime}")
    else:
        assets = [args.asset.upper()]
    
    # Run tests
    results = []
    
    for i, asset in enumerate(assets, 1):
        print(f"\n[{i}/{len(assets)}] Testing {asset}...")
        
        try:
            result = run_stress_test(asset, args.regime)
            results.append(result)
        except Exception as e:
            print(f"\nERROR testing {asset}: {e}")
            results.append({
                'asset': asset,
                'regime': args.regime,
                'status': 'ERROR',
                'reason': str(e),
                'bars': 0,
                'pct': 0,
                'sharpe': np.nan,
                'max_dd': np.nan,
                'n_trades': 0,
                'win_rate': np.nan,
                'total_return': np.nan,
                'verdict': 'ERROR'
            })
    
    # Create DataFrame
    df = pd.DataFrame(results)
    
    # Summary
    print(f"\n{'='*70}")
    print(f"SUMMARY - STRESS TEST: {args.regime}")
    print(f"{'='*70}\n")
    
    summary_cols = ['asset', 'status', 'bars', 'pct', 'sharpe', 'n_trades', 'max_dd']
    available_cols = [c for c in summary_cols if c in df.columns]
    print(df[available_cols].to_string(index=False))
    
    # Statistics
    print(f"\n{'='*70}")
    print("STATISTICS")
    print(f"{'='*70}\n")
    
    valid_results = df[df['status'].isin(['PASS', 'MARGINAL', 'FAIL'])]
    
    if len(valid_results) > 0:
        n_fail = len(df[df['status'] == 'FAIL'])
        n_marginal = len(df[df['status'] == 'MARGINAL'])
        n_pass = len(df[df['status'] == 'PASS'])
        n_inconclusive = len(df[df['status'] == 'INCONCLUSIVE'])
        n_skip = len(df[df['status'] == 'SKIP'])
        n_error = len(df[df['status'] == 'ERROR'])
        
        print(f"Assets tested: {len(assets)}")
        print(f"  PASS: {n_pass}")
        print(f"  MARGINAL: {n_marginal}")
        print(f"  FAIL: {n_fail}")
        print(f"  INCONCLUSIVE: {n_inconclusive}")
        print(f"  SKIP: {n_skip}")
        print(f"  ERROR: {n_error}")
        
        if len(valid_results) > 0:
            mean_sharpe = valid_results['sharpe'].mean()
            mean_bars_pct = valid_results['pct'].mean()
            
            print(f"\nAverages (PASS/MARGINAL/FAIL only):")
            print(f"  Mean Sharpe: {mean_sharpe:.2f}")
            print(f"  Mean % bars in {args.regime}: {mean_bars_pct:.1f}%")
    
    # Save results
    if args.output:
        output_path = args.output
    else:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_path = f"outputs/stress_test_{args.regime}_{timestamp}.csv"
    
    df.to_csv(output_path, index=False)
    print(f"\nSaved: {output_path}")
    
    # Critical alerts
    print(f"\n{'='*70}")
    print("CRITICAL ALERTS")
    print(f"{'='*70}\n")
    
    fails = df[df['status'] == 'FAIL']
    if len(fails) > 0:
        print(f"[ALERT] {len(fails)} assets FAIL on {args.regime}!")
        print("\nFailed assets:")
        for _, row in fails.iterrows():
            sharpe_str = f"{row['sharpe']:.2f}" if pd.notna(row.get('sharpe')) else 'N/A'
            trades_str = row.get('n_trades', 'N/A')
            print(f"  - {row['asset']}: Sharpe {sharpe_str}, {trades_str} trades")
        
        print(f"\nRECOMMENDATION:")
        print(f"   These assets do NOT survive in {args.regime} regime.")
        print(f"   Live action: FLAT or HEDGE when this regime is detected.")
    else:
        print(f"[OK] No assets FAIL - strategy robust on {args.regime}")
    
    # Inconclusive/Skip warnings
    inconclusive = df[df['status'].isin(['INCONCLUSIVE', 'SKIP'])]
    if len(inconclusive) > 0:
        print(f"\n[WARNING] {len(inconclusive)} assets INCONCLUSIVE/SKIP:")
        for _, row in inconclusive.iterrows():
            reason = row.get('reason', row.get('verdict', 'N/A'))
            print(f"  - {row['asset']}: {reason}")
    
    print(f"\n{'='*70}\n")
    
    return df


if __name__ == '__main__':
    main()
