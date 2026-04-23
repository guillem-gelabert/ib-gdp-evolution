"""02-01 Task 3: Act II series routing (DATA-02)."""
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


class TestAct2Routing(unittest.TestCase):
    def test_routing_nuts0_portugal(self) -> None:
        m = _load_extend_gdp()
        specs = m.act2_series_list()
        pt = next(s for s in specs if s.key == "pt")
        info = m.act2_routing_info(pt)
        self.assertEqual(info["scope"], "nuts0")
        self.assertEqual(info["eurostat_geo"], "PT")
        self.assertEqual(info["ine_code"], None)

    def test_routing_nuts2_extremadura(self) -> None:
        m = _load_extend_gdp()
        ex = next(s for s in m.act2_series_list() if s.key == "extremadura")
        info = m.act2_routing_info(ex)
        self.assertEqual(info["ine_code"], "ES43")
        self.assertEqual(info["rw_code"], "ES43")

    def test_normalize_lookup(self) -> None:
        m = _load_extend_gdp()
        self.assertEqual(m.normalize_act2_lookup_key("  pt  "), "PT")
        self.assertEqual(m.normalize_act2_lookup_key("es11"), "ES11")
