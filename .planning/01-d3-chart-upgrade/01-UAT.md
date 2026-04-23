---
status: complete
phase: 01-d3-chart-upgrade
source:
  - 01-01-SUMMARY.md
  - 01-02-SUMMARY.md
  - 01-03-SUMMARY.md
started: "2026-04-23T00:00:00.000Z"
updated: "2026-04-23T12:30:00.000Z"
---

## Current Test

[testing complete]

## Tests

### 1. Points hidden by default
expected: Load the chart at any scroll step. No per-year data-point circles should be visible on the line. The line itself is the only mark — no dots along the path.
result: pass

### 2. Perlin noise line distortion
expected: The line path deviates subtly from a perfectly straight interpolation between data years. The deviation should look organic / hand-drawn (smooth, spatially coherent wiggles), not random jitter between adjacent pixels.
result: pass

### 3. Arrowhead at end of line
expected: An arrowhead chevron is visible at the right end of the line (the most recent year). It should be styled consistently with the line (same dark-red color, similar stroke weight) and point in the direction of the line at its tip.
result: pass

### 4. Nearest-x tooltip on hover
expected: Moving the cursor horizontally over the chart plot area shows a tooltip for the year closest to the cursor's x-position. The tooltip shows year, data source, and GDP per capita value. A small filled dot appears on the line at that year.
result: pass

### 5. Full-height crosshair on hover
expected: When hovering over the chart, a dashed vertical crosshair line spans the full height of the plot area at the hovered year's x-position.
result: issue
reported: "yes, but this isn't what I wanted, the line should go from the data point downwards (no upwards)"
severity: minor

### 6. Tooltip clears on mouse leave
expected: Moving the cursor off the chart plot area (not just off a data point, but off the whole chart rectangle) hides the tooltip, the crosshair line, and the highlight dot completely.
result: pass

### 7. Line grow animation on scroll step change
expected: When scrolling to a new step that extends the visible year range, the line animates as if being drawn progressively from the previous endpoint to the new one — not a fade or an instant redraw. When scrolling backward to a step with fewer years, the line erases from the right.
result: pass

### 8. Build passes
expected: `nuxt generate` completes with exit code 0 and no console errors related to the chart component.
result: pass

## Summary

total: 8
passed: 7
issues: 1
pending: 0
skipped: 0

## Gaps

- truth: "The crosshair line should run from the hovered data point's y-position downward to the bottom of the plot area only (not upward to the top)"
  status: failed
  reason: "User reported: yes, but this isn't what I wanted, the line should go from the data point downwards (no upwards)"
  severity: minor
  test: 5
  artifacts: []
  missing: []
