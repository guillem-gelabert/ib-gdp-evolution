# IB GDP Evolution

## What This Is

A Nuxt scrollytelling site about the Balearic Islands' GDP-per-capita arc from 1900 to 2024. The shipped repo now contains two narrative acts: an editorial single-series Act I line chart and an Act II comparison scene that places the Balearic trajectory against peer regions plus an EU-15 benchmark.

## Core Value

Present the long-run GDP-per-capita story as a beautiful, editorial, animated reading experience that makes the historical arc legible at a glance.

## Current Milestone

No active milestone. v3.0 shipped 2026-04-30. Run `/gsd-new-milestone` to start the next cycle.

## Requirements

### Validated

- ✓ Act I chart upgrade shipped: hidden points, nearest-x hover, Perlin-style distortion, arrowhead, 800 ms reveal — v1.0
- ✓ Act II local-proxy data generation path shipped via `scripts/extend_gdp.py --act2-local-proxy` — v2.0
- ✓ Act II comparison chart shipped with multi-line rendering and animated real-eur ↔ pct-eu15 transitions — v2.0
- ✓ Act II scrollytelling scene shipped with preloaded data and the Step 8-17 narrative arc — v2.0
- ✓ Full Eurostat-backed ETL for all Act II comparison series via data-lake adapter with API fallback — v3.0
- ✓ Chain-linking with Rosés-Wolf for every region at 2019 anchor; EU-15 population-weighted average with UK carry-forward — v3.0
- ✓ Sanity validation against local-proxy baseline (8/8 PASS, growth-rate correlation = 1.0000) — v3.0

### Active

(None — awaiting next milestone definition)

### Out of Scope

- Server-side data APIs while static CSV delivery remains sufficient.
- Broad UI state-management changes; the story remains component-driven.
- Membership-date-aware EU-15 composition for the current analytical benchmark.
- ONS-sourced UK GDP for 2020-2024 (carry-forward stopgap is acceptable for current Act II story).

## Context

- **Frontend:** Nuxt 4, Vue 3, D3, static generation via `pnpm generate`.
- **Data path:** Offline Python ETL plus a shipped local-proxy comparison-data branch for Act II.
- **Narrative surface:** Act I and Act II both live on the home-page reading flow.
- **Reference docs:** `.planning/milestones/v2.0-ROADMAP.md`, `.planning/MILESTONES.md`, `.planning/codebase/`.

## Known Gaps

- Browser-based UAT for pacing, feel, and responsiveness is still manual.
- UK post-Brexit GDP relies on a 2019 carry-forward stopgap; real ONS integration not yet pursued.
- GSD CLI milestone parsing is not fully aligned with the archived repo state.

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Use Perlin/simplex-style distortion rather than random jitter | Preserve the line's trend while adding an editorial hand-drawn feel | ✓ Good |
| Keep the Act I data asset untouched and emit separate `act2_*.csv` files | Avoid regressions in the shipped first-act story while enabling Act II | ✓ Good |
| Build Act II as a dedicated chart component with shared helpers | The multi-line dual-axis behavior is structurally different from Act I | ✓ Good |
| Ship Act II in local-proxy mode when raw inputs are missing | Better to ship honestly documented scope than imply a pipeline the repo cannot reproduce | ✓ Resolved in v3.0 — replaced by data-lake ETL |
| Make the EU-15 baseline transition scroll-driven | The axis switch is a narrative beat, not a utility toggle | ✓ Good |
| Batch ingestion (3 Eurostat sources) over per-geo ingestion (~20 sources) | Simpler static catalog index, fewer artifacts in the data-lake | ✓ Good |
| Data-lake-first adapter with transparent API fallback | Reproducibility and offline runs without losing live-fetch escape hatch | ✓ Good |
| 2019 anchor year for chain-linking instead of 2022 | Avoid COVID-distorted GDP levels in the splice point | ✓ Good |
| UK 2019 carry-forward for 2020-2024 in EU-15 average | Eurostat NAMA_10_PC drops UK post-Brexit; carry-forward keeps the weighted average continuous | ⚠ Revisit if ONS data is needed |

## Previous Milestone Brief

<details>
<summary>Archived v3.0 focus</summary>

v3.0's goal was to retire the local-proxy Act II data path and replace it with a real Eurostat-backed pipeline. Phase 5 ingested 3 Eurostat datasets into the data-lake, built a data-lake-first adapter with API fallback, chain-linked all 7 series to Rosés-Wolf at 2019, computed the EU-15 population-weighted average with UK carry-forward, and emitted the same `public/data/act2_*.csv` files the frontend already consumed. Verified by 8/8 sanity checks PASS and growth-rate correlation = 1.0000 against the local-proxy baseline. Full details in `.planning/milestones/v3.0-ROADMAP.md`.

</details>

<details>
<summary>Archived v2.0 focus</summary>

Act II's milestone goal was to show that the Balearic post-1960 rise was continental while the later relative decline was more specific. The shipped implementation covered the comparison-data path, a dedicated chart component, and the second scrollytelling scene, all documented in `.planning/milestones/v2.0-ROADMAP.md`.

</details>

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd-transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd-complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-04-30 after v3.0 milestone — Full Act II ETL shipped*
