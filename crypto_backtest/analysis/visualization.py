"""Visualization helpers using Plotly."""

from __future__ import annotations

from typing import Optional
import numpy as np
import pandas as pd


def plot_equity_curve(equity_curve: pd.Series):
    """Create an interactive equity curve plot."""
    if equity_curve.empty:
        raise ValueError("equity_curve is empty")

    try:
        import plotly.graph_objects as go
    except ImportError as exc:
        raise ImportError("plotly is required for visualization") from exc

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=equity_curve.index,
            y=equity_curve.values,
            mode="lines",
            name="Equity",
            line=dict(color="#2E86AB", width=2),
        )
    )
    fig.update_layout(
        title="Equity Curve",
        xaxis_title="Time",
        yaxis_title="Equity ($)",
        template="plotly_white",
        hovermode="x unified",
    )
    return fig


def plot_drawdown(equity_curve: pd.Series):
    """Create a drawdown chart."""
    try:
        import plotly.graph_objects as go
    except ImportError as exc:
        raise ImportError("plotly is required for visualization") from exc

    if equity_curve.empty:
        raise ValueError("equity_curve is empty")

    peak = equity_curve.cummax()
    drawdown = (equity_curve - peak) / peak * 100

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=drawdown.index,
            y=drawdown.values,
            mode="lines",
            name="Drawdown",
            fill="tozeroy",
            line=dict(color="#E74C3C", width=1),
            fillcolor="rgba(231, 76, 60, 0.3)",
        )
    )
    fig.update_layout(
        title="Drawdown",
        xaxis_title="Time",
        yaxis_title="Drawdown (%)",
        template="plotly_white",
        hovermode="x unified",
    )
    return fig


def plot_price_with_signals(
    data: pd.DataFrame,
    trades: pd.DataFrame,
    show_volume: bool = True,
):
    """Plot price chart with entry/exit markers."""
    try:
        import plotly.graph_objects as go
        from plotly.subplots import make_subplots
    except ImportError as exc:
        raise ImportError("plotly is required for visualization") from exc

    if data.empty:
        raise ValueError("data is empty")

    rows = 2 if show_volume else 1
    row_heights = [0.7, 0.3] if show_volume else [1.0]

    fig = make_subplots(
        rows=rows,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.05,
        row_heights=row_heights,
    )

    # Candlestick chart
    fig.add_trace(
        go.Candlestick(
            x=data.index,
            open=data["open"],
            high=data["high"],
            low=data["low"],
            close=data["close"],
            name="Price",
            increasing_line_color="#26A69A",
            decreasing_line_color="#EF5350",
        ),
        row=1,
        col=1,
    )

    # Add trade markers if trades exist
    if not trades.empty:
        # Entry points (long = green triangle up, short = red triangle down)
        if "entry_time" in trades.columns and "entry_price" in trades.columns:
            long_entries = trades[trades.get("direction", 1) > 0]
            short_entries = trades[trades.get("direction", 1) < 0]

            if not long_entries.empty:
                fig.add_trace(
                    go.Scatter(
                        x=long_entries["entry_time"],
                        y=long_entries["entry_price"],
                        mode="markers",
                        marker=dict(
                            symbol="triangle-up",
                            size=12,
                            color="#00C853",
                            line=dict(width=1, color="white"),
                        ),
                        name="Long Entry",
                        hovertemplate="Long Entry<br>Price: %{y:.2f}<br>Time: %{x}<extra></extra>",
                    ),
                    row=1,
                    col=1,
                )

            if not short_entries.empty:
                fig.add_trace(
                    go.Scatter(
                        x=short_entries["entry_time"],
                        y=short_entries["entry_price"],
                        mode="markers",
                        marker=dict(
                            symbol="triangle-down",
                            size=12,
                            color="#FF1744",
                            line=dict(width=1, color="white"),
                        ),
                        name="Short Entry",
                        hovertemplate="Short Entry<br>Price: %{y:.2f}<br>Time: %{x}<extra></extra>",
                    ),
                    row=1,
                    col=1,
                )

        # Exit points
        if "exit_time" in trades.columns and "exit_price" in trades.columns:
            exits = trades.dropna(subset=["exit_time", "exit_price"])
            if not exits.empty:
                # Color based on PnL
                colors = ["#00C853" if pnl > 0 else "#FF1744" for pnl in exits.get("pnl", [0] * len(exits))]
                fig.add_trace(
                    go.Scatter(
                        x=exits["exit_time"],
                        y=exits["exit_price"],
                        mode="markers",
                        marker=dict(
                            symbol="x",
                            size=10,
                            color=colors,
                            line=dict(width=2),
                        ),
                        name="Exit",
                        hovertemplate="Exit<br>Price: %{y:.2f}<br>Time: %{x}<extra></extra>",
                    ),
                    row=1,
                    col=1,
                )

    # Volume chart
    if show_volume and "volume" in data.columns:
        colors = [
            "#26A69A" if c >= o else "#EF5350"
            for o, c in zip(data["open"], data["close"])
        ]
        fig.add_trace(
            go.Bar(
                x=data.index,
                y=data["volume"],
                name="Volume",
                marker_color=colors,
                opacity=0.7,
            ),
            row=2,
            col=1,
        )

    fig.update_layout(
        title="Price Chart with Trade Signals",
        template="plotly_white",
        xaxis_rangeslider_visible=False,
        hovermode="x unified",
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )

    return fig


