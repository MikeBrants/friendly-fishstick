"""
Filter Mode Configurations - FINAL TRIGGER v2
Simplifié : 3 modes rationnels (baseline → moderate → conservative)

Changement 2026-01-24:
- Ancien système: 12 combinaisons arbitraires (data mining)
- Nouveau système: 3 modes avec cascade rescue
- Seuil sensitivity relevé à 15% (était 10%)
"""

FILTER_MODES = {
    'baseline': {
        'use_distance_filter': False,
        'use_volume_filter': False,
        'use_regression_cloud': False,
        'use_kama_oscillator': False,
        'use_ichimoku_filter': True,
        'ichi5in1_strict': False,
    },
    'moderate': {
        'use_distance_filter': True,
        'use_volume_filter': True,
        'use_regression_cloud': True,
        'use_kama_oscillator': True,
        'use_ichimoku_filter': True,
        'ichi5in1_strict': False,
    },
    'conservative': {
        'use_distance_filter': True,
        'use_volume_filter': True,
        'use_regression_cloud': True,
        'use_kama_oscillator': True,
        'use_ichimoku_filter': True,
        'ichi5in1_strict': True,
    },
}

# Seuils par mode (trades OOS minimum, WFE minimum)
MODE_THRESHOLDS = {
    'baseline': {'min_trades_oos': 60, 'min_wfe': 0.6},
    'moderate': {'min_trades_oos': 50, 'min_wfe': 0.6},
    'conservative': {'min_trades_oos': 40, 'min_wfe': 0.55},
}


def get_filter_config(mode: str = 'baseline') -> dict:
    """Get filter configuration for a mode."""
    if mode not in FILTER_MODES:
        raise ValueError(f"Unknown mode '{mode}'. Available: {list(FILTER_MODES.keys())}")
    return FILTER_MODES[mode].copy()


def get_mode_thresholds(mode: str = 'baseline') -> dict:
    """Get validation thresholds for a mode."""
    if mode not in MODE_THRESHOLDS:
        raise ValueError(f"Unknown mode '{mode}'. Available: {list(MODE_THRESHOLDS.keys())}")
    return MODE_THRESHOLDS[mode].copy()
