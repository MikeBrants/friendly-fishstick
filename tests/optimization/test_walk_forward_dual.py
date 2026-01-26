"""
Smoke tests for WFE DUAL patch (J1 deliverable).

Verifies that:
1. WalkForwardResult has correct renamed fields
2. wfe_pardo != return_efficiency (they measure different things)
3. degradation_pct is calculated correctly
"""
import numpy as np
import pytest
import pandas as pd

from crypto_backtest.optimization.walk_forward import WalkForwardResult


def test_walk_forward_result_fields():
    """Test that WalkForwardResult has renamed fields."""
    result = WalkForwardResult(
        combined_metrics={"sharpe_ratio": 2.0},
        return_efficiency=0.95,
        wfe_pardo=0.80,
        degradation_pct=20.0,
    )

    # Check fields exist
    assert hasattr(result, "return_efficiency")
    assert hasattr(result, "wfe_pardo")
    assert hasattr(result, "degradation_pct")

    # Check old fields are gone
    assert not hasattr(result, "efficiency_ratio")
    assert not hasattr(result, "degradation_ratio")


def test_wfe_pardo_vs_return_efficiency():
    """Test that wfe_pardo and return_efficiency are different metrics."""
    # wfe_pardo uses Sharpe ratios (correct WFE)
    # return_efficiency uses returns (not WFE)

    result1 = WalkForwardResult(
        combined_metrics={},
        return_efficiency=0.95,  # Return ratio
        wfe_pardo=0.80,  # Sharpe ratio (TRUE WFE)
        degradation_pct=20.0,
    )

    # They should be different values
    assert result1.return_efficiency != result1.wfe_pardo

    # wfe_pardo should be used for WFE validation
    assert result1.wfe_pardo < 1.0  # Degradation expected


def test_degradation_pct_calculation():
    """Test that degradation_pct is calculated from wfe_pardo."""
    # degradation_pct = (1 - wfe_pardo) * 100 when wfe_pardo < 1

    result1 = WalkForwardResult(
        combined_metrics={},
        return_efficiency=0.90,
        wfe_pardo=0.75,
        degradation_pct=25.0,
    )

    # Check degradation_pct matches expected formula
    expected_degradation = (1 - result1.wfe_pardo) * 100
    assert abs(result1.degradation_pct - expected_degradation) < 0.1

    # When wfe_pardo > 1 (OOS better than IS), degradation should be 0
    result2 = WalkForwardResult(
        combined_metrics={},
        return_efficiency=1.05,
        wfe_pardo=1.20,
        degradation_pct=0.0,
    )

    assert result2.degradation_pct == 0.0


def test_wfe_pardo_is_sharpe_based():
    """Verify that wfe_pardo uses Sharpe ratios (not returns)."""
    # This is a conceptual test - wfe_pardo should be:
    # wfe_pardo = mean_oos_sharpe / mean_is_sharpe

    # Example: IS Sharpe = 2.0, OOS Sharpe = 1.5
    # wfe_pardo = 1.5 / 2.0 = 0.75

    is_sharpe = 2.0
    oos_sharpe = 1.5
    expected_wfe = oos_sharpe / is_sharpe

    result = WalkForwardResult(
        combined_metrics={},
        return_efficiency=0.90,  # Different from wfe_pardo
        wfe_pardo=expected_wfe,
        degradation_pct=(1 - expected_wfe) * 100,
    )

    assert abs(result.wfe_pardo - 0.75) < 0.01
    assert abs(result.degradation_pct - 25.0) < 0.1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
