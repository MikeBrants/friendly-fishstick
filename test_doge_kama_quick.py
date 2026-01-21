"""
Test rapide: Compare DOGE avec/sans filtres KAMA (sans re-optimiser).

Utilise les parametres actuels du scan et compare:
- BASELINE: sans filtres KAMA
- CONSERVATIVE: avec filtres KAMA
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import pandas as pd
from crypto_backtest.strategies.final_trigger import FinalTriggerParams
from crypto_backtest.engine.backtest import VectorizedBacktester, BacktestConfig
from crypto_backtest.optimization.walk_forward import validate_oos

print("=" * 80)
print("TEST RAPIDE DOGE: BASELINE vs CONSERVATIVE (KAMA FILTERS)")
print("=" * 80)

# Load data
print("\n[1/3] Chargement donnees DOGE...")
data = pd.read_parquet("data/DOGE_1H.parquet")
print(f"  - Fichier: data/DOGE_1H.parquet")

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
# BASELINE (sans filtres KAMA) - Params du scan
# ============================================================================
print("\n[2/3] Walk-Forward BASELINE (sans filtres KAMA)...")
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

baseline_wf = validate_oos(
    data=data,
    params=baseline_params,
    backtest_config=backtest_config,
)

print(f"\n  Resultats BASELINE:")
print(f"    - IS Sharpe: {baseline_wf['is_sharpe']:.2f} ({baseline_wf['is_trades']} trades)")
print(f"    - VAL Sharpe: {baseline_wf['val_sharpe']:.2f} ({baseline_wf['val_trades']} trades)")
print(f"    - OOS Sharpe: {baseline_wf['oos_sharpe']:.2f} ({baseline_wf['oos_trades']} trades)")
print(f"    - WFE: {baseline_wf['wfe']:.2f}")
print(f"    - OOS Return: {baseline_wf['oos_return']:.2f}%")
print(f"    - OOS Max DD: {baseline_wf['oos_max_dd']:.2f}%")

# ============================================================================
# CONSERVATIVE (avec filtres KAMA) - Memes params mais filtres ON
# ============================================================================
print("\n[3/3] Walk-Forward CONSERVATIVE (avec filtres KAMA)...")
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

conservative_wf = validate_oos(
    data=data,
    params=conservative_params,
    backtest_config=backtest_config,
)

print(f"\n  Resultats CONSERVATIVE:")
print(f"    - IS Sharpe: {conservative_wf['is_sharpe']:.2f} ({conservative_wf['is_trades']} trades)")
print(f"    - VAL Sharpe: {conservative_wf['val_sharpe']:.2f} ({conservative_wf['val_trades']} trades)")
print(f"    - OOS Sharpe: {conservative_wf['oos_sharpe']:.2f} ({conservative_wf['oos_trades']} trades)")
print(f"    - WFE: {conservative_wf['wfe']:.2f}")
print(f"    - OOS Return: {conservative_wf['oos_return']:.2f}%")
print(f"    - OOS Max DD: {conservative_wf['oos_max_dd']:.2f}%")

# ============================================================================
# COMPARAISON
# ============================================================================
print("\n" + "=" * 80)
print("COMPARAISON: BASELINE vs CONSERVATIVE")
print("=" * 80)

comparison = pd.DataFrame({
    "Metric": ["OOS Sharpe", "WFE", "OOS Trades", "OOS Return", "OOS Max DD", "IS Sharpe"],
    "BASELINE": [
        f"{baseline_wf['oos_sharpe']:.2f}",
        f"{baseline_wf['wfe']:.2f}",
        str(baseline_wf['oos_trades']),
        f"{baseline_wf['oos_return']:.2f}%",
        f"{baseline_wf['oos_max_dd']:.2f}%",
        f"{baseline_wf['is_sharpe']:.2f}",
    ],
    "CONSERVATIVE": [
        f"{conservative_wf['oos_sharpe']:.2f}",
        f"{conservative_wf['wfe']:.2f}",
        str(conservative_wf['oos_trades']),
        f"{conservative_wf['oos_return']:.2f}%",
        f"{conservative_wf['oos_max_dd']:.2f}%",
        f"{conservative_wf['is_sharpe']:.2f}",
    ],
})

print("\n" + comparison.to_string(index=False))

# Delta
wfe_delta = conservative_wf["wfe"] - baseline_wf["wfe"]
sharpe_delta = conservative_wf["oos_sharpe"] - baseline_wf["oos_sharpe"]
trades_delta = conservative_wf["oos_trades"] - baseline_wf["oos_trades"]

print("\n" + "-" * 80)
print("DELTA (CONSERVATIVE - BASELINE):")
print("-" * 80)

if baseline_wf["wfe"] != 0:
    wfe_pct = wfe_delta / abs(baseline_wf["wfe"]) * 100
else:
    wfe_pct = 0

if baseline_wf["oos_sharpe"] != 0:
    sharpe_pct = sharpe_delta / abs(baseline_wf["oos_sharpe"]) * 100
else:
    sharpe_pct = 0

if baseline_wf["oos_trades"] > 0:
    trades_pct = trades_delta / baseline_wf["oos_trades"] * 100
else:
    trades_pct = 0

print(f"  - WFE: {wfe_delta:+.3f} ({wfe_pct:+.1f}%)")
print(f"  - OOS Sharpe: {sharpe_delta:+.3f} ({sharpe_pct:+.1f}%)")
print(f"  - OOS Trades: {trades_delta:+d} ({trades_pct:+.1f}%)")

print("\n" + "=" * 80)
print("VERDICT:")
print("=" * 80)

# Criteres de validation
wfe_improved = wfe_delta > 0.15  # Amelioration de 15%+ du WFE
wfe_passing = conservative_wf["wfe"] >= 0.6  # Atteint le seuil
sharpe_maintained = sharpe_delta > -0.2  # Sharpe pas trop degrade

if wfe_improved and wfe_passing and sharpe_maintained:
    print("  [SUCCESS] Filtres KAMA ameliorent significativement DOGE!")
    print(f"    - WFE: {baseline_wf['wfe']:.2f} -> {conservative_wf['wfe']:.2f} (seuil: 0.6)")
    print(f"    - OOS Sharpe: {baseline_wf['oos_sharpe']:.2f} -> {conservative_wf['oos_sharpe']:.2f}")
    print(f"    - Overfit reduit, strategie plus robuste")
    print(f"    - Recommandation: RE-OPTIMISER avec filtres KAMA actives")
elif wfe_delta > 0 and sharpe_maintained:
    print("  [PARTIAL] Filtres KAMA ameliorent legerement DOGE")
    print(f"    - WFE: {baseline_wf['wfe']:.2f} -> {conservative_wf['wfe']:.2f} (seuil: 0.6)")
    if not wfe_passing:
        print(f"    - WFE encore sous le seuil (0.6), amelioration insuffisante")
    print(f"    - Recommandation: Tenter RE-OPTIMISATION avec filtres KAMA")
else:
    print("  [FAIL] Filtres KAMA n'ameliorent pas DOGE")
    print(f"    - WFE: {baseline_wf['wfe']:.2f} -> {conservative_wf['wfe']:.2f}")
    print(f"    - Asset probablement inadapte a la strategie FINAL TRIGGER")
    print(f"    - Recommandation: EXCLURE l'asset du portfolio")

print("\n" + "=" * 80)
