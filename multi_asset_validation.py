"""Validate optimized strategy across multiple assets (BTC/ETH/SOL)."""

from __future__ import annotations

from dataclasses import dataclass
from math import sqrt
from pathlib import Path

import pandas as pd

from crypto_backtest.analysis.metrics import compute_metrics
from crypto_backtest.data.fetcher import DataFetcher, FetchRequest
from crypto_backtest.data.storage import ParquetStore
from crypto_backtest.engine.backtest import BacktestConfig, VectorizedBacktester
from crypto_backtest.indicators.five_in_one import FiveInOneConfig
from crypto_backtest.indicators.ichimoku import IchimokuConfig
from crypto_backtest.strategies.final_trigger import FinalTriggerParams, FinalTriggerStrategy


ASSETS = {
    "BTC": {"symbol": "BTC/USDT", "csv": "data/Binance_BTCUSDT_1h.csv"},
    "ETH": {"symbol": "ETH/USDT", "csv": "data/Binance_ETHUSDT_1h.csv"},
    "SOL": {"symbol": "SOL/USDT", "csv": "data/Binance_SOLUSDT_1h.csv"},
}


@dataclass
class AssetResult:
    asset: str
    total_return_pct: float
    sharpe: float
    sortino: float
    max_drawdown_pct: float
    profit_factor: float
    trades: int
    win_rate_pct: float
    expectancy: float
    equity_curve: pd.Series


def _load_csv(path: str, warmup: int = 200) -> pd.DataFrame:
    df = pd.read_csv(path)
    df.columns = [col.strip() for col in df.columns]
    data = df[["open", "high", "low", "close"]].copy()

    if "volume" in df.columns:
        data["volume"] = df["volume"].fillna(0.0)
    else:
        data["volume"] = 0.0

    if "timestamp" in df.columns:
        data.index = pd.to_datetime(df["timestamp"], utc=True)

    return data.iloc[warmup:]


def _btc_date_range(path: str) -> tuple[pd.Timestamp, pd.Timestamp]:
    df = pd.read_csv(path)
    timestamps = pd.to_datetime(df["timestamp"], utc=True)
    return timestamps.iloc[0], timestamps.iloc[-1]


def _fetch_binance_csv(symbol: str, start: pd.Timestamp, end: pd.Timestamp, output_path: str) -> None:
    store = ParquetStore("data/cache")
    fetcher = DataFetcher("binance", store=store)
    since_ms = int(start.value / 1_000_000)
    request = FetchRequest(symbol=symbol, timeframe="1h", since=since_ms, limit=1000)
    df = fetcher.fetch_ohlcv(request)
    df = df[df["timestamp"] <= end].copy()
    df.to_csv(output_path, index=False)


def _build_params() -> FinalTriggerParams:
    five_in_one = FiveInOneConfig(
        fast_period=7,
        slow_period=19,
        er_period=8,
        norm_period=50,
        use_norm=True,
        ad_norm_period=50,
        use_ad_line=True,
        ichi5in1_strict=False,
        use_transition_mode=False,
        use_distance_filter=False,
        use_volume_filter=False,
        use_regression_cloud=False,
        use_kama_oscillator=False,
        use_ichimoku_filter=True,
        tenkan_5=12,
        kijun_5=21,
        displacement_5=52,
    )

    ichimoku = IchimokuConfig(
        tenkan=13,
        kijun=34,
        displacement=52,
    )

    return FinalTriggerParams(
        grace_bars=1,
        use_mama_kama_filter=False,
        require_fama_between=False,
        strict_lock_5in1_last=False,
        mama_fast_limit=0.5,
        mama_slow_limit=0.05,
        kama_length=20,
        atr_length=14,
        sl_mult=3.75,
        tp1_mult=3.75,
        tp2_mult=9.0,
        tp3_mult=7.0,
        ichimoku=ichimoku,
        five_in_one=five_in_one,
    )


def _pnl_series(trades: pd.DataFrame) -> pd.Series:
    if trades is None or trades.empty:
        return pd.Series(dtype=float)
    for col in ("net_pnl", "pnl", "gross_pnl"):
        if col in trades.columns:
            return trades[col].astype(float)
    return pd.Series(dtype=float)


def _periods_per_year(index: pd.Index) -> float:
    if not isinstance(index, pd.DatetimeIndex) or len(index) < 2:
        return 252.0
    freq = pd.infer_freq(index)
    if freq:
        offset = pd.tseries.frequencies.to_offset(freq)
        try:
            delta = offset.as_timedelta()
        except AttributeError:
            delta = pd.Timedelta(offset.nanos, unit="ns")
        return pd.Timedelta(days=365.25) / delta
    delta = (index[1:] - index[:-1]).median()
    if delta <= pd.Timedelta(0):
        return 252.0
    return pd.Timedelta(days=365.25) / delta


def _portfolio_metrics(returns: pd.Series) -> tuple[float, float, float]:
    if returns.empty:
        return 0.0, 0.0, 0.0
    equity = (1.0 + returns).cumprod()
    total_return = (equity.iloc[-1] / equity.iloc[0]) - 1.0
    std = returns.std(ddof=0)
    sharpe = 0.0 if std == 0 else (returns.mean() / std) * sqrt(_periods_per_year(returns.index))
    max_dd = (equity / equity.cummax() - 1.0).min()
    return total_return * 100.0, sharpe, max_dd * 100.0


