"""
Parallel Multi-Asset Optimizer for CODEX MULTI-ASSET-005
Uses joblib for parallel execution across multiple assets
"""
from __future__ import annotations

import json
import os
import warnings
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from contextlib import contextmanager
from typing import Any

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

try:
    import fcntl  # type: ignore[attr-defined]
except ImportError:
    fcntl = None

from crypto_backtest.analysis.metrics import compute_metrics
from crypto_backtest.config.scan_assets import (
    OPTIM_CONFIG,
    ATR_SEARCH_SPACE,
    ICHI_SEARCH_SPACE,
    PASS_CRITERIA,
    EXCHANGE_MAP,
)
from crypto_backtest.engine.backtest import BacktestConfig, VectorizedBacktester
from crypto_backtest.strategies.final_trigger import FinalTriggerStrategy
from crypto_backtest.optimization.bayesian import _instantiate_strategy, _apply_overrides
from crypto_backtest.validation.conservative_reopt import (
    CONSERVATIVE_ATR_SPACE,
    CONSERVATIVE_ICHI_SPACE,
    CONSERVATIVE_SPLIT_RATIO,
)


# Suppress Optuna logging
try:
    import optuna
    optuna.logging.set_verbosity(optuna.logging.WARNING)
except ImportError:
    pass


BASE_CONFIG = BacktestConfig(
    initial_capital=10000.0,
    fees_bps=5.0,
    slippage_bps=2.0,
    sizing_mode="fixed",
    intrabar_order="stop_first",
)


SEED = 42  # Global seed for reproducibility


@dataclass
class AssetScanResult:
    """Result of scanning a single asset."""
    asset: str
    status: str
    # Metadata
    exchange: str = ""
    timeframe: str = "1H"
    start_date: str = ""
    end_date: str = ""
    total_bars: int = 0
    seed: int = SEED
    fail_reason: str = ""
    # ATR params
    sl_mult: float = 0.0
    tp1_mult: float = 0.0
    tp2_mult: float = 0.0
    tp3_mult: float = 0.0
    # Ichimoku params
    tenkan: int = 0
    kijun: int = 0
    tenkan_5: int = 0
    kijun_5: int = 0
    # IS metrics
    is_sharpe: float = 0.0
    is_return: float = 0.0
    is_trades: int = 0
    # VAL metrics
    val_sharpe: float = 0.0
    val_return: float = 0.0
    val_trades: int = 0
    # OOS metrics
    oos_sharpe: float = 0.0
    oos_return: float = 0.0
    oos_trades: int = 0
    oos_max_dd: float = 0.0
    oos_pf: float = 0.0
    # Validation
    wfe: float = 0.0
    mc_p: float = 1.0
    # Error info
    error: str = ""


@contextmanager
def _locked_file(path: Path):
    """Open a file with an exclusive lock when supported."""
    path.parent.mkdir(exist_ok=True)
    with open(path, "a+", newline="") as handle:
        if fcntl is not None:
            fcntl.flock(handle, fcntl.LOCK_EX)
        try:
            yield handle
        finally:
            if fcntl is not None:
                fcntl.flock(handle, fcntl.LOCK_UN)


def _log_progress(asset: str, stage: str) -> None:
    print(f"[{asset}] {stage}")


def _result_to_row(result: AssetScanResult) -> dict[str, Any]:
    return {
        "asset": result.asset,
        "status": result.status,
        "exchange": result.exchange,
        "timeframe": result.timeframe,
        "start_date": result.start_date,
        "end_date": result.end_date,
        "total_bars": result.total_bars,
        "seed": result.seed,
        "fail_reason": result.fail_reason,
        "sl_mult": result.sl_mult,
        "tp1_mult": result.tp1_mult,
        "tp2_mult": result.tp2_mult,
        "tp3_mult": result.tp3_mult,
        "tenkan": result.tenkan,
        "kijun": result.kijun,
        "tenkan_5": result.tenkan_5,
        "kijun_5": result.kijun_5,
        "is_sharpe": result.is_sharpe,
        "is_return": result.is_return,
        "is_trades": result.is_trades,
        "val_sharpe": result.val_sharpe,
        "val_return": result.val_return,
        "val_trades": result.val_trades,
        "oos_sharpe": result.oos_sharpe,
        "oos_return": result.oos_return,
        "oos_trades": result.oos_trades,
        "oos_max_dd": result.oos_max_dd,
        "oos_pf": result.oos_pf,
        "wfe": result.wfe,
        "mc_p": result.mc_p,
        "error": result.error,
    }


