# Domain Pitfalls

**Domain:** Multi-region Eurostat data ingestion for GDP chain-linking pipeline
**Researched:** 2026-04-29
**Scope:** Replacing local-proxy Act II data path with full Eurostat-backed ETL for 7 series (3 Spanish NUTS2, 3 NUTS0 countries, EU-15 average)

## Critical Pitfalls

### Pitfall 1: nama_10r_2gdp Has No Chain-Linked Volume Data for NUTS2 Regions

**What goes wrong:** The developer assumes `nama_10r_2gdp` can provide real (constant-price) GDP per capita for Spanish NUTS2 regions (ES53, ES43, ES61), mirroring the CLV data available at national level from `nama_10_pc`. In reality, `nama_10r_2gdp` only reports GDP at **current market prices** (EUR_HAB, MIO_EUR). There is no CLV10_EUR_HAB equivalent for NUTS2 regions in Eurostat.

**Why it happens:** The existing pipeline already uses `fetch_nama_10_pc_clv10` for national-level series and `fetch_nama_10r_2gdp_eur_hab` for regional — the naming similarity masks the fact that one is chain-linked volume and the other is current prices. The unit guard (`enforce_eurostat_unit_guard`) correctly rejects CP/PPS from CSV files, but the API fetch functions bypass the guard because the unit is baked into the query parameters.

**Consequences:** If current-price EUR_HAB is chain-linked with Rosés-Wolf (which is in 2011 PPP dollars), the resulting series conflates real growth with inflation. The spliced curve would show Spanish regions growing faster than reality from 2000 onward, and the post-2020 inflationary spike would appear as a GDP boom.

**Prevention:**
- For Spanish NUTS2 regions, use INE chain-linked regional accounts (the current approach with `InstitutionalSource.ine` is correct — preserve it).
- If INE data is unavailable, derive real growth rates from `nama_10r_2gvagr` (volume growth by NUTS2 region) and apply them to the Rosés-Wolf anchor level.
- Never mix `EUR_HAB` (current prices) with PPP or CLV series in the same chain-linking operation without explicit deflation.
- Add a unit assertion at the series-spec level: each `Act2SeriesSpec` should declare expected unit class (CLV vs CP) so the pipeline can reject mismatched data before chain-linking.

**Detection:** Sanity check 6 (level plausibility) should catch the most egregious cases — a 2024/2019 ratio above 1.5 for any region is almost certainly an inflation contamination signal.

**Which phase should address it:** Phase 1 (data ingestion layer) — validate unit class per series before any chain-linking proceeds.

---

### Pitfall 2: Anchor Year 2020 Distorts Tourism-Dependent Regions

**What goes wrong:** The current default `ANCHOR_YEAR = 2020` is a COVID year. For tourism-dependent economies like the Balearic Islands, 2020 GDP per capita dropped ~25%. Chain-linking at this anchor means the entire pre-2000 historical series is scaled relative to a COVID-depressed level, artificially inflating all historical values.

**Why it happens:** The anchor year was chosen for data availability (both Rosés-Wolf v7 and Eurostat cover 2020). COVID's regional asymmetry means a globally "available" year is locally pathological.

**Consequences:** The Balearic Islands' historical GDP per capita appears 20-30% higher than it should relative to other regions that experienced a milder COVID shock. Cross-regional comparisons (the entire point of Act II) become systematically biased. The seam continuity check passes because both sides of the splice match at the anchor — but the anchor level itself is wrong.

**Prevention:**
- Use 2019 as the anchor year: it's the last pre-COVID year with full data from both Rosés-Wolf v7 (extends to 2022) and Eurostat.
- If 2019 is unavailable for some series, use 2018 as fallback.
- Add a check: if anchor year is 2020 or 2021, emit a WARN in the sanity report noting COVID distortion risk for tourism regions.
- Validate by comparing the chain-linked 2019 level against the Rosés-Wolf 2019 level — divergence beyond 2% signals a bad anchor.

**Detection:** Compare chain-linked output for ES53 at year 2019 against known Rosés-Wolf v7 value. A ratio outside 0.95–1.05 indicates the anchor year is injecting distortion.

