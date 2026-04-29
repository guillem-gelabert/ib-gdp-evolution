# Technology Stack

**Project:** IB GDP Evolution — v3.0 Full Act II ETL
**Researched:** 2026-04-29
**Scope:** Stack additions for reading Eurostat NAMA JSON from data-lake artifacts and chain-linking with Rosés-Wolf

## Recommendation: No New Dependencies

The existing stack handles the full requirement. The data-lake stores Eurostat API responses as local JSON files in JSON-stat v2.0 format — the exact format the pipeline's `_eurostat_json_to_df()` already parses.

### Existing Stack (unchanged)

| Technology | Version | Purpose | Status |
|------------|---------|---------|--------|
| Python 3 | ≥3.12 | ETL runtime | Already in use |
| pandas | (latest) | DataFrame ops, CSV I/O, chain-linking | Already in use |
| numpy | (latest) | `np.unravel_index` / `np.prod` in JSON-stat parser | Already in use (lazy import inside `_eurostat_json_to_df`) |
| json (stdlib) | — | Parse JSON files | Already in use for API responses |
| pathlib (stdlib) | — | File path handling | Already in use |
| openpyxl | (latest) | Excel read/write for Rosés-Wolf workbook | Already in use |

### Why Zero New Dependencies

**Confidence: HIGH** — verified against data-lake artifact and existing parser source.

1. **The parser already works.** `_eurostat_json_to_df()` (line 713–732 of `extend_gdp.py`) reads `d["id"]`, `d["size"]`, `d["dimension"][dim]["category"]["index"]`, and `d["value"]` — exactly the JSON-stat v2.0 fields present in data-lake `raw.json` artifacts.

2. **The data-lake provides local file paths.** The MCP `get` tool returns `artifact_paths.raw` as an absolute path to a JSON file (e.g. `/…/lake/sources/<id>/raw.json`). Reading this requires only `json.load(open(path))`, no HTTP client.

3. **The API fetch path stays as fallback.** `_eurostat_get()` + `urllib.request` remain for cases where a dataset isn't in the data-lake. No reason to add `requests` or `httpx`.

## Verified JSON-stat v2.0 Structure

Data-lake source `01KPWPQ902XYG9BT12QCXKFG4K` (NAMA_10R_2GDP, ES53, EUR_HAB) confirmed:

```json
{
  "version": "2.0",
  "class": "dataset",
  "id": ["freq", "unit", "geo", "time"],
  "size": [1, 1, 1, 25],
  "dimension": {
    "unit": { "category": { "index": { "EUR_HAB": 0 } } },
    "geo":  { "category": { "index": { "ES53": 0 } } },
    "time": { "category": { "index": { "2000": 0, "2001": 1, … } } }
  },
  "value": { "0": 20000, "1": 21400, … },
  "extension": { "id": "NAMA_10R_2GDP" }
}
```

This is identical to what `_eurostat_get()` returns from the live API — the parser works without modification.

## Integration Points with `extend_gdp.py`

### What to add (code, not deps)

| Change | Where | Why |
|--------|-------|-----|
| `load_json_stat_file(path: Path) -> pd.DataFrame` | New function | Read local JSON, call existing `_eurostat_json_to_df()`, normalize to `(nuts2_code, year, value)` |
| Unit guard for JSON-stat | New function or adapt `enforce_eurostat_unit_guard` | Current guard reads CSV column values; JSON-stat encodes unit in `dimension.unit.category.index` key (e.g. `"CLV10_EUR_HAB"`, `"EUR_HAB"`) |
| `--data-lake-root` or per-dataset path CLI args | `parse_args()` | Accept local artifact paths instead of relying on API or CSV files |
| Route `Act2SeriesSpec` through file loader | `run_act2()` | Replace `fetch_nama_10_pc_clv10()` / `fetch_nama_10r_2gdp_eur_hab()` calls with file-based loading when artifact paths are provided |
| `extension.id` dataset routing | New helper | JSON-stat `extension.id` field (e.g. `"NAMA_10R_2GDP"`, `"NAMA_10_PC"`) identifies which dataset a file belongs to — use for validation |

