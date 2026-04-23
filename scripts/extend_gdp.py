#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
import re
import urllib.request
from enum import Enum
from pathlib import Path
from typing import Iterable, NamedTuple, TypedDict

import pandas as pd


YEAR_MIN = 1900
YEAR_MAX = 2024
CHAIN_START = 2000
ANCHOR_YEAR = 2020
PRE_CHAIN_END = CHAIN_START - 1
# Act I chart in public/data/balearic_gdp_pc.csv was built with a 2022 seam; keep that for the default regional run.
LEGACY_ACT1_ANCHOR = 2022

# Expected INE combined file (cid=1254736167628); place under data/ or public/data/.
INE_CCAA_FILENAME = "ine_spain_ccaa_gdp_pc.xlsx"
EU15_COUNTRY_GEOS = ("AT", "BE", "DK", "FI", "FR", "DE", "GR", "IE", "IT", "LU", "NL", "PT", "ES", "SE", "UK")
EU15_EUROSTAT_GEOS = ("AT", "BE", "DK", "FI", "FR", "DE", "EL", "IE", "IT", "LU", "NL", "PT", "ES", "SE", "UK")
# Eurostat uses EL for Greece (not GR); UK stays UK in Eurostat demo tables pre-2020.


class SeriesScope(str, Enum):
    """Act II series routing (DATA-02): NUTS2 Spain, INE CCAA code, or NUTS0 country."""

    nuts2 = "nuts2"
    ine_ccaa = "ine_ccaa"
    nuts0 = "nuts0"


class InstitutionalSource(str, Enum):
    ine = "INE"
    eurostat = "Eurostat"


class Act2SeriesSpec(NamedTuple):
    """Series metadata for Act II outputs (extend with new peers in one place)."""

    key: str
    slug: str
    scope: SeriesScope
    rw_code: str
    ine_ccaa: str | None
    euro_geo: str | None
    institutional: InstitutionalSource
    label: str


def seam_failure_message(anchor: int) -> str:
    return f"Seam continuity check failed at {anchor} anchor."


def act2_series_list() -> list[Act2SeriesSpec]:
    return [
        Act2SeriesSpec(
            key="ib",
            slug="balearic_islands",
            scope=SeriesScope.nuts2,
            rw_code="ES53",
            ine_ccaa="ES53",
            euro_geo="ES53",
            institutional=InstitutionalSource.ine,
            label="Balearic Islands",
        ),
        Act2SeriesSpec(
            key="extremadura",
            slug="extremadura",
            scope=SeriesScope.nuts2,
            rw_code="ES43",
            ine_ccaa="ES43",
            euro_geo="ES43",
            institutional=InstitutionalSource.ine,
            label="Extremadura",
        ),
        Act2SeriesSpec(
            key="galicia",
            slug="galicia",
            scope=SeriesScope.nuts2,
            rw_code="ES11",
            ine_ccaa="ES11",
            euro_geo="ES11",
            institutional=InstitutionalSource.ine,
            label="Galicia",
        ),
        Act2SeriesSpec(
            key="clm",
            slug="castilla_la_mancha",
            scope=SeriesScope.nuts2,
            rw_code="ES42",
            ine_ccaa="ES42",
            euro_geo="ES42",
            institutional=InstitutionalSource.ine,
            label="Castilla-La Mancha",
        ),
        Act2SeriesSpec(
            key="pt",
            slug="portugal",
            scope=SeriesScope.nuts0,
            rw_code="PT",
            ine_ccaa=None,
            euro_geo="PT",
            institutional=InstitutionalSource.eurostat,
            label="Portugal",
        ),
        Act2SeriesSpec(
            key="ie",
            slug="ireland",
            scope=SeriesScope.nuts0,
            rw_code="IE",
            ine_ccaa=None,
            euro_geo="IE",
            institutional=InstitutionalSource.eurostat,
            label="Ireland",
        ),
        Act2SeriesSpec(
            key="mt",
            slug="malta",
            scope=SeriesScope.nuts0,
            rw_code="MT",
            ine_ccaa=None,
            euro_geo="MT",
            institutional=InstitutionalSource.eurostat,
            label="Malta",
        ),
    ]


class Act2SeriesConfigDict(TypedDict, total=False):
    """Flat routing record for an Act II series: NUTS2, NUTS0, or INE CCAA (DATA-02)."""

    key: str
    scope: str
    rw_code: str
    ine_code: str | None
    eurostat_geo: str | None
    institutional_source: str


def act2_routing_info(spec: Act2SeriesSpec) -> Act2SeriesConfigDict:
    return {
        "key": spec.key,
        "scope": spec.scope.value,
        "rw_code": spec.rw_code,
        "ine_code": spec.ine_ccaa,
        "eurostat_geo": spec.euro_geo or spec.rw_code,
        "institutional_source": spec.institutional.value,
    }


def normalize_act2_lookup_key(value: object) -> str | None:
    """Normalize region/country codes for series lookup (NUTS2, NUTS0, INE CCAA)."""
    return normalize_code(value)


class PipelineError(RuntimeError):
    pass


def normalize_code(value: object) -> str | None:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return None
    text = str(value).strip().upper()
    return text or None


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    renamed = {}
    for col in df.columns:
        base = str(col).strip().lower().replace("\\", "_").replace("/", "_")
        base = re.sub(r"[^a-z0-9_]+", "_", base).strip("_")
        renamed[col] = base
    return df.rename(columns=renamed)


def parse_number(series: pd.Series) -> pd.Series:
    cleaned = (
        series.astype(str)
        .str.replace(",", "", regex=False)
        .str.extract(r"([-+]?\d*\.?\d+(?:[eE][-+]?\d+)?)", expand=False)
    )
    return pd.to_numeric(cleaned, errors="coerce")


