"""02-03 Task 1 (TDD): NUTS0 chain-link for PT, IE, MT (DATA-04).

Each of PT, IE, MT has:
- Full year range 1900-2024 in output (after join).
- enforce_eurostat_unit_guard runs on every Eurostat CSV read (CLV required, CP/PPS rejected).
- chain_link_rw_plus_institutional used for NUTS0 series, same anchor pattern.
"""
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


def _make_rw_nuts0_df(code: str, anchor_year: int = 2020, value_at_anchor: float = 20000.0) -> pd.DataFrame:
    """Synthetic RW series for a NUTS0 country code, 1900..anchor_year."""
    years = list(range(1900, anchor_year + 1))
    values = [value_at_anchor * (0.15 + 0.85 * (y - 1900) / max(1, anchor_year - 1900)) for y in years]
    return pd.DataFrame({"nuts2_code": code, "year": years, "value": values})


def _make_eurostat_nuts0_df(code: str, anchor_year: int = 2020, value_at_anchor: float = 25000.0) -> pd.DataFrame:
    """Synthetic Eurostat CLV series for a NUTS0 country, 2000..2024."""
    years = list(range(2000, 2025))
    values = [value_at_anchor * (0.85 + 0.15 * (y - 2000) / (2024 - 2000)) for y in years]
    return pd.DataFrame({"year": years, "value": values})


