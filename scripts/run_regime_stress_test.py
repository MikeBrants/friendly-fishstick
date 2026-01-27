#!/usr/bin/env python3
"""
Regime Stress Test - FINAL TRIGGER v2

Filters trades by ENTRY regime using regime_v3 (no look-ahead).

CLI:
  python scripts/run_regime_stress_test.py --asset ETH --regimes MARKDOWN SIDEWAYS --output outputs/regime_stress_ETH.csv
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable, List, Tuple

import numpy as np
import pandas as pd

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from crypto_backtest.analysis.regime_v3 import CryptoRegimeAnalyzer, CryptoRegime, TrendRegime
from crypto_backtest.config.asset_config import ASSET_CONFIG
from crypto_backtest.engine.backtest import BacktestConfig, VectorizedBacktester
from crypto_backtest.optimization.bayesian import _instantiate_strategy
from crypto_backtest.optimization.parallel_optimizer import build_strategy_params, load_data
from crypto_backtest.strategies.final_trigger import FinalTriggerStrategy


ALLOWED_REGIMES = {"MARKDOWN", "SIDEWAYS"}


@dataclass
class TradeStats:
    n_trades: int
    sharpe: float
    max_dd: float


def _to_utc_index(index: pd.Index) -> pd.DatetimeIndex:
    dt_index = pd.to_datetime(index)
    if dt_index.tz is None:
        return dt_index.tz_localize("UTC")
    return dt_index.tz_convert("UTC")


def _to_utc_series(series: pd.Series) -> pd.Series:
    dt = pd.to_datetime(series, errors="coerce")
    if dt.dt.tz is None:
        return dt.dt.tz_localize("UTC")
    return dt.dt.tz_convert("UTC")


def resolve_regime_column(regime: str) -> Tuple[str, str]:
    regime = regime.upper()
    if regime == "MARKDOWN":
        return "crypto_regime", CryptoRegime.MARKDOWN.value
    if regime == "SIDEWAYS":
        return "trend_regime", TrendRegime.SIDEWAYS.value
    raise ValueError(f"Unsupported regime: {regime}. Allowed: {sorted(ALLOWED_REGIMES)}")


def _aggregate_trade_pnl(trades: pd.DataFrame) -> pd.Series:
    if trades is None or trades.empty:
        return pd.Series(dtype=float)

    if "pnl" in trades.columns:
        pnl_col = "pnl"
    elif "net_pnl" in trades.columns:
        pnl_col = "net_pnl"
    elif "gross_pnl" in trades.columns:
        pnl_col = "gross_pnl"
    else:
        return pd.Series(dtype=float)

    if "entry_time" in trades.columns:
        return trades.groupby("entry_time")[pnl_col].sum().astype(float)

    return trades[pnl_col].astype(float)


def compute_trade_stats(trades: pd.DataFrame, initial_capital: float = 10000.0) -> TradeStats:
    pnl = _aggregate_trade_pnl(trades)
    if pnl.empty:
        return TradeStats(n_trades=0, sharpe=float("nan"), max_dd=float("nan"))

    pnl = pnl.sort_index()
    trade_returns = pnl / initial_capital

    std = float(trade_returns.std(ddof=0))
    if std > 0:
        sharpe = float(trade_returns.mean() / std * np.sqrt(252))
    else:
        sharpe = 0.0

    equity = initial_capital + pnl.cumsum()
    hwm = equity.cummax()
    drawdown = equity / hwm - 1.0
    max_dd = float(abs(drawdown.min()) * 100.0) if not drawdown.empty else 0.0

    return TradeStats(n_trades=int(len(pnl)), sharpe=sharpe, max_dd=max_dd)


def filter_trades_by_entry_regime(
    trades: pd.DataFrame,
    regimes_df: pd.DataFrame,
    regime_column: str,
    target_regime: str,
) -> pd.DataFrame:
    if trades is None or trades.empty:
        return trades

    if "entry_time" not in trades.columns:
        return trades.iloc[0:0]

    regimes = regimes_df.copy()
    regimes.index = _to_utc_index(regimes.index)
    regimes = regimes.sort_index()

    entry_times = _to_utc_series(trades["entry_time"])

    indexer = regimes.index.get_indexer(entry_times, method="pad")
    valid_mask = indexer >= 0
    mapped = pd.Series(index=trades.index, dtype=object)
    mapped.loc[valid_mask] = regimes.iloc[indexer[valid_mask]][regime_column].to_numpy()

    return trades[mapped == target_regime]


def evaluate_verdict(regime: str, n_trades: int, sharpe: float) -> str:
    regime = regime.upper()
    if regime == "MARKDOWN":
        if n_trades <= 10:
            return "PASS"
        if np.isnan(sharpe):
            return "FAIL"
        return "PASS" if sharpe >= -2.0 else "FAIL"
    if regime == "SIDEWAYS":
        if np.isnan(sharpe):
            return "EXCLU"
        return "PASS" if sharpe >= 0.0 else "EXCLU"
    raise ValueError(f"Unsupported regime: {regime}")


def _get_asset_params(asset: str) -> dict:
    if asset not in ASSET_CONFIG:
        raise KeyError(f"Asset {asset} not found in ASSET_CONFIG")

    cfg = ASSET_CONFIG[asset]
    return build_strategy_params(
        sl_mult=cfg["atr"]["sl_mult"],
        tp1_mult=cfg["atr"]["tp1_mult"],
        tp2_mult=cfg["atr"]["tp2_mult"],
        tp3_mult=cfg["atr"]["tp3_mult"],
        tenkan=cfg["ichimoku"]["tenkan"],
        kijun=cfg["ichimoku"]["kijun"],
        tenkan_5=cfg["five_in_one"]["tenkan_5"],
        kijun_5=cfg["five_in_one"]["kijun_5"],
        displacement=cfg.get("displacement", 52),
    )


def _run_backtest(asset: str) -> Tuple[pd.DataFrame, pd.DataFrame]:
    data = load_data(asset, data_dir=str(PROJECT_ROOT / "data"))
    data.index = _to_utc_index(data.index)

    params = _get_asset_params(asset)
    strategy = _instantiate_strategy(FinalTriggerStrategy, params)

    config = BacktestConfig(
        initial_capital=10000.0,
        fees_bps=6.0,
        slippage_bps=2.0,
        sizing_mode="fixed",
        risk_per_trade=0.01,
        intrabar_order="stop_first",
    )
    backtester = VectorizedBacktester(config)
    result = backtester.run(data, strategy)

    return data, result.trades


def _compute_regimes(data: pd.DataFrame) -> pd.DataFrame:
    analyzer = CryptoRegimeAnalyzer(use_hmm=False, lookback=200)
    regimes_df = analyzer.fit_and_classify(data)
    regimes_df.index = _to_utc_index(regimes_df.index)
    return regimes_df


def run_asset_regime_stress(asset: str, regimes: Iterable[str]) -> List[dict]:
    asset = asset.upper()
    data, trades = _run_backtest(asset)
    regimes_df = _compute_regimes(data)

    rows = []
    for regime in regimes:
        col, target = resolve_regime_column(regime)
        filtered = filter_trades_by_entry_regime(trades, regimes_df, col, target)
        stats = compute_trade_stats(filtered)
        verdict = evaluate_verdict(regime, stats.n_trades, stats.sharpe)
        rows.append(
            {
                "asset": asset,
                "regime": regime.upper(),
                "trades": stats.n_trades,
                "sharpe": round(stats.sharpe, 4) if not np.isnan(stats.sharpe) else np.nan,
                "max_dd": round(stats.max_dd, 4) if not np.isnan(stats.max_dd) else np.nan,
                "verdict": verdict,
            }
        )
    return rows


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Regime stress test (entry regime filter)")
    parser.add_argument("--asset", type=str, help="Single asset to test (e.g., ETH)")
    parser.add_argument("--assets", nargs="+", help="Multiple assets to test (space-separated)")
    parser.add_argument("--regimes", nargs="+", required=True, help="Regimes to test (MARKDOWN, SIDEWAYS)")
    parser.add_argument("--output", type=str, help="Output CSV path")
    parser.add_argument("--regime", type=str, help="Deprecated. Use --regimes instead.")
    return parser.parse_args()


def _normalize_regimes(regimes: Iterable[str], fallback: str | None) -> List[str]:
    normalized = [r.upper() for r in regimes] if regimes else []
    if fallback:
        normalized.append(fallback.upper())
    normalized = list(dict.fromkeys(normalized))

    for regime in normalized:
        if regime not in ALLOWED_REGIMES:
            raise ValueError(f"Unsupported regime: {regime}. Allowed: {sorted(ALLOWED_REGIMES)}")

    return normalized


def main() -> int:
    args = _parse_args()

    assets: List[str] = []
    if args.asset:
        assets.append(args.asset)
    if args.assets:
        assets.extend(args.assets)
    assets = [a.upper() for a in assets]

    if not assets:
        raise SystemExit("Provide --asset or --assets")

    regimes = _normalize_regimes(args.regimes, args.regime)

    results: List[dict] = []
    for asset in assets:
        results.extend(run_asset_regime_stress(asset, regimes))

    df = pd.DataFrame(results, columns=["asset", "regime", "trades", "sharpe", "max_dd", "verdict"])

    output_path = args.output
    if not output_path:
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        output_path = f"outputs/regime_stress_{timestamp}.csv"

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    print(df.to_string(index=False))
    print(f"Saved: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