**Which phase should address it:** Phase 1 (pipeline configuration) — change `ANCHOR_YEAR` default; Phase 2 (chain-linking) — add anchor-year validation.

---

### Pitfall 3: UK Data Gap Breaks EU-15 Average Post-2020

**What goes wrong:** EU-15 includes the United Kingdom. Eurostat stopped receiving UK data from ONS after Brexit (January 2021). Any EU-15 population-weighted average computed from Eurostat sources alone will silently drop the UK from 2021 onward, causing a level discontinuity in the EU-15 benchmark series.

**Why it happens:** The existing code defines `EU15_EUROSTAT_GEOS` with `"UK"` included. The `fetch_nama_10_pc_clv10` call includes UK in the query, but Eurostat returns no data for UK after ~2020. The `_fill_population_backward` helper forward-fills population but the GDP per capita side silently has no values. The weighted average loop in `run_act2` skips countries where `o_row` is empty for a given year — so UK just vanishes from the denominator.

**Consequences:** The EU-15 average jumps when UK drops out because UK's GDP per capita differs from the remaining 14. The narrative interpretation ("Balearics converge to EU-15") changes meaning mid-series if the benchmark composition shifts.

**Prevention:**
- Source UK GDP per capita from ONS directly (chain-linked volume, 2019 prices) for 2021–2024.
- Alternatively, project UK values using OECD or IMF WEO growth rates applied to the last Eurostat observation.
- As a minimum, emit a WARN when any EU-15 country drops out mid-series and document the compositional break in the output metadata.
- Consider freezing UK weight at the 2020 level and projecting with OECD growth rates — this preserves series continuity at the cost of some accuracy.

**Detection:** Check that all 15 countries contribute to the weighted average in every year from 2000 to 2024. If contributor count drops below 15, flag it.

**Which phase should address it:** Phase 2 (EU-15 computation) — implement UK fallback before computing the average; Phase 3 (sanity checks) — add contributor-count check.

---

### Pitfall 4: Silently Mixing PPP Dollars and Chain-Linked Euros

**What goes wrong:** Rosés-Wolf expresses GDP per capita in **2011 international PPP dollars**. Eurostat CLV data uses **chain-linked 2010 euros** (CLV10_EUR_HAB). These are not the same unit. A developer may try to directly compare or concatenate levels from the two sources, producing a meaningless splice.

**Why it happens:** The chain-linking methodology in `compute_chainlinked_output` and `chain_link_rw_plus_institutional` correctly uses ratio-splicing (preserving growth rates and anchoring at a common year), which implicitly handles the unit difference. But if any code path bypasses ratio-splicing — e.g., directly appending Eurostat rows to the pre-2000 Rosés-Wolf rows — the unit mismatch creates a level jump that looks like a GDP shock.

**Consequences:** The spliced series has a false discontinuity at the seam year. If the ratio-splice is done correctly, this pitfall is avoided — but any future refactoring that simplifies the join logic (e.g., "just concatenate where years don't overlap") will reintroduce it.

**Prevention:**
- Never concatenate raw Rosés-Wolf and Eurostat rows without going through ratio-splice logic.
- Add an explicit assertion: output column `gdp_pc_2011ppp` must have originated from the ratio-splice function, not from raw Eurostat values.
- The sanity check (seam continuity) catches this — but only at the anchor year. Add a check that verifies the first chain-linked year (2000) doesn't jump more than 10% from the last Rosés-Wolf year (1999).

**Detection:** Seam check at anchor year + year-on-year growth check at the 1999→2000 boundary. If growth > 15% at the boundary (excluding known boom periods), flag as potential unit contamination.

**Which phase should address it:** Phase 2 (chain-linking) — strengthen seam checks; guard the concatenation boundary.

## Moderate Pitfalls

### Pitfall 5: Greece EL/GR Dual-Code Creates Silent Data Gaps