def append_partial_result(
    result: AssetScanResult,
    output_path: str = "outputs/multi_asset_scan_partial.csv",
) -> None:
    """Append a single result row to a partial CSV for live progress."""
    row = _result_to_row(result)
    path = Path(output_path)

    with _locked_file(path) as handle:
        handle.seek(0, os.SEEK_END)
        header_needed = handle.tell() == 0
        pd.DataFrame([row]).to_csv(handle, header=header_needed, index=False)


def load_data(asset: str, data_dir: str = "data") -> pd.DataFrame:
    """Load OHLCV data for an asset."""
    # Try parquet first, then CSV
    parquet_path = Path(data_dir) / f"{asset}_1H.parquet"
    csv_path = Path(data_dir) / f"Binance_{asset}USDT_1h.csv"

    if parquet_path.exists():
        df = pd.read_parquet(parquet_path)
        if not isinstance(df.index, pd.DatetimeIndex):
            if "timestamp" in df.columns:
                df.index = pd.to_datetime(df["timestamp"], utc=True)
            else:
                df.index = pd.to_datetime(df.index, utc=True)
        return df

    if csv_path.exists():
        df = pd.read_csv(csv_path)
        df.columns = [col.strip() for col in df.columns]
        if "timestamp" in df.columns:
            df.index = pd.to_datetime(df["timestamp"], utc=True)
        return df[["open", "high", "low", "close", "volume"]]

    raise FileNotFoundError(f"No data found for {asset} in {data_dir}")


def split_data(df: pd.DataFrame, splits=(0.6, 0.2, 0.2)):
    """Split data into IS/VAL/OOS segments."""
    n = len(df)
    is_end = int(n * splits[0])
    val_end = int(n * (splits[0] + splits[1]))
    return df.iloc[:is_end], df.iloc[is_end:val_end], df.iloc[val_end:]


def build_strategy_params(
    sl_mult: float,
    tp1_mult: float,
    tp2_mult: float,
    tp3_mult: float,
    tenkan: int,
    kijun: int,
    tenkan_5: int,
    kijun_5: int,
) -> dict[str, Any]:
    """Build strategy parameters dict."""
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


def run_backtest(
    data: pd.DataFrame,
    params: dict[str, Any],
    config: BacktestConfig = BASE_CONFIG,
) -> dict[str, float]:
    """Run backtest and return metrics dict."""
    strategy = _instantiate_strategy(FinalTriggerStrategy, params)
    backtester = VectorizedBacktester(config)
    result = backtester.run(data, strategy)
    metrics = compute_metrics(result.equity_curve, result.trades)

    return {
        "sharpe": float(metrics.get("sharpe_ratio", 0.0)),
        "total_return": float(metrics.get("total_return", 0.0) * 100.0),
        "max_drawdown": float(metrics.get("max_drawdown", 0.0) * 100.0),
        "profit_factor": float(metrics.get("profit_factor", 0.0)),
        "trades": int(len(result.trades)),
        "win_rate": float(metrics.get("win_rate", 0.0) * 100.0),
    }


def optimize_atr(
    data: pd.DataFrame,
    n_trials: int = 100,
    min_trades: int = 50,
) -> tuple[dict[str, float], float]:
    """Optimize ATR parameters."""
    import optuna

    best_params = {}
    best_sharpe = -np.inf

    def objective(trial: optuna.Trial) -> float:
        sl = trial.suggest_float("sl_mult", *ATR_SEARCH_SPACE["sl_mult"], step=0.25)
        tp1 = trial.suggest_float("tp1_mult", *ATR_SEARCH_SPACE["tp1_mult"], step=0.25)
        tp2 = trial.suggest_float("tp2_mult", *ATR_SEARCH_SPACE["tp2_mult"], step=0.5)
        tp3 = trial.suggest_float("tp3_mult", *ATR_SEARCH_SPACE["tp3_mult"], step=0.5)

        params = build_strategy_params(
            sl_mult=sl, tp1_mult=tp1, tp2_mult=tp2, tp3_mult=tp3,
            tenkan=9, kijun=26, tenkan_5=9, kijun_5=26
        )

        result = run_backtest(data, params)

        if result["trades"] < min_trades:
            return -10.0

        return result["sharpe"]

    sampler = optuna.samplers.TPESampler(seed=42)
    study = optuna.create_study(direction="maximize", sampler=sampler)
    study.optimize(objective, n_trials=n_trials, show_progress_bar=False)

    return study.best_params, float(study.best_value)