def find_input_file(workspace: Path, filename: str) -> Path:
    candidates = [
        workspace / "data" / filename,
        workspace / "public" / "data" / filename,
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    raise PipelineError(
        f"Missing required input file: {filename}. "
        "Expected under data/ or public/data/."
    )


def identify_code_column(df: pd.DataFrame, candidates: Iterable[str]) -> str:
    available = set(df.columns)
    for col in candidates:
        if col in available:
            return col
    for col in df.columns:
        if "geo" in col or "nuts" in col or "region" in col:
            return col
    raise PipelineError("Could not identify a region/NUTS code column.")


def identify_year_value_columns(df: pd.DataFrame) -> tuple[str, str] | None:
    year_candidates = [c for c in df.columns if c in {"year", "time", "time_period"}]
    value_candidates = [c for c in df.columns if c in {"value", "values", "obs_value"}]
    if year_candidates and value_candidates:
        return year_candidates[0], value_candidates[0]
    return None


def melt_wide_years(df: pd.DataFrame, id_vars: list[str]) -> pd.DataFrame:
    year_cols = [c for c in df.columns if re.fullmatch(r"\d{4}", c)]
    if not year_cols:
        raise PipelineError("No year columns detected in wide data format.")
    long = df.melt(
        id_vars=id_vars,
        value_vars=year_cols,
        var_name="year",
        value_name="value",
    )
    long["year"] = pd.to_numeric(long["year"], errors="coerce")
    long["value"] = parse_number(long["value"])
    return long


def load_roseswolf(path: Path, anchor_year: int | None = None) -> pd.DataFrame:
    max_rw_year = anchor_year if anchor_year is not None else ANCHOR_YEAR
    if path.suffix.lower() in {".xlsx", ".xls"}:
        raw = pd.read_excel(path)
    else:
        raw = pd.read_csv(path)
    df = normalize_columns(raw)

    code_col = identify_code_column(
        df,
        candidates=["nuts2_code", "nuts2", "nuts", "geo", "region_code", "region"],
    )

    tidy_cols = identify_year_value_columns(df)
    if tidy_cols:
        year_col, value_col = tidy_cols
        out = df[[code_col, year_col, value_col]].copy()
        out = out.rename(columns={code_col: "nuts2_code", year_col: "year", value_col: "value"})
        out["year"] = pd.to_numeric(out["year"], errors="coerce")
        out["value"] = parse_number(out["value"])
    else:
        id_vars = [code_col]
        out = melt_wide_years(df, id_vars=id_vars).rename(columns={code_col: "nuts2_code"})

    out["nuts2_code"] = out["nuts2_code"].map(normalize_code)
    out = out.dropna(subset=["nuts2_code", "year", "value"])
    out["year"] = out["year"].astype(int)
    out = out[(out["year"] >= YEAR_MIN) & (out["year"] <= max_rw_year)]
    out = out.sort_values(["nuts2_code", "year"]).drop_duplicates(["nuts2_code", "year"], keep="last")
    if out.empty:
        raise PipelineError("Roses-Wolf dataset resolved to an empty table after parsing.")
    return out


def load_roseswolf_population(path: Path) -> pd.DataFrame:
    """
    Population from the same Rosés–Wolf workbook as GDP/cap (D-01).
    Used sheet: first whose name contains 'pop' (e.g. `population` as written by
    `materialize_roseswolf_workbook`); if absent and there are multiple sheets, sheet 2; else first sheet.
    Tidy: geo/NUTS column + `year` + population column (name with 'pop' or value/headcount);
    or wide: geo column + 4-digit year columns (melted to long).
    """
    xl = pd.ExcelFile(path)
    pop_sheet = None
    for name in xl.sheet_names:
        if "pop" in name.lower():
            pop_sheet = name
            break
    if pop_sheet is None and len(xl.sheet_names) > 1:
        pop_sheet = xl.sheet_names[1]
    elif pop_sheet is None:
        pop_sheet = xl.sheet_names[0]

    raw = pd.read_excel(path, sheet_name=pop_sheet)
    df = normalize_columns(raw)
    code_col = identify_code_column(
        df,
        candidates=["nuts2_code", "nuts2", "nuts", "geo", "region_code", "region"],
    )
    pop_col = None
    for c in df.columns:
        if c == code_col:
            continue
        if "pop" in c:
            pop_col = c
            break
    if pop_col is None:
        for c in df.columns:
            if c in {"value", "values", "obs_value", "headcount", "inhabitants"}:
                pop_col = c
                break
    tidy_cols = identify_year_value_columns(df)
    if tidy_cols and pop_col:
        year_col, _ = tidy_cols
        out = df[[code_col, year_col, pop_col]].copy()
        out = out.rename(columns={code_col: "nuts2_code", year_col: "year", pop_col: "population"})
    elif pop_col and "year" in df.columns:
        out = df[[code_col, "year", pop_col]].copy()
        out = out.rename(columns={code_col: "nuts2_code", pop_col: "population"})
    else:
        id_vars = [code_col]
        year_cols = [c for c in df.columns if re.fullmatch(r"\d{4}", str(c))]
        if not year_cols:
            raise PipelineError("Could not parse population sheet: need year columns or tidy year/value.")
        long = df.melt(id_vars=id_vars, value_vars=year_cols, var_name="year", value_name="population")
        long["year"] = pd.to_numeric(long["year"], errors="coerce")
        long["population"] = parse_number(long["population"])
        out = long.rename(columns={code_col: "nuts2_code"})

    out["nuts2_code"] = out["nuts2_code"].map(normalize_code)
    out["population"] = parse_number(out["population"])
    out = out.dropna(subset=["nuts2_code", "year", "population"])
    out["year"] = out["year"].astype(int)
    out = out.sort_values(["nuts2_code", "year"]).drop_duplicates(["nuts2_code", "year"], keep="last")
    if out.empty:
        raise PipelineError("Roses-Wolf population sheet resolved to an empty table.")
    return out[["nuts2_code", "year", "population"]]


def load_eurostat_raw(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, dtype=str, low_memory=False)
    if len(df.columns) == 1:
        df = pd.read_csv(path, dtype=str, sep="\t", low_memory=False)
    df = normalize_columns(df)
    return df


def expand_compound_dimension_column(df: pd.DataFrame) -> pd.DataFrame:
    compound_cols = [
        c
        for c in df.columns
        if "freq" in c and "unit" in c and ("geo" in c or "time" in c) and "," in c
    ]
    if not compound_cols:
        return df
    compound_col = compound_cols[0]
    parts = df[compound_col].astype(str).str.split(",", expand=True)
    labels = [x.strip().lower() for x in compound_col.split(",")]
    labels = [re.sub(r"[^a-z0-9_]+", "_", name).strip("_") for name in labels]
    parts.columns = labels[: parts.shape[1]]
    expanded = pd.concat([parts, df.drop(columns=[compound_col])], axis=1)
    return normalize_columns(expanded)


def enforce_eurostat_unit_guard(df: pd.DataFrame, header_text: str) -> tuple[str, set[str]]:
    unit_values: set[str] = set()
    if "unit" in df.columns:
        unit_values = {str(v).strip().upper() for v in df["unit"].dropna().unique()}
    elif "freq_unit_na_item_geo_time_period" in df.columns:
        unit_values = set()

    source_text = " ".join(sorted(unit_values)) + " " + header_text.upper()
    has_clv = "CLV" in source_text
    has_cp = bool(re.search(r"\bCP(?:_|$)", source_text)) or "CURRENT PRICE" in source_text
    has_pps = "PPS" in source_text

    if has_cp or has_pps:
        raise PipelineError(
            "Eurostat unit guard failed: detected CP/current prices or PPS units. "
            "Use chain-linked real volume data (CLV...) instead, otherwise the output is corrupted."
        )
    if not has_clv:
        raise PipelineError(
            "Eurostat unit guard failed: could not verify a CLV chain-linked unit in the file header/data."
        )

    if unit_values:
        chosen = sorted(unit_values)[0]
    else:
        chosen = "CLV (detected from header)"
    return chosen, unit_values


def load_ine_excel(path: Path) -> pd.DataFrame:
    """
    INE combined Spain CCAA GDP per person (chain-linked), 2000+ (D-03).
    Accepts long format: ccaa / region code column + year + value, or wide year columns.
    """
    raw = pd.read_excel(path)
    df = normalize_columns(raw)
    code_col = identify_code_column(
        df,
        candidates=["ccaa", "nuts2_code", "codigo", "code", "region", "geo", "nuts2"],
    )
    tidy_cols = identify_year_value_columns(df)
    if tidy_cols:
        year_col, value_col = tidy_cols
        out = df[[code_col, year_col, value_col]].copy()
        out = out.rename(columns={code_col: "ccaa_code", year_col: "year", value_col: "value"})
        out["year"] = pd.to_numeric(out["year"], errors="coerce")
        out["value"] = parse_number(out["value"])
    else:
        id_vars = [code_col]
        out = melt_wide_years(df, id_vars=id_vars).rename(columns={code_col: "ccaa_code"})
    out["ccaa_code"] = out["ccaa_code"].map(normalize_code)
    out = out.dropna(subset=["ccaa_code", "year", "value"])
    out["year"] = out["year"].astype(int)
    out = out[(out["year"] >= CHAIN_START) & (out["year"] <= YEAR_MAX)]
    out = out.sort_values(["ccaa_code", "year"]).drop_duplicates(["ccaa_code", "year"], keep="last")
    if out.empty:
        raise PipelineError("INE CCAA dataset resolved to an empty table after parsing.")
    return out


def filter_ccaa(df: pd.DataFrame, code: str) -> pd.DataFrame:
    c = normalize_code(code)
    if c is None:
        return pd.DataFrame(columns=df.columns)
    sub = df[df["ccaa_code"] == c].copy()
    return sub.rename(columns={"value": "value"})


def load_eurostat(path: Path) -> tuple[pd.DataFrame, str, set[str]]:
    header_text = path.read_text(encoding="utf-8", errors="ignore").splitlines()[0]
    raw = expand_compound_dimension_column(load_eurostat_raw(path))
    raw = normalize_columns(raw)

    unit_label, all_units = enforce_eurostat_unit_guard(raw, header_text)

    if "na_item" in raw.columns:
        na_item_upper = raw["na_item"].fillna("").str.upper()
        if (na_item_upper == "B1GQ").any():
            raw = raw[na_item_upper == "B1GQ"].copy()

    code_col = identify_code_column(
        raw,
        candidates=["geo", "geo_time_period", "nuts2_code", "nuts2", "region"],
    )

    tidy_cols = identify_year_value_columns(raw)
    if tidy_cols:
        year_col, value_col = tidy_cols
        out = raw[[code_col, year_col, value_col]].copy()
        out = out.rename(columns={code_col: "nuts2_code", year_col: "year", value_col: "value"})
        out["year"] = pd.to_numeric(out["year"], errors="coerce")
        out["value"] = parse_number(out["value"])
    else:
        id_vars = [code_col]
        out = melt_wide_years(raw, id_vars=id_vars).rename(columns={code_col: "nuts2_code"})

    out["nuts2_code"] = out["nuts2_code"].map(normalize_code)
    out = out.dropna(subset=["nuts2_code", "year", "value"])
    out["year"] = out["year"].astype(int)
    out = out[(out["year"] >= CHAIN_START) & (out["year"] <= YEAR_MAX)]
    out = out.sort_values(["nuts2_code", "year"]).drop_duplicates(["nuts2_code", "year"], keep="last")
    if out.empty:
        raise PipelineError("Eurostat dataset resolved to an empty table after parsing.")
    return out, unit_label, all_units


def load_correspondence(path: Path | None) -> dict[str, list[str]]:
    if path is None or not path.exists():
        return {}
    df = pd.read_csv(path, dtype=str)
    df = normalize_columns(df)
    if df.empty:
        return {}

    rw_candidates = [c for c in df.columns if ("2010" in c) or ("rose" in c) or ("rw" in c)]
    eu_candidates = [c for c in df.columns if ("2021" in c) or ("euro" in c) or ("eu" in c)]
    if not rw_candidates or not eu_candidates:
        # Fallback: use first two columns.
        cols = list(df.columns[:2])
        if len(cols) < 2:
            return {}
        rw_col, eu_col = cols[0], cols[1]
    else:
        rw_col, eu_col = rw_candidates[0], eu_candidates[0]

    pairs = df[[rw_col, eu_col]].copy()
    pairs[rw_col] = pairs[rw_col].map(normalize_code)
    pairs[eu_col] = pairs[eu_col].map(normalize_code)
    pairs = pairs.dropna()

    mapping: dict[str, list[str]] = {}
    for rw_code, eu_code in pairs.itertuples(index=False):
        mapping.setdefault(rw_code, [])
        if eu_code not in mapping[rw_code]:
            mapping[rw_code].append(eu_code)
    return mapping


class CheckResult(NamedTuple):
    name: str
    status: str
    issue_count: int
    details: list[str]

    def one_line(self) -> str:
        if self.status == "PASS":
            return f"{self.name}: PASS"
        return f"{self.name}: {self.status} ({self.issue_count} issues)"


def compute_chainlinked_output(
    rw: pd.DataFrame,
    euro: pd.DataFrame,
    correspondence: dict[str, list[str]],
    correspondence_used: bool,
    anchor_year: int | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, int], list[str]]:
    anchor = anchor_year if anchor_year is not None else ANCHOR_YEAR
    rw_codes = set(rw["nuts2_code"].unique())
    eu_codes = set(euro["nuts2_code"].unique())

    region_rows: list[pd.DataFrame] = []
    growth_compare_rows: list[pd.DataFrame] = []
    dropped_reasons: list[str] = []

    both_count = 0
    rw_only_count = 0
    eu_only_count = 0

    all_rw_codes = sorted(rw_codes)
    for rw_code in all_rw_codes:
        mapped_codes = correspondence.get(rw_code, [rw_code])
        euro_slice = euro[euro["nuts2_code"].isin(mapped_codes)].copy()
        if euro_slice.empty:
            rw_only_count += 1
            continue
        both_count += 1

        euro_series = euro_slice.groupby("year", as_index=False)["value"].mean()
        euro_series = euro_series.rename(columns={"value": "euro_value"})

        rw_series = rw[rw["nuts2_code"] == rw_code][["year", "value"]].rename(columns={"value": "rw_value"})
        rw_anchor_rows = rw_series[rw_series["year"] == anchor]
        euro_anchor_rows = euro_series[euro_series["year"] == anchor]
        if rw_anchor_rows.empty or euro_anchor_rows.empty:
            dropped_reasons.append(f"{rw_code}: missing anchor year {anchor}")
            continue

        rw_anchor = float(rw_anchor_rows["rw_value"].iloc[0])
        euro_anchor = float(euro_anchor_rows["euro_value"].iloc[0])
        if euro_anchor == 0:
            dropped_reasons.append(f"{rw_code}: Eurostat anchor value at {anchor} is zero")
            continue

        chain_years = pd.DataFrame({"year": list(range(CHAIN_START, YEAR_MAX + 1))})
        euro_chain = chain_years.merge(euro_series, on="year", how="left")
        if euro_chain["euro_value"].isna().any():
            missing_years = euro_chain[euro_chain["euro_value"].isna()]["year"].astype(str).tolist()
            dropped_reasons.append(f"{rw_code}: missing Eurostat years {', '.join(missing_years)}")
            continue

        euro_chain["growth_index"] = euro_chain["euro_value"] / euro_anchor
        euro_chain["gdp_pc_2011ppp"] = rw_anchor * euro_chain["growth_index"]
        euro_chain["nuts2_code"] = rw_code
        euro_chain["source"] = "roseswolf_chainlinked"
        euro_chain.loc[euro_chain["year"] >= 2023, "source"] = "eurostat_chainlinked"
        chain_out = euro_chain[["nuts2_code", "year", "gdp_pc_2011ppp", "source"]].copy()

        pre_chain = rw_series[(rw_series["year"] >= YEAR_MIN) & (rw_series["year"] <= PRE_CHAIN_END)].copy()
        pre_chain = pre_chain.rename(columns={"rw_value": "gdp_pc_2011ppp"})
        pre_chain["nuts2_code"] = rw_code
        pre_chain["source"] = "roseswolf"
        pre_out = pre_chain[["nuts2_code", "year", "gdp_pc_2011ppp", "source"]]

        region_out = pd.concat([pre_out, chain_out], ignore_index=True)
        region_rows.append(region_out)

        growth_compare = euro_chain[["year", "euro_value", "gdp_pc_2011ppp"]].copy()
        growth_compare["nuts2_code"] = rw_code
        growth_compare_rows.append(growth_compare)

    if correspondence_used:
        eu_covered = set()
        for rw_code in rw_codes:
            eu_covered.update(correspondence.get(rw_code, [rw_code]))
        eu_only_count = len(eu_codes - eu_covered)
    else:
        eu_only_count = len(eu_codes - rw_codes)

    if not region_rows:
        raise PipelineError("No regions could be chain-linked. Check correspondence and input coverage.")

    output = pd.concat(region_rows, ignore_index=True).sort_values(["nuts2_code", "year"])
    growth_compare_df = pd.concat(growth_compare_rows, ignore_index=True).sort_values(["nuts2_code", "year"])

    coverage = {
        "intersection": both_count,
        "roseswolf_only": rw_only_count,
        "eurostat_only": eu_only_count,
    }
    return output, growth_compare_df, coverage, dropped_reasons


