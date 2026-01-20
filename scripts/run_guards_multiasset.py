"""
Run full production guards for multiple assets using per-asset params.
"""
from __future__ import annotations

import argparse
import os
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from crypto_backtest.analysis.metrics import compute_metrics
from crypto_backtest.analysis.regime import REGIMES_V2, classify_regimes_v2
from crypto_backtest.config.scan_assets import OPTIM_CONFIG
from crypto_backtest.engine.backtest import BacktestConfig, VectorizedBacktester
from crypto_backtest.optimization.bayesian import _instantiate_strategy
from crypto_backtest.optimization.parallel_optimizer import build_strategy_params, load_data
from crypto_backtest.strategies.final_trigger import FinalTriggerStrategy


BASE_CONFIG = BacktestConfig(
    initial_capital=10000.0,
    fees_bps=5.0,
    slippage_bps=2.0,
    sizing_mode="fixed",
    intrabar_order="stop_first",
)

SEED = 42


def _pnl_series(trades: pd.DataFrame) -> pd.Series:
    if trades is None or trades.empty:
        return pd.Series(dtype=float)
    for col in ("net_pnl", "pnl", "gross_pnl"):
        if col in trades.columns:
            return trades[col].astype(float)
    return pd.Series(dtype=float)


def _run_backtest(
    data: pd.DataFrame,
    params: dict[str, Any],
    config: BacktestConfig,
):
    strategy = _instantiate_strategy(FinalTriggerStrategy, params)
    backtester = VectorizedBacktester(config)
    return backtester.run(data, strategy)


def _map_trade_indices(data: pd.DataFrame, trades: pd.DataFrame) -> pd.DataFrame:
    entries = pd.to_datetime(trades["entry_time"], utc=True)
    exits = pd.to_datetime(trades["exit_time"], utc=True)
    entry_idx = data.index.get_indexer(entries, method="nearest")
    exit_idx = data.index.get_indexer(exits, method="nearest")

    mapped = trades.copy()
    mapped["entry_idx"] = entry_idx
    mapped["exit_idx"] = exit_idx
    mapped["duration"] = mapped["exit_idx"] - mapped["entry_idx"]
    mapped = mapped[mapped["duration"] > 0].reset_index(drop=True)
    return mapped


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


def _monte_carlo_permutation(
    data: pd.DataFrame,
    result,
    iterations: int = 1000,
    seed: int = 42,
) -> tuple[pd.DataFrame, float]:
    trades = result.trades.copy()
    mapped = _map_trade_indices(data, trades)
    if mapped.empty:
        raise RuntimeError("No valid trades for Monte Carlo permutation.")

    direction = mapped["direction"].astype(str).str.lower()
    signs = np.where(direction.str.contains("short"), -1.0, 1.0)

    if "quantity" in mapped.columns:
        quantities = mapped["quantity"].astype(float).to_numpy()
    elif "size" in mapped.columns:
        quantities = mapped["size"].astype(float).to_numpy()
    else:
        quantities = np.ones(len(mapped), dtype=float)

    durations = mapped["duration"].astype(int).to_numpy()
    prices = data["close"].to_numpy()
    cost_rate = (BASE_CONFIG.fees_bps + BASE_CONFIG.slippage_bps) / 10000.0

    actual_metrics = compute_metrics(result.equity_curve, result.trades)
    actual_sharpe = float(actual_metrics.get("sharpe_ratio", 0.0) or 0.0)

    rng = np.random.default_rng(seed)
    rows = []
    for i in range(1, iterations + 1):
        equity = _build_random_equity_curve(
            prices=prices,
            durations=durations,
            signs=signs,
            quantities=quantities,
            cost_rate=cost_rate,
            initial_capital=BASE_CONFIG.initial_capital,
            rng=rng,
        )
        equity_series = pd.Series(equity, index=data.index)
        metrics = compute_metrics(equity_series, pd.DataFrame())
        total_return = (equity[-1] / BASE_CONFIG.initial_capital - 1) * 100
        rows.append(
            {
                "iteration": i,
                "sharpe": float(metrics.get("sharpe_ratio", 0.0) or 0.0),
                "return": float(total_return),
                "max_dd": float(metrics.get("max_drawdown", 0.0) or 0.0),
                "actual_sharpe": actual_sharpe,
            }
        )

    df = pd.DataFrame(rows)
    p_value = float((df["sharpe"] >= actual_sharpe).mean())
    df["p_value"] = p_value
    return df, p_value


