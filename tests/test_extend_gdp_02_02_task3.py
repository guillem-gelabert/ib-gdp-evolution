"""02-02 Task 3: INE file not found raises PipelineError with actionable message."""
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


class TestIneFileBlocker(unittest.TestCase):
    """Task 3: Missing INE file fails fast with actionable error text (D-03)."""

    def test_missing_ine_raises_pipeline_error(self) -> None:
        """_find_ine_excel_path raises PipelineError when file is absent."""
        m = _load_extend_gdp()
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            (workspace / "data").mkdir(parents=True)
            (workspace / "public" / "data").mkdir(parents=True)
            with self.assertRaises(m.PipelineError):
                m._find_ine_excel_path(workspace)

    def test_error_message_includes_expected_filename(self) -> None:
        """Error text mentions the expected filename so user knows what to provide."""
        m = _load_extend_gdp()
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            (workspace / "data").mkdir(parents=True)
            (workspace / "public" / "data").mkdir(parents=True)
            try:
                m._find_ine_excel_path(workspace)
                self.fail("Expected PipelineError was not raised.")
            except m.PipelineError as exc:
                msg = str(exc)
                self.assertIn("ine", msg.lower(), "Error must name the INE file")

    def test_error_message_includes_ine_url(self) -> None:
        """Error text includes INE download URL so user knows where to get the file."""
        m = _load_extend_gdp()
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            (workspace / "data").mkdir(parents=True)
            (workspace / "public" / "data").mkdir(parents=True)
            try:
                m._find_ine_excel_path(workspace)
                self.fail("Expected PipelineError was not raised.")
            except m.PipelineError as exc:
                msg = str(exc)
                self.assertIn("ine.es", msg.lower(), "Error must include the INE download URL")

    def test_finds_file_in_data_dir(self) -> None:
        """_find_ine_excel_path resolves when file is placed under data/."""
        m = _load_extend_gdp()
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            data_dir = workspace / "data"
            data_dir.mkdir(parents=True)
            (workspace / "public" / "data").mkdir(parents=True)
            # Place a minimal xlsx at the expected filename
            filename = m.INE_CCAA_FILENAME
            xlsx_path = data_dir / filename
            pd.DataFrame({"ccaa": ["ES53"], "2000": [15000]}).to_excel(xlsx_path, index=False)
            found = m._find_ine_excel_path(workspace)
            self.assertEqual(found, xlsx_path)

    def test_finds_file_in_public_data_dir(self) -> None:
        """_find_ine_excel_path resolves when file is placed under public/data/."""
        m = _load_extend_gdp()
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            (workspace / "data").mkdir(parents=True)
            pub_dir = workspace / "public" / "data"
            pub_dir.mkdir(parents=True)
            filename = m.INE_CCAA_FILENAME
            xlsx_path = pub_dir / filename
            pd.DataFrame({"ccaa": ["ES53"], "2000": [15000]}).to_excel(xlsx_path, index=False)
            found = m._find_ine_excel_path(workspace)
            self.assertEqual(found, xlsx_path)

    def test_find_input_file_also_raises_pipeline_error_for_missing(self) -> None:
        """find_input_file raises PipelineError for arbitrary missing files (generic utility)."""
        m = _load_extend_gdp()
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            (workspace / "data").mkdir(parents=True)
            (workspace / "public" / "data").mkdir(parents=True)
            with self.assertRaises(m.PipelineError):
                m.find_input_file(workspace, "nonexistent_file.xlsx")

    def test_find_input_file_message_names_the_file(self) -> None:
        """find_input_file error message includes the missing filename."""
        m = _load_extend_gdp()
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            (workspace / "data").mkdir(parents=True)
            (workspace / "public" / "data").mkdir(parents=True)
            filename = "some_missing_file.xlsx"
            try:
                m.find_input_file(workspace, filename)
                self.fail("Expected PipelineError.")
            except m.PipelineError as exc:
                self.assertIn(filename, str(exc))


if __name__ == "__main__":
    unittest.main()
