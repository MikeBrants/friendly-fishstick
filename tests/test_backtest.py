import pandas as pd

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


def test_equity_sizing_uses_net_pnl():
    index = pd.date_range("2020-01-01", periods=4, freq="h", tz="UTC")
    data = pd.DataFrame(
        {
            "open": [100.0, 100.0, 100.0, 100.0],
            "high": [100.0, 111.0, 100.0, 111.0],
            "low": [100.0, 99.0, 100.0, 99.0],
            "close": [100.0, 110.0, 100.0, 110.0],
            "volume": [1.0, 1.0, 1.0, 1.0],
        },
        index=index,
    )
    signals = pd.DataFrame(
        {
            "signal": [1, 0, 1, 0],
            "entry_price": [100.0, float("nan"), 100.0, float("nan")],
            "sl_price": [90.0, float("nan"), 90.0, float("nan")],
            "tp1_price": [110.0, float("nan"), 110.0, float("nan")],
            "tp2_price": [120.0, float("nan"), 120.0, float("nan")],
            "tp3_price": [130.0, float("nan"), 130.0, float("nan")],
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
        slippage_bps=0.0,
    )

    assert len(trades) == 2
    first_trade = trades.iloc[0]
    second_trade = trades.iloc[1]
    expected_equity = 10_000.0 + first_trade["net_pnl"]
    assert abs(second_trade["notional"] - expected_equity) < 1e-6
