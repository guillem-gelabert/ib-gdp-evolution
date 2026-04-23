---
phase: 01-d3-chart-upgrade-v1-0
plan: 01-01
subsystem: chart
tags: [d3, svg, simplex, marker]
requires: []
provides: [CHART-01, CHART-03, CHART-05]
---

# Phase 1 Plan 01-01: Editorial defaults + marker endcap — Summary

**One-liner:** Default hidden year dots, deterministic simplex resampling between anchors, and `#660000` SVG `marker` endcap on the main series via `marker-end`, removing the old free-form arrow path.

## Completed

- **CHART-01:** Circles use `r = 0` when `showAllPoints` is false (default); optional visible points only via noise dev panel.
- **CHART-03:** `simplex-noise` + `alea` seed; `ensureNoiseCache` / `buildNoiseKey` unchanged; no extra work in pointer handlers.
- **CHART-05:** `<defs><marker id="line-arrow-cap">` with filled path; primary `path.series-line` uses `marker-end` after static or post-tween state; marker hidden during dash animations so the cap does not sit at the wrong vertex.

## Verification

- `pnpm run build` — PASS (2026-04-23).

## Deviations from Plan

### TDD (Task 2)

The project has no test runner (`package.json` has no `test` script). **Behavior** (stable noise for the same seed + keys) is enforced by `createNoise2D(alea(seed))` and `buildNoiseKey` in code. No separate RED/GREEN test file added.

## Self-Check: PASSED

- `app/components/line-chart.vue` updated; build green.