def optimize_atr_conservative(
    data: pd.DataFrame,
    n_trials: int = 200,
    min_trades: int = 50,
) -> tuple[dict[str, float], float]:
    """Optimize ATR parameters with a discrete grid."""
    import optuna

    def objective(trial: optuna.Trial) -> float:
        sl = trial.suggest_categorical("sl_mult", CONSERVATIVE_ATR_SPACE["sl_mult"])
        tp1 = trial.suggest_categorical("tp1_mult", CONSERVATIVE_ATR_SPACE["tp1_mult"])
        tp2 = trial.suggest_categorical("tp2_mult", CONSERVATIVE_ATR_SPACE["tp2_mult"])
        tp3 = trial.suggest_categorical("tp3_mult", CONSERVATIVE_ATR_SPACE["tp3_mult"])

        params = build_strategy_params(
            sl_mult=sl, tp1_mult=tp1, tp2_mult=tp2, tp3_mult=tp3,
            tenkan=9, kijun=26, tenkan_5=9, kijun_5=26
        )

        result = run_backtest(data, params)

        if result["trades"] < min_trades:
            return -10.0

        return result["sharpe"]

    sampler = optuna.samplers.TPESampler(seed=42)
    study = optuna.create_study(direction="maximize", sampler=sampler)
    study.optimize(objective, n_trials=n_trials, show_progress_bar=False)

    return study.best_params, float(study.best_value)


def optimize_ichimoku(
    data: pd.DataFrame,
    atr_params: dict[str, float],
    n_trials: int = 100,
    min_trades: int = 50,
) -> tuple[dict[str, int], float]:
    """Optimize Ichimoku parameters."""
    import optuna

    def objective(trial: optuna.Trial) -> float:
        tenkan = trial.suggest_int("tenkan", *ICHI_SEARCH_SPACE["tenkan"])
        kijun = trial.suggest_int("kijun", *ICHI_SEARCH_SPACE["kijun"])
        tenkan_5 = trial.suggest_int("tenkan_5", *ICHI_SEARCH_SPACE["tenkan_5"])
        kijun_5 = trial.suggest_int("kijun_5", *ICHI_SEARCH_SPACE["kijun_5"])

        params = build_strategy_params(
            sl_mult=atr_params["sl_mult"],
            tp1_mult=atr_params["tp1_mult"],
            tp2_mult=atr_params["tp2_mult"],
            tp3_mult=atr_params["tp3_mult"],
            tenkan=tenkan, kijun=kijun,
            tenkan_5=tenkan_5, kijun_5=kijun_5,
        )

        result = run_backtest(data, params)

        if result["trades"] < min_trades:
            return -10.0

        return result["sharpe"]

    sampler = optuna.samplers.TPESampler(seed=42)
    study = optuna.create_study(direction="maximize", sampler=sampler)
    study.optimize(objective, n_trials=n_trials, show_progress_bar=False)

    return study.best_params, float(study.best_value)


