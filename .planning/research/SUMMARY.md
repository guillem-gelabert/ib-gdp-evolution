# Project Research Summary

**Project:** IB GDP Evolution — v3.0 Full Act II ETL
**Domain:** Multi-region GDP chain-linking ETL (Eurostat + Rosés-Wolf → static CSV → D3 scrollytelling)
**Researched:** 2026-04-29
**Confidence:** HIGH

## Executive Summary

The v3.0 milestone replaces the temporary `--act2-local-proxy` data path with a fully sourced ETL that reads Eurostat JSON-stat v2.0 artifacts from the project's data-lake, chain-links them with Rosés-Wolf historical data, and emits the same 7 `act2_*.csv` files the frontend already consumes. The existing `extend_gdp.py` already implements ~90% of the required logic (JSON-stat parsing, chain-linking, EU-15 weighted average, sanity checks, CSV output). The primary new work is a thin data-lake adapter layer, a catalog index file, series-spec alignment with the frontend, and a baseline regression check.

No new Python dependencies are needed. The data-lake stores Eurostat API responses as local JSON-stat v2.0 files identical in structure to what the existing `_eurostat_json_to_df()` parser already handles. The recommended architecture is a Strangler Fig adapter: route each Eurostat data fetch through a `fetch_eurostat_series()` function that tries the data-lake first and falls back to the live API. This preserves the existing code paths while migrating to reproducible, offline-capable data sourcing.

The critical risks are: (1) mixing current-price EUR_HAB with chain-linked volume data for Spanish NUTS2 regions (Eurostat offers no CLV at NUTS2 — must use INE), (2) anchor-year 2020 COVID distortion biasing tourism-dependent regions, (3) UK data gap post-2020 breaking EU-15 average continuity, and (4) a series-spec mismatch where the ETL defines galicia/castilla_la_mancha/malta but the frontend expects andalucia/france. All four have known mitigations documented in the research.

## Key Findings

### Recommended Stack

No dependency changes. The existing stack (Python 3, pandas, numpy, openpyxl, json/pathlib stdlib) handles the full requirement. The data-lake provides local JSON-stat files that the existing `_eurostat_json_to_df()` parser reads without modification.

**Core technologies (all existing):**
- **pandas**: DataFrame operations, chain-linking math, CSV output — already in use
- **json (stdlib)**: Parse data-lake JSON-stat artifacts — already used for API responses
- **numpy**: `np.unravel_index` in JSON-stat dimension flattening — already imported

**Evaluated and rejected:** pyjstat (unmaintained since 2023), jsonstat.py (unnecessary abstraction), eurostat/eurostatpy (API wrappers irrelevant for local file reading). See STACK.md for details.

### Expected Features

**Must have (table stakes — F-01 through F-10):**
- **F-01: Data-lake ingestion** — read Eurostat JSON-stat from local data-lake artifacts instead of live API
- **F-04: Dual-dataset routing** — NUTS2 regions via `nama_10r_2gdp`, countries via `nama_10_pc`
- **F-05: INE chain-linking for Spanish NUTS2** — Eurostat lacks CLV at regional level; INE is required
- **F-06: EU-15 population-weighted average** — 15-country weighted mean with per-country chain-linking
- **F-09: Baseline regression** — compare full-ETL output against local-proxy baseline
- **F-10: Same CSV contract** — `year,gdp_pc,source,unit` schema, same filenames

**Should have (differentiators — defer to v3.1+):**
- D-01: Data-lake freshness check
- D-04: Provisional/estimated flag propagation to frontend

**Anti-features (explicitly excluded):**
- Live API calls in ETL hot path
- Membership-date-aware EU-15 composition
- PPS/current-price GDP series mixing
- Server-side data API

**Critical path:** F-01 → F-02 → F-04 → F-07 → F-10 → F-09

### Architecture Approach