def _sensitivity_grid(
    data: pd.DataFrame,
    base_params: dict[str, Any],
) -> tuple[pd.DataFrame, float]:
    tenkan = int(base_params["tenkan"])
    kijun = int(base_params["kijun"])
    tenkan_5 = int(base_params["tenkan_5"])
    kijun_5 = int(base_params["kijun_5"])

    tenkan_range = range(max(1, tenkan - 2), tenkan + 3)
    kijun_range = range(max(1, kijun - 2), kijun + 3)
    tenkan_5_range = range(max(1, tenkan_5 - 2), tenkan_5 + 3)
    kijun_5_range = range(max(1, kijun_5 - 2), kijun_5 + 3)

    rows = []
    for t in tenkan_range:
        for k in kijun_range:
            for t5 in tenkan_5_range:
                for k5 in kijun_5_range:
                    local_params = build_strategy_params(
                        sl_mult=base_params["sl_mult"],
                        tp1_mult=base_params["tp1_mult"],
                        tp2_mult=base_params["tp2_mult"],
                        tp3_mult=base_params["tp3_mult"],
                        tenkan=t,
                        kijun=k,
                        tenkan_5=t5,
                        kijun_5=k5,
                    )
                    result = _run_backtest(data, local_params, BASE_CONFIG)
                    metrics = compute_metrics(result.equity_curve, result.trades)
                    rows.append(
                        {
                            "tenkan": t,
                            "kijun": k,
                            "tenkan_5": t5,
                            "kijun_5": k5,
                            "sharpe": float(metrics.get("sharpe_ratio", 0.0) or 0.0),
                            "return": float(metrics.get("total_return", 0.0) or 0.0) * 100.0,
                            "max_dd": float(metrics.get("max_drawdown", 0.0) or 0.0) * 100.0,
                            "trades": int(len(result.trades)),
                        }
                    )

    df = pd.DataFrame(rows)
    mean_sharpe = float(df["sharpe"].mean()) if not df.empty else 0.0
    std_sharpe = float(df["sharpe"].std(ddof=0)) if not df.empty else 0.0
    variance_pct = (std_sharpe / mean_sharpe * 100.0) if mean_sharpe != 0 else 0.0
    df["mean_sharpe"] = mean_sharpe
    df["std_sharpe"] = std_sharpe
    df["variance_pct"] = variance_pct
    return df, variance_pct


def _bootstrap_confidence(
    pnls: np.ndarray,
    initial_capital: float,
    iterations: int = 10000,
    seed: int = 42,
) -> tuple[pd.DataFrame, dict[str, float]]:
    n = len(pnls)
    rng = np.random.default_rng(seed)
    indices = rng.integers(0, n, size=(iterations, n))
    samples = pnls[indices]

    sample_sum = samples.sum(axis=1)
    total_return = sample_sum / initial_capital * 100.0

    positives = np.where(samples > 0, samples, 0).sum(axis=1)
    negatives = np.where(samples < 0, samples, 0).sum(axis=1)
    profit_factor = np.where(
        negatives == 0,
        np.where(positives > 0, np.inf, 0.0),
        positives / np.abs(negatives),
    )

    returns = samples / initial_capital
    mean_returns = returns.mean(axis=1)
    std_returns = returns.std(axis=1, ddof=0)
    sharpe = np.where(std_returns == 0, 0.0, mean_returns / std_returns * np.sqrt(n))

    metrics = {
        "sharpe": sharpe,
        "total_return": total_return,
        "profit_factor": profit_factor,
    }

    rows = []
    for name, values in metrics.items():
        rows.append(
            {
                "metric": name,
                "mean": float(np.mean(values)),
                "std": float(np.std(values, ddof=0)),
                "ci_lower_95": float(np.percentile(values, 2.5)),
                "ci_upper_95": float(np.percentile(values, 97.5)),
            }
        )

    summary = {row["metric"]: row for row in rows}
    df_summary = pd.DataFrame(rows)
    return df_summary, summary


