#!/usr/bin/env python3
"""
Signal Parity Validation Script - ETH Focus

This script validates that Python generates SHORT signals correctly
after the TS5/KS5 fix (Issue #18, PR #19).

Usage:
    python scripts/validate_signal_parity.py --asset ETH
    python scripts/validate_signal_parity.py --asset ETH --data data/ETHUSDT_1h.parquet
    python scripts/validate_signal_parity.py --all

Output:
    - Config comparison table (Pine vs Python)
    - Signal counts (LONG/SHORT)
    - Parity verdict (PASS/FAIL)
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from dataclasses import dataclass
from typing import Optional

import numpy as np
import pandas as pd

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from configs.asset_config import (
    get_asset_config,
    build_params_for_asset,
    ASSET_CONFIGS,
)
from crypto_backtest.strategies.final_trigger import FinalTriggerStrategy


# Pine reference configs (extracted from PineScript presets)
PINE_REFERENCE = {
    "ETH": {
        "tenkan": 17, "kijun": 31,
        "tenkan_5": 13, "kijun_5": 20,
        "sl_mult": 2.0, "tp1_mult": 3.0, "tp2_mult": 7.0, "tp3_mult": 11.0,
    },
    "BTC": {
        "tenkan": 12, "kijun": 28,
        "tenkan_5": 9, "kijun_5": 29,
        "sl_mult": 2.6, "tp1_mult": 1.5, "tp2_mult": 4.0, "tp3_mult": 7.0,
    },
    "SHIB": {
        "tenkan": 7, "kijun": 31,
        "tenkan_5": 8, "kijun_5": 30,
        "sl_mult": 2.2, "tp1_mult": 3.0, "tp2_mult": 7.0, "tp3_mult": 12.0,
    },
    "DOT": {
        "tenkan": 10, "kijun": 32,
        "tenkan_5": 12, "kijun_5": 27,
        "sl_mult": 2.2, "tp1_mult": 3.0, "tp2_mult": 7.0, "tp3_mult": 12.0,
    },
    "NEAR": {
        "tenkan": 9, "kijun": 29,
        "tenkan_5": 10, "kijun_5": 26,
        "sl_mult": 2.3, "tp1_mult": 2.5, "tp2_mult": 6.0, "tp3_mult": 11.0,
    },
    "DOGE": {
        "tenkan": 12, "kijun": 28,
        "tenkan_5": 10, "kijun_5": 28,
        "sl_mult": 2.4, "tp1_mult": 2.0, "tp2_mult": 5.0, "tp3_mult": 10.0,
    },
}


@dataclass
class ParityResult:
    """Result of parity validation"""
    asset: str
    config_match: bool
    signals_generated: int
    longs: int
    shorts: int
    short_ratio: float
    alternation_ok: bool
    first_is_long: bool
    verdict: str
    details: str


def generate_synthetic_data(n_bars: int = 2000, seed: int = 42) -> pd.DataFrame:
    """Generate synthetic OHLCV with alternating trends.
    
    Creates clear bull/bear cycles to test signal alternation.
    """
    np.random.seed(seed)
    
    # Start price
    price = 3000.0  # ETH-like
    prices = [price]
    
    for i in range(1, n_bars):
        # Cycle every ~200 bars between bull (1) and bear (-1)
        cycle = (i // 200) % 4
        if cycle in [0, 1]:  # 400 bars bull
            trend = 0.0003
        else:  # 400 bars bear
            trend = -0.0003
        
        # Add noise
        change = np.random.normal(trend, 0.008)
        price = price * (1 + change)
        price = max(price, 100)  # Floor
        prices.append(price)
    
    close = pd.Series(prices)
    
    # Generate OHLCV
    noise = np.abs(np.random.normal(0, 0.003, n_bars))
    high = close * (1 + noise)
    low = close * (1 - noise)
    open_ = close.shift(1).fillna(close.iloc[0])
    volume = pd.Series(np.random.uniform(1e8, 5e8, n_bars))
    
    df = pd.DataFrame({
        "open": open_,
        "high": high,
        "low": low,
        "close": close,
        "volume": volume,
    })
    
    # Add datetime index
    df.index = pd.date_range("2024-01-01", periods=n_bars, freq="1h")
    df.index.name = "timestamp"
    
    return df


def compare_configs(asset: str) -> tuple[bool, str]:
    """Compare Python config vs Pine reference."""
    if asset not in PINE_REFERENCE:
        return True, f"No Pine reference for {asset}"
    
    pine = PINE_REFERENCE[asset]
    python = get_asset_config(asset)
    
    mismatches = []
    for key in ["tenkan", "kijun", "tenkan_5", "kijun_5"]:
        if pine.get(key) != python.get(key):
            mismatches.append(f"{key}: Pine={pine.get(key)} vs Python={python.get(key)}")
    
    if mismatches:
        return False, "; ".join(mismatches)
    
    return True, "All params match Pine reference"


def check_alternation(signals: pd.Series) -> tuple[bool, str]:
    """Check that signals alternate LONG→SHORT→LONG."""
    entries = signals[signals != 0]
    
    if len(entries) < 2:
        return True, "Too few signals to check alternation"
    
    violations = []
    for i in range(1, len(entries)):
        if entries.iloc[i] == entries.iloc[i-1]:
            violations.append(i)
    
    if violations:
        return False, f"{len(violations)} alternation violations at indices: {violations[:5]}"
    
    return True, f"All {len(entries)} signals alternate correctly"


def validate_asset(asset: str, data: Optional[pd.DataFrame] = None) -> ParityResult:
    """Run full parity validation for one asset."""
    print(f"\n{'='*60}")
    print(f"  VALIDATING: {asset}")
    print(f"{'='*60}")
    
    # 1. Compare configs
    config_match, config_details = compare_configs(asset)
    print(f"\n[Config] Match: {config_match}")
    print(f"         {config_details}")
    
    # 2. Build params and show TS5/KS5
    try:
        params = build_params_for_asset(asset)
        print(f"\n[Params] PUZZLE: tenkan={params.ichimoku.tenkan_period}, kijun={params.ichimoku.kijun_period}")
        print(f"         5-in-1: TS5={params.five_in_one.tenkan_5}, KS5={params.five_in_one.kijun_5}")
    except Exception as e:
        return ParityResult(
            asset=asset,
            config_match=False,
            signals_generated=0,
            longs=0,
            shorts=0,
            short_ratio=0.0,
            alternation_ok=False,
            first_is_long=False,
            verdict="FAIL",
            details=f"Failed to build params: {e}",
        )
    
    # 3. Generate signals
    if data is None:
        print(f"\n[Data] Using synthetic data (2000 bars)")
        data = generate_synthetic_data(2000)
    else:
        print(f"\n[Data] Using provided data ({len(data)} bars)")
    
    strategy = FinalTriggerStrategy(params)
    signals_df = strategy.generate_signals(data)
    signals = signals_df["signal"]
    
    # 4. Count signals
    longs = (signals == 1).sum()
    shorts = (signals == -1).sum()
    total = longs + shorts
    short_ratio = shorts / total if total > 0 else 0.0
    
    print(f"\n[Signals] Total: {total}")
    print(f"          LONGs: {longs} ({longs/total*100:.1f}%)" if total > 0 else "          LONGs: 0")
    print(f"          SHORTs: {shorts} ({shorts/total*100:.1f}%)" if total > 0 else "          SHORTs: 0")
    
    # 5. Check alternation
    alternation_ok, alt_details = check_alternation(signals)
    print(f"\n[Alternation] OK: {alternation_ok}")
    print(f"              {alt_details}")
    
    # 6. Check first signal
    entries = signals[signals != 0]
    first_is_long = entries.iloc[0] == 1 if len(entries) > 0 else True
    print(f"\n[First Signal] Is LONG: {first_is_long}")
    
    # 7. Determine verdict
    issues = []
    if not config_match:
        issues.append("config mismatch")
    if shorts == 0 and total > 5:
        issues.append("NO SHORTS generated")
    if not alternation_ok:
        issues.append("alternation broken")
    if not first_is_long:
        issues.append("first signal not LONG")
    
    verdict = "PASS" if not issues else "FAIL"
    details = "; ".join(issues) if issues else "All checks passed"
    
    print(f"\n{'='*60}")
    print(f"  VERDICT: {verdict}")
    print(f"  {details}")
    print(f"{'='*60}")
    
    return ParityResult(
        asset=asset,
        config_match=config_match,
        signals_generated=total,
        longs=longs,
        shorts=shorts,
        short_ratio=short_ratio,
        alternation_ok=alternation_ok,
        first_is_long=first_is_long,
        verdict=verdict,
        details=details,
    )


def print_summary(results: list[ParityResult]) -> None:
    """Print summary table of all results."""
    print("\n" + "="*80)
    print("                    SIGNAL PARITY VALIDATION SUMMARY")
    print("="*80)
    print(f"{'Asset':<8} {'Config':<8} {'Signals':<10} {'LONGs':<8} {'SHORTs':<8} {'Ratio':<8} {'Alt':<6} {'Verdict':<8}")
    print("-"*80)
    
    for r in results:
        print(
            f"{r.asset:<8} "
            f"{'OK' if r.config_match else 'FAIL':<8} "
            f"{r.signals_generated:<10} "
            f"{r.longs:<8} "
            f"{r.shorts:<8} "
            f"{r.short_ratio*100:.1f}%{'  ':<4} "
            f"{'OK' if r.alternation_ok else 'FAIL':<6} "
            f"{'PASS' if r.verdict == 'PASS' else 'FAIL':<8}"
        )
    
    print("-"*80)
    passed = sum(1 for r in results if r.verdict == "PASS")
    print(f"Total: {passed}/{len(results)} PASS")
    print("="*80)


def main():
    parser = argparse.ArgumentParser(description="Validate signal parity Pine/Python")
    parser.add_argument("--asset", type=str, help="Asset to validate (e.g., ETH)")
    parser.add_argument("--all", action="store_true", help="Validate all configured assets")
    parser.add_argument("--data", type=str, help="Path to OHLCV parquet file")
    parser.add_argument("--prod-only", action="store_true", help="Only validate PROD assets")
    args = parser.parse_args()
    
    # Load data if provided
    data = None
    if args.data:
        path = Path(args.data)
        if not path.exists():
            print(f"ERROR: Data file not found: {path}")
            sys.exit(1)
        data = pd.read_parquet(path)
        print(f"Loaded {len(data)} bars from {path}")
    
    # Determine assets to validate
    if args.all:
        assets = list(ASSET_CONFIGS.keys())
    elif args.asset:
        assets = [args.asset.upper()]
    else:
        # Default: ETH (the main test case for TS5/KS5 bug)
        assets = ["ETH"]
    
    if args.prod_only:
        # Filter to known PROD assets
        prod_assets = {"BTC", "ETH", "SHIB", "DOT", "NEAR", "DOGE", "TIA", "MINA", "OSMO", "JOE", "FET", "OP"}
        assets = [a for a in assets if a in prod_assets]
    
    # Run validations
    results = []
    for asset in assets:
        if asset not in ASSET_CONFIGS:
            print(f"\n⚠️  Skipping {asset} - not in ASSET_CONFIGS")
            continue
        result = validate_asset(asset, data)
        results.append(result)
    
    # Print summary
    print_summary(results)
    
    # Exit code
    failed = sum(1 for r in results if r.verdict == "FAIL")
    sys.exit(1 if failed > 0 else 0)


if __name__ == "__main__":
    main()
