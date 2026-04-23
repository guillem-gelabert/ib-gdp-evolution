# Plan 01-03 — Summary

**Status:** Done  
**Date:** 2026-04-23

## Done

- `applyLineGrow`: `getTotalLength()`, `stroke-dasharray` / `stroke-dashoffset`, 800 ms `d3.easeCubicInOut`, on every `update(animate)` after `d` is set.
- No noise or `getTotalLength` inside transition tweens except the single length read on the built path.

## Verification

- `pnpm run build` — exit 0  
- `pnpm run generate` — exit 0  

## Marker vs. dash (UAT)

Native `marker-end` stays at the **subpath end** while `stroke-dashoffset` animates. The arrowhead can read as “full length” before the stroke finishes. A one-line comment in `line-chart.vue` points to UI-SPEC fallback (overlay head at noised `xMax`) if product wants the tip to track the animating end.
