import pandas as pd

from crypto_backtest.engine.backtest import VectorizedBacktester, BacktestConfig
from crypto_backtest.engine.position_manager import MultiTPPositionManager, PositionLeg


def _make_data(index: pd.DatetimeIndex) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "open": [100.0, 100.0],
            "high": [100.0, 106.0],
            "low": [100.0, 94.0],
            "close": [100.0, 100.0],
            "volume": [1.0, 1.0],
        },
        index=index,
    )


def _make_signals(index: pd.DatetimeIndex) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "signal": [1, 0],
            "entry_price": [100.0, float("nan")],
            "sl_price": [95.0, float("nan")],
            "tp1_price": [105.0, float("nan")],
            "tp2_price": [110.0, float("nan")],
            "tp3_price": [115.0, float("nan")],
        },
        index=index,
    )


def test_intrabar_order_stop_first():
    index = pd.date_range("2020-01-01", periods=2, freq="h", tz="UTC")
    data = _make_data(index)
    signals = _make_signals(index)
    manager = MultiTPPositionManager([PositionLeg(size=1.0, tp_multiple=2.0)])

    trades = manager.simulate(
        signals,
        data,
        initial_capital=10_000.0,
        sizing_mode="fixed",
        intrabar_order="stop_first",
    )

    assert len(trades) == 1
    assert trades.iloc[0]["exit_reason"] == "stop"


def test_intrabar_order_tp_first():
    index = pd.date_range("2020-01-01", periods=2, freq="h", tz="UTC")
    data = _make_data(index)
    signals = _make_signals(index)
    manager = MultiTPPositionManager([PositionLeg(size=1.0, tp_multiple=2.0)])

    trades = manager.simulate(
        signals,
        data,
        initial_capital=10_000.0,
        sizing_mode="fixed",
        intrabar_order="tp_first",
    )

    assert len(trades) == 1
    assert trades.iloc[0]["exit_reason"] == "tp1"


def test_three_legs_tp1_then_stop():
    index = pd.date_range("2020-01-01", periods=3, freq="h", tz="UTC")
    data = pd.DataFrame(
        {
            "open": [100.0, 100.0, 100.0],
            "high": [100.0, 111.0, 105.0],
            "low": [100.0, 99.0, 99.0],
            "close": [100.0, 105.0, 100.0],
            "volume": [1.0, 1.0, 1.0],
        },
        index=index,
    )
    signals = pd.DataFrame(
        {
            "signal": [1, 0, 0],
            "entry_price": [100.0, float("nan"), float("nan")],
            "sl_price": [90.0, float("nan"), float("nan")],
            "tp1_price": [110.0, float("nan"), float("nan")],
            "tp2_price": [120.0, float("nan"), float("nan")],
            "tp3_price": [130.0, float("nan"), float("nan")],
        },
        index=index,
    )
    manager = MultiTPPositionManager(
        [
            PositionLeg(size=0.5, tp_multiple=2.0),
            PositionLeg(size=0.3, tp_multiple=6.0),
            PositionLeg(size=0.2, tp_multiple=10.0),
        ]
    )

    trades = manager.simulate(
        signals,
        data,
        initial_capital=10_000.0,
        sizing_mode="fixed",
        intrabar_order="stop_first",
    )

    assert len(trades) == 3
    assert (trades["exit_reason"] == "tp1").sum() == 1
    stop_trades = trades[trades["exit_reason"] == "stop"]
    assert len(stop_trades) == 2
    assert (stop_trades["exit_price"] == 100.0).all()