def plot_pnl_distribution(trades: pd.DataFrame):
    """Plot PnL distribution histogram."""
    try:
        import plotly.graph_objects as go
    except ImportError as exc:
        raise ImportError("plotly is required for visualization") from exc

    if trades.empty or "pnl" not in trades.columns:
        raise ValueError("trades must contain 'pnl' column")

    pnl = trades["pnl"].dropna()
    wins = pnl[pnl > 0]
    losses = pnl[pnl <= 0]

    fig = go.Figure()

    # Wins histogram
    fig.add_trace(
        go.Histogram(
            x=wins,
            name=f"Wins ({len(wins)})",
            marker_color="#00C853",
            opacity=0.7,
            nbinsx=30,
        )
    )

    # Losses histogram
    fig.add_trace(
        go.Histogram(
            x=losses,
            name=f"Losses ({len(losses)})",
            marker_color="#FF1744",
            opacity=0.7,
            nbinsx=30,
        )
    )

    # Add mean lines
    fig.add_vline(
        x=pnl.mean(),
        line_dash="dash",
        line_color="blue",
        annotation_text=f"Mean: ${pnl.mean():.2f}",
    )

    fig.update_layout(
        title="PnL Distribution",
        xaxis_title="PnL ($)",
        yaxis_title="Count",
        template="plotly_white",
        barmode="overlay",
    )

    return fig


def plot_monthly_returns_heatmap(equity_curve: pd.Series):
    """Create a monthly returns heatmap."""
    try:
        import plotly.graph_objects as go
    except ImportError as exc:
        raise ImportError("plotly is required for visualization") from exc

    if equity_curve.empty:
        raise ValueError("equity_curve is empty")

    # Calculate daily returns
    returns = equity_curve.pct_change().dropna()

    # Resample to monthly
    monthly_returns = returns.resample("ME").apply(lambda x: (1 + x).prod() - 1) * 100

    # Create pivot table (Year x Month)
    df = pd.DataFrame({"returns": monthly_returns})
    df["year"] = df.index.year
    df["month"] = df.index.month

    pivot = df.pivot_table(values="returns", index="year", columns="month", aggfunc="sum")
    pivot.columns = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

    fig = go.Figure(
        data=go.Heatmap(
            z=pivot.values,
            x=pivot.columns,
            y=pivot.index,
            colorscale=[
                [0, "#FF1744"],
                [0.5, "#FFFFFF"],
                [1, "#00C853"],
            ],
            zmid=0,
            text=np.round(pivot.values, 1),
            texttemplate="%{text}%",
            textfont={"size": 10},
            hovertemplate="Year: %{y}<br>Month: %{x}<br>Return: %{z:.2f}%<extra></extra>",
        )
    )

    fig.update_layout(
        title="Monthly Returns Heatmap (%)",
        xaxis_title="Month",
        yaxis_title="Year",
        template="plotly_white",
    )

    return fig


