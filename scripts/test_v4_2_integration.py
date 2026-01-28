"""v4.2 integration checks."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from crypto_backtest.validation.pbo_legacy import probability_of_backtest_overfitting
from crypto_backtest.validation.pbo_cscv import cscv_pbo_compat
from crypto_backtest.v4.backtest_adapter import run_coupled_backtest


def smoke() -> None:
    returns = np.random.randn(10, 1000)
    proxy = probability_of_backtest_overfitting(returns, n_splits=8)
    cscv = cscv_pbo_compat(returns, folds=10, purge_bars=5, embargo_bars=0, annualization_factor=8760)
    assert 0.0 <= proxy.pbo <= 1.0
    assert 0.0 <= float(cscv.get("pbo")) <= 1.0


def asset_check(asset: str) -> None:
    parquet = Path("data") / f"{asset}_1H.parquet"
    csv = Path("data") / f"Binance_{asset}USDT_1h.csv"
    if not parquet.exists() and not csv.exists():
        print(f"SKIP: no data for {asset}")
        return
    result = run_coupled_backtest(asset=asset, recipe_config={}, mode="combined")
    if not result.get("metrics"):
        raise RuntimeError("No metrics returned from backtest")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--asset", default=None)
    args = parser.parse_args()

    if args.smoke:
        smoke()
        print("PASS")
        return
    if args.asset:
        asset_check(args.asset)
        print("PASS")
        return

    parser.error("Provide --smoke or --asset")


if __name__ == "__main__":
    main()