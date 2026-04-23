# Architecture

**Analysis Date:** 2026-04-23

## Pattern Overview

**Overall:** Nuxt 4 single-page scrollytelling site with a Python ETL sidecar.

**Key Characteristics:**
- Nuxt 4 app (`nuxt ^4.4.2`, Vue 3.5, Vue Router) using file-based routing with a single page (`app/pages/index.vue`) mounted through `<NuxtPage />` in `app/app.vue`.
- Client-rendered data visualization: a long-form narrative page (`app/components/story-page.vue`) scrolls through D3-rendered line-chart steps (`app/components/line-chart.vue`) driven by `scrollama`.
- Static data lives under `public/data/*.csv` and is consumed in-browser via `useFetch` + `d3.csvParse`; no server API layer.
- Data preparation is decoupled: a standalone Python pipeline (`scripts/extend_gdp.py`) chain-links Rosés-Wolf (1900–1999) with Eurostat/INE real-growth (2000–2024) outputs to produce the CSVs consumed by the front end.
- Styling via Tailwind (`@nuxtjs/tailwindcss` + `tailwind.config.ts`) with a custom editorial color/typography theme; no component library.
- No backend, no auth, no database — pure static/SSG-capable Nuxt project (`nuxt generate` available in `package.json`).

## Layers

**Entry layer (Nuxt shell):**
- Purpose: Mount the router and provide global `<head>` (fonts).
- Location: `app/app.vue`, `nuxt.config.ts`
- Contains: `<NuxtPage />`, Google Fonts preconnect/stylesheet links, Tailwind + ESLint module registration, `vite.optimizeDeps.exclude: ["d3"]`.
- Depends on: `@nuxt/eslint`, `@nuxtjs/tailwindcss`.
- Used by: The Nuxt runtime (build/dev).

**Page layer:**
- Purpose: File-based route producing the single URL `/`.
- Location: `app/pages/index.vue`
- Contains: A thin wrapper that renders `<story-page />`.
- Depends on: `app/components/story-page.vue` (auto-imported by Nuxt).
- Used by: `<NuxtPage />` in `app/app.vue`.

**Narrative / orchestrator component:**
- Purpose: Owns the scrollytelling UX — hero, intro prose, scroll-driven chart figure, outro, data-methods, footer.
- Location: `app/components/story-page.vue`
- Contains: Step definitions (`steps` array of `{ body, from, to, xMax }`), data fetch (`useFetch("/data/balearic_gdp_pc.csv", { server: false })`), D3 CSV parsing, computed `sliced`/`xDomain`/`yDomain`, `scrollama` setup, scroll-arrow sticky calculation, Tailwind markup, inline SVG `<filter id="shadow">` reused by steps.
- Depends on: `scrollama`, `d3` (`csvParse`, `extent`), `./line-chart.vue` (type import `GdpDataPoint`).
- Used by: `app/pages/index.vue`.

**Visualization component:**
- Purpose: Render and animate the GDP-per-capita line chart in SVG.
- Location: `app/components/line-chart.vue`
- Contains: Exports `interface GdpDataPoint`; imperative D3 pipeline (`initialize` / `update`) for scales, axes, lines, points, hover tooltip; transitions via `d3.transition().duration(800).ease(d3.easeCubicInOut)`; per-source styling maps (`sourceColors`, `sourceOrder`, `pointRadius`).
- Depends on: `d3` (namespace import).
- Used by: `app/components/story-page.vue` via `<line-chart :data :y-domain :x-domain />`.

**Static data layer:**
- Purpose: Serve preprocessed CSVs to the browser.
- Location: `public/data/`
- Contains: `balearic_gdp_pc.csv` (spliced series consumed by the app), plus supporting/intermediate tables `balearic_ine_chainlinked_gdp_pc.csv`, `balearic_ine_gdp_pc_datalake.csv`, `roses_wolf_selected_comparison.csv`.
- Depends on: Nothing at runtime.
- Used by: `story-page.vue` via `useFetch`.

