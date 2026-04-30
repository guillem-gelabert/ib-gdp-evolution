#!/usr/bin/env python3
"""Find Spanish regions and countries whose GDP-pc curve is closest to the Balearic Islands (ES53).

Loads the full Rosés-Wolf v7 workbook (A1b GDP per capita 2011 PPP + A3 population),
log-interpolates sparse anchors to annual series, then ranks by Pearson r of **year-over-year
fractional growth** (v_t/v_{t-1} − 1) **for calendar years 1900-1990 only** (growth pairs
1901..1990), never levels or the 1900 index.

Outputs:
  - public/data/closest_curves_ranking.csv      (top lists + full rankings)
  - public/data/closest_curves.csv              (indexed: 1900 = 100)
  - public/data/closest_curves_absolute.csv     (2011 PPP $ per year)
  - output/closest_curves.png                   (indexed chart, x-axis 1900-1990)
  - output/closest_curves_absolute.png          (absolute GDP pc chart, x-axis 1900-1990)
"""
from __future__ import annotations

import csv
import math
import re
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
RW_PATH = ROOT / "data" / "roseswolf_regionalgdp_v7.xlsx"
SHEET_GDP = "A1b Regional GDP (2011PPP)"
SHEET_POP = "A3 Population"
OUT_RANKING = ROOT / "public" / "data" / "closest_curves_ranking.csv"
OUT_CSV = ROOT / "public" / "data" / "closest_curves.csv"
OUT_CSV_ABSOLUTE = ROOT / "public" / "data" / "closest_curves_absolute.csv"
OUT_PNG = ROOT / "output" / "closest_curves.png"
OUT_PNG_ABSOLUTE = ROOT / "output" / "closest_curves_absolute.png"

START_YEAR = 1900
END_YEAR = 2022
# Pearson r uses YoY growth g_y = v_y/v_{y-1}-1 only for y in (CORR_GROWTH_FROM, CORR_GROWTH_TO]
CORR_GROWTH_FROM = 1900
CORR_GROWTH_TO = 1990
REF_CODE = "ES53"
REF_LABEL = "Illes Balears (ES53)"
SPAIN_COUNTRY = "Spain"
TOP_N = 5


def log_interpolate(anchors: list[tuple[int, float]], year: int) -> float:
    if not anchors:
        return float("nan")
    if year <= anchors[0][0]:
        return anchors[0][1]
    if year >= anchors[-1][0]:
        return anchors[-1][1]
    for (y0, v0), (y1, v1) in zip(anchors, anchors[1:]):
        if y0 <= year <= y1:
            t = (year - y0) / (y1 - y0)
            return math.exp(math.log(v0) + t * (math.log(v1) - math.log(v0)))
    return anchors[-1][1]


def year_columns(df: pd.DataFrame) -> list[str]:
    cols: list[str] = []
    for c in df.columns:
        s = str(c).strip()
        if re.fullmatch(r"\d{4}", s):
            cols.append(c)
    return cols


def is_aggregate_code(code: object) -> bool:
    return "+" in str(code)


def parse_float(v: object) -> float | None:
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return None
    if isinstance(v, str):
        t = v.strip()
        if t in {"", ".", "..", "-", "—"}:
            return None
    try:
        x = float(v)
    except (TypeError, ValueError):
        return None
    if math.isnan(x):
        return None
    return x


def annual_from_row(row: pd.Series, ycols: list[str]) -> dict[int, float]:
    anchors: list[tuple[int, float]] = []
    for c in ycols:
        v = row[c]
        fv = parse_float(v)
        if fv is not None and fv > 0:
            y = int(float(str(c).strip()))
            anchors.append((y, fv))
    anchors.sort(key=lambda x: x[0])
    if len(anchors) < 2:
        return {}
    return {y: log_interpolate(anchors, y) for y in range(START_YEAR, END_YEAR + 1)}


def index_to_1900(series: dict[int, float]) -> dict[int, float]:
    """Scale each year so START_YEAR equals 100 (1900 = 100% of base level)."""
    base = series.get(START_YEAR)
    if base is None or base <= 0:
        return {}
    return {y: v / base * 100.0 for y, v in series.items()}