class TestNuts0ChainLinkPtIeMt(unittest.TestCase):
    """NUTS0 chain-link for PT, IE, MT via chain_link_rw_plus_institutional (DATA-04)."""

    def setUp(self) -> None:
        self.m = _load_extend_gdp()
        self.anchor = 2020
        self.countries = ["PT", "IE", "MT"]

    def test_act2_series_list_includes_pt_ie_mt(self) -> None:
        """act2_series_list() must include entries for PT, IE, MT with nuts0 scope."""
        m = self.m
        specs = m.act2_series_list()
        nuts0_rw_codes = {s.rw_code for s in specs if s.scope == m.SeriesScope.nuts0}
        for country in self.countries:
            self.assertIn(country, nuts0_rw_codes, f"Missing NUTS0 entry for {country}")

    def test_act2_series_pt_ie_mt_use_eurostat(self) -> None:
        """PT, IE, MT series must use InstitutionalSource.eurostat."""
        m = self.m
        specs = m.act2_series_list()
        for spec in specs:
            if spec.rw_code in self.countries:
                self.assertEqual(
                    spec.institutional,
                    m.InstitutionalSource.eurostat,
                    f"{spec.rw_code} must use Eurostat, not {spec.institutional}",
                )

    def test_act2_series_pt_ie_mt_have_euro_geo(self) -> None:
        """PT, IE, MT series must have euro_geo set to their ISO code."""
        m = self.m
        for spec in m.act2_series_list():
            if spec.rw_code in self.countries:
                self.assertIsNotNone(spec.euro_geo, f"{spec.rw_code} must have euro_geo")
                self.assertEqual(
                    spec.euro_geo, spec.rw_code,
                    f"{spec.rw_code} euro_geo should match rw_code",
                )

    def test_chain_link_nuts0_full_year_range(self) -> None:
        """chain_link_rw_plus_institutional on PT produces rows for all 1900..2024."""
        m = self.m
        for code in self.countries:
            rw = _make_rw_nuts0_df(code, self.anchor)
            inst = _make_eurostat_nuts0_df(code, self.anchor)
            full, _ = m.chain_link_rw_plus_institutional(
                rw, inst, code, self.anchor, institutional_label="eurostat"
            )
            years = set(full["year"].astype(int).tolist())
            self.assertEqual(min(years), m.YEAR_MIN, f"{code}: min year should be {m.YEAR_MIN}")
            self.assertEqual(max(years), m.YEAR_MAX, f"{code}: max year should be {m.YEAR_MAX}")

    def test_chain_link_nuts0_seam_at_anchor(self) -> None:
        """At anchor year, chain-linked value matches RW value (within 1e-6)."""
        m = self.m
        for code in self.countries:
            rw_anchor_val = 18000.0
            rw = _make_rw_nuts0_df(code, self.anchor, value_at_anchor=rw_anchor_val)
            inst = _make_eurostat_nuts0_df(code, self.anchor, value_at_anchor=23000.0)
            full, _ = m.chain_link_rw_plus_institutional(
                rw, inst, code, self.anchor, institutional_label="eurostat"
            )
            row = full[full["year"] == self.anchor]
            self.assertFalse(row.empty, f"{code}: anchor year row must exist")
            extended_val = float(row["gdp_pc_2011ppp"].iloc[0])
            self.assertAlmostEqual(
                extended_val, rw_anchor_val, places=4,
                msg=f"{code}: value at {self.anchor} ({extended_val}) must match RW ({rw_anchor_val})",
            )

    def test_chain_link_nuts0_pre_chain_uses_rw(self) -> None:
        """Years before 2000 use RW values directly (not Eurostat)."""
        m = self.m
        code = "PT"
        rw = _make_rw_nuts0_df(code, self.anchor, value_at_anchor=18000.0)
        inst = _make_eurostat_nuts0_df(code, self.anchor, value_at_anchor=23000.0)
        full, _ = m.chain_link_rw_plus_institutional(
            rw, inst, code, self.anchor, institutional_label="eurostat"
        )
        pre = full[full["year"] < m.CHAIN_START]
        for yr in [1900, 1950, 1999]:
            rw_val = float(rw[(rw["nuts2_code"] == code) & (rw["year"] == yr)]["value"].iloc[0])
            ext_val = float(pre[pre["year"] == yr]["gdp_pc_2011ppp"].iloc[0])
            self.assertAlmostEqual(
                ext_val, rw_val, places=4,
                msg=f"PT {yr}: pre-chain must use RW value {rw_val}",
            )

    def test_chain_link_nuts0_source_column(self) -> None:
        """Output has a 'source' column; pre-chain rows labelled 'roseswolf'."""
        m = self.m
        code = "IE"
        rw = _make_rw_nuts0_df(code, self.anchor)
        inst = _make_eurostat_nuts0_df(code, self.anchor)
        full, _ = m.chain_link_rw_plus_institutional(
            rw, inst, code, self.anchor, institutional_label="eurostat"
        )
        self.assertIn("source", full.columns, "Output must have 'source' column")
        pre_sources = full[full["year"] < m.CHAIN_START]["source"].unique()
        self.assertTrue(
            all(s == "roseswolf" for s in pre_sources),
            f"Pre-chain rows must be labelled 'roseswolf', got: {pre_sources}",
        )

    def test_eurostat_unit_guard_rejects_cp(self) -> None:
        """enforce_eurostat_unit_guard raises PipelineError on CP/current-price data."""
        m = self.m
        df_cp = pd.DataFrame({"unit": ["CP_EUR_HAB"], "geo": ["PT"], "year": [2020], "value": [20000]})
        with self.assertRaises(m.PipelineError):
            m.enforce_eurostat_unit_guard(df_cp, header_text="CP_EUR_HAB PT 2020")

    def test_eurostat_unit_guard_rejects_pps(self) -> None:
        """enforce_eurostat_unit_guard raises PipelineError on PPS data."""
        m = self.m
        df_pps = pd.DataFrame({"unit": ["PPS_EUR_HAB"], "geo": ["PT"], "year": [2020], "value": [20000]})
        with self.assertRaises(m.PipelineError):
            m.enforce_eurostat_unit_guard(df_pps, header_text="PPS_EUR_HAB PT 2020")

    def test_eurostat_unit_guard_passes_clv(self) -> None:
        """enforce_eurostat_unit_guard passes on CLV data."""
        m = self.m
        df_clv = pd.DataFrame({"unit": ["CLV10_EUR_HAB"], "geo": ["PT"], "year": [2020], "value": [20000]})
        label, units = m.enforce_eurostat_unit_guard(df_clv, header_text="CLV10_EUR_HAB PT 2020")
        self.assertIn("CLV10_EUR_HAB", units)

    def test_nuts0_specs_have_correct_slugs(self) -> None:
        """PT, IE, MT series specs have expected slugs."""
        m = self.m
        expected = {"PT": "portugal", "IE": "ireland", "MT": "malta"}
        for spec in m.act2_series_list():
            if spec.rw_code in expected:
                self.assertEqual(
                    spec.slug, expected[spec.rw_code],
                    f"{spec.rw_code} slug should be '{expected[spec.rw_code]}'",
                )
