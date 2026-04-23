---
phase: 1
slug: d3-chart-upgrade
status: draft
shadcn_initialized: false
preset: none
created: 2026-04-23
---

# Phase 1 — D3 Chart Upgrade — UI Design Contract

> Visual and interaction contract for `app/components/line-chart.vue` only. Sourced from `.planning/REQUIREMENTS.md` (CHART-01–06), `PROJECT.md` Key Decisions, and current implementation. Verified next by gsd-ui-checker.

**Scope note:** Nuxt 4 + Vue 3 + D3 + Tailwind — no shadcn / no new UI component files unless strictly unavoidable (per roadmap). Accessibility improvements remain out of scope (REQUIREMENTS v2 ACCESS-01).

---

## Design System

| Property | Value |
|----------|-------|
| Tool | **none** (Nuxt/SVG/D3; not React/shadcn) |
| Preset | not applicable |
| Component library | **none** (imperative D3 in one SFC) |
| Icon library | **none** (SVG markers only) |
| Font | **DM Mono**, `"DM Mono", "Courier New", monospace` (Google Fonts via `nuxt.config.ts`); match existing axis + tooltip usage |

**Dependencies (this phase):** `d3@^7.9` (existing). **Add** `simplex-noise@^4` (`jwagner/simplex-noise.js`). **Add** `alea@^1` for deterministic PRNG when seeding noise (recommended by simplex-noise 4.x docs; keeps noise stable per memo key). Register new packages in Vite if needed; default is bundled ESM (no `optimizeDeps.exclude` required unless a package misbehaves).

---

## Spacing Scale

Declared 8 pt scale (multiples of 4). Chart-internal measurements use **SVG user units** in `viewBox="0 0 928 400"` unless noted.

| Token | Value | Usage (this phase) |
|-------|-------|--------------------|
| xs | 4px | Tooltip `lineGap` between text lines; minor nudges |
| sm | 8px | Tooltip `padX` / `padY` (8 / 6 per current — padY 6 is exception below) |
| md | 16px | `MARGIN.top` |
| lg | 24px | (Reserved — not used in fixed chart) |
| xl | 32px | — |
| 2xl | 48px | — |
| 3xl | 64px | — |

**Exceptions:** Tooltip vertical padding `padY = 6` (not multiple of 4) — **retain** for visual parity with current `line-chart.vue`; treat as approved micro-adjustment. `MARGIN` values `{ top: 16, right: 30, bottom: 36, left: 80 }` are fixed (already in code).

---

## Typography

| Role | Size | Weight | Line height | Usage |
|------|------|--------|------------|--------|
| Body | 12px | 400 (regular) | 1.2 (implicit single-line) | X-axis tick labels |
| Label | 11px | 400 | 1.2 | Tooltip year + source lines |
| **Value** | 12px | 400 | 1.2 | Tooltip numeric GDP value |
| Display | — | — | — | *Not used in chart* |

**Weights used:** 400 only (no semibold in chart chrome).

---

## Color

| Role | Value | Usage |
|------|-------|--------|
| Dominant (60%) | `#fff1e5` (`tailwind` `cream`) | Page/figure background behind chart |
| Chart “paper” (within SVG) | `#FAF7F0` | Tooltip `fill` (matches current rect); use for highlight-dot stroke “halo” if needed to separate from line |
| Secondary (30%) | `#D6D5D3` (`rule`) | Axis domain, grid clone lines, tooltip border |
| Muted | `#6B6B6B` | Axis tick labels, crosshair (see below) |
| Ink | `#2F2F2F` | Primary tooltip text |
| **Accent (10%)** | `#660000` | **Line stroke, arrowhead fill, series color, highlight dot fill** — single editorial red |

**Accent reserved for:** Series line, terminator arrowhead, source label in tooltip, hover highlight dot — **not** for axes, grid, or crosshair.

| Destructive | *N/A* | No destructive actions in this component. |

**Frozen for milestone:** No changes to palette or font families beyond the above (REQUIREMENTS + PROJECT.md).

---

## Copywriting Contract

| Element | Copy |
|---------|------|
| Primary CTA | *N/A* — scrollytelling has no in-chart CTA. |
| Empty state (no rows after parse / `data.length === 0`) | **No** headline or marketing copy inside SVG. Axes + empty plot only; same as current `update()` early exit (no new strings). |
| Error state | *Out of component scope* — `useFetch` has no custom error UI in v1. **Do not** add toast/modal. |
| Destructive confirmation | *N/A* |

**Tooltip content (unchanged structure):** Year (integer string), `source` (e.g. `RW` / `INE`), formatted GDP with `d3.format(",.0f")` — same as `showTooltip` today.

---

## Registry Safety

| Registry | Blocks Used | Safety Gate |
|----------|-------------|-------------|
| shadcn / ui registries | *none* | not applicable |

---

