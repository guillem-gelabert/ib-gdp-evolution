# Requirements: IB GDP Evolution

**Defined:** 2026-04-23
**Core Value:** Present the 125-year GDP-per-capita story as a beautiful, editorial, animated chart that communicates the long-arc transformation at a glance.

## v1 Requirements (Act I — chart upgrade, Phase 1)

Requirements for milestone v1.0: D3 chart visual enhancements on `app/components/line-chart.vue`.

### Chart Interaction

- [x] **CHART-01**: Data-point circles are hidden in the default rendered state (the line is the only visible mark).
- [x] **CHART-02**: When the cursor is over the chart plot area, a single point + tooltip + crosshair are shown for the datum whose year is horizontally closest to the cursor's x-position (nearest-x bisect, not per-circle hover), and moving off the plot clears hover affordances.

### Chart Aesthetics

- [x] **CHART-03**: The line path is displaced with simplex/Perlin-style noise so it reads as hand-drawn/organic, while preserving the overall trend (seeded, bounded, spatially coherent — not per-frame random jitter).
- [x] **CHART-04**: On initial mount and on forward scrollama updates, the line animates as if being drawn (stroke-dash reveal, default **800ms** for the standard path; wide domain-zoom / backward-erase use longer or speed-based timings).

### Chart Animation & Ship

- [x] **CHART-05**: An arrowhead is drawn at the end of the main series (most recent year), sized and colored consistently with the line (SVG `marker` + `marker-end`).
- [x] **CHART-06**: `nuxt generate` succeeds; no `console.*` in `line-chart.vue` (browser scroll/console smoke recommended for UAT; see phase verification).

## v2 Requirements (Act II — "Who Else Got Richer")

Requirements for milestone v2.0. Source narrative: `act2.md`. Decisions log: `.planning/notes/act2-datastory-decisions.md`.

### Data Pipeline

- [ ] **DATA-01**: `scripts/extend_gdp.py` supports configurable `ANCHOR_YEAR` (default 2020).
- [ ] **DATA-02**: Pipeline accepts non-NUTS2 series identifiers alongside NUTS2 (country ISO codes for IE/PT/MT; INE codes for Spanish regions).
- [ ] **DATA-03**: Pipeline produces chain-linked per-capita GDP series for Extremadura, Galicia, and Castilla-La Mancha (RW 1900–1999 + INE 2000+), passing all existing sanity checks.
- [ ] **DATA-04**: Pipeline produces chain-linked per-capita GDP series for Portugal, Ireland, and Malta (RW 1900–1999 + Eurostat CLV 2000+), passing all existing sanity checks.
- [ ] **DATA-05**: The IB series is regenerated on the 2020 anchor, replacing the 2022-anchor artifact, with seam continuity verified at the anchor year.
- [ ] **DATA-06**: Pipeline produces an EU-15 reference series computed as a GDP-weighted per-capita average across the 15 member countries (RW-derived 1900–1999 + Eurostat EU-15 aggregate 2000+).
- [ ] **DATA-07**: All generated series pass the existing sanity checks (seam continuity, growth preservation, no missing years, outlier guard, level plausibility, CLV unit guard).
- [ ] **DATA-08**: Pipeline emits a single tidy CSV (`series, year, value, unit, source`) consumable directly by the Act II chart component.

### Act II Chart Component

- [ ] **ACT2-01**: A new Vue component renders N peer lines + the IB line + the EU-15 reference from the combined Act II CSV.
- [ ] **ACT2-02**: The component supports two axis modes — `real-eur` (GDP per capita, real €) and `pct-eu15` (% of EU-15 average, EU-15 = 100) — selected via a prop.
- [ ] **ACT2-03**: Transitioning from `real-eur` to `pct-eu15` is an animated tween in which the EU-15 line morphs/flattens to the y=100 baseline while all other lines re-scale in the same tween (held moment, longer duration than surrounding transitions).
- [ ] **ACT2-04**: Per-line visual state (active-color, faded-gray, hidden, highlighted) is controlled via step-driven props, with independent transitions per line.
- [ ] **ACT2-05**: The component reuses Act I's visual language (Perlin-noise line distortion, arrowhead terminator, editorial palette) via shared utilities extracted where practical.
- [ ] **ACT2-06**: Chart annotations (shaded "peak" band for IB ~1990, horizontal y=100 reference line) are rendered as first-class, data-driven primitives.

### Scrollytelling (Act II)

- [ ] **STORY-01**: Act II renders as a new scrollytelling scene (separate from Act I's `story-page.vue`), with its own scrollama container driving the new chart component.
- [ ] **STORY-02**: All Act II data (IB + peers + EU-15) is pre-loaded on component mount via a single static fetch; no lazy-loading per step.
- [ ] **STORY-03**: Scrollama steps 8–17 from `act2.md` drive chart state — active line set, highlighted line, axis mode, annotations — with the per-step semantics specified in the narrative.
- [ ] **STORY-04**: The Step 13 axis transition dwells longer than surrounding steps (held moment, per `act2.md` craft notes).
- [ ] **STORY-05**: Step prose from `act2.md` renders alongside chart steps in the editorial style established in Act I (typography, spacing, palette).
- [ ] **STORY-06**: `nuxt generate` continues to succeed and no console errors are thrown during Act II scrollytelling interaction.

## Deferred (future milestones)

- **ACCESS-01**: SVG accessibility (`role`, `aria-label`, keyboard focus for tooltip) — deferred (see `.planning/codebase/CONCERNS.md`).
- **ACT3-01**: Act III "Why the fall" — explanatory narrative layer. Out of v2.0 scope per `act2.md` craft notes.
- **TOGGLE-01**: User-driven axis toggle (button to switch real € ↔ % of EU-15 outside of scroll choreography) — deferred.

## Out of Scope

| Feature | Reason |
|---------|--------|
| Adding/keeping visible circles | Cleaner editorial aesthetic without per-year dots (v1.0) |
| Per-point hover events on Act I circles | Replaced by nearest-x bisect on the plot area (v1.0) |
| Changing color palette / fonts | Editorial style is frozen; peer lines use muted/gray variants of the Act I palette (v2.0) |
| Adding unit / E2E tests | No test infra exists; not worth introducing for a visual/narrative build |
| Server-side data API | Static CSV via `useFetch` remains sufficient for Act II |
| User-driven axis toggle | Axis switch is scroll-choreographed only; no UI control (v2.0) |
| Explanation of IB's post-1990 drift | Act II ends on the observation per `act2.md` craft notes; "why" is Act III |
| Membership-date-aware EU-15 composition | EU-15 composition held constant across 1900–2024 as an analytical benchmark |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

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

**Coverage:**
- v1 requirements: 6 total, mapped to 1 phase (Phase 1)
- v2 requirements: 20 total, mapped to 3 phases (Phase 2 / 3 / 4)
- Unmapped: 0 ✓

---
*Requirements defined: 2026-04-23*
*Last updated: 2026-04-23 — Phase 1 (CHART-01..06) marked complete*
