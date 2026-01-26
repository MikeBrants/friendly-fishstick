"""Asset-specific configuration for FINAL TRIGGER v2.

SOURCE OF TRUTH: PineScript presets in Pinefinal.txt.

This file exists to guarantee Pine ↔ Python signal parity by ensuring that:
- PUZZLE Ichimoku params (tenkan/kijun) are used for the PUZZLE layer
- 5-in-1 Ichimoku params (tenkan_5/kijun_5) are used for the 5-in-1 layer

If tenkan_5/kijun_5 are not passed, Python silently falls back to defaults
(9/26) and SHORT signals can diverge or disappear.

Ref: Issue #18 (Short Signal Parity Pine/Python)
"""

from __future__ import annotations

from typing import Any, Dict


# =============================================================================
# ASSET CONFIGURATIONS — Extracted from Pine presets
# Pine format: [SL, TP1, TP2, TP3, Tenkan, Kijun, Tenkan5, Kijun5]
# =============================================================================

ASSET_CONFIGS: Dict[str, Dict[str, Any]] = {
    # WF presets available in Pinefinal.txt
    "BTC": {
        "sl_mult": 4.50,
        "tp1_mult": 4.25,
        "tp2_mult": 7.50,
        "tp3_mult": 9.50,
        "tenkan": 6,
        "kijun": 37,
        "tenkan_5": 9,
        "kijun_5": 29,
        "displacement": 52,
        "displacement_5": 52,
    },
    "ETH": {
        "sl_mult": 4.50,
        "tp1_mult": 4.75,
        "tp2_mult": 3.00,
        "tp3_mult": 4.50,
        "tenkan": 17,
        "kijun": 31,
        "tenkan_5": 13,
        "kijun_5": 20,
        "displacement": 52,
        "displacement_5": 52,
    },
    "AVAX": {
        "sl_mult": 2.75,
        "tp1_mult": 1.50,
        "tp2_mult": 10.50,
        "tp3_mult": 8.00,
        "tenkan": 20,
        "kijun": 23,
        "tenkan_5": 12,
        "kijun_5": 16,
        "displacement": 52,
        "displacement_5": 52,
    },
    "UNI": {
        "sl_mult": 4.25,
        "tp1_mult": 4.50,
        "tp2_mult": 3.00,
        "tp3_mult": 9.50,
        "tenkan": 7,
        "kijun": 23,
        "tenkan_5": 8,
        "kijun_5": 28,
        "displacement": 52,
        "displacement_5": 52,
    },
    "SEI": {
        "sl_mult": 4.25,
        "tp1_mult": 4.75,
        "tp2_mult": 3.00,
        "tp3_mult": 9.50,
        "tenkan": 20,
        "kijun": 33,
        "tenkan_5": 8,
        "kijun_5": 28,
        "displacement": 52,
        "displacement_5": 52,
    },

    # Fallback (matches Pine "Custom" defaults)
    "DEFAULT": {
        "sl_mult": 3.00,
        "tp1_mult": 2.00,
        "tp2_mult": 6.00,
        "tp3_mult": 10.00,
        "tenkan": 9,
        "kijun": 26,
        "tenkan_5": 9,
        "kijun_5": 26,
        "displacement": 52,
        "displacement_5": 52,
    },
}


def get_asset_config(asset: str) -> Dict[str, Any]:
    """Return a validated config dict for an asset (or DEFAULT)."""
    asset_upper = asset.upper().replace("/USDT", "").replace("USDT", "")
    return ASSET_CONFIGS.get(asset_upper, ASSET_CONFIGS["DEFAULT"]).copy()


def validate_config(config: Dict[str, Any]) -> None:
    """Raise if required fields are missing."""
    required = [
        "sl_mult",
        "tp1_mult",
        "tp2_mult",
        "tp3_mult",
        "tenkan",
        "kijun",
        "tenkan_5",
        "kijun_5",
    ]
    missing = [k for k in required if k not in config]
    if missing:
        raise ValueError(f"Missing required config fields: {missing}")


def build_params_for_asset(asset: str):
    """Build FinalTriggerParams using both IchimokuConfig and FiveInOneConfig.

    IMPORTANT: This is the safe constructor that guarantees TS5/KS5 propagation.
    """
    from crypto_backtest.strategies.final_trigger import FinalTriggerParams
    from crypto_backtest.indicators.ichimoku import IchimokuConfig
    from crypto_backtest.indicators.five_in_one import FiveInOneConfig

    config = get_asset_config(asset)
    validate_config(config)

    ichimoku_config = IchimokuConfig(
        tenkan_period=config["tenkan"],
        kijun_period=config["kijun"],
        displacement=config.get("displacement", 52),
    )

    five_in_one_config = FiveInOneConfig(
        tenkan_5=config["tenkan_5"],
        kijun_5=config["kijun_5"],
        displacement_5=config.get("displacement_5", 52),
    )

    return FinalTriggerParams(
        sl_mult=config["sl_mult"],
        tp1_mult=config["tp1_mult"],
        tp2_mult=config["tp2_mult"],
        tp3_mult=config["tp3_mult"],
        ichimoku=ichimoku_config,
        five_in_one=five_in_one_config,
    )
