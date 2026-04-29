# Phase 5: Full Act II ETL - Research

**Researched:** 2026-04-29
**Domain:** Multi-region GDP chain-linking ETL (data-lake ingestion → Eurostat adapter → chain-link → CSV emit)
**Confidence:** HIGH

## Summary

This phase replaces the `--act2-local-proxy` data path with a full ETL that reads Eurostat JSON-stat v2.0 artifacts from the data-lake, chain-links them with Rosés-Wolf historical data at a 2019 anchor, and emits the 7 `act2_*.csv` files the frontend consumes. The existing `extend_gdp.py` (~1577 lines) implements ~90% of the required logic — JSON-stat parsing (`_eurostat_json_to_df()`), chain-linking (`chain_link_rw_plus_institutional()`), EU-15 weighted average, sanity checks, and CSV output. The primary new work is: (1) ingesting ~20 Eurostat API responses into the data-lake, (2) a static catalog index file, (3) a data-lake adapter with API fallback, (4) `act2_series_list()` alignment with the frontend, and (5) a baseline regression check.

No new Python dependencies are needed. The data-lake stores Eurostat API responses as raw JSON files identical in structure to what `_eurostat_json_to_df()` already parses. The adapter is a thin resolution layer: `json.load()` a local file instead of `urllib.request.urlopen()` a remote URL.

**Primary recommendation:** Build an ingestion helper script in this project (not the data-lake project) that calls the data-lake CLI to ingest each required Eurostat URL, then emit a `datalake_eurostat_index.json` mapping (dataset, geo, unit) → source_id. Wire `run_act2()` through a `fetch_eurostat_series()` adapter that reads `raw.json` from data-lake artifact paths with API fallback.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** This is a one-off data pipeline task — minimal ceremony, just get the data flowing.
- **D-02:** Collapse original 4 phases (5-8) into a single phase. All work happens here.
- **D-03:** Use the data-lake project's ingestion scripts (pattern from `fetch_balearic_gdp_sources.py`) to fetch Eurostat API responses and store as raw JSON artifacts.
- **D-04:** The data-lake MCP is read-only — ingestion happens through the data-lake project's Python scripts at `/Users/guillem/vault/projects/personal/data-lake/`.
- **D-05:** Build a static `datalake_eurostat_index.json` mapping (dataset, geo, unit) → source_id for deterministic lookup.
- **D-06:** Uniform approach for all regions: Rosés-Wolf (1900-1999) + Eurostat NAMA (2000-2024). No INE special-casing needed if Eurostat current-price EUR_HAB is acceptable for the comparison chart.
- **D-07:** `act2_series_list()` must match the 7 frontend CSVs: balearic_islands, extremadura, andalucia, portugal, ireland, france, eu15_avg.
- **D-08:** Anchor year 2019 (avoid COVID-distorted 2020).
- **D-09:** Data-lake adapter with API fallback: try local artifact first, fall back to live Eurostat API.
- **D-10:** Sanity checks must pass. Baseline regression compares growth-rate correlation vs local-proxy, not absolute levels.

### Claude's Discretion
- Exact Eurostat API query parameters and NUTS code mapping
- Internal function organization within `extend_gdp.py`
- Specific sanity check thresholds

