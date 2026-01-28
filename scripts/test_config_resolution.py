"""Basic assertions for v4.2 config resolution."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from crypto_backtest.v4.config import load_yaml, resolve_family, get_policy, get_thresholds


def main() -> None:
    cfg = load_yaml("configs/families.yaml")

    for family_id in ("A", "B", "C"):
        resolved = resolve_family(cfg, family_id)
        assert isinstance(resolved, dict)
        for key in ("strategy", "filters", "regime", "displacement"):
            assert key in resolved
        assert isinstance(resolved["filters"].get("preset"), str)

    resolved_b = resolve_family(cfg, "B")
    assert resolved_b["strategy"]["split_long_short"] is True
    assert resolved_b["regime"]["enabled"] is True

    rescue_r1 = resolve_family(cfg, "A", rescue_id="R1")
    rescue_r2 = resolve_family(cfg, "A", rescue_id="R2")
    assert rescue_r1["filters"]["preset"] == "moderate"
    assert rescue_r2["filters"]["preset"] == "conservative"

    policy = get_policy(cfg)
    thresholds = get_thresholds(cfg)
    assert policy.get("random_seed") == 42
    assert "guards" in thresholds
    assert "pbo" in thresholds

    print("PASS")


if __name__ == "__main__":
    main()