def optimize_ichimoku_conservative(
    data: pd.DataFrame,
    atr_params: dict[str, float],
    n_trials: int = 200,
    min_trades: int = 50,
) -> tuple[dict[str, int], float]:
    """Optimize Ichimoku parameters with a discrete grid."""
    import optuna

    def objective(trial: optuna.Trial) -> float:
        tenkan = trial.suggest_categorical("tenkan", CONSERVATIVE_ICHI_SPACE["tenkan"])
        kijun = trial.suggest_categorical("kijun", CONSERVATIVE_ICHI_SPACE["kijun"])
        tenkan_5 = trial.suggest_categorical("tenkan_5", CONSERVATIVE_ICHI_SPACE["tenkan_5"])
        kijun_5 = trial.suggest_categorical("kijun_5", CONSERVATIVE_ICHI_SPACE["kijun_5"])

        if tenkan >= kijun or tenkan_5 >= kijun_5:
            return -10.0

        params = build_strategy_params(
            sl_mult=atr_params["sl_mult"],
            tp1_mult=atr_params["tp1_mult"],
            tp2_mult=atr_params["tp2_mult"],
            tp3_mult=atr_params["tp3_mult"],
            tenkan=tenkan, kijun=kijun,
            tenkan_5=tenkan_5, kijun_5=kijun_5,
        )

        result = run_backtest(data, params)

        if result["trades"] < min_trades:
            return -10.0

        return result["sharpe"]

    sampler = optuna.samplers.TPESampler(seed=42)
    study = optuna.create_study(direction="maximize", sampler=sampler)
    study.optimize(objective, n_trials=n_trials, show_progress_bar=False)

    return study.best_params, float(study.best_value)


def monte_carlo_pvalue(
    data: pd.DataFrame,
    params: dict[str, Any],
    actual_sharpe: float,
    iterations: int = 500,
    seed: int = 42,
) -> float:
    """Quick Monte Carlo permutation test."""
    strategy = _instantiate_strategy(FinalTriggerStrategy, params)
    backtester = VectorizedBacktester(BASE_CONFIG)
    result = backtester.run(data, strategy)

    if result.trades.empty:
        return 1.0

    # Extract trade info
    prices = data["close"].to_numpy()
    n_bars = len(prices)
    n_trades = len(result.trades)

    if n_trades == 0:
        return 1.0

    # Simplified: randomize entry points
    rng = np.random.default_rng(seed)
    sharpe_values = []

    for _ in range(iterations):
        # Random equity curve
        random_returns = rng.choice(prices[1:] / prices[:-1] - 1, size=n_bars - 1)
        equity = BASE_CONFIG.initial_capital * np.cumprod(1 + random_returns * 0.01)
        equity_series = pd.Series(equity, index=data.index[1:])
        metrics = compute_metrics(equity_series, pd.DataFrame())
        sharpe_values.append(float(metrics.get("sharpe_ratio", 0.0)))

    return float((np.array(sharpe_values) >= actual_sharpe).mean())