### What stays unchanged

- `load_roseswolf()` — reads the same Excel workbook
- `chain_link_rw_plus_institutional()` — same chain-linking math
- `_write_act2_public_csv()` — same CSV output format
- `run_checks()` — same sanity checks
- All frontend code — consumes the same `act2_*.csv` files

## Alternatives Considered

| Library | Version | Why Not |
|---------|---------|---------|
| `pyjstat` | 2.4.0 (last release 2023-03-31) | Adds OOP abstraction + `requests` transitive dep for something the existing 20-line parser already handles. No updates in 3+ years. |
| `jsonstat.py` | 0.1.14 | Less maintained than pyjstat; same zero-benefit tradeoff — wrapping a trivially-parsed format in a class hierarchy. |
| `eurostat` | 1.1.1 | Fetches via SDMX 2.1 API (different wire format). We're reading local JSON-stat files, not calling the API. |
| `eurostatpy` | 1.1.0 | Same: API-fetching wrapper. Irrelevant for local file reading. |

## Data-Lake Integration Pattern

The data-lake MCP (`project-0-ib-gdp-evolution-data-lake`) exposes:

1. **`search(query)`** — find source IDs by keyword (e.g. "NAMA_10R_2GDP")
2. **`get(id, full=false)`** — returns metadata + `artifact_paths` dict
3. **`artifact_paths.raw`** — absolute path to the JSON file on disk

ETL integration pattern:

```
CLI arg --data-lake-root  ──or──  MCP get(id).artifact_paths.raw
        │                                    │
        ▼                                    ▼
   Path to raw.json on disk ────────────────►│
                                             ▼
                              json.load(open(path))
                                             │
                                             ▼
                              _eurostat_json_to_df(d)
                                             │
                                             ▼
                              pd.DataFrame (nuts2_code, year, value)
```

For v3.0, the pipeline should accept either:
- Direct file paths (offline / CI-friendly)
- Data-lake source IDs (resolved to paths at runtime via the Stitch MCP or CLI)

## NAMA Dataset Differences

Both datasets use JSON-stat v2.0 with the same structure, but have different dimension semantics:

| Dataset | Scope | `geo` values | `unit` values needed | `extension.id` |
|---------|-------|-------------|---------------------|-----------------|
| `nama_10r_2gdp` | NUTS2 regional | ES53, ES43, ES61, ES11, ES42 | `EUR_HAB` (current prices, only option for regional) | `NAMA_10R_2GDP` |
| `nama_10_pc` | NUTS0 national | PT, IE, MT, FR, + EU-15 set | `CLV10_EUR_HAB` (chain-linked volumes) | `NAMA_10_PC` |

The unit guard must be adapted per dataset:
- `nama_10r_2gdp`: only offers current-price `EUR_HAB` at NUTS2 level (this is a known Eurostat limitation for regional data) — the pipeline already handles this via INE chain-linked proxy for Spanish regions
- `nama_10_pc`: requires `CLV10_EUR_HAB` filter — existing guard logic applies

## Sources

| Claim | Source | Confidence |
|-------|--------|------------|
| JSON-stat v2.0 structure | Data-lake artifact `01KPWPQ902XYG9BT12QCXKFG4K/raw.json` — direct read | HIGH |
| Existing parser compatibility | `extend_gdp.py` `_eurostat_json_to_df()` lines 713–732 — code review | HIGH |
| pyjstat v2.4.0 last release 2023-03-31 | PyPI JSON API | HIGH |
| `eurostat` v1.1.1 uses SDMX not JSON-stat | PyPI project page | HIGH |
| Data-lake MCP returns `artifact_paths` | MCP `get` tool schema and live response | HIGH |
| NAMA_10R_2GDP only offers EUR_HAB regionally | Eurostat API documentation, confirmed via data-lake sample | MEDIUM |
