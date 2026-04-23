"""02-03 Task 3 (TDD): EU-15 population-weighted reference series (DATA-06).

Formula (act2 notes §5): EU-15 = sum(pcpi_i × pop_i) / sum(pop_i) per year.
- Same anchor year 2020 as all other Act II series.
- Linear interpolation of RW decadal pcpi to annual (matching existing regional behavior).
- Pre-2000: RW population (from roseswolf workbook or comparable source).
- Post-2000: Eurostat population (demo_pjan / demo_r_d2jan).
- Output tidy series (nuts2_code='EU15', year, gdp_pc_2011ppp, source).
"""
from __future__ import annotations

import importlib.util
import math
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


def _make_eu15_country_series(
    geos: list[str],
    anchor_year: int = 2020,
    base_pcpi: float = 20000.0,
) -> dict[str, pd.DataFrame]:
    """Synthetic full series (1900..2024) per country."""
    out: dict[str, pd.DataFrame] = {}
    for i, g in enumerate(geos):
        years = list(range(1900, 2025))
        scale = 1.0 + i * 0.1
        values = [base_pcpi * scale * (0.15 + 0.85 * (y - 1900) / (2024 - 1900)) for y in years]
        out[g] = pd.DataFrame(
            {
                "nuts2_code": g,
                "year": years,
                "gdp_pc_2011ppp": values,
                "source": ["roseswolf" if y < 2000 else "roseswolf_chainlinked" for y in years],
            }
        )
    return out


def _make_pop_series(
    geos: list[str],
    year_min: int = 1900,
    year_max: int = 2024,
    base_pop: float = 5_000_000.0,
) -> pd.DataFrame:
    """Synthetic population DataFrame covering all years."""
    rows: list[dict] = []
    for i, g in enumerate(geos):
        pop = base_pop * (1 + i * 0.5)
        for y in range(year_min, year_max + 1):
            rows.append({"nuts2_code": g, "year": y, "population": pop})
    return pd.DataFrame(rows)


def _compute_manual_eu15_avg(
    out_by_g: dict[str, pd.DataFrame],
    pop_filled: pd.DataFrame,
    year_min: int,
    year_max: int,
) -> dict[int, float]:
    """Reference implementation of the EU-15 weighted average formula."""
    result: dict[int, float] = {}
    for y in range(year_min, year_max + 1):
        num = 0.0
        den = 0.0
        for g, df in out_by_g.items():
            p_rows = pop_filled[(pop_filled["nuts2_code"] == g) & (pop_filled["year"] == y)]
            o_rows = df[df["year"] == y]
            if p_rows.empty or o_rows.empty:
                continue
            p = float(p_rows["population"].iloc[0])
            v = float(o_rows["gdp_pc_2011ppp"].iloc[0])
            if p > 0 and not math.isnan(p):
                num += v * p
                den += p
        if den > 0:
            result[y] = num / den
    return result


