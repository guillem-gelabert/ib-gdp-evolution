"""02-01 Task 1: ANCHOR_YEAR default, --anchor-year, seam message."""
from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

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


class TestAnchorYear(unittest.TestCase):
    def test_module_default_anchor(self) -> None:
        m = _load_extend_gdp()
        self.assertEqual(m.ANCHOR_YEAR, 2020)

    def test_parse_args_default_anchor_year(self) -> None:
        m = _load_extend_gdp()
        args = m.parse_args([])
        self.assertEqual(args.anchor_year, 2020)

    def test_parse_args_custom_anchor_year(self) -> None:
        m = _load_extend_gdp()
        args = m.parse_args(["--anchor-year", "2019"])
        self.assertEqual(args.anchor_year, 2019)

    def test_seam_failure_message_uses_active_anchor(self) -> None:
        m = _load_extend_gdp()
        anchor = 2018
        msg = m.seam_failure_message(anchor)
        self.assertIn(str(anchor), msg)
        self.assertNotIn("2022", msg)
