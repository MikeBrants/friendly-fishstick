"""
Ré-optimisation DOGE avec filtres KAMA conservative.

Test comparatif:
1. Optimisation BASELINE (sans filtres KAMA)
2. Optimisation CONSERVATIVE (avec filtres KAMA)
3. Comparaison WFE, Sharpe OOS, nombre de trades
"""
import sys
from pathlib import Path
from dataclasses import dataclass, asdict

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

import pandas as pd
import numpy as np

from crypto_backtest.data.storage import OHLCVStorage
from crypto_backtest.optimization.bayesian import optimize_atr_params, optimize_ichimoku_params
from crypto_backtest.strategies.final_trigger import FinalTriggerParams
from crypto_backtest.config.scan_assets import (
    ATR_SEARCH_SPACE,
    ICHIMOKU_SEARCH_SPACE,
    BASE_PARAMS,
)

print("=" * 80)
print("TEST REOPTIMISATION DOGE - BASELINE vs CONSERVATIVE (KAMA FILTERS)")
print("=" * 80)

# Load data
storage = OHLCVStorage()
print("\n[1/6] Chargement donnees DOGE...")
data = storage.load("DOGE", exchange="binance", timeframe="1H")
print(f"  - Donnees chargees: {len(data)} bougies")
print(f"  - Periode: {data.index[0]} -> {data.index[-1]}")

# Warmup
WARMUP = 200
data = data.iloc[WARMUP:].copy()
print(f"  - Apres warmup: {len(data)} bougies")

# ============================================================================
# BASELINE (sans filtres KAMA) - Params actuels du scan
# ============================================================================
print("\n[2/6] Configuration BASELINE (sans filtres KAMA)...")
baseline_params = FinalTriggerParams(
    # ATR (from scan)
    sl_mult=3.0,
    tp1_mult=3.5,
    tp2_mult=7.5,
    tp3_mult=9.5,
    # Ichimoku (from scan)
    tenkan=18,
    kijun=25,
    tenkan_5=9,
    kijun_5=25,
    displacement=52,
    # Filtres DESACTIVES (baseline)
    use_mama_kama_filter=False,
    use_distance_filter=False,
    use_obv_filter=False,
    use_kama_filter=False,
    ichi5in1_strict=False,
    # Autres configs
    use_ichimoku_filter=True,
    use_transition_mode=False,
    grace_bars=1,
)

print("  - Filtres actifs:")
print(f"    - use_mama_kama_filter: {baseline_params.use_mama_kama_filter}")
print(f"    - use_distance_filter: {baseline_params.use_distance_filter}")
print(f"    - use_obv_filter: {baseline_params.use_obv_filter}")
print(f"    - use_kama_filter: {baseline_params.use_kama_filter}")
print(f"    - ichi5in1_strict: {baseline_params.ichi5in1_strict}")

# ============================================================================
# OPTIMISATION BASELINE - ATR
# ============================================================================
print("\n[3/6] Optimisation BASELINE - ATR (80 trials)...")
from crypto_backtest.engine.backtest import VectorizedBacktester, BacktestConfig

backtest_config = BacktestConfig(
    initial_capital=10000,
    fees_bps=5,
    slippage_bps=2,
    sizing_mode="fixed",
    risk_per_trade=0.02,
)

baseline_atr_result = optimize_atr_params(
    data=data,
    base_params=baseline_params,
    search_space=ATR_SEARCH_SPACE,
    backtest_config=backtest_config,
    n_trials=80,
    enforce_tp_progression=True,
    timeout=300,  # 5 min max
)

print(f"  - Best Sharpe: {baseline_atr_result['best_sharpe']:.2f}")
print(f"  - Best params: SL={baseline_atr_result['best_params']['sl_mult']:.2f}, "
      f"TP1={baseline_atr_result['best_params']['tp1_mult']:.2f}, "
      f"TP2={baseline_atr_result['best_params']['tp2_mult']:.2f}, "
      f"TP3={baseline_atr_result['best_params']['tp3_mult']:.2f}")

# Update baseline params
baseline_params.sl_mult = baseline_atr_result["best_params"]["sl_mult"]
baseline_params.tp1_mult = baseline_atr_result["best_params"]["tp1_mult"]
baseline_params.tp2_mult = baseline_atr_result["best_params"]["tp2_mult"]
baseline_params.tp3_mult = baseline_atr_result["best_params"]["tp3_mult"]

# ============================================================================
# OPTIMISATION BASELINE - Ichimoku
# ============================================================================
print("\n[4/6] Optimisation BASELINE - Ichimoku (80 trials)...")
baseline_ichi_result = optimize_ichimoku_params(
    data=data,
    base_params=baseline_params,
    search_space=ICHIMOKU_SEARCH_SPACE,
    backtest_config=backtest_config,
    n_trials=80,
    timeout=300,
)