## Phase 1 — Visual Contract (chart chrome)

| Element | Spec |
|---------|------|
| SVG root | `viewBox="0 0 928 400"`, `preserveAspectRatio="xMidYMid meet"`, `class="block w-full max-w-[1200px] mx-auto max-h-[70vh]"` (unchanged) |
| Line stroke | `#660000`, width **2.5px**, `stroke-linecap="round"`, `stroke-linejoin="round"`, `fill="none"` |
| Y-axis tick text | DM Mono, 12px, fill `#6B6B6B` |
| X-axis (styled) | Same 12px; tick line treatment unchanged (`styleXAxis`) |
| Horizontal grid (tick extension) | `#D6D5D3`, 50% opacity, `stroke-dasharray: 2,4` (existing) |
| Tooltip panel | `fill: #FAF7F0`, `stroke: #D6D5D3`, `rx/ry: 4`, text sizes 11/11/12 as in Typography |
| Crosshair (vertical) | `stroke: #8C8A85` (between `muted` and `rule`; **current implementation**), `stroke-width: 1`, `stroke-dasharray: 2,4`, **no pointer events** |
| **Crosshair extent** | Full plot band: from `y = MARGIN.top` to `y = HEIGHT - MARGIN.bottom` at `x =` hovered year’s x (not only from point downward) |
| **Highlight dot** (hover only) | `r = 4` (SVG units), `fill: #660000`, `stroke: #FAF7F0`, `stroke-width: 1.2` — single dot for nearest year |

---

## Phase 1 — Noise Contract (CHART-04)

| Decision | Spec |
|----------|------|
| Library | `simplex-noise@^4` — `import { createNoise2D } from "simplex-noise"`. **Do not** animate noise amplitude over time in v1. |
| Seeding | `import alea from "alea"`. Use `const noise2D = createNoise2D(alea(SEED))` where `SEED` is a **stable string or number** fixed for the life of a chart build (e.g. `"balearic-gdp-ib"` or hash of `xMin-xMax` + `data` revision). **No** per-frame or `requestAnimationFrame` seed drift. |
| Sampling | For each data point in drawing order, sample `yOffset = noise2D(nx, ny) * AMPLITUDE` where `nx = x / X_FREQ` (x in **data space** or **SVG x**—pick one and apply consistently) and `ny` = constant **0** or `source` index (0/1) to decorrelate series if two paths exist. **Lock:** `nx = year / 40` (trend-scale along x) and `ny = 0` for a single path; for two segments, use `ny ∈ {0, 0.1}` to keep coherence. **Amplitude scale:** **±4px maximum** in SVG y (map noise ∈ [-1,1] to [-4, 4] before adding to `yScale(gdp_pc)`). |
| Frequency / scale | **X_FREQ** in “years per cycle” sense: use divisor **40** on **year** so noise varies slowly across the century (readable trend). If line appears too wiggly, reduce amplitude to **3px** before touching frequency. |
| Trend preservation | Displace **perpendicular in screen space** by adding offset to the **y** coordinate after `yScale` (not to raw GDP), so domain stays honest. |
| Jitter rule | **Never** re-roll noise in `d3.tween` on each frame; recompute only when `props.data` or `props.xDomain` / `yDomain` (re-init path) changes. |

**Memoization (performance):** Cache an array of `y` offsets or final `x,y` points keyed by `JSON.stringify(xDomain) + data fingerprint + SEED` so transitions do not recompute simplex for every `tick`. Recompute the path string when the key changes.

---

## Phase 1 — Animation Contract (CHART-06)

| Decision | Spec |
|----------|------|
| Technique | **stroke-dasharray / stroke-dashoffset** on the visible line `<path class="series-line">` (D3 7: `getTotalLength()` on the same path in the DOM) |
| Duration | **800 ms** — constant `DURATION` (keep existing) |
| Easing | `d3.easeCubicInOut` — same as axis transitions |
| Triggers | (1) Initial mount after first successful draw, (2) every `update(true)` from prop watch (scrollama step / domain change) |
| **Noise + draw order** | Build **one** `d` string that **already includes** noise displacements, then apply dash offset animation. **Do not** animate a clean line and blend noise in afterward. |
| On re-run | If `xScale` or path geometry changes, **recompute** total length, reset `stroke-dasharray` to `${length} ${length}`, animate `stroke-dashoffset` from `length` → `0`. |

---

## Phase 1 — Interaction Contract (CHART-02, CHART-03)