def _trade_distribution(pnls: np.ndarray) -> dict[str, float]:
    sorted_pnls = np.sort(pnls)[::-1]
    total_pnl = float(pnls.sum())

    top_5_sum = float(sorted_pnls[:5].sum()) if len(sorted_pnls) >= 5 else float(sorted_pnls.sum())
    top_10_sum = float(sorted_pnls[:10].sum()) if len(sorted_pnls) >= 10 else float(sorted_pnls.sum())

    pct_return_top_5 = (top_5_sum / total_pnl * 100.0) if total_pnl != 0 else 0.0
    pct_return_top_10 = (top_10_sum / total_pnl * 100.0) if total_pnl != 0 else 0.0

    return {
        "total_pnl": total_pnl,
        "pct_return_top_5": pct_return_top_5,
        "pct_return_top_10": pct_return_top_10,
    }


def _run_scenario(
    data: pd.DataFrame,
    params: dict[str, Any],
    fees_bps: float,
    slippage_bps: float,
) -> dict[str, Any]:
    config = BacktestConfig(
        initial_capital=BASE_CONFIG.initial_capital,
        fees_bps=fees_bps,
        slippage_bps=slippage_bps,
        sizing_mode=BASE_CONFIG.sizing_mode,
        intrabar_order=BASE_CONFIG.intrabar_order,
    )
    result = _run_backtest(data, params, config)
    final_equity = (
        float(result.equity_curve.iloc[-1])
        if len(result.equity_curve)
        else config.initial_capital
    )
    total_return = (final_equity / config.initial_capital - 1) * 100.0

    metrics = compute_metrics(result.equity_curve, result.trades)
    return {
        "fees_bps": fees_bps,
        "slippage_bps": slippage_bps,
        "total_return_pct": total_return,
        "sharpe": float(metrics.get("sharpe_ratio", 0.0) or 0.0),
        "max_drawdown_pct": float(metrics.get("max_drawdown", 0.0) or 0.0) * 100.0,
        "profit_factor": float(metrics.get("profit_factor", 0.0) or 0.0),
        "trades": int(len(result.trades)),
    }


def _find_break_even_fees(data: pd.DataFrame, params: dict[str, Any]) -> float:
    break_even = 0.0
    for fees in range(0, 51):
        slippage = fees * 0.4
        metrics = _run_scenario(data, params, fees_bps=fees, slippage_bps=slippage)
        if metrics["total_return_pct"] > 0 and metrics["sharpe"] > 0:
            break_even = fees
    return float(break_even)


