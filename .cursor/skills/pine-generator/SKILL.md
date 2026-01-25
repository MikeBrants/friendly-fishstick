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
- Dossier `pine/` existe (ou le créer)

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

### Étape 2: Générer le Pine Script

Créer le fichier `pine/FT_ASSET.pine` avec le template suivant :

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

### Étape 3: Script Python de Génération Automatique
```python
import pandas as pd
from glob import glob
from datetime import datetime

def generate_pine(asset: str) -> str:
    scan = pd.read_csv(sorted(glob("outputs/multiasset_scan*.csv"))[-1])
    p = scan[scan['asset'] == asset].iloc[0]
    
    template = f'''// ... (template complet ci-dessus)
float slMult = {p['sl_mult']:.2f}
float tp1Mult = {p['tp1_mult']:.2f}
float tp2Mult = {p['tp2_mult']:.2f}
float tp3Mult = {p['tp3_mult']:.2f}
int tenkanPeriod = {int(p['tenkan'])}
int kijunPeriod = {int(p['kijun'])}
int tenkan5Period = {int(p['tenkan5'])}
int kijun5Period = {int(p['kijun5'])}
int displacement = {int(p['displacement'])}
// ...
'''
    return template

# Générer et sauvegarder
asset = "BTC"
pine_code = generate_pine(asset)
with open(f"pine/FT_{asset}.pine", "w") as f:
    f.write(pine_code)
print(f"✅ Pine script généré: pine/FT_{asset}.pine")
```

### Étape 4: Checklist Validation Pine

Avant de déployer, vérifier :

- [ ] `[1]` shift sur TOUS les signaux (anti look-ahead)
- [ ] Commission 0.05% (5 bps)
- [ ] Slippage 2 ticks
- [ ] `process_orders_on_close = true`
- [ ] `warmupBars = 200`
- [ ] Multi-TP: 50/30/20 split
- [ ] Paramètres correspondent au scan validé
- [ ] TP progression respectée (TP1 < TP2 < TP3)

### Étape 5: Documenter la Génération

```markdown
# Dans comms/riley-ops.md
HHMM DONE riley-ops -> casey-quant:
Asset: [ASSET]
Action: Pine script généré
File: pine/FT_[ASSET].pine
Params: sl=[X.XX], tp1=[X.XX], tp2=[X.XX], tp3=[X.XX]
Displacement: d[XX]
Status: Ready for TradingView paper trading
```

## Output Attendu

Fichier `pine/FT_ASSET.pine` prêt à copier-coller dans TradingView.

## Troubleshooting

| Problème | Solution |
|----------|----------|
| Params manquants dans scan | Vérifier que l'asset a bien été validé |
| Erreur syntax Pine | Vérifier les types (float vs int) |
| Signaux différents de backtest | Vérifier [1] shift sur tous les indicateurs |
| Performance différente | Normal, slippage TradingView ≠ backtest |

## Escalade
- Si paramètres manquants → @Jordan vérifier le run
- Si doute sur params → @Sam revalider
- Après génération → @Casey mise à jour project-state.md
