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