def plot_trade_analysis(trades: pd.DataFrame):
    """Create trade analysis charts (win rate by hour, day, duration)."""
    try:
        import plotly.graph_objects as go
        from plotly.subplots import make_subplots
    except ImportError as exc:
        raise ImportError("plotly is required for visualization") from exc

    if trades.empty:
        raise ValueError("trades is empty")

    fig = make_subplots(
        rows=2,
        cols=2,
        subplot_titles=(
            "Win Rate by Hour",
            "Win Rate by Day of Week",
            "Trade Duration Distribution",
            "Cumulative PnL",
        ),
    )

    # Ensure datetime columns
    if "entry_time" in trades.columns:
        trades = trades.copy()
        trades["entry_time"] = pd.to_datetime(trades["entry_time"])
        trades["hour"] = trades["entry_time"].dt.hour
        trades["day_of_week"] = trades["entry_time"].dt.day_name()

        # Win rate by hour
        if "pnl" in trades.columns:
            hourly_stats = trades.groupby("hour").agg(
                win_rate=("pnl", lambda x: (x > 0).mean() * 100),
                count=("pnl", "count"),
            )

            fig.add_trace(
                go.Bar(
                    x=hourly_stats.index,
                    y=hourly_stats["win_rate"],
                    name="Win Rate by Hour",
                    marker_color="#2E86AB",
                    hovertemplate="Hour: %{x}<br>Win Rate: %{y:.1f}%<br>Trades: %{customdata}<extra></extra>",
                    customdata=hourly_stats["count"],
                ),
                row=1,
                col=1,
            )

            # Win rate by day of week
            day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
            daily_stats = trades.groupby("day_of_week").agg(
                win_rate=("pnl", lambda x: (x > 0).mean() * 100),
                count=("pnl", "count"),
            ).reindex(day_order)

            fig.add_trace(
                go.Bar(
                    x=daily_stats.index,
                    y=daily_stats["win_rate"],
                    name="Win Rate by Day",
                    marker_color="#A23B72",
                    hovertemplate="Day: %{x}<br>Win Rate: %{y:.1f}%<br>Trades: %{customdata}<extra></extra>",
                    customdata=daily_stats["count"],
                ),
                row=1,
                col=2,
            )

    # Trade duration
    if "entry_time" in trades.columns and "exit_time" in trades.columns:
        trades_with_exit = trades.dropna(subset=["exit_time"])
        if not trades_with_exit.empty:
            trades_with_exit = trades_with_exit.copy()
            trades_with_exit["exit_time"] = pd.to_datetime(trades_with_exit["exit_time"])
            duration = (trades_with_exit["exit_time"] - trades_with_exit["entry_time"]).dt.total_seconds() / 3600

            fig.add_trace(
                go.Histogram(
                    x=duration,
                    name="Trade Duration",
                    marker_color="#F18F01",
                    nbinsx=30,
                    hovertemplate="Duration: %{x:.1f}h<br>Count: %{y}<extra></extra>",
                ),
                row=2,
                col=1,
            )

    # Cumulative PnL
    if "pnl" in trades.columns and "exit_time" in trades.columns:
        trades_sorted = trades.dropna(subset=["exit_time", "pnl"]).sort_values("exit_time")
        if not trades_sorted.empty:
            cumulative_pnl = trades_sorted["pnl"].cumsum()

            fig.add_trace(
                go.Scatter(
                    x=list(range(1, len(cumulative_pnl) + 1)),
                    y=cumulative_pnl.values,
                    mode="lines",
                    name="Cumulative PnL",
                    line=dict(color="#2E86AB", width=2),
                    hovertemplate="Trade #%{x}<br>Cumulative PnL: $%{y:.2f}<extra></extra>",
                ),
                row=2,
                col=2,
            )

    fig.update_layout(
        title="Trade Analysis",
        template="plotly_white",
        showlegend=False,
        height=600,
    )

    # Add 50% reference line for win rate charts
    fig.add_hline(y=50, line_dash="dash", line_color="gray", row=1, col=1)
    fig.add_hline(y=50, line_dash="dash", line_color="gray", row=1, col=2)

    return fig


