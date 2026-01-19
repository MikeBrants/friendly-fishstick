"""Analysis module for backtest metrics, validation, and visualization."""

from crypto_backtest.analysis.metrics import (
    calculate_all_metrics,
    calculate_sharpe_ratio,
    calculate_sortino_ratio,
    calculate_max_drawdown,
    calculate_calmar_ratio,
    calculate_win_rate,
    calculate_profit_factor,
)

from crypto_backtest.analysis.validation import (
    validate_backtest_results,
    check_look_ahead_bias,
)

from crypto_backtest.analysis.visualization import (
    plot_equity_curve,
    plot_drawdown,
    plot_price_with_signals,
    plot_pnl_distribution,
    plot_monthly_returns_heatmap,
    plot_trade_analysis,
    plot_rolling_metrics,
    plot_backtest_report,
    generate_html_report,
)

__all__ = [
    # Metrics
    "calculate_all_metrics",
    "calculate_sharpe_ratio",
    "calculate_sortino_ratio",
    "calculate_max_drawdown",
    "calculate_calmar_ratio",
    "calculate_win_rate",
    "calculate_profit_factor",
    # Validation
    "validate_backtest_results",
    "check_look_ahead_bias",
    # Visualization
    "plot_equity_curve",
    "plot_drawdown",
    "plot_price_with_signals",
    "plot_pnl_distribution",
    "plot_monthly_returns_heatmap",
    "plot_trade_analysis",
    "plot_rolling_metrics",
    "plot_backtest_report",
    "generate_html_report",
]
