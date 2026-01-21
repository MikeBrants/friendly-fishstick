"""System utilities for resource management."""
from __future__ import annotations

import json
import os
import shutil
from pathlib import Path

CONFIG_PATH = Path("config/machine_profile.json")


def get_default_workers(task: str = "bayesian") -> int:
    """Get recommended workers for a task based on machine profile."""
    cpu_count = os.cpu_count() or 4

    if CONFIG_PATH.exists():
        profile = json.loads(CONFIG_PATH.read_text())
        profile_value = profile.get("workers", {}).get(task)
        if profile_value:
            return int(profile_value)

    defaults = {
        "bayesian": min(6, cpu_count),
        "guards": min(4, cpu_count),
        "download": min(8, cpu_count),
        "displacement_grid": min(6, cpu_count),
    }
    return defaults.get(task, min(4, cpu_count))


def check_storage_warning() -> tuple[bool, str]:
    """Check if storage is running low."""
    total, used, free = shutil.disk_usage("/")
    used_pct = (used / total) * 100
    free_gb = free / (1024**3)

    if used_pct > 90:
        return True, f"⚠️ Stockage critique: {used_pct:.0f}% utilisé ({free_gb:.1f} GB libre)"
    return False, f"Stockage OK: {free_gb:.1f} GB libre"


def get_system_info() -> dict:
    """Get system information for display."""
    import psutil

    cpu_count = os.cpu_count() or 0
    ram_gb = psutil.virtual_memory().total / (1024**3)
    total, used, free = shutil.disk_usage("/")

    return {
        "cpu_cores": cpu_count,
        "ram_gb": round(ram_gb, 1),
        "disk_total_gb": round(total / (1024**3), 1),
        "disk_free_gb": round(free / (1024**3), 1),
        "disk_used_pct": round((used / total) * 100, 1),
    }