The adapter-with-fallback pattern inserts a thin data-lake resolution layer between `run_act2()` and the Eurostat API. A static catalog index file (`datalake_eurostat_index.json`) maps `(dataset, geo, unit)` triples to data-lake source IDs deterministically — avoiding unreliable BM25 search at runtime. All new functions live in `extend_gdp.py` (no premature module splitting).

**Major components:**
1. **`fetch_eurostat_series()`** — unified entry point: data-lake → API fallback
2. **`load_eurostat_from_datalake()`** — read + parse a single data-lake JSON-stat artifact
3. **`load_datalake_index()`** — read the catalog index JSON
4. **Updated `act2_series_list()`** — aligned with frontend (add andalucia/france, remove galicia/clm/malta)
5. **Baseline regression check** — new sanity check comparing full-ETL vs local-proxy output

**Critical finding:** The frontend expects 7 CSVs (balearic_islands, extremadura, andalucia, portugal, ireland, france, eu15_avg) but `act2_series_list()` defines galicia/castilla_la_mancha/malta instead of andalucia/france. The ETL must align to the shipped frontend contract.

### Critical Pitfalls

1. **nama_10r_2gdp has no CLV data for NUTS2** — Spanish regional Eurostat data is current prices only; must use INE chain-linked data (or Eurostat proxy with explicit deflation). Mixing EUR_HAB with PPP chain-linking produces inflation-contaminated curves.
2. **Anchor year 2020 is a COVID year** — tourism-dependent Balearic Islands had ~25% GDP drop; chain-linking at 2020 inflates all historical values by 20-30%. Switch to 2019 anchor.
3. **UK data gap post-2020** — Eurostat stopped receiving UK data after Brexit; EU-15 average silently drops UK, causing a level discontinuity. Need ONS fallback or OECD projection.
4. **PPP vs CLV unit mixing** — Rosés-Wolf uses 2011 PPP dollars; Eurostat uses chain-linked 2010 euros. Only ratio-splicing (growth-rate preservation) is safe — never concatenate raw values.
5. **Greece EL/GR dual code** — Eurostat uses EL, Rosés-Wolf uses GR. Normalize at ingestion boundary.

## Implications for Roadmap

### Phase 1: Data-Lake Ingestion & Catalog Index
**Rationale:** Everything downstream depends on having Eurostat datasets available locally. The data-lake currently has only 1 source (ES53/EUR_HAB); the full ETL requires ~20+ sources across `nama_10r_2gdp`, `nama_10_pc`, and `demo_pjan`.
**Delivers:** All required Eurostat JSON-stat artifacts ingested into data-lake + `datalake_eurostat_index.json` mapping file.
**Addresses:** F-01 (data-lake ingestion)
**Avoids:** P11 (API query limits), P12 (provisional data not tracked)
**Note:** This phase is the prerequisite gate — nothing else can run until data-lake sources exist.

### Phase 2: Data-Lake Adapter & Series Alignment
**Rationale:** With data-lake populated, build the adapter functions and fix the series-spec mismatch before any chain-linking work.
**Delivers:** `fetch_eurostat_series()`, `load_eurostat_from_datalake()`, `load_datalake_index()`, updated `act2_series_list()` aligned with frontend, geo-code normalization (EL/GR).
**Addresses:** F-01, F-02, F-04, F-03 (NUTS correspondence)
**Avoids:** P1 (current-price trap — unit validation per series), P5 (EL/GR dual code), P8 (NUTS version mismatch)

### Phase 3: Chain-Linking & EU-15 Computation
**Rationale:** With data flowing through the adapter, wire `run_act2()` to use `fetch_eurostat_series()` and validate the full chain-linking pipeline including EU-15 weighted average.
**Delivers:** Full ETL pipeline producing 7 `act2_*.csv` files with correct chain-linking, EU-15 average with UK fallback handling, anchor year switched to 2019.
**Addresses:** F-05, F-06, F-07
**Avoids:** P2 (COVID anchor), P3 (UK gap), P4 (unit mixing), P9 (anachronistic EU-15 label), P10 (non-additivity)