def pearson_yoy_growth(a: dict[int, float], b: dict[int, float]) -> float:
    """Pearson r between aligned **year-over-year growth rates** only (not levels).

    Growth is fractional change g_y = v_y / v_{y-1} − 1 on the real GDP-pc series, for
    y from CORR_GROWTH_FROM+1 through CORR_GROWTH_TO (inclusive), i.e. 1901-1990.
    Re-basing to 1900=100 would not change these ratios, so this is independent of index charts.
    """
    ra: list[float] = []
    rb: list[float] = []
    for y in range(CORR_GROWTH_FROM + 1, CORR_GROWTH_TO + 1):
        y0 = y - 1
        if y0 not in a or y not in a or y0 not in b or y not in b:
            continue
        v0a, v1a = a[y0], a[y]
        v0b, v1b = b[y0], b[y]
        if min(v0a, v1a, v0b, v1b) <= 0:
            continue
        ra.append(v1a / v0a - 1.0)
        rb.append(v1b / v0b - 1.0)
    if len(ra) < 10 or np.std(ra) == 0 or np.std(rb) == 0:
        return float("nan")
    return float(np.corrcoef(ra, rb)[0, 1])


def load_rw_frames() -> tuple[pd.DataFrame, pd.DataFrame, list[str]]:
    gdp = pd.read_excel(RW_PATH, sheet_name=SHEET_GDP, header=5)
    pop = pd.read_excel(RW_PATH, sheet_name=SHEET_POP, header=5)
    ycols = year_columns(gdp)
    return gdp, pop, ycols


def build_pop_lookup(pop: pd.DataFrame, ycols: list[str]) -> dict[tuple[str, str], float]:
    out: dict[tuple[str, str], float] = {}
    for _, row in pop.iterrows():
        if is_aggregate_code(row.get("NUTS-Codes", "")):
            continue
        code = str(row["NUTS-Codes"]).strip().upper()
        for c in ycols:
            v = row[c]
            fv = parse_float(v)
            if fv is not None and fv > 0:
                out[(code, str(c).strip())] = fv
    return out


def country_weighted_series(
    gdp: pd.DataFrame,
    pop_lookup: dict[tuple[str, str], float],
    ycols: list[str],
    country: str,
) -> dict[int, float]:
    sub = gdp[(gdp["Country (current borders)"] == country) & (~gdp["NUTS-Codes"].map(is_aggregate_code))]
    if sub.empty:
        return {}
    out_yearly: dict[int, float] = {}
    for c in ycols:
        num = 0.0
        den = 0.0
        ckey = str(c).strip()
        for _, row in sub.iterrows():
            code = str(row["NUTS-Codes"]).strip().upper()
            g = row[c]
            p = pop_lookup.get((code, ckey))
            gv = parse_float(g)
            if gv is not None and gv > 0 and p is not None and p > 0:
                num += gv * p
                den += p
        if den > 0:
            y = int(float(ckey))
            out_yearly[y] = num / den
    years_sorted = sorted(out_yearly.keys())
    if len(years_sorted) < 2:
        return {}
    anchors = [(y, out_yearly[y]) for y in years_sorted]
    return {y: log_interpolate(anchors, y) for y in range(START_YEAR, END_YEAR + 1)}