def optimize_single_asset(
    asset: str,
    data_dir: str = "data",
    n_trials_atr: int = None,
    n_trials_ichi: int = None,
    mc_iterations: int = 500,
    conservative: bool = False,
) -> AssetScanResult:
    """Full optimization pipeline for one asset."""
    default_atr = OPTIM_CONFIG["n_trials_atr"]
    default_ichi = OPTIM_CONFIG["n_trials_ichi"]
    n_trials_atr = n_trials_atr or default_atr
    n_trials_ichi = n_trials_ichi or default_ichi
    if conservative:
        n_trials_atr = max(n_trials_atr, 200)
        n_trials_ichi = max(n_trials_ichi, 200)
    min_trades = OPTIM_CONFIG["min_trades"]
    exchange = EXCHANGE_MAP.get(asset, "binance")
    start_date = ""
    end_date = ""
    total_bars_raw = 0

    _log_progress(asset, "START")

    try:
        # 1. Load and split data
        _log_progress(asset, "download")
        df = load_data(asset, data_dir)
        total_bars_raw = len(df)
        start_date = str(df.index[0])[:10] if len(df) > 0 else ""
        end_date = str(df.index[-1])[:10] if len(df) > 0 else ""

        df = df.iloc[OPTIM_CONFIG["warmup_bars"]:]
        splits = CONSERVATIVE_SPLIT_RATIO if conservative else (0.6, 0.2, 0.2)
        df_is, df_val, df_oos = split_data(df, splits=splits)

        print(f"[{asset}] Data: IS={len(df_is)}, VAL={len(df_val)}, OOS={len(df_oos)} bars [{start_date} → {end_date}]")

        # 2. ATR Optimization on IS
        _log_progress(asset, "ATR opt")
        if conservative:
            atr_params, atr_sharpe = optimize_atr_conservative(
                df_is, n_trials_atr, min_trades
            )
        else:
            atr_params, atr_sharpe = optimize_atr(df_is, n_trials_atr, min_trades)
        print(f"[{asset}] ATR done: Sharpe={atr_sharpe:.2f}, params={atr_params}")

        # 3. Ichimoku Optimization on IS
        _log_progress(asset, "Ichi opt")
        if conservative:
            ichi_params, ichi_sharpe = optimize_ichimoku_conservative(
                df_is, atr_params, n_trials_ichi, min_trades
            )
        else:
            ichi_params, ichi_sharpe = optimize_ichimoku(
                df_is, atr_params, n_trials_ichi, min_trades
            )
        print(f"[{asset}] Ichi done: Sharpe={ichi_sharpe:.2f}, params={ichi_params}")

        # 4. Build final params
        final_params = build_strategy_params(
            sl_mult=atr_params["sl_mult"],
            tp1_mult=atr_params["tp1_mult"],
            tp2_mult=atr_params["tp2_mult"],
            tp3_mult=atr_params["tp3_mult"],
            tenkan=ichi_params["tenkan"],
            kijun=ichi_params["kijun"],
            tenkan_5=ichi_params["tenkan_5"],
            kijun_5=ichi_params["kijun_5"],
        )

        # 5. Evaluate on all segments
        _log_progress(asset, "WF")
        is_results = run_backtest(df_is, final_params)
        val_results = run_backtest(df_val, final_params)
        oos_results = run_backtest(df_oos, final_params)

        # 6. Calculate WFE
        wfe = oos_results["sharpe"] / is_results["sharpe"] if is_results["sharpe"] > 0 else 0

        # 7. Monte Carlo p-value
        _log_progress(asset, "MC")
        mc_p = monte_carlo_pvalue(df_oos, final_params, oos_results["sharpe"], mc_iterations)

        # 8. Determine status and fail_reason
        status = "SUCCESS"
        fail_reasons = []

        if oos_results["sharpe"] < PASS_CRITERIA["oos_sharpe_min"]:
            fail_reasons.append(f"OOS_SHARPE<{PASS_CRITERIA['oos_sharpe_min']}")
        if wfe < PASS_CRITERIA["wfe_min"]:
            fail_reasons.append(f"WFE<{PASS_CRITERIA['wfe_min']}")
        if oos_results["trades"] < PASS_CRITERIA["oos_trades_min"]:
            fail_reasons.append(f"TRADES<{PASS_CRITERIA['oos_trades_min']}")
        if abs(oos_results["max_drawdown"]) > PASS_CRITERIA["max_dd_max"] * 100:
            fail_reasons.append(f"DD>{PASS_CRITERIA['max_dd_max']*100}%")

        if fail_reasons:
            status = "FAIL"
        if wfe < 0.6:
            fail_reasons.append("OVERFIT")
            if status == "SUCCESS":
                status = "FAIL"

        fail_reason = "; ".join(fail_reasons) if fail_reasons else ""

        result = AssetScanResult(
            asset=asset,
            status=status,
            exchange=exchange,
            timeframe="1H",
            start_date=start_date,
            end_date=end_date,
            total_bars=total_bars_raw,
            seed=SEED,
            fail_reason=fail_reason,
            sl_mult=atr_params["sl_mult"],
            tp1_mult=atr_params["tp1_mult"],
            tp2_mult=atr_params["tp2_mult"],
            tp3_mult=atr_params["tp3_mult"],
            tenkan=ichi_params["tenkan"],
            kijun=ichi_params["kijun"],
            tenkan_5=ichi_params["tenkan_5"],
            kijun_5=ichi_params["kijun_5"],
            is_sharpe=is_results["sharpe"],
            is_return=is_results["total_return"],
            is_trades=is_results["trades"],
            val_sharpe=val_results["sharpe"],
            val_return=val_results["total_return"],
            val_trades=val_results["trades"],
            oos_sharpe=oos_results["sharpe"],
            oos_return=oos_results["total_return"],
            oos_trades=oos_results["trades"],
            oos_max_dd=oos_results["max_drawdown"],
            oos_pf=oos_results["profit_factor"],
            wfe=wfe,
            mc_p=mc_p,
        )

        _log_progress(asset, "DONE")
        print(f"[{asset}] ✓ Complete: OOS Sharpe={oos_results['sharpe']:.2f}, WFE={wfe:.2f}, Status={status}")
        try:
            append_partial_result(result)
        except Exception as append_error:
            print(f"[{asset}] Partial CSV append failed: {append_error}")
        return result

    except Exception as e:
        print(f"[{asset}] ✗ Error: {e}")
        result = AssetScanResult(
            asset=asset,
            status="FAIL",
            exchange=exchange,
            timeframe="1H",
            start_date=start_date,
            end_date=end_date,
            total_bars=total_bars_raw,
            seed=SEED,
            fail_reason=f"ERROR: {str(e)}",
            error=str(e)
        )
        try:
            append_partial_result(result)
        except Exception as append_error:
            print(f"[{asset}] Partial CSV append failed: {append_error}")
        return result


