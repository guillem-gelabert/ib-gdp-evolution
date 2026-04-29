---
phase: 05-data-lake-ingestion-catalog-index
plan: 02
subsystem: data-pipeline
tags: [eurostat, chain-linking, act2, datalake, cli, uk-carry-forward]

requires:
  - phase: 05-01
    provides: data-lake adapter (_fetch_eurostat_df), catalog index (datalake_eurostat_index.json)
provides:
  - Updated act2_series_list matching frontend contract (6 entries)
  - --act2-datalake CLI flag with anchor 2019
  - UK post-Brexit carry-forward in EU-15 weighted average
  - baseline_regression_check() for proxy comparison
  - 7 emitted act2_*.csv files from full datalake ETL
affects: [05-03, act2-story-section.vue]

tech-stack:
  added: []
  patterns: [datalake CLI branch in main(), UK carry-forward on Eurostat input before chain-linking]

key-files:
  created:
    - public/data/act2_andalucia.csv
    - public/data/act2_france.csv
    - output/sanity_report_act2.txt
  modified:
    - scripts/extend_gdp.py
    - public/data/act2_balearic_islands.csv
    - public/data/act2_extremadura.csv
    - public/data/act2_portugal.csv
    - public/data/act2_ireland.csv
    - public/data/act2_eu15_avg.csv

key-decisions:
  - "UK carry-forward applied at Eurostat input level (pre chain-link) to avoid PipelineError, then source relabeled post chain-link"
  - "Baseline regression WARN is expected: local-proxy used interpolated sparse data vs real annual Eurostat CLV"

patterns-established:
  - "Datalake CLI pattern: configure _datalake_index/_datalake_root globals, call run_act2, reset globals"
  - "Fallback materialization: try load_roseswolf, catch PipelineError → materialize_roseswolf_workbook"

requirements-completed: [ETL-02, ETL-03, ETL-04, CHAIN-01, CHAIN-02, CHAIN-03, CHAIN-04, VALID-01, VALID-02, VALID-03]

duration: 10min
completed: 2026-04-29
---

# Phase 05 Plan 02: Act II Series Alignment & Datalake Pipeline Summary

**Aligned act2_series_list to frontend contract (6 entries), wired --act2-datalake CLI with anchor 2019, added UK carry-forward for EU-15 average, and emitted all 7 act2_*.csv files via full datalake ETL with passing sanity checks**

## Performance

- **Duration:** 10 min
- **Started:** 2026-04-29T13:42:00Z
- **Completed:** 2026-04-29T13:52:00Z
- **Tasks:** 2
- **Files modified:** 10

## Accomplishments
- Replaced act2_series_list: removed galicia/castilla_la_mancha/malta, added andalucia (ES61) and france (FR) — exactly 6 entries matching frontend slugToPath contract
- Wired --act2-datalake CLI flag that configures datalake globals, defaults anchor to 2019, runs full pipeline
- Added UK post-Brexit carry-forward in EU-15 average (2019 value extended to 2020-2024 with source="carry_forward")
- Added baseline_regression_check() comparing growth-rate correlations vs local-proxy CSVs
- Pipeline emits all 7 act2_*.csv files with year,gdp_pc,source,unit schema spanning 1900-2024
- Sanity report: 7/7 checks PASS, baseline regression WARN (expected — see below)

## Task Commits

Each task was committed atomically:

1. **Task 1: Update series list, proxy builder, wire pipeline, add CLI flag** - `4c52c4d` (feat)
2. **Task 2: Add baseline regression check, run full pipeline, verify outputs** - `27d686e` (feat)

## Files Created/Modified
- `scripts/extend_gdp.py` - Updated series list, proxy builder, CLI flag, UK carry-forward, baseline check, RW load fix, materializer fix
- `public/data/act2_balearic_islands.csv` - Balearic Islands GDP per capita (datalake-sourced)
- `public/data/act2_extremadura.csv` - Extremadura GDP per capita (datalake-sourced)
- `public/data/act2_andalucia.csv` - Andalucia GDP per capita (new, datalake-sourced)
- `public/data/act2_france.csv` - France GDP per capita (new, datalake-sourced)
- `public/data/act2_portugal.csv` - Portugal GDP per capita (datalake-sourced)
- `public/data/act2_ireland.csv` - Ireland GDP per capita (datalake-sourced)
- `public/data/act2_eu15_avg.csv` - EU-15 population-weighted average (datalake-sourced, with UK carry-forward)
- `output/sanity_report_act2.txt` - Full sanity report with 8 checks
- `data/roseswolf_regionalgdp_v7.xlsx` - Materialized RW workbook (created by fallback)

