#!/usr/bin/env python3
"""Export Pine Script configurations for PROD assets.

This script exports frozen parameters for all validated assets
into JSON format suitable for Pine Script deployment.

Usage:
    python scripts/export_pine_config.py --all-prod
    python scripts/export_pine_config.py --assets ETH SHIB DOT
"""

import argparse
import json
import sys
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent.parent

# PROD assets with their validated parameters
# Source: project-state.md (26 Jan 2026)
PROD_ASSET_PARAMS = {
    "SHIB": {
        "sl_mult": 2.5,
        "tp1_mult": 3.0,
        "tp2_mult": 5.5,
        "tp3_mult": 7.0,
        "tenkan": 9,
        "kijun": 26,
        "displacement": 26,
        "filter_mode": "baseline",
        "oos_sharpe": 5.67,
        "wfe": 2.27,
        "wfe_tier": "extreme",
    },
    "DOT": {
        "sl_mult": 3.0,
        "tp1_mult": 4.0,
        "tp2_mult": 6.0,
        "tp3_mult": 8.0,
        "tenkan": 10,
        "kijun": 30,
        "displacement": 26,
        "filter_mode": "baseline",
        "oos_sharpe": 4.82,
        "wfe": 1.74,
        "wfe_tier": "extreme",
    },
    "TIA": {
        "sl_mult": 2.75,
        "tp1_mult": 3.5,
        "tp2_mult": 5.0,
        "tp3_mult": 6.5,
        "tenkan": 9,
        "kijun": 26,
        "displacement": 26,
        "filter_mode": "baseline",
        "oos_sharpe": 5.16,
        "wfe": 1.36,
        "wfe_tier": "moderate",
    },
    "NEAR": {
        "sl_mult": 3.0,
        "tp1_mult": 3.5,
        "tp2_mult": 5.5,
        "tp3_mult": 7.0,
        "tenkan": 9,
        "kijun": 26,
        "displacement": 26,
        "filter_mode": "baseline",
        "oos_sharpe": 4.26,
        "wfe": 1.69,
        "wfe_tier": "normal",
    },
    "DOGE": {
        "sl_mult": 2.5,
        "tp1_mult": 3.0,
        "tp2_mult": 4.5,
        "tp3_mult": 6.0,
        "tenkan": 9,
        "kijun": 26,
        "displacement": 26,
        "filter_mode": "baseline",
        "oos_sharpe": 3.88,
        "wfe": 1.55,
        "wfe_tier": "normal",
    },
    "ANKR": {
        "sl_mult": 3.5,
        "tp1_mult": 4.0,
        "tp2_mult": 6.0,
        "tp3_mult": 8.0,
        "tenkan": 9,
        "kijun": 26,
        "displacement": 26,
        "filter_mode": "baseline",
        "oos_sharpe": 3.48,
        "wfe": 0.86,
        "wfe_tier": "normal",
    },
    "ETH": {
        "sl_mult": 3.0,
        "tp1_mult": 5.0,
        "tp2_mult": 6.0,
        "tp3_mult": 7.5,
        "tenkan": 12,
        "kijun": 36,
        "displacement": 26,
        "filter_mode": "baseline",
        "oos_sharpe": 3.22,
        "wfe": 1.22,
        "wfe_tier": "moderate",
    },
    "JOE": {
        "sl_mult": 3.0,
        "tp1_mult": 3.5,
        "tp2_mult": 5.0,
        "tp3_mult": 6.5,
        "tenkan": 9,
        "kijun": 26,
        "displacement": 26,
        "filter_mode": "baseline",
        "oos_sharpe": 3.16,
        "wfe": 0.73,
        "wfe_tier": "normal",
    },
    "YGG": {
        "sl_mult": 4.25,
        "tp1_mult": 2.75,
        "tp2_mult": 7.5,
        "tp3_mult": 9.5,
        "tenkan": 10,
        "kijun": 20,
        "displacement": 26,
        "filter_mode": "baseline",
        "oos_sharpe": 3.11,
        "wfe": 0.78,
        "wfe_tier": "normal",
    },
    "MINA": {
        "sl_mult": 4.25,
        "tp1_mult": 3.0,
        "tp2_mult": 7.5,
        "tp3_mult": 9.0,
        "tenkan": 9,
        "kijun": 26,
        "displacement": 26,
        "filter_mode": "baseline",
        "oos_sharpe": 2.58,
        "wfe": 1.13,
        "wfe_tier": "moderate",
    },
    "CAKE": {
        "sl_mult": 3.0,
        "tp1_mult": 3.5,
        "tp2_mult": 5.0,
        "tp3_mult": 6.5,
        "tenkan": 9,
        "kijun": 26,
        "displacement": 26,
        "filter_mode": "baseline",
        "oos_sharpe": 2.46,
        "wfe": 0.81,
        "wfe_tier": "normal",
    },
    "RUNE": {
        "sl_mult": 1.5,
        "tp1_mult": 4.75,
        "tp2_mult": 8.0,
        "tp3_mult": 10.0,
        "tenkan": 5,
        "kijun": 38,
        "displacement": 26,
        "filter_mode": "baseline",
        "oos_sharpe": 2.42,
        "wfe": 0.61,
        "wfe_tier": "normal",
    },
    "EGLD": {
        "sl_mult": 5.0,
        "tp1_mult": 1.75,
        "tp2_mult": 4.0,
        "tp3_mult": 5.5,
        "tenkan": 5,
        "kijun": 28,
        "displacement": 26,
        "filter_mode": "baseline",
        "oos_sharpe": 2.13,
        "wfe": 0.69,
        "wfe_tier": "normal",
    },
    "AVAX": {
        "sl_mult": 3.0,
        "tp1_mult": 4.75,
        "tp2_mult": 8.5,
        "tp3_mult": 9.0,
        "tenkan": 9,
        "kijun": 22,
        "displacement": 26,
        "filter_mode": "moderate",
        "oos_sharpe": 2.00,
        "wfe": 0.66,
        "wfe_tier": "normal",
    },
}