def _run_backtest(asset: str, data: pd.DataFrame, params: FinalTriggerParams) -> AssetResult:
    config = BacktestConfig(
        initial_capital=10000.0,
        fees_bps=5.0,
        slippage_bps=2.0,
        sizing_mode="fixed",
        intrabar_order="stop_first",
    )
    backtester = VectorizedBacktester(config)
    result = backtester.run(data, FinalTriggerStrategy(params))

    metrics = compute_metrics(result.equity_curve, result.trades)
    pnl = _pnl_series(result.trades)

    return AssetResult(
        asset=asset,
        total_return_pct=float(metrics.get("total_return", 0.0) * 100.0),
        sharpe=float(metrics.get("sharpe_ratio", 0.0)),
        sortino=float(metrics.get("sortino_ratio", 0.0)),
        max_drawdown_pct=float(metrics.get("max_drawdown", 0.0) * 100.0),
        profit_factor=float(metrics.get("profit_factor", 0.0)),
        trades=int(len(result.trades)),
        win_rate_pct=float(metrics.get("win_rate", 0.0) * 100.0),
        expectancy=float(metrics.get("expectancy", 0.0)),
        equity_curve=result.equity_curve,
    )


def main() -> None:
    btc_start, btc_end = _btc_date_range(ASSETS["BTC"]["csv"])

    for asset, meta in ASSETS.items():
        if asset == "BTC":
            continue
        if not Path(meta["csv"]).exists():
            print(f"Fetching {asset} data from Binance...")
            _fetch_binance_csv(meta["symbol"], btc_start, btc_end, meta["csv"])

    params = _build_params()

    results: dict[str, AssetResult] = {}
    for asset, meta in ASSETS.items():
        data = _load_csv(meta["csv"], warmup=200)
        results[asset] = _run_backtest(asset, data, params)

    rows = []
    for asset in ("BTC", "ETH", "SOL"):
        res = results[asset]
        rows.append(
            {
                "asset": asset,
                "total_return_pct": res.total_return_pct,
                "sharpe": res.sharpe,
                "sortino": res.sortino,
                "max_drawdown_pct": res.max_drawdown_pct,
                "profit_factor": res.profit_factor,
                "trades": res.trades,
                "win_rate_pct": res.win_rate_pct,
                "expectancy": res.expectancy,
            }
        )

    output_csv = "outputs/multi_asset_validation.csv"
    Path("outputs").mkdir(exist_ok=True)
    pd.DataFrame(rows).to_csv(output_csv, index=False)

    eth_pass = results["ETH"].sharpe > 1.0
    sol_pass = results["SOL"].sharpe > 1.0
    sharpe_pass_count = sum(r.sharpe > 1.0 for r in results.values())

    asset_specific = results["ETH"].sharpe < 0.5 and results["SOL"].sharpe < 0.5
    transferable = eth_pass or sol_pass
    portfolio_ready = sharpe_pass_count >= 2

    report_path = "outputs/multi_asset_report.txt"
    with open(report_path, "w") as report:
        report.write("MULTI-ASSET VALIDATION REPORT\n")
        report.write("=" * 70 + "\n")
        report.write(f"Date range: {btc_start} to {btc_end}\n")
        report.write("Params: ATR 3.75/3.75/9.0/7.0, Ichi 13/34/52, 5in1 12/21/52\n\n")

        report.write("Per-asset metrics:\n")
        for asset in ("BTC", "ETH", "SOL"):
            res = results[asset]
            report.write(
                f"{asset}: return={res.total_return_pct:+.2f}%, sharpe={res.sharpe:.2f}, "
                f"sortino={res.sortino:.2f}, max_dd={res.max_drawdown_pct:.2f}%, "
                f"pf={res.profit_factor:.2f}, trades={res.trades}, "
                f"win_rate={res.win_rate_pct:.2f}%, expectancy={res.expectancy:.2f}\n"
            )

        report.write("\nComparison vs BTC baseline:\n")
        report.write("| Asset | Return | Sharpe | MaxDD | Trades | Status |\n")
        report.write("|-------|--------|--------|-------|--------|--------|\n")
        btc = results["BTC"]
        for asset in ("ETH", "SOL"):
            res = results[asset]
            status = "PASS" if res.sharpe > 1.0 else "FAIL"
            report.write(
                f"| {asset} | {res.total_return_pct:+.2f}% | {res.sharpe:.2f} | "
                f"{res.max_drawdown_pct:.2f}% | {res.trades} | {status} |\n"
            )
        report.write(
            f"\nBTC baseline: return={btc.total_return_pct:+.2f}%, "
            f"sharpe={btc.sharpe:.2f}, max_dd={btc.max_drawdown_pct:.2f}%\n"
        )

        if eth_pass and sol_pass:
            returns = pd.concat(
                [
                    results["BTC"].equity_curve.pct_change().dropna().rename("BTC"),
                    results["ETH"].equity_curve.pct_change().dropna().rename("ETH"),
                    results["SOL"].equity_curve.pct_change().dropna().rename("SOL"),
                ],
                axis=1,
                join="inner",
            )
            portfolio_returns = returns.mean(axis=1)
            port_return, port_sharpe, port_max_dd = _portfolio_metrics(portfolio_returns)
            report.write("\nEqual-weight portfolio (BTC/ETH/SOL):\n")
            report.write(
                f"return={port_return:+.2f}%, sharpe={port_sharpe:.2f}, "
                f"max_dd={port_max_dd:.2f}%\n"
            )

        report.write("\nFlags:\n")
        report.write(f"ASSET_SPECIFIC: {'YES' if asset_specific else 'NO'}\n")
        report.write(f"TRANSFERABLE: {'YES' if transferable else 'NO'}\n")
        report.write(f"PORTFOLIO_READY: {'YES' if portfolio_ready else 'NO'}\n")

    print(f"Saved CSV: {output_csv}")
    print(f"Saved report: {report_path}")


if __name__ == "__main__":
    main()