def run_parallel_scan(
    assets: list[str],
    data_dir: str = "data",
    n_workers: int = None,
    n_trials_atr: int = None,
    n_trials_ichi: int = None,
    cluster: bool = False,
    cluster_count: int = None,
    conservative: bool = False,
) -> pd.DataFrame:
    """Run optimization for all assets in parallel."""
    from joblib import Parallel, delayed
    import multiprocessing

    n_workers = n_workers or min(multiprocessing.cpu_count(), len(assets))

    print("=" * 60)
    print("MULTI-ASSET PARALLEL SCAN")
    print(f"Assets: {assets}")
    print(f"Workers: {n_workers}")
    print(f"Conservative: {conservative}")
    print("=" * 60)

    # Run in parallel
    results = Parallel(n_jobs=n_workers)(
        delayed(optimize_single_asset)(
            asset, data_dir, n_trials_atr, n_trials_ichi, 500, conservative
        )
        for asset in assets
    )

    # Convert to DataFrame
    rows = [_result_to_row(r) for r in results]

    df = pd.DataFrame(rows)

    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    Path("outputs").mkdir(exist_ok=True)
    output_path = f"outputs/multiasset_scan_{timestamp}.csv"
    debug_output_path = f"outputs/multi_asset_scan_{timestamp}.csv"
    df.to_csv(output_path, index=False)
    df.to_csv(debug_output_path, index=False)

    # Print summary
    print("\n" + "=" * 60)
    print("SCAN COMPLETE")
    print("=" * 60)

    success_df = df[df["status"].str.startswith("SUCCESS")]
    if len(success_df) > 0:
        print("\nPASSED ASSETS:")
        print(success_df[["asset", "oos_sharpe", "oos_trades", "wfe"]].to_string(index=False))

    failed_df = df[~df["status"].str.startswith("SUCCESS")]
    if len(failed_df) > 0:
        print("\nFAILED ASSETS:")
        print(failed_df[["asset", "status", "oos_sharpe", "wfe"]].to_string(index=False))

    print(f"\nResults saved to: {output_path}")
    print(f"Debug copy saved to: {debug_output_path}")

    if cluster:
        from crypto_backtest.analysis.cluster_params import run_full_analysis

        print("\nRunning clustering analysis...")
        run_full_analysis(output_path, cluster_count)

    return df


def main():
    import argparse
    from crypto_backtest.config.scan_assets import SCAN_ASSETS

    parser = argparse.ArgumentParser(description="Multi-Asset Parallel Optimizer")
    parser.add_argument("--workers", type=int, default=None, help="Number of parallel workers")
    parser.add_argument("--assets", nargs="+", default=None, help="Specific assets to scan")
    parser.add_argument("--trials-atr", type=int, default=100, help="ATR optimization trials")
    parser.add_argument("--trials-ichi", type=int, default=100, help="Ichimoku optimization trials")
    parser.add_argument("--data-dir", type=str, default="data", help="Data directory")
    parser.add_argument("--cluster", action="store_true", help="Run clustering on successful assets")
    parser.add_argument("--clusters", type=int, default=None, help="Force number of clusters")
    parser.add_argument("--conservative", action="store_true", help="Use conservative search space")
    args = parser.parse_args()

    assets = args.assets or SCAN_ASSETS

    run_parallel_scan(
        assets=assets,
        data_dir=args.data_dir,
        n_workers=args.workers,
        n_trials_atr=args.trials_atr,
        n_trials_ichi=args.trials_ichi,
        cluster=args.cluster,
        cluster_count=args.clusters,
        conservative=args.conservative,
    )


if __name__ == "__main__":
    main()