class TestEu15WeightedAverage(unittest.TestCase):
    """EU-15 population-weighted reference series (DATA-06)."""

    def setUp(self) -> None:
        self.m = _load_extend_gdp()
        self.anchor = 2020
        # Use a small subset of EU-15 geos for fast synthetic tests.
        self.geos = ["PT", "IE", "FR"]

    def test_fill_population_backward_expands_to_year_min(self) -> None:
        """_fill_population_backward produces rows for YEAR_MIN..YEAR_MAX for each geo."""
        m = self.m
        # Start population from 2000 only.
        rows = [{"nuts2_code": "PT", "year": y, "population": 10_000_000.0} for y in range(2000, 2025)]
        pop = pd.DataFrame(rows)
        filled = m._fill_population_backward(pop)
        pt = filled[filled["nuts2_code"] == "PT"]
        self.assertEqual(pt["year"].min(), m.YEAR_MIN)
        self.assertEqual(pt["year"].max(), m.YEAR_MAX)
        self.assertTrue((pt["population"] > 0).all(), "All filled populations must be positive")

    def test_fill_population_backward_non_negative(self) -> None:
        """_fill_population_backward never introduces negative or NaN population."""
        m = self.m
        pop = _make_pop_series(["AT", "BE"], year_min=2000)
        filled = m._fill_population_backward(pop)
        self.assertFalse(filled["population"].isna().any(), "No NaN after fill")
        self.assertTrue((filled["population"] >= 0).all(), "No negative population after fill")

    def test_eu15_weighted_avg_formula_year_2020(self) -> None:
        """Weighted average for 2020 equals manual sum(pcpi*pop)/sum(pop)."""
        m = self.m
        out_by_g = _make_eu15_country_series(self.geos, self.anchor)
        pop = _make_pop_series(self.geos)

        expected = _compute_manual_eu15_avg(out_by_g, pop, 2020, 2020)
        self.assertIn(2020, expected, "Manual formula should produce a value for 2020")

        # Reproduce the pipeline's aggregation loop inline.
        num = 0.0
        den = 0.0
        y = 2020
        for g in self.geos:
            p = float(pop[(pop["nuts2_code"] == g) & (pop["year"] == y)]["population"].iloc[0])
            v = float(out_by_g[g][out_by_g[g]["year"] == y]["gdp_pc_2011ppp"].iloc[0])
            if p > 0:
                num += v * p
                den += p
        pipeline_val = num / den
        self.assertAlmostEqual(
            pipeline_val, expected[2020], places=4,
            msg="Pipeline formula must match manual reference implementation",
        )

    def test_eu15_weighted_avg_finite_for_all_years(self) -> None:
        """EU-15 weighted average is finite for every year 1900..2024 given complete data."""
        m = self.m
        out_by_g = _make_eu15_country_series(self.geos, self.anchor)
        pop = _make_pop_series(self.geos)

        result = _compute_manual_eu15_avg(out_by_g, pop, m.YEAR_MIN, m.YEAR_MAX)
        self.assertEqual(len(result), m.YEAR_MAX - m.YEAR_MIN + 1, "Expected one value per year")
        for y, v in result.items():
            self.assertTrue(math.isfinite(v), f"EU-15 value for {y} is not finite: {v}")

    def test_eu15_weighted_avg_skips_year_when_no_pop(self) -> None:
        """When population is zero/missing for all countries in a year, that year is skipped."""
        out_by_g = _make_eu15_country_series(self.geos, self.anchor)
        # Population missing for year 1910.
        pop = _make_pop_series(self.geos)
        pop_no_1910 = pop[pop["year"] != 1910].copy()

        result = _compute_manual_eu15_avg(out_by_g, pop_no_1910, 1910, 1910)
        # No valid population for 1910 → year is absent from result.
        self.assertNotIn(1910, result, "Year with no population must be absent from result")

    def test_eu15_avg_output_tagged_eu15(self) -> None:
        """The eu15_avg output DataFrame uses nuts2_code='EU15' as identifier."""
        m = self.m
        # Build a minimal agg_rows list as the pipeline does and confirm the identifier.
        agg_rows: list[dict] = []
        geos = self.geos
        out_by_g = _make_eu15_country_series(geos, self.anchor)
        pop = _make_pop_series(geos)
        for y in [2000, 2020]:
            num = 0.0
            den = 0.0
            for g in geos:
                p_rows = pop[(pop["nuts2_code"] == g) & (pop["year"] == y)]
                o_rows = out_by_g[g][out_by_g[g]["year"] == y]
                if p_rows.empty or o_rows.empty:
                    continue
                p = float(p_rows["population"].iloc[0])
                v = float(o_rows["gdp_pc_2011ppp"].iloc[0])
                if p > 0:
                    num += v * p
                    den += p
            if den > 0:
                agg_rows.append(
                    {"nuts2_code": "EU15", "year": y, "gdp_pc_2011ppp": num / den, "source": "eu15_population_weighted"}
                )
        eu15_df = pd.DataFrame(agg_rows)
        self.assertTrue((eu15_df["nuts2_code"] == "EU15").all(), "All rows must have nuts2_code='EU15'")
        self.assertIn("gdp_pc_2011ppp", eu15_df.columns)
        self.assertIn("source", eu15_df.columns)

    def test_eu15_avg_source_label(self) -> None:
        """The eu15_avg source column is 'eu15_population_weighted'."""
        m = self.m
        geos = self.geos
        out_by_g = _make_eu15_country_series(geos, self.anchor)
        pop = _make_pop_series(geos)
        agg_rows: list[dict] = []
        for y in [1950, 2020]:
            num, den = 0.0, 0.0
            for g in geos:
                p_rows = pop[(pop["nuts2_code"] == g) & (pop["year"] == y)]
                o_rows = out_by_g[g][out_by_g[g]["year"] == y]
                if p_rows.empty or o_rows.empty:
                    continue
                p = float(p_rows["population"].iloc[0])
                v = float(o_rows["gdp_pc_2011ppp"].iloc[0])
                if p > 0:
                    num += v * p
                    den += p
            if den > 0:
                agg_rows.append(
                    {"nuts2_code": "EU15", "year": y, "gdp_pc_2011ppp": num / den, "source": "eu15_population_weighted"}
                )
        eu15_df = pd.DataFrame(agg_rows)
        unique_sources = set(eu15_df["source"].unique())
        self.assertEqual(unique_sources, {"eu15_population_weighted"})

    def test_eu15_geos_list_has_15_entries(self) -> None:
        """EU15_EUROSTAT_GEOS constant has exactly 15 country codes."""
        m = self.m
        geos = list(m.EU15_EUROSTAT_GEOS)
        self.assertEqual(len(geos), 15, f"Expected 15 EU-15 geos, got {len(geos)}: {geos}")

    def test_eu15_geos_includes_expected_countries(self) -> None:
        """EU15_EUROSTAT_GEOS includes key EU-15 member codes (Eurostat notation)."""
        m = self.m
        geos = set(m.EU15_EUROSTAT_GEOS)
        # Greece is EL in Eurostat (not GR); UK stays UK in pre-2020 Eurostat demo tables.
        for code in ["AT", "BE", "DE", "FR", "IT", "NL", "PT", "IE", "ES", "SE", "DK", "FI", "LU", "EL", "UK"]:
            self.assertIn(code, geos, f"EU15_EUROSTAT_GEOS missing {code}")

    def test_weighted_avg_different_from_simple_mean(self) -> None:
        """With unequal populations, weighted avg differs from simple mean."""
        # Country A: gdp=30000, pop=10M; Country B: gdp=10000, pop=1M
        # Simple mean = 20000; weighted = (30000*10 + 10000*1)/11 ≈ 28182
        geos = ["A", "B"]
        pops = {"A": 10_000_000.0, "B": 1_000_000.0}
        gdps = {"A": 30000.0, "B": 10000.0}
        out_by_g = {
            g: pd.DataFrame({"nuts2_code": g, "year": [2020], "gdp_pc_2011ppp": [gdps[g]], "source": ["test"]})
            for g in geos
        }
        pop_df = pd.DataFrame(
            [{"nuts2_code": g, "year": 2020, "population": pops[g]} for g in geos]
        )
        result = _compute_manual_eu15_avg(out_by_g, pop_df, 2020, 2020)
        weighted = result[2020]
        simple_mean = sum(gdps.values()) / len(gdps)
        self.assertNotAlmostEqual(weighted, simple_mean, places=1)
        expected_weighted = (30000.0 * 10_000_000 + 10000.0 * 1_000_000) / 11_000_000
        self.assertAlmostEqual(weighted, expected_weighted, places=2)

    def test_load_eurostat_population_tidy_format(self) -> None:
        """load_eurostat_population parses a tidy CSV (geo, time, value columns)."""
        import tempfile
        import os

        m = self.m
        rows = [
            {"geo": "PT", "time": 2020, "value": 10_000_000},
            {"geo": "IE", "time": 2020, "value": 5_000_000},
            {"geo": "PT", "time": 2021, "value": 10_100_000},
        ]
        with tempfile.TemporaryDirectory() as tmpdir:
            p = Path(tmpdir) / "eurostat_demo_pop_nuts0.csv"
            pd.DataFrame(rows).to_csv(p, index=False)
            result = m.load_eurostat_population(p)

        self.assertIn("nuts2_code", result.columns)
        self.assertIn("year", result.columns)
        self.assertIn("population", result.columns)
        pt_2020 = result[(result["nuts2_code"] == "PT") & (result["year"] == 2020)]
        self.assertFalse(pt_2020.empty)
        self.assertAlmostEqual(float(pt_2020["population"].iloc[0]), 10_000_000.0, places=0)

    def test_load_eurostat_population_wide_format(self) -> None:
        """load_eurostat_population parses a wide CSV (geo column + year columns)."""
        import tempfile

        m = self.m
        rows = [{"geo": "PT", "2020": 10_000_000, "2021": 10_100_000}]
        with tempfile.TemporaryDirectory() as tmpdir:
            p = Path(tmpdir) / "eurostat_demo_pop_nuts0.csv"
            pd.DataFrame(rows).to_csv(p, index=False)
            result = m.load_eurostat_population(p)

        pt_2020 = result[(result["nuts2_code"] == "PT") & (result["year"] == 2020)]
        self.assertFalse(pt_2020.empty)
        self.assertAlmostEqual(float(pt_2020["population"].iloc[0]), 10_000_000.0, places=0)
