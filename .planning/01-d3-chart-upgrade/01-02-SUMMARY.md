# Plan 01-02 — Summary

**Status:** Done  
**Date:** 2026-04-23

## Done

- Transparent plot `<rect>` overlay with `pointermove` / `pointerleave`.
- `d3.pointers` + `xScale.invert` → fractional year + `d3.bisector((d) => d.year).center` on **one point per calendar year** (last source wins when RW+INE share a year).
- Full-height crosshair (`MARGIN.top` → `HEIGHT - MARGIN.bottom`), highlight dot `r=4` at noised `(px, yNoise)`.
- `hideTooltip` clears tooltip, crosshair, and highlight dot.
- Removed all per-circle mouse handlers.

## Notes

- DOM order: lines → points → hover line → highlight → **plot overlay** → tooltip (tooltip on top, `pointer-events: none`).
