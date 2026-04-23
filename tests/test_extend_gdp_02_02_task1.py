"""02-02 Task 1: load_ine_excel and filter_ccaa for combined Spain CCAA file (D-03)."""
from __future__ import annotations

import importlib.util
import io
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


def _make_ine_wide_xlsx(tmp: Path) -> Path:
    """Wide format: ccaa_code + year columns (e.g. 2000, 2001, ..., 2010)."""
    years = list(range(2000, 2011))
    rows = [
        {"ccaa": code, **{str(y): 10000 + idx * 1000 + (y - 2000) * 100 for y in years}}
        for idx, code in enumerate(["ES53", "ES43", "ES11", "ES42"])
    ]
    df = pd.DataFrame(rows)
    p = tmp / "ine_wide.xlsx"
    df.to_excel(p, index=False)
    return p


def _make_ine_tidy_xlsx(tmp: Path) -> Path:
    """Tidy format: ccaa_code, year, value columns."""
    years = list(range(2000, 2011))
    rows = [
        {"ccaa": code, "year": y, "value": 10000 + idx * 1000 + (y - 2000) * 100}
        for idx, code in enumerate(["ES53", "ES43", "ES11", "ES42"])
        for y in years
    ]
    df = pd.DataFrame(rows)
    p = tmp / "ine_tidy.xlsx"
    df.to_excel(p, index=False)
    return p


class TestLoadIneExcel(unittest.TestCase):
    def test_ine_filename_constant_is_documented(self) -> None:
        """INE_CCAA_FILENAME must be set and reference the expected xlsx name."""
        m = _load_extend_gdp()
        self.assertTrue(hasattr(m, "INE_CCAA_FILENAME"), "INE_CCAA_FILENAME constant missing.")
        self.assertIn("ine", m.INE_CCAA_FILENAME.lower())
        self.assertTrue(m.INE_CCAA_FILENAME.endswith((".xlsx", ".xls")))

    def test_load_ine_excel_wide_format(self) -> None:
        """Wide-format INE Excel: returns ccaa_code, year, value for all CCAA rows."""
        m = _load_extend_gdp()
        with tempfile.TemporaryDirectory() as tmp:
            xlsx = _make_ine_wide_xlsx(Path(tmp))
            df = m.load_ine_excel(xlsx)
        self.assertIn("ccaa_code", df.columns)
        self.assertIn("year", df.columns)
        self.assertIn("value", df.columns)
        codes = set(df["ccaa_code"].unique())
        self.assertEqual(codes, {"ES53", "ES43", "ES11", "ES42"})
        # All years from 2000–2010 present
        for code in ["ES53", "ES43", "ES11", "ES42"]:
            years = set(df[df["ccaa_code"] == code]["year"].astype(int).tolist())
            self.assertTrue(years.issuperset(set(range(2000, 2011))))

    def test_load_ine_excel_tidy_format(self) -> None:
        """Tidy-format INE Excel: same result as wide, different input layout."""
        m = _load_extend_gdp()
        with tempfile.TemporaryDirectory() as tmp:
            xlsx = _make_ine_tidy_xlsx(Path(tmp))
            df = m.load_ine_excel(xlsx)
        self.assertIn("ccaa_code", df.columns)
        codes = set(df["ccaa_code"].unique())
        self.assertEqual(codes, {"ES53", "ES43", "ES11", "ES42"})

    def test_load_ine_excel_raises_on_empty_result(self) -> None:
        """Empty result after parsing raises PipelineError."""
        m = _load_extend_gdp()
        with tempfile.TemporaryDirectory() as tmp:
            # Write an empty-ish file (no CCAA code column)
            df = pd.DataFrame({"a": [1], "b": [2]})
            p = Path(tmp) / "empty.xlsx"
            df.to_excel(p, index=False)
            # Should raise PipelineError due to no valid region code column or empty result
            with self.assertRaises(Exception):
                m.load_ine_excel(p)


class TestFilterCcaa(unittest.TestCase):
    def _sample_ine_df(self) -> "pd.DataFrame":
        m = _load_extend_gdp()
        rows = [
            {"ccaa_code": code, "year": y, "value": 10000 + idx * 1000}
            for idx, code in enumerate(["ES53", "ES43", "ES11", "ES42"])
            for y in [2000, 2001, 2002]
        ]
        return pd.DataFrame(rows)

    def test_filter_ccaa_es53(self) -> None:
        m = _load_extend_gdp()
        df = self._sample_ine_df()
        sub = m.filter_ccaa(df, "ES53")
        self.assertFalse(sub.empty)
        self.assertTrue((sub["ccaa_code"] == "ES53").all())

    def test_filter_ccaa_normalizes_lowercase(self) -> None:
        m = _load_extend_gdp()
        df = self._sample_ine_df()
        sub = m.filter_ccaa(df, "es53")
        self.assertFalse(sub.empty)
        self.assertTrue((sub["ccaa_code"] == "ES53").all())

    def test_filter_ccaa_missing_code_returns_empty(self) -> None:
        m = _load_extend_gdp()
        df = self._sample_ine_df()
        sub = m.filter_ccaa(df, "ZZZZ")
        self.assertTrue(sub.empty)

    def test_filter_ccaa_target_codes_all_present(self) -> None:
        """All four target CCAA (ES53, ES43, ES11, ES42) can be filtered independently."""
        m = _load_extend_gdp()
        df = self._sample_ine_df()
        for code in ["ES53", "ES43", "ES11", "ES42"]:
            sub = m.filter_ccaa(df, code)
            self.assertFalse(sub.empty, f"filter_ccaa should return rows for {code}")


if __name__ == "__main__":
    unittest.main()