**What goes wrong:** Eurostat uses `EL` for Greece; ISO 3166 (and Rosés-Wolf) uses `GR`. The existing code defines two tuples — `EU15_COUNTRY_GEOS` with `"GR"` and `EU15_EUROSTAT_GEOS` with `"EL"`. If a lookup accidentally uses the wrong tuple, Greece silently drops out of the EU-15 average computation.

**Prevention:**
- Use a single canonical lookup mapping: `{"GR": "EL"}` applied at the data-ingestion boundary.
- Delete one of the two tuples and normalize all geo codes to Eurostat convention (`EL`) at load time.
- The EU-15 contributor-count check (from Pitfall 3) also catches this — if only 14 countries contribute, investigate.

**Which phase should address it:** Phase 1 (data normalization) — unify geo code representation.

---

### Pitfall 6: Sparse Rosés-Wolf Decadal Data Creates Misleading Inter-Census Trajectories

**What goes wrong:** Rosés-Wolf provides data at roughly decadal intervals (1900, 1910, 1925, 1938, 1950, 1960, 1970, 1980, 1990, 2000, ...). The `_annualize_sparse_series` function linearly interpolates between these points. For regions with non-linear growth (e.g., the Balearic Islands' tourism takeoff in the 1960s or Ireland's Celtic Tiger), linear interpolation creates smooth curves that miss the actual trajectory shape.

**Prevention:**
- Accept this as a known limitation and document it: pre-2000 annual values are interpolated, not observed.
- Do not run growth-rate checks on interpolated years — only check at observed Rosés-Wolf years.
- In the output CSV, mark interpolated years with a distinct `source` value (e.g., `roseswolf_interpolated` vs `roseswolf`).

**Which phase should address it:** Phase 2 (chain-linking) — add interpolation flag to output; Phase 3 (sanity checks) — exclude interpolated years from YoY checks.

---

### Pitfall 7: INE-to-Eurostat Coverage Misalignment for Spanish NUTS2

**What goes wrong:** INE chain-linked regional GDP starts from 2000 but may have gaps or revisions. The Eurostat proxy (`nama_10r_2gdp` EUR_HAB) starts from ~2000 too but in current prices. If INE lacks the anchor year for one region (e.g., because a recent revision dropped it), chain-linking silently fails with a `PipelineError` — but only for that region, leaving a partial output.

**Prevention:**
- Pre-check all target Spanish NUTS2 codes against the INE DataFrame before entering the chain-link loop. If any code is missing the anchor year, report all missing codes together rather than failing on the first.
- Implement a fallback: if INE is missing for a specific region-year, try the Eurostat EUR_HAB proxy with explicit CPI deflation.
- The existing `load_ine_or_build_proxy` correctly falls back to Eurostat, but the proxy uses current prices — add a deflation step or flag the output as lower-confidence.

**Which phase should address it:** Phase 1 (data ingestion) — validate anchor-year availability for all target regions upfront.

---

### Pitfall 8: NUTS Version Mismatch Between Rosés-Wolf and Eurostat

**What goes wrong:** Rosés-Wolf v7 uses NUTS-2 codes based on the 2010/2013 classification. Eurostat API returns data under the current NUTS 2021 (or 2024) classification by default. For the regions in scope (ES53, ES43, ES61), the codes happen to be stable across all NUTS versions. But if the series list is extended to other regions (e.g., French NUTS2, German Länder), code changes between NUTS versions can cause silent joins on non-matching keys.

**Prevention:**
- For the current 7 series, verify that ES53/ES43/ES61 and FR/IE/PT/MT codes are unchanged across NUTS 2010→2021. (They are — document this.)
- If adding new regions in future, always check the NUTS correspondence tables at `ec.europa.eu/eurostat/web/nuts/history`.
- Add a `nuts_version` field to `Act2SeriesSpec` and validate against Eurostat metadata.

**Which phase should address it:** Phase 1 (spec validation) — document NUTS stability for current targets; add guard for future additions.

---

### Pitfall 9: EU-15 Composition Is Anachronistic Before 1995

