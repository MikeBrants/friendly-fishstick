---
name: pine-generator
description: Génère un script Pine Script v6 pour TradingView à partir des paramètres validés (7/7 PASS). Utiliser après validation Sam, quand un asset passe en PROD, ou pour préparer le paper trading. Exporte les params figés vers un fichier .pine exécutable.
---

# Pine Script Generator

## Quand Utiliser
- Après validation 7/7 PASS par Sam
- Quand un asset passe officiellement en PROD
- Pour préparer le paper trading sur TradingView
- Riley doit générer le script déployable

## Prérequis
- Asset validé 7/7 PASS par Sam
- Paramètres figés dans `outputs/multiasset_scan*.csv`
- Asset listé dans `status/project-state.md` comme PROD

## Instructions

### Étape 1: Récupérer les Paramètres Validés
```python
import pandas as pd
from glob import glob

# Charger derniers résultats
scan = pd.read_csv(sorted(glob("outputs/multiasset_scan*.csv"))[-1])

# Filtrer l'asset validé
asset = "BTC"  # Remplacer par l'asset cible
params = scan[scan['asset'] == asset].iloc[0]

print(f"""
Asset: {asset}
SL mult: {params['sl_mult']:.2f}
TP1 mult: {params['tp1_mult']:.2f}
TP2 mult: {params['tp2_mult']:.2f}
TP3 mult: {params['tp3_mult']:.2f}
Tenkan: {int(params['tenkan'])}
Kijun: {int(params['kijun'])}
Tenkan5: {int(params['tenkan5'])}
Kijun5: {int(params['kijun5'])}
Displacement: {int(params['displacement'])}
""")
```

### Étape 2: Vérifier TP Progression
```python
tp1, tp2, tp3 = params['tp1_mult'], params['tp2_mult'], params['tp3_mult']
gap1, gap2 = tp2 - tp1, tp3 - tp2

assert tp1 < tp2 < tp3, f"TP non progressif: {tp1} < {tp2} < {tp3}"
assert gap1 >= 0.5, f"Gap TP1-TP2 insuffisant: {gap1:.2f}"
assert gap2 >= 0.5, f"Gap TP2-TP3 insuffisant: {gap2:.2f}"
print("✅ TP progression valide")
```

### Étape 3: Générer le Pine Script

Créer le fichier `FT_ASSET.pine` avec le template:

```pine
//@version=6
strategy("FT_[ASSET]", overlay=true,
    initial_capital=10000,
    default_qty_type=strategy.percent_of_equity,
    default_qty_value=100,
    commission_type=strategy.commission.percent,
    commission_value=0.05,
    slippage=2,
    process_orders_on_close=true,
    calc_on_every_tick=false)

// ===============================================================
// PARAMS FROZEN [ASSET] - DO NOT MODIFY
// Generated: [DATE]
// Validated: 7/7 PASS by Sam
// Source: outputs/multiasset_scan_YYYYMMDD_HHMMSS.csv
// ===============================================================
float slMult = [SL_VALUE]
float tp1Mult = [TP1_VALUE]
float tp2Mult = [TP2_VALUE]
float tp3Mult = [TP3_VALUE]
int tenkanPeriod = [TENKAN]
int kijunPeriod = [KIJUN]
int tenkan5Period = [TENKAN5]
int kijun5Period = [KIJUN5]
int displacement = [DISP]
float trailStart = 9.0
float trailStep = 7.0
int warmupBars = 200

// ===============================================================
// ATR & LEVELS
// ===============================================================
atr14 = ta.atr(14)
entryPrice = strategy.position_avg_price
slLevel = entryPrice - (atr14 * slMult)
tp1Level = entryPrice + (atr14 * tp1Mult)
tp2Level = entryPrice + (atr14 * tp2Mult)
tp3Level = entryPrice + (atr14 * tp3Mult)

// ===============================================================
// ICHIMOKU STANDARD
// ===============================================================
tenkan = (ta.highest(high, tenkanPeriod) + ta.lowest(low, tenkanPeriod)) / 2
kijun = (ta.highest(high, kijunPeriod) + ta.lowest(low, kijunPeriod)) / 2
senkouA = (tenkan + kijun) / 2
senkouB = (ta.highest(high, 52) + ta.lowest(low, 52)) / 2

// ===============================================================
// ICHIMOKU 5-IN-1
// ===============================================================
tenkan5 = (ta.highest(high, tenkan5Period) + ta.lowest(low, tenkan5Period)) / 2
kijun5 = (ta.highest(high, kijun5Period) + ta.lowest(low, kijun5Period)) / 2

// ===============================================================
// SIGNAL LOGIC (ANTI LOOK-AHEAD: use [1] shift)
// ===============================================================
puzzleLong = ta.crossover(tenkan[1], kijun[1]) and close > senkouA[displacement]
fiveInOneLong = tenkan5[1] > kijun5[1]
finalSignal = puzzleLong and fiveInOneLong and bar_index > warmupBars

// ===============================================================
// ENTRIES & EXITS
// ===============================================================
if finalSignal and strategy.position_size == 0
    strategy.entry("Long", strategy.long)

// Multi-TP: 50% / 30% / 20%
strategy.exit("TP1", "Long", qty_percent=50, limit=tp1Level, stop=slLevel)
strategy.exit("TP2", "Long", qty_percent=60, limit=tp2Level, stop=entryPrice)  // BE after TP1
strategy.exit("TP3", "Long", qty_percent=100, limit=tp3Level, stop=tp1Level)

// ===============================================================
// PLOTS
// ===============================================================
plot(slLevel, "SL", color=color.red, style=plot.style_linebr)
plot(tp1Level, "TP1", color=color.green, style=plot.style_linebr)
plot(tp2Level, "TP2", color=color.lime, style=plot.style_linebr)
plot(tp3Level, "TP3", color=color.teal, style=plot.style_linebr)

// ===============================================================
// ALERTS (Telegram-ready JSON)
// ===============================================================
alertcondition(finalSignal, "FT_[ASSET]_ENTRY", 
    '{"asset":"[ASSET]","action":"LONG_ENTRY","price":{{close}},"sl":{{plot_0}},"tp1":{{plot_1}}}')
```

