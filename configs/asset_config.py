"""Asset-specific configuration for FINAL TRIGGER v2.

This file contains optimized parameters for each asset, extracted from
PineScript presets to ensure Python/Pine signal parity.

CRITICAL: Both PUZZLE Ichimoku (tenkan/kijun) AND 5-in-1 Ichimoku (tenkan_5/kijun_5)
must be specified per asset. Using defaults causes SHORT signal failures.

Reference: Issue #18 - Short Signal Parity Pine/Python
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Any


# =============================================================================
# ASSET CONFIGURATIONS - Extracted from Pine presets
# Format: [slMult, tp1, tp2, tp3, TSD1, KSD1, TS5, KS5]
# =============================================================================

ASSET_CONFIGS: Dict[str, Dict[str, Any]] = {
    # -------------------------------------------------------------------------
    # TIER 1 - Core Assets (High Priority)
    # -------------------------------------------------------------------------
    "BTC": {
        "sl_mult": 4.50, "tp1_mult": 4.25, "tp2_mult": 7.50, "tp3_mult": 9.50,
        "tenkan": 6, "kijun": 37,
        "tenkan_5": 9, "kijun_5": 29,
        "displacement": 52, "displacement_5": 52,
    },
    "ETH": {
        "sl_mult": 4.50, "tp1_mult": 4.75, "tp2_mult": 3.00, "tp3_mult": 4.50,
        "tenkan": 17, "kijun": 31,
        "tenkan_5": 13, "kijun_5": 20,
        "displacement": 52, "displacement_5": 52,
    },
    
    # -------------------------------------------------------------------------
    # TIER 2 - Validated Assets (PROD ready)
    # -------------------------------------------------------------------------
    "SHIB": {
        "sl_mult": 3.00, "tp1_mult": 2.00, "tp2_mult": 6.00, "tp3_mult": 10.00,
        "tenkan": 9, "kijun": 26,
        "tenkan_5": 9, "kijun_5": 26,
        "displacement": 52, "displacement_5": 52,
    },
    "DOT": {
        "sl_mult": 3.25, "tp1_mult": 2.50, "tp2_mult": 5.50, "tp3_mult": 8.50,
        "tenkan": 11, "kijun": 28,
        "tenkan_5": 10, "kijun_5": 24,
        "displacement": 52, "displacement_5": 52,
    },
    "TIA": {
        "sl_mult": 3.50, "tp1_mult": 3.00, "tp2_mult": 5.00, "tp3_mult": 9.00,
        "tenkan": 14, "kijun": 30,
        "tenkan_5": 11, "kijun_5": 22,
        "displacement": 52, "displacement_5": 52,
    },
    "NEAR": {
        "sl_mult": 3.75, "tp1_mult": 3.25, "tp2_mult": 6.00, "tp3_mult": 8.00,
        "tenkan": 12, "kijun": 29,
        "tenkan_5": 10, "kijun_5": 25,
        "displacement": 52, "displacement_5": 52,
    },
    "DOGE": {
        "sl_mult": 4.00, "tp1_mult": 3.50, "tp2_mult": 5.50, "tp3_mult": 9.50,
        "tenkan": 8, "kijun": 32,
        "tenkan_5": 9, "kijun_5": 27,
        "displacement": 52, "displacement_5": 52,
    },
    "ANKR": {
        "sl_mult": 3.25, "tp1_mult": 2.75, "tp2_mult": 6.50, "tp3_mult": 10.00,
        "tenkan": 10, "kijun": 27,
        "tenkan_5": 9, "kijun_5": 26,
        "displacement": 52, "displacement_5": 52,
    },
    "JOE": {
        "sl_mult": 3.50, "tp1_mult": 3.00, "tp2_mult": 7.00, "tp3_mult": 9.50,
        "tenkan": 13, "kijun": 25,
        "tenkan_5": 11, "kijun_5": 23,
        "displacement": 52, "displacement_5": 52,
    },
    "YGG": {
        "sl_mult": 3.75, "tp1_mult": 3.25, "tp2_mult": 5.50, "tp3_mult": 8.50,
        "tenkan": 15, "kijun": 28,
        "tenkan_5": 12, "kijun_5": 24,
        "displacement": 52, "displacement_5": 52,
    },
    "MINA": {
        "sl_mult": 4.00, "tp1_mult": 3.50, "tp2_mult": 6.00, "tp3_mult": 9.00,
        "tenkan": 11, "kijun": 30,
        "tenkan_5": 10, "kijun_5": 26,
        "displacement": 52, "displacement_5": 52,
    },
    "CAKE": {
        "sl_mult": 3.50, "tp1_mult": 2.75, "tp2_mult": 5.50, "tp3_mult": 8.00,
        "tenkan": 14, "kijun": 27,
        "tenkan_5": 11, "kijun_5": 25,
        "displacement": 52, "displacement_5": 52,
    },
    "RUNE": {
        "sl_mult": 4.25, "tp1_mult": 4.00, "tp2_mult": 6.50, "tp3_mult": 10.00,
        "tenkan": 10, "kijun": 33,
        "tenkan_5": 9, "kijun_5": 28,
        "displacement": 52, "displacement_5": 52,
    },
    
    # -------------------------------------------------------------------------
    # TIER 3 - Previously validated (needs re-validation post-fix)
    # -------------------------------------------------------------------------
    "AVAX": {
        "sl_mult": 2.75, "tp1_mult": 1.50, "tp2_mult": 10.50, "tp3_mult": 8.00,
        "tenkan": 20, "kijun": 23,
        "tenkan_5": 12, "kijun_5": 16,
        "displacement": 52, "displacement_5": 52,
    },
    "UNI": {
        "sl_mult": 4.25, "tp1_mult": 4.50, "tp2_mult": 3.00, "tp3_mult": 9.50,
        "tenkan": 7, "kijun": 23,
        "tenkan_5": 8, "kijun_5": 28,
        "displacement": 52, "displacement_5": 52,
    },
    "SEI": {
        "sl_mult": 4.25, "tp1_mult": 4.75, "tp2_mult": 3.00, "tp3_mult": 9.50,
        "tenkan": 20, "kijun": 33,
        "tenkan_5": 8, "kijun_5": 28,
        "displacement": 52, "displacement_5": 52,
    },
    "OSMO": {
        "sl_mult": 3.50, "tp1_mult": 3.00, "tp2_mult": 6.00, "tp3_mult": 9.00,
        "tenkan": 12, "kijun": 28,
        "tenkan_5": 10, "kijun_5": 25,
        "displacement": 52, "displacement_5": 52,
    },
    
    # -------------------------------------------------------------------------
    # DEFAULT - Fallback for unknown assets
    # -------------------------------------------------------------------------
    "DEFAULT": {
        "sl_mult": 3.00, "tp1_mult": 2.00, "tp2_mult": 6.00, "tp3_mult": 10.00,
        "tenkan": 9, "kijun": 26,
        "tenkan_5": 9, "kijun_5": 26,
        "displacement": 52, "displacement_5": 52,
    },
}


def get_asset_config(asset: str) -> Dict[str, Any]:
    """Get configuration for a specific asset.
    
    Args:
        asset: Asset symbol (e.g., 'ETH', 'BTC')
        
    Returns:
        Dictionary with all params for the asset
        
    Example:
        >>> config = get_asset_config("ETH")
        >>> print(config["tenkan_5"])  # 13
        >>> print(config["kijun_5"])   # 20
    """
    # Normalize asset name
    asset_upper = asset.upper().replace("/USDT", "").replace("USDT", "")
    
    if asset_upper in ASSET_CONFIGS:
        return ASSET_CONFIGS[asset_upper].copy()
    
    # Return default with warning
    import warnings
    warnings.warn(
        f"No config found for asset '{asset}', using DEFAULT. "
        f"This may cause suboptimal results. Add config to asset_config.py."
    )
    return ASSET_CONFIGS["DEFAULT"].copy()


def validate_config(config: Dict[str, Any]) -> bool:
    """Validate that a config has all required fields.
    
    Args:
        config: Asset configuration dictionary
        
    Returns:
        True if valid, raises ValueError if invalid
    """
    required_fields = [
        "sl_mult", "tp1_mult", "tp2_mult", "tp3_mult",
        "tenkan", "kijun",
        "tenkan_5", "kijun_5",  # CRITICAL for SHORT signals
    ]
    
    missing = [f for f in required_fields if f not in config]
    if missing:
        raise ValueError(f"Missing required config fields: {missing}")
    
    # Validate TP progression
    if not (config["tp1_mult"] <= config["tp2_mult"] <= config["tp3_mult"]):
        # Allow some flexibility but warn
        import warnings
        warnings.warn(
            f"TP progression may be non-standard: "
            f"TP1={config['tp1_mult']}, TP2={config['tp2_mult']}, TP3={config['tp3_mult']}"
        )
    
    return True


# =============================================================================
# CONVENIENCE FUNCTION - Build FinalTriggerParams from asset config
# =============================================================================

def build_params_for_asset(asset: str):
    """Build FinalTriggerParams from asset config.
    
    Args:
        asset: Asset symbol
        
    Returns:
        FinalTriggerParams instance with correct configs
        
    Example:
        >>> params = build_params_for_asset("ETH")
        >>> strategy = FinalTriggerStrategy(params)
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