**What goes wrong:** The EU-15 only existed from January 1995 (when Austria, Sweden, and Finland joined). Computing an "EU-15 average" for 1900–1994 is not measuring a historical entity but a retrospective benchmark group. If the narrative calls it "the EU-15 average" without qualification, readers may assume it reflects an actual institutional aggregate.

**Prevention:**
- Label the series as "EU-15 benchmark" or "EU-15 peer group" in the frontend, not "EU-15 GDP."
- In the output CSV, use source label `eu15_benchmark_retrospective` for years before 1995 and `eu15_population_weighted` for 1995+.
- Document this clearly in the data-methods section of the scrollytelling narrative.

**Which phase should address it:** Phase 2 (EU-15 computation) — add source-label distinction; Phase 4 (frontend narrative) — update data-methods copy.

---

### Pitfall 10: Non-Additivity of Chain-Linked Series in EU-15 Aggregation

**What goes wrong:** Chain-linked (chained-volume) series are not additive. You cannot sum chain-linked GDP across 15 countries and divide by total population to get a valid EU-15 per-capita figure. The error can be several percentage points.

**Why it happens:** Chain-linking uses previous-year price weights that differ per country. Aggregating chain-linked series as if they were fixed-base-year series introduces a "residual" that grows over time.

**Prevention:**
- The existing `run_act2` correctly computes EU-15 as a population-weighted average of **per-capita** chain-linked series — this is methodologically acceptable because it weights the per-capita levels rather than summing chain-linked aggregates.
- Verify this approach is preserved in the refactored code: `EU-15 avg = Σ(gdp_pc_i × pop_i) / Σ(pop_i)`.
- Do NOT switch to summing chain-linked total GDP and dividing by total population — this is the non-additive trap.

**Which phase should address it:** Phase 2 (EU-15 computation) — add a code comment and test asserting the per-capita-weighted methodology.

## Minor Pitfalls

### Pitfall 11: Eurostat API Query Size Limits

**What goes wrong:** Requesting all EU-15 countries in a single `nama_10_pc` API call can hit URL character limits or trigger `EXTRACTION_TOO_BIG` errors, especially when combined with multiple time periods.

**Prevention:**
- Batch country requests: max 5–6 geos per API call.
- The existing `fetch_nama_10_pc_clv10` builds the geo query string by concatenating `geo=XX` parameters — test that 15 countries doesn't exceed limits.
- Add retry logic with smaller batches on 400 errors.

**Which phase should address it:** Phase 1 (data ingestion) — add batch splitting and retry.

---

### Pitfall 12: Provisional Data Flags in Recent Eurostat Years

**What goes wrong:** The most recent 1–2 years in Eurostat datasets are often provisional (flagged `P`). These values may be revised significantly in subsequent releases. If the pipeline uses 2024 as the terminal year and 2024 data is provisional, the output may change when Eurostat revises.

**Prevention:**
- Log which years are flagged provisional in the sanity report.
- Set `YEAR_MAX` to the last confirmed (non-provisional) year, or at minimum document the provisional status.
- The existing `_eurostat_json_to_df` discards flags — consider parsing the `status` field from the JSON response.

**Which phase should address it:** Phase 1 (data ingestion) — parse and log flags; Phase 3 (sanity checks) — warn on provisional terminal year.

---

### Pitfall 13: Synthetic Rosés-Wolf Backcast Quality for Non-Core Countries

**What goes wrong:** The `_synthetic_national_rw_from_eurostat_clv` function fabricates pre-1975 GDP series using a linear ramp from 25% of the 1975 value to 100% — a crude extrapolation with no historical basis. For countries like Ireland (whose pre-1960 economy was fundamentally different from post-Celtic-Tiger), this creates a fictional trajectory.

**Prevention:**
- Use actual Rosés-Wolf v7 country-level data where available (Portugal, Ireland, France are all in the dataset).
- Reserve synthetic backcasts only for countries genuinely absent from Rosés-Wolf.
- Mark synthetic backcast years with a distinct source label so the frontend can style them differently (e.g., dashed lines).

**Which phase should address it:** Phase 1 (data sourcing) — prefer real Rosés-Wolf data over synthetic; Phase 2 (chain-linking) — mark synthetic vs real source.