def plot_rolling_metrics(equity_curve: pd.Series, window: int = 30):
    """Plot rolling Sharpe ratio and volatility."""
    try:
        import plotly.graph_objects as go
        from plotly.subplots import make_subplots
    except ImportError as exc:
        raise ImportError("plotly is required for visualization") from exc

    if equity_curve.empty:
        raise ValueError("equity_curve is empty")

    returns = equity_curve.pct_change().dropna()

    # Calculate rolling metrics
    rolling_mean = returns.rolling(window).mean() * 252  # Annualized
    rolling_std = returns.rolling(window).std() * np.sqrt(252)  # Annualized
    rolling_sharpe = rolling_mean / rolling_std

    fig = make_subplots(
        rows=2,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.1,
        subplot_titles=(f"Rolling Sharpe Ratio ({window}d)", f"Rolling Volatility ({window}d)"),
    )

    # Rolling Sharpe
    fig.add_trace(
        go.Scatter(
            x=rolling_sharpe.index,
            y=rolling_sharpe.values,
            mode="lines",
            name="Rolling Sharpe",
            line=dict(color="#2E86AB", width=2),
        ),
        row=1,
        col=1,
    )
    fig.add_hline(y=0, line_dash="dash", line_color="gray", row=1, col=1)
    fig.add_hline(y=1, line_dash="dot", line_color="green", row=1, col=1)

    # Rolling Volatility
    fig.add_trace(
        go.Scatter(
            x=rolling_std.index,
            y=rolling_std.values * 100,
            mode="lines",
            name="Rolling Volatility",
            line=dict(color="#E74C3C", width=2),
            fill="tozeroy",
            fillcolor="rgba(231, 76, 60, 0.2)",
        ),
        row=2,
        col=1,
    )

    fig.update_layout(
        title="Rolling Performance Metrics",
        template="plotly_white",
        hovermode="x unified",
        showlegend=False,
        height=500,
    )

    fig.update_yaxes(title_text="Sharpe Ratio", row=1, col=1)
    fig.update_yaxes(title_text="Volatility (%)", row=2, col=1)

    return fig


