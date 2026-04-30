#!/usr/bin/env python3
"""Build a yearly CSV of GDP per capita and tourist arrivals indexed to 100 in 1900.

Each successive year compounds the year-over-year growth rate from the source data.
GDP per capita anchors are sparse, so we log-linearly interpolate between anchors
(equivalent to a constant CAGR between consecutive anchor years).

Inputs:
  - public/data/balearic_gdp_pc.csv (RW + INE chain-linked, sparse anchor years)
  - data/arrivals_per_year_with_source.csv (yearly tourist arrivals)

Output:
  - public/data/indexed_growth_1900.csv (year, gdppc, tourists)
"""
from __future__ import annotations

import csv
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GDP_CSV = ROOT / "public" / "data" / "balearic_gdp_pc.csv"
ARRIVALS_CSV = ROOT / "data" / "arrivals_per_year_with_source.csv"
OUT_CSV = ROOT / "public" / "data" / "indexed_growth_1900.csv"

START_YEAR = 1900
END_YEAR = 2024


def load_gdp_anchors() -> list[tuple[int, float]]:
    by_year: dict[int, tuple[float, str]] = {}
    with GDP_CSV.open() as f:
        reader = csv.DictReader(f)
        for r in reader:
            year = int(r["year"])
            value = float(r["gdp_pc"])
            source = r["source"]
            if year not in by_year or source == "INE":
                by_year[year] = (value, source)
    return sorted((y, v) for y, (v, _src) in by_year.items())


def gdp_at(year: int, anchors: list[tuple[int, float]]) -> float:
    if year <= anchors[0][0]:
        return anchors[0][1]
    if year >= anchors[-1][0]:
        return anchors[-1][1]
    for (y0, v0), (y1, v1) in zip(anchors, anchors[1:]):
        if y0 <= year <= y1:
            t = (year - y0) / (y1 - y0)
            return math.exp(math.log(v0) + t * (math.log(v1) - math.log(v0)))
    raise RuntimeError(f"unreachable: year {year} outside anchors")


def load_arrivals() -> dict[int, float]:
    out: dict[int, float] = {}
    with ARRIVALS_CSV.open() as f:
        reader = csv.DictReader(f)
        for r in reader:
            out[int(r["year"])] = float(r["arrivals"])
    return out


def main() -> None:
    anchors = load_gdp_anchors()
    arrivals = load_arrivals()

    gdp_base = gdp_at(START_YEAR, anchors)
    tourists_base = arrivals[START_YEAR]

    rows: list[tuple[int, float, float]] = []
    for y in range(START_YEAR, END_YEAR + 1):
        g = gdp_at(y, anchors) / gdp_base * 100.0
        if y not in arrivals:
            continue
        t = arrivals[y] / tourists_base * 100.0
        rows.append((y, g, t))

    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with OUT_CSV.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["year", "gdppc", "tourists"])
        for y, g, t in rows:
            w.writerow([y, f"{g:.4f}", f"{t:.4f}"])

    print(f"Wrote {len(rows)} rows → {OUT_CSV.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
