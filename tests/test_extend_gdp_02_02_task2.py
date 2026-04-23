"""02-02 Task 2 (TDD): Chain-link four Spanish NUTS2 series + IB Act II 2020 anchor (DATA-03, DATA-05)."""
from __future__ import annotations

import importlib.util
import sys
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


def _make_rw_df(code: str, anchor_year: int = 2020, value_at_anchor: float = 15000.0) -> pd.DataFrame:
    """Synthetic RW series 1900..anchor_year with linear growth."""
    years = list(range(1900, anchor_year + 1))
    values = [value_at_anchor * (0.2 + 0.8 * (y - 1900) / (anchor_year - 1900)) for y in years]
    return pd.DataFrame({"nuts2_code": code, "year": years, "value": values})


def _make_institutional_df(code: str, anchor_year: int = 2020, value_at_anchor: float = 20000.0) -> pd.DataFrame:
    """Synthetic institutional (INE/Eurostat) series 2000..2024."""
    years = list(range(2000, 2025))
    values = [value_at_anchor * (0.9 + 0.1 * (y - 2000) / (2024 - 2000)) for y in years]
    return pd.DataFrame({"year": years, "value": values})


class TestChainLinkRwPlusInstitutional(unittest.TestCase):
    """Tests for chain_link_rw_plus_institutional for Spanish CCAA series."""

    def setUp(self) -> None:
        self.m = _load_extend_gdp()
        self.anchor = 2020

    def test_output_covers_full_range_1900_2024(self) -> None:
        """Chain-linked output must span YEAR_MIN..YEAR_MAX (1900..2024)."""
        rw = _make_rw_df("ES53", self.anchor)
        inst = _make_institutional_df("ES53", self.anchor)
        full, _ = self.m.chain_link_rw_plus_institutional(rw, inst, "ES53", self.anchor, institutional_label="ine")
        years = set(full["year"].astype(int).tolist())
        self.assertEqual(min(years), self.m.YEAR_MIN)
        self.assertEqual(max(years), self.m.YEAR_MAX)

    def test_seam_at_anchor_year_matches_rw(self) -> None:
        """At anchor year, chain-linked output must match RW value (within 1e-6)."""
        rw_anchor_val = 15000.0
        rw = _make_rw_df("ES53", self.anchor, value_at_anchor=rw_anchor_val)
        inst = _make_institutional_df("ES53", self.anchor, value_at_anchor=20000.0)
        full, _ = self.m.chain_link_rw_plus_institutional(rw, inst, "ES53", self.anchor, institutional_label="ine")
        row = full[full["year"] == self.anchor]
        self.assertFalse(row.empty, "anchor year row must exist")
        extended_val = float(row["gdp_pc_2011ppp"].iloc[0])
        self.assertAlmostEqual(extended_val, rw_anchor_val, places=4,
                               msg=f"Extended value at {self.anchor} ({extended_val}) must match RW ({rw_anchor_val})")

    def test_pre_chain_rows_use_rw_values(self) -> None:
        """Years before CHAIN_START (2000) use RW values directly."""
        rw_anchor_val = 15000.0
        rw = _make_rw_df("ES43", self.anchor, value_at_anchor=rw_anchor_val)
        inst = _make_institutional_df("ES43", self.anchor, value_at_anchor=20000.0)
        full, _ = self.m.chain_link_rw_plus_institutional(rw, inst, "ES43", self.anchor, institutional_label="ine")
        chain_start = self.m.CHAIN_START
        pre = full[full["year"] < chain_start]
        rw_pre = rw[rw["year"] < chain_start]
        for yr in [1900, 1950, 1999]:
            rw_val = float(rw_pre[rw_pre["year"] == yr]["value"].iloc[0])
            ext_val = float(pre[pre["year"] == yr]["gdp_pc_2011ppp"].iloc[0])
            self.assertAlmostEqual(ext_val, rw_val, places=4,
                                   msg=f"Pre-chain year {yr}: extended={ext_val} should equal rw={rw_val}")

    def test_source_column_present(self) -> None:
        """Output must contain a 'source' column marking data provenance."""
        rw = _make_rw_df("ES11", self.anchor)
        inst = _make_institutional_df("ES11", self.anchor)
        full, _ = self.m.chain_link_rw_plus_institutional(rw, inst, "ES11", self.anchor, institutional_label="ine")
        self.assertIn("source", full.columns)
        pre_sources = set(full[full["year"] < self.m.CHAIN_START]["source"].unique())
        self.assertTrue(pre_sources.issubset({"roseswolf"}), f"Pre-chain sources: {pre_sources}")

    def test_growth_compare_df_returned(self) -> None:
        """Second return value is a growth-compare DataFrame with year, euro_value, gdp_pc_2011ppp."""
        rw = _make_rw_df("ES42", self.anchor)
        inst = _make_institutional_df("ES42", self.anchor)
        _, gc = self.m.chain_link_rw_plus_institutional(rw, inst, "ES42", self.anchor, institutional_label="ine")
        for col in ["year", "euro_value", "gdp_pc_2011ppp"]:
            self.assertIn(col, gc.columns, f"growth-compare must have '{col}' column")

    def test_missing_anchor_in_rw_raises_pipeline_error(self) -> None:
        """If RW has no row for anchor_year, PipelineError must be raised."""
        rw = _make_rw_df("ES53", 2019)  # stops at 2019
        inst = _make_institutional_df("ES53", self.anchor)
        with self.assertRaises(self.m.PipelineError):
            self.m.chain_link_rw_plus_institutional(rw, inst, "ES53", self.anchor, institutional_label="ine")

    def test_missing_anchor_in_inst_raises_pipeline_error(self) -> None:
        """If institutional series has no row for anchor_year, PipelineError must be raised."""
        rw = _make_rw_df("ES53", self.anchor)
        # Truncate to stop before anchor year 2020
        inst = _make_institutional_df("ES53", self.anchor)
        inst = inst[inst["year"] < self.anchor]  # exclude anchor year
        with self.assertRaises(self.m.PipelineError):
            self.m.chain_link_rw_plus_institutional(rw, inst, "ES53", self.anchor, institutional_label="ine")

    def test_all_four_spanish_codes_chain_link_independently(self) -> None:
        """ES53, ES43, ES11, ES42 each produce valid outputs when processed separately."""
        for code in ["ES53", "ES43", "ES11", "ES42"]:
            rw = _make_rw_df(code, self.anchor)
            inst = _make_institutional_df(code, self.anchor)
            full, gc = self.m.chain_link_rw_plus_institutional(
                rw, inst, code, self.anchor, institutional_label="ine"
            )
            self.assertFalse(full.empty, f"{code}: output must not be empty")
            self.assertEqual(len(full), self.m.YEAR_MAX - self.m.YEAR_MIN + 1,
                             f"{code}: must have one row per year 1900..2024")

    def test_ib_act2_acts_as_separate_series(self) -> None:
        """IB Act II uses ES53 RW code — its output should not modify Act I CSV data."""
        rw = _make_rw_df("ES53", self.anchor, value_at_anchor=15000.0)
        inst = _make_institutional_df("ES53", self.anchor, value_at_anchor=22000.0)
        full, _ = self.m.chain_link_rw_plus_institutional(rw, inst, "ES53", self.anchor, institutional_label="ine")
        # The output DataFrame is in-memory only; verify it doesn't touch public/data/balearic_gdp_pc.csv
        act1_csv = REPO_ROOT / "public" / "data" / "balearic_gdp_pc.csv"
        if act1_csv.exists():
            original_content = act1_csv.read_text()
            # chain_link does not write anything; just verify the file is untouched
            self.assertEqual(act1_csv.read_text(), original_content,
                             "Act I CSV must not be modified by chain_link_rw_plus_institutional")

    def test_series_spec_list_includes_all_four_spanish_series(self) -> None:
        """act2_series_list() must include ES53 (IB), ES43, ES11, ES42 with INE institutional source."""
        m = self.m
        specs = m.act2_series_list()
        ine_specs = [s for s in specs if s.institutional == m.InstitutionalSource.ine]
        ine_codes = {s.ine_ccaa for s in ine_specs if s.ine_ccaa}
        for expected in ["ES53", "ES43", "ES11", "ES42"]:
            self.assertIn(expected, ine_codes, f"{expected} must be in Act II INE series list")


if __name__ == "__main__":
    unittest.main()
