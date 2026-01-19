import pytest

from crypto_backtest.engine.backtest import BacktestConfig
from crypto_backtest.examples.optimize_final_trigger import (
    BASE_PARAMS,
    SEARCH_SPACE_FULL,
    SEARCH_SPACE_QUICK,
    SEARCH_SPACE_TOGGLES,
    get_param_space,
)


def test_get_param_space_quick():
    param_space = get_param_space(mode="quick")
    assert param_space["base_params"] == BASE_PARAMS
    assert param_space["search_space"] == SEARCH_SPACE_QUICK
    assert isinstance(param_space["backtest_config"], BacktestConfig)


def test_get_param_space_full():
    param_space = get_param_space(mode="full")
    assert param_space["search_space"] == SEARCH_SPACE_FULL
    assert "five_in_one.fast_period" in param_space["search_space"]


def test_get_param_space_toggles_includes_booleans():
    param_space = get_param_space(mode="toggles")
    search_space = param_space["search_space"]
    for key in SEARCH_SPACE_TOGGLES:
        assert key in search_space


def test_get_param_space_unknown_mode():
    with pytest.raises(ValueError):
        get_param_space(mode="unknown")