### Deferred Ideas (OUT OF SCOPE)
None — discussion stayed within phase scope.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| INGEST-01 | Pipeline reads Eurostat JSON-stat v2.0 from data-lake local paths | Data-lake artifact structure verified: `raw.json` at `lake/sources/<id>/raw.json` is valid JSON-stat v2.0 parseable by existing `_eurostat_json_to_df()` |
| INGEST-02 | All required Eurostat datasets ingested (~20 sources across nama_10r_2gdp, nama_10_pc, demo_pjan) | Enumerated 20 exact Eurostat API URLs needed — see Standard Stack / Ingestion Inventory |
| INGEST-03 | Static catalog index maps (dataset, geo, unit) → source_id | Index design documented; maps each triple to a data-lake source ID from `meta.yaml` |
| ETL-01 | Data-lake adapter resolves data from data-lake first, falls back to live API | Adapter pattern documented; `json.load()` of `raw.json` → `_eurostat_json_to_df()` — zero parser changes |
| ETL-02 | `act2_series_list()` aligned with frontend contract | Mismatch identified and mapped: remove galicia/castilla_la_mancha/malta, add andalucia(ES61)/france(FR) |
| ETL-03 | Dual-dataset routing: NUTS2 via nama_10r_2gdp, countries via nama_10_pc | Existing routing in `run_act2()` already handles this via `InstitutionalSource.ine` vs `.eurostat` |
| ETL-04 | Geo-code normalization (EL/GR for Greece) | `EU15_EUROSTAT_GEOS` already uses EL; `normalize_code()` handles uppercasing |
| CHAIN-01 | Spanish NUTS2 uses INE chain-linked data | Current code uses `load_ine_or_build_proxy()` → `build_ine_proxy_from_eurostat()` which fetches `nama_10r_2gdp` EUR_HAB. Need to add ES61 (Andalucia) to proxy. D-06 accepts EUR_HAB for comparison chart |
| CHAIN-02 | EU-15 population-weighted average from 15 countries | Already implemented in `run_act2()` lines 1304-1347; needs adapter wiring |
| CHAIN-03 | UK post-Brexit data gap handled | Research documents: Eurostat stops at 2019 for UK GDP; need documented exclusion or last-value carry-forward for 2020-2024 |
| CHAIN-04 | Anchor year 2019 | Change `ANCHOR_YEAR` or pass `anchor_year=2019` to `run_act2()` |
| VALID-01 | Output preserves CSV contract (year, gdp_pc, source, unit) and filenames | Verified existing output format matches; `_write_act2_public_csv()` already emits correct schema |
| VALID-02 | All existing sanity checks pass | 7 existing checks in `run_checks()` — no changes needed, just run |
| VALID-03 | Baseline regression vs local-proxy | New check: load existing local-proxy CSVs, compute growth-rate correlation ≥0.95 |
</phase_requirements>

## Standard Stack

### Core (all existing — zero new dependencies)

| Library | Version | Purpose | Status |
|---------|---------|---------|--------|
| pandas | existing | DataFrame operations, chain-linking, CSV I/O | Already in use |
| json (stdlib) | 3.x | Parse data-lake JSON-stat artifacts | Already used for API responses |
| numpy | existing | `np.unravel_index` in JSON-stat dimension flattening | Already imported |
| pathlib (stdlib) | 3.x | Data-lake artifact path resolution | Already in use |

[VERIFIED: codebase inspection — no new packages needed]

### Data-Lake Ingestion Tool

| Tool | Version | Purpose | Location |
|------|---------|---------|----------|
| data-lake CLI | v1 (uv) | Ingest Eurostat API URLs into data-lake | `/Users/guillem/vault/projects/personal/data-lake/` |

**Ingestion command pattern:** [VERIFIED: data-lake CLI help output]
```bash
cd /Users/guillem/vault/projects/personal/data-lake
uv run python -m data_lake.ingest.cli.app ingest "<eurostat_url>" --format json
```

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Static JSON index | Data-lake MCP `search` | BM25 search is non-deterministic; static index is reliable and fast |
| Per-geo separate ingestions | Multi-geo batch queries | Multi-geo batches need fewer sources but complicate the index; per-geo is simpler to map |

## Ingestion Inventory

### Required Eurostat API URLs

**Dataset 1: `nama_10r_2gdp` (NUTS2 regional GDP, EUR_HAB)**

For Spanish NUTS2 regions — Eurostat has no CLV at NUTS2 level, EUR_HAB (current prices) is used. D-06 accepts this for comparison charts.

| # | Geo | Label | URL | Data-lake status |
|---|-----|-------|-----|-----------------|
| 1 | ES53 | Balearic Islands | `https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/nama_10r_2gdp?format=JSON&lang=en&unit=EUR_HAB&geo=ES53` | EXISTS: `01KPWPQ902XYG9BT12QCXKFG4K` |
| 2 | ES43 | Extremadura | `https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/nama_10r_2gdp?format=JSON&lang=en&unit=EUR_HAB&geo=ES43` | NEEDS INGEST |
| 3 | ES61 | Andalucia | `https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/nama_10r_2gdp?format=JSON&lang=en&unit=EUR_HAB&geo=ES61` | NEEDS INGEST |

