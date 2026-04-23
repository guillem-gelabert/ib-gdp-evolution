"""02-01 Task 2: load_roseswolf_population."""
from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "extend_gdp.py"


def _load_extend_gdp():
    name = "extend_gdp_tests_dynamic"
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[name] = mod
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


class TestRosesWolfPopulation(unittest.TestCase):
    def test_load_population_tidy_xlsx(self) -> None:
        m = _load_extend_gdp()
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "roseswolf_regionalgdp_v7.xlsx"
            pop = pd.DataFrame(
                {
                    "nuts2_code": ["ES53", "PT"],
                    "year": [2000, 2000],
                    "population": [1_000_000.0, 10_000_000.0],
                }
            )
            gdp = pd.DataFrame({"nuts2_code": ["ES53"], "2020": [30000.0]})
            with pd.ExcelWriter(p, engine="openpyxl") as w:
                gdp.to_excel(w, sheet_name="gdp_pc_ppp", index=False)
                pop.to_excel(w, sheet_name="population", index=False)
            df = m.load_roseswolf_population(p)
            self.assertFalse(df.empty)
            self.assertIn("year", df.columns)
            self.assertIn("population", df.columns)
            self.assertIn("ES53", set(df["nuts2_code"]))

    def test_load_population_checked_in_data_xlsx(self) -> None:
        m = _load_extend_gdp()
        p = m.find_input_file(REPO_ROOT, "roseswolf_regionalgdp_v7.xlsx")
        df = m.load_roseswolf_population(p)
        self.assertFalse(df.empty)
        self.assertIn("year", df.columns)