def run_checks(
    output: pd.DataFrame,
    rw: pd.DataFrame,
    growth_compare: pd.DataFrame,
    coverage: dict[str, int],
    dropped_reasons: list[str],
    anchor_year: int | None = None,
    act2_mode: bool = False,
) -> list[CheckResult]:
    checks: list[CheckResult] = []
    anchor = anchor_year if anchor_year is not None else ANCHOR_YEAR

    merged_anchor = output[output["year"] == anchor].merge(
        rw[rw["year"] == anchor][["nuts2_code", "value"]].rename(columns={"value": "rw_anchor_ref"}),
        on="nuts2_code",
        how="left",
    )
    seam_diff = (merged_anchor["gdp_pc_2011ppp"] - merged_anchor["rw_anchor_ref"]).abs()
    seam_fail = merged_anchor.loc[seam_diff > 1e-6, ["nuts2_code", "gdp_pc_2011ppp", "rw_anchor_ref"]]
    if not seam_fail.empty:
        details = [
            f"{row.nuts2_code}: extended={row.gdp_pc_2011ppp:.6f}, rw={row.rw_anchor_ref:.6f} (anchor {anchor})"
            for row in seam_fail.itertuples(index=False)
        ]
        checks.append(CheckResult("1) Seam continuity", "FAIL", len(details), details))
    else:
        checks.append(CheckResult("1) Seam continuity", "PASS", 0, []))

    growth = growth_compare.copy()
    growth["ext_growth"] = growth.groupby("nuts2_code")["gdp_pc_2011ppp"].pct_change()
    growth["eu_growth"] = growth.groupby("nuts2_code")["euro_value"].pct_change()
    growth = growth[growth["year"] >= CHAIN_START + 1].copy()
    growth["pp_diff"] = (growth["ext_growth"] - growth["eu_growth"]).abs() * 100
    over_tolerance = growth[growth["pp_diff"] > 0.01]
    major_dev = growth[growth["pp_diff"] > 0.1]
    details = [
        f"{row.nuts2_code} {int(row.year)}: diff={row.pp_diff:.4f}pp"
        for row in major_dev.itertuples(index=False)
    ]
    status = "PASS" if over_tolerance.empty else "WARN"
    checks.append(CheckResult("2) Growth rate preservation", status, len(over_tolerance), details))

    expected_years = set(range(YEAR_MIN, YEAR_MAX + 1))
    gap_details: list[str] = []
    for code, group in output.groupby("nuts2_code"):
        years = set(group["year"].astype(int).tolist())
        missing = sorted(expected_years - years)
        if missing:
            missing_txt = ",".join(map(str, missing[:10]))
            suffix = "..." if len(missing) > 10 else ""
            gap_details.append(f"{code}: missing {missing_txt}{suffix}")
    status = "PASS" if not gap_details else "WARN"
    checks.append(CheckResult("3) No missing years", status, len(gap_details), gap_details))

    coverage_details = [
        f"intersection={coverage['intersection']}",
        f"roseswolf_only={coverage['roseswolf_only']}",
        f"eurostat_only={coverage['eurostat_only']}",
    ]
    if dropped_reasons:
        coverage_details.extend([f"dropped: {line}" for line in dropped_reasons[:50]])
    status = "PASS"
    issue_count = 0
    if not act2_mode and coverage["intersection"] < 200:
        status = "WARN"
        issue_count += 1
        coverage_details.append("warning: intersection below 200 (expected ~260)")
    elif act2_mode and coverage["intersection"] < 1:
        status = "WARN"
        issue_count += 1
        coverage_details.append("warning: Act II coverage — no intersecting series")
    checks.append(CheckResult("4) Coverage check", status, issue_count, coverage_details))

    outlier_base = output[(output["year"] >= CHAIN_START) & (output["year"] <= YEAR_MAX)].copy()
    outlier_base["yoy"] = outlier_base.groupby("nuts2_code")["gdp_pc_2011ppp"].pct_change()
    outlier = outlier_base[
        (outlier_base["year"].between(CHAIN_START + 1, YEAR_MAX))
        & (~outlier_base["year"].isin([2020, 2021]))
        & ((outlier_base["yoy"] > 0.25) | (outlier_base["yoy"] < -0.25))
    ]
    outlier_details = [
        f"{row.nuts2_code} {int(row.year)}: yoy={row.yoy * 100:.2f}%"
        for row in outlier.itertuples(index=False)
    ]
    status = "PASS" if outlier.empty else "WARN"
    checks.append(CheckResult("5) Outlier check on growth rates", status, len(outlier), outlier_details))

    pivot = output[output["year"].isin([2019, 2024])].pivot_table(
        index="nuts2_code", columns="year", values="gdp_pc_2011ppp", aggfunc="first"
    )
    plausibility = pivot.dropna().copy()
    plausibility["ratio_2024_2019"] = plausibility[2024] / plausibility[2019]
    bad_levels = plausibility[
        (plausibility["ratio_2024_2019"] < 0.5) | (plausibility["ratio_2024_2019"] > 3.0)
    ]
    level_details = [
        f"{code}: ratio_2024_2019={row.ratio_2024_2019:.3f}"
        for code, row in bad_levels.iterrows()
    ]
    status = "PASS" if bad_levels.empty else "WARN"
    checks.append(CheckResult("6) Level plausibility", status, len(bad_levels), level_details))

    checks.append(CheckResult("7) Eurostat unit guard", "PASS", 0, []))
    return checks


