---
phase: 02-data-pipeline-extension-v2-0
plan: "02"
subsystem: data-pipeline
tags: [python, etl, ine, chain-linking, spanish-regions, act2]
dependency_graph:
  requires: [scripts/extend_gdp.py@02-01, Act2SeriesSpec, chain_link_rw_plus_institutional]
  provides: [load_ine_excel, filter_ccaa, _find_ine_excel_path, INE_CCAA_FILENAME, chain-link Spanish CCAA via INE]
  affects: [02-03, 02-04]
tech_stack:
  added: []
  patterns: [TDD RED→GREEN, PipelineError fast-fail, wide+tidy Excel parsing, synthetic fixtures via tempfile]
key_files:
  created:
    - tests/test_extend_gdp_02_02_task1.py
    - tests/test_extend_gdp_02_02_task2.py
    - tests/test_extend_gdp_02_02_task3.py
  modified: []
decisions:
  - "All implementation (load_ine_excel, filter_ccaa, chain_link_rw_plus_institutional, _find_ine_excel_path) was already present from wave 1 worktree; plan 02-02 scope was test coverage and verification"
  - "test_missing_anchor_in_inst_raises_pipeline_error: fixed test helper to truncate institutional df at anchor year rather than relying on generator parameter — cleaner fixture design"
  - "TDD green: implementation already passed all 10 chain-link behavioral tests without modification"
metrics:
  duration: "~8 minutes"
  completed: "2026-04-23T14:04:02Z"
  tasks_completed: 3
  files_created: 3
  files_modified: 0
requirements: [DATA-02, DATA-03, DATA-05]
requirements-completed: [DATA-02, DATA-03, DATA-05]
---

# Phase 02 Plan 02: INE Spanish CCAA Chain-link Summary

**One-liner:** Tests for load_ine_excel, filter_ccaa, chain_link_rw_plus_institutional (Spanish CCAA 2020 anchor), and INE file blocker — 25 tests covering D-03, DATA-03, DATA-05, D-06, D-09.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | load_ine_excel and filter_ccaa for Spanish CCAA (D-03) | 6104056 | tests/test_extend_gdp_02_02_task1.py |
| 2 | TDD chain-link four Spanish NUTS2 series + IB Act II 2020 anchor (DATA-03, DATA-05) | 7fa422b | tests/test_extend_gdp_02_02_task2.py |
| 3 | INE file blocker — PipelineError with actionable message and URL | ae3d4d5 | tests/test_extend_gdp_02_02_task3.py |

## What Was Built

### Task 1: load_ine_excel and filter_ccaa tests (D-03)

- `INE_CCAA_FILENAME` constant existence and `.xlsx` suffix validated
- `load_ine_excel()`: wide-format Excel (year-columns) and tidy-format (year/value columns) both parsed to `(ccaa_code, year, value)`
- `filter_ccaa()`: normalizes lowercase codes, returns subset for target CCAA, empty on missing code
- All four target codes (ES53, ES43, ES11, ES42) each independently filterable
- Empty result case raises `PipelineError`
- 8 tests passing

### Task 2: chain_link_rw_plus_institutional TDD tests (DATA-03, DATA-05)

- Full year range 1900..2024 required in output
- Seam at anchor year 2020 matches RW value within 1e-6 (D-09)
- Pre-chain rows (1900–1999) use RW values directly, not institutional
- `source` column present; pre-chain rows labeled `roseswolf`
- Growth-compare DataFrame returned with `year`, `euro_value`, `gdp_pc_2011ppp`
- `PipelineError` raised on missing anchor in either RW or institutional series
- IB Act II chain-link is in-memory only; `balearic_gdp_pc.csv` untouched (D-06)
- `act2_series_list()` includes all four INE CCAA codes (ES53, ES43, ES11, ES42)
- 10 tests passing

### Task 3: INE file blocker tests

- `_find_ine_excel_path` raises `PipelineError` when file absent from both `data/` and `public/data/`
- Error message names the expected filename (contains "ine")
- Error message includes INE download URL (`ine.es`)
- File resolved correctly when placed in `data/` or `public/data/`
- `find_input_file` generic utility also names missing file in error message
- 7 tests passing

## Verification Results

```
Ran 25 tests in 0.165s — OK
py_compile: PASS
module import: ok
```

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed test fixture for missing-anchor-in-institutional test**

- **Found during:** Task 2
- **Issue:** `_make_institutional_df(code, 2019)` did not truncate years at 2019 — the helper hardcoded `range(2000, 2025)` regardless of the anchor_year parameter, so the institutional series always included 2020 and PipelineError was never triggered.
- **Fix:** Changed the test to truncate the institutional df via `inst[inst["year"] < self.anchor]` — makes the test fixture semantically correct.
- **Files modified:** tests/test_extend_gdp_02_02_task2.py
- **Commit:** 7fa422b

## Known Stubs

None — all implementation was already wired in the script; tests verify the wired behavior.

## Threat Flags

No new network endpoints, auth paths, file access patterns, or schema changes introduced. Test files use `tempfile.TemporaryDirectory` for isolation; no credentials or external calls.

## Self-Check: PASSED

- tests/test_extend_gdp_02_02_task1.py: FOUND
- tests/test_extend_gdp_02_02_task2.py: FOUND
- tests/test_extend_gdp_02_02_task3.py: FOUND
- Commit 6104056: FOUND
- Commit 7fa422b: FOUND
- Commit ae3d4d5: FOUND