| Decision | Spec |
|----------|------|
| Hit target | One **transparent** `<rect>` (or the plot `<g>`) covering the inner plot: `x: MARGIN.left` → `WIDTH - MARGIN.right`, `y: MARGIN.top` → `HEIGHT - MARGIN.bottom`, `fill: transparent` (or `pointer-events: all` on a captured layer), `cursor: crosshair` (optional, CSS on SVG) |
| Pointer events | **Remove** per-circle `mouseenter` / `mousemove` / `mouseleave` from data-point circles. Circles are either not joined or `display: none` / `r=0` / not rendered. |
| Nearest year | Invert `xScale` to get a `Date` from `pointer` x; convert to year number; `d3.bisector((d: GdpDataPoint) => d.year).center(sortedByYear, yearFloat)` (D3 7: **bisector.center** returns index of closest value). If multiple `GdpDataPoint` share a year, pick the **last** in source order (INE after RW) or the single series row — data model should be one per year; if duplicate years exist, disambiguate with `sourceOrder` **after** index pick. |
| Crosshair + tooltip + dot | `showTooltip(chosenPoint)` with **same** three-layer behavior as now, with crosshair and dot positions matching **the chosen** datum. |
| Leave plot | `mouseleave` on overlay (or `pointerleave`) → `hideTooltip()`; hide crosshair, tooltip, and highlight dot. |
| Tooltip clamping | Retain `tx` / `ty` clamping to **inner plot** bounds (`MARGIN` insets) as today; do not allow tooltip to overlap axis labels if avoidable. |

**Reference (Context7 / D3 7):** `d3.pointers(event, target)` for coordinates relative to SVG; `d3.bisector(accessor).center(array, x)` for closest index.

---

## Phase 1 — Arrowhead Contract (CHART-05)

| Decision | Spec |
|----------|------|
| Mechanism | Native SVG **`<marker>`** in `<defs>`, referenced via `marker-end="url(#series-arrow)"` on the **line path that represents the most recent year** (the “active” or topmost series in draw order, same color as line). |
| Shape | **Filled triangle** (editorial, matches scroll-arrow pattern in `story-page.vue` but sized for 2.5px stroke) — **not** a stroked open chevron |
| `orient` | `auto-start-reverse` (same as `scroll-arrow-head`) so the tip points along the end tangent |
| Colors | `fill: #660000`, `stroke: none` (line cap handles continuity; head reads as part of the stroke) |
| Sizing (user units) | `viewBox="0 0 10 10"`, `refX="9"` `refY="5"` (tip at right), `markerWidth="8"` `markerHeight="8"` (tune 7–8 if needed for crispness) |
| Path | `d="M0 0 L0 10 L9 5 Z"` (or equivalent isosceles) |
| **Placement** | Marker on the **end of the line path** that ends at the latest visible year; when dash animation runs, the marker is visible at the **end of the path** and must move with the path’s terminal. Coordinate with `stroke-dashoffset` so the arrow **appears at the growing tip** (may require `marker-end` on a separate short segment or last segment — if implementationally simpler, add a tiny **no-dash** tail segment; if not, document in PLAN as implementation detail, but **end state** must show arrow at 2024 / `xMax` end). **Executor:** Prefer single path + dash animation; if marker does not track dash tip, add **overlay arrowhead** at last point position updated in `update()` — not preferred but acceptable with UI-checker sign-off. |

---

## Phase 1 — Responsiveness & Performance

| Rule | Spec |
|------|------|
| Viewport | `max-h-[70vh]` + `w-full` — unchanged; chart scales uniformly via viewBox |
| `nuxt generate` | Must succeed; no `console.error` in normal scroll/hover (REQUIREMENTS success criterion 6) |
| Noise | Memoize as in Noise Contract; no `getTotalLength` or `noise2D` in a `rAF` loop |
| d3 / Vite | Keep `d3` in `optimizeDeps.exclude` (`nuxt.config.ts`) |

---

## Phase 1 — Accessibility

| Note | Text |
|------|------|
| Scope | **Out of v1** per PROJECT.md: no `role`, `aria-label`, or keyboard focus for tooltip (deferred ACCESS-01). |
| **Do not** | Block future a11y with `aria-hidden` on the whole chart; leaving SVG as-is (neutral) is acceptable. |

---

## Traceability

| ID | UI contract |
|----|-------------|
| CHART-01 | No visible point circles in default; highlight dot only on hover (Section Visual + Interaction) |
| CHART-02 | Plot overlay, bisector.center, one datum (Interaction) |
| CHART-03 | pointer leave hides all hover UI |
| CHART-04 | simplex-noise, amplitude ±4px, slow x-scale, no temporal jitter (Noise) |
| CHART-05 | SVG marker, filled triangle `#660000` (Arrowhead) |
| CHART-06 | dash animation 800ms cubic in-out, noise in path, mount + step (Animation) |

---

## Checker Sign-Off

- [ ] Dimension 1 Copywriting: PASS
- [ ] Dimension 2 Visuals: PASS
- [ ] Dimension 3 Color: PASS
- [ ] Dimension 4 Typography: PASS
- [ ] Dimension 5 Spacing: PASS
- [ ] Dimension 6 Registry Safety: PASS

**Approval:** pending
