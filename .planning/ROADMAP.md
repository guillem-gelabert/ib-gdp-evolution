# Roadmap: IB GDP Evolution

## Milestones

- ✅ **v1.0 Act I Chart Upgrade** — Phase 1 shipped 2026-04-23. Full shipped snapshot preserved in `.planning/milestones/v2.0-ROADMAP.md`.
- ✅ **v2.0 Act II — Who Else Got Richer** — Phases 2-4 shipped 2026-04-23 in documented local-proxy mode. See `.planning/milestones/v2.0-ROADMAP.md`.
- 🚧 **v3.0 Full Act II ETL** — Phases 5-8 (in progress)

## Phases

- [ ] **Phase 5: Data-Lake Ingestion & Catalog Index** - Ingest all required Eurostat datasets into data-lake and build the deterministic lookup index
- [ ] **Phase 6: Data-Lake Adapter & Series Alignment** - Build the adapter layer that resolves Eurostat data from data-lake and align series specs with the frontend contract
- [ ] **Phase 7: Chain-Linking & EU-15 Computation** - Wire the full chain-linking pipeline through the adapter and compute the EU-15 weighted average
- [ ] **Phase 8: Sanity Suite & Baseline Regression** - Validate full-ETL output against existing checks and the local-proxy baseline

## Phase Details

### 🚧 v3.0 Full Act II ETL (In Progress)

**Milestone Goal:** Replace the `--act2-local-proxy` data path with a pipeline that sources Eurostat NAMA regional GDP from the data-lake MCP, chain-links with Rosés-Wolf, and emits the same `act2_*.csv` files.

#### Phase 5: Data-Lake Ingestion & Catalog Index
**Goal**: All required Eurostat datasets are available locally in the data-lake with a deterministic catalog index
**Depends on**: Nothing (first phase of v3.0)
**Requirements**: INGEST-01, INGEST-02, INGEST-03
**Success Criteria** (what must be TRUE):
  1. Pipeline can read Eurostat JSON-stat v2.0 artifacts from local data-lake paths without any live API calls
  2. All ~20 required Eurostat sources are present in the data-lake across nama_10r_2gdp, nama_10_pc, and demo_pjan datasets
  3. A static `datalake_eurostat_index.json` maps every required (dataset, geo, unit) triple to a data-lake source ID deterministically
**Plans**: TBD

#### Phase 6: Data-Lake Adapter & Series Alignment
**Goal**: ETL pipeline reads Eurostat data through a unified adapter and targets the correct set of regions and countries matching the frontend
**Depends on**: Phase 5
**Requirements**: ETL-01, ETL-02, ETL-03, ETL-04
**Success Criteria** (what must be TRUE):
  1. `fetch_eurostat_series()` resolves data from data-lake first, falling back to live API only when a source is missing
  2. `act2_series_list()` matches the 7 frontend CSV filenames exactly (balearic_islands, extremadura, andalucia, portugal, ireland, france, eu15_avg)
  3. NUTS2 regions route through nama_10r_2gdp and countries route through nama_10_pc automatically
  4. Greece geo-code normalization handles Eurostat EL vs Rosés-Wolf GR transparently
**Plans**: TBD

#### Phase 7: Chain-Linking & EU-15 Computation
**Goal**: Full chain-linking pipeline produces the 7 act2_*.csv files with correct historical splicing and EU-15 population-weighted average
**Depends on**: Phase 6
**Requirements**: CHAIN-01, CHAIN-02, CHAIN-03, CHAIN-04
**Success Criteria** (what must be TRUE):
  1. Spanish NUTS2 regions (ES53, ES43, ES61) use INE chain-linked volume data instead of Eurostat current-price data
  2. EU-15 population-weighted average is computed from 15 individual country series
  3. UK post-Brexit data gap is handled (fallback source or documented exclusion post-2020) without breaking the EU-15 average
  4. Anchor year is 2019, avoiding COVID-year distortion
  5. Running `extend_gdp.py` in full-ETL mode produces all 7 act2_*.csv files the frontend loads without error
**Plans**: TBD

#### Phase 8: Sanity Suite & Baseline Regression
**Goal**: Full-ETL output is validated against existing sanity checks and the local-proxy baseline CSVs
**Depends on**: Phase 7
**Requirements**: VALID-01, VALID-02, VALID-03
**Success Criteria** (what must be TRUE):
  1. All 7 output CSVs preserve the `year,gdp_pc,source,unit` schema and the expected filenames
  2. All existing sanity checks pass on full-ETL output without modification
  3. Baseline regression test shows high growth-rate correlation (≥0.95) between full-ETL and local-proxy CSVs for each series
**Plans**: TBD

## Progress

**Execution Order:** 5 → 6 → 7 → 8

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 5. Data-Lake Ingestion & Catalog Index | v3.0 | 0/? | Not started | - |
| 6. Data-Lake Adapter & Series Alignment | v3.0 | 0/? | Not started | - |
| 7. Chain-Linking & EU-15 Computation | v3.0 | 0/? | Not started | - |
| 8. Sanity Suite & Baseline Regression | v3.0 | 0/? | Not started | - |

---
*Roadmap created: 2026-04-29 for v3.0 Full Act II ETL*