**Data pipeline (offline):**
- Purpose: Produce the public CSVs from Rosés-Wolf + Eurostat/INE inputs with sanity checks.
- Location: `scripts/extend_gdp.py`
- Contains: Loaders for Rosés-Wolf and Eurostat, NUTS correspondence resolution, chain-linking at a 2022 anchor, seam/growth/coverage/outlier/level checks, CSV + text-report output.
- Depends on: `pandas` (external Python environment, not in `package.json`).
- Used by: Operated manually by the developer; not invoked by the Nuxt runtime.

## Data Flow

**Runtime narrative render:**

1. Nuxt boots `app/app.vue`; `<NuxtPage />` resolves to `app/pages/index.vue`, which renders `<story-page />`.
2. `story-page.vue` calls `useFetch("/data/balearic_gdp_pc.csv", { server: false })` — the CSV is fetched client-side from `public/data/`.
3. The raw CSV string is parsed by `d3.csvParse` and coerced into `GdpDataPoint[]` (year, gdp_pc, source, unit), filtered for NaNs and sorted by year in the `parsed` computed.
4. `yDomain` is computed from `d3.extent` over the full series (stable axis); `sliced` and `xDomain` are recomputed from the current `activeStep`.
5. On mount, `scrollama().setup({ step, offset: 0.5 }).onStepEnter(...)` updates `activeStep.value` as the user scrolls through the `.step` elements inside `<article>`.
6. Each change of `props.data` / `props.xDomain` triggers `watch` in `line-chart.vue`, which re-runs D3 enter/update/exit joins for paths and circles with an 800 ms cubic ease-in-out transition.

**Hover interaction:**

1. Circles have `mouseenter` / `mousemove` / `mouseleave` handlers bound in `update()` that call `showTooltip(d)` / `hideTooltip()`.
2. `showTooltip` measures tooltip text via `getBBox()`, positions an SVG `<g>` and a dashed hover line at the hovered year/value, and clamps to the chart margins.

**Offline data flow (Python):**

1. `scripts/extend_gdp.py` resolves Rosés-Wolf and Eurostat inputs (`data/` or `public/data/`) and an optional NUTS correspondence file.
2. Eurostat is unit-guarded (must be CLV chain-linked; CP/PPS rejected), filtered to `na_item=B1GQ` when present, melted to long format, and restricted to 2000–2024.
3. For each Rosés-Wolf region it chains `gdp_pc_2011ppp = rw_anchor * (euro_t / euro_anchor)` at `ANCHOR_YEAR=2022`, prefixes 1900–1999 Rosés-Wolf values, runs seven sanity checks, and writes `output/gdp_per_capita_extended.csv` plus `output/sanity_report.txt`.
4. The Nuxt-facing CSV (`public/data/balearic_gdp_pc.csv`) is produced/curated from this pipeline (spliced single-region series with `source ∈ {RW, INE}`).

**State Management:**
- Component-local Vue refs only (`activeStep`, `scrollArrowHeight`, etc.) in `story-page.vue`.
- No Pinia, no Vuex, no Nuxt state composables.
- Mutable D3 selections are held in module-scope `let` bindings inside `line-chart.vue`'s `<script setup>` (`xScale`, `yScale`, `linesG`, `pointsG`, `tooltipG`, …) and reset by `initialize()`.

## Key Abstractions

**`GdpDataPoint` (data contract):**
- Purpose: Single row of the plotted GDP-per-capita series.
- Examples: `app/components/line-chart.vue` (exports interface), `app/components/story-page.vue` (type import).
- Pattern: Exported TypeScript `interface` co-located with the consumer component; imported via a Vue SFC type import (`import type { GdpDataPoint } from "./line-chart.vue"`).