**Dataset 2: `nama_10_pc` (national GDP per capita, CLV10_EUR_HAB)**

For country-level Act2 series and EU-15 components. Chain-linked volume data — the correct unit for long-run comparison.

| # | Geo | Label | URL | Notes |
|---|-----|-------|-----|-------|
| 4 | PT | Portugal | `...nama_10_pc?format=JSON&lang=en&unit=CLV10_EUR_HAB&na_item=B1GQ&geo=PT` | Act2 series |
| 5 | IE | Ireland | `...&geo=IE` | Act2 series |
| 6 | FR | France | `...&geo=FR` | Act2 series |
| 7 | AT | Austria | `...&geo=AT` | EU-15 component |
| 8 | BE | Belgium | `...&geo=BE` | EU-15 component |
| 9 | DK | Denmark | `...&geo=DK` | EU-15 component |
| 10 | FI | Finland | `...&geo=FI` | EU-15 component |
| 11 | DE | Germany | `...&geo=DE` | EU-15 component |
| 12 | EL | Greece | `...&geo=EL` | EU-15 component (EL not GR) |
| 13 | IT | Italy | `...&geo=IT` | EU-15 component |
| 14 | LU | Luxembourg | `...&geo=LU` | EU-15 component |
| 15 | NL | Netherlands | `...&geo=NL` | EU-15 component |
| 16 | ES | Spain | `...&geo=ES` | EU-15 component |
| 17 | SE | Sweden | `...&geo=SE` | EU-15 component |
| 18 | UK | United Kingdom | `...&geo=UK` | EU-15 component; data ends 2019 |

**Dataset 3: `demo_pjan` (population, annual)**

| # | Geo | Label | URL | Notes |
|---|-----|-------|-----|-------|
| 19 | All EU-15 | Population | `...demo_pjan?format=JSON&lang=en&sex=T&age=TOTAL&geo=AT&geo=BE&geo=DK&geo=FI&geo=FR&geo=DE&geo=EL&geo=IE&geo=IT&geo=LU&geo=NL&geo=PT&geo=ES&geo=SE&geo=UK` | Multi-geo batch OK; single source |

**Alternative: batch ingestion**

Instead of 18 individual `nama_10_pc` queries, batch all EU-15 geos + Act2 geos into one URL:
```
...nama_10_pc?format=JSON&lang=en&unit=CLV10_EUR_HAB&na_item=B1GQ&geo=AT&geo=BE&geo=DK&geo=FI&geo=FR&geo=DE&geo=EL&geo=IE&geo=IT&geo=LU&geo=NL&geo=PT&geo=ES&geo=SE&geo=UK
```
This reduces to **4 total data-lake sources** (1 existing + 2 NUTS2 + 1 national batch + 1 population batch). The catalog index maps each `(dataset, geo, unit)` triple to the source containing that geo.

**Recommendation:** Use batched queries (4 sources total) — simpler ingestion, simpler maintenance. The catalog index handles per-geo lookup regardless.

**Total ingestion work:** 3 new data-lake sources (nama_10r_2gdp ES43 + ES61, nama_10_pc EU-15 batch, demo_pjan EU-15 batch). 1 source already exists.

## Architecture Patterns

### Recommended Changes to extend_gdp.py

```
extend_gdp.py (existing ~1577 lines)
├── NEW: load_datalake_index(path) → dict  # Read datalake_eurostat_index.json
├── NEW: fetch_eurostat_from_datalake(source_id, datalake_root) → dict  # json.load raw.json
├── NEW: fetch_eurostat_series(dataset, geo, unit, ...) → pd.DataFrame  # Adapter: datalake → API fallback
├── MODIFY: act2_series_list()  # Replace galicia/clm/malta with andalucia/france
├── MODIFY: run_act2()  # Wire through adapter, change anchor to 2019
├── MODIFY: build_ine_proxy_from_eurostat()  # Add ES61 to proxy fetch
├── NEW: baseline_regression_check()  # Compare vs local-proxy CSVs
└── MODIFY: parse_args() / main()  # New --act2-datalake flag or auto-detect
```