print(f"  - Best Sharpe: {baseline_ichi_result['best_sharpe']:.2f}")
print(f"  - Best params: tenkan={baseline_ichi_result['best_params']['tenkan']}, "
      f"kijun={baseline_ichi_result['best_params']['kijun']}, "
      f"tenkan_5={baseline_ichi_result['best_params']['tenkan_5']}, "
      f"kijun_5={baseline_ichi_result['best_params']['kijun_5']}")

# Update baseline params
baseline_params.tenkan = baseline_ichi_result["best_params"]["tenkan"]
baseline_params.kijun = baseline_ichi_result["best_params"]["kijun"]
baseline_params.tenkan_5 = baseline_ichi_result["best_params"]["tenkan_5"]
baseline_params.kijun_5 = baseline_ichi_result["best_params"]["kijun_5"]

# ============================================================================
# WALK-FORWARD VALIDATION BASELINE
# ============================================================================
print("\n[5/6] Walk-Forward Validation BASELINE (60/20/20)...")
from crypto_backtest.optimization.walk_forward import validate_oos

baseline_wf = validate_oos(
    data=data,
    params=baseline_params,
    backtest_config=backtest_config,
)

print(f"  - IS Sharpe: {baseline_wf['is_sharpe']:.2f}, IS trades: {baseline_wf['is_trades']}")
print(f"  - VAL Sharpe: {baseline_wf['val_sharpe']:.2f}, VAL trades: {baseline_wf['val_trades']}")
print(f"  - OOS Sharpe: {baseline_wf['oos_sharpe']:.2f}, OOS trades: {baseline_wf['oos_trades']}")
print(f"  - WFE: {baseline_wf['wfe']:.2f}")

# ============================================================================
# CONSERVATIVE (avec filtres KAMA)
# ============================================================================
print("\n[6/6] Configuration CONSERVATIVE (avec filtres KAMA)...")
conservative_params = FinalTriggerParams(
    # ATR (will be optimized)
    sl_mult=3.0,
    tp1_mult=3.5,
    tp2_mult=7.5,
    tp3_mult=9.5,
    # Ichimoku (will be optimized)
    tenkan=18,
    kijun=25,
    tenkan_5=9,
    kijun_5=25,
    displacement=52,
    # Filtres ACTIVES (conservative)
    use_mama_kama_filter=True,
    use_distance_filter=True,
    use_obv_filter=True,
    use_kama_filter=True,
    ichi5in1_strict=True,
    # Autres configs
    use_ichimoku_filter=True,
    use_transition_mode=False,
    grace_bars=1,
)

print("  - Filtres actifs:")
print(f"    - use_mama_kama_filter: {conservative_params.use_mama_kama_filter}")
print(f"    - use_distance_filter: {conservative_params.use_distance_filter}")
print(f"    - use_obv_filter: {conservative_params.use_obv_filter}")
print(f"    - use_kama_filter: {conservative_params.use_kama_filter}")
print(f"    - ichi5in1_strict: {conservative_params.ichi5in1_strict}")

print("\n  Optimisation CONSERVATIVE - ATR (80 trials)...")
conservative_atr_result = optimize_atr_params(
    data=data,
    base_params=conservative_params,
    search_space=ATR_SEARCH_SPACE,
    backtest_config=backtest_config,
    n_trials=80,
    enforce_tp_progression=True,
    timeout=300,
)

print(f"  - Best Sharpe: {conservative_atr_result['best_sharpe']:.2f}")
print(f"  - Best params: SL={conservative_atr_result['best_params']['sl_mult']:.2f}, "
      f"TP1={conservative_atr_result['best_params']['tp1_mult']:.2f}, "
      f"TP2={conservative_atr_result['best_params']['tp2_mult']:.2f}, "
      f"TP3={conservative_atr_result['best_params']['tp3_mult']:.2f}")

conservative_params.sl_mult = conservative_atr_result["best_params"]["sl_mult"]
conservative_params.tp1_mult = conservative_atr_result["best_params"]["tp1_mult"]
conservative_params.tp2_mult = conservative_atr_result["best_params"]["tp2_mult"]
conservative_params.tp3_mult = conservative_atr_result["best_params"]["tp3_mult"]

print("\n  Optimisation CONSERVATIVE - Ichimoku (80 trials)...")
conservative_ichi_result = optimize_ichimoku_params(
    data=data,
    base_params=conservative_params,
    search_space=ICHIMOKU_SEARCH_SPACE,
    backtest_config=backtest_config,
    n_trials=80,
    timeout=300,
)

