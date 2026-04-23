---
phase: 01-d3-chart-upgrade-v1-0
plan: 01-02
subsystem: chart
tags: [d3, bisect, hover]
requires: [01-01]
provides: [CHART-02]
---

# Phase 1 Plan 01-02: Nearest-x interaction — Summary

**One-liner:** Plot overlay drives `d3.bisector(...).center` on deduped years with x-range clamping, full-height vertical rule, single highlight dot + tooltip, and `pointerleave` / `pointercancel` clearing hover.

## Completed

- **Crosshair:** `hoverLine` spans `y = MARGIN.top` to `y = HEIGHT - MARGIN.bottom` (full plot height).
- **Bisect:** `mx` clamped to `[xScale(minYear), xScale(maxYear)]` before invert; `yearBisect(forBisect, yearFloat)` index used directly (no erroneous `Math.round` on the index).
- **Leave:** `hideTooltip()` clears crosshair, highlight, and tooltip; overlay keeps `pointer-events: all`.

## Verification

- `pnpm run build` — PASS (2026-04-23).

## Deviations from Plan

None.

## Self-Check: PASSED
