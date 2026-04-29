# Architecture Patterns

**Domain:** Full Eurostat ETL integration into existing extend_gdp.py
**Researched:** 2026-04-29
**Confidence:** HIGH — based on direct codebase analysis and live data-lake MCP queries

## Recommended Architecture

### Pattern: Adapter Layer with Fallback

Add a thin **data-lake adapter** between `run_act2()` and the Eurostat API. The adapter resolves source IDs from the data-lake catalog, reads JSON-stat v2.0 artifacts from local disk, and returns the same `pd.DataFrame` the existing `fetch_*` functions return. When a required dataset is not in the data-lake, the adapter falls back to the live Eurostat API (the current path).

This is a **Strangler Fig** migration: the live API calls remain as fallback, and each dataset is migrated to data-lake sourcing independently.

```
┌─────────────────────────────────────────────────────────┐
│ run_act2(workspace, anchor_year)                        │
│   ├─ load_ine_or_build_proxy()     [unchanged]          │
│   ├─ load_roseswolf()              [unchanged]          │
│   ├─ FOR each Act2SeriesSpec:                           │
│   │   ├─ resolve_eurostat(spec) ─┐                      │
│   │   │   ├─ data-lake lookup    │  NEW: adapter layer  │
│   │   │   ├─ read raw.json       │                      │
│   │   │   ├─ parse JSON-stat     │                      │
│   │   │   └─ OR fallback to API ─┘                      │
│   │   └─ chain_link_rw_plus_institutional()  [unchanged]│
│   ├─ build EU-15 weighted average            [unchanged]│
│   └─ run_checks() + write CSVs               [unchanged]│
└─────────────────────────────────────────────────────────┘
```

### Component Boundaries

| Component | Responsibility | Status | Communicates With |
|-----------|---------------|--------|-------------------|
| `act2_series_list()` | Define which series the ETL produces | **MODIFY** — align slugs with frontend contract | `run_act2()` |
| `_eurostat_json_to_df()` | Parse JSON-stat v2.0 dict → DataFrame | EXISTS (line 713) — promote to public | data-lake adapter |
| `resolve_datalake_source()` | Map (dataset, geo, unit) → source_id | **NEW** | data-lake MCP or catalog file |
| `load_eurostat_from_datalake()` | Read raw.json artifact, call parser | **NEW** | `resolve_datalake_source`, `_eurostat_json_to_df` |
| `fetch_eurostat_series()` | Unified entry: try data-lake → fallback API | **NEW** | all the above, `fetch_nama_*` |
| `run_act2()` | Orchestrate Act II ETL | **MODIFY** — replace direct `fetch_*` calls | `fetch_eurostat_series`, chain-linking |
| `chain_link_rw_plus_institutional()` | Splice RW pre-2000 + institutional post-2000 | EXISTS — no changes | `run_act2()` |
| `run_checks()` | Sanity validation suite | EXISTS — add baseline comparison check | `run_act2()` |
| `run_act2_local_proxy()` | Legacy local-proxy fallback | EXISTS — no changes | CLI |

### Data Flow

```
Data Lake (MCP)                    Eurostat API (live)
      │                                  │
      ▼                                  ▼
  search(query)                    urllib.request
      │                                  │
      ▼                                  │
  get(source_id)                         │
      │                                  │
      ▼                                  │
  artifact_paths.raw                     │
      │                                  │
      ▼                                  ▼
  json.load(raw.json)              json.loads(response)
      │                                  │
      └──────────┬───────────────────────┘
                 ▼
     _eurostat_json_to_df(dict)    ← SINGLE PARSER
                 │
                 ▼
         pd.DataFrame(nuts2_code, year, value)
                 │
                 ▼
     chain_link_rw_plus_institutional()
                 │
                 ▼
         act2_{slug}.csv  →  public/data/
```

## Critical Finding: Series Spec Mismatch

The frontend (`act2-story-section.vue` line 110-116) consumes **7 specific CSVs**:

| Frontend slug | Frontend expects | `act2_series_list()` has | Status |
|---------------|-----------------|------------------------|--------|
| `balearic_islands` | ES53 | ES53 (key: ib) | ✓ Match |
| `extremadura` | ES43 | ES43 | ✓ Match |
| `andalucia` | ES61 | — | **MISSING from spec** |
| `portugal` | PT | PT | ✓ Match |
| `ireland` | IE | IE | ✓ Match |
| `france` | FR | — | **MISSING from spec** |
| `eu15_avg` | Weighted avg | Built separately | ✓ Match |
| — | — | `galicia` (ES11) | **Not consumed by frontend** |
| — | — | `castilla_la_mancha` (ES42) | **Not consumed by frontend** |
| — | — | `malta` (MT) | **Not consumed by frontend** |

