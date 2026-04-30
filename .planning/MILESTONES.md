# Milestones

## v3.0 — Full Act II ETL

- **Status:** Shipped 2026-04-30
- **Scope:** 1 phase, 3 plans, 6 tasks
- **Archive:** `.planning/milestones/v3.0-ROADMAP.md`, `.planning/milestones/v3.0-REQUIREMENTS.md`

**Key accomplishments:**

1. Ingested 3 Eurostat datasets (`nama_10r_2gdp` NUTS2, `nama_10_pc` NUTS0 EU-15, `demo_pjan` EU-15 population) into the data-lake with a static catalog index of 33 `dataset|geo` entries.
2. Added a data-lake-first adapter layer in `extend_gdp.py` (`_fetch_eurostat_df`) with transparent fallback to the live Eurostat API.
3. Aligned `act2_series_list()` with the 7 frontend slugs (balearic_islands, extremadura, andalucia, portugal, ireland, france, eu15_avg) and chain-linked all series to Rosés-Wolf at the 2019 anchor year.
4. Computed the EU-15 population-weighted average from individual country series with UK post-Brexit carry-forward (2019 value held for 2020-2024).
5. Replaced `--act2-local-proxy` with `--act2-datalake` end-to-end; sanity report shows 8/8 PASS and baseline-regression growth-rate correlation = 1.0000 against the local-proxy baseline.
6. Validated pipeline determinism: re-runs produce byte-identical CSVs.

**Known gaps carried forward:**

- Browser-based UAT for the full Act I + Act II reading flow is still manual.
- UK post-Brexit GDP carry-forward is a stopgap; real ONS data integration deferred to a future milestone.
- Membership-date-aware EU-15 composition still uses the static analytical benchmark.

---

## v2.0 — Act II: Who Else Got Richer

- **Status:** Shipped 2026-04-23, archived 2026-04-27
- **Scope:** 4 phases, 9 plans, 2 shipped story acts in the repo
- **Archive:** `.planning/milestones/v2.0-ROADMAP.md`, `.planning/milestones/v2.0-REQUIREMENTS.md`, `.planning/milestones/v2.0-MILESTONE-AUDIT.md`

**Key accomplishments:**

1. Upgraded the Act I chart with hidden points, nearest-x hover, editorial line distortion, marker endcap, and an 800 ms reveal.
2. Added a shipped Act II local-proxy data pipeline that emits the comparison CSV set needed by the frontend.
3. Built a dedicated Act II comparison chart with multi-line rendering, per-series state, and animated real-euro to EU-15-relative axis transitions.
4. Integrated Act II into the story flow as a separate scrollama scene with preloaded datasets and narrative choreography for Steps 8-17.
5. Verified the shipped scope with `pnpm generate` and `python3 scripts/extend_gdp.py --act2-local-proxy`.

**Known gaps carried forward:**

- Browser-based UAT for the full Act I + Act II reading flow is still manual.
- Full raw-input ETL support for Act II remains deferred behind missing upstream inputs.
- GSD CLI milestone parsing still disagrees with the now-archived artifact state in this repo.
