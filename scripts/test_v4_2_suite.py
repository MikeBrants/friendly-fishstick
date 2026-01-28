"""v4.2 unit test suite."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd


def _run(cmd: list[str]) -> None:
    result = subprocess.run(cmd, check=False)
    if result.returncode != 0:
        raise SystemExit(result.returncode)


def _portfolio_corr_unit() -> None:
    rng = np.random.default_rng(42)
    long_returns = rng.normal(0, 1, 1000)
    short_returns = rng.normal(0, 1, 1000)
    ret_eps = 1e-12
    active_long = np.abs(long_returns) > ret_eps
    active_short = np.abs(short_returns) > ret_eps
    active_union = active_long | active_short
    lr = long_returns[active_union]
    sr = short_returns[active_union]
    corr = float(np.corrcoef(lr, sr)[0, 1])
    assert -1.0 <= corr <= 1.0


def _holdout_slicing_unit() -> None:
    idx = pd.date_range("2020-01-01", periods=24 * 100, freq="H", tz="UTC")
    df = pd.DataFrame({"close": np.arange(len(idx))}, index=idx)
    end_ts = idx[-1]
    sliced = df.loc[: end_ts - pd.DateOffset(months=1)]
    assert len(sliced) < len(df)


def main() -> None:
    _run([sys.executable, "scripts/validate_configs.py"])
    _run([sys.executable, "scripts/test_direction_toggles.py"])
    _portfolio_corr_unit()
    _holdout_slicing_unit()
    print("PASS")


if __name__ == "__main__":
    main()