## Phase-Specific Warnings

| Phase Topic | Likely Pitfall | Mitigation |
|-------------|---------------|------------|
| Data ingestion (Eurostat API) | nama_10r_2gdp current-price trap (P1) | Use INE for Spanish NUTS2; verify unit class per series |
| Data ingestion (Eurostat API) | UK gap post-2020 (P3) | Source UK from ONS or project with OECD growth rates |
| Data ingestion (Eurostat API) | API query size limits (P11) | Batch geo parameters; retry on 400 |
| Data ingestion (Rosés-Wolf) | NUTS version mismatch (P8) | Document code stability; add correspondence guard |
| Chain-linking | Anchor year COVID distortion (P2) | Switch to 2019 anchor |
| Chain-linking | Unit mixing PPP vs CLV (P4) | Enforce ratio-splice path; add 1999→2000 seam check |
| Chain-linking | INE coverage gaps (P7) | Pre-validate anchor year for all regions |
| EU-15 average | UK dropout mid-series (P3) | Contributor-count check per year |
| EU-15 average | Non-additivity trap (P10) | Preserve per-capita-weighted methodology |
| EU-15 average | Greece EL/GR code (P5) | Normalize all geo codes at boundary |
| EU-15 average | Anachronistic pre-1995 label (P9) | Label as benchmark, not institutional aggregate |
| Output / sanity | Provisional data (P12) | Parse and log Eurostat flags |
| Output / sanity | Interpolation artifacts (P6) | Mark interpolated years; exclude from YoY checks |

## Integration Pitfalls

### Full-ETL vs Local-Proxy Output Compatibility

The full ETL must produce CSV files identical in schema to the local-proxy outputs (`year,gdp_pc,source,unit`). Key differences to watch:

1. **Year density:** Local proxy has ~15 sparse years per series; full ETL should produce annual data (125 rows per series). The frontend `act2-chart.vue` must handle both densities — if it assumes sparse data, annual rendering may degrade performance or clutter the visualization.

2. **Source column values:** Local proxy uses `comparison_*` labels; full ETL uses `roseswolf`, `roseswolf_chainlinked`, `ine_chainlinked`, `eurostat_chainlinked`. The frontend may key styling on source values — verify the chart component handles the new labels or map them to a common label set.

3. **Value magnitude:** If the anchor year changes (2020 → 2019), all historical levels shift by the ratio `RW(2019)/RW(2020)`. For ES53 this is ~33% because COVID cratered the 2020 level. A regression test comparing full-ETL output against local-proxy baselines must account for this systematic level shift — it is not a bug.

4. **EU-15 provenance:** Local proxy uses a pre-computed `eu15_minus_greece` series from `roses_wolf_selected_comparison.csv`. Full ETL computes a population-weighted 15-country average. These will differ in level and shape — the sanity check should compare growth-rate correlation, not absolute levels.

## Sources

- Eurostat Data Browser: nama_10r_2gdp metadata (current market prices only for NUTS2) — https://ec.europa.eu/eurostat/databrowser/view/nama_10r_2gdp
- Eurostat Data Browser: nama_10_pc metadata (national, includes CLV10_EUR_HAB) — https://ec.europa.eu/eurostat/databrowser/product/view/nama_10_pc
- Eurostat Data Browser: nama_10r_2gvagr (regional volume growth rates) — https://ec.europa.eu/eurostat/databrowser/product/view/tgs00037
- Eurostat NUTS history and correspondence tables — https://ec.europa.eu/eurostat/web/nuts/history
- Eurostat FAQ on UK post-Brexit — https://ec.europa.eu/eurostat/help/faq
- Rosés-Wolf v7 (CEPR) — https://cepr.org/node/424487
- BEA on non-additivity of chained series — https://www.bea.gov/resources/methodologies/chained-dollar-indexes
- Global Macro Database methodology (ratio-splicing) — https://www.globalmacrodata.com/files/GMD.pdf
- Eurostat API FAQ (query limits) — https://ec.europa.eu/eurostat/web/user-guides/data-browser/api-data-access/api-faq