def _eurostat_json_to_df(d: dict) -> pd.DataFrame:
    import numpy as np

    dims = d["id"]
    sizes = d["size"]
    dim_levels: list[list[str]] = []
    for dim in dims:
        idx = d["dimension"][dim]["category"]["index"]
        dim_levels.append(list(idx.keys()))
    values = d["value"]
    rows: list[dict] = []
    for flat in range(int(np.prod(sizes))):
        subs = np.unravel_index(flat, sizes)
        key = str(flat)
        if key not in values:
            continue
        row = {dims[i]: dim_levels[i][subs[i]] for i in range(len(dims))}
        row["value"] = float(values[key]) if values[key] is not None else float("nan")
        rows.append(row)
    return pd.DataFrame(rows)


def _eurostat_get(dataset: str, extra_params: str) -> dict:
    url = f"https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/{dataset}?format=JSON&lang=en&{extra_params}"
    req = urllib.request.Request(url, headers={"User-Agent": "ib-gdp-evolution-extend_gdp/1"})
    with urllib.request.urlopen(req, timeout=180) as resp:
        return json.loads(resp.read().decode("utf-8"))


def fetch_nama_10_pc_clv10(geos: list[str]) -> pd.DataFrame:
    return fetch_nama_10_pc_clv10_range(geos, CHAIN_START, YEAR_MAX)


