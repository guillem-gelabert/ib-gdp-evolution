---
phase: 01-d3-chart-upgrade-v1-0
plan: 01-03
subsystem: chart
tags: [animation, ssg]
requires: [01-02]
provides: [CHART-04, CHART-06]
---

# Phase 1 Plan 01-03: 800ms reveal + static generation — Summary

**One-liner:** Standard forward line grow uses constant `REVEAL_MS = 800` with `d3.easeCubicInOut`; x-axis transition matches `axisDuration` from the same `update()` branch; `pnpm run generate` passes; no `console.*` in `line-chart.vue`.

## Durations (code branches)

| Branch | Line | Axis | Notes |
|--------|------|------|--------|
| Forward grow / mount (`applyLineGrow` with `runAnimation`) | **800ms** | **800ms** (`axisDuration` return) | `REVEAL_MS` |
| Domain width change (`domainChanged`) | 2000ms tween | 2000ms | `MAX_DURATION` (wide zoom) |
| Backward erase (`dataShrunk`) | `min(MAX, max(MIN, delta/LINE_SPEED))` | same | Speed-based erase |
| `update(false)` | 0 | 0 | Instant |

## Verification

- `pnpm run build` — PASS (2026-04-23).
- `pnpm run generate` — PASS; output under `.output/public`.

## Plan 01-03 Task 3 (human browser smoke)

**Status:** **PENDING HUMAN** — Executor did not run an interactive browser session. Recommended: `pnpm dev`, open `/`, devtools Console, full Act I scroll + chart hover; expect no red errors. Not a code blocker for SSG.

## Deviations from Plan

None for automated tasks.

## Self-Check: PASSED (automated); human UAT outstanding