**Resolution:** Update `act2_series_list()` to match the frontend contract. Add Andalucía (ES61, NUTS2, INE) and France (FR, NUTS0, Eurostat). Remove galicia, castilla_la_mancha, and malta. The frontend is the shipped product; the ETL aligns to it, not the reverse.

## New Functions — Detailed Design

### 1. `resolve_datalake_source(dataset, geo, unit, datalake_index)` → `str | None`

Looks up the data-lake source ID for a given Eurostat API query. The data-lake's `search` tool is BM25-based (text search), which is unreliable for structured lookups. Two approaches:

**Option A — Catalog index file (recommended):** Maintain a small JSON file (`data/datalake_eurostat_index.json`) that maps `(dataset, geo, unit)` triples to source IDs. This is populated once during data-lake ingestion and is deterministic. The ETL reads it at startup.

```python
# data/datalake_eurostat_index.json
{
  "nama_10r_2gdp|ES53|EUR_HAB": "01KPWPQ902XYG9BT12QCXKFG4K",
  "nama_10_pc|FR|CLV10_EUR_HAB": "...",
  ...
}
```

**Option B — MCP search at runtime:** Call the data-lake MCP `get` tool by guessing IDs. Too fragile — the BM25 search doesn't reliably rank by (dataset, geo, unit) and costs a network round-trip per series.

### 2. `load_eurostat_from_datalake(source_id, datalake_root)` → `pd.DataFrame`

Reads the `raw.json` artifact from the data-lake's local filesystem, parses JSON-stat v2.0, returns a tidy DataFrame.

```python
def load_eurostat_from_datalake(source_id: str, datalake_root: Path) -> pd.DataFrame:
    raw_path = datalake_root / "lake" / "sources" / source_id / "raw.json"
    if not raw_path.exists():
        raise PipelineError(f"Data-lake artifact not found: {raw_path}")
    with raw_path.open() as f:
        data = json.load(f)
    return _eurostat_json_to_df(data)
```

**Key fact:** The data-lake artifact path pattern is: `{datalake_root}/lake/sources/{source_id}/raw.json`. The `artifact_paths` field in the MCP `get` response confirms this.

### 3. `fetch_eurostat_series(dataset, geo, unit, *, datalake_index, datalake_root)` → `pd.DataFrame`

Unified entry point. Try data-lake first, fall back to live API.

```python
def fetch_eurostat_series(
    dataset: str,
    geos: list[str],
    unit: str,
    *,
    datalake_index: dict[str, str] | None = None,
    datalake_root: Path | None = None,
) -> pd.DataFrame:
    frames = []
    for geo in geos:
        key = f"{dataset}|{geo}|{unit}"
        source_id = (datalake_index or {}).get(key)
        if source_id and datalake_root:
            frames.append(load_eurostat_from_datalake(source_id, datalake_root))
        else:
            # Fallback: existing live API functions
            frames.append(_fetch_from_api(dataset, geo, unit))
    return pd.concat(frames, ignore_index=True)
```

### 4. Updated `act2_series_list()` — aligned with frontend

```python
def act2_series_list() -> list[Act2SeriesSpec]:
    return [
        Act2SeriesSpec(key="ib",          slug="balearic_islands", scope=SeriesScope.nuts2, rw_code="ES53", ine_ccaa="ES53", euro_geo="ES53", institutional=InstitutionalSource.ine,      label="Balearic Islands"),
        Act2SeriesSpec(key="extremadura", slug="extremadura",      scope=SeriesScope.nuts2, rw_code="ES43", ine_ccaa="ES43", euro_geo="ES43", institutional=InstitutionalSource.ine,      label="Extremadura"),
        Act2SeriesSpec(key="andalucia",   slug="andalucia",        scope=SeriesScope.nuts2, rw_code="ES61", ine_ccaa="ES61", euro_geo="ES61", institutional=InstitutionalSource.ine,      label="Andalucía"),
        Act2SeriesSpec(key="pt",          slug="portugal",         scope=SeriesScope.nuts0, rw_code="PT",   ine_ccaa=None,   euro_geo="PT",   institutional=InstitutionalSource.eurostat, label="Portugal"),
        Act2SeriesSpec(key="ie",          slug="ireland",          scope=SeriesScope.nuts0, rw_code="IE",   ine_ccaa=None,   euro_geo="IE",   institutional=InstitutionalSource.eurostat, label="Ireland"),
        Act2SeriesSpec(key="fr",          slug="france",           scope=SeriesScope.nuts0, rw_code="FR",   ine_ccaa=None,   euro_geo="FR",   institutional=InstitutionalSource.eurostat, label="France"),
    ]
```

