# Phase 2: Data Pipeline Extension (v2.0) — Context

**Gathered:** 2026-04-23
**Status:** Ready for planning

<domain>
## Phase Boundary

Extend `scripts/extend_gdp.py` to produce one CSV per series (IB re-anchored at 2020 + 6 peer regions/countries + EU-15 weighted reference) for Act II. The existing Act I pipeline and `public/data/balearic_gdp_pc.csv` must not be modified.
</domain>

<decisions>
## Implementation Decisions

### EU-15 Population Source (pre-2000)
- **D-01:** Extract population from `roseswolf_regionalgdp_v7.xlsx` directly — the same RW Excel used for GDP per capita. A new `load_roseswolf_population()` function must be added to read the population column/sheet. This keeps EU-15 weighting internally consistent (same source for both GDP/cap and pop pre-2000).
- **D-02:** For post-2000 EU-15: use Eurostat population data (already accessible via `demo_r_d2jan` or national `demo_pjan`), consistent with the Eurostat GDP data used post-2000.

### INE Source for Spanish Peer Regions
- **D-03:** Use INE Spanish Regional Accounts (`cid=1254736167628`), "GDP and GDP per person 2000-2024 Series" — the same source and format as the existing IB data. INE offers a combined Spain Excel with all CCAA; pre-download locally and place in input directory. Same `load_ine_excel` parsing path as current IB pipeline.
- **D-04:** Spanish peers: Extremadura (ES43), Galicia (ES11), Castilla-La Mancha (ES42). These are CCAA-level, not NUTS2 lookups — use the same non-NUTS2-ID approach decided in the v2.0 exploration session.

### Eurostat Source for Country Peers
- **D-05:** Portugal (PT), Ireland (IE), Malta (MT) sourced from Eurostat `nama_10r_2gdp` or national `nama_10_gdp` using the CLV (chain-linked volume) unit — same `enforce_eurostat_unit_guard` enforcement as current pipeline. Use country-level NUTS0 codes.

### IB File Handling
- **D-06:** Do NOT modify `public/data/balearic_gdp_pc.csv` (Act I anchor remains 2022, Act I chart is untouched). For Act II, recompute IB at 2020 anchor as one of the per-series output files.

### Output Layout
- **D-07:** One CSV per series (separate files under `public/data/`), not a combined multi-series file. The Act II chart will fetch each series in parallel. File naming: `act2_{series_slug}.csv`, e.g. `act2_balearic_islands.csv`, `act2_extremadura.csv`, `act2_eu15_avg.csv`.
- **D-08:** Each file schema: `year,gdp_pc,source,unit` — same schema as the existing `balearic_gdp_pc.csv` so Act II chart can reuse the same parsing logic.

### Anchor Year & Chain-linking
- **D-09:** Anchor year: **2020** for all Act II series (locked from v2.0 exploration). The 2020 value in each series equals the raw 2020 EUR value; all other years are scaled proportionally via the same RW + Eurostat growth-rate chain-linking method as Act I.

### Claude's Discretion
- How to structure the RW population read (new function vs. additional parameter on existing `load_roseswolf`) — Claude decides.
- Whether to generate a combined manifest/index file alongside the per-series CSVs — Claude decides.
- Handling of decadal RW interpolation for EU-15 weighting (interpolate linearly or step) — Claude decides, flag in commit message.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Existing Pipeline
- `scripts/extend_gdp.py` — full current pipeline; all extension work starts here
- `public/data/balearic_gdp_pc.csv` — Act I output (DO NOT OVERWRITE)
- `public/data/roses_wolf_selected_comparison.csv` — derived RW per-capita CSV (shows existing schema)

### Data Sources (data lake catalog)
- INE Regional Accounts `cid=1254736167628`: `https://www.ine.es/dyngs/INEbase/en/operacion.htm?c=Estadistica_C&cid=1254736167628&idp=1254735576581&menu=resultados` — GDP and GDP per person 2000-2024 for all CCAA; download combined Spain Excel
- Eurostat `nama_10r_2gdp` API: `https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/nama_10r_2gdp` — NUTS2/national GDP; use `unit=CLV10_EUR_HAB` or equivalent chain-linked unit
- Eurostat population `demo_r_d2jan`: `https://ec.europa.eu/eurostat/databrowser/view/demo_r_d2jan/default/table` — regional/national population post-2000

### Planning Documents
- `.planning/notes/act2-datastory-decisions.md` — locked decisions from v2.0 exploration (peer set, EU-15 construction, narrative spec)
- `.planning/REQUIREMENTS.md` §v2 Requirements — DATA-01 through DATA-08

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `load_roseswolf(path)` — loads RW Excel/CSV into tidy `(nuts2_code, year, value)` df; needs extension to also extract population
- `load_ine_excel(path)` — parses INE chain-linked Excel into tidy df; directly reusable for all Spanish CCAA peers
- `enforce_eurostat_unit_guard(df)` — validates CLV unit on Eurostat data; reuse unchanged
- `chain_link(rw_df, eurostat_df, anchor_year)` — core chain-linking logic; parameterise `anchor_year` (currently hardcoded as 2022→2020)
- `find_input_file(workspace, filename)` — searches `data/`, `public/data/` for input files; reuse for peer inputs

### Established Patterns
- `ANCHOR_YEAR` constant at module top — change to 2020 for Act II outputs
- `PipelineError` / `CheckResult` — use same error/validation pattern for new series
- Output written to `output/` directory at runtime (not committed); then manually copied to `public/data/` — same workflow for Act II outputs

### Integration Points
- New per-series CSV files land in `public/data/act2_*.csv` — fetched by Act II Vue component via `useFetch("/data/act2_{slug}.csv")`
- `YEAR_MIN` (1900) and `YEAR_MAX` remain unchanged

</code_context>

<specifics>
## Specific Ideas

- EU-15 member countries (1995 accession boundaries): AT, BE, DE, DK, FI, FR, GB, GR, IE, IT, LU, MT (joined 2004 — clarify if included), NL, PT, SE. Confirm exact list against `act2.md` narrative.
- The `roses_wolf_selected_comparison.csv` shows the existing approach: per-decadal RW values interpolated to annual by the chain-linking step — same interpolation applies to EU-15 country RW values before weighting.
- For the EU-15 reference, the output file will be `act2_eu15_avg.csv` with values as real EUR per capita (same unit as all other Act II series).

</specifics>

<deferred>
## Deferred Ideas

- Fetching INE data programmatically via INE JSON API at runtime — deferred; use pre-downloaded files for Phase 2.
- Adding a `--series` CLI flag to `extend_gdp.py` to selectively rebuild one series — could be backlog item.
- Validation dashboard / HTML report from sanity checks — deferred to future.

</deferred>

---

*Phase: 02-data-pipeline-extension-v2-0*
*Context gathered: 2026-04-23*
