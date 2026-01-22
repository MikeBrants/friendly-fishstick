"""
Filter mode configurations for optimization.
"""

FILTER_MODES = {
    "baseline": {
        "use_distance_filter": False,
        "use_volume_filter": False,
        "use_regression_cloud": False,
        "use_kama_oscillator": False,
        "use_ichimoku_filter": True,
        "ichi5in1_strict": False,
    },
    "light_kama": {
        "use_distance_filter": False,
        "use_volume_filter": False,
        "use_regression_cloud": False,
        "use_kama_oscillator": True,
        "use_ichimoku_filter": True,
        "ichi5in1_strict": False,
    },
    "light_distance": {
        "use_distance_filter": True,
        "use_volume_filter": False,
        "use_regression_cloud": False,
        "use_kama_oscillator": False,
        "use_ichimoku_filter": True,
        "ichi5in1_strict": False,
    },
    "light_volume": {
        "use_distance_filter": False,
        "use_volume_filter": True,
        "use_regression_cloud": False,
        "use_kama_oscillator": False,
        "use_ichimoku_filter": True,
        "ichi5in1_strict": False,
    },
    "light_regression": {
        "use_distance_filter": False,
        "use_volume_filter": False,
        "use_regression_cloud": True,
        "use_kama_oscillator": False,
        "use_ichimoku_filter": True,
        "ichi5in1_strict": False,
    },
    "medium_kama_distance": {
        "use_distance_filter": True,
        "use_volume_filter": False,
        "use_regression_cloud": False,
        "use_kama_oscillator": True,
        "use_ichimoku_filter": True,
        "ichi5in1_strict": False,
    },
    "medium_kama_volume": {
        "use_distance_filter": False,
        "use_volume_filter": True,
        "use_regression_cloud": False,
        "use_kama_oscillator": True,
        "use_ichimoku_filter": True,
        "ichi5in1_strict": False,
    },
    "medium_kama_regression": {
        "use_distance_filter": False,
        "use_volume_filter": False,
        "use_regression_cloud": True,
        "use_kama_oscillator": True,
        "use_ichimoku_filter": True,
        "ichi5in1_strict": False,
    },
    "medium_distance_volume": {
        "use_distance_filter": True,
        "use_volume_filter": True,
        "use_regression_cloud": False,
        "use_kama_oscillator": False,
        "use_ichimoku_filter": True,
        "ichi5in1_strict": False,
    },
    "moderate": {
        "use_distance_filter": True,
        "use_volume_filter": True,
        "use_regression_cloud": True,
        "use_kama_oscillator": True,
        "use_ichimoku_filter": True,
        "ichi5in1_strict": False,
    },
    "strict_ichi": {
        "use_distance_filter": False,
        "use_volume_filter": False,
        "use_regression_cloud": False,
        "use_kama_oscillator": False,
        "use_ichimoku_filter": True,
        "ichi5in1_strict": True,
    },
}


def get_filter_config(mode: str = "baseline") -> dict:
    key = mode.lower()
    if key not in FILTER_MODES:
        raise ValueError(f"Unknown mode: {mode}. Available: {list(FILTER_MODES.keys())}")
    return FILTER_MODES[key].copy()
