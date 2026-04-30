---
phase: 05-data-lake-ingestion-catalog-index
reviewed: 2026-04-29T13:56:00Z
depth: standard
files_reviewed: 3
files_reviewed_list:
  - scripts/ingest_eurostat_to_datalake.py
  - scripts/datalake_eurostat_index.json
  - scripts/extend_gdp.py
findings:
  critical: 0
  warning: 2
  info: 3
  total: 5
status: issues_found
---

# Phase 05: Code Review Report

**Reviewed:** 2026-04-29T13:56:00Z
**Depth:** standard
**Files Reviewed:** 3
**Status:** issues_found

## Summary

Reviewed the 3 source files changed in Phase 05: the ingestion script, catalog index JSON, and the extended ETL pipeline. No critical or security issues found — subprocess calls use list form (no shell injection), no secrets are exposed, and all I/O is local filesystem. Two warnings flag a logic bug in the CLI anchor-year override and a block of dead code that obscures intent. Three info items note hardcoded machine-specific paths, additional dead code, and a minor inefficiency.

## Warnings

### WR-01: `--act2-datalake --anchor-year 2020` silently overridden to 2019

**File:** `scripts/extend_gdp.py:1596`
**Issue:** The condition `args.anchor_year if args.anchor_year != ANCHOR_YEAR else 2019` cannot distinguish between the argparse default (`ANCHOR_YEAR = 2020`) and a user who *explicitly* passes `--anchor-year 2020`. In the explicit case, the user's intent is silently discarded and anchor is set to 2019.
**Fix:**

```python
# In parse_args, change the default to None:
parser.add_argument(
    "--anchor-year",
    type=int,
    default=None,
    help="Chain-link and seam anchor year (default: 2020, or 2019 with --act2-datalake).",
)

# In the --act2-datalake branch:
anchor = args.anchor_year if args.anchor_year is not None else 2019

# In the legacy branch (after the act2 checks):
anchor = args.anchor_year if args.anchor_year is not None else ANCHOR_YEAR
```

### WR-02: Dead code block in `_eu15_rws_from_comparison_and_euro`

**File:** `scripts/extend_gdp.py:1031-1046`
**Issue:** The `mapping` dict (line 1031) and `rws` list (populated in the first loop, lines 1034-1046) are computed but never referenced. The actual output is built by the second loop (lines 1048-1055). The first loop also contains dead assignments: `cname` and `sub` are computed inside the `if g in {"PT", "IE", "FR", "ES"}` block but immediately fall out of scope or are overwritten. This makes the function harder to reason about.
**Fix:** Remove lines 1031-1046 entirely (the `mapping` dict and the first `for g in EU15_EUROSTAT_GEOS` loop). Only the second loop (lines 1048-1055) produces output.

## Info

### IN-01: Hardcoded absolute path ties scripts to one machine

**File:** `scripts/ingest_eurostat_to_datalake.py:20` and `scripts/datalake_eurostat_index.json:4`
**Issue:** `DATALAKE_ROOT = Path("/Users/guillem/vault/projects/personal/data-lake")` and the corresponding `datalake_root` in the catalog index JSON are machine-specific. The ingestion script and the `--act2-datalake` pipeline will fail on any other checkout.
**Fix:** Accept `--datalake-root` as a CLI argument (or read from an environment variable like `DATALAKE_ROOT`) with the current path as a documented default. The index JSON's `_meta.datalake_root` is already read dynamically by `main()`, so only the ingestion script needs the CLI flag.

### IN-02: Dead code in `materialize_roseswolf_workbook`

**File:** `scripts/extend_gdp.py:1083-1085`
**Issue:** `geos15` is assigned, then `popg` is assigned with a filter excluding `"EL"`, then immediately overwritten on the next line with the unfiltered list. Neither `geos15` nor `popg` is used afterward — line 1086 references `EU15_EUROSTAT_GEOS` directly.
**Fix:** Remove lines 1083-1085.

### IN-03: Catalog index JSON read twice in `main()`

**File:** `scripts/extend_gdp.py:1593-1594`
**Issue:** `load_datalake_index(idx_path)` reads and parses the JSON (line 1593), then `json.loads(idx_path.read_text(...))` reads it again to extract `_meta` (line 1594). Minor I/O duplication.
**Fix:** Have `load_datalake_index` return both the index and the raw dict, or extract `_meta` from the same parse:

```python
raw = json.loads(idx_path.read_text(encoding="utf-8"))
_datalake_index = {k: v for k, v in raw.items() if not k.startswith("_")}
_datalake_root = Path(raw.get("_meta", {}).get("datalake_root", ""))
```

---

_Reviewed: 2026-04-29T13:56:00Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
