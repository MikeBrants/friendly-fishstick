"""
Conservative reoptimization mode for failed assets.
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Callable

import optuna
import pandas as pd

CONSERVATIVE_ATR_SPACE = {
    "sl_mult": [3.0, 3.5, 4.0, 4.5, 5.0],
    "tp1_mult": [3.0, 3.5, 4.0, 4.5, 5.0],
    "tp2_mult": [3.0, 4.0, 5.0, 6.0],
    "tp3_mult": [6.0, 7.0, 8.0, 9.0],
}

CONSERVATIVE_ICHI_SPACE = {
    "tenkan": [9, 13, 18],
    "kijun": [26, 34, 42],
    "tenkan_5": [9, 13, 18],
    "kijun_5": [21, 26, 34],
    "displacement": [52],
}

CONSERVATIVE_SPLIT_RATIO = (0.70, 0.15, 0.15)


class ConservativeReoptimizer:
    """Reoptimization with anti-overfitting constraints."""

    CONSERVATIVE_ATR_SPACE = CONSERVATIVE_ATR_SPACE
    CONSERVATIVE_ICHI_SPACE = CONSERVATIVE_ICHI_SPACE
    MIN_TRIALS_ATR = 200
    MIN_TRIALS_ICHI = 200
    SPLIT_RATIO = CONSERVATIVE_SPLIT_RATIO
    MIN_TRADES_OOS = 80

    def __init__(self, asset: str, data: pd.DataFrame, backtest_func: Callable):
        self.asset = asset
        self.data = data
        self.backtest_func = backtest_func
        self.results: dict = {}
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M")

    def run_conservative_optimization(self) -> dict:
        """Run full conservative reoptimization."""
        print(f"[{self.asset}] Starting CONSERVATIVE reoptimization...")

        n = len(self.data)
        is_end = int(n * self.SPLIT_RATIO[0])
        val_end = int(n * (self.SPLIT_RATIO[0] + self.SPLIT_RATIO[1]))

        data_is = self.data.iloc[:is_end]
        data_val = self.data.iloc[is_end:val_end]
        data_oos = self.data.iloc[val_end:]

        print(
            f"[{self.asset}] Data split: IS={len(data_is)}, "
            f"VAL={len(data_val)}, OOS={len(data_oos)} bars"
        )

        print(
            f"[{self.asset}] Phase 1: ATR optimization "
            f"({self.MIN_TRIALS_ATR} trials, discrete grid)..."
        )
        atr_params = self._optimize_atr_conservative(data_is)

        print(
            f"[{self.asset}] Phase 2: Ichi optimization "
            f"({self.MIN_TRIALS_ICHI} trials, discrete grid)..."
        )
        ichi_params = self._optimize_ichi_conservative(data_is, atr_params)

        final_params = {**atr_params, **ichi_params}

        print(f"[{self.asset}] Phase 3: Walk-forward validation...")
        wf_result = self._walk_forward_validation(data_is, data_val, data_oos, final_params)

        success = (
            wf_result["wfe"] > 0.6
            and wf_result["oos_sharpe"] > 1.0
            and wf_result["oos_trades"] >= self.MIN_TRADES_OOS
        )

        status = "SUCCESS" if success else "FAIL_AGAIN"

        result = {
            "asset": self.asset,
            "timestamp": self.timestamp,
            "mode": "CONSERVATIVE",
            "status": status,
            "params": final_params,
            "is_sharpe": wf_result["is_sharpe"],
            "oos_sharpe": wf_result["oos_sharpe"],
            "oos_trades": wf_result["oos_trades"],
            "wfe": wf_result["wfe"],
            "split_ratio": self.SPLIT_RATIO,
            "constraints": {
                "min_trades_oos": self.MIN_TRADES_OOS,
                "wfe_threshold": 0.6,
                "sharpe_threshold": 1.0,
            },
        }

        self._save_result(result)

        print(
            f"[{self.asset}] Conservative reopt complete: "
            f"OOS Sharpe={wf_result['oos_sharpe']:.2f}, "
            f"WFE={wf_result['wfe']:.2f}, Status={status}"
        )

        return result

    def _optimize_atr_conservative(self, data: pd.DataFrame) -> dict:
        """Optimize ATR using discrete grid."""

        def objective(trial: optuna.Trial) -> float:
            params = {
                "sl_mult": trial.suggest_categorical(
                    "sl_mult", self.CONSERVATIVE_ATR_SPACE["sl_mult"]
                ),
                "tp1_mult": trial.suggest_categorical(
                    "tp1_mult", self.CONSERVATIVE_ATR_SPACE["tp1_mult"]
                ),
                "tp2_mult": trial.suggest_categorical(
                    "tp2_mult", self.CONSERVATIVE_ATR_SPACE["tp2_mult"]
                ),
                "tp3_mult": trial.suggest_categorical(
                    "tp3_mult", self.CONSERVATIVE_ATR_SPACE["tp3_mult"]
                ),
            }

            result = self.backtest_func(data, params)
            return float(result.get("sharpe", -999))

        study = optuna.create_study(direction="maximize")
        study.optimize(objective, n_trials=self.MIN_TRIALS_ATR, show_progress_bar=False)

        return study.best_params

    def _optimize_ichi_conservative(self, data: pd.DataFrame, atr_params: dict) -> dict:
        """Optimize Ichimoku using discrete grid."""

        def objective(trial: optuna.Trial) -> float:
            ichi_params = {
                "tenkan": trial.suggest_categorical(
                    "tenkan", self.CONSERVATIVE_ICHI_SPACE["tenkan"]
                ),
                "kijun": trial.suggest_categorical(
                    "kijun", self.CONSERVATIVE_ICHI_SPACE["kijun"]
                ),
                "tenkan_5": trial.suggest_categorical(
                    "tenkan_5", self.CONSERVATIVE_ICHI_SPACE["tenkan_5"]
                ),
                "kijun_5": trial.suggest_categorical(
                    "kijun_5", self.CONSERVATIVE_ICHI_SPACE["kijun_5"]
                ),
                "displacement": 52,
            }

            if ichi_params["tenkan"] >= ichi_params["kijun"]:
                return -999
            if ichi_params["tenkan_5"] >= ichi_params["kijun_5"]:
                return -999

            params = {**atr_params, **ichi_params}
            result = self.backtest_func(data, params)
            return float(result.get("sharpe", -999))

        study = optuna.create_study(direction="maximize")
        study.optimize(objective, n_trials=self.MIN_TRIALS_ICHI, show_progress_bar=False)

        best = study.best_params
        best["displacement"] = 52
        return best

    def _walk_forward_validation(
        self,
        data_is: pd.DataFrame,
        data_val: pd.DataFrame,
        data_oos: pd.DataFrame,
        params: dict,
    ) -> dict:
        """Walk-forward validation."""
        result_is = self.backtest_func(data_is, params)
        result_oos = self.backtest_func(data_oos, params)

        is_sharpe = float(result_is.get("sharpe", 0))
        oos_sharpe = float(result_oos.get("sharpe", 0))
        wfe = oos_sharpe / is_sharpe if is_sharpe > 0 else 0

        return {
            "is_sharpe": is_sharpe,
            "oos_sharpe": oos_sharpe,
            "oos_trades": int(result_oos.get("trades", 0)),
            "wfe": wfe,
        }

    def _save_result(self, result: dict) -> None:
        """Persist reoptimization results."""
        output_dir = Path("outputs")
        output_dir.mkdir(exist_ok=True)

        csv_file = output_dir / f"{self.asset}_reopt_conservative_{self.timestamp}.csv"
        pd.DataFrame([result]).to_csv(csv_file, index=False)

        json_file = output_dir / f"{self.asset}_reopt_conservative_{self.timestamp}.json"
        with open(json_file, "w") as handle:
            json.dump(result, handle, indent=2, default=str)

        history_file = output_dir / "reoptimization_history.json"
        if history_file.exists():
            with open(history_file, "r") as handle:
                history = json.load(handle)
        else:
            history = {"reoptimizations": []}

        history["reoptimizations"].append(
            {
                "asset": result["asset"],
                "timestamp": result["timestamp"],
                "mode": result["mode"],
                "status": result["status"],
                "oos_sharpe": result["oos_sharpe"],
                "wfe": result["wfe"],
            }
        )

        with open(history_file, "w") as handle:
            json.dump(history, handle, indent=2)

        print(f"[{self.asset}] Results saved to {csv_file}")