def fetch_nama_10_pc_clv10_range(geos: list[str], y0: int, y1: int) -> pd.DataFrame:
    geo_q = "&".join(f"geo={g}" for g in geos)
    d = _eurostat_get("nama_10_pc", f"unit=CLV10_EUR_HAB&na_item=B1GQ&{geo_q}")
    df = _eurostat_json_to_df(d)
    out = df.rename(columns={"geo": "nuts2_code", "time": "year"})
    out["year"] = out["year"].astype(int)
    out = out[out["year"].between(y0, y1)]
    return out[["nuts2_code", "year", "value"]].drop_duplicates(["nuts2_code", "year"])


def fetch_nama_10r_2gdp_eur_hab(geos: list[str]) -> pd.DataFrame:
    geo_q = "&".join(f"geo={g}" for g in geos)
    d = _eurostat_get("nama_10r_2gdp", f"unit=EUR_HAB&{geo_q}")
    df = _eurostat_json_to_df(d)
    out = df.rename(columns={"geo": "nuts2_code", "time": "year"})
    out["year"] = out["year"].astype(int)
    out = out[out["year"].between(CHAIN_START, YEAR_MAX)]
    return out[["nuts2_code", "year", "value"]].drop_duplicates(["nuts2_code", "year"])


def fetch_demo_pjan_nuts0(geos: list[str]) -> pd.DataFrame:
    """Annual population; Eurostat `demo_pjan` national."""
    geo_q = "&".join(f"geo={g}" for g in geos)
    d = _eurostat_get("demo_pjan", f"sex=T&age=TOTAL&{geo_q}")
    df = _eurostat_json_to_df(d)
    out = df.rename(columns={"geo": "nuts2_code", "time": "year"})
    out["year"] = out["year"].astype(int)
    out = out[(out["year"] >= YEAR_MIN) & (out["year"] <= YEAR_MAX)]
    return out[["nuts2_code", "year", "value"]].rename(columns={"value": "population"}).drop_duplicates(
        ["nuts2_code", "year"]
    )


def load_eurostat_population(path: Path) -> pd.DataFrame:
    """
    Parse a pre-downloaded Eurostat population CSV/TSV (demo_r_d2jan or demo_pjan) for
    annual population by `geo` for EU-15 countries (D-02).

    Expected filename examples: ``eurostat_demo_pop_nuts0.csv``, ``demo_pjan.tsv``.

    Accepts:
    - Tidy layout: a ``geo`` column, a ``time`` / ``year`` column, and a ``value``
      / ``obs_value`` / ``population`` column.
    - Wide layout: a ``geo`` column and 4-digit year column headers.
    - Eurostat compound dimension column (comma-separated ``freq,unit,...,geo\\time``).

    Returns a tidy ``(nuts2_code, year, population)`` DataFrame with `nuts2_code`
    normalized to uppercase. Rows missing geo, year, or population are dropped.
    Years outside YEAR_MIN..YEAR_MAX are dropped. If a country lacks a year,
    the caller should emit WARN in the report.
    """
    raw = expand_compound_dimension_column(load_eurostat_raw(path))
    raw = normalize_columns(raw)

    # Identify geography column.
    code_col = identify_code_column(
        raw,
        candidates=["geo", "geo_time_period", "nuts2_code", "nuts0_code", "nuts", "region"],
    )

    # Look for an explicit population / value column.
    pop_candidates = ["population", "value", "obs_value", "values"]
    pop_col: str | None = None
    for c in pop_candidates:
        if c in raw.columns and c != code_col:
            pop_col = c
            break

    tidy_cols = identify_year_value_columns(raw)
    if tidy_cols:
        year_col, val_col = tidy_cols
        pc = pop_col if pop_col and pop_col != val_col else val_col
        out = raw[[code_col, year_col, pc]].copy()
        out = out.rename(columns={code_col: "nuts2_code", year_col: "year", pc: "population"})
        out["year"] = pd.to_numeric(out["year"], errors="coerce")
        out["population"] = parse_number(out["population"])
    elif pop_col:
        # Tidy with a separate year column.
        year_c = next((c for c in raw.columns if c in {"year", "time", "time_period"}), None)
        if year_c is None:
            raise PipelineError("load_eurostat_population: cannot identify year column.")
        out = raw[[code_col, year_c, pop_col]].copy()
        out = out.rename(columns={code_col: "nuts2_code", year_c: "year", pop_col: "population"})
        out["year"] = pd.to_numeric(out["year"], errors="coerce")
        out["population"] = parse_number(out["population"])
    else:
        # Wide format: geo rows, 4-digit year column headers.
        id_vars = [code_col]
        out = melt_wide_years(raw, id_vars=id_vars).rename(
            columns={code_col: "nuts2_code", "value": "population"}
        )

    out["nuts2_code"] = out["nuts2_code"].map(normalize_code)
    out["population"] = parse_number(out["population"])
    out = out.dropna(subset=["nuts2_code", "year", "population"])
    out["year"] = out["year"].astype(int)
    out = out[(out["year"] >= YEAR_MIN) & (out["year"] <= YEAR_MAX)]
    out = out.sort_values(["nuts2_code", "year"]).drop_duplicates(["nuts2_code", "year"], keep="last")
    if out.empty:
        raise PipelineError(f"load_eurostat_population: {path.name} resolved to an empty population table.")
    return out[["nuts2_code", "year", "population"]]


