# Requirements: IB GDP Evolution

**Defined:** 2026-04-29
**Core Value:** Present the long-run GDP-per-capita story as a beautiful, editorial, animated reading experience that makes the historical arc legible at a glance.

## v3.0 Requirements

Requirements for milestone v3.0: Full Act II ETL. Each maps to roadmap phases.

### Data Ingestion

- [ ] **INGEST-01**: Pipeline can read Eurostat JSON-stat v2.0 artifacts from data-lake local paths instead of live API calls
- [ ] **INGEST-02**: All required Eurostat datasets are ingested into the data-lake (~20 sources across nama_10r_2gdp, nama_10_pc, demo_pjan)
- [ ] **INGEST-03**: A static catalog index file maps (dataset, geo, unit) triples to data-lake source IDs deterministically

### ETL Pipeline

- [ ] **ETL-01**: Data-lake adapter function resolves Eurostat data from data-lake first, falls back to live API
- [ ] **ETL-02**: `act2_series_list()` is aligned with the shipped frontend contract (andalucia, france — not galicia, castilla_la_mancha, malta)
- [ ] **ETL-03**: Dual-dataset routing: NUTS2 regions via nama_10r_2gdp, countries via nama_10_pc
- [ ] **ETL-04**: Geo-code normalization handles Eurostat EL vs Rosés-Wolf GR for Greece

### Chain-Linking

- [ ] **CHAIN-01**: Spanish NUTS2 regions use INE chain-linked data (Eurostat lacks CLV at regional level)
- [ ] **CHAIN-02**: EU-15 population-weighted average computed from 15 individual country series
- [ ] **CHAIN-03**: UK post-Brexit data gap handled (fallback source or documented exclusion post-2020)
- [ ] **CHAIN-04**: Anchor year is 2019 (not COVID-distorted 2020)

### Validation

- [ ] **VALID-01**: Output preserves the same CSV contract (year, gdp_pc, source, unit) and filenames the frontend expects
- [ ] **VALID-02**: All existing sanity checks pass on the full-ETL output
- [ ] **VALID-03**: Baseline regression compares full-ETL output against local-proxy CSVs (growth-rate correlation, not absolute levels)

## Future Requirements

### Deferred to v3.1+

- **FRESH-01**: Data-lake freshness check before ETL run
- **PROV-01**: Provisional/estimated flag propagation from Eurostat status to frontend
- **AUTO-01**: Auto-detect data-lake vs API mode based on environment

## Out of Scope

| Feature | Reason |
|---------|--------|
| Live API calls in ETL hot path | Data-lake provides reproducible, offline-capable sourcing |
| Membership-date-aware EU-15 composition | Analytical simplification per v2.0 decision |
| PPS/current-price GDP series mixing | Only chain-linked volume data is valid for long-run comparison |
| Server-side data API | Static CSV delivery remains sufficient |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| INGEST-01 | Phase 5 | Pending |
| INGEST-02 | Phase 5 | Pending |
| INGEST-03 | Phase 5 | Pending |
| ETL-01 | Phase 6 | Pending |
| ETL-02 | Phase 6 | Pending |
| ETL-03 | Phase 6 | Pending |
| ETL-04 | Phase 6 | Pending |
| CHAIN-01 | Phase 7 | Pending |
| CHAIN-02 | Phase 7 | Pending |
| CHAIN-03 | Phase 7 | Pending |
| CHAIN-04 | Phase 7 | Pending |
| VALID-01 | Phase 8 | Pending |
| VALID-02 | Phase 8 | Pending |
| VALID-03 | Phase 8 | Pending |

**Coverage:**
- v3.0 requirements: 14 total
- Mapped to phases: 14/14 ✓
- Unmapped: 0

---
*Requirements defined: 2026-04-29*
*Last updated: 2026-04-29 after roadmap creation*
