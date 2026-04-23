# Roadmap: IB GDP Evolution

## Overview

**v1.0** (Phase 1) focuses on upgrading the D3 line chart in `app/components/line-chart.vue` with editorial, animated, and organic enhancements: hidden points, nearest-x bisect tooltip, Perlin-noise line distortion, smooth grow animation, and arrowhead terminator. One cohesive phase because all six requirements touch the same component and the same D3 update cycle.

**v2.0** (Phases 2–4) implements the Act II datastory from `act2.md` — "Who Else Got Richer". The Balearic climb is placed alongside peer regions (Extremadura, Galicia, Castilla-La Mancha, Portugal, Ireland, Malta) and a weighted EU-15 reference, then the Y-axis switches from real € to "% of EU-15 average (EU-15 = 100)" in a held, scroll-choreographed moment. Phases split along clean seams: data (Python ETL extension) → chart (new Vue component with multi-line + dual-axis) → narrative (scrollytelling Steps 8–17).

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3, 4): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

- [x] **Phase 1: D3 Chart Upgrade** — Hide points, nearest-x tooltip, Perlin-noise line, grow animation, arrowhead *(v1.0)*
- [ ] **Phase 2: Data Pipeline Extension** — Extend `extend_gdp.py`: 2020 anchor, peer regions/countries, EU-15 weighted reference, regenerated IB *(v2.0)*
- [ ] **Phase 3: Act II Chart Component** — New Vue component: multi-line, dual axis modes, animated axis transition, per-line state, annotations *(v2.0)*
- [ ] **Phase 4: Act II Scrollytelling** — New scrollama scene, Steps 8–17 from `act2.md`, axis-switch choreography, editorial prose layout *(v2.0)*

## Phase Details

### Phase 1: D3 Chart Upgrade *(v1.0)*

**Goal**: Transform `app/components/line-chart.vue` into an editorial, organic, animated line chart with a nearest-x interaction model.

**UI hint**: yes

**Depends on**: Nothing (first phase)

**Requirements**: CHART-01, CHART-02, CHART-03, CHART-04, CHART-05, CHART-06

**Success Criteria** (what must be TRUE):
  1. No data-point circles are visible in the default rendered chart state.
  2. Moving the cursor horizontally over the chart area always highlights exactly one point (the nearest year) with tooltip + crosshair; moving off the chart hides them.
  3. The line path visibly deviates from a pure straight interpolation in a smooth, spatially coherent way (Perlin noise), reading as hand-drawn rather than jittery.
  4. On mount and on each scrollama step change, the line animates as if being drawn progressively from start to end.
  5. An arrowhead is visible at the most-recent-year end of the line, styled consistently with the line's color and stroke.
  6. `nuxt generate` still succeeds and no console errors are thrown during scrollytelling interaction.

**Plans**: 3 plans in 3 waves (sequential — same component file)

Plans:
- [x] `01-d3-chart-upgrade-v1-0/01-01-PLAN.md` — CHART-01, CHART-03, CHART-05: hidden default points, memoized simplex line, marker defs + `marker-end`
- [x] `01-d3-chart-upgrade-v1-0/01-02-PLAN.md` — CHART-02: overlay, `d3.pointers` + nearest-year bisect, full-height crosshair, highlight + tooltip, pointer leave clears
- [x] `01-d3-chart-upgrade-v1-0/01-03-PLAN.md` — CHART-04, CHART-06: 800ms stroke-dash reveal + `nuxt generate` + browser console smokescreen

---

### Phase 2: Data Pipeline Extension *(v2.0)*

**Goal**: Extend `scripts/extend_gdp.py` to produce Act II per-series chain-linked per-capita GDP CSVs (2020 anchor) for IB + six peer series + a population-weighted EU-15 reference (`public/data/act2_*.csv`, schema `year,gdp_pc,source,unit`), all passing the existing sanity checks, without overwriting Act I’s `balearic_gdp_pc.csv` (per `02-CONTEXT.md` D-06–D-08).

**UI hint**: no

**Depends on**: Nothing (independent of Phase 1; can run in parallel with it)

**Requirements**: DATA-01, DATA-02, DATA-03, DATA-04, DATA-05, DATA-06, DATA-07, DATA-08

**Success Criteria** (what must be TRUE):
  1. `extend_gdp.py` runs with `ANCHOR_YEAR=2020` (default) and emits one `public/data/act2_*.csv` per series: IB, Extremadura, Galicia, Castilla-La Mancha, Portugal, Ireland, Malta, and EU-15, each covering 1900–2024 with no unintended gaps (checks surface exceptions).
  2. Every series passes the existing sanity checks: seam continuity at the anchor year, growth-rate preservation (post-CHAIN_START), no missing years, outlier guard (YoY within ±25% except 2020–2021), level plausibility (2024/2019 ratio in [0.5, 3.0]), and CLV unit guard on Eurostat inputs.
  3. The EU-15 reference series is computed as `sum(per_capita_i × population_i) / sum(population_i)` over the 15 member countries per year, with population from RW (pre-2000) and Eurostat (2000+), per `02-CONTEXT.md` D-01–D-02 and `act2-datastory-decisions.md` §5.
  4. Act I’s `balearic_gdp_pc.csv` (2022 anchor) remains unchanged; the 2020-anchor IB line for Act II is `act2_balearic_islands.csv` (or the slug locked in `02-CONTEXT.md`). Act I continues to use the original file.
  5. A sanity report is written (same format as today) and every check is PASS or WARN-with-explanation — no FAILs.

**Plans**: 4 plans in 4 waves (02-01 → 02-04)