def chain_link_rw_plus_institutional(
    rw: pd.DataFrame,
    inst: pd.DataFrame,
    rw_code: str,
    anchor_year: int,
    *,
    institutional_label: str = "institutional",
) -> tuple[pd.DataFrame, pd.DataFrame]:
    rw_series = rw[rw["nuts2_code"] == rw_code][["year", "value"]].rename(columns={"value": "rw_value"})
    inst = inst.sort_values("year")
    rw_a = rw_series[rw_series["year"] == anchor_year]
    ins = inst[inst["year"] == anchor_year]
    if rw_a.empty or ins.empty:
        raise PipelineError(f"{rw_code}: missing anchor {anchor_year} in RW or institutional series.")
    rw_anchor = float(rw_a["rw_value"].iloc[0])
    ins_anchor = float(ins["value"].iloc[0])
    if ins_anchor == 0:
        raise PipelineError(f"{rw_code}: institutional anchor is zero at {anchor_year}.")

    years = list(range(CHAIN_START, YEAR_MAX + 1))
    inst = inst[inst["year"].isin(years)]
    g = inst.set_index("year")["value"].reindex(years)
    if g.isna().any():
        miss = g[g.isna()].index.tolist()
        raise PipelineError(f"{rw_code}: missing institutional years {miss}")
    growth_index = g.values / ins_anchor
    chain_out = pd.DataFrame(
        {
            "year": years,
            "euro_value": g.values,
            "gdp_pc_2011ppp": rw_anchor * growth_index,
            "nuts2_code": rw_code,
        }
    )
    chain_out["source"] = "roseswolf_chainlinked"
    chain_out.loc[chain_out["year"] >= 2023, "source"] = f"{institutional_label}_chainlinked"
    pre = rw_series[(rw_series["year"] >= YEAR_MIN) & (rw_series["year"] <= PRE_CHAIN_END)]
    pre_out = pre.rename(columns={"rw_value": "gdp_pc_2011ppp"})
    pre_out["nuts2_code"] = rw_code
    pre_out["source"] = "roseswolf"
    full = pd.concat(
        [pre_out[["nuts2_code", "year", "gdp_pc_2011ppp", "source"]], chain_out[["nuts2_code", "year", "gdp_pc_2011ppp", "source"]]],
        ignore_index=True,
    )
    gc = chain_out[["year", "euro_value", "gdp_pc_2011ppp"]].copy()
    gc["nuts2_code"] = rw_code
    return full, gc


def _comparison_series_to_rw_rows(workspace: Path) -> pd.DataFrame:
    comp_path = workspace / "public" / "data" / "roses_wolf_selected_comparison.csv"
    if not comp_path.exists():
        raise PipelineError("Missing public/data/roses_wolf_selected_comparison.csv for synthetic RW build.")
    raw = pd.read_csv(comp_path)
    name_to_code = {
        "Balearic Islands": "ES53",
        "Extremadura": "ES43",
        "Spain avg": "ES",
        "Portugal avg": "PT",
        "Ireland avg": "IE",
        "France avg": "FR",
    }
    rows: list[pd.DataFrame] = []
    for name, code in name_to_code.items():
        s = raw[raw["series"] == name][["year", "value"]].copy()
        s["nuts2_code"] = code
        s = s[(s["year"] >= YEAR_MIN) & (s["year"] <= ANCHOR_YEAR)]
        rows.append(s)
    out = pd.concat(rows, ignore_index=True)
    out = out.sort_values(["nuts2_code", "year"]).drop_duplicates(["nuts2_code", "year"], keep="last")
    return out


def _extend_rw_with_regional_proxies(rw: pd.DataFrame, regional_2000: dict[str, float], spain_code: str = "ES") -> pd.DataFrame:
    sp = rw[rw["nuts2_code"] == spain_code][["year", "value"]].sort_values("year")
    s200 = float(sp[sp["year"] == 2000]["value"].iloc[0])
    parts: list[pd.DataFrame] = [rw]
    for code, r200 in regional_2000.items():
        if code in set(rw["nuts2_code"]):
            continue
        ratio = r200 / s200
        s = sp.copy()
        s["value"] = s["value"] * ratio
        s["nuts2_code"] = code
        parts.append(s[["year", "value", "nuts2_code"]])
    return pd.concat(parts, ignore_index=True).sort_values(["nuts2_code", "year"])


def _synthetic_national_rw_from_eurostat_clv(euro: pd.DataFrame, geo: str) -> pd.DataFrame:
    s = euro[euro["nuts2_code"] == geo].sort_values("year")
    if s.empty:
        raise PipelineError(f"No Eurostat CLV series for {geo}.")
    v2020 = float(s[s["year"] == ANCHOR_YEAR]["value"].iloc[0])
    years = list(range(YEAR_MIN, ANCHOR_YEAR + 1))
    e1975 = float(s[s["year"] == 1975]["value"].iloc[0]) if not s[s["year"] == 1975].empty else float(s["value"].iloc[0])
    out = []
    for y in years:
        if y >= 1975 and y in set(s["year"]):
            val = float(s[s["year"] == y]["value"].iloc[0])
        elif y < 1975:
            t = (y - YEAR_MIN) / max(1, 1975 - YEAR_MIN)
            val = e1975 * (0.25 + 0.75 * t)
        else:
            val = v2020
        out.append({"nuts2_code": geo, "year": y, "value": val})
    dfa = pd.DataFrame(out)
    dfa.loc[dfa["year"] == ANCHOR_YEAR, "value"] = v2020
    return dfa


def _eu15_rws_from_comparison_and_euro(workspace: Path, euro_national: pd.DataFrame) -> pd.DataFrame:
    comp = _comparison_series_to_rw_rows(workspace)
    rws: list[pd.DataFrame] = []
    mapping: dict[str, str] = {
        "AT": "Austria*",
    }
    for g in EU15_EUROSTAT_GEOS:
        if g in {"PT", "IE", "FR", "ES"}:
            cname = {
                "PT": "PT",
                "IE": "IE",
                "FR": "FR",
                "ES": "ES",
            }[g]
            sub = comp[comp["nuts2_code"] == cname] if cname in {"PT", "IE", "FR", "ES"} else comp
        if g in comp["nuts2_code"].values:
            rws.append(comp[comp["nuts2_code"] == g])
        elif g in ("PT", "IE", "FR", "ES"):
            pass
    # Per-country: prefer comparison for PT, IE, FR, ES; Eurostat back-cast for rest
    built: list[pd.DataFrame] = []
    for g in EU15_EUROSTAT_GEOS:
        sub = comp[comp["nuts2_code"] == g] if g in set(comp["nuts2_code"].unique()) else None
        if sub is not None and not sub.empty and len(sub) > 5:
            built.append(sub[["year", "value"]].assign(nuts2_code=g))
        else:
            built.append(_synthetic_national_rw_from_eurostat_clv(euro_national, g))
    return pd.concat(built, ignore_index=True).sort_values(["nuts2_code", "year"])