def _regime_reconciliation(
    data: pd.DataFrame,
    result,
) -> tuple[pd.DataFrame, float]:
    regimes = classify_regimes_v2(data)
    trades = result.trades.copy()
    if trades.empty:
        raise RuntimeError("No trades found for regime reconciliation.")

    trades["entry_time"] = pd.to_datetime(trades["entry_time"], utc=True)
    trades["exit_time"] = pd.to_datetime(trades["exit_time"], utc=True)
    trades["net_pnl"] = _pnl_series(trades)

    entry_idx = data.index.get_indexer(trades["entry_time"], method="nearest")
    if (entry_idx < 0).any():
        trades = trades.loc[entry_idx >= 0].copy()
        entry_idx = entry_idx[entry_idx >= 0]
    trades["regime"] = regimes.iloc[entry_idx].values

    total_pnl_trades = float(trades["net_pnl"].sum())
    regime_pnl = trades.groupby("regime")["net_pnl"].sum()
    regime_count = trades.groupby("regime").size()
    total_pnl_regimes = float(regime_pnl.sum())

    mismatch_pct = (
        abs(total_pnl_trades - total_pnl_regimes) / abs(total_pnl_trades) * 100.0
        if total_pnl_trades != 0
        else 0.0
    )

    reconciliation = []
    for regime in REGIMES_V2:
        pnl = float(regime_pnl.get(regime, 0.0))
        trades_count = int(regime_count.get(regime, 0))
        return_pct = pnl / BASE_CONFIG.initial_capital * 100.0
        pct_total = (pnl / total_pnl_trades * 100.0) if total_pnl_trades else 0.0
        avg_pnl = pnl / trades_count if trades_count else 0.0
        reconciliation.append(
            {
                "regime": regime,
                "trades": trades_count,
                "net_pnl": pnl,
                "return_pct": return_pct,
                "pct_of_total_pnl": pct_total,
                "avg_pnl_per_trade": avg_pnl,
                "pnl_mismatch_pct": mismatch_pct,
            }
        )

    recon_df = pd.DataFrame(reconciliation)
    return recon_df, mismatch_pct


def _write_report(
    path: str,
    asset: str,
    guard_results: dict[str, Any],
) -> None:
    lines = [
        f"GUARDS VALIDATION REPORT: {asset}",
        "=" * 70,
        f"GUARD-001 Monte Carlo p-value: {guard_results['guard001_p_value']:.4f} -> "
        f"{'PASS' if guard_results['guard001_pass'] else 'FAIL'}",
        f"GUARD-002 Sensitivity variance: {guard_results['guard002_variance_pct']:.2f}% -> "
        f"{'PASS' if guard_results['guard002_pass'] else 'FAIL'}",
        "GUARD-003 Bootstrap Sharpe CI lower: "
        f"{guard_results['guard003_sharpe_ci_lower']:.2f} -> "
        f"{'PASS' if guard_results['guard003_pass'] else 'FAIL'}",
        "GUARD-005 Trade distribution top10: "
        f"{guard_results['guard005_top10_pct']:.2f}% -> "
        f"{'PASS' if guard_results['guard005_pass'] else 'FAIL'}",
        "GUARD-006 Stress1 Sharpe: "
        f"{guard_results['guard006_stress1_sharpe']:.2f} -> "
        f"{'PASS' if guard_results['guard006_pass'] else 'FAIL'}",
        "GUARD-007 Regime reconciliation mismatch: "
        f"{guard_results['guard007_mismatch_pct']:.2f}% -> "
        f"{'PASS' if guard_results['guard007_pass'] else 'FAIL'}",
        "-" * 70,
        f"ALL PASS: {'YES' if guard_results['all_pass'] else 'NO'}",
    ]
    Path(path).write_text("\n".join(lines))


def _load_params(params_file: str) -> dict[str, dict[str, Any]]:
    df = pd.read_csv(params_file)
    params_map = {}
    for row in df.itertuples(index=False):
        params_map[str(row.asset)] = {
            "sl_mult": float(row.sl_mult),
            "tp1_mult": float(row.tp1_mult),
            "tp2_mult": float(row.tp2_mult),
            "tp3_mult": float(row.tp3_mult),
            "tenkan": int(row.tenkan),
            "kijun": int(row.kijun),
            "tenkan_5": int(row.tenkan_5),
            "kijun_5": int(row.kijun_5),
        }
    return params_map


