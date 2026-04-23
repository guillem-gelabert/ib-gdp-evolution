# Plan 01-01 — Summary

**Status:** Done  
**Date:** 2026-04-23

## Done

- Added `simplex-noise@^4` and `alea@^1` to `package.json` / lockfile.
- `MARGIN.right = 32`, tooltip `padY = 8`.
- Memoized `simplex-noise` offsets per `(x domain, y domain, data fingerprint, seed)`; `noise2D(year/40, ny)` with `ny` 0 / 0.1 for INE vs RW.
- SVG `<defs>` marker `#series-arrow` + `marker-end` on each `path.series-line`.
- Data circles `r = 0`, `pointer-events: none` (hover deferred to 01-02).

## Notes

- Line path includes vertical noise in **screen y** after `yScale(gdp_pc)`.