def test_tp1_tp2_same_bar_then_stop_moves_tp1():
    index = pd.date_range("2020-01-01", periods=3, freq="h", tz="UTC")
    data = pd.DataFrame(
        {
            "open": [100.0, 100.0, 100.0],
            "high": [100.0, 125.0, 115.0],
            "low": [100.0, 99.0, 109.0],
            "close": [100.0, 120.0, 110.0],
            "volume": [1.0, 1.0, 1.0],
        },
        index=index,
    )
    signals = pd.DataFrame(
        {
            "signal": [1, 0, 0],
            "entry_price": [100.0, float("nan"), float("nan")],
            "sl_price": [90.0, float("nan"), float("nan")],
            "tp1_price": [110.0, float("nan"), float("nan")],
            "tp2_price": [120.0, float("nan"), float("nan")],
            "tp3_price": [130.0, float("nan"), float("nan")],
        },
        index=index,
    )
    manager = MultiTPPositionManager(
        [
            PositionLeg(size=0.5, tp_multiple=2.0),
            PositionLeg(size=0.3, tp_multiple=6.0),
            PositionLeg(size=0.2, tp_multiple=10.0),
        ]
    )

    trades = manager.simulate(
        signals,
        data,
        initial_capital=10_000.0,
        sizing_mode="fixed",
        intrabar_order="tp_first",
    )

    assert len(trades) == 3
    assert (trades["exit_reason"] == "tp1").sum() == 1
    assert (trades["exit_reason"] == "tp2").sum() == 1
    stop_trades = trades[trades["exit_reason"] == "stop"]
    assert len(stop_trades) == 1
    assert float(stop_trades.iloc[0]["exit_price"]) == 110.0


def test_short_tp1_then_stop():
    index = pd.date_range("2020-01-01", periods=3, freq="h", tz="UTC")
    data = pd.DataFrame(
        {
            "open": [100.0, 100.0, 100.0],
            "high": [100.0, 105.0, 101.0],
            "low": [100.0, 89.0, 95.0],
            "close": [100.0, 90.0, 100.0],
            "volume": [1.0, 1.0, 1.0],
        },
        index=index,
    )
    signals = pd.DataFrame(
        {
            "signal": [-1, 0, 0],
            "entry_price": [100.0, float("nan"), float("nan")],
            "sl_price": [110.0, float("nan"), float("nan")],
            "tp1_price": [90.0, float("nan"), float("nan")],
            "tp2_price": [80.0, float("nan"), float("nan")],
            "tp3_price": [70.0, float("nan"), float("nan")],
        },
        index=index,
    )
    manager = MultiTPPositionManager(
        [
            PositionLeg(size=0.5, tp_multiple=2.0),
            PositionLeg(size=0.3, tp_multiple=6.0),
            PositionLeg(size=0.2, tp_multiple=10.0),
        ]
    )

    trades = manager.simulate(
        signals,
        data,
        initial_capital=10_000.0,
        sizing_mode="fixed",
        intrabar_order="stop_first",
    )

    assert len(trades) == 3
    assert (trades["exit_reason"] == "tp1").sum() == 1
    stop_trades = trades[trades["exit_reason"] == "stop"]
    assert len(stop_trades) == 2
    assert (stop_trades["exit_price"] == 100.0).all()


# ============================================================
# Tests sizing_mode="equity" (compounding net of costs)
# ============================================================


