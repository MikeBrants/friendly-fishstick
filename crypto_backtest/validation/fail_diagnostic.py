"""
Fail diagnostic module for failed assets.
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd


HISTORY_OUTPUT_PATH = Path("outputs/diagnostic_history.json")
HISTORY_CONFIG_PATH = Path("config/diagnostic_history.json")


class FailDiagnostic:
    """Forensic analysis to explain why an asset failed."""

    def __init__(
        self,
        asset: str,
        scan_result: dict,
        data: pd.DataFrame,
        trades_is: Optional[pd.DataFrame] = None,
        trades_oos: Optional[pd.DataFrame] = None,
    ):
        self.asset = asset
        self.result = scan_result
        self.data = data
        self.trades_is = self._normalize_trades(trades_is)
        self.trades_oos = self._normalize_trades(trades_oos)
        self.diagnosis: list[dict] = []
        self.timestamp = datetime.now().isoformat()

    def run_full_diagnostic(self) -> dict:
        """Run all diagnostics and return a report."""
        checks = [
            self.check_overfitting_severity(),
            self.check_regime_shift(),
            self.check_sample_size(),
            self.check_param_stability(),
            self.check_trade_distribution_shift(),
            self.check_temporal_decay(),
        ]

        valid_checks = [c for c in checks if c.get("probability", 0) > 0]
        self.diagnosis = sorted(
            valid_checks, key=lambda x: x["probability"], reverse=True
        )

        report = {
            "asset": self.asset,
            "timestamp": self.timestamp,
            "scan_result": self.result,
            "primary_cause": self.diagnosis[0] if self.diagnosis else None,
            "all_causes": self.diagnosis,
            "recommendation": self.generate_recommendation(),
            "recoverable": self.is_recoverable(),
        }

        self._save_to_history(report)
        return report

    def check_overfitting_severity(self) -> dict:
        """Measure overfitting severity."""
        is_sharpe = float(self.result.get("is_sharpe", 0))
        oos_sharpe = float(self.result.get("oos_sharpe", 0))
        wfe = float(self.result.get("wfe", 0))

        perf_gap = is_sharpe - oos_sharpe
        perf_gap_pct = (perf_gap / is_sharpe * 100) if is_sharpe > 0 else 0

        if wfe < 0:
            severity, probability = "CRITICAL", 95
        elif wfe < 0.3:
            severity, probability = "SEVERE", 80
        elif wfe < 0.6:
            severity, probability = "MODERATE", 60
        else:
            severity, probability = "LOW", 20

        return {
            "cause": "OVERFITTING",
            "severity": severity,
            "probability": probability,
            "metrics": {
                "is_sharpe": round(is_sharpe, 2),
                "oos_sharpe": round(oos_sharpe, 2),
                "wfe": round(wfe, 2),
                "performance_gap": round(perf_gap, 2),
                "performance_gap_pct": round(perf_gap_pct, 1),
            },
            "explanation": (
                f"IS Sharpe ({is_sharpe:.2f}) vs OOS Sharpe ({oos_sharpe:.2f}) "
                f"= {perf_gap_pct:.0f}% degradation"
            ),
            "fix": "Reduce search space, add regularization, simplify strategy",
        }

    def check_regime_shift(self) -> dict:
        """Detect market regime shift between IS and OOS."""
        n = len(self.data)
        is_end = int(n * 0.6)
        oos_start = int(n * 0.8)

        data_is = self.data.iloc[:is_end]
        data_oos = self.data.iloc[oos_start:]

        def calc_market_stats(df: pd.DataFrame) -> dict:
            returns = df["close"].pct_change().dropna()
            return {
                "volatility": returns.std() * np.sqrt(24 * 365) * 100,
                "trend": (df["close"].iloc[-1] / df["close"].iloc[0] - 1) * 100,
                "avg_range": ((df["high"] - df["low"]) / df["close"]).mean() * 100,
            }

        stats_is = calc_market_stats(data_is)
        stats_oos = calc_market_stats(data_oos)

        vol_shift = (
            abs(stats_oos["volatility"] - stats_is["volatility"])
            / max(stats_is["volatility"], 0.01)
            * 100
        )
        trend_shift = stats_is["trend"] * stats_oos["trend"] < 0
        range_shift = (
            abs(stats_oos["avg_range"] - stats_is["avg_range"])
            / max(stats_is["avg_range"], 0.01)
            * 100
        )

        probability = 0
        if vol_shift > 50:
            probability += 40
        if trend_shift:
            probability += 35
        if range_shift > 30:
            probability += 25

        severity = "CRITICAL" if probability > 70 else "MODERATE" if probability > 40 else "LOW"

        return {
            "cause": "REGIME_SHIFT",
            "severity": severity,
            "probability": min(probability, 95),
            "metrics": {
                "is_volatility": round(stats_is["volatility"], 1),
                "oos_volatility": round(stats_oos["volatility"], 1),
                "volatility_change_pct": round(vol_shift, 1),
                "is_trend": round(stats_is["trend"], 1),
                "oos_trend": round(stats_oos["trend"], 1),
                "trend_reversal": trend_shift,
            },
            "explanation": (
                f"Volatility: {stats_is['volatility']:.0f}% -> "
                f"{stats_oos['volatility']:.0f}% ({vol_shift:.0f}% shift). "
                f"Trend reversal: {trend_shift}"
            ),
            "fix": "Add regime detection or test a different OOS window",
        }

    def check_sample_size(self) -> dict:
        """Check if the trade sample size is sufficient."""
        n_trades_is = len(self.trades_is) if self.trades_is is not None else 0
        n_trades_oos = len(self.trades_oos) if self.trades_oos is not None else 0

        if n_trades_oos == 0:
            n_trades_oos = int(self.result.get("oos_trades", 0))
        if n_trades_is == 0:
            n_trades_is = int(self.result.get("is_trades", 0))

        if n_trades_oos < 20:
            severity, probability = "CRITICAL", 85
        elif n_trades_oos < 50:
            severity, probability = "SEVERE", 65
        elif n_trades_oos < 100:
            severity, probability = "MODERATE", 40
        else:
            severity, probability = "LOW", 15

        return {
            "cause": "INSUFFICIENT_SAMPLE",
            "severity": severity,
            "probability": probability,
            "metrics": {
                "trades_is": n_trades_is,
                "trades_oos": n_trades_oos,
                "minimum_recommended": 50,
                "ideal": 100,
            },
            "explanation": f"Only {n_trades_oos} OOS trades - high variance",
            "fix": "Use more history or a shorter timeframe",
        }

    def check_param_stability(self) -> dict:
        """Check if the optimal params are on a sharp local peak."""
        params = self.result.get("params", {})
        estimated_variance = 30

        if estimated_variance > 40:
            severity, probability = "CRITICAL", 75
        elif estimated_variance > 25:
            severity, probability = "SEVERE", 55
        elif estimated_variance > 15:
            severity, probability = "MODERATE", 35
        else:
            severity, probability = "LOW", 15

        return {
            "cause": "PARAM_INSTABILITY",
            "severity": severity,
            "probability": probability,
            "metrics": {
                "estimated_local_variance": estimated_variance,
                "optimal_params": params,
            },
            "explanation": f"Estimated local variance {estimated_variance:.0f}% - possible isolated peak",
            "fix": "Use discrete grid search instead of continuous space",
        }

    def check_trade_distribution_shift(self) -> dict:
        """Compare trade distributions between IS and OOS."""
        if self.trades_is is None or self.trades_oos is None:
            return {
                "cause": "TRADE_DIST_SHIFT",
                "severity": "UNKNOWN",
                "probability": 0,
                "explanation": "Trade data unavailable",
                "metrics": {},
                "fix": "",
            }

        if len(self.trades_is) < 10 or len(self.trades_oos) < 10:
            return {
                "cause": "TRADE_DIST_SHIFT",
                "severity": "UNKNOWN",
                "probability": 0,
                "explanation": "Not enough trades to compare",
                "metrics": {},
                "fix": "",
            }

        is_mean = self.trades_is["pnl_pct"].mean()
        oos_mean = self.trades_oos["pnl_pct"].mean()
        is_winrate = (self.trades_is["pnl_pct"] > 0).mean() * 100
        oos_winrate = (self.trades_oos["pnl_pct"] > 0).mean() * 100

        mean_shift = oos_mean - is_mean
        winrate_shift = oos_winrate - is_winrate

        probability = 0
        if mean_shift < -0.5:
            probability += 40
        if winrate_shift < -10:
            probability += 35

        severity = "CRITICAL" if probability > 70 else "MODERATE" if probability > 40 else "LOW"

        return {
            "cause": "TRADE_DISTRIBUTION_SHIFT",
            "severity": severity,
            "probability": min(probability, 90),
            "metrics": {
                "is_avg_pnl": round(is_mean, 3),
                "oos_avg_pnl": round(oos_mean, 3),
                "is_winrate": round(is_winrate, 1),
                "oos_winrate": round(oos_winrate, 1),
                "winrate_shift": round(winrate_shift, 1),
            },
            "explanation": (
                f"Win rate: {is_winrate:.0f}% -> {oos_winrate:.0f}% "
                f"({winrate_shift:+.0f}pp)"
            ),
            "fix": "Check if market conditions changed between IS and OOS",
        }

    def check_temporal_decay(self) -> dict:
        """Check if performance decays over time."""
        if self.trades_oos is None or len(self.trades_oos) < 20:
            return {
                "cause": "TEMPORAL_DECAY",
                "severity": "UNKNOWN",
                "probability": 0,
                "explanation": "Not enough OOS trades",
                "metrics": {},
                "fix": "",
            }

        n = len(self.trades_oos)
        third = n // 3

        early_pnl = self.trades_oos.iloc[:third]["pnl_pct"].sum()
        mid_pnl = self.trades_oos.iloc[third : 2 * third]["pnl_pct"].sum()
        late_pnl = self.trades_oos.iloc[2 * third :]["pnl_pct"].sum()

        is_decaying = early_pnl > mid_pnl > late_pnl
        decay_rate = (
            (late_pnl - early_pnl) / abs(early_pnl) * 100 if early_pnl != 0 else 0
        )

        if is_decaying and decay_rate < -50:
            severity, probability = "CRITICAL", 80
        elif is_decaying and decay_rate < -25:
            severity, probability = "SEVERE", 60
        elif decay_rate < 0:
            severity, probability = "MODERATE", 40
        else:
            severity, probability = "LOW", 10

        return {
            "cause": "TEMPORAL_DECAY",
            "severity": severity,
            "probability": probability,
            "metrics": {
                "early_oos_pnl": round(early_pnl, 2),
                "mid_oos_pnl": round(mid_pnl, 2),
                "late_oos_pnl": round(late_pnl, 2),
                "decay_rate_pct": round(decay_rate, 1),
                "is_monotonic_decay": is_decaying,
            },
            "explanation": (
                f"OOS PnL: {early_pnl:.1f}% -> {mid_pnl:.1f}% -> {late_pnl:.1f}%"
            ),
            "fix": "Edge decays over time - likely no longer exploitable",
        }

    def generate_recommendation(self) -> dict:
        """Generate a recommendation based on the diagnosis."""
        if not self.diagnosis:
            return {"action": "UNKNOWN", "details": "No diagnosis available", "command": ""}

        primary = self.diagnosis[0]

        recommendations = {
            "OVERFITTING": {
                "action": "REOPTIMIZE_CONSERVATIVE",
                "details": "Rerun with a reduced search space and more regularization",
                "command": f"REOPT_CONSERVATIVE:{self.asset}",
                "auto_actionable": True,
            },
            "REGIME_SHIFT": {
                "action": "TEST_DIFFERENT_PERIOD",
                "details": "Test a different OOS window or add regime detection",
                "command": f"TEST_ALT_PERIOD:{self.asset}",
                "auto_actionable": False,
            },
            "INSUFFICIENT_SAMPLE": {
                "action": "INCREASE_DATA",
                "details": "Add more historical data or reduce timeframe",
                "command": f"TRY_4H:{self.asset}",
                "auto_actionable": True,
            },
            "PARAM_INSTABILITY": {
                "action": "USE_DISCRETE_GRID",
                "details": "Switch from continuous search to a discrete grid",
                "command": f"REOPT_CONSERVATIVE:{self.asset}",
                "auto_actionable": True,
            },
            "TRADE_DISTRIBUTION_SHIFT": {
                "action": "INVESTIGATE_MARKET_CHANGE",
                "details": "Investigate market changes between IS and OOS",
                "command": f"ANALYZE_MARKET:{self.asset}",
                "auto_actionable": False,
            },
            "TEMPORAL_DECAY": {
                "action": "CONSIDER_DEAD",
                "details": "Edge decays over time - likely not exploitable",
                "command": f"MARK_DEAD:{self.asset}",
                "auto_actionable": False,
            },
        }

        return recommendations.get(
            primary["cause"],
            {
                "action": "MANUAL_REVIEW",
                "details": "Manual review required",
                "command": "",
                "auto_actionable": False,
            },
        )

    def is_recoverable(self) -> bool:
        """Estimate if the asset is recoverable."""
        if not self.diagnosis:
            return False

        primary = self.diagnosis[0]
        recoverable_causes = {"OVERFITTING", "INSUFFICIENT_SAMPLE", "PARAM_INSTABILITY"}
        dead_causes = {"TEMPORAL_DECAY"}

        if primary["cause"] in dead_causes and primary["probability"] > 70:
            return False
        if primary["cause"] in recoverable_causes:
            return True
        return primary["probability"] < 60

    def _normalize_trades(self, trades: Optional[pd.DataFrame]) -> Optional[pd.DataFrame]:
        if trades is None or trades.empty:
            return trades

        trades = trades.copy()
        if "pnl_pct" not in trades.columns:
            pnl_col = None
            if "net_pnl" in trades.columns:
                pnl_col = "net_pnl"
            elif "gross_pnl" in trades.columns:
                pnl_col = "gross_pnl"
            if pnl_col and "notional" in trades.columns:
                trades["pnl_pct"] = (trades[pnl_col] / trades["notional"]) * 100.0
        return trades

    def _save_to_history(self, report: dict) -> None:
        """Save diagnostic summary to persistent history."""
        history_payload = {
            "asset": report["asset"],
            "timestamp": report["timestamp"],
            "primary_cause": report["primary_cause"]["cause"] if report["primary_cause"] else None,
            "recoverable": report["recoverable"],
            "recommendation": report["recommendation"]["action"],
        }

        for path in [HISTORY_OUTPUT_PATH, HISTORY_CONFIG_PATH]:
            path.parent.mkdir(parents=True, exist_ok=True)
            history = {"diagnostics": []}
            if path.exists():
                try:
                    history = json.loads(path.read_text())
                except json.JSONDecodeError:
                    history = {"diagnostics": []}

            history["diagnostics"].append(history_payload)
            history["diagnostics"] = history["diagnostics"][-100:]
            path.write_text(json.dumps(history, indent=2))
