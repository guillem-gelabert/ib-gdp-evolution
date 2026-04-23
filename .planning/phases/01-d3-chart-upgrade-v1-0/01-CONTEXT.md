# Phase 1: D3 Chart Upgrade *(v1.0)* - Context

**Gathered:** 2026-04-23
**Status:** Ready for planning

<domain>
## Phase Boundary

Transform `app/components/line-chart.vue` into an editorial, organic, animated line chart by implementing hidden default points, nearest-x interaction, coherent line distortion, draw-on-enter animation, and an endpoint arrowhead without breaking static generation.

</domain>

<decisions>
## Implementation Decisions

### Interaction Model
- Use a dedicated transparent plot overlay for pointer capture and nearest-x lookup.
- Hover highlights exactly one nearest-year point and draws a full-height vertical crosshair.
- On pointer leave, clear crosshair, highlighted point, and tooltip.

### Organic Line Styling
- Apply deterministic Perlin/simplex-style distortion keyed by source and year so the curve stays stable across re-renders.
- Keep distortion subtle and spatially coherent to preserve data readability while avoiding a rigid straight interpolation feel.

### Motion
- Animate line reveal with `stroke-dasharray`/`stroke-dashoffset` using an 800ms transition.
- Trigger reveal on initial mount and on scroll-driven range updates that call chart update transitions.

### Visual Endcap
- Define SVG marker arrowheads once in `<defs>` and attach via `marker-end` to the terminal segment.
- Keep arrowhead color and stroke style tied to the source line styling tokens.

### Claude's Discretion
Fine-tune hover hit-testing tolerance, distortion amplitude/frequency constants, and transition timing details as needed to satisfy smoothness and readability constraints while preserving all success criteria.

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- `app/components/line-chart.vue` already contains the full D3 initialize/update lifecycle, typed `GdpDataPoint`, axis styling helper, and tooltip plumbing.
- `app/components/story-page.vue` already controls scroll-step data slices and domains, so chart updates can remain prop-driven.

### Established Patterns
- D3 state is module-scoped in `line-chart.vue`, initialized once and updated via `update(animate)`.
- Styling uses shared constants/maps (`LINE_COLOR`, `sourceColors`, `sourceOrder`) and Tailwind handles page-level visual styling.
- Guards and defaults favor early returns and null-safe handling.

### Integration Points
- Implement all Phase 1 behavior inside `app/components/line-chart.vue` watchers/initialize/update flow.
- Keep `story-page.vue` API contract unchanged: data + domain props drive re-render/animation.
- Validate with `nuxt generate` and interactive pointer behavior on the chart scene.

</code_context>

<specifics>
## Specific Ideas

No additional bespoke requirements beyond the approved defaults and roadmap success criteria.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>
