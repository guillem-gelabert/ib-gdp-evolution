# Phase 5: Full Act II ETL - Context

**Gathered:** 2026-04-29
**Status:** Ready for planning

<domain>
## Phase Boundary

Replace the `--act2-local-proxy` data path with a complete ETL that: (1) ingests all needed Eurostat datasets into the data-lake, (2) reads them back via data-lake artifact paths, (3) chain-links with Rosés-Wolf, and (4) emits the same 7 `act2_*.csv` files the frontend consumes. This is a single collapsed phase covering all v3.0 requirements (INGEST-01 through VALID-03).

</domain>

<decisions>
## Implementation Decisions

### Approach
- **D-01:** This is a one-off data pipeline task — minimal ceremony, just get the data flowing.
- **D-02:** Collapse original 4 phases (5-8) into a single phase. All work happens here.

### Data Ingestion
- **D-03:** Use the data-lake project's ingestion scripts (pattern from `fetch_balearic_gdp_sources.py`) to fetch Eurostat API responses and store as raw JSON artifacts.
- **D-04:** The data-lake MCP is read-only — ingestion happens through the data-lake project's Python scripts at `/Users/guillem/vault/projects/personal/data-lake/`.
- **D-05:** Build a static `datalake_eurostat_index.json` mapping (dataset, geo, unit) → source_id for deterministic lookup.

### ETL Pipeline
- **D-06:** Uniform approach for all regions: Rosés-Wolf (1900-1999) + Eurostat NAMA (2000-2024). No INE special-casing needed if Eurostat current-price EUR_HAB is acceptable for the comparison chart (the chart shows relative trajectories, not absolute purchasing power).
- **D-07:** `act2_series_list()` must match the 7 frontend CSVs: balearic_islands, extremadura, andalucia, portugal, ireland, france, eu15_avg.
- **D-08:** Anchor year 2019 (avoid COVID-distorted 2020).
- **D-09:** Data-lake adapter with API fallback: try local artifact first, fall back to live Eurostat API.

### Validation
- **D-10:** Sanity checks must pass. Baseline regression compares growth-rate correlation vs local-proxy, not absolute levels.

### Claude's Discretion
- Exact Eurostat API query parameters and NUTS code mapping
- Internal function organization within `extend_gdp.py`
- Specific sanity check thresholds

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### ETL Pipeline
- `scripts/extend_gdp.py` — Existing ETL with chain-linking logic, Act2SeriesSpec, local-proxy path
- `.planning/research/SUMMARY.md` — Research synthesis with pitfalls and architecture recommendations

### Data-Lake
- `/Users/guillem/vault/projects/personal/data-lake/fetch_balearic_gdp_sources.py` — Pattern for data-lake ingestion scripts
- `/Users/guillem/vault/projects/personal/data-lake/fetch_sources.py` — General source fetching script

### Frontend Contract
- `app/components/act2-story-section.vue` lines 110-116 — CSV filenames the frontend loads

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `_eurostat_json_to_df()` in extend_gdp.py — already parses Eurostat JSON-stat v2.0 format
- `chain_link_rw_plus_institutional()` — existing chain-linking function
- `run_act2_local_proxy()` — current entry point to replace
- `act2_series_list()` — series metadata (needs alignment with frontend)
- `EU15_EUROSTAT_GEOS` — EU-15 country code list (EL for Greece)

### Established Patterns
- Data-lake stores sources under `lake/sources/{id}/raw.json` with `meta.yaml`
- Existing ETL uses `urllib.request` for live Eurostat API calls
- Sanity checks return `SanityCheck` tuples processed by `write_report()`

### Integration Points
- New `--act2-datalake` CLI flag (or replace `--act2-local-proxy` behavior)
- Data-lake artifact paths from MCP `get()` response's `artifact_paths.raw`
- Frontend loads from `public/data/act2_*.csv` — contract must not change

</code_context>

<specifics>
## Specific Ideas

No specific requirements — open to standard approaches. Keep it simple and direct.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 05-data-lake-ingestion-catalog-index*
*Context gathered: 2026-04-29*