print(f"  - Best Sharpe: {conservative_ichi_result['best_sharpe']:.2f}")
print(f"  - Best params: tenkan={conservative_ichi_result['best_params']['tenkan']}, "
      f"kijun={conservative_ichi_result['best_params']['kijun']}, "
      f"tenkan_5={conservative_ichi_result['best_params']['tenkan_5']}, "
      f"kijun_5={conservative_ichi_result['best_params']['kijun_5']}")

conservative_params.tenkan = conservative_ichi_result["best_params"]["tenkan"]
conservative_params.kijun = conservative_ichi_result["best_params"]["kijun"]
conservative_params.tenkan_5 = conservative_ichi_result["best_params"]["tenkan_5"]
conservative_params.kijun_5 = conservative_ichi_result["best_params"]["kijun_5"]

print("\n  Walk-Forward Validation CONSERVATIVE (60/20/20)...")
conservative_wf = validate_oos(
    data=data,
    params=conservative_params,
    backtest_config=backtest_config,
)

print(f"  - IS Sharpe: {conservative_wf['is_sharpe']:.2f}, IS trades: {conservative_wf['is_trades']}")
print(f"  - VAL Sharpe: {conservative_wf['val_sharpe']:.2f}, VAL trades: {conservative_wf['val_trades']}")
print(f"  - OOS Sharpe: {conservative_wf['oos_sharpe']:.2f}, OOS trades: {conservative_wf['oos_trades']}")
print(f"  - WFE: {conservative_wf['wfe']:.2f}")

# ============================================================================
# COMPARAISON FINALE
# ============================================================================
print("\n" + "=" * 80)
print("COMPARAISON FINALE: BASELINE vs CONSERVATIVE")
print("=" * 80)

comparison = pd.DataFrame({
    "Metric": ["OOS Sharpe", "WFE", "OOS Trades", "IS Sharpe", "OOS Return", "OOS Max DD"],
    "BASELINE": [
        f"{baseline_wf['oos_sharpe']:.2f}",
        f"{baseline_wf['wfe']:.2f}",
        str(baseline_wf['oos_trades']),
        f"{baseline_wf['is_sharpe']:.2f}",
        f"{baseline_wf['oos_return']:.2f}%",
        f"{baseline_wf['oos_max_dd']:.2f}%",
    ],
    "CONSERVATIVE": [
        f"{conservative_wf['oos_sharpe']:.2f}",
        f"{conservative_wf['wfe']:.2f}",
        str(conservative_wf['oos_trades']),
        f"{conservative_wf['is_sharpe']:.2f}",
        f"{conservative_wf['oos_return']:.2f}%",
        f"{conservative_wf['oos_max_dd']:.2f}%",
    ],
})

print("\n" + comparison.to_string(index=False))

# Calculate improvements
wfe_delta = conservative_wf["wfe"] - baseline_wf["wfe"]
sharpe_delta = conservative_wf["oos_sharpe"] - baseline_wf["oos_sharpe"]
trades_delta = conservative_wf["oos_trades"] - baseline_wf["oos_trades"]

print("\n" + "-" * 80)
print("DELTA (CONSERVATIVE - BASELINE):")
print("-" * 80)
print(f"  - WFE: {wfe_delta:+.2f} ({wfe_delta/baseline_wf['wfe']*100:+.1f}%)")
print(f"  - OOS Sharpe: {sharpe_delta:+.2f} ({sharpe_delta/baseline_wf['oos_sharpe']*100:+.1f}%)")
print(f"  - OOS Trades: {trades_delta:+d} ({trades_delta/baseline_wf['oos_trades']*100:+.1f}%)")

print("\n" + "=" * 80)
print("VERDICT:")
print("=" * 80)

if wfe_delta > 0.1 and conservative_wf["wfe"] >= 0.6:
    print("  [SUCCESS] Filtres KAMA ameliorent significativement le WFE!")
    print(f"  - WFE passe de {baseline_wf['wfe']:.2f} a {conservative_wf['wfe']:.2f}")
    print(f"  - Overfit reduit, strategie plus robuste")
elif wfe_delta > 0:
    print("  [PARTIAL] Filtres KAMA ameliorent legerement le WFE")
    print(f"  - WFE passe de {baseline_wf['wfe']:.2f} a {conservative_wf['wfe']:.2f}")
    print(f"  - Amelioration insuffisante pour valider l'asset")
else:
    print("  [FAIL] Filtres KAMA n'ameliorent pas le WFE")
    print(f"  - WFE reste a {conservative_wf['wfe']:.2f} (seuil: 0.6)")
    print(f"  - Asset probablement inadapte a la strategie")

print("\n" + "=" * 80)
