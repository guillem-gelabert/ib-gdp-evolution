# IB GDP Evolution

## What This Is

A Nuxt scrollytelling site about the Balearic Islands' GDP-per-capita arc from 1900 to 2024. The shipped repo now contains two narrative acts: an editorial single-series Act I line chart and an Act II comparison scene that places the Balearic trajectory against peer regions plus an EU-15 benchmark.

## Core Value

Present the long-run GDP-per-capita story as a beautiful, editorial, animated reading experience that makes the historical arc legible at a glance.

## Current Milestone: v3.0 Full Act II ETL

**Goal:** Replace the `--act2-local-proxy` data path with a pipeline that sources Eurostat NAMA regional GDP from the data-lake MCP for all series, chain-links with Roses-Wolf, and emits the same `act2_*.csv` files.

**Target features:**
- Ingest Eurostat NAMA_10R_2GDP (NUTS2) from data-lake for Spanish regions (ES53, ES43, ES61)
- Ingest Eurostat NAMA_10_PC (NUTS0) from data-lake for countries (FR, IE, PT, plus EU-15 set)
- Chain-link all modern Eurostat series with Roses-Wolf (1900-1999) at an anchor year
- Emit the 7 `act2_*.csv` files the frontend already consumes
- Sanity checks validating full-ETL output against the local-proxy baseline

## Requirements

### Validated

- ✓ Act I chart upgrade shipped: hidden points, nearest-x hover, Perlin-style distortion, arrowhead, 800 ms reveal.
- ✓ Act II local-proxy data generation path shipped via `scripts/extend_gdp.py --act2-local-proxy`.
- ✓ Act II comparison chart shipped with multi-line rendering and animated real-eur ↔ pct-eu15 transitions.
- ✓ Act II scrollytelling scene shipped with preloaded data and the Step 8-17 narrative arc.

### Active

- [ ] Full Eurostat-backed ETL for all Act II comparison series
- [ ] Chain-linking with Roses-Wolf for every region
- [ ] Sanity validation against local-proxy baseline

### Out of Scope

- Server-side data APIs while static CSV delivery remains sufficient.
- Broad UI state-management changes; the story remains component-driven.
- Membership-date-aware EU-15 composition for the current analytical benchmark.

## Context

- **Frontend:** Nuxt 4, Vue 3, D3, static generation via `pnpm generate`.
- **Data path:** Offline Python ETL plus a shipped local-proxy comparison-data branch for Act II.
- **Narrative surface:** Act I and Act II both live on the home-page reading flow.
- **Reference docs:** `.planning/milestones/v2.0-ROADMAP.md`, `.planning/MILESTONES.md`, `.planning/codebase/`.

## Known Gaps

- Browser-based UAT for pacing, feel, and responsiveness is still manual.
- The fully sourced Act II ETL remains deferred behind missing upstream raw data.
- GSD CLI milestone parsing is not fully aligned with the archived repo state.

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Use Perlin/simplex-style distortion rather than random jitter | Preserve the line's trend while adding an editorial hand-drawn feel | ✓ Good |
| Keep the Act I data asset untouched and emit separate `act2_*.csv` files | Avoid regressions in the shipped first-act story while enabling Act II | ✓ Good |
| Build Act II as a dedicated chart component with shared helpers | The multi-line dual-axis behavior is structurally different from Act I | ✓ Good |
| Ship Act II in local-proxy mode when raw inputs are missing | Better to ship honestly documented scope than imply a pipeline the repo cannot reproduce | ⚠ Revisit when full inputs arrive |
| Make the EU-15 baseline transition scroll-driven | The axis switch is a narrative beat, not a utility toggle | ✓ Good |

## Previous Milestone Brief

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
*Last updated: 2026-04-29 — Phase 5 complete: full Act II ETL replaces local-proxy with data-lake pipeline*
