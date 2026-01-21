"""Test diagnostic DOGE et recommandations filtres KAMA."""
import pandas as pd
from crypto_backtest.analysis.diagnostics import diagnose_asset

# Créer Series DOGE à partir du scan CSV
scan_data = {
    "asset": "DOGE",
    "status": "FAIL",
    "oos_sharpe": 1.0050126608196153,
    "is_sharpe": 2.319240876184654,
    "wfe": 0.43333690395839586,
    "oos_max_dd": -2.569215316465534,
    "oos_trades": 90,
    "oos_return": 1.6342890694329704,
    "mc_p": 0.076,
}

scan_row = pd.Series(scan_data)

# Pas de guards pour l'instant
guards_row = None

# Run diagnostics
diag = diagnose_asset("DOGE", scan_row, guards_row)

print("=" * 80)
print(f"DIAGNOSTIC COMPLET: {diag.asset}")
print("=" * 80)
print(f"\nStatut Global: {diag.overall_status}\n")

print("-" * 80)
print("CHECKS DETAILLES:")
print("-" * 80)
for check in diag.checks:
    status_symbols = {"PASS": "[OK]", "WARN": "[WARN]", "FAIL": "[FAIL]"}
    print(f"\n{status_symbols[check.status]} {check.name}")
    print(f"   Valeur: {check.value}")
    print(f"   Seuil: {check.threshold}")
    print(f"   Status: {check.status}")
    print(f"   Explication: {check.explanation}")
    print(f"   Recommandation: {check.recommendation}")

print("\n" + "=" * 80)
print("PARAMETRES RECOMMANDES:")
print("=" * 80)
settings = diag.recommended_settings
for key, value in settings.items():
    print(f"  {key}: {value}")

print("\n" + "=" * 80)
print("FILTRES KAMA RECOMMANDES:")
print("=" * 80)

# Verifier si les filtres KAMA sont recommandes
sharpe_check = next(c for c in diag.checks if c.name == "Sharpe Ratio OOS")
wfe_check = next(c for c in diag.checks if c.name == "Walk-Forward Efficiency")

if sharpe_check.status in ["WARN", "FAIL"] or wfe_check.status in ["WARN", "FAIL"]:
    print("  [OK] FILTRES KAMA RECOMMANDES")
    print("\n  Configuration Conservative a appliquer:")
    print("  - use_mama_kama_filter: True")
    print("  - use_distance_filter: True")
    print("  - use_obv_filter: True")
    print("  - use_kama_filter: True")
    print("  - ichi5in1_strict: True")
    print("\n  Benefices attendus:")
    print("  - [UP] WFE (reduction overfit)")
    print("  - [UP] Qualite des trades")
    print("  - [DOWN] Nombre de trades (plus selectif)")
else:
    print("  [WARN] Filtres KAMA non necessaires")