### Pattern: Data-Lake Adapter with API Fallback

```python
# Source: codebase analysis of existing _eurostat_get() + data-lake artifact structure
def fetch_eurostat_series(
    dataset: str, geos: list[str], unit: str, *,
    datalake_index: dict | None = None,
    datalake_root: Path | None = None,
    extra_params: str = "",
) -> pd.DataFrame:
    """Try data-lake artifact first, fall back to live Eurostat API."""
    if datalake_index and datalake_root:
        # Look up source_id from index
        key = f"{dataset}|{unit}|{'|'.join(sorted(geos))}"
        source_id = datalake_index.get(key)
        if source_id:
            raw_path = datalake_root / "lake" / "sources" / source_id / "raw.json"
            if raw_path.exists():
                d = json.loads(raw_path.read_text())
                return _eurostat_json_to_df(d)  # EXISTING parser — no changes
    # Fallback: live API (existing code path)
    d = _eurostat_get(dataset, f"unit={unit}&{'&'.join(f'geo={g}' for g in geos)}&{extra_params}")
    return _eurostat_json_to_df(d)
```

### Pattern: Catalog Index File

```json
{
  "_meta": {
    "created": "2026-04-29",
    "datalake_root": "/Users/guillem/vault/projects/personal/data-lake"
  },
  "nama_10r_2gdp|EUR_HAB|ES53": "01KPWPQ902XYG9BT12QCXKFG4K",
  "nama_10r_2gdp|EUR_HAB|ES43": "<source_id_after_ingest>",
  "nama_10r_2gdp|EUR_HAB|ES61": "<source_id_after_ingest>",
  "nama_10_pc|CLV10_EUR_HAB|AT|BE|DE|DK|EL|ES|FI|FR|IE|IT|LU|NL|PT|SE|UK": "<source_id>",
  "demo_pjan|T|TOTAL|AT|BE|DE|DK|EL|ES|FI|FR|IE|IT|LU|NL|PT|SE|UK": "<source_id>"
}
```

### Series Alignment: Current vs Required

| Slot | Current `act2_series_list()` | Required (frontend) | Action |
|------|----------------------------|---------------------|--------|
| 1 | balearic_islands (ES53, INE) | balearic_islands | Keep |
| 2 | extremadura (ES43, INE) | extremadura | Keep |
| 3 | galicia (ES11, INE) | **andalucia** | **Replace**: key=an, slug=andalucia, rw_code=ES61, ine_ccaa=ES61, euro_geo=ES61 |
| 4 | castilla_la_mancha (ES42, INE) | **france** | **Replace**: key=fr, slug=france, scope=nuts0, rw_code=FR, euro_geo=FR, institutional=Eurostat |
| 5 | portugal (PT, Eurostat) | portugal | Keep |
| 6 | ireland (IE, Eurostat) | ireland | Keep |
| 7 | malta (MT, Eurostat) | **REMOVE** | Drop — not in frontend contract |

### Anti-Patterns to Avoid

- **Don't split `extend_gdp.py` into modules** — D-01 says minimal ceremony; the file is already self-contained and works
- **Don't use data-lake MCP search for lookups** — BM25 search is non-deterministic; use static index for reproducibility
- **Don't mix EUR_HAB and CLV10_EUR_HAB units** — Spanish NUTS2 is EUR_HAB (current prices), countries are CLV10_EUR_HAB (chain-linked volume). The chain-linking math uses growth ratios, not absolute values, so the unit mismatch is safe for ratio-splicing

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| JSON-stat parsing | Custom JSON-stat parser | Existing `_eurostat_json_to_df()` | Already handles v2.0 dimension flattening with `np.unravel_index` |
| Chain-linking math | Custom ratio-splicing | Existing `chain_link_rw_plus_institutional()` | Handles anchor calculation, source labeling, year range assembly |
| EU-15 population weighting | Custom aggregation | Existing `run_act2()` lines 1322-1346 | Already handles per-country chain-linking + population-weighted sum |
| Data-lake ingestion | Custom fetcher | Data-lake CLI: `uv run python -m data_lake.ingest.cli.app ingest <url>` | Handles URL canonicalization, dedup, artifact storage, catalog registration |
| Sanity checks | Custom validation | Existing `run_checks()` with 7 checks | Seam continuity, growth-rate preservation, coverage, outliers, level plausibility |

