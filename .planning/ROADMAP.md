# Roadmap: IB GDP Evolution

## Overview

Milestone 1 focuses on upgrading the D3 line chart in `app/components/line-chart.vue` with editorial, animated, and organic enhancements: hidden points, nearest-x bisect tooltip, Perlin-noise line distortion, smooth grow animation, and arrowhead terminator. All 6 v1 requirements fall into one cohesive phase because they touch the same component and the same D3 update cycle.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

- [ ] **Phase 1: D3 Chart Upgrade** — Hide points, nearest-x tooltip, Perlin-noise line, grow animation, arrowhead

## Phase Details

### Phase 1: D3 Chart Upgrade

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

**Plans**: TBD (planner decides; expected 1–3 plans)

Plans:
- [ ] 01-01: TBD (populated by `/gsd-plan-phase 1`)

## Current State

**Active Phase**: 1
**Completed Phases**: None

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| CHART-01 | Phase 1 | Pending |
| CHART-02 | Phase 1 | Pending |
| CHART-03 | Phase 1 | Pending |
| CHART-04 | Phase 1 | Pending |
| CHART-05 | Phase 1 | Pending |
| CHART-06 | Phase 1 | Pending |

**Coverage:** 6/6 requirements mapped. ✓

---
*Roadmap created: 2026-04-23*
