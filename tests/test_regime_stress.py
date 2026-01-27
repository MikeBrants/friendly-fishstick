import sys
from pathlib import Path

import numpy as np
import pandas as pd

# Allow importing the script as a module
SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import run_regime_stress_test as rst


def test_resolve_regime_column():
    col, target = rst.resolve_regime_column("MARKDOWN")
    assert col == "crypto_regime"
    assert target == "MARKDOWN"

    col, target = rst.resolve_regime_column("SIDEWAYS")
    assert col == "trend_regime"
    assert target == "SIDEWAYS"


def test_filter_trades_by_entry_regime_uses_entry_time():
    idx = pd.to_datetime([
        "2026-01-01 00:00:00",
        "2026-01-01 01:00:00",
        "2026-01-01 02:00:00",
    ])
    regimes_df = pd.DataFrame(
        {
            "trend_regime": ["SIDEWAYS", "WEAK_BULL", "SIDEWAYS"],
            "crypto_regime": ["MARKDOWN", "MARKDOWN", "MARKUP"],
        },
        index=idx,
    )

    trades = pd.DataFrame(
        {
            "entry_time": [idx[0], idx[1], idx[0] + pd.Timedelta(minutes=30)],
            "pnl": [10.0, -5.0, 3.0],
        }
    )

    filtered = rst.filter_trades_by_entry_regime(
        trades,
        regimes_df,
        "trend_regime",
        "SIDEWAYS",
    )

    assert len(filtered) == 2


def test_evaluate_verdict_rules():
    assert rst.evaluate_verdict("MARKDOWN", 10, -999.0) == "PASS"
    assert rst.evaluate_verdict("MARKDOWN", 11, -2.1) == "FAIL"
    assert rst.evaluate_verdict("MARKDOWN", 11, -2.0) == "PASS"

    assert rst.evaluate_verdict("SIDEWAYS", 5, -0.1) == "EXCLU"
    assert rst.evaluate_verdict("SIDEWAYS", 5, 0.0) == "PASS"


def test_compute_trade_stats_basic():
    trades = pd.DataFrame(
        {
            "entry_time": pd.to_datetime([
                "2026-01-01 00:00:00",
                "2026-01-01 01:00:00",
            ]),
            "pnl": [100.0, -50.0],
        }
    )

    stats = rst.compute_trade_stats(trades, initial_capital=10000.0)
    assert stats.n_trades == 2
    assert np.isfinite(stats.max_dd)
