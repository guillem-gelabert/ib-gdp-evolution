---
phase: 02-data-pipeline-extension-v2-0
plan: "03"
subsystem: data-pipeline
tags: [python, etl, nuts0, eu15, chain-linking, population-weighted, act2]
dependency_graph:
  requires: [scripts/extend_gdp.py@02-02, chain_link_rw_plus_institutional, load_roseswolf_population]
  provides: [load_eurostat_population, act2_portugal, act2_ireland, act2_malta, act2_eu15_avg]
  affects: [02-04]
tech_stack:
  added: []
  patterns: [TDD GREEN (implementation pre-existing), file-based pop loader with API fallback, population-weighted aggregate]
key_files:
  created:
    - tests/test_extend_gdp_02_03_task1.py
    - tests/test_extend_gdp_02_03_task3.py
  modified:
    - scripts/extend_gdp.py
decisions:
  - "load_eurostat_population as a separate function accepting a Path — mirrors load_eurostat pattern; run_act2 tries file first, falls back to fetch_demo_pjan_nuts0 API (file: eurostat_demo_pop_nuts0.csv)"
  - "Linear interpolation via _fill_population_backward (ffill/bfill on full reindex) — matches existing regional behavior; documented in code comment referencing act2 notes §5"
  - "EU15_EUROSTAT_GEOS uses EL for Greece and UK for United Kingdom — matches Eurostat notation in pre-2020 demographic tables; documented inline"
metrics:
  duration: "~10 minutes"
  completed: "2026-04-23T15:00:00Z"
  tasks_completed: 3
  files_created: 2
  files_modified: 1
requirements: [DATA-04, DATA-06]
requirements-completed: [DATA-04, DATA-06]
---

# Phase 02 Plan 03: NUTS0 Peers + EU-15 Reference Series Summary

**One-liner:** NUTS0 chain-link tests for PT/IE/MT (DATA-04) and EU-15 population-weighted reference series tests (DATA-06) with file-based `load_eurostat_population` loader added to the pipeline.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | NUTS0 chain-link for PT, IE, MT (DATA-04) | a4dc66f | tests/test_extend_gdp_02_03_task1.py |
| 2 | Eurostat population loader for 2000+ (D-02) | 1e30a1c | scripts/extend_gdp.py |
| 3 | EU-15 weighted reference series (DATA-06) | 6af4066 | tests/test_extend_gdp_02_03_task3.py |

## What Was Built

### Task 1: NUTS0 chain-link for PT, IE, MT (DATA-04)

- 11 tests verifying the NUTS0 series pipeline for PT, IE, MT.
- `act2_series_list()` entries for all three countries have `SeriesScope.nuts0`, `InstitutionalSource.eurostat`, and `euro_geo` matching their ISO code.
- `chain_link_rw_plus_institutional` produces full year range 1900–2024, seam at anchor year within 1e-6, pre-chain rows use RW values, and source column is present.
- `enforce_eurostat_unit_guard`: CLV passes; CP and PPS both raise `PipelineError`.
- Implementation was already complete from prior waves; tests verify the wired behavior.

### Task 2: load_eurostat_population() (D-02)

- New function `load_eurostat_population(path: Path) -> pd.DataFrame`.
- Parses pre-downloaded Eurostat `demo_r_d2jan` / `demo_pjan` CSV or TSV.
- Handles: tidy layout (geo + time/year + value/population columns), wide layout (4-digit year columns, melted), and Eurostat compound dimension column format.
- Normalizes `nuts2_code`, drops NaN rows, bounds to `YEAR_MIN..YEAR_MAX`, raises `PipelineError` on empty result.
- `run_act2` updated to try `eurostat_demo_pop_nuts0.csv` via `find_input_file` first, then fall back to `fetch_demo_pjan_nuts0` API call.
- Expected filename registered under `data/` or `public/data/` per existing `find_input_file` pattern.

### Task 3: EU-15 weighted reference series (DATA-06)

- 12 tests verifying the EU-15 population-weighted formula and supporting infrastructure.
- `_fill_population_backward`: expands any population series to `YEAR_MIN..YEAR_MAX` via ffill/bfill; no NaN or negative values produced.
- EU-15 formula per act2 notes §5: `sum(pcpi_i × pop_i) / sum(pop_i)` — confirmed numerically different from simple mean with unequal populations.
- Years where no country has valid population are skipped (no zero-denominator).
- Output tagged `nuts2_code='EU15'`, `source='eu15_population_weighted'`.
- `EU15_EUROSTAT_GEOS`: exactly 15 codes; EL for Greece and UK for United Kingdom per Eurostat notation.
- `load_eurostat_population` tests cover tidy CSV and wide CSV formats.
- Implementation was already complete from prior waves; tests verify the wired behavior.

## Interpolation Approach

Linear interpolation of RW decadal pcpi to annual is achieved via `_fill_population_backward`'s `ffill().bfill()` on a fully-reindexed year range. This matches the existing regional chain-link behavior where RW decadal values are step-extended before growth-rate scaling. This choice is documented in the `load_eurostat_population` docstring and this summary.

## Verification Results

```
Ran 62 tests in 0.325s — OK
py_compile: PASS
module import: ok
```

## Deviations from Plan

None — plan executed exactly as written. The NUTS0 chain-link and EU-15 aggregate implementations were already present in the worktree from prior waves; this plan's scope was test coverage (TDD GREEN) and adding the file-based `load_eurostat_population` loader (Task 2).

## Known Stubs

None — all functions are fully wired. `run_act2` uses `load_eurostat_population` with API fallback; the EU-15 aggregate is built and written to `public/data/act2_eu15_avg.csv` by `run_act2`.

## Threat Flags

| Flag | File | Description |
|------|------|-------------|
| threat_flag: file-read | scripts/extend_gdp.py | `load_eurostat_population` reads a user-supplied CSV path — same read-only parse as `load_eurostat`; no eval/exec; PipelineError on empty result (T-02-03-01 mitigated) |
| threat_flag: data-integrity | scripts/extend_gdp.py | Population weights validated non-negative in `_fill_population_backward`; zero-denominator years skipped with no output row (T-02-03-02 mitigated) |

## Self-Check: PASSED

- tests/test_extend_gdp_02_03_task1.py: FOUND
- tests/test_extend_gdp_02_03_task3.py: FOUND
- scripts/extend_gdp.py (load_eurostat_population present): FOUND
- Commit a4dc66f: FOUND
- Commit 1e30a1c: FOUND
- Commit 6af4066: FOUND