## Integration Points — What Changes vs. What Stays

### Unchanged (Act I safe)

| Function | Why unchanged |
|----------|--------------|
| `main()` Act I path | Different CLI flag, different code path entirely |
| `load_roseswolf()` | Reads xlsx/csv — no Eurostat dependency |
| `load_eurostat()` (Act I CSV reader) | Only used by Act I's `main()` |
| `compute_chainlinked_output()` | Only used by Act I |
| `chain_link_rw_plus_institutional()` | Pure function; takes DataFrames as input, agnostic to source |
| `run_checks()` | Pure validation; doesn't care where data came from |
| `run_act2_local_proxy()` | Stays as `--act2-local-proxy` fallback |

### Modified

| Function | Change |
|----------|--------|
| `act2_series_list()` | Replace galicia/clm/malta with andalucia/france |
| `run_act2()` | Accept `datalake_index` + `datalake_root` params; replace `fetch_nama_*` calls with `fetch_eurostat_series()` |
| `_eurostat_json_to_df()` | Rename to `eurostat_json_to_df()` (drop leading underscore), no logic change |

### New

| Function | Purpose |
|----------|---------|
| `load_eurostat_from_datalake()` | Read + parse a single data-lake artifact |
| `fetch_eurostat_series()` | Unified entry: data-lake → API fallback |
| `load_datalake_index()` | Read the catalog index JSON |
| `build_datalake_index()` | (Optional) Generate the index by querying the MCP |
| `--act2-datalake` CLI flag | Or make data-lake the default when index exists |

## Data-Lake Artifact Structure

Each Eurostat dataset in the data-lake follows this layout (confirmed via MCP `get` output):

```
{datalake_root}/lake/sources/{source_id}/
├── raw.json     ← JSON-stat v2.0 (the actual data)
├── text.md      ← Extracted text summary (not needed by ETL)
└── meta.yaml    ← Catalog metadata (fetched_at, url, sha256)
```

The `raw.json` is **identical** in structure to what the Eurostat REST API returns — same `version: "2.0"`, `id` array (dimension names), `size` array, `dimension` object, flat `value` dict. The existing `_eurostat_json_to_df()` parser handles it without modification.

**Current data-lake state:** Only 1 Eurostat JSON source exists (ES53 / EUR_HAB from nama_10r_2gdp). The milestone requires ingesting additional datasets:

| Dataset | Geos needed | Unit | Purpose |
|---------|-------------|------|---------|
| `nama_10r_2gdp` | ES53, ES43, ES61 | `EUR_HAB` | Spanish NUTS2 regions |
| `nama_10_pc` | FR, IE, PT + EU-15 set | `CLV10_EUR_HAB` | National GDP/cap (chain-linked) |
| `demo_pjan` | EU-15 set | `T/TOTAL` | Population for EU-15 weighting |

Each (dataset, geo, unit) tuple is a separate data-lake source — matching how the Eurostat API is parameterized per-geo.

## Patterns to Follow

### Pattern 1: Adapter with Fallback
**What:** Every Eurostat data fetch goes through `fetch_eurostat_series()`, which tries data-lake first.
**When:** All Act II Eurostat data loading.
**Why:** Allows incremental migration. Can ship phases that work with partial data-lake coverage.

### Pattern 2: Static Catalog Index
**What:** A committed JSON file maps (dataset, geo, unit) → source_id deterministically.
**When:** At ETL startup, before any data loading.
**Why:** The data-lake's BM25 search is not structured enough for reliable (dataset, geo, unit) lookups. A static index is deterministic and fast. It also serves as documentation of which datasets have been ingested.

### Pattern 3: Shared Parser
**What:** `eurostat_json_to_df()` is the single parser for JSON-stat v2.0, used by both the data-lake path and the API path.
**When:** Every Eurostat data load.
**Why:** Both the data-lake `raw.json` and the live API response are identical JSON-stat v2.0. One parser, tested once.

