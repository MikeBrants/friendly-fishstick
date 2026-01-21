"""
Test ULTRA simple: Compare DOGE avec/sans filtres KAMA (backtest simple).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import pandas as pd
from crypto_backtest.strategies.final_trigger import FinalTriggerParams, FinalTriggerStrategy
from crypto_backtest.engine.backtest import VectorizedBacktester, BacktestConfig

print("=" * 80)
print("TEST SIMPLE DOGE: BASELINE vs CONSERVATIVE (KAMA FILTERS)")
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
baseline_params = FinalTriggerParams(
    # ATR (from scan CSV)
    sl_mult=3.0,
    tp1_mult=3.5,
    tp2_mult=7.5,
    tp3_mult=9.5,
    # Ichimoku (from scan CSV)
    tenkan=18,
    kijun=25,
    tenkan_5=9,
    kijun_5=25,
    displacement=52,
    # Filtres DESACTIVES
    use_mama_kama_filter=False,
    use_distance_filter=False,
    use_obv_filter=False,
    use_kama_filter=False,
    ichi5in1_strict=False,
    # Autres
    use_ichimoku_filter=True,
    use_transition_mode=False,
    grace_bars=1,
)

print("  Filtres:")
print(f"    - MAMA/KAMA: {baseline_params.use_mama_kama_filter}")
print(f"    - Distance: {baseline_params.use_distance_filter}")
print(f"    - OBV: {baseline_params.use_obv_filter}")
print(f"    - KAMA Osc: {baseline_params.use_kama_filter}")
print(f"    - Ichi Strict: {baseline_params.ichi5in1_strict}")

baseline_strategy = FinalTriggerStrategy(baseline_params)
baseline_backtester = VectorizedBacktester(backtest_config)
baseline_result = baseline_backtester.run(data, baseline_strategy)

baseline_metrics = baseline_result.metrics
print(f"\n  Resultats BASELINE:")
print(f"    - Return: {baseline_metrics['return_pct']:.2f}%")
print(f"    - Sharpe: {baseline_metrics['sharpe_ratio']:.2f}")
print(f"    - Max DD: {baseline_metrics['max_drawdown_pct']:.2f}%")
print(f"    - Win Rate: {baseline_metrics['win_rate']:.2f}%")
print(f"    - Profit Factor: {baseline_metrics['profit_factor']:.2f}")
print(f"    - Trades: {baseline_metrics['n_trades']}")

# ============================================================================
# CONSERVATIVE (avec filtres KAMA)
# ============================================================================
print("\n[3/3] Backtest CONSERVATIVE (avec filtres KAMA)...")
conservative_params = FinalTriggerParams(
    # ATR (memes params)
    sl_mult=3.0,
    tp1_mult=3.5,
    tp2_mult=7.5,
    tp3_mult=9.5,
    # Ichimoku (memes params)
    tenkan=18,
    kijun=25,
    tenkan_5=9,
    kijun_5=25,
    displacement=52,
    # Filtres ACTIVES
    use_mama_kama_filter=True,
    use_distance_filter=True,
    use_obv_filter=True,
    use_kama_filter=True,
    ichi5in1_strict=True,
    # Autres
    use_ichimoku_filter=True,
    use_transition_mode=False,
    grace_bars=1,
)

print("  Filtres:")
print(f"    - MAMA/KAMA: {conservative_params.use_mama_kama_filter}")
print(f"    - Distance: {conservative_params.use_distance_filter}")
print(f"    - OBV: {conservative_params.use_obv_filter}")
print(f"    - KAMA Osc: {conservative_params.use_kama_filter}")
print(f"    - Ichi Strict: {conservative_params.ichi5in1_strict}")

conservative_strategy = FinalTriggerStrategy(conservative_params)
conservative_backtester = VectorizedBacktester(backtest_config)
conservative_result = conservative_backtester.run(data, conservative_strategy)

conservative_metrics = conservative_result.metrics
print(f"\n  Resultats CONSERVATIVE:")
print(f"    - Return: {conservative_metrics['return_pct']:.2f}%")
print(f"    - Sharpe: {conservative_metrics['sharpe_ratio']:.2f}")
print(f"    - Max DD: {conservative_metrics['max_drawdown_pct']:.2f}%")
print(f"    - Win Rate: {conservative_metrics['win_rate']:.2f}%")
print(f"    - Profit Factor: {conservative_metrics['profit_factor']:.2f}")
print(f"    - Trades: {conservative_metrics['n_trades']}")

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
        f"{baseline_metrics['return_pct']:.2f}%",
        f"{baseline_metrics['max_drawdown_pct']:.2f}%",
        f"{baseline_metrics['win_rate']:.2f}%",
        f"{baseline_metrics['profit_factor']:.2f}",
        str(baseline_metrics['n_trades']),
    ],
    "CONSERVATIVE": [
        f"{conservative_metrics['sharpe_ratio']:.2f}",
        f"{conservative_metrics['return_pct']:.2f}%",
        f"{conservative_metrics['max_drawdown_pct']:.2f}%",
        f"{conservative_metrics['win_rate']:.2f}%",
        f"{conservative_metrics['profit_factor']:.2f}",
        str(conservative_metrics['n_trades']),
    ],
})

print("\n" + comparison.to_string(index=False))

# Delta
sharpe_delta = conservative_metrics["sharpe_ratio"] - baseline_metrics["sharpe_ratio"]
trades_delta = conservative_metrics["n_trades"] - baseline_metrics["n_trades"]
return_delta = conservative_metrics["return_pct"] - baseline_metrics["return_pct"]

print("\n" + "-" * 80)
print("DELTA (CONSERVATIVE - BASELINE):")
print("-" * 80)

if baseline_metrics["sharpe_ratio"] != 0:
    sharpe_pct = sharpe_delta / abs(baseline_metrics["sharpe_ratio"]) * 100
else:
    sharpe_pct = 0

if baseline_metrics["n_trades"] > 0:
    trades_pct = trades_delta / baseline_metrics["n_trades"] * 100
else:
    trades_pct = 0

print(f"  - Sharpe: {sharpe_delta:+.3f} ({sharpe_pct:+.1f}%)")
print(f"  - Return: {return_delta:+.2f}%")
print(f"  - Trades: {trades_delta:+d} ({trades_pct:+.1f}%)")

print("\n" + "=" * 80)
print("VERDICT:")
print("=" * 80)

# Criteres
sharpe_improved = sharpe_delta > 0.2  # +20% Sharpe
sharpe_maintained = sharpe_delta > -0.3  # Sharpe pas trop degrade
trades_reduced = trades_delta < 0  # Moins de trades (plus selectif)

if sharpe_improved and conservative_metrics["sharpe_ratio"] >= 1.5:
    print("  [SUCCESS] Filtres KAMA ameliorent significativement DOGE!")
    print(f"    - Sharpe: {baseline_metrics['sharpe_ratio']:.2f} -> {conservative_metrics['sharpe_ratio']:.2f}")
    print(f"    - Strategie plus selective et performante")
    print(f"    - Recommandation: RE-OPTIMISER avec filtres KAMA actives")
elif sharpe_maintained and trades_reduced and conservative_metrics["sharpe_ratio"] >= 1.0:
    print("  [PARTIAL] Filtres KAMA ameliorent la qualite des trades")
    print(f"    - Sharpe maintenu: {baseline_metrics['sharpe_ratio']:.2f} -> {conservative_metrics['sharpe_ratio']:.2f}")
    print(f"    - Trades reduits: {baseline_metrics['n_trades']} -> {conservative_metrics['n_trades']}")
    print(f"    - Recommandation: Tester RE-OPTIMISATION avec filtres KAMA")
else:
    print("  [FAIL] Filtres KAMA n'ameliorent pas DOGE")
    print(f"    - Sharpe: {baseline_metrics['sharpe_ratio']:.2f} -> {conservative_metrics['sharpe_ratio']:.2f}")
    if not sharpe_maintained:
        print(f"    - Degradation significative du Sharpe")
    print(f"    - Recommandation: GARDER config BASELINE ou EXCLURE l'asset")

print("\n" + "=" * 80)