def main() -> None:
    if not RW_PATH.exists():
        raise SystemExit(f"Missing RW workbook: {RW_PATH}")

    gdp, pop, ycols = load_rw_frames()
    pop_lookup = build_pop_lookup(pop, ycols)

    ref_row = gdp[gdp["NUTS-Codes"].astype(str).str.strip().str.upper() == REF_CODE]
    if ref_row.empty:
        raise SystemExit(f"Reference region {REF_CODE} not found in {SHEET_GDP}")
    ref_series = annual_from_row(ref_row.iloc[0], ycols)
    if not ref_series:
        raise SystemExit("Could not build reference annual series")

    # --- Per-region (single NUTS, no aggregates) ---
    region_rows: list[dict[str, object]] = []
    for _, row in gdp.iterrows():
        if is_aggregate_code(row.get("NUTS-Codes")):
            continue
        code = str(row["NUTS-Codes"]).strip().upper()
        label = str(row.get("Region", code))
        country = str(row.get("Country (current borders)", ""))
        s = annual_from_row(row, ycols)
        if not s:
            continue
        r = pearson_yoy_growth(ref_series, s)
        region_rows.append({
            "kind": "region",
            "code": code,
            "label": label,
            "country": country,
            "r": r,
            "series": s,
        })

    # --- Countries (population-weighted; exclude Spain from country ranking) ---
    countries = sorted(gdp["Country (current borders)"].dropna().unique())
    country_rows: list[dict[str, object]] = []
    for ctry in countries:
        if ctry == SPAIN_COUNTRY:
            continue
        s = country_weighted_series(gdp, pop_lookup, ycols, ctry)
        if not s:
            continue
        r = pearson_yoy_growth(ref_series, s)
        country_rows.append({
            "kind": "country",
            "code": ctry,
            "label": ctry,
            "country": ctry,
            "r": r,
            "series": s,
        })

    es_regions = [x for x in region_rows if str(x["code"]).startswith("ES") and x["code"] != REF_CODE]
    es_regions_valid = [x for x in es_regions if not math.isnan(float(x["r"]))]

    es_sorted = sorted(es_regions_valid, key=lambda x: float(x["r"]), reverse=True)
    co_sorted = sorted(
        [x for x in country_rows if not math.isnan(float(x["r"]))],
        key=lambda x: float(x["r"]),
        reverse=True,
    )

    top_es = es_sorted[:TOP_N]
    top_co = co_sorted[:TOP_N]

    OUT_RANKING.parent.mkdir(parents=True, exist_ok=True)
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    OUT_PNG.parent.mkdir(parents=True, exist_ok=True)

    with OUT_RANKING.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["bucket", "rank", "id", "label", "r_yoy_growth_vs_ib_1900_1990"])
        for i, row in enumerate(top_es, start=1):
            w.writerow(["top5_spanish_ccaa", i, row["code"], row["label"], f"{float(row['r']):.6f}"])
        for i, row in enumerate(top_co, start=1):
            w.writerow(["top5_country", i, row["code"], row["label"], f"{float(row['r']):.6f}"])
        w.writerow([])
        w.writerow(["# all_spanish_ccaa_ranked"])
        w.writerow(["rank", "code", "label", "r_yoy_growth_vs_ib_1900_1990"])
        for i, row in enumerate(es_sorted, start=1):
            w.writerow([i, row["code"], row["label"], f"{float(row['r']):.6f}"])
        w.writerow([])
        w.writerow(["# all_countries_ranked_ex_spain"])
        w.writerow(["rank", "country", "r_yoy_growth_vs_ib_1900_1990"])
        for i, row in enumerate(co_sorted, start=1):
            w.writerow([i, row["code"], f"{float(row['r']):.6f}"])

    # --- Wide CSV + chart: index 1900 = 100 (relative growth from base year) ---
    plot_keys: list[tuple[str, dict[int, float]]] = [(REF_LABEL, ref_series)]
    for row in top_es:
        plot_keys.append((f"{row['label']} ({row['code']})", row["series"]))  # type: ignore[arg-type]
    for row in top_co:
        plot_keys.append((f"{row['label']} (avg)", row["series"]))  # type: ignore[arg-type]

    plot_indexed: list[tuple[str, dict[int, float]]] = [
        (name, index_to_1900(ser)) for name, ser in plot_keys
    ]

    years = list(range(START_YEAR, END_YEAR + 1))
    with OUT_CSV.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["year"] + [k for k, _ in plot_indexed])
        for y in years:
            w.writerow([y] + [f"{ser[y]:.4f}" for _, ser in plot_indexed])

    with OUT_CSV_ABSOLUTE.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["year"] + [k for k, _ in plot_keys])
        for y in years:
            w.writerow([y] + [f"{ser[y]:.4f}" for _, ser in plot_keys])

    print(f"Wrote {OUT_RANKING.relative_to(ROOT)}")
    print(f"Wrote {OUT_CSV.relative_to(ROOT)}")
    print(f"Wrote {OUT_CSV_ABSOLUTE.relative_to(ROOT)}")

    print(f"\nTop {TOP_N} Spanish regions (vs {REF_CODE}):")
    for i, row in enumerate(top_es, 1):
        print(f"  {i}. {row['label']} ({row['code']})  r={float(row['r']):.4f}")
    print(f"\nTop {TOP_N} countries (population-weighted NUTS, excl. {SPAIN_COUNTRY}):")
    for i, row in enumerate(top_co, 1):
        print(f"  {i}. {row['label']}  r={float(row['r']):.4f}")

    # --- Charts (colour + linestyle; right-end labels) ---
    CREAM = "#FFFDF5"
    INK = "#1a1a1a"
    ACCENT = "#660000"
    RULE = "#d4c5a9"
    MUTED = "#8a7e6b"

    warm = ["#c4883c", "#d4a574", "#b85c38", "#e8a060", "#a0522d"]
    cool = ["#4a7c9b", "#5c8aab", "#6b9e8f", "#7b8aab", "#5a7a9e"]

    OTHER_LINE_STYLES: list[str | tuple[float, tuple[float, ...]]] = [
        "--",
        "-.",
        ":",
        (0, (8, 4)),
        (0, (12, 2, 2, 2)),
        (0, (4, 2, 1, 2)),
        (0, (1, 1.2)),
        (0, (14, 4)),
        (0, (6, 2, 1, 2, 1, 2)),
        (0, (10, 2, 2, 2)),
    ]

    def render_chart(
        plot_series: list[tuple[str, dict[int, float]]],
        out_path: Path,
        *,
        chart_title: str,
        y_axis_label: str,
        y_major_formatter: plt.FuncFormatter,
    ) -> None:
        chart_years = list(range(CORR_GROWTH_FROM, CORR_GROWTH_TO + 1))
        label_year = CORR_GROWTH_TO

        plt.rcParams.update({
            "font.family": "monospace",
            "axes.labelcolor": INK,
            "xtick.color": MUTED,
            "ytick.color": MUTED,
        })

        fig, ax = plt.subplots(figsize=(14, 7))
        fig.patch.set_facecolor(CREAM)
        ax.set_facecolor(CREAM)

        def _end_label(text: str, color: str, y_end: float) -> None:
            ax.annotate(
                text,
                xy=(label_year, y_end),
                xytext=(5, 0),
                textcoords="offset points",
                ha="left",
                va="center",
                fontsize=7,
                color=color,
                clip_on=False,
                zorder=30,
            )

        for i, (name, ser) in enumerate(plot_series):
            vals = [ser[y] for y in chart_years]
            y_end = float(ser[label_year])
            if i == 0:
                ax.plot(
                    chart_years,
                    vals,
                    color=ACCENT,
                    linewidth=2.8,
                    linestyle="-",
                    solid_capstyle="round",
                    label=name,
                    zorder=20,
                )
                _end_label(name, ACCENT, y_end)
                continue
            orig = plot_keys[i][1]
            r_ib = pearson_yoy_growth(ref_series, orig)
            rr = float(r_ib) if not math.isnan(r_ib) else 0.0
            ls = OTHER_LINE_STYLES[(i - 1) % len(OTHER_LINE_STYLES)]
            if 1 <= i <= TOP_N:
                col = warm[(i - 1) % len(warm)]
            else:
                col = cool[(i - 1 - TOP_N) % len(cool)]
            leg = f"{name}  (r_growth={rr:.2f})"
            ax.plot(
                chart_years,
                vals,
                color=col,
                linewidth=1.55,
                linestyle=ls,
                alpha=0.92,
                label=leg,
            )
            _end_label(name, col, y_end)

        ax.set_ylabel(y_axis_label, fontsize=11, color=MUTED)
        ax.set_title(chart_title, fontsize=15, fontfamily="serif", color=INK, pad=14)
        ax.legend(loc="upper left", fontsize=8, framealpha=0.92, edgecolor=RULE)
        ax.yaxis.set_major_formatter(y_major_formatter)
        ax.grid(axis="y", color=RULE, linewidth=0.5, alpha=0.6)
        ax.set_xlim(CORR_GROWTH_FROM, CORR_GROWTH_TO)
        for spine in ax.spines.values():
            spine.set_visible(False)
        ax.tick_params(length=0)

        fig.tight_layout()
        fig.subplots_adjust(right=0.72)
        fig.savefig(out_path, dpi=150, bbox_inches="tight", pad_inches=0.15)
        plt.close(fig)
        print(f"Wrote {out_path.relative_to(ROOT)}")

    corr_note = f"r = YoY growth correlation ({CORR_GROWTH_FROM}-{CORR_GROWTH_TO})"
    render_chart(
        plot_indexed,
        OUT_PNG,
        chart_title=(
            "Relative GDP/cap growth vs the Balearic Islands (1900 = 100, Rosés–Wolf v7)\n"
            f"{corr_note}"
        ),
        y_axis_label="Index (1900 = 100)",
        y_major_formatter=plt.FuncFormatter(lambda x, _: f"{x:.0f}"),
    )
    render_chart(
        plot_keys,
        OUT_PNG_ABSOLUTE,
        chart_title=f"GDP per capita in 2011 PPP $ (Rosés–Wolf v7)\n{corr_note}",
        y_axis_label="GDP per capita (2011 PPP $)",
        y_major_formatter=plt.FuncFormatter(lambda x, _: f"{x / 1000:.0f}k"),
    )


if __name__ == "__main__":
    main()