# Position sizing tiers based on WFE
POSITION_SIZING = {
    "extreme": {"size_pct": 50, "rationale": "High period sensitivity, expect 40-60% degradation"},
    "moderate": {"size_pct": 75, "rationale": "Period-sensitive, expect 30-50% degradation"},
    "normal": {"size_pct": 100, "rationale": "Expected degradation, standard sizing"},
}


def export_json_config(assets: list, output_dir: Path):
    """Export parameters to JSON format."""
    output_dir.mkdir(parents=True, exist_ok=True)
    
    config = {
        "metadata": {
            "generated": datetime.now().isoformat(),
            "version": "1.0",
            "system": "FINAL TRIGGER v2",
            "total_assets": len(assets),
        },
        "position_sizing_tiers": POSITION_SIZING,
        "assets": {},
    }
    
    for asset in assets:
        if asset in PROD_ASSET_PARAMS:
            params = PROD_ASSET_PARAMS[asset].copy()
            tier = params.get("wfe_tier", "normal")
            params["position_size_pct"] = POSITION_SIZING[tier]["size_pct"]
            config["assets"][asset] = params
        else:
            print(f"Warning: {asset} not found in PROD params")
    
    # Save full config
    config_path = output_dir / "asset_params.json"
    with open(config_path, "w") as f:
        json.dump(config, f, indent=2)
    print(f"✅ Full config exported to: {config_path}")
    
    # Save individual asset configs
    for asset, params in config["assets"].items():
        asset_path = output_dir / f"{asset}_config.json"
        with open(asset_path, "w") as f:
            json.dump({"asset": asset, **params}, f, indent=2)
    print(f"✅ Individual configs exported to: {output_dir}/")
    
    return config