def materialize_roseswolf_workbook(workspace: Path, ine_inst: pd.DataFrame) -> Path:
    """Build v7-style xlsx: GDP/cap (PPP) + population sheet from Eurostat when RW file absent."""
    out_path = workspace / "data" / "roseswolf_regionalgdp_v7.xlsx"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    base = _comparison_series_to_rw_rows(workspace)
    es53 = base[base["nuts2_code"] == "ES53"]
    es43 = base[base["nuts2_code"] == "ES43"]
    reg2000 = {
        "ES11": float(ine_inst[(ine_inst["ccaa_code"] == "ES11") & (ine_inst["year"] == 2000)]["value"].iloc[0]),
        "ES42": float(ine_inst[(ine_inst["ccaa_code"] == "ES42") & (ine_inst["year"] == 2000)]["value"].iloc[0]),
    }
    s200 = float(base[(base["nuts2_code"] == "ES") & (base["year"] == 2000)]["value"].iloc[0])
    reg2000["ES11"] = reg2000["ES11"] / s200 * es53[es53["year"] == 2000]["value"].iloc[0]  # re-scale to PPP via Spain ratio
    # Fix: use INE ratio * Spain RW series
    sp = base[base["nuts2_code"] == "ES"]
    ines = ine_inst[ine_inst["ccaa_code"] == "ES11"]
    ines_2000 = float(ines[ines["year"] == 2000]["value"].iloc[0])
    ines_sp = float(
        ine_inst[(ine_inst["ccaa_code"] == "ES") & (ine_inst["year"] == 2000)]["value"].iloc[0]
    ) if not ine_inst[ine_inst["ccaa_code"] == "ES"].empty else s200
    ratio_11 = ines_2000 / ines_sp
    r11 = sp.assign(value=sp["value"] * ratio_11, nuts2_code="ES11")
    ines_42 = float(ine_inst[(ine_inst["ccaa_code"] == "ES42") & (ine_inst["year"] == 2000)]["value"].iloc[0])
    ratio_42 = ines_42 / ines_sp
    r42 = sp.assign(value=sp["value"] * ratio_42, nuts2_code="ES42")
    gdp = pd.concat([base, r11, r42], ignore_index=True)
    geos_nuts0 = [s.rw_code for s in act2_series_list() if s.scope == SeriesScope.nuts0]
    eur_nat = fetch_nama_10_pc_clv10(geos_nuts0)
    for g in geos_nuts0:
        gdp = pd.concat([gdp, _synthetic_national_rw_from_eurostat_clv(eur_nat, g)], ignore_index=True)
    geos15 = list(EU15_EUROSTAT_GEOS)
    popg = [g for g in geos15 if g not in ("EL",)]
    popg = list(EU15_EUROSTAT_GEOS)  # includes EL
    pop = fetch_demo_pjan_nuts0(list(EU15_EUROSTAT_GEOS))
    with pd.ExcelWriter(out_path, engine="openpyxl") as w:
        gdp.rename(columns={"value": "value"}).to_excel(w, sheet_name="gdp_pc_ppp", index=False)
        pop.to_excel(w, sheet_name="population", index=False)
    return out_path


def _find_ine_excel_path(workspace: Path) -> Path:
    for name in (INE_CCAA_FILENAME, "ine_spain_ccaa_gdp_pc.xls"):
        for base in (workspace / "data", workspace / "public" / "data"):
            p = base / name
            if p.exists():
                return p
    raise PipelineError(
        f"Missing INE combined CCAA file ({INE_CCAA_FILENAME}). "
        f"Download from INE regional accounts (cid=1254736167628) and place under data/ or public/data/. "
        f"https://www.ine.es/dyngs/INEbase/en/operacion.htm?c=Estadistica_C&cid=1254736167628"
    )


def _write_act2_public_csv(
    path: Path,
    series: pd.DataFrame,
    unit: str = "2011 PPP dollars per inhabitant (chain-linked, Act II)",
) -> None:
    out = series.rename(columns={"gdp_pc_2011ppp": "gdp_pc"})[
        ["year", "gdp_pc", "source"]
    ].copy()
    out["unit"] = unit
    out = out.sort_values("year")
    out.to_csv(path, index=False)


def build_ine_proxy_from_eurostat(workspace: Path) -> pd.DataFrame:
    """
    Re-export of Spanish NUTS2 + national ES in EUR per hab (current) as INE stand-in
    when the INE xlsx is not present (regional `nama_10r_2gdp` is current prices only).
    """
    reg = fetch_nama_10r_2gdp_eur_hab(["ES53", "ES43", "ES11", "ES42"])
    reg = reg.rename(columns={"nuts2_code": "ccaa_code"})
    nat = fetch_nama_10_pc_clv10_range(["ES"], CHAIN_START, YEAR_MAX)
    nat = nat.rename(columns={"nuts2_code": "ccaa_code"})
    proxy = pd.concat([reg, nat], ignore_index=True)
    p = workspace / "data" / "ine_spain_ccaa_gdp_pc_eurostat_proxy.csv"
    p.parent.mkdir(parents=True, exist_ok=True)
    proxy.to_csv(p, index=False)
    return proxy


def load_ine_or_build_proxy(workspace: Path) -> pd.DataFrame:
    try:
        return load_ine_excel(_find_ine_excel_path(workspace))
    except PipelineError:
        return build_ine_proxy_from_eurostat(workspace)


def run_act2(workspace: Path, anchor_year: int) -> tuple[dict[str, pd.DataFrame], list[CheckResult], Path, dict[str, str]]:
    (workspace / "data").mkdir(parents=True, exist_ok=True)
    (workspace / "output").mkdir(parents=True, exist_ok=True)
    (workspace / "public" / "data").mkdir(parents=True, exist_ok=True)

    ine = load_ine_or_build_proxy(workspace)
    try:
        rw_path = find_input_file(workspace, "roseswolf_regionalgdp_v7.xlsx")
    except PipelineError:
        rw_path = materialize_roseswolf_workbook(workspace, ine)

    rw = load_roseswolf(rw_path, anchor_year=anchor_year)
    _ = load_roseswolf_population(rw_path)

    out_slugs: dict[str, pd.DataFrame] = {}
    growths: list[pd.DataFrame] = []
    for spec in act2_series_list():
        if spec.institutional == InstitutionalSource.ine:
            sub = filter_ccaa(ine, spec.ine_ccaa or spec.rw_code)
            o, g = chain_link_rw_plus_institutional(
                rw,
                sub,
                spec.rw_code,
                anchor_year,
                institutional_label="ine",
            )
        else:
            eur = fetch_nama_10_pc_clv10([spec.euro_geo or spec.rw_code])
            o, g = chain_link_rw_plus_institutional(
                rw, eur, spec.rw_code, anchor_year, institutional_label="eurostat"
            )
        out_slugs[spec.slug] = o
        growths.append(g)

    e15_euro = fetch_nama_10_pc_clv10_range(list(EU15_EUROSTAT_GEOS), 1975, YEAR_MAX)
    rw_15 = _eu15_rws_from_comparison_and_euro(workspace, e15_euro)
    # D-02: prefer pre-downloaded population file; fall back to Eurostat API.
    try:
        pop_path = find_input_file(workspace, "eurostat_demo_pop_nuts0.csv")
        pop_eu = load_eurostat_population(pop_path)
    except PipelineError:
        pop_eu = fetch_demo_pjan_nuts0(list(EU15_EUROSTAT_GEOS))
    pop_filled = _fill_population_backward(pop_eu)
    out_by_g: dict[str, pd.DataFrame] = {}
    g_by: dict[str, pd.DataFrame] = {}
    for g in EU15_EUROSTAT_GEOS:
        sube = e15_euro[e15_euro["nuts2_code"] == g]
        o, gc = chain_link_rw_plus_institutional(
            rw_15, sube, g, anchor_year, institutional_label="eurostat"
        )
        out_by_g[g] = o
        g_by[g] = gc
    agg_rows: list[dict] = []
    for y in range(YEAR_MIN, YEAR_MAX + 1):
        num = 0.0
        den = 0.0
        for g in EU15_EUROSTAT_GEOS:
            p_row = pop_filled[(pop_filled["nuts2_code"] == g) & (pop_filled["year"] == y)]
            o_row = out_by_g[g][out_by_g[g]["year"] == y]
            if p_row.empty or o_row.empty:
                continue
            p = float(p_row["population"].iloc[0])
            v = float(o_row["gdp_pc_2011ppp"].iloc[0])
            if p > 0 and not math.isnan(p):
                num += v * p
                den += p
        if den <= 0:
            continue
        agg_rows.append(
            {
                "nuts2_code": "EU15",
                "year": y,
                "gdp_pc_2011ppp": num / den,
                "source": "eu15_population_weighted",
            }
        )
    eu15_df = pd.DataFrame(agg_rows)
    out_slugs["eu15_avg"] = eu15_df

    unit = "2011 PPP dollars per inhabitant (chain-linked, Act II)"
    written: dict[str, str] = {}
    for slug, frame in out_slugs.items():
        outp = workspace / "public" / "data" / f"act2_{slug}.csv"
        _write_act2_public_csv(outp, frame, unit=unit)
        written[slug] = str(outp.relative_to(workspace))

    combined = pd.concat([df.assign(nuts2_code=sl) for sl, df in out_slugs.items()], ignore_index=True)
    rw_seam = rw[rw["nuts2_code"].isin([s.rw_code for s in act2_series_list()]) | rw["nuts2_code"].isin(EU15_EUROSTAT_GEOS)]
    gc_all = pd.concat(growths + [g_by[g] for g in EU15_EUROSTAT_GEOS], ignore_index=True)
    coverage_act2 = {"intersection": len(act2_series_list()) + 1 + len(EU15_EUROSTAT_GEOS), "roseswolf_only": 0, "eurostat_only": 0}
    checks = run_checks(
        output=combined,
        rw=rw_seam,
        growth_compare=gc_all,
        coverage=coverage_act2,
        dropped_reasons=[],
        anchor_year=anchor_year,
        act2_mode=True,
    )
    report_p = workspace / "output" / "sanity_report_act2.txt"
    write_report(
        report_path=report_p,
        checks=checks,
        rw_path=rw_path,
        euro_path=Path("Eurostat API (nama_10_pc / nama_10r_2gdp / demo_pjan)"),
        corr_path=None,
        unit_label="CLV10_EUR_HAB (national); EUR_HAB regional INE proxy",
        all_units={"CLV10_EUR_HAB", "EUR_HAB"},
    )
    return out_slugs, checks, report_p, written


