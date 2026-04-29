# Feature Landscape

**Domain:** Full Eurostat-to-Rosés-Wolf chain-linking ETL (replacing Act II local-proxy path)
**Researched:** 2026-04-29
**Scope:** Delta from the existing `--act2-local-proxy` path to a fully sourced ETL

## Table Stakes

Features the full ETL **must** deliver to replace the local-proxy path. Missing any = pipeline cannot ship.

| Feature | Why Expected | Complexity | Dependencies |
|---------|-------------|------------|--------------|
| **F-01: Data-lake MCP ingestion for Eurostat datasets** | The data-lake already indexes `nama_10r_2gdp` (source `01KPWPQ902XYG9BT12QCXKFG4K`) with raw JSON-stat artifacts on disk. Pipeline must read from the lake instead of hitting the Eurostat API live, so runs are reproducible and offline-capable. | Medium | Data-lake MCP `get` tool to resolve `artifact_paths.raw` → local JSON file |
| **F-02: JSON-stat 2.0 parser** | Eurostat's Statistics API returns JSON-stat 2.0 with a flat `value` object keyed by row-major index, `id`/`size`/`dimension` arrays for cube layout. The existing `_eurostat_json_to_df` uses `np.unravel_index` and already handles this. But it must also handle **sparse value objects** (missing keys = missing observations) and the `status` map (`"p"` = provisional, `"e"` = estimated). | Low | Existing `_eurostat_json_to_df` in `extend_gdp.py` (lines 713–732) covers the core; needs status-flag propagation |
| **F-03: NUTS code correspondence handling** | Spanish NUTS2 codes (ES53, ES43, ES61, ES11, ES42) are stable across NUTS 2013/2016/2021/2024 revisions—no boundary changes for Spain at NUTS2. For the 7 Act II series, no correspondence table is needed. However, the existing `load_correspondence` function should be preserved as a fallback for future non-Spanish regions. | Low | No new work for the current series list; `load_correspondence` already exists |
| **F-04: Dual-dataset regional vs national routing** | Spanish regions use `nama_10r_2gdp` (NUTS2, EUR_HAB only—no CLV at regional level). Countries (PT, IE, MT) use `nama_10_pc` (NUTS0, CLV10_EUR_HAB). The existing `Act2SeriesSpec` with `SeriesScope.nuts2` / `SeriesScope.nuts0` already models this split. Full ETL must route each series to the correct dataset+unit combination. | Low | `act2_series_list()` routing metadata already defined (lines 61–133) |
| **F-05: INE-sourced Spanish regional chain-linking** | For Spanish NUTS2 regions, Eurostat only publishes EUR_HAB (current prices). Real-volume chain-linking requires INE CRE data (chain-linked indices) or the existing Eurostat proxy path (`build_ine_proxy_from_eurostat`). Full ETL must: (1) try INE Excel if present, (2) fall back to Eurostat `nama_10r_2gdp` EUR_HAB as proxy. | Medium | `load_ine_or_build_proxy` already implements this fallback (lines 1234–1238); `chain_link_rw_plus_institutional` handles the splice |
| **F-06: EU-15 population-weighted average** | Must compute GDP/cap for the EU-15 aggregate as a population-weighted mean of 15 country-level series (AT, BE, DK, FI, FR, DE, EL, IE, IT, LU, NL, PT, ES, SE, UK). Requires: (a) country-level GDP/cap from `nama_10_pc` CLV10_EUR_HAB, (b) population from `demo_pjan`, (c) each country chain-linked with its own Rosés-Wolf pre-2000 series, (d) population back-filled for years before Eurostat coverage. Greece = EL (not GR). UK included for historical benchmark despite Brexit. | High | Existing `run_act2` already does this (lines 1304–1347) but via live API; needs data-lake path. `_fill_population_backward` and `_eu15_rws_from_comparison_and_euro` exist. |
| **F-07: Chain-linking at configurable anchor year** | Splice Rosés-Wolf (1900–1999) with modern institutional data (2000–2024) at a configurable anchor year (default 2020). Formula: `extended_value[y] = rw_anchor * (institutional[y] / institutional[anchor])`. Growth rates of the modern series are preserved exactly; levels are in Rosés-Wolf 2011 PPP dollars. | Low | `chain_link_rw_plus_institutional` already implements this exactly (lines 849–895) |
| **F-08: 7-check sanity suite** | Must run all 7 existing checks against the full-ETL output: (1) seam continuity at anchor, (2) growth-rate preservation, (3) no missing years, (4) coverage count, (5) outlier YoY growth, (6) level plausibility 2024/2019, (7) Eurostat unit guard. | Low | `run_checks` already implements all 7 (lines 607–710) |
| **F-09: Baseline regression against local-proxy output** | Compare full-ETL `act2_*.csv` output against the existing local-proxy baseline to catch silent regressions. Series should match within tolerance (historical Rosés-Wolf values identical, post-2000 values within the difference expected from switching data sources). | Medium | New feature; must load existing local-proxy CSVs and diff against ETL output |
| **F-10: Emit same CSV contract** | Output CSVs must have identical schema: `year,gdp_pc,source,unit` with the same filenames (`act2_{slug}.csv`) under `public/data/`. The frontend (`act2-chart.vue`, `act2-story-section.vue`) must not need changes. | Low | `_write_act2_public_csv` already emits this format (lines 1080–1091) |

## Differentiators

