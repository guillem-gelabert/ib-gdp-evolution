#!/usr/bin/env python3
"""One-off chart: GDP per capita vs tourist arrivals, indexed to 100 in 1900."""
from __future__ import annotations

import csv
from pathlib import Path

import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "public" / "data" / "indexed_growth_1900.csv"
OUT = ROOT / "output" / "indexed_growth_1900.png"


def main() -> None:
    years: list[int] = []
    gdppc: list[float] = []
    tourists: list[float] = []
    with SRC.open() as f:
        for r in csv.DictReader(f):
            years.append(int(r["year"]))
            gdppc.append(float(r["gdppc"]))
            tourists.append(float(r["tourists"]))

    GDP_COLOR = "#660000"
    TOURIST_COLOR = "#1f6feb"

    fig, ax_gdp = plt.subplots(figsize=(11, 6))
    ax_tour = ax_gdp.twinx()

    (gdp_line,) = ax_gdp.plot(years, gdppc, label="GDP per capita", color=GDP_COLOR, linewidth=2)
    (tour_line,) = ax_tour.plot(years, tourists, label="Tourist arrivals", color=TOURIST_COLOR, linewidth=2)

    ax_gdp.set_xlabel("Year")
    ax_gdp.set_ylabel("GDP per capita (1900 = 100)", color=GDP_COLOR)
    ax_tour.set_ylabel("Tourist arrivals (1900 = 100)", color=TOURIST_COLOR)
    ax_gdp.tick_params(axis="y", colors=GDP_COLOR)
    ax_tour.tick_params(axis="y", colors=TOURIST_COLOR)
    ax_gdp.set_title("Balearic Islands: GDP per capita vs tourist arrivals (indexed, 1900 = 100)")
    ax_gdp.grid(True, linestyle=":", alpha=0.4)
    ax_gdp.legend(handles=[gdp_line, tour_line], loc="upper left", frameon=False)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(OUT, dpi=150)
    print(f"Wrote {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