def plot_backtest_report(
    equity_curve: pd.Series,
    trades: pd.DataFrame,
    data: Optional[pd.DataFrame] = None,
    initial_capital: float = 10000.0,
):
    """Create a comprehensive backtest report dashboard."""
    try:
        import plotly.graph_objects as go
        from plotly.subplots import make_subplots
    except ImportError as exc:
        raise ImportError("plotly is required for visualization") from exc

    if equity_curve.empty:
        raise ValueError("equity_curve is empty")

    # Calculate key metrics for header
    total_return = (equity_curve.iloc[-1] / initial_capital - 1) * 100
    peak = equity_curve.cummax()
    max_drawdown = ((equity_curve - peak) / peak).min() * 100

    returns = equity_curve.pct_change().dropna()
    sharpe = (returns.mean() * 252) / (returns.std() * np.sqrt(252)) if returns.std() > 0 else 0

    if not trades.empty and "pnl" in trades.columns:
        win_rate = (trades["pnl"] > 0).mean() * 100
        total_trades = len(trades)
        avg_pnl = trades["pnl"].mean()
    else:
        win_rate = 0
        total_trades = 0
        avg_pnl = 0

    # Create subplot layout
    fig = make_subplots(
        rows=3,
        cols=2,
        subplot_titles=(
            "Equity Curve",
            "Drawdown",
            "Price Chart with Signals" if data is not None else "PnL Distribution",
            "PnL Distribution" if data is not None else "Monthly Returns",
            "Monthly Returns Heatmap",
            "Trade Analysis",
        ),
        specs=[
            [{"type": "scatter"}, {"type": "scatter"}],
            [{"type": "scatter" if data is not None else "histogram"}, {"type": "histogram"}],
            [{"type": "heatmap"}, {"type": "bar"}],
        ],
        vertical_spacing=0.08,
        horizontal_spacing=0.08,
        row_heights=[0.35, 0.35, 0.30],
    )

    # 1. Equity Curve
    fig.add_trace(
        go.Scatter(
            x=equity_curve.index,
            y=equity_curve.values,
            mode="lines",
            name="Equity",
            line=dict(color="#2E86AB", width=2),
            hovertemplate="Time: %{x}<br>Equity: $%{y:,.2f}<extra></extra>",
        ),
        row=1,
        col=1,
    )

    # 2. Drawdown
    drawdown = (equity_curve - peak) / peak * 100
    fig.add_trace(
        go.Scatter(
            x=drawdown.index,
            y=drawdown.values,
            mode="lines",
            name="Drawdown",
            fill="tozeroy",
            line=dict(color="#E74C3C", width=1),
            fillcolor="rgba(231, 76, 60, 0.3)",
            hovertemplate="Time: %{x}<br>Drawdown: %{y:.2f}%<extra></extra>",
        ),
        row=1,
        col=2,
    )

    # 3. Price or PnL Distribution
    if data is not None and not data.empty:
        # Simplified price line instead of candlestick for subplot
        fig.add_trace(
            go.Scatter(
                x=data.index,
                y=data["close"],
                mode="lines",
                name="Price",
                line=dict(color="#26A69A", width=1),
            ),
            row=2,
            col=1,
        )

        # Add trade markers
        if not trades.empty and "entry_time" in trades.columns:
            fig.add_trace(
                go.Scatter(
                    x=trades["entry_time"],
                    y=trades["entry_price"],
                    mode="markers",
                    marker=dict(symbol="triangle-up", size=8, color="#00C853"),
                    name="Entry",
                ),
                row=2,
                col=1,
            )

    # 4. PnL Distribution
    if not trades.empty and "pnl" in trades.columns:
        pnl = trades["pnl"].dropna()
        wins = pnl[pnl > 0]
        losses = pnl[pnl <= 0]

        fig.add_trace(
            go.Histogram(
                x=wins,
                name="Wins",
                marker_color="#00C853",
                opacity=0.7,
            ),
            row=2,
            col=2,
        )
        fig.add_trace(
            go.Histogram(
                x=losses,
                name="Losses",
                marker_color="#FF1744",
                opacity=0.7,
            ),
            row=2,
            col=2,
        )

    # 5. Monthly Returns Heatmap
    monthly_returns = returns.resample("ME").apply(lambda x: (1 + x).prod() - 1) * 100
    if not monthly_returns.empty:
        df = pd.DataFrame({"returns": monthly_returns})
        df["year"] = df.index.year
        df["month"] = df.index.month

        pivot = df.pivot_table(values="returns", index="year", columns="month", aggfunc="sum")
        month_names = ["J", "F", "M", "A", "M", "J", "J", "A", "S", "O", "N", "D"]

        fig.add_trace(
            go.Heatmap(
                z=pivot.values,
                x=month_names[: len(pivot.columns)],
                y=pivot.index,
                colorscale=[[0, "#FF1744"], [0.5, "#FFFFFF"], [1, "#00C853"]],
                zmid=0,
                showscale=False,
                hovertemplate="Year: %{y}<br>Month: %{x}<br>Return: %{z:.1f}%<extra></extra>",
            ),
            row=3,
            col=1,
        )

    # 6. Trade Stats Bar Chart
    if not trades.empty and "pnl" in trades.columns:
        stats_names = ["Win Rate", "Avg Win", "Avg Loss", "Profit Factor"]
        wins = trades[trades["pnl"] > 0]["pnl"]
        losses = trades[trades["pnl"] <= 0]["pnl"]

        avg_win = wins.mean() if len(wins) > 0 else 0
        avg_loss = abs(losses.mean()) if len(losses) > 0 else 0
        profit_factor = abs(wins.sum() / losses.sum()) if losses.sum() != 0 else 0

        # Normalize for display
        stats_values = [win_rate, avg_win, avg_loss, profit_factor * 10]
        colors = ["#2E86AB", "#00C853", "#FF1744", "#F18F01"]

        fig.add_trace(
            go.Bar(
                x=stats_names,
                y=stats_values,
                marker_color=colors,
                text=[f"{win_rate:.1f}%", f"${avg_win:.2f}", f"${avg_loss:.2f}", f"{profit_factor:.2f}"],
                textposition="auto",
            ),
            row=3,
            col=2,
        )

    # Update layout
    fig.update_layout(
        title=dict(
            text=(
                f"<b>Backtest Report</b><br>"
                f"<span style='font-size:12px'>"
                f"Return: {total_return:+.2f}% | "
                f"Sharpe: {sharpe:.2f} | "
                f"Max DD: {max_drawdown:.2f}% | "
                f"Win Rate: {win_rate:.1f}% | "
                f"Trades: {total_trades}"
                f"</span>"
            ),
            x=0.5,
            xanchor="center",
        ),
        template="plotly_white",
        height=900,
        showlegend=False,
        hovermode="closest",
    )

    return fig


