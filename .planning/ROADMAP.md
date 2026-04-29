# Roadmap: IB GDP Evolution

## Milestones

- ✅ **v1.0 Act I Chart Upgrade** — Phase 1 shipped 2026-04-23. Full shipped snapshot preserved in `.planning/milestones/v2.0-ROADMAP.md`.
- ✅ **v2.0 Act II — Who Else Got Richer** — Phases 2-4 shipped 2026-04-23 in documented local-proxy mode. See `.planning/milestones/v2.0-ROADMAP.md`.
- 🚧 **v3.0 Full Act II ETL** — Phase 5 (in progress)

## Phases

- [ ] **Phase 5: Full Act II ETL** - Ingest Eurostat data into data-lake, build adapter + chain-linking pipeline, emit act2_*.csv files, validate against baseline

## Phase Details

### 🚧 v3.0 Full Act II ETL (In Progress)

**Milestone Goal:** Replace the `--act2-local-proxy` data path with a pipeline that sources Eurostat NAMA regional GDP from the data-lake MCP, chain-links with Rosés-Wolf, and emits the same `act2_*.csv` files.

#### Phase 5: Full Act II ETL
**Goal**: End-to-end replacement of the local-proxy path — ingest data, build adapter, chain-link, validate, emit CSVs
**Depends on**: Nothing (single phase for v3.0)
**Requirements**: INGEST-01, INGEST-02, INGEST-03, ETL-01, ETL-02, ETL-03, ETL-04, CHAIN-01, CHAIN-02, CHAIN-03, CHAIN-04, VALID-01, VALID-02, VALID-03
**Success Criteria** (what must be TRUE):
  1. All required Eurostat datasets are ingested in the data-lake with a static catalog index
  2. `extend_gdp.py` reads Eurostat data from data-lake artifacts (fallback to live API)
  3. `act2_series_list()` matches the 7 frontend CSV filenames (balearic_islands, extremadura, andalucia, portugal, ireland, france, eu15_avg)
  4. Chain-linking uses 2019 anchor year for all series
  5. EU-15 population-weighted average computed from individual country series
  6. All 7 `act2_*.csv` files emitted with correct `year,gdp_pc,source,unit` schema
  7. Sanity checks pass and growth-rate correlation ≥0.95 vs local-proxy baseline
**Plans**: TBD

## Progress

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 5. Full Act II ETL | v3.0 | 0/? | Not started | - |

---
*Roadmap created: 2026-04-29 for v3.0 Full Act II ETL*
*Updated: 2026-04-29 — collapsed phases 5-8 into single phase 5*