Plans:
- [ ] `02-data-pipeline-extension-v2-0/02-01-PLAN.md` — DATA-01, DATA-02: anchor 2020, RW population loader, series identifier hooks
- [ ] `02-data-pipeline-extension-v2-0/02-02-PLAN.md` — DATA-02, DATA-03, DATA-05: `load_ine_excel`, Spanish NUTS2+IB INE+RW chain-link
- [ ] `02-data-pipeline-extension-v2-0/02-03-PLAN.md` — DATA-04, DATA-06: PT/IE/MT NUTS0, pop loaders, EU-15 weighted index
- [ ] `02-data-pipeline-extension-v2-0/02-04-PLAN.md` — DATA-05, DATA-07, DATA-08: `act2_*.csv` emission, full sanity report, e2e verify

---

### Phase 3: Act II Chart Component *(v2.0)*

**Goal**: Build a new Vue/D3 component that renders the Act II multi-line chart with two axis modes and an animated scroll-driven transition between them, sharing visual language with Act I via extracted utilities.

**UI hint**: yes

**Depends on**: Phase 2 (needs the Act II `act2_*.csv` per-series assets). Independent of Phase 1 for shipping, but should consume shared utilities extracted from Phase 1's component.

**Requirements**: ACT2-01, ACT2-02, ACT2-03, ACT2-04, ACT2-05, ACT2-06

**Success Criteria** (what must be TRUE):
  1. The component renders IB + 6 peer lines + EU-15 reference from the Phase 2 CSV, each with independently controllable visual state (active color, faded gray, hidden, highlighted).
  2. Switching the `axisMode` prop from `real-eur` to `pct-eu15` animates in a single tween: the EU-15 line morphs to a horizontal y=100 line while all other lines re-scale to their percentage-of-EU-15 positions.
  3. The reverse transition (`pct-eu15` → `real-eur`) is also animated and visually consistent.
  4. The component reuses Act I's Perlin line distortion, arrowhead terminator, and editorial palette via shared utilities (imported, not duplicated).
  5. A "peak" shaded annotation band (IB, ~1988–1993) and the y=100 reference line render as data-driven primitives, not hard-coded overlays.
  6. `nuxt generate` succeeds with the new component included.

**Plans**: TBD (finalized during `/gsd-plan-phase 3`)

---

### Phase 4: Act II Scrollytelling *(v2.0)*

**Goal**: Wire the Act II chart component into a new scrollama scene that executes Steps 8–17 from `act2.md`, including the held Step 13 axis transition, and ship the Act II prose alongside the chart in Act I's editorial style.

**UI hint**: yes

**Depends on**: Phase 3 (needs the component). Benefits from Phase 1 (shared editorial tokens/typography) but does not block on it.

**Requirements**: STORY-01, STORY-02, STORY-03, STORY-04, STORY-05, STORY-06

**Success Criteria** (what must be TRUE):
  1. Act II renders as a new scene (separate from Act I's `story-page.vue`) with its own scrollama instance driving the new chart component.
  2. All peer and EU-15 data is pre-loaded at mount (e.g. parallel `useFetch` on each `act2_*.csv` or one composed loader); no per-step fetches.
  3. Scrolling through Steps 8–17 reproduces the narrative beats in `act2.md`: Extremadura fade-in, peer forest, axis switch, Balearic highlight climb across 100, 1990 peak + descent, peers continuing, IB isolated "hinge" close.
  4. The Step 13 axis transition is a visibly held moment — noticeably longer dwell than surrounding steps — during which the EU-15 line flattens into y=100 while peers re-scale.
  5. Prose for Steps 8–17 renders alongside the chart in the same editorial style as Act I (typography, palette, spacing).
  6. `nuxt generate` succeeds and no console errors are thrown during a full scroll from Act I through Act II.

**Plans**: TBD (finalized during `/gsd-plan-phase 4`)

## Current State

**Active Phase**: 2 (v2.0 — next)
**Queued**: Phases 2 → 3 → 4 (v2.0, requirements locked, plans TBD)
**Completed Phases**: Phase 1 (v1.0 D3 chart upgrade)

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| CHART-01 | Phase 1 | Complete |
| CHART-02 | Phase 1 | Complete |
| CHART-03 | Phase 1 | Complete |
| CHART-04 | Phase 1 | Complete |
| CHART-05 | Phase 1 | Complete |
| CHART-06 | Phase 1 | Complete |
| DATA-01  | Phase 2 | Pending |
| DATA-02  | Phase 2 | Pending |
| DATA-03  | Phase 2 | Pending |
| DATA-04  | Phase 2 | Pending |
| DATA-05  | Phase 2 | Pending |
| DATA-06  | Phase 2 | Pending |
| DATA-07  | Phase 2 | Pending |
| DATA-08  | Phase 2 | Pending |
| ACT2-01  | Phase 3 | Pending |
| ACT2-02  | Phase 3 | Pending |
| ACT2-03  | Phase 3 | Pending |
| ACT2-04  | Phase 3 | Pending |
| ACT2-05  | Phase 3 | Pending |
| ACT2-06  | Phase 3 | Pending |
| STORY-01 | Phase 4 | Pending |
| STORY-02 | Phase 4 | Pending |
| STORY-03 | Phase 4 | Pending |
| STORY-04 | Phase 4 | Pending |
| STORY-05 | Phase 4 | Pending |
| STORY-06 | Phase 4 | Pending |

**Coverage:** 26/26 requirements mapped. ✓

---
*Roadmap created: 2026-04-23*
*Updated: 2026-04-23 — Phase 1 executed (3/3 plans); v2.0 (Act II) phases queued*