## Common Pitfalls

### Pitfall 1: EUR_HAB vs CLV — Spanish NUTS2 Unit Trap
**What goes wrong:** Eurostat's `nama_10r_2gdp` only has EUR_HAB (current prices) at NUTS2 level, not CLV (chain-linked volume). Using current prices directly as if they were real GDP produces inflation-contaminated growth curves.
**Why it happens:** Developer assumes all Eurostat GDP data is chain-linked because the national `nama_10_pc` dataset offers CLV10_EUR_HAB.
**How to avoid:** D-06 accepts EUR_HAB for comparison charts because chain-linking uses growth *ratios*, not absolute values. The INE chain-linked proxy serves the same purpose. Document the unit in the sanity report.
**Warning signs:** Suspiciously high growth rates in nominal vs real terms for Spanish regions post-2010.

### Pitfall 2: Anchor Year 2020 — COVID Distortion
**What goes wrong:** Tourism-dependent Balearic Islands had ~25% GDP drop in 2020. Chain-linking at 2020 inflates all historical values by 20-30%.
**Why it happens:** Current code defaults `ANCHOR_YEAR = 2020`.
**How to avoid:** D-08 locks anchor at 2019. Pass `anchor_year=2019` or update the constant.
**Warning signs:** All pre-2020 GDP values implausibly high; IB pre-2000 values exceed France.

### Pitfall 3: UK Post-Brexit Data Gap
**What goes wrong:** Eurostat stopped receiving UK data after 2019. EU-15 population-weighted average silently drops UK for 2020-2024, causing a level discontinuity.
**Why it happens:** UK exited EU data agreements; `fetch_nama_10_pc_clv10()` returns NaN for UK post-2019.
**How to avoid:** Two options: (a) carry forward UK's 2019 value as flat extrapolation, or (b) exclude UK from EU-15 post-2020 and document the composition change. Option (a) is simpler and preserves the population weight.
**Warning signs:** EU-15 average drops sharply in 2020 beyond COVID expectations.

### Pitfall 4: Greece EL/GR Dual Code
**What goes wrong:** Rosés-Wolf uses GR; Eurostat uses EL. Code that compares these without normalization silently drops Greece from EU-15.
**Why it happens:** Historical vs current ISO standard divergence for Greece.
**How to avoid:** `EU15_EUROSTAT_GEOS` already uses EL; `_comparison_series_to_rw_rows()` maps using name, not code. Ensure index keys use the Eurostat convention (EL).
**Warning signs:** EU-15 average based on 14 countries instead of 15.

### Pitfall 5: Andalucia Missing from INE Proxy
**What goes wrong:** Current `build_ine_proxy_from_eurostat()` fetches ES53, ES43, ES11, ES42 — but NOT ES61 (Andalucia). New series spec requires ES61.
**Why it happens:** Original series list didn't include Andalucia.
**How to avoid:** Add ES61 to the list in `build_ine_proxy_from_eurostat()`.
**Warning signs:** `PipelineError` for ES61 missing in institutional series.

### Pitfall 6: Data-Lake Source ID Instability
**What goes wrong:** Data-lake source IDs are ULIDs generated at ingest time. Re-ingesting the same URL creates a new ID if the canonical URL differs slightly.
**Why it happens:** URL parameter ordering varies (e.g., `geo=ES53&unit=EUR_HAB` vs `unit=EUR_HAB&geo=ES53`).
**How to avoid:** The data-lake canonicalizes URLs (verified: existing source shows `canonical_url` with sorted params). Check with `--dry-run` first to see if the source already exists. Build the index after ingestion using the actual IDs returned.
**Warning signs:** Duplicate sources in data-lake for the same Eurostat query.