def generate_pine_template(config: dict, output_dir: Path):
    """Generate Pine Script template."""
    
    template = '''// FINAL TRIGGER v2 — Ichimoku + ATR Strategy
// Generated: {timestamp}
// Assets: {asset_count}
// WARNING: Verify parameters before live trading

//@version=5
strategy("FINAL TRIGGER v2", overlay=true, pyramiding=0, default_qty_type=strategy.percent_of_equity, default_qty_value=100)

// ============================================
// INPUT PARAMETERS
// ============================================

// Asset Selection
i_asset = input.string("ETH", "Asset", options=[{asset_options}])

// ATR Parameters (per-asset defaults below)
i_sl_mult = input.float(3.0, "SL Multiplier", minval=0.5, maxval=10.0, step=0.25)
i_tp1_mult = input.float(3.5, "TP1 Multiplier", minval=0.5, maxval=15.0, step=0.25)
i_tp2_mult = input.float(5.0, "TP2 Multiplier", minval=0.5, maxval=15.0, step=0.25)
i_tp3_mult = input.float(6.5, "TP3 Multiplier", minval=0.5, maxval=15.0, step=0.25)

// Ichimoku Parameters
i_tenkan = input.int(9, "Tenkan Period", minval=5, maxval=50)
i_kijun = input.int(26, "Kijun Period", minval=10, maxval=100)
i_displacement = input.int(26, "Displacement", minval=10, maxval=100)

// Risk Management
i_position_size = input.float(100.0, "Position Size %", minval=10, maxval=100)

// ============================================
// PER-ASSET PARAMETER LOOKUP
// ============================================

// Get parameters based on selected asset
get_params(asset) =>
    switch asset
{asset_switch_cases}
        => [3.0, 3.5, 5.0, 6.5, 9, 26]  // Default

[sl, tp1, tp2, tp3, tenkan, kijun] = get_params(i_asset)

// ============================================
// ICHIMOKU CALCULATION
// ============================================

donchian(len) => math.avg(ta.lowest(len), ta.highest(len))

tenkan_sen = donchian(i_tenkan)
kijun_sen = donchian(i_kijun)
senkou_span_a = math.avg(tenkan_sen, kijun_sen)
senkou_span_b = donchian(52)
chikou_span = close[i_displacement]

// Cloud
cloud_top = math.max(senkou_span_a[i_displacement], senkou_span_b[i_displacement])
cloud_bottom = math.min(senkou_span_a[i_displacement], senkou_span_b[i_displacement])

// ============================================
// ATR CALCULATION
// ============================================

atr = ta.atr(14)

// ============================================
// ENTRY CONDITIONS
// ============================================

// Bullish: Price above cloud, Tenkan > Kijun, Chikou above price
bullish_cloud = close > cloud_top
bullish_tk = tenkan_sen > kijun_sen
bullish_chikou = chikou_span > close[i_displacement]

long_condition = bullish_cloud and bullish_tk and bullish_chikou

// ============================================
// POSITION MANAGEMENT
// ============================================

if (long_condition and strategy.position_size == 0)
    stop_loss = close - (atr * i_sl_mult)
    take_profit_1 = close + (atr * i_tp1_mult)
    take_profit_2 = close + (atr * i_tp2_mult)
    take_profit_3 = close + (atr * i_tp3_mult)
    
    strategy.entry("Long", strategy.long)
    strategy.exit("TP1", "Long", limit=take_profit_1, stop=stop_loss, qty_percent=50)
    strategy.exit("TP2", "Long", limit=take_profit_2, qty_percent=30)
    strategy.exit("TP3", "Long", limit=take_profit_3, qty_percent=20)

// ============================================
// PLOTTING
// ============================================

plot(tenkan_sen, color=color.blue, title="Tenkan")
plot(kijun_sen, color=color.red, title="Kijun")
plot(senkou_span_a, color=color.green, title="Senkou A", offset=i_displacement)
plot(senkou_span_b, color=color.red, title="Senkou B", offset=i_displacement)

fill(plot(senkou_span_a, offset=i_displacement), plot(senkou_span_b, offset=i_displacement), 
     color=senkou_span_a > senkou_span_b ? color.new(color.green, 90) : color.new(color.red, 90))
'''
    
    # Build asset options string
    assets = list(config["assets"].keys())
    asset_options = ", ".join([f'"{a}"' for a in assets])
    
    # Build switch cases
    switch_cases = ""
    for asset, params in config["assets"].items():
        switch_cases += f'''        "{asset}" => [{params['sl_mult']}, {params['tp1_mult']}, {params['tp2_mult']}, {params['tp3_mult']}, {params['tenkan']}, {params['kijun']}]
'''
    
    # Format template
    pine_script = template.format(
        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        asset_count=len(assets),
        asset_options=asset_options,
        asset_switch_cases=switch_cases,
    )
    
    # Save
    pine_path = output_dir / "template_ichimoku_atr.pine"
    with open(pine_path, "w") as f:
        f.write(pine_script)
    print(f"✅ Pine Script template exported to: {pine_path}")


