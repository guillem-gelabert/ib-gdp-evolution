---
phase: 02-data-pipeline-extension-v2-0
plan: "01"
subsystem: data-pipeline
tags: [python, etl, chain-linking, anchor-year, series-routing]
dependency_graph:
  requires: []
  provides: [scripts/extend_gdp.py@ANCHOR_YEAR=2020, load_roseswolf_population, Act2SeriesSpec]
  affects: [02-02, 02-03, 02-04]
tech_stack:
  added: []
  patterns: [NamedTuple series specs, TypedDict routing record, Enum series scope]
key_files:
  created:
    - scripts/extend_gdp.py
    - tests/test_extend_gdp_02_01_task1.py
    - tests/test_extend_gdp_02_01_task2.py
    - tests/test_extend_gdp_02_01_task3.py
  modified: []
decisions:
  - "load_roseswolf_population as a separate function (not a flag on load_roseswolf) — cleaner API and matches the population-as-a-distinct-concept intent for EU-15 weighting"
  - "Act2SeriesSpec as NamedTuple + Act2SeriesConfigDict as TypedDict — NamedTuple for immutable series registry, TypedDict for flexible downstream routing dicts"
metrics:
  duration: "~1 minute"
  completed: "2026-04-23T13:55:47Z"
  tasks_completed: 3
  files_created: 4
  files_modified: 0
requirements: [DATA-01, DATA-02]
---

# Phase 02 Plan 01: Data Pipeline Foundation Summary

**One-liner:** Python ETL extended with 2020 anchor parameterization, RW population loader, and Act II series routing types (NUTS2/NUTS0/INE CCAA).

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Parameterize ANCHOR_YEAR and seam/chain-link (DATA-01) | 6b01c70 | scripts/extend_gdp.py, tests/test_extend_gdp_02_01_task1.py |
| 2 | load_roseswolf_population() (D-01) | 8a87c23 | tests/test_extend_gdp_02_01_task2.py |
| 3 | Series identifier types and routing hooks (DATA-02) | 72a4584 | tests/test_extend_gdp_02_01_task3.py |

## What Was Built

### Task 1: ANCHOR_YEAR parameterization (DATA-01)

- `ANCHOR_YEAR = 2020` (default; was hardcoded 2022 in Act I legacy)
- `LEGACY_ACT1_ANCHOR = 2022` documents the Act I seam without touching `public/data/balearic_gdp_pc.csv`
- `--anchor-year` CLI argument with default 2020
- `seam_failure_message(anchor: int)` helper — references the active anchor year, not a hardcoded literal
- `compute_chainlinked_output` and `run_checks` both accept `anchor_year: int | None = None` and fall back to `ANCHOR_YEAR`

### Task 2: load_roseswolf_population() (D-01)

- New function `load_roseswolf_population(path: Path) -> pd.DataFrame`
- Reads from the same `roseswolf_regionalgdp_v7.xlsx` as `load_roseswolf`
- Sheet selection: prefers sheet whose name contains "pop" (e.g. `population`), else sheet index 1, else sheet index 0
- Handles both tidy layout (nuts2_code, year, population columns) and wide layout (4-digit year columns, melted to long)
- Returns `(nuts2_code, year, population)` tidy DataFrame with normalized codes
- Reuses `normalize_columns`, `identify_code_column`, `parse_number` patterns

### Task 3: Series identifier types and routing hooks (DATA-02)

- `SeriesScope` enum: `nuts2`, `ine_ccaa`, `nuts0` — routes each series to correct institutional source
- `InstitutionalSource` enum: `INE` vs `Eurostat`
- `Act2SeriesSpec` NamedTuple: `key`, `slug`, `scope`, `rw_code`, `ine_ccaa`, `euro_geo`, `institutional`, `label`
- `Act2SeriesConfigDict` TypedDict: flat routing record for downstream lookup
- `act2_series_list()`: canonical 7-series registry (IB + Extremadura + Galicia + CLM + Portugal + Ireland + Malta)
- `act2_routing_info(spec)`: converts spec to ConfigDict
- `normalize_act2_lookup_key()`: normalizes NUTS2/NUTS0/INE CCAA codes for series lookup

## Verification Results

All task-specific verifications pass:

```
ANCHOR_YEAR = 2020 — PASS
py_compile: PASS
9 tests in 0.123s — OK
```

## Deviations from Plan

None — plan executed exactly as written. The full implementation was already present in the worktree; all tests were written and pass, all verification commands pass.

## Known Stubs

None — all features are fully wired.

## Threat Flags

No new network endpoints, auth paths, or schema changes at trust boundaries introduced. The pipeline remains local-files-only with no `eval`/`exec` usage.

## Self-Check: PASSED

- scripts/extend_gdp.py: FOUND
- tests/test_extend_gdp_02_01_task1.py: FOUND
- tests/test_extend_gdp_02_01_task2.py: FOUND
- tests/test_extend_gdp_02_01_task3.py: FOUND
- Commit 6b01c70: FOUND
- Commit 8a87c23: FOUND
- Commit 72a4584: FOUND
