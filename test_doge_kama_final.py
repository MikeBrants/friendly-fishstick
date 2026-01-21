"""
Test FINAL: Compare DOGE avec/sans filtres KAMA.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import pandas as pd
from crypto_backtest.strategies.final_trigger import FinalTriggerParams, FinalTriggerStrategy
from crypto_backtest.indicators.ichimoku import IchimokuConfig
from crypto_backtest.indicators.five_in_one import FiveInOneConfig
from crypto_backtest.engine.backtest import VectorizedBacktester, BacktestConfig
from crypto_backtest.analysis.metrics import compute_metrics

print("=" * 80)
print("TEST DOGE: BASELINE vs CONSERVATIVE (KAMA FILTERS)")
print("=" * 80)

# Load data
print("\n[1/3] Chargement donnees DOGE...")
data = pd.read_parquet("data/DOGE_1H.parquet")

# Warmup
WARMUP = 200
data = data.iloc[WARMUP:].copy()
print(f"  - Donnees: {len(data)} bougies apres warmup")
print(f"  - Periode: {data.index[0]} -> {data.index[-1]}")

# Backtest config
backtest_config = BacktestConfig(
    initial_capital=10000,
    fees_bps=5,
    slippage_bps=2,
    sizing_mode="fixed",
    risk_per_trade=0.02,
)

# ============================================================================
# BASELINE (sans filtres KAMA)
# ============================================================================
print("\n[2/3] Backtest BASELINE (sans filtres KAMA)...")

# Configs from scan CSV
ichi_config_baseline = IchimokuConfig(
    tenkan=18,
    kijun=25,
    displacement=52,
)

five_config_baseline = FiveInOneConfig(
    tenkan_5=9,
    kijun_5=25,
    displacement_5=52,
    # Filtres DESACTIVES
    use_distance_filter=False,
    use_volume_filter=False,
    use_regression_cloud=False,
    use_kama_oscillator=False,
    ichi5in1_strict=False,
    use_transition_mode=False,
    use_ichimoku_filter=True,
)

baseline_params = FinalTriggerParams(
    # ATR
    sl_mult=3.0,
    tp1_mult=3.5,
    tp2_mult=7.5,
    tp3_mult=9.5,
    # Configs
    ichimoku=ichi_config_baseline,
    five_in_one=five_config_baseline,
    # MAMA/KAMA filter OFF
    use_mama_kama_filter=False,
    # Autres
    grace_bars=1,
)

print("  Filtres BASELINE:")
print(f"    - MAMA/KAMA: {baseline_params.use_mama_kama_filter}")
print(f"    - Distance: {five_config_baseline.use_distance_filter}")
print(f"    - Volume: {five_config_baseline.use_volume_filter}")
print(f"    - KAMA Osc: {five_config_baseline.use_kama_oscillator}")
print(f"    - Ichi Strict: {five_config_baseline.ichi5in1_strict}")

baseline_strategy = FinalTriggerStrategy(baseline_params)
baseline_backtester = VectorizedBacktester(backtest_config)
baseline_result = baseline_backtester.run(data, baseline_strategy)

baseline_metrics = compute_metrics(baseline_result.equity_curve, baseline_result.trades)
n_baseline_trades = len(baseline_result.trades)
print(f"\n  Resultats BASELINE:")
print(f"    - Return: {baseline_metrics['total_return']*100:.2f}%")
print(f"    - Sharpe: {baseline_metrics['sharpe_ratio']:.2f}")
print(f"    - Max DD: {baseline_metrics['max_drawdown']*100:.2f}%")
print(f"    - Win Rate: {baseline_metrics['win_rate']*100:.2f}%")
print(f"    - Profit Factor: {baseline_metrics['profit_factor']:.2f}")
print(f"    - Trades: {n_baseline_trades}")

# ============================================================================
# CONSERVATIVE (avec filtres KAMA)
# ============================================================================
print("\n[3/3] Backtest CONSERVATIVE (avec filtres KAMA)...")

# Memes configs Ichimoku
ichi_config_conservative = IchimokuConfig(
    tenkan=18,
    kijun=25,
    displacement=52,
)

# Filtres ACTIVES
five_config_conservative = FiveInOneConfig(
    tenkan_5=9,
    kijun_5=25,
    displacement_5=52,
    # Filtres ACTIVES
    use_distance_filter=True,
    use_volume_filter=True,
    use_regression_cloud=False,  # Peut etre trop lent
    use_kama_oscillator=True,
    ichi5in1_strict=True,  # Mode strict
    use_transition_mode=False,
    use_ichimoku_filter=True,
)

conservative_params = FinalTriggerParams(
    # Memes ATR
    sl_mult=3.0,
    tp1_mult=3.5,
    tp2_mult=7.5,
    tp3_mult=9.5,
    # Configs
    ichimoku=ichi_config_conservative,
    five_in_one=five_config_conservative,
    # MAMA/KAMA filter ON
    use_mama_kama_filter=True,
    # Autres
    grace_bars=1,
)

print("  Filtres CONSERVATIVE:")
print(f"    - MAMA/KAMA: {conservative_params.use_mama_kama_filter}")
print(f"    - Distance: {five_config_conservative.use_distance_filter}")
print(f"    - Volume: {five_config_conservative.use_volume_filter}")
print(f"    - KAMA Osc: {five_config_conservative.use_kama_oscillator}")
print(f"    - Ichi Strict: {five_config_conservative.ichi5in1_strict}")

conservative_strategy = FinalTriggerStrategy(conservative_params)
conservative_backtester = VectorizedBacktester(backtest_config)
conservative_result = conservative_backtester.run(data, conservative_strategy)

conservative_metrics = compute_metrics(conservative_result.equity_curve, conservative_result.trades)
n_conservative_trades = len(conservative_result.trades)
print(f"\n  Resultats CONSERVATIVE:")
print(f"    - Return: {conservative_metrics['total_return']*100:.2f}%")
print(f"    - Sharpe: {conservative_metrics['sharpe_ratio']:.2f}")
print(f"    - Max DD: {conservative_metrics['max_drawdown']*100:.2f}%")
print(f"    - Win Rate: {conservative_metrics['win_rate']*100:.2f}%")
print(f"    - Profit Factor: {conservative_metrics['profit_factor']:.2f}")
print(f"    - Trades: {n_conservative_trades}")

# ============================================================================
# COMPARAISON
# ============================================================================
print("\n" + "=" * 80)
print("COMPARAISON: BASELINE vs CONSERVATIVE")
print("=" * 80)

comparison = pd.DataFrame({
    "Metric": ["Sharpe", "Return", "Max DD", "Win Rate", "PF", "Trades"],
    "BASELINE": [
        f"{baseline_metrics['sharpe_ratio']:.2f}",
        f"{baseline_metrics['total_return']*100:.2f}%",
        f"{baseline_metrics['max_drawdown']*100:.2f}%",
        f"{baseline_metrics['win_rate']*100:.2f}%",
        f"{baseline_metrics['profit_factor']:.2f}",
        str(n_baseline_trades),
    ],
    "CONSERVATIVE": [
        f"{conservative_metrics['sharpe_ratio']:.2f}",
        f"{conservative_metrics['total_return']*100:.2f}%",
        f"{conservative_metrics['max_drawdown']*100:.2f}%",
        f"{conservative_metrics['win_rate']*100:.2f}%",
        f"{conservative_metrics['profit_factor']:.2f}",
        str(n_conservative_trades),
    ],
})

print("\n" + comparison.to_string(index=False))

# Delta
sharpe_delta = conservative_metrics["sharpe_ratio"] - baseline_metrics["sharpe_ratio"]
trades_delta = n_conservative_trades - n_baseline_trades
return_delta = (conservative_metrics["total_return"] - baseline_metrics["total_return"]) * 100

print("\n" + "-" * 80)
print("DELTA (CONSERVATIVE - BASELINE):")
print("-" * 80)

if baseline_metrics["sharpe_ratio"] != 0:
    sharpe_pct = sharpe_delta / abs(baseline_metrics["sharpe_ratio"]) * 100
else:
    sharpe_pct = 0

if n_baseline_trades > 0:
    trades_pct = trades_delta / n_baseline_trades * 100
else:
    trades_pct = 0

print(f"  - Sharpe: {sharpe_delta:+.3f} ({sharpe_pct:+.1f}%)")
print(f"  - Return: {return_delta:+.2f}%")
print(f"  - Trades: {trades_delta:+d} ({trades_pct:+.1f}%)")

print("\n" + "=" * 80)
print("VERDICT:")
print("=" * 80)

# Criteres
sharpe_improved = sharpe_delta > 0.2
sharpe_maintained = sharpe_delta > -0.3
trades_reduced = trades_delta < 0

if sharpe_improved and conservative_metrics["sharpe_ratio"] >= 1.5:
    print("  [SUCCESS] Filtres KAMA ameliorent significativement DOGE!")
    print(f"    - Sharpe: {baseline_metrics['sharpe_ratio']:.2f} -> {conservative_metrics['sharpe_ratio']:.2f}")
    print(f"    - Strategie plus selective et performante")
    print(f"    - Recommandation: RE-OPTIMISER avec filtres KAMA actives")
elif sharpe_maintained and trades_reduced and conservative_metrics["sharpe_ratio"] >= 1.0:
    print("  [PARTIAL] Filtres KAMA ameliorent la qualite des trades")
    print(f"    - Sharpe maintenu: {baseline_metrics['sharpe_ratio']:.2f} -> {conservative_metrics['sharpe_ratio']:.2f}")
    print(f"    - Trades reduits: {n_baseline_trades} -> {n_conservative_trades}")
    print(f"    - Recommandation: Tester RE-OPTIMISATION avec filtres KAMA")
else:
    print("  [FAIL] Filtres KAMA n'ameliorent pas DOGE")
    print(f"    - Sharpe: {baseline_metrics['sharpe_ratio']:.2f} -> {conservative_metrics['sharpe_ratio']:.2f}")
    if not sharpe_maintained:
        print(f"    - Degradation significative du Sharpe")
    print(f"    - Recommandation: GARDER config BASELINE ou EXCLURE l'asset")

print("\n" + "=" * 80)
print("\nNote: Ces resultats utilisent les memes params ATR/Ichi du scan initial.")
print("Pour une evaluation complete, re-optimiser les params avec filtres KAMA actives.")
print("=" * 80)