def generate_html_report(
    equity_curve: pd.Series,
    trades: pd.DataFrame,
    data: Optional[pd.DataFrame] = None,
    initial_capital: float = 10000.0,
    output_path: str = "backtest_report.html",
) -> str:
    """Generate a complete HTML report with all charts."""
    try:
        import plotly.io as pio
    except ImportError as exc:
        raise ImportError("plotly is required for visualization") from exc

    # Generate all figures
    figs = []

    # Main dashboard
    figs.append(("Overview", plot_backtest_report(equity_curve, trades, data, initial_capital)))

    # Detailed charts
    figs.append(("Equity Curve", plot_equity_curve(equity_curve)))
    figs.append(("Drawdown", plot_drawdown(equity_curve)))

    if data is not None and not data.empty:
        figs.append(("Price Chart", plot_price_with_signals(data, trades)))

    if not trades.empty and "pnl" in trades.columns:
        figs.append(("PnL Distribution", plot_pnl_distribution(trades)))
        figs.append(("Trade Analysis", plot_trade_analysis(trades)))

    figs.append(("Monthly Returns", plot_monthly_returns_heatmap(equity_curve)))
    figs.append(("Rolling Metrics", plot_rolling_metrics(equity_curve)))

    # Build HTML
    html_parts = [
        """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Backtest Report</title>
            <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
                .container { max-width: 1400px; margin: 0 auto; }
                .chart-section { background: white; margin: 20px 0; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
                h1 { color: #2E86AB; text-align: center; }
                h2 { color: #333; border-bottom: 2px solid #2E86AB; padding-bottom: 10px; }
                .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 20px 0; }
                .stat-card { background: linear-gradient(135deg, #2E86AB, #1a5276); color: white; padding: 20px; border-radius: 8px; text-align: center; }
                .stat-value { font-size: 28px; font-weight: bold; }
                .stat-label { font-size: 14px; opacity: 0.9; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>📊 Backtest Report</h1>
        """
    ]

    # Add summary stats
    total_return = (equity_curve.iloc[-1] / initial_capital - 1) * 100
    peak = equity_curve.cummax()
    max_dd = ((equity_curve - peak) / peak).min() * 100
    returns = equity_curve.pct_change().dropna()
    sharpe = (returns.mean() * 252) / (returns.std() * np.sqrt(252)) if returns.std() > 0 else 0

    if not trades.empty and "pnl" in trades.columns:
        win_rate = (trades["pnl"] > 0).mean() * 100
        total_trades = len(trades)
    else:
        win_rate = 0
        total_trades = 0

    html_parts.append(f"""
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-value">${equity_curve.iloc[-1]:,.2f}</div>
                <div class="stat-label">Final Equity</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{total_return:+.2f}%</div>
                <div class="stat-label">Total Return</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{sharpe:.2f}</div>
                <div class="stat-label">Sharpe Ratio</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{max_dd:.2f}%</div>
                <div class="stat-label">Max Drawdown</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{win_rate:.1f}%</div>
                <div class="stat-label">Win Rate</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{total_trades}</div>
                <div class="stat-label">Total Trades</div>
            </div>
        </div>
    """)

    # Add each chart
    for title, fig in figs:
        chart_html = pio.to_html(fig, full_html=False, include_plotlyjs=False)
        html_parts.append(f"""
            <div class="chart-section">
                <h2>{title}</h2>
                {chart_html}
            </div>
        """)

    html_parts.append("""
            </div>
        </body>
        </html>
    """)

    html_content = "".join(html_parts)

    # Write to file
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    return output_path