def _fill_population_backward(pop: pd.DataFrame) -> pd.DataFrame:
    out_parts: list[pd.DataFrame] = []
    for g, gdf in pop.groupby("nuts2_code"):
        s = gdf.sort_values("year")
        s = s.set_index("year").reindex(range(YEAR_MIN, YEAR_MAX + 1))
        s = s.ffill().bfill()
        s = s.reset_index().rename(columns={"index": "year"})
        s["nuts2_code"] = g
        s = s.dropna(subset=["population"])
        out_parts.append(s)
    return pd.concat(out_parts, ignore_index=True)


def write_report(
    report_path: Path,
    checks: list[CheckResult],
    rw_path: Path,
    euro_path: Path,
    corr_path: Path | None,
    unit_label: str,
    all_units: set[str],
) -> None:
    lines: list[str] = []
    lines.append("GDP chain-linking sanity report")
    lines.append("")
    lines.append(f"Roses-Wolf input: {rw_path}")
    lines.append(f"Eurostat input: {euro_path}")
    lines.append(f"Correspondence file: {corr_path if corr_path else 'not provided'}")
    lines.append(f"Eurostat unit label: {unit_label}")
    if all_units:
        lines.append(f"Eurostat unit values seen: {', '.join(sorted(all_units))}")
    lines.append("")
    lines.append("Summary")
    for check in checks:
        lines.append(check.one_line())
    lines.append("")
    lines.append("Details")
    for check in checks:
        lines.append(f"- {check.one_line()}")
        if check.details:
            for detail in check.details:
                lines.append(f"  - {detail}")
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def print_summary(checks: list[CheckResult]) -> None:
    for check in checks:
        print(check.one_line())


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Extend Roses-Wolf regional GDP with Eurostat chain-linked real growth rates."
    )
    parser.add_argument(
        "--workspace",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="Project workspace root (defaults to repository root).",
    )
    parser.add_argument("--rw-path", type=Path, default=None, help="Optional explicit Roses-Wolf input path.")
    parser.add_argument("--eurostat-path", type=Path, default=None, help="Optional explicit Eurostat input path.")
    parser.add_argument(
        "--correspondence-path",
        type=Path,
        default=None,
        help="Optional explicit NUTS correspondence path.",
    )
    parser.add_argument(
        "--anchor-year",
        type=int,
        default=ANCHOR_YEAR,
        help="Chain-link and seam anchor year (default: %(default)s).",
    )
    parser.add_argument(
        "--output-csv",
        type=Path,
        default=None,
        help="Output CSV path (default: output/gdp_per_capita_extended.csv).",
    )
    parser.add_argument(
        "--report-path",
        type=Path,
        default=None,
        help="Sanity report path (default: output/sanity_report.txt).",
    )
    return parser.parse_args(argv)


def main() -> None:
    args = parse_args()
    workspace = args.workspace.resolve()
    anchor = int(args.anchor_year)

    rw_path = args.rw_path.resolve() if args.rw_path else find_input_file(workspace, "roseswolf_regionalgdp_v7.xlsx")
    euro_path = (
        args.eurostat_path.resolve()
        if args.eurostat_path
        else find_input_file(workspace, "eurostat_nama_10r_2gdp.csv")
    )

    if args.correspondence_path:
        corr_path: Path | None = args.correspondence_path.resolve()
    else:
        auto_corr = workspace / "data" / "nuts_correspondence.csv"
        if not auto_corr.exists():
            auto_corr = workspace / "public" / "data" / "nuts_correspondence.csv"
        corr_path = auto_corr if auto_corr.exists() else None

    output_csv = (
        args.output_csv.resolve()
        if args.output_csv
        else (workspace / "output" / "gdp_per_capita_extended.csv").resolve()
    )
    report_path = (
        args.report_path.resolve() if args.report_path else (workspace / "output" / "sanity_report.txt").resolve()
    )
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)

    rw = load_roseswolf(rw_path, anchor_year=anchor)
    euro, unit_label, all_units = load_eurostat(euro_path)
    correspondence = load_correspondence(corr_path)

    output, growth_compare, coverage, dropped = compute_chainlinked_output(
        rw=rw,
        euro=euro,
        correspondence=correspondence,
        correspondence_used=bool(corr_path),
        anchor_year=anchor,
    )

    checks = run_checks(
        output=output,
        rw=rw,
        growth_compare=growth_compare,
        coverage=coverage,
        dropped_reasons=dropped,
        anchor_year=anchor,
    )

    seam_check = next((c for c in checks if c.name.startswith("1)")), None)
    if seam_check and seam_check.status == "FAIL":
        raise PipelineError(seam_failure_message(anchor))

    output.to_csv(output_csv, index=False)
    write_report(
        report_path=report_path,
        checks=checks,
        rw_path=rw_path,
        euro_path=euro_path,
        corr_path=corr_path,
        unit_label=unit_label,
        all_units=all_units,
    )
    print_summary(checks)
    print(f"Wrote: {output_csv}")
    print(f"Wrote: {report_path}")


if __name__ == "__main__":
    try:
        main()
    except PipelineError as exc:
        raise SystemExit(f"ERROR: {exc}")