def test_sizing_mode_equity_compounding():
    """Verify that net_pnl is used for equity compounding, not gross_pnl."""
    index = pd.date_range("2020-01-01", periods=3, freq="h", tz="UTC")
    # Trade 1: entry at 100, TP at 110 -> +10% gross
    data = pd.DataFrame(
        {
            "open": [100.0, 100.0, 100.0],
            "high": [100.0, 115.0, 100.0],
            "low": [100.0, 99.0, 99.0],
            "close": [100.0, 110.0, 100.0],
            "volume": [1.0, 1.0, 1.0],
        },
        index=index,
    )
    signals = pd.DataFrame(
        {
            "signal": [1, 0, 0],
            "entry_price": [100.0, float("nan"), float("nan")],
            "sl_price": [90.0, float("nan"), float("nan")],
            "tp1_price": [110.0, float("nan"), float("nan")],
            "tp2_price": [120.0, float("nan"), float("nan")],
            "tp3_price": [130.0, float("nan"), float("nan")],
        },
        index=index,
    )
    manager = MultiTPPositionManager([PositionLeg(size=1.0, tp_multiple=2.0)])

    # With fees/slippage, net_pnl < gross_pnl
    trades = manager.simulate(
        signals,
        data,
        initial_capital=10_000.0,
        sizing_mode="equity",
        intrabar_order="tp_first",
        fees_bps=10.0,
        slippage_bps=5.0,
    )

    assert len(trades) == 1
    trade = trades.iloc[0]
    # risk_amount = 10000 * 0.005 = 50, stop_distance = 10/100 = 0.1
    # notional = 50 / 0.1 = 500
    assert abs(trade["notional"] - 500.0) < 1e-6
    # gross_pnl = (110 - 100) * (500 / 100) = 50
    assert abs(trade["gross_pnl"] - 50.0) < 1e-6
    # costs = 500 * (15/10000) * 2 = 1.5
    assert abs(trade["costs"] - 1.5) < 1e-6
    # net_pnl = 50 - 1.5 = 48.5
    assert abs(trade["net_pnl"] - 48.5) < 1e-6


def test_sizing_mode_equity_second_trade_uses_updated_equity():
    """Verify second trade notional is based on equity after first trade net PnL."""
    index = pd.date_range("2020-01-01", periods=5, freq="h", tz="UTC")
    # Trade 1: entry bar 0, TP bar 1
    # Trade 2: entry bar 2, TP bar 3
    data = pd.DataFrame(
        {
            "open": [100.0, 100.0, 100.0, 100.0, 100.0],
            "high": [100.0, 115.0, 100.0, 115.0, 100.0],
            "low": [100.0, 99.0, 100.0, 99.0, 100.0],
            "close": [100.0, 110.0, 100.0, 110.0, 100.0],
            "volume": [1.0, 1.0, 1.0, 1.0, 1.0],
        },
        index=index,
    )
    signals = pd.DataFrame(
        {
            "signal": [1, 0, 1, 0, 0],
            "entry_price": [100.0, float("nan"), 100.0, float("nan"), float("nan")],
            "sl_price": [90.0, float("nan"), 90.0, float("nan"), float("nan")],
            "tp1_price": [110.0, float("nan"), 110.0, float("nan"), float("nan")],
            "tp2_price": [120.0, float("nan"), 120.0, float("nan"), float("nan")],
            "tp3_price": [130.0, float("nan"), 130.0, float("nan"), float("nan")],
        },
        index=index,
    )
    manager = MultiTPPositionManager([PositionLeg(size=1.0, tp_multiple=2.0)])

    trades = manager.simulate(
        signals,
        data,
        initial_capital=10_000.0,
        sizing_mode="equity",
        intrabar_order="tp_first",
        fees_bps=10.0,
        slippage_bps=5.0,
    )

    assert len(trades) == 2
    # Trade 1: notional = 500, net_pnl = 48.5 -> equity = 10048.5
    trade1 = trades.iloc[0]
    assert abs(trade1["notional"] - 500.0) < 1e-6
    assert abs(trade1["net_pnl"] - 48.5) < 1e-6

    # Trade 2: notional scales with equity after trade 1
    trade2 = trades.iloc[1]
    # equity = 10048.5, risk_amount = 50.2425, stop_distance = 0.1
    expected_notional = 50.2425 / 0.1
    assert abs(trade2["notional"] - expected_notional) < 1e-6
    # gross_pnl = (110 - 100) * (notional / 100)
    expected_gross = (110.0 - 100.0) * (expected_notional / 100.0)
    assert abs(trade2["gross_pnl"] - expected_gross) < 1e-6
    # costs = notional * (15/10000) * 2
    expected_costs = expected_notional * (15 / 10_000) * 2
    assert abs(trade2["costs"] - expected_costs) < 1e-6