def _asset_guard_worker(
    asset: str,
    params: dict[str, Any],
    data_dir: str,
    outputs_dir: str,
) -> dict[str, Any]:
    data = load_data(asset, data_dir)
    if data.index.tz is None:
        data.index = data.index.tz_localize("UTC")
    else:
        data.index = data.index.tz_convert("UTC")
    warmup = OPTIM_CONFIG["warmup_bars"]
    data = data.iloc[warmup:]

    full_params = build_strategy_params(
        sl_mult=params["sl_mult"],
        tp1_mult=params["tp1_mult"],
        tp2_mult=params["tp2_mult"],
        tp3_mult=params["tp3_mult"],
        tenkan=params["tenkan"],
        kijun=params["kijun"],
        tenkan_5=params["tenkan_5"],
        kijun_5=params["kijun_5"],
    )

    base_result = _run_backtest(data, full_params, BASE_CONFIG)
    base_metrics = compute_metrics(base_result.equity_curve, base_result.trades)
    base_sharpe = float(base_metrics.get("sharpe_ratio", 0.0) or 0.0)

    outputs_path = Path(outputs_dir)
    outputs_path.mkdir(exist_ok=True)

    # GUARD-001 Monte Carlo
    mc_df, mc_p = _monte_carlo_permutation(data, base_result, iterations=1000, seed=SEED)
    mc_path = outputs_path / f"{asset}_montecarlo.csv"
    mc_df.to_csv(mc_path, index=False)
    guard001_pass = mc_p < 0.05

    # GUARD-002 Sensitivity
    sens_df, variance_pct = _sensitivity_grid(data, params)
    sens_path = outputs_path / f"{asset}_sensitivity.csv"
    sens_df.to_csv(sens_path, index=False)
    guard002_pass = variance_pct < 10.0

    # GUARD-003 Bootstrap
    pnls = _pnl_series(base_result.trades).to_numpy()
    if len(pnls) == 0:
        raise RuntimeError("No trades for bootstrap confidence intervals.")
    bootstrap_df, bootstrap_summary = _bootstrap_confidence(
        pnls,
        initial_capital=BASE_CONFIG.initial_capital,
        iterations=10000,
        seed=SEED,
    )
    bootstrap_path = outputs_path / f"{asset}_bootstrap.csv"
    bootstrap_df.to_csv(bootstrap_path, index=False)
    sharpe_ci_lower = float(bootstrap_summary["sharpe"]["ci_lower_95"])
    guard003_pass = sharpe_ci_lower > 1.0

    # GUARD-005 Trade distribution
    trade_dist = _trade_distribution(pnls)
    trade_dist["total_return_pct"] = pnls.sum() / BASE_CONFIG.initial_capital * 100.0
    trade_dist_path = outputs_path / f"{asset}_tradedist.csv"
    pd.DataFrame([trade_dist]).to_csv(trade_dist_path, index=False)
    guard005_pass = trade_dist["pct_return_top_10"] < 40.0

    # GUARD-006 Stress test
    scenarios = [
        ("Base", 5, 2),
        ("Stress1", 10, 5),
        ("Stress2", 15, 10),
        ("Stress3", 20, 15),
    ]
    stress_rows = []
    for label, fees, slippage in scenarios:
        metrics = _run_scenario(data, full_params, fees_bps=fees, slippage_bps=slippage)
        metrics["scenario"] = label
        stress_rows.append(metrics)
    break_even_fees = _find_break_even_fees(data, full_params)
    edge_buffer_bps = break_even_fees - 5
    for row in stress_rows:
        row["break_even_fees_bps"] = break_even_fees
        row["edge_buffer_bps"] = edge_buffer_bps
    stress_df = pd.DataFrame(stress_rows)
    stress_path = outputs_path / f"{asset}_stresstest.csv"
    stress_df.to_csv(stress_path, index=False)
    stress1_row = stress_df[stress_df["scenario"] == "Stress1"].iloc[0]
    guard006_pass = float(stress1_row["sharpe"]) > 1.0

    # GUARD-007 Regime reconciliation
    regime_df, mismatch_pct = _regime_reconciliation(data, base_result)
    regime_path = outputs_path / f"{asset}_regime.csv"
    regime_df.to_csv(regime_path, index=False)
    guard007_pass = mismatch_pct < 1.0

    all_pass = all(
        [
            guard001_pass,
            guard002_pass,
            guard003_pass,
            guard005_pass,
            guard006_pass,
            guard007_pass,
        ]
    )

    report_path = outputs_path / f"{asset}_validation_report.txt"
    _write_report(
        str(report_path),
        asset,
        {
            "guard001_p_value": mc_p,
            "guard001_pass": guard001_pass,
            "guard002_variance_pct": variance_pct,
            "guard002_pass": guard002_pass,
            "guard003_sharpe_ci_lower": sharpe_ci_lower,
            "guard003_pass": guard003_pass,
            "guard005_top10_pct": trade_dist["pct_return_top_10"],
            "guard005_pass": guard005_pass,
            "guard006_stress1_sharpe": float(stress1_row["sharpe"]),
            "guard006_pass": guard006_pass,
            "guard007_mismatch_pct": mismatch_pct,
            "guard007_pass": guard007_pass,
            "all_pass": all_pass,
        },
    )

    return {
        "asset": asset,
        "base_sharpe": base_sharpe,
        "guard001_p_value": mc_p,
        "guard001_pass": guard001_pass,
        "guard002_variance_pct": variance_pct,
        "guard002_pass": guard002_pass,
        "guard003_sharpe_ci_lower": sharpe_ci_lower,
        "guard003_pass": guard003_pass,
        "guard005_top10_pct": trade_dist["pct_return_top_10"],
        "guard005_pass": guard005_pass,
        "guard006_stress1_sharpe": float(stress1_row["sharpe"]),
        "guard006_pass": guard006_pass,
        "guard007_mismatch_pct": mismatch_pct,
        "guard007_pass": guard007_pass,
        "all_pass": all_pass,
        "error": "",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run full guard suite for multiple assets.")
    parser.add_argument("--assets", nargs="+", required=True, help="Assets to validate")
    parser.add_argument("--params-file", required=True, help="CSV with per-asset params")
    parser.add_argument("--data-dir", default="data")
    parser.add_argument("--outputs-dir", default="outputs")
    parser.add_argument("--workers", type=int, default=max(os.cpu_count() - 1, 1))
    args = parser.parse_args()

    params_map = _load_params(args.params_file)
    assets = args.assets

    rows = []
    with ProcessPoolExecutor(max_workers=args.workers) as executor:
        futures = {}
        for asset in assets:
            if asset not in params_map:
                rows.append(
                    {
                        "asset": asset,
                        "guard001_pass": False,
                        "guard002_pass": False,
                        "guard003_pass": False,
                        "guard005_pass": False,
                        "guard006_pass": False,
                        "guard007_pass": False,
                        "all_pass": False,
                        "error": "missing_params",
                    }
                )
                continue
            futures[executor.submit(
                _asset_guard_worker,
                asset,
                params_map[asset],
                args.data_dir,
                args.outputs_dir,
            )] = asset

        for future in as_completed(futures):
            asset = futures[future]
            try:
                rows.append(future.result())
            except Exception as exc:
                rows.append(
                    {
                        "asset": asset,
                        "guard001_pass": False,
                        "guard002_pass": False,
                        "guard003_pass": False,
                        "guard005_pass": False,
                        "guard006_pass": False,
                        "guard007_pass": False,
                        "all_pass": False,
                        "error": str(exc),
                    }
                )

    summary_df = pd.DataFrame(rows)
    output_path = Path(args.outputs_dir) / "multiasset_guards_summary.csv"
    summary_df.to_csv(output_path, index=False)


if __name__ == "__main__":
    main()