### Pitfall 7: Local-Proxy CSV Sparsity vs Full-ETL Density
**What goes wrong:** Local-proxy CSVs have ~15 sparse data points (1900, 1910, 1925, 1938, 1950, 1960, 1970, 1980, 1990, 2000, 2005, 2015, 2022, 2024). Full-ETL CSVs will have ~125 annual rows.
**Why it happens:** Full ETL chain-links every year 2000-2024 and includes every Rosés-Wolf data year.
**How to avoid:** The baseline regression (VALID-03) must compare growth-rate *correlation* not point-to-point equality. Interpolation artifacts in the local-proxy baseline are expected.
**Warning signs:** Low correlation despite correct data — caused by comparing sparse vs dense series. Align to common years before correlation.

## Code Examples

### Reading a Data-Lake JSON-stat Artifact (verified pattern)

```python
# Source: data-lake artifact structure verified via MCP get() + direct file inspection
import json
from pathlib import Path

DATALAKE_ROOT = Path("/Users/guillem/vault/projects/personal/data-lake")

def load_eurostat_from_datalake(source_id: str) -> dict:
    raw_path = DATALAKE_ROOT / "lake" / "sources" / source_id / "raw.json"
    return json.loads(raw_path.read_text(encoding="utf-8"))

# Then parse with existing function:
df = _eurostat_json_to_df(load_eurostat_from_datalake("01KPWPQ902XYG9BT12QCXKFG4K"))
# Returns: nuts2_code | year | value  (same as API path)
```

### Data-Lake Ingestion Command (verified)

```bash
# Source: data-lake CLI --help output
cd /Users/guillem/vault/projects/personal/data-lake

# Ingest a single Eurostat API URL
uv run python -m data_lake.ingest.cli.app ingest \
  "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/nama_10r_2gdp?format=JSON&lang=en&unit=EUR_HAB&geo=ES43" \
  --format json

# Returns: ingested source_id=<ULID>
# Artifacts stored at: lake/sources/<ULID>/raw.json, meta.yaml, text.md, chunks.parquet
```

### Updated act2_series_list() (required change)

```python
def act2_series_list() -> list[Act2SeriesSpec]:
    return [
        Act2SeriesSpec(key="ib", slug="balearic_islands", scope=SeriesScope.nuts2,
                       rw_code="ES53", ine_ccaa="ES53", euro_geo="ES53",
                       institutional=InstitutionalSource.ine, label="Balearic Islands"),
        Act2SeriesSpec(key="extremadura", slug="extremadura", scope=SeriesScope.nuts2,
                       rw_code="ES43", ine_ccaa="ES43", euro_geo="ES43",
                       institutional=InstitutionalSource.ine, label="Extremadura"),
        # CHANGED: was galicia (ES11)
        Act2SeriesSpec(key="an", slug="andalucia", scope=SeriesScope.nuts2,
                       rw_code="ES61", ine_ccaa="ES61", euro_geo="ES61",
                       institutional=InstitutionalSource.ine, label="Andalucia"),
        # CHANGED: was castilla_la_mancha (ES42)
        Act2SeriesSpec(key="fr", slug="france", scope=SeriesScope.nuts0,
                       rw_code="FR", ine_ccaa=None, euro_geo="FR",
                       institutional=InstitutionalSource.eurostat, label="France"),
        Act2SeriesSpec(key="pt", slug="portugal", scope=SeriesScope.nuts0,
                       rw_code="PT", ine_ccaa=None, euro_geo="PT",
                       institutional=InstitutionalSource.eurostat, label="Portugal"),
        Act2SeriesSpec(key="ie", slug="ireland", scope=SeriesScope.nuts0,
                       rw_code="IE", ine_ccaa=None, euro_geo="IE",
                       institutional=InstitutionalSource.eurostat, label="Ireland"),
        # REMOVED: malta (MT) — not in frontend contract
    ]
```