### Étape 4: Script Python de Génération
```python
from datetime import datetime

def generate_pine(asset: str, params: dict) -> str:
    """Génère le script Pine complet pour un asset."""
    
    template = f'''//@version=6
strategy("FT_{asset}", overlay=true,
    initial_capital=10000,
    default_qty_type=strategy.percent_of_equity,
    default_qty_value=100,
    commission_type=strategy.commission.percent,
    commission_value=0.05,
    slippage=2,
    process_orders_on_close=true,
    calc_on_every_tick=false)

// PARAMS FROZEN {asset} - DO NOT MODIFY
// Generated: {datetime.now().strftime("%Y-%m-%d %H:%M")}
float slMult = {params['sl_mult']:.2f}
float tp1Mult = {params['tp1_mult']:.2f}
float tp2Mult = {params['tp2_mult']:.2f}
float tp3Mult = {params['tp3_mult']:.2f}
int tenkanPeriod = {int(params['tenkan'])}
int kijunPeriod = {int(params['kijun'])}
int tenkan5Period = {int(params['tenkan5'])}
int kijun5Period = {int(params['kijun5'])}
int displacement = {int(params['displacement'])}
// ... (rest of template)
'''
    return template

# Utilisation
pine_code = generate_pine(asset, params.to_dict())
with open(f"FT_{asset}.pine", "w") as f:
    f.write(pine_code)
print(f"✅ Script généré: FT_{asset}.pine")
```

### Étape 5: Checklist Validation Pine

Avant de déployer, vérifier:

- [ ] `[1]` shift sur TOUS les signaux (anti look-ahead)
- [ ] Commission 0.05% (5 bps)
- [ ] Slippage 2 ticks
- [ ] `process_orders_on_close = true`
- [ ] `warmupBars = 200`
- [ ] Multi-TP: 50/30/20 split
- [ ] Paramètres correspondent au scan validé
- [ ] TP progression respectée (TP1 < TP2 < TP3, gaps ≥ 0.5)
- [ ] Asset 7/7 PASS confirmé par Sam

### Étape 6: Documenter la Génération

```markdown
HHMM DONE riley-ops -> casey-quant:
Asset: [ASSET]
Action: Pine script généré ✅
File: FT_[ASSET].pine
Source: outputs/multiasset_scan_YYYYMMDD_HHMMSS.csv
Params:
  - SL: [X.XX]
  - TP1/TP2/TP3: [X.XX]/[X.XX]/[X.XX]
  - Tenkan/Kijun: [XX]/[XX]
  - Displacement: d[XX]
Validation: 7/7 PASS by Sam
Status: Ready for TradingView paper trading
```

## Assets PROD Actuels (Référence)

| Asset | Disp | Mode | OOS Sharpe | WFE |
|-------|------|------|------------|-----|
| BTC | 52 | baseline | 2.14 | >0.6 |
| ETH | 52 | medium_distance_volume | 2.09 | 0.82 |
| JOE | 26 | baseline | 5.03 | 1.44 |
| OSMO | 65 | baseline | 3.18 | 0.77 |
| MINA | 78 | baseline | 1.76 | 0.61 |

## Output Attendu

Fichier `FT_ASSET.pine` prêt à copier-coller dans TradingView.

## Troubleshooting

| Problème | Solution |
|----------|----------|
| Params manquants dans scan | Vérifier que l'asset a 7/7 PASS |
| Erreur syntax Pine | Vérifier les types (float vs int) |
| Signaux différents de backtest | Vérifier `[1]` shift sur tous les indicateurs |
| Performance différente | Normal, slippage TradingView ≠ backtest |

## Escalade
- Si params manquants → @Jordan vérifier le run
- Si doute sur params → @Sam revalider guards
- Après génération → @Casey mise à jour project-state.md