Features that improve the ETL beyond the local-proxy baseline. Not required for v3.0 launch, but valued.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| **D-01: Data-lake artifact caching with freshness check** | Store downloaded Eurostat JSON-stat responses in the data-lake so subsequent runs are instant and offline. Compare `updated` timestamp in JSON-stat response with lake entry to detect stale data. | Medium | The data-lake MCP already stores artifacts; need a "refresh if stale" flag on the pipeline |
| **D-02: Expanded series roster** | Add Galicia (ES11), Castilla-La Mancha (ES42), Malta (MT) which are already defined in `act2_series_list()` but not consumed by the current frontend. Enables richer comparison narratives. | Low | Series specs exist; frontend needs new scroll steps |
| **D-03: Source provenance column in output CSV** | Add an `institutional_source` column (e.g., "INE", "Eurostat", "Rosés-Wolf") so the frontend can display data-source attribution per data point. | Low | The `source` column exists but uses synthetic labels like `roseswolf_chainlinked` |
| **D-04: Provisional/estimated flag propagation** | Eurostat JSON-stat includes a `status` map (e.g., `"p"` = provisional for 2023–2024). Propagate this to the output CSV so the frontend can style provisional data points differently (e.g., dashed line segment). | Low | `_eurostat_json_to_df` currently ignores status |
| **D-05: CLI `--act2-full-etl` entry point** | Explicit flag (vs removing `--act2-local-proxy`) so both paths coexist during transition. | Low | Argument already partially modeled; needs flag |

## Anti-Features

Features to explicitly **not** build.

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| **Live API calls in the ETL hot path** | Breaks offline reproducibility; Eurostat API has rate limits and occasional downtime; non-deterministic runs | Ingest into data-lake first, ETL reads from lake artifacts only |
| **Membership-date-aware EU-15 composition** | PROJECT.md explicitly marks this out of scope; the narrative treats EU-15 as a fixed analytical benchmark, not a time-varying policy entity | Keep the fixed 15-country list (including UK for full historical range) |
| **PPS/current-price GDP series** | Mixing price bases corrupts the chain-linking math; the unit guard already rejects CP and PPS | Only accept CLV10_EUR_HAB (national) and EUR_HAB (regional, for growth-rate proxy) |
| **Server-side API for data** | PROJECT.md: "Out of Scope — Server-side data APIs while static CSV delivery remains sufficient" | Continue emitting static CSVs under `public/data/` |
| **Automatic NUTS boundary reapportionment** | Complex spatial operation; Spanish NUTS2 boundaries are stable; no other countries need NUTS2 in current scope | Use identity mapping; revisit only if non-Spanish NUTS2 regions are added |

## Feature Dependencies

```
F-01 (data-lake ingestion) → F-02 (JSON-stat parser) → F-04 (routing)
                                                       → F-05 (INE chain-linking)
                                                       → F-06 (EU-15 average)
F-04 → F-07 (chain-linking at anchor)
F-05 → F-07
F-06 → F-07
F-07 → F-08 (sanity checks)
F-07 → F-10 (CSV output)
F-10 → F-09 (baseline regression)
```

Critical path: F-01 → F-02 → F-04 → F-07 → F-10 → F-09

## MVP Recommendation

**Phase 1 (must-ship):** F-01 through F-10. These are all table stakes because the goal is to replace the local-proxy path entirely. The existing codebase already implements F-02 through F-08 and F-10 in `run_act2()` — the primary new work is:
1. **F-01**: Wire data-lake MCP artifact paths as an input source instead of live `urllib` calls
2. **F-09**: Build the baseline regression check
3. Integration test confirming the full path from lake artifacts → 7 CSVs → sanity pass

**Defer:** All differentiators (D-01 through D-05). They add polish but the local-proxy path already ships without them.

**Estimated new code:** ~150–250 lines of Python (data-lake reader, regression check, CLI flag). Most chain-linking logic is already written and tested.

## Sources

- Eurostat Statistics API documentation: https://ec.europa.eu/eurostat/web/user-guides/data-browser/api-data-access/api-detailed-guidelines/api-statistics (HIGH confidence — official docs, verified 2026-04-29)
- Eurostat JSON-stat 2.0 format: verified against data-lake artifact `01KPWPQ902XYG9BT12QCXKFG4K` which contains a raw `nama_10r_2gdp` response with `version: "2.0"`, `id: ["freq","unit","geo","time"]`, sparse `value` object (HIGH confidence — direct artifact inspection)
- NUTS 2021/2024 stability for Spain: Eurostat NUTS correspondence tables confirm no NUTS2 boundary changes for Spain between 2013–2024 revisions (MEDIUM confidence — verified via web search, not direct table inspection)
- Rosés-Wolf v7 (2025): CEPR dataset page confirms coverage 1900–2022 at NUTS2, 2011 PPP dollars (HIGH confidence — https://cepr.org/node/424487)
- Chain-linking methodology: CSO Ireland explanation + Eurostat ESA 2010 guidelines confirm growth-rate preservation approach (HIGH confidence — standard national accounts methodology)
- EU-15 composition and EL/GR convention: Eurostat glossary confirms EL for Greece; EU-15 aggregate must be computed manually from country-level data (HIGH confidence — official Eurostat glossary)
- Existing codebase: `scripts/extend_gdp.py` already implements chain-linking, JSON-stat parsing, EU-15 aggregation, sanity checks, and CSV output (HIGH confidence — direct code review)