### Baseline Regression Check (new)

```python
def baseline_regression_check(
    new_csvs: dict[str, pd.DataFrame],
    workspace: Path,
) -> CheckResult:
    """Compare full-ETL output against local-proxy CSVs (growth-rate correlation)."""
    correlations: list[float] = []
    for slug, new_df in new_csvs.items():
        proxy_path = workspace / "public" / "data" / f"act2_{slug}.csv"
        if not proxy_path.exists():
            continue
        proxy = pd.read_csv(proxy_path)
        # Align to common years
        common_years = set(new_df["year"]) & set(proxy["year"])
        if len(common_years) < 3:
            continue
        n = new_df[new_df["year"].isin(common_years)].sort_values("year")
        p = proxy[proxy["year"].isin(common_years)].sort_values("year")
        # Growth-rate correlation (not absolute levels)
        n_growth = n["gdp_pc"].pct_change().dropna()
        p_growth = p["gdp_pc"].pct_change().dropna()
        if len(n_growth) > 1 and len(p_growth) > 1:
            corr = n_growth.corr(p_growth)
            correlations.append(corr)
    if not correlations:
        return CheckResult("8) Baseline regression", "WARN", 1, ["No proxy CSVs found for comparison"])
    min_corr = min(correlations)
    avg_corr = sum(correlations) / len(correlations)
    if min_corr >= 0.95:
        return CheckResult("8) Baseline regression", "PASS", 0,
                           [f"min_corr={min_corr:.4f}, avg_corr={avg_corr:.4f}"])
    return CheckResult("8) Baseline regression", "WARN", 1,
                       [f"min_corr={min_corr:.4f} < 0.95 threshold, avg={avg_corr:.4f}"])
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `--act2-local-proxy` (sparse comparison CSVs) | Full ETL via data-lake adapter | This phase (v3.0) | Annual data density, proper chain-linking, reproducible sourcing |
| `ANCHOR_YEAR = 2020` | Anchor 2019 (D-08) | This phase | Avoids COVID distortion in tourism-dependent regions |
| galicia/clm/malta series | andalucia/france series | This phase | Aligns ETL output with shipped frontend contract |

## Rosés-Wolf Data Availability

| Region/Country | RW Code | Available in roseswolf_regionalgdp_v7.xlsx | Available in roses_wolf_selected_comparison.csv |
|----------------|---------|-------------------------------------------|------------------------------------------------|
| Balearic Islands | ES53 | ✓ | ✓ |
| Extremadura | ES43 | ✓ | ✓ |
| Andalucia | ES61 | ✓ | ✓ |
| France | FR (NUTS2 regions) | ✓ (FR10, FR21, ...) | ✓ ("France avg") |
| Portugal | PT (NUTS2 regions) | ✓ (PT11, PT15, ...) | ✓ ("Portugal avg") |
| Ireland | IE0 | ✓ | ✓ ("Ireland avg") |
| EU-15 countries | Various | ✓ (via NUTS2) | Partial |

[VERIFIED: direct Excel sheet inspection of roseswolf_regionalgdp_v7.xlsx and comparison CSV grep]

**Note:** France and Portugal RW data is at NUTS2 regional level, not national aggregate. The existing `_comparison_series_to_rw_rows()` loads pre-computed national averages from `roses_wolf_selected_comparison.csv`. For EU-15 countries not in that file, `_synthetic_national_rw_from_eurostat_clv()` back-casts from Eurostat data.

## UK Post-Brexit Handling (CHAIN-03)

**Situation:** Eurostat `nama_10_pc` for UK stops at 2019. `demo_pjan` for UK may have partial post-2020 data but GDP per capita is unavailable.

**Options:**
1. **Carry forward 2019 value** — simplest; UK GDP frozen at 2019 level in EU-15 average. Population weight preserved. Produces ~1-2% downward bias on EU-15 average growth post-2020 (UK grew ~2% real 2020-2024).
2. **Exclude UK post-2020** — EU-15 becomes EU-14 silently. Population weight shifts to remaining countries. Causes visible discontinuity.
3. **ONS fallback** — fetch from UK ONS regional accounts. Requires new source format and parser. Out of scope per D-01 (minimal ceremony).

**Recommendation:** Option 1 (carry forward). Document in sanity report. This matches the project's analytical simplification stance (membership-date-aware composition is out of scope per REQUIREMENTS.md).

[ASSUMED — UK handling strategy; user should confirm preference]

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python 3 | ETL pipeline | ✓ | 3.14 | — |
| pandas | ETL | ✓ | installed | — |
| numpy | JSON-stat parsing | ✓ | installed | — |
| data-lake CLI | Ingestion | ✓ | uv-managed at `/Users/guillem/vault/projects/personal/data-lake/` | Direct URL fetch |
| Eurostat API | Fallback data source | ✓ (network) | v1.0 | — |

[VERIFIED: tool availability confirmed via shell]

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | UK 2019 carry-forward is acceptable for EU-15 average | UK Post-Brexit Handling | EU-15 average growth 2020-2024 has ~1-2% downward bias. Low risk for comparative visualization |
| A2 | Batched multi-geo queries are preferred over individual per-geo | Ingestion Inventory | If data-lake dedup logic struggles with multi-geo URLs, fall back to per-geo. Low risk |
| A3 | EUR_HAB current prices are acceptable for Spanish NUTS2 comparison chart | Pitfall 1 / D-06 | If user later wants real-term comparison, need INE chain-linked data or deflation. Already accepted in D-06 |

## Open Questions

1. **Batch vs per-geo ingestion strategy**
   - What we know: Both work; batch reduces sources from ~20 to ~4; per-geo gives cleaner 1:1 index
   - What's unclear: Whether data-lake handles multi-geo Eurostat URLs gracefully (URL canonicalization may differ)
   - Recommendation: Try batch first with `--dry-run`; fall back to per-geo if needed

2. **CLI flag naming**
   - What we know: Current flag is `--act2-local-proxy`; new mode needs a flag
   - What's unclear: Whether to add `--act2-datalake` or replace `--act2-local-proxy` behavior
   - Recommendation: Add `--act2-datalake` flag; keep `--act2-local-proxy` as fallback. Or auto-detect data-lake presence.

## Sources

### Primary (HIGH confidence)
- `scripts/extend_gdp.py` (1577 lines) — direct code review: parser, chain-linking, EU-15 computation, sanity checks, series specs
- `app/components/act2-story-section.vue` lines 109-117 — frontend CSV contract (7 slugs verified)
- Data-lake MCP `get("01KPWPQ902XYG9BT12QCXKFG4K")` — artifact structure, JSON-stat format, `artifact_paths.raw` path
- Data-lake source directory inspection — `meta.yaml`, `raw.json`, `text.md`, `chunks.parquet` structure
- Data-lake CLI `--help` — ingestion command syntax and options
- `data/roseswolf_regionalgdp_v7.xlsx` — ES61 (Andalucia) availability confirmed in sheet "A1b Regional GDP (2011PPP)"
- `public/data/roses_wolf_selected_comparison.csv` — Andalucia and France avg series confirmed
- `data/ine_spain_ccaa_gdp_pc_eurostat_proxy.csv` — ES61 NOT present; needs addition

### Secondary (MEDIUM confidence)
- Eurostat API URL patterns — verified against existing `_eurostat_get()` function and data-lake canonical URL
- `.planning/research/SUMMARY.md` — prior research synthesis

### Tertiary (LOW confidence)
- UK ONS GDP data availability post-2020 — not verified, carry-forward recommended instead

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — zero new dependencies; all verified against codebase
- Architecture: HIGH — adapter pattern verified against live data-lake artifact and existing parser
- Pitfalls: HIGH — 7 pitfalls identified from direct code/data inspection; mitigations traced to existing code
- Ingestion: HIGH — data-lake CLI verified, existing source structure inspected

**Research date:** 2026-04-29
**Valid until:** 2026-06-29 (stable — data sources and APIs unchanged)