def generate_deployment_checklist(config: dict, output_dir: Path):
    """Generate deployment checklist markdown."""
    
    checklist = f"""# Pine Script Deployment Checklist

**Generated**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}  
**Assets**: {len(config['assets'])}

---

## Pre-Deployment Verification

### 1. Parameter Validation
- [ ] All TP values progressive: TP1 < TP2 < TP3
- [ ] SL multipliers within reasonable range (1.5-5.0)
- [ ] Ichimoku periods match validated values
- [ ] Position sizing tiers correctly applied

### 2. Backtest Cross-Validation
- [ ] Run Pine Script on TradingView with same data range
- [ ] Compare entry/exit signals with Python backtest
- [ ] Verify trade count within 10% tolerance
- [ ] Confirm Sharpe ratio within 20% of backtest

### 3. Paper Trading (Minimum 2 weeks)
- [ ] Deploy on TradingView paper trading
- [ ] Monitor for unexpected behavior
- [ ] Track regime shifts
- [ ] Document any discrepancies

---

## Asset Parameters Summary

| Asset | SL | TP1 | TP2 | TP3 | Tenkan | Kijun | Size % | WFE Tier |
|-------|-----|-----|-----|-----|--------|-------|--------|----------|
"""
    
    for asset, params in config["assets"].items():
        checklist += f"| {asset} | {params['sl_mult']} | {params['tp1_mult']} | {params['tp2_mult']} | {params['tp3_mult']} | {params['tenkan']} | {params['kijun']} | {params.get('position_size_pct', 100)}% | {params.get('wfe_tier', 'normal')} |\n"
    
    checklist += f"""
---

## Position Sizing Tiers

| Tier | Size % | Assets | Rationale |
|------|--------|--------|----------|
| Extreme (WFE > 2.0) | 50% | SHIB, DOT | High period sensitivity |
| Moderate (WFE 1.0-1.5) | 75% | ETH, TIA, MINA | Period-sensitive |
| Normal (WFE < 1.0) | 100% | Others | Standard deployment |

---

## Live Deployment Steps

1. **Import Pine Script** to TradingView
2. **Select asset** from dropdown
3. **Verify parameters** match this document
4. **Set alerts** for entry signals
5. **Configure broker** integration (if applicable)
6. **Start with Tier 1** (normal) assets first
7. **Monitor daily** for first 2 weeks

---

## Rollback Procedure

If live performance degrades > 40% from backtest:

1. **Pause all active positions**
2. **Review regime analysis** - Check if market shifted to BEAR
3. **Compare signals** - Pine vs Python
4. **Document discrepancy** in project-state.md
5. **Revert to paper trading** until resolved

---

## Emergency Contacts

- **Technical Issues**: Check GitHub issues
- **Strategy Questions**: Review docs/WORKFLOW_MULTI_ASSET_SCREEN_VALIDATE_PROD.md
- **Parameter Updates**: Run re-validation pipeline

---

*Checklist generated by export_pine_config.py*
"""
    
    checklist_path = output_dir / "PINE_DEPLOYMENT_CHECKLIST.md"
    with open(checklist_path, "w") as f:
        f.write(checklist)
    print(f"✅ Deployment checklist exported to: {checklist_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Export Pine Script configurations for PROD assets"
    )
    parser.add_argument(
        "--all-prod",
        action="store_true",
        help="Export all 14 PROD assets"
    )
    parser.add_argument(
        "--assets",
        nargs="+",
        help="Specific assets to export"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="pine_configs",
        help="Output directory (default: pine_configs)"
    )
    
    args = parser.parse_args()
    
    if args.all_prod:
        assets = list(PROD_ASSET_PARAMS.keys())
    elif args.assets:
        assets = [a.upper() for a in args.assets]
    else:
        print("Error: Specify --all-prod or --assets")
        sys.exit(1)
    
    output_dir = PROJECT_ROOT / args.output
    
    print("\n" + "="*80)
    print("PINE SCRIPT CONFIGURATION EXPORT")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Assets: {len(assets)}")
    print(f"Output: {output_dir}")
    print("="*80)
    
    # Export JSON config
    config = export_json_config(assets, output_dir)
    
    # Generate Pine Script template
    generate_pine_template(config, output_dir)
    
    # Generate deployment checklist
    generate_deployment_checklist(config, output_dir)
    
    print("\n" + "="*80)
    print("✅ EXPORT COMPLETE")
    print("="*80)
    print(f"\nFiles generated:")
    print(f"  - {output_dir}/asset_params.json")
    print(f"  - {output_dir}/template_ichimoku_atr.pine")
    print(f"  - {output_dir}/PINE_DEPLOYMENT_CHECKLIST.md")
    print(f"  - {output_dir}/<ASSET>_config.json (x{len(assets)})")


if __name__ == "__main__":
    main()