### Pattern 4: Baseline Regression Check
**What:** After producing act2_*.csv via the full ETL, compare numerically against the local-proxy outputs.
**When:** As a sanity check (new check #8 in `run_checks()`).
**Why:** The local-proxy CSVs are the accepted baseline. The full ETL must produce equivalent (within tolerance) results, or the chart visuals change unexpectedly.

## Anti-Patterns to Avoid

### Anti-Pattern 1: Splitting extend_gdp.py into multiple modules prematurely
**What:** Creating a `datalake/` package or separate `json_stat.py` module.
**Why bad:** The script is 1577 lines and growing, but it's a single-purpose CLI. Module boundaries add import complexity without clear ownership boundaries. The existing pattern of module-scope functions works.
**Instead:** Keep all new functions in `extend_gdp.py`. Only extract if it exceeds ~2500 lines or a second consumer appears.

### Anti-Pattern 2: Calling data-lake MCP at ETL runtime
**What:** Having the Python ETL call the MCP server (via HTTP or subprocess) to resolve source IDs.
**Why bad:** Adds a runtime dependency on the MCP server being up. The ETL is an offline batch script.
**Instead:** Use the static catalog index file. The MCP is for interactive exploration; the ETL reads files directly.

### Anti-Pattern 3: Changing the frontend CSV contract
**What:** Updating `act2-story-section.vue` to consume different slugs because the ETL's `act2_series_list()` uses different names.
**Why bad:** The frontend was shipped and validated. Changing it risks Act II regressions.
**Instead:** Align the ETL's series spec to match the frontend's existing file names.

### Anti-Pattern 4: Breaking Act I by refactoring shared functions
**What:** Modifying `load_eurostat()`, `compute_chainlinked_output()`, or `main()` to support data-lake features.
**Why bad:** Act I works and has its own code path. Entangling Act I with Act II's data-lake layer risks regressions.
**Instead:** All data-lake integration goes through `run_act2()` and its helpers. Act I code stays untouched.

## Suggested Build Order

Dependencies flow top-down; each step builds on the previous.

| Phase | Task | Depends on | Modifies | New |
|-------|------|------------|----------|-----|
| **1** | Ingest required Eurostat datasets into data-lake | Data-lake tooling (outside this repo) | — | Multiple data-lake sources |
| **2** | Create catalog index file (`datalake_eurostat_index.json`) | Phase 1 (sources must exist) | — | `data/datalake_eurostat_index.json` |
| **3** | Promote `_eurostat_json_to_df()` → `eurostat_json_to_df()` | — | `extend_gdp.py` (rename) | — |
| **4** | Add `load_eurostat_from_datalake()` | Phase 3 | `extend_gdp.py` | New function |
| **5** | Add `fetch_eurostat_series()` (unified entry + fallback) | Phase 4 | `extend_gdp.py` | New function |
| **6** | Fix `act2_series_list()` to match frontend contract | — | `extend_gdp.py` | — |
| **7** | Wire `run_act2()` to use `fetch_eurostat_series()` | Phases 5 + 6 | `extend_gdp.py` `run_act2()` | — |
| **8** | Add baseline regression check (new sanity check) | Phase 7 | `extend_gdp.py` `run_checks()` | — |
| **9** | CLI integration (`--act2-datalake` or auto-detect) | Phase 7 | `extend_gdp.py` `parse_args()` | — |
| **10** | End-to-end validation: full ETL → CSV diff vs local-proxy | Phases 7-9 | — | Test script |

**Critical path:** Phases 1→2→4→5→7→10. Phase 6 is independent and can be done in parallel with 3-5. Phase 8 can be done in parallel with 9.

**Phase 1 is the prerequisite gate:** The data-lake currently has only 1 Eurostat source (ES53/EUR_HAB). The full ETL requires ~20+ sources across 3 datasets. Data-lake ingestion must happen first, likely as a separate phase or prerequisite task.

## Configuration

### New CLI Arguments

```
--datalake-root PATH    Path to data-lake root (default: auto-detect from known location)
--datalake-index PATH   Path to catalog index JSON (default: data/datalake_eurostat_index.json)
--no-datalake           Force live API mode (skip data-lake)
```

### Catalog Index Schema

```json
{
  "$comment": "Maps 'dataset|geo|unit' → data-lake source ID",
  "nama_10r_2gdp|ES53|EUR_HAB": "01KPWPQ902XYG9BT12QCXKFG4K",
  "nama_10_pc|FR|CLV10_EUR_HAB": "<source_id>",
  "demo_pjan|FR|T_TOTAL": "<source_id>"
}
```

## Sources

- Direct codebase analysis: `scripts/extend_gdp.py` (1577 lines, read in full)
- Data-lake MCP `get` response for source `01KPWPQ902XYG9BT12QCXKFG4K` — confirmed artifact path layout and JSON-stat structure
- Data-lake MCP `search` — confirmed only 1 JSON Eurostat source currently ingested
- Data-lake MCP `list_sources` with `format: json` filter — confirmed 1 source total
- Frontend `act2-story-section.vue` lines 110-116 — confirmed 7 CSV slug expectations
- `public/data/act2_balearic_islands.csv` — confirmed output CSV schema: `year, gdp_pc, source, unit`
- Data-lake `raw.json` file — confirmed JSON-stat v2.0 structure identical to Eurostat API response
- Confidence: **HIGH** — all claims verified against actual code and live MCP responses
