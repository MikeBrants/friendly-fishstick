"""Optimize FINAL TRIGGER v2 parameters per asset and validate robustness."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from math import sqrt
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from crypto_backtest.analysis.metrics import compute_metrics
from crypto_backtest.data.fetcher import DataFetcher, FetchRequest
from crypto_backtest.data.storage import ParquetStore
from crypto_backtest.engine.backtest import BacktestConfig, VectorizedBacktester
from crypto_backtest.optimization.bayesian import _apply_overrides, _instantiate_strategy, _suggest_params
from crypto_backtest.strategies.final_trigger import FinalTriggerStrategy


BTC_CSV = "data/Binance_BTCUSDT_1h.csv"
WARMUP_BARS = 200

ASSETS = {
    "ETH": {"symbol": "ETH/USDT", "csv": "data/Binance_ETHUSDT_1h.csv"},
    "SOL": {"symbol": "SOL/USDT", "csv": "data/Binance_SOLUSDT_1h.csv"},
    "XRP": {"symbol": "XRP/USDT", "csv": "data/Binance_XRPUSDT_1h.csv"},
    "AAVE": {"symbol": "AAVE/USDT", "csv": "data/Binance_AAVEUSDT_1h.csv"},
}

BASE_CONFIG = BacktestConfig(
    initial_capital=10000.0,
    fees_bps=5.0,
    slippage_bps=2.0,
    sizing_mode="fixed",
    intrabar_order="stop_first",
)


@dataclass
class AssetOptimizationResult:
    asset: str
    total_return_pct: float
    sharpe: float
    max_drawdown_pct: float
    trades: int
    wfe: float
    mc_p: float
    status: str
    equity_curve: pd.Series
    daily_returns: pd.Series


def _load_csv(path: str, start: pd.Timestamp | None, end: pd.Timestamp | None) -> pd.DataFrame:
    df = pd.read_csv(path)
    df.columns = [col.strip() for col in df.columns]
    data = df[["open", "high", "low", "close"]].copy()

    if "volume" in df.columns:
        data["volume"] = df["volume"].fillna(0.0)
    else:
        data["volume"] = 0.0

    if "timestamp" in df.columns:
        data.index = pd.to_datetime(df["timestamp"], utc=True)

    if start is not None:
        data = data[data.index >= start]
    if end is not None:
        data = data[data.index <= end]

    return data.iloc[WARMUP_BARS:]


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
    df = df[(df["timestamp"] >= start) & (df["timestamp"] <= end)].copy()
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)


def _build_base_params(
    sl_mult: float,
    tp1_mult: float,
    tp2_mult: float,
    tp3_mult: float,
    tenkan: int,
    kijun: int,
    tenkan_5: int,
    kijun_5: int,
) -> dict[str, Any]:
    return {
        "grace_bars": 1,
        "use_mama_kama_filter": False,
        "require_fama_between": False,
        "strict_lock_5in1_last": False,
        "mama_fast_limit": 0.5,
        "mama_slow_limit": 0.05,
        "kama_length": 20,
        "atr_length": 14,
        "sl_mult": sl_mult,
        "tp1_mult": tp1_mult,
        "tp2_mult": tp2_mult,
        "tp3_mult": tp3_mult,
        "ichimoku": {
            "tenkan": tenkan,
            "kijun": kijun,
            "displacement": 52,
        },
        "five_in_one": {
            "fast_period": 7,
            "slow_period": 19,
            "er_period": 8,
            "norm_period": 50,
            "use_norm": True,
            "ad_norm_period": 50,
            "use_ad_line": True,
            "ichi5in1_strict": False,
            "use_transition_mode": False,
            "use_distance_filter": False,
            "use_volume_filter": False,
            "use_regression_cloud": False,
            "use_kama_oscillator": False,
            "use_ichimoku_filter": True,
            "tenkan_5": tenkan_5,
            "kijun_5": kijun_5,
            "displacement_5": 52,
        },
    }


def _metrics_summary(metrics: dict[str, float], trades: pd.DataFrame) -> dict[str, float]:
    total_return_pct = float(metrics.get("total_return", 0.0) * 100.0)
    max_drawdown_pct = float(metrics.get("max_drawdown", 0.0) * 100.0)
    return {
        "total_return_pct": total_return_pct,
        "sharpe": float(metrics.get("sharpe_ratio", 0.0)),
        "sortino": float(metrics.get("sortino_ratio", 0.0)),
        "max_drawdown_pct": max_drawdown_pct,
        "profit_factor": float(metrics.get("profit_factor", 0.0)),
        "trades": int(len(trades)),
        "win_rate_pct": float(metrics.get("win_rate", 0.0) * 100.0),
        "expectancy": float(metrics.get("expectancy", 0.0)),
    }


def _run_backtest(
    data: pd.DataFrame,
    params: dict[str, Any],
    config: BacktestConfig,
) -> tuple[pd.Series, pd.DataFrame, dict[str, float]]:
    strategy = _instantiate_strategy(FinalTriggerStrategy, params)
    backtester = VectorizedBacktester(config)
    result = backtester.run(data, strategy)
    metrics = compute_metrics(result.equity_curve, result.trades)
    return result.equity_curve, result.trades, metrics


def _optimize(
    data: pd.DataFrame,
    base_params: dict[str, Any],
    search_space: dict[str, Any],
    config: BacktestConfig,
    n_trials: int,
    min_trades: int,
    objective: str,
) -> tuple[dict[str, Any], float, pd.DataFrame]:
    import optuna

    trial_rows: list[dict[str, Any]] = []

    def objective_fn(trial: optuna.Trial) -> float:
        overrides = _suggest_params(trial, search_space)
        params = _apply_overrides(base_params, overrides)
        equity, trades, metrics = _run_backtest(data, params, config)

        score = float(metrics.get(objective, float("-inf")))
        trades_count = int(len(trades))
        valid = trades_count >= min_trades and not np.isnan(score)
        if not valid:
            score = float("-inf")

        row = {
            "trial": trial.number,
            "score": score,
            "trades": trades_count,
            "total_return_pct": float(metrics.get("total_return", 0.0) * 100.0),
            "sharpe": float(metrics.get("sharpe_ratio", 0.0)),
            "max_drawdown_pct": float(metrics.get("max_drawdown", 0.0) * 100.0),
            "profit_factor": float(metrics.get("profit_factor", 0.0)),
            "valid": valid,
        }
        row.update(overrides)
        trial_rows.append(row)
        return score

    sampler = optuna.samplers.TPESampler(seed=42)
    study = optuna.create_study(direction="maximize", sampler=sampler)
    study.optimize(objective_fn, n_trials=n_trials)

    trials_df = pd.DataFrame(trial_rows)
    return study.best_params, float(study.best_value), trials_df


def _walk_forward_split(
    data: pd.DataFrame,
    params: dict[str, Any],
    config: BacktestConfig,
) -> tuple[pd.DataFrame, float]:
    n = len(data)
    if n < 10:
        return pd.DataFrame(), 0.0

    is_end = int(n * 0.6)
    val_end = int(n * 0.8)

    segments = {
        "IS": data.iloc[:is_end],
        "VAL": data.iloc[is_end:val_end],
        "OOS": data.iloc[val_end:],
    }

    rows = []
    is_sharpe = 0.0
    oos_sharpe = 0.0

    for name, segment in segments.items():
        equity, trades, metrics = _run_backtest(segment, params, config)
        summary = _metrics_summary(metrics, trades)
        row = {
            "segment": name,
            "bars": int(len(segment)),
            "start": segment.index[0] if not segment.empty else None,
            "end": segment.index[-1] if not segment.empty else None,
        }
        row.update(summary)
        rows.append(row)

        if name == "IS":
            is_sharpe = summary["sharpe"]
        if name == "OOS":
            oos_sharpe = summary["sharpe"]

    wfe = (oos_sharpe / is_sharpe) if is_sharpe else 0.0
    df = pd.DataFrame(rows)
    return df, wfe


def _pnl_series(trades: pd.DataFrame) -> np.ndarray:
    if trades is None or trades.empty:
        return np.array([], dtype=float)
    for col in ("net_pnl", "pnl", "gross_pnl"):
        if col in trades.columns:
            return trades[col].astype(float).to_numpy()
    return np.array([], dtype=float)


def _map_trade_indices(data: pd.DataFrame, trades: pd.DataFrame) -> pd.DataFrame:
    entries = pd.to_datetime(trades["entry_time"], utc=True)
    exits = pd.to_datetime(trades["exit_time"], utc=True)
    entry_idx = data.index.get_indexer(entries, method="nearest")
    exit_idx = data.index.get_indexer(exits, method="nearest")

    mapped = trades.copy()
    mapped["entry_idx"] = entry_idx
    mapped["exit_idx"] = exit_idx
    mapped["duration"] = mapped["exit_idx"] - mapped["entry_idx"]
    return mapped[mapped["duration"] > 0].reset_index(drop=True)


def _extract_signs(trades: pd.DataFrame) -> np.ndarray:
    direction = trades["direction"]
    if np.issubdtype(direction.dtype, np.number):
        return np.where(direction.astype(float) < 0, -1.0, 1.0)
    values = direction.astype(str).str.lower()
    return np.where(values.str.contains("short") | (values == "-1"), -1.0, 1.0)


def _extract_quantities(trades: pd.DataFrame) -> np.ndarray:
    if "quantity" in trades.columns:
        return trades["quantity"].astype(float).to_numpy()
    if "size" in trades.columns:
        return trades["size"].astype(float).to_numpy()
    return np.ones(len(trades), dtype=float)


def _build_random_equity_curve(
    prices: np.ndarray,
    durations: np.ndarray,
    signs: np.ndarray,
    quantities: np.ndarray,
    cost_rate: float,
    initial_capital: float,
    rng: np.random.Generator,
) -> np.ndarray:
    n_bars = len(prices)
    max_entry = n_bars - durations
    entry_idx = (rng.random(len(durations)) * max_entry).astype(int)
    exit_idx = entry_idx + durations

    entry_price = prices[entry_idx]
    exit_price = prices[exit_idx]

    pnl = signs * (exit_price - entry_price) * quantities
    costs = cost_rate * (np.abs(entry_price) + np.abs(exit_price)) * quantities
    pnl_net = pnl - costs

    pnl_by_exit = np.zeros(n_bars, dtype=float)
    np.add.at(pnl_by_exit, exit_idx, pnl_net)
    equity = initial_capital + np.cumsum(pnl_by_exit)
    return equity


def _monte_carlo_p_value(
    data: pd.DataFrame,
    trades: pd.DataFrame,
    actual_sharpe: float,
    config: BacktestConfig,
    iterations: int,
    seed: int = 42,
) -> float:
    if trades.empty:
        return 1.0

    mapped = _map_trade_indices(data, trades)
    if mapped.empty:
        return 1.0

    prices = data["close"].to_numpy()
    durations = mapped["duration"].astype(int).to_numpy()
    signs = _extract_signs(mapped)
    quantities = _extract_quantities(mapped)
    cost_rate = (config.fees_bps + config.slippage_bps) / 10000.0

    rng = np.random.default_rng(seed)
    sharpe_values = []

    for _ in range(iterations):
        equity = _build_random_equity_curve(
            prices=prices,
            durations=durations,
            signs=signs,
            quantities=quantities,
            cost_rate=cost_rate,
            initial_capital=config.initial_capital,
            rng=rng,
        )
        equity_series = pd.Series(equity, index=data.index)
        metrics = compute_metrics(equity_series, pd.DataFrame())
        sharpe_values.append(float(metrics.get("sharpe_ratio", 0.0)))

    sharpe_values = np.array(sharpe_values, dtype=float)
    return float((sharpe_values >= actual_sharpe).mean())


def _bootstrap_confidence(
    pnls: np.ndarray,
    initial_capital: float,
    iterations: int,
    seed: int = 42,
) -> pd.DataFrame:
    if len(pnls) == 0:
        return pd.DataFrame(
            [
                {
                    "metric": "sharpe",
                    "mean": 0.0,
                    "std": 0.0,
                    "ci_lower_95": 0.0,
                    "ci_upper_95": 0.0,
                }
            ]
        )

    n = len(pnls)
    rng = np.random.default_rng(seed)
    indices = rng.integers(0, n, size=(iterations, n))
    samples = pnls[indices]

    sample_sum = samples.sum(axis=1)
    total_return = sample_sum / initial_capital * 100

    returns = samples / initial_capital
    mean_returns = returns.mean(axis=1)
    std_returns = returns.std(axis=1, ddof=0)
    sharpe = np.where(std_returns == 0, 0.0, mean_returns / std_returns * np.sqrt(n))

    rows = []
    for name, values in {
        "sharpe": sharpe,
        "total_return": total_return,
    }.items():
        rows.append(
            {
                "metric": name,
                "mean": float(np.mean(values)),
                "std": float(np.std(values, ddof=0)),
                "ci_lower_95": float(np.percentile(values, 2.5)),
                "ci_upper_95": float(np.percentile(values, 97.5)),
            }
        )

    return pd.DataFrame(rows)


def _daily_returns(equity_curve: pd.Series) -> pd.Series:
    daily = equity_curve.resample("1D").last().ffill()
    return daily.pct_change().dropna()


def _portfolio_metrics(returns: pd.Series) -> tuple[float, float, float]:
    if returns.empty:
        return 0.0, 0.0, 0.0
    equity = (1.0 + returns).cumprod()
    total_return = (equity.iloc[-1] / equity.iloc[0]) - 1.0
    std = returns.std(ddof=0)
    sharpe = 0.0 if std == 0 else (returns.mean() / std) * sqrt(_periods_per_year(returns.index))
    max_dd = (equity / equity.cummax() - 1.0).min()
    return total_return * 100.0, sharpe, max_dd * 100.0


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


def _optimize_weights(
    returns: pd.DataFrame,
    min_weight: float,
    iterations: int = 20000,
    seed: int = 42,
) -> tuple[np.ndarray, float, float, float]:
    rng = np.random.default_rng(seed)
    assets = returns.columns
    best_sharpe = -np.inf
    best_weights = None
    best_return = 0.0
    best_max_dd = 0.0

    for _ in range(iterations):
        weights = rng.random(len(assets))
        weights = weights / weights.sum()
        weights = min_weight + (1 - min_weight * len(assets)) * weights
        weights = weights / weights.sum()

        portfolio_returns = (returns * weights).sum(axis=1)
        port_return, port_sharpe, port_max_dd = _portfolio_metrics(portfolio_returns)
        if port_sharpe > best_sharpe:
            best_sharpe = port_sharpe
            best_weights = weights
            best_return = port_return
            best_max_dd = port_max_dd

    return best_weights, best_return, best_sharpe, best_max_dd


def _optimize_asset(
    asset: str,
    data: pd.DataFrame,
    trials: int,
    mc_iterations: int,
    bootstrap_iterations: int,
) -> tuple[AssetOptimizationResult, dict[str, Any]]:
    print(f"\n=== {asset}: ATR optimization ({trials} trials) ===")
    atr_base = _build_base_params(
        sl_mult=3.0,
        tp1_mult=2.0,
        tp2_mult=6.0,
        tp3_mult=10.0,
        tenkan=9,
        kijun=26,
        tenkan_5=9,
        kijun_5=26,
    )
    atr_space = {
        "sl_mult": {"type": "float", "low": 1.5, "high": 5.0, "step": 0.25},
        "tp1_mult": {"type": "float", "low": 1.5, "high": 5.0, "step": 0.25},
        "tp2_mult": {"type": "float", "low": 3.0, "high": 12.0, "step": 0.5},
        "tp3_mult": {"type": "float", "low": 2.0, "high": 10.0, "step": 0.5},
    }

    atr_best, atr_score, atr_trials = _optimize(
        data=data,
        base_params=atr_base,
        search_space=atr_space,
        config=BASE_CONFIG,
        n_trials=trials,
        min_trades=100,
        objective="sharpe_ratio",
    )

    Path("outputs").mkdir(exist_ok=True)
    atr_trials_path = f"outputs/optim_{asset}_atr.csv"
    atr_trials.to_csv(atr_trials_path, index=False)

    atr_params = {
        "sl_mult": atr_best.get("sl_mult", atr_base["sl_mult"]),
        "tp1_mult": atr_best.get("tp1_mult", atr_base["tp1_mult"]),
        "tp2_mult": atr_best.get("tp2_mult", atr_base["tp2_mult"]),
        "tp3_mult": atr_best.get("tp3_mult", atr_base["tp3_mult"]),
    }

    print(f"Best ATR Sharpe: {atr_score:.4f}")
    print(
        "ATR params: "
        f"{atr_params['sl_mult']:.2f}/"
        f"{atr_params['tp1_mult']:.2f}/"
        f"{atr_params['tp2_mult']:.2f}/"
        f"{atr_params['tp3_mult']:.2f}"
    )

    print(f"\n=== {asset}: Ichimoku optimization ({trials} trials) ===")
    ichi_base = _build_base_params(
        sl_mult=atr_params["sl_mult"],
        tp1_mult=atr_params["tp1_mult"],
        tp2_mult=atr_params["tp2_mult"],
        tp3_mult=atr_params["tp3_mult"],
        tenkan=9,
        kijun=26,
        tenkan_5=9,
        kijun_5=26,
    )

    ichi_space = {
        "ichimoku.tenkan": {"type": "int", "low": 7, "high": 15},
        "ichimoku.kijun": {"type": "int", "low": 20, "high": 40},
        "five_in_one.tenkan_5": {"type": "int", "low": 8, "high": 16},
        "five_in_one.kijun_5": {"type": "int", "low": 15, "high": 30},
    }

    ichi_best, ichi_score, ichi_trials = _optimize(
        data=data,
        base_params=ichi_base,
        search_space=ichi_space,
        config=BASE_CONFIG,
        n_trials=trials,
        min_trades=100,
        objective="sharpe_ratio",
    )

    ichi_trials_path = f"outputs/optim_{asset}_ichi.csv"
    ichi_trials.to_csv(ichi_trials_path, index=False)

    best_params = _apply_overrides(ichi_base, ichi_best)

    print(f"Best Ichimoku Sharpe: {ichi_score:.4f}")
    print(
        "Ichimoku params: "
        f"{best_params['ichimoku']['tenkan']}/"
        f"{best_params['ichimoku']['kijun']}/"
        f"{best_params['five_in_one']['tenkan_5']}/"
        f"{best_params['five_in_one']['kijun_5']}"
    )

    equity, trades, metrics = _run_backtest(data, best_params, BASE_CONFIG)
    summary = _metrics_summary(metrics, trades)

    wf_df, wfe = _walk_forward_split(data, best_params, BASE_CONFIG)

    pnls = _pnl_series(trades)
    bootstrap_df = _bootstrap_confidence(
        pnls, BASE_CONFIG.initial_capital, bootstrap_iterations
    )
    sharpe_ci_lower = float(
        bootstrap_df.loc[bootstrap_df["metric"] == "sharpe", "ci_lower_95"].iloc[0]
    )

    mc_p = _monte_carlo_p_value(
        data=data,
        trades=trades,
        actual_sharpe=summary["sharpe"],
        config=BASE_CONFIG,
        iterations=mc_iterations,
    )

    validation_path = f"outputs/optim_{asset}_validation.csv"
    wf_df["wfe"] = None
    if not wf_df.empty:
        wf_df.loc[wf_df["segment"] == "OOS", "wfe"] = wfe
    wf_df.to_csv(validation_path, index=False)

    best_params_path = f"outputs/optim_{asset}_best_params.json"
    with open(best_params_path, "w") as f:
        json.dump(
            {
                "asset": asset,
                "atr_best": atr_params,
                "ichi_best": ichi_best,
                "full_params": best_params,
                "summary": summary,
                "wfe": wfe,
                "mc_p": mc_p,
                "bootstrap_sharpe_ci_lower": sharpe_ci_lower,
            },
            f,
            indent=2,
        )

    flags = []
    if mc_p > 0.05 or sharpe_ci_lower < 0.5:
        flags.append("WEAK")
    if wfe < 0.6:
        flags.append("OVERFIT")

    status = "PASS"
    if not (
        summary["sharpe"] > 1.0
        and wfe > 0.6
        and mc_p < 0.05
        and summary["trades"] >= 100
        and abs(summary["max_drawdown_pct"]) < 15.0
    ):
        status = "FAIL"

    if flags:
        status = f"{status} ({','.join(flags)})"

    daily_returns = _daily_returns(equity)

    result = AssetOptimizationResult(
        asset=asset,
        total_return_pct=summary["total_return_pct"],
        sharpe=summary["sharpe"],
        max_drawdown_pct=summary["max_drawdown_pct"],
        trades=summary["trades"],
        wfe=wfe,
        mc_p=mc_p,
        status=status,
        equity_curve=equity,
        daily_returns=daily_returns,
    )

    extra = {
        "bootstrap_sharpe_ci_lower": sharpe_ci_lower,
        "validation_path": validation_path,
        "atr_trials_path": atr_trials_path,
        "ichi_trials_path": ichi_trials_path,
    }

    return result, extra


def main() -> None:
    parser = argparse.ArgumentParser(description="Multi-asset optimization pipeline")
    parser.add_argument(
        "--assets",
        default=",".join(ASSETS.keys()),
        help="Comma-separated asset tickers (default: ETH,SOL,XRP,AAVE)",
    )
    parser.add_argument("--trials", type=int, default=100)
    parser.add_argument("--mc-iterations", type=int, default=500)
    parser.add_argument("--bootstrap-iterations", type=int, default=5000)
    parser.add_argument("--skip-fetch", action="store_true")
    parser.add_argument(
        "--jobs",
        type=int,
        default=1,
        help="Parallel jobs for asset optimization (use -1 for all cores).",
    )
    args = parser.parse_args()

    assets = [asset.strip().upper() for asset in args.assets.split(",") if asset.strip()]

    btc_start, btc_end = _btc_date_range(BTC_CSV)

    for asset in assets:
        if asset not in ASSETS:
            raise ValueError(f"Unsupported asset: {asset}")
        if args.skip_fetch:
            continue
        csv_path = ASSETS[asset]["csv"]
        if not Path(csv_path).exists():
            print(f"Fetching {asset} data from Binance...")
            _fetch_binance_csv(ASSETS[asset]["symbol"], btc_start, btc_end, csv_path)

    if args.jobs == 1:
        results: list[AssetOptimizationResult] = []
        for asset in assets:
            csv_path = ASSETS[asset]["csv"]
            data = _load_csv(csv_path, btc_start, btc_end)
            result, _extra = _optimize_asset(
                asset,
                data,
                trials=args.trials,
                mc_iterations=args.mc_iterations,
                bootstrap_iterations=args.bootstrap_iterations,
            )
            results.append(result)
    else:
        from joblib import Parallel, delayed

        def run_asset(asset: str) -> tuple[AssetOptimizationResult, dict[str, Any]]:
            csv_path = ASSETS[asset]["csv"]
            data = _load_csv(csv_path, btc_start, btc_end)
            return _optimize_asset(
                asset,
                data,
                trials=args.trials,
                mc_iterations=args.mc_iterations,
                bootstrap_iterations=args.bootstrap_iterations,
            )

        tasks = Parallel(n_jobs=args.jobs)(
            delayed(run_asset)(asset) for asset in assets
        )
        results = [res for res, _extra in tasks]

    portfolio_assets = [res for res in results if res.status == "PASS"]

    summary_rows = []
    for res in results:
        summary_rows.append(
            {
                "asset": res.asset,
                "return": res.total_return_pct,
                "sharpe": res.sharpe,
                "maxdd": res.max_drawdown_pct,
                "trades": res.trades,
                "wfe": res.wfe,
                "mc_p": res.mc_p,
                "status": res.status,
            }
        )

    summary_path = "outputs/multi_asset_optimized_summary.csv"
    Path("outputs").mkdir(exist_ok=True)
    pd.DataFrame(summary_rows).to_csv(summary_path, index=False)

    if len(portfolio_assets) >= 2:
        returns = pd.concat(
            [res.daily_returns.rename(res.asset) for res in portfolio_assets],
            axis=1,
            join="inner",
        )
        corr = returns.corr()
        equal_returns = returns.mean(axis=1)
        eq_return, eq_sharpe, eq_max_dd = _portfolio_metrics(equal_returns)

        opt_weights, opt_return, opt_sharpe, opt_max_dd = _optimize_weights(
            returns, min_weight=0.1
        )

        rows = []
        for asset in corr.index:
            for col in corr.columns:
                rows.append(
                    {
                        "section": "correlation",
                        "asset": asset,
                        "metric": col,
                        "value": float(corr.loc[asset, col]),
                    }
                )

        for asset in returns.columns:
            rows.append(
                {
                    "section": "equal_weight",
                    "asset": asset,
                    "metric": "weight",
                    "value": float(1.0 / len(returns.columns)),
                }
            )
        rows.extend(
            [
                {
                    "section": "equal_weight",
                    "asset": "portfolio",
                    "metric": "return_pct",
                    "value": eq_return,
                },
                {
                    "section": "equal_weight",
                    "asset": "portfolio",
                    "metric": "sharpe",
                    "value": eq_sharpe,
                },
                {
                    "section": "equal_weight",
                    "asset": "portfolio",
                    "metric": "max_dd_pct",
                    "value": eq_max_dd,
                },
            ]
        )

        for asset, weight in zip(returns.columns, opt_weights):
            rows.append(
                {
                    "section": "optimized_weight",
                    "asset": asset,
                    "metric": "weight",
                    "value": float(weight),
                }
            )
        rows.extend(
            [
                {
                    "section": "optimized_weight",
                    "asset": "portfolio",
                    "metric": "return_pct",
                    "value": opt_return,
                },
                {
                    "section": "optimized_weight",
                    "asset": "portfolio",
                    "metric": "sharpe",
                    "value": opt_sharpe,
                },
                {
                    "section": "optimized_weight",
                    "asset": "portfolio",
                    "metric": "max_dd_pct",
                    "value": opt_max_dd,
                },
            ]
        )

        portfolio_path = "outputs/portfolio_construction.csv"
        pd.DataFrame(rows).to_csv(portfolio_path, index=False)

    print(f"Saved summary: {summary_path}")


if __name__ == "__main__":
    main()
