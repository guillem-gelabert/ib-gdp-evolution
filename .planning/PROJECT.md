# IB GDP Evolution

## What This Is

A Nuxt 4 scrollytelling site that visualizes the evolution of GDP per capita in the Balearic Islands (Illes Balears) from 1900 to 2024. A long-form narrative page scrolls through D3-rendered line-chart steps powered by `scrollama`, driven by a single spliced CSV series produced by an offline Python ETL that chain-links Rosés-Wolf (1900–1999) with Eurostat/INE (2000–2024).

## Core Value

Present the 125-year GDP-per-capita story as a beautiful, editorial, animated chart that communicates the long-arc transformation at a glance.

## Current Milestone: v2.0 Act II — Who Else Got Richer

**Goal:** Build the Act II scrollytelling scene — a multi-line, axis-switching peer comparison that shows IB's post-1960 climb was continental, and its post-1990 relative fall is its own.

**Target features:**
- Extended chain-linked data pipeline (peer regions/countries + EU-15 reference) anchored at **2020**
- Peer series: Extremadura, Galicia, Castilla-La Mancha, Portugal, Ireland, Malta
- EU-15 reference line (GDP-weighted per-capita average of the 15 member countries)
- New Act II chart component (separate from `line-chart.vue`) supporting multi-line + dual axis modes
- Scroll-driven animated axis transition (real € → % of EU-15 avg; EU-15 line flattens to y=100 baseline)
- Scrollytelling Steps 8–17 from `act2.md` (pre-loaded data, step-driven state)

**Source spec:** `act2.md` (narrative). **Decisions log:** `.planning/notes/act2-datastory-decisions.md`.

**Note on v1.0:** Phase 1 (D3 Chart Upgrade) remains in the roadmap as `pending`; v2.0 phases continue numbering from there.

## Requirements

### Validated

<!-- Shipped and confirmed valuable. -->

- ✓ Chain-linked Rosés-Wolf + Eurostat/INE series at 2022 anchor — existing
- ✓ Client-rendered D3 line chart with per-source styling (`RW`, `INE`) — existing (`app/components/line-chart.vue`)
- ✓ `scrollama`-driven scrollytelling steps window the chart by year range — existing (`app/components/story-page.vue`)
- ✓ Hover tooltip with dashed crosshair line — existing (`showTooltip` in `line-chart.vue`)
- ✓ Tailwind editorial theme with custom tokens (`cream`, `ink`, `muted`, `accent`, `rule`) — existing (`tailwind.config.ts`)
- ✓ Static CSV data loading via `useFetch` + `d3.csvParse` — existing
- ✓ Python ETL with 7 sanity checks and chain-linking at `ANCHOR_YEAR=2022` — existing (`scripts/extend_gdp.py`)

### Active

<!-- Current scope. Building toward these. -->

#### v1.0 — Act I chart upgrade (Phase 1, still pending)

- [ ] Hide individual data points (circles) on the line chart
- [ ] On mouseover anywhere on the chart, show tooltip + crosshair for the point horizontally closest to the cursor (x-axis bisect)
- [ ] Apply subtle perlin-noise displacement to the line path for a hand-drawn/organic feel
- [ ] Animate the line growing smoothly (stroke reveal / progressive draw on step change)
- [ ] Add an arrowhead marker at the end of the line

#### v2.0 — Act II "Who Else Got Richer"

- [ ] Extend `extend_gdp.py` with configurable anchor year (2020) and non-NUTS2 series identifiers
- [ ] Regenerate IB series + produce chain-linked peer series (Extremadura, Galicia, Castilla-La Mancha, Portugal, Ireland, Malta) and EU-15 weighted reference
- [ ] Build Act II chart component (multi-line, dual axis modes, animated axis transition, per-line state)
- [ ] Wire Steps 8–17 from `act2.md` as scrollytelling steps driving chart state
- [ ] Axis-transition scroll step where EU-15 line flattens to y=100 baseline while peers re-scale

### Out of Scope

- Multi-region comparison in UI — current story focuses on a single spliced Balearic series; other regions stay in the ETL only
- Server-side data API — CSV served statically from `public/data/` keeps deploys simple
- Unit tests / E2E tests — no test infra exists; not worth adding for a single-component edit
- Pinia / global state — component-local refs are sufficient
- Accessibility overhaul of SVG — known gap (see `.planning/codebase/CONCERNS.md`) but out of this milestone's scope

## Context

- **Nuxt 4.4.2 + Vue 3.5 + TypeScript**, single page (`/`), SSG-capable (`nuxt generate`).
- **Visualization component:** `app/components/line-chart.vue` — imperative D3 `initialize()` / `update(animate)` pipeline, enter/update/exit joins keyed by `source`/`year`, 800 ms `easeCubicInOut` transitions.
- **D3 usage:** namespace import `import * as d3 from "d3"`, excluded from Vite optimizeDeps (`nuxt.config.ts`).
- **Current line rendering:** two `path.series-line` (one per `source`) using `d3.line()` with no curve interpolation.
- **Current point rendering:** one `<circle>` per data point in `pointsG`, with per-point `mouseenter`/`mousemove`/`mouseleave` bound to `showTooltip` / `hideTooltip`.
- **Codebase map:** fresh as of 2026-04-23, see `.planning/codebase/`.

## Constraints

- **Tech stack**: Must remain Nuxt 4 + Vue 3 Composition API + D3 — no alternate viz libraries introduced.
- **Browser compatibility**: Modern evergreen browsers only (viz is the product, not reach).
- **Build**: `nuxt generate` must continue to work (static output).
- **Performance**: Chart re-renders on every scrollama step — per-frame Perlin noise work must be bounded so transitions stay smooth.
- **Style**: Stay within the editorial palette (`#660000` line, cream background, DM Mono labels) — no color or typography drift without explicit decision.

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Treat D3 chart enhancements as a single phase | 5 tightly-coupled visual tweaks on one component | — Pending |
| Use Perlin noise (not random jitter) for the hand-drawn feel | Spatially coherent distortion preserves the line's trend | — Pending |
| Nearest-x tooltip via `d3.bisect` on years | Standard pattern; data is already year-sorted | — Pending |
| Line-grow animation via `stroke-dasharray` / `stroke-dashoffset` | Idiomatic D3/SVG technique, GPU-friendly | — Pending |
| Arrowhead via `<marker>` with `marker-end` on the path | Native SVG, transitions cleanly | — Pending |
| Re-anchor all chain-linking at 2020 for v2.0 | Consistent seam across all series (IB + peers + EU-15); required by multi-line compare | — Pending |
| Act II uses a new chart component, not a fork of `line-chart.vue` | Multi-line + dual-axis + animated transition has different structural requirements; share visual language via extracted utilities | — Pending |
| EU-15 reference constructed as GDP-weighted per-capita average of 15 member countries | Analytical benchmark held constant across 1900–2024; better than unweighted mean, cleaner than membership-date composition | — Pending |
| Axis transition (real € → % EU-15) is scroll-driven, not a toggle | Matches `act2.md` Step 13 narrative choreography; EU-15 line literally flattens into the y=100 baseline | — Pending |
| Pre-load all Act II peer data on mount | Dataset is small (tens of KB); avoids lazy-load jank during scroll | — Pending |

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
*Last updated: 2026-04-23 — milestone v2.0 (Act II) kickoff*
