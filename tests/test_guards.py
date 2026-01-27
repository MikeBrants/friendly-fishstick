import sys
from pathlib import Path

import numpy as np

# Allow importing scripts as modules
SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import run_guards_multiasset as rgm


def test_monte_carlo_pvalue_not_exact_zero():
    shuffled = np.zeros(1000, dtype=float)
    actual = 10.0
    p_value = rgm._mc_pvalue(shuffled, actual)
    assert p_value > 0.0


def test_pvalue_minimum_bound():
    shuffled = np.zeros(1000, dtype=float)
    actual = 10.0
    p_value = rgm._mc_pvalue(shuffled, actual)
    assert p_value >= 1.0 / (len(shuffled) + 1)