### Phase 4: Sanity Suite & Baseline Regression
**Rationale:** With CSVs being produced, validate correctness against existing checks and baseline output.
**Delivers:** All 7 existing checks passing + new baseline regression check comparing full-ETL vs local-proxy output, CLI integration (`--act2-datalake` or auto-detect).
**Addresses:** F-08, F-09, F-10
**Avoids:** P6 (interpolation artifacts in YoY checks), P7 (INE coverage gaps caught early)

### Phase Ordering Rationale

- **Phase 1 is a hard prerequisite** — without data-lake sources, the adapter has nothing to read. This is the gate.
- **Phase 2 before Phase 3** — adapter + series alignment must be correct before chain-linking runs; otherwise wrong units/geos propagate through.
- **Phase 3 before Phase 4** — sanity checks and regression need output CSVs to validate against.
- **Phases 2 and 3 could partially overlap** — functions being built in Phase 2 can be tested with the single existing data-lake source (ES53) while Phase 1 completes ingestion of the remaining sources.

### Research Flags

Phases likely needing deeper research during planning:
- **Phase 1:** Data-lake ingestion tooling — need to determine how to batch-ingest ~20 Eurostat API responses into the data-lake (via MCP, CLI, or script). The `project-0-ib-gdp-evolution-data-lake` MCP's capabilities for batch ingestion should be investigated.
- **Phase 3 (EU-15):** UK post-Brexit data sourcing — ONS data format and availability for 2021–2024 needs verification.

Phases with standard patterns (skip research-phase):
- **Phase 2:** Adapter pattern is straightforward; all functions are small and well-specified by ARCHITECTURE.md.
- **Phase 4:** Sanity checks extend existing patterns; baseline regression is a simple CSV diff.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | Zero new dependencies; verified existing parser against actual data-lake artifact |
| Features | HIGH | All 10 table-stakes features traced to existing code + clearly scoped new work (~150–250 lines) |
| Architecture | HIGH | Adapter pattern verified against live MCP responses and codebase analysis |
| Pitfalls | HIGH | 13 pitfalls identified with prevention strategies; critical ones (P1–P4) have known mitigations in existing code |

**Overall confidence:** HIGH

### Gaps to Address

- **Data-lake batch ingestion workflow:** How to efficiently ingest ~20 Eurostat datasets is undefined. May require a helper script or MCP batch tooling.
- **UK post-Brexit GDP source:** ONS data format and chain-linked volume availability for 2021–2024 needs verification during Phase 3 planning.
- **INE data freshness:** Current INE CRE Excel coverage unknown — may only go to 2022 or 2023. Need to verify coverage for all 3 Spanish NUTS2 regions.
- **Frontend density handling:** Local-proxy CSVs have ~15 sparse years; full-ETL CSVs will have ~125 annual rows. Verify `act2-chart.vue` handles annual data density without performance issues.

## Sources

### Primary (HIGH confidence)
- Data-lake artifact `01KPWPQ902XYG9BT12QCXKFG4K/raw.json` — direct JSON-stat v2.0 structure inspection
- `scripts/extend_gdp.py` (1577 lines) — direct code review of parser, chain-linking, EU-15 computation, sanity checks
- `app/components/act2-story-section.vue` lines 110–116 — frontend CSV contract
- `public/data/act2_balearic_islands.csv` — output CSV schema verification
- Data-lake MCP `get`/`search`/`list_sources` — live artifact path and coverage verification

### Secondary (MEDIUM confidence)
- Eurostat API documentation — NAMA dataset unit availability, JSON-stat v2.0 format
- Eurostat NUTS correspondence tables — NUTS2 code stability for Spain (2013–2024)
- Rosés-Wolf v7 (CEPR, 2025 release) — coverage 1900–2022 at NUTS2, 2011 PPP dollars

### Tertiary (LOW confidence)
- UK ONS GDP data availability post-2020 — not directly verified, needs investigation in Phase 3
- INE CRE Excel year coverage — assumed current but not verified for all 3 target NUTS2 codes

---
*Research completed: 2026-04-29*
*Ready for roadmap: yes*