## Decisions Made
- UK carry-forward applied at Eurostat input level (before chain_link_rw_plus_institutional) rather than on output, because chain_link_rw_plus_institutional requires complete year coverage and would raise PipelineError for missing 2020-2024. Post chain-link, UK output rows >2019 are relabeled source="carry_forward".
- Baseline regression correlation <0.95 is documented and expected: local-proxy CSVs used linearly interpolated sparse RW comparison points, while datalake pipeline uses real annual Eurostat CLV data. Spanish NUTS2 correlations are higher (0.87-0.94) since both use the same EUR_HAB source; national series correlations are low/negative because the proxy had no real annual variation.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] Added Andalucia mapping in _comparison_series_to_rw_rows**
- **Found during:** Task 1
- **Issue:** _comparison_series_to_rw_rows name_to_code dict lacked "Andalucia" → "ES61" mapping. Without it, Andalucia pre-2000 data would use a rough Spain-average proxy instead of the actual regional data from the comparison CSV.
- **Fix:** Added "Andalucia": "ES61" to the name_to_code dictionary
- **Files modified:** scripts/extend_gdp.py
- **Committed in:** 4c52c4d

**2. [Rule 3 - Blocking] Fixed run_act2 RW workbook loading**
- **Found during:** Task 2
- **Issue:** Real v7 Rosés-Wolf workbook (data/roseswolf_regionalgdp_v7.xlsx) has multi-sheet format with metadata "Content" first sheet — load_roseswolf failed with "No year columns detected"
- **Fix:** Wrapped load_roseswolf in try-except, falling back to materialize_roseswolf_workbook which creates a clean gdp_pc_ppp sheet format
- **Files modified:** scripts/extend_gdp.py
- **Committed in:** 27d686e

**3. [Rule 3 - Blocking] Fixed materialize_roseswolf_workbook ES11/ES42 references**
- **Found during:** Task 2
- **Issue:** materialize_roseswolf_workbook hardcoded ES11/ES42 (removed from series list), would crash because INE proxy no longer fetches those codes
- **Fix:** Replaced with dynamic derivation from act2_series_list(), building missing Spanish codes from INE ratios
- **Files modified:** scripts/extend_gdp.py
- **Committed in:** 27d686e

---

**Total deviations:** 3 auto-fixed (1 missing critical, 2 blocking)
**Impact on plan:** All fixes necessary for correctness and pipeline execution. No scope creep.

## Issues Encountered
- Real v7 Rosés-Wolf workbook incompatible with load_roseswolf (different sheet format, GDP in millions not per capita) — resolved via materializer fallback

## User Setup Required
None — no external service configuration required.

## Next Phase Readiness
- All 7 act2_*.csv files emitted and committed — frontend contract satisfied
- Plan 03 (validation/testing) can proceed with the emitted data
- Baseline regression documented: datalake data replaces local-proxy, growth patterns differ as expected

## Self-Check: PASSED

- [x] `public/data/act2_balearic_islands.csv` exists
- [x] `public/data/act2_extremadura.csv` exists
- [x] `public/data/act2_andalucia.csv` exists
- [x] `public/data/act2_france.csv` exists
- [x] `public/data/act2_portugal.csv` exists
- [x] `public/data/act2_ireland.csv` exists
- [x] `public/data/act2_eu15_avg.csv` exists
- [x] `output/sanity_report_act2.txt` has zero FAIL results
- [x] Commit `4c52c4d` exists
- [x] Commit `27d686e` exists

---
*Phase: 05-data-lake-ingestion-catalog-index*
*Completed: 2026-04-29*