**Scrollytelling step:**
- Purpose: Narrative beat that controls the chart window.
- Examples: `steps` array in `app/components/story-page.vue` (literal `{ body, from, to, xMax }`).
- Pattern: Plain inline data array indexed by `activeStep`; no separate config file.

**D3 imperative update loop:**
- Purpose: Keep SVG in sync with reactive props.
- Examples: `initialize()` / `update(animate)` in `app/components/line-chart.vue`, driven by `watch([() => props.data, () => props.xDomain], …)`.
- Pattern: Enter/update/exit joins with key functions (`d => d.source` for series paths, `` `${d.source}-${d.year}` `` for points).

**Per-source styling maps:**
- Purpose: Differentiate Rosés-Wolf (`RW`) vs INE (`INE`) marks.
- Examples: `sourceColors`, `sourceOrder`, `pointRadius`, `sourceWidth` in `app/components/line-chart.vue`.
- Pattern: `Map<string, …>` / pure functions keyed on `d.source`.

## Entry Points

**Nuxt root:**
- Location: `app/app.vue`
- Triggers: Nuxt runtime on any route.
- Responsibilities: Render `<NuxtPage />`.

**Home route:**
- Location: `app/pages/index.vue`
- Triggers: Navigation to `/` (the only route).
- Responsibilities: Render `<story-page />`.

**Nuxt configuration:**
- Location: `nuxt.config.ts`
- Triggers: Build/dev server startup.
- Responsibilities: Register `@nuxt/eslint` and `@nuxtjs/tailwindcss`, inject Google Fonts `<link>` tags, set `vite.optimizeDeps.exclude: ["d3"]`, `compatibilityDate: "2025-07-15"`.

**ESLint entry:**
- Location: `eslint.config.mjs`
- Triggers: `eslint` invocations.
- Responsibilities: Re-export `withNuxt()` from `.nuxt/eslint.config.mjs`.

**Data pipeline CLI:**
- Location: `scripts/extend_gdp.py`
- Triggers: `python scripts/extend_gdp.py [--workspace ... --rw-path ... --eurostat-path ... --output-csv ...]`.
- Responsibilities: Produce chain-linked GDP CSV + sanity report.

## Error Handling

**Strategy:** Minimal defensive guards at the boundaries; no global error handler.

**Patterns:**
- Front end: `parsed` computed returns `[]` when `gdpCsv.value` is not a string and filters out NaN years/values before plotting; `sliced` / `xDomain` / `yDomain` return safe defaults (`[]`, `[1900, 1990]`, `[0, 1]`) when the data or step is missing; `line-chart.vue` short-circuits `update()` with `if (!ready) return` and clears paths/points on empty data.
- Hover positioning clamps tooltip `tx` / `ty` within `MARGIN` bounds to avoid overflow.
- Data pipeline: Custom `PipelineError` raised on missing inputs, failed Eurostat unit guard (`CLV` required, `CP` / `PPS` rejected), empty datasets, or failed seam-continuity check; `main()` catches it and exits non-zero with `raise SystemExit(f"ERROR: {exc}")`.

## Cross-Cutting Concerns

**Logging:** None in the Nuxt code. The Python pipeline prints one-line check summaries and output paths via `print_summary` / `print`.

**Validation:** Purely structural in the front end (`Number.isNaN` filters, type import). The pipeline enforces Eurostat unit constraints, anchor-year presence, and seam continuity within 1e-6.

**Authentication:** Not applicable (static site, public CSVs).

**Styling / theming:** Tailwind utility classes throughout; custom tokens in `tailwind.config.ts` (`cream`, `ink`, `muted`, `accent`, `rule`, `footer-bg`, `font-headline`/`font-body`/`font-label`).

**Font loading:** Declared in `nuxt.config.ts` via Google Fonts preconnect + stylesheet (`Instrument Serif`, `DM Mono`, `Literata`, `Source Sans 3`).

**Routing:** File-based Nuxt pages; one page only (`/`).

---

*Architecture analysis: 2026-04-23*
