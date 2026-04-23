<!-- GSD:project-start source:PROJECT.md -->
## Project

**IB GDP Evolution**

A Nuxt 4 scrollytelling site that visualizes the evolution of GDP per capita in the Balearic Islands (Illes Balears) from 1900 to 2024. A long-form narrative page scrolls through D3-rendered line-chart steps powered by `scrollama`, driven by a single spliced CSV series produced by an offline Python ETL that chain-links Rosés-Wolf (1900–1999) with Eurostat/INE (2000–2024).

**Core Value:** Present the 125-year GDP-per-capita story as a beautiful, editorial, animated chart that communicates the long-arc transformation at a glance.

### Constraints

- **Tech stack**: Must remain Nuxt 4 + Vue 3 Composition API + D3 — no alternate viz libraries introduced.
- **Browser compatibility**: Modern evergreen browsers only (viz is the product, not reach).
- **Build**: `nuxt generate` must continue to work (static output).
- **Performance**: Chart re-renders on every scrollama step — per-frame Perlin noise work must be bounded so transitions stay smooth.
- **Style**: Stay within the editorial palette (`#660000` line, cream background, DM Mono labels) — no color or typography drift without explicit decision.
<!-- GSD:project-end -->

<!-- GSD:stack-start source:codebase/STACK.md -->
## Technology Stack

## Languages
- TypeScript (via Nuxt's generated `tsconfig.*.json` references in `tsconfig.json`) — used for Vue SFC `<script setup lang="ts">` blocks (`app/components/line-chart.vue`, `app/components/story-page.vue`) and config (`nuxt.config.ts`, `tailwind.config.ts`).
- Vue 3 SFC (`.vue`) — the entire UI layer (`app/app.vue`, `app/pages/index.vue`, `app/components/*.vue`).
- Python 3 — offline data pipeline only, not runtime (`scripts/extend_gdp.py`, shebang `#!/usr/bin/env python3`, uses `pandas`).
- JavaScript (ESM, `.mjs`) — ESLint config (`eslint.config.mjs`).
## Runtime
- Node.js — required by Nuxt 4 (no `.nvmrc` or `engines` field declared in `package.json`; pnpm lockfile records dependencies requiring `node >= 20`).
- Nitro server runtime — bundled by Nuxt (inferred from `.gitignore` entries `.nitro`, `.output`).
- pnpm (workspace configured via `pnpm-workspace.yaml`, lockfile `pnpm-lock.yaml` at `lockfileVersion: '9.0'`).
- Lockfile: present (`pnpm-lock.yaml`).
## Frameworks
- `nuxt` ^4.4.2 — full-stack Vue meta-framework (`nuxt.config.ts`). `compatibilityDate: "2025-07-15"`.
- `vue` ^3.5.32 — UI rendering (composition API with `<script setup>`).
- `vue-router` ^5.0.4 — routing (implicit via Nuxt file-based routing: `app/pages/index.vue`).
- Not detected. No `jest.config.*`, `vitest.config.*`, or `*.test.*` / `*.spec.*` files in the repository.
- Vite 7.x — bundler used by Nuxt (configured in `nuxt.config.ts` under `vite: { optimizeDeps: { exclude: ["d3"] } }`).
- `@nuxt/eslint` 1.15.2 — ESLint integration; generated config consumed via `./.nuxt/eslint.config.mjs` in `eslint.config.mjs`.
- `@nuxtjs/tailwindcss` 6.14.0 — Tailwind CSS Nuxt module (registered in `nuxt.config.ts` `modules`).
## Key Dependencies
- `d3` ^7.9.0 — SVG chart rendering for the GDP line chart (`app/components/line-chart.vue`: `d3.scaleTime`, `d3.scaleLinear`, `d3.line`, `d3.axisLeft`, `d3.transition`, `d3.format`). Excluded from Vite dep optimization in `nuxt.config.ts`.
- `@types/d3` ^7.4.3 — TypeScript typings for d3.
- `scrollama` ^3.2.0 — scrollytelling step tracking (`app/components/story-page.vue`: `import scrollama from "scrollama"`).
- `@nuxt/eslint` 1.15.2 — linting integration.
- `@nuxtjs/tailwindcss` 6.14.0 — utility CSS integration.
- `pandas` — CSV/Excel ingestion and chain-linking transforms (`scripts/extend_gdp.py`: `pd.read_csv`, `pd.read_excel`).
## Configuration
- No `.env` files present. `.gitignore` allows only `.env.example` (not present).
- No `useRuntimeConfig()` usage detected in `app/`. No runtime secrets or env-driven feature flags.
- Build is fully static/client-side: data is loaded from `public/data/*.csv` via `useFetch`.
- `nuxt.config.ts` — Nuxt modules, head `<link>` preconnect + Google Fonts stylesheet, Vite `optimizeDeps` exclusion for d3, devtools enabled.
- `tailwind.config.ts` — theme extension with custom editorial color palette (`cream`, `ink`, `accent`, etc.) and font families (`Instrument Serif`, `DM Mono`, `Literata`, `Source Sans 3`).
- `tsconfig.json` — delegates to Nuxt-generated `./.nuxt/tsconfig.{app,server,shared,node}.json` via `references`.
- `eslint.config.mjs` — flat config, wraps Nuxt's generated config with `withNuxt()`.
- `pnpm-workspace.yaml` — declares `ignoredBuiltDependencies: [@parcel/watcher, esbuild, unrs-resolver]`.
## Platform Requirements
- Node.js (>=20 per transitive dep `@parcel/watcher`).
- pnpm (install via `pnpm install`).
- Dev server: `pnpm dev` (`nuxt dev`) on `http://localhost:3000`.
- Optional: Python 3 + `pandas` for regenerating CSVs via `scripts/extend_gdp.py`.
- Static site generation target via `pnpm generate` (`nuxt generate`) — all data lives under `public/data/` so the app can be deployed as static HTML/JS to any static host. `nuxt build` + `nuxt preview` also available.
- No hosting platform configuration committed (no `vercel.json`, `netlify.toml`, `Dockerfile`, etc.).
## Scripts
# postinstall: nuxt prepare (regenerates .nuxt/)
<!-- GSD:stack-end -->

<!-- GSD:conventions-start source:CONVENTIONS.md -->
## Conventions

## Framework & Language Baseline
- **Nuxt 4** (`^4.4.2`) with Vue 3 (`^3.5.32`) and TypeScript
- Single-file components (`.vue`) using `<script setup lang="ts">` exclusively — no Options API, no plain JS
- TypeScript config is delegated to Nuxt-generated references in `tsconfig.json`; no custom compiler options
- ESLint via `@nuxt/eslint` module with default Nuxt ruleset (see `eslint.config.mjs` — no custom rules added)
- Tailwind CSS via `@nuxtjs/tailwindcss` (v6) with theme extensions in `tailwind.config.ts` (colors, fontFamily only)
## Naming Patterns
- Vue components: `kebab-case.vue` — e.g. `line-chart.vue`, `story-page.vue` in `app/components/`
- Pages: `kebab-case.vue` — e.g. `app/pages/index.vue`
- Config files: lowercase with dots — `nuxt.config.ts`, `tailwind.config.ts`, `eslint.config.mjs`
- Kebab-case, matching filename — `<line-chart />`, `<story-page />`, `<NuxtPage />` (Nuxt built-ins stay PascalCase)
- `camelCase` for all functions — `styleXAxis`, `hideTooltip`, `showTooltip`, `yearToDate`, `pointRadius`, `computeArrowStickyTop`, `handleResize`
- Prefix unused parameters with `_` — `function sourceColor(_source: string)`, `.on("mouseenter", (_event, d) => …)`
- `camelCase` for locals, refs, and computeds — `xScale`, `tooltipBg`, `activeStep`, `gdpCsv`, `parsed`, `sliced`, `yDomain`
- Module-level mutable D3 state uses `let` with full generic types (see `app/components/line-chart.vue` lines 27–39)
- `UPPER_SNAKE_CASE` for module-level immutable values — `WIDTH`, `HEIGHT`, `MARGIN`, `DURATION`, `LINE_COLOR` in `app/components/line-chart.vue`
- `PascalCase` — `GdpDataPoint` (exported inline from `app/components/line-chart.vue` line 9)
- Interfaces defined in the component that owns them; re-imported via `import type` (see `app/components/story-page.vue` line 292)
## Code Style
- 2-space indentation
- Double quotes (`"..."`) for all strings — both in TS and HTML attributes
- Semicolons terminate statements
- Trailing commas on multi-line object/array literals and type parameters
- No Prettier config committed; style is consistent manually and enforced via Nuxt ESLint defaults
- `@nuxt/eslint` auto-generates flat config from `.nuxt/eslint.config.mjs`
- No custom rules added — accept Nuxt/Vue 3 defaults
- Run: `pnpm nuxt prepare` to regenerate; no dedicated `lint` script in `package.json`
## Import Organization
- Namespace import in heavy D3 consumers — `import * as d3 from "d3"` (`app/components/line-chart.vue` line 6)
- Named imports when only a few helpers are needed — `import { csvParse, extent as d3Extent } from "d3"` (`app/components/story-page.vue` line 291)
- `@types/d3` provides full typings; keep namespace form when using many primitives
- Vue reactivity: `ref`, `computed`, `watch`
- Lifecycle: `onMounted`, `onBeforeUnmount`
- Data fetching: `useFetch`
- If it looks like a Vue/Nuxt composable and there is no import, it is auto-imported — do not add explicit imports
- Default Nuxt aliases (`~/`, `@/` → project root); not used in current code, prefer relative imports within `app/components/`
## Vue 3 Component Patterns
- Always `<script setup lang="ts">` — never `<script lang="ts">` with `defineComponent`
- Template first, script after (see both components)
- No `<style>` blocks — all styling via Tailwind utility classes
- Type-only generic form: `const props = defineProps<{ data: Array<GdpDataPoint>; yDomain?: [number, number] }>()`
- Optional props use `?` and are resolved with nullish coalescing: `props.xDomain?.[0] ?? d3.min(...)`
- `const svg = ref(null)` for untyped SVG roots when passed directly to D3
- Typed refs for DOM interaction: `const figure = ref<HTMLElement>()`, `const scrollArrow = ref<SVGSVGElement | null>(null)`
- Use `ref="svg"` in template to bind
- Derived data via `computed<T>(...)` with explicit generic when the shape is not obvious (`app/components/story-page.vue` lines 383, 396, 408)
- Side-effects on prop changes via `watch([() => props.a, () => props.b], ..., { deep: true })` — pass getters, not the prop directly
- Early-return guard pattern: `if (!ready) { initialize(); return }` inside watchers (`app/components/line-chart.vue` lines 347–351)
- Initialize D3 in `onMounted`
- Always pair `window.addEventListener` in `onMounted` with removal in `onBeforeUnmount` (see `app/components/story-page.vue` lines 428–462)
## D3 Usage Patterns
- `initialize()` runs once: clears the SVG (`svgEl.selectAll("*").remove()`), creates scales, appends static groups (axes, lines, points, tooltip), and flips a module-level `ready` flag. Called from `onMounted` and when domains change structurally.
- `update(animate: boolean)` rebinds data on the existing groups using the general update pattern. Called on data/xDomain changes.
- D3 selections held in `let` declarations typed as `d3.Selection<SVGGElement, unknown, null, undefined>` so `initialize()` can assign and `update()` can reuse them (lines 27–39).
- Use `.data(…, keyFn).join(enterFn, updateFn, exitFn)` with a stable key (`(d: any) => \`${d.source}-${d.year}\``)
- Put static attributes inside the enter branch; dynamic attributes after `.join(...)`
- `d3.transition().duration(DURATION).ease(d3.easeCubicInOut)` for coordinated axis animations
- Cast transitions where TS overload resolution fails: `xAxisG.transition(t as any) as any` — acceptable pragmatic cast in this codebase
- Time axis over years built from `new Date(year, 0, 0)` via `yearToDate(y)` helper
- Axis styling via `.call(styleXAxis)` helper — never inline large style chains
- Use `d3.format(",.0f")` at module level (`valueFormat` on line 40), reuse across tooltips
- CSV via Nuxt `useFetch` with `{ server: false }` (client-only), then `d3.csvParse(gdpCsv.value)` in a `computed` (`app/components/story-page.vue` lines 379–394)
- Coerce fields with `+d.year!` and `parseFloat(d.gdp_pc!)`, filter `Number.isNaN`, then `.sort()`
- `vite.optimizeDeps.exclude: ["d3"]` in `nuxt.config.ts` to avoid Vite pre-bundling issues with D3's ESM
## Tailwind Conventions
- Utility-first, **no `<style>` blocks** anywhere in the codebase
- Extensive use of Tailwind arbitrary values: `text-[clamp(2.5rem,6vw,4.5rem)]`, `tracking-[0.4em]`, `h-[0.5px]`, `min-h-[1280px]`, `[filter:url(#shadow)]`
- Custom semantic colors defined in `tailwind.config.ts` — use `bg-cream`, `text-ink`, `text-muted`, `text-accent`, `border-rule`, `bg-footer-bg`; do not reintroduce hex literals in templates
- Custom font families — `font-headline` (Instrument Serif), `font-body` (DM Mono), `font-label` (DM Mono)
- Responsive variants at `md:` breakpoint only (no `sm:` / `lg:` usage in current code)
- Multi-line class lists: break the `class="..."` attribute across lines inside the template when it exceeds ~80 chars (see `app/components/story-page.vue` lines 68–69)
## Error Handling
- Explicit guard returns rather than try/catch — e.g. `if (typeof gdpCsv.value !== "string") return []` (`app/components/story-page.vue` line 384)
- D3 accessors use nullish coalescing for missing data: `d3.min(newData, d => d.year) ?? 1900`
- DOM queries guard via optional chaining and `?? null`: `scrollArrowContainer.value?.querySelector(...)`
## Logging
- No logger. No `console.log` in committed code. Keep it that way.
## Comments
- Extremely sparse — code is expected to speak for itself
- Only existing comments are section markers inside `initialize()` (e.g. `// Y-axis (static, drawn once)` on line 160) and config pointers (`// https://nuxt.com/docs/...`)
- Do **not** add narration comments; only explain non-obvious trade-offs or constraints
## Function Design
- Small, single-purpose helpers at module scope (not inside `setup()`) when they don't capture reactive state — `yearToDate`, `pointRadius`, `sourceColor`, `styleXAxis`
- Closure-based helpers (`showTooltip`, `hideTooltip`, `initialize`, `update`) live at module scope and read module-level `let` bindings
- Prefer explicit parameter and return types for exported/shared interfaces; rely on inference for local closures
## Module Design
- One component per file; no barrel files (`index.ts`) in `app/components/`
- Shared types co-located with their primary consumer and exported inline (see `GdpDataPoint` in `app/components/line-chart.vue`)
- Python data-prep scripts live in `scripts/` (e.g. `scripts/extend_gdp.py`) — separate from the Nuxt app, not imported by it
- Static data in `public/data/*.csv`, loaded at runtime via `useFetch("/data/...")`
<!-- GSD:conventions-end -->

<!-- GSD:architecture-start source:ARCHITECTURE.md -->
## Architecture

## Pattern Overview
- Nuxt 4 app (`nuxt ^4.4.2`, Vue 3.5, Vue Router) using file-based routing with a single page (`app/pages/index.vue`) mounted through `<NuxtPage />` in `app/app.vue`.
- Client-rendered data visualization: a long-form narrative page (`app/components/story-page.vue`) scrolls through D3-rendered line-chart steps (`app/components/line-chart.vue`) driven by `scrollama`.
- Static data lives under `public/data/*.csv` and is consumed in-browser via `useFetch` + `d3.csvParse`; no server API layer.
- Data preparation is decoupled: a standalone Python pipeline (`scripts/extend_gdp.py`) chain-links Rosés-Wolf (1900–1999) with Eurostat/INE real-growth (2000–2024) outputs to produce the CSVs consumed by the front end.
- Styling via Tailwind (`@nuxtjs/tailwindcss` + `tailwind.config.ts`) with a custom editorial color/typography theme; no component library.
- No backend, no auth, no database — pure static/SSG-capable Nuxt project (`nuxt generate` available in `package.json`).
## Layers
- Purpose: Mount the router and provide global `<head>` (fonts).
- Location: `app/app.vue`, `nuxt.config.ts`
- Contains: `<NuxtPage />`, Google Fonts preconnect/stylesheet links, Tailwind + ESLint module registration, `vite.optimizeDeps.exclude: ["d3"]`.
- Depends on: `@nuxt/eslint`, `@nuxtjs/tailwindcss`.
- Used by: The Nuxt runtime (build/dev).
- Purpose: File-based route producing the single URL `/`.
- Location: `app/pages/index.vue`
- Contains: A thin wrapper that renders `<story-page />`.
- Depends on: `app/components/story-page.vue` (auto-imported by Nuxt).
- Used by: `<NuxtPage />` in `app/app.vue`.
- Purpose: Owns the scrollytelling UX — hero, intro prose, scroll-driven chart figure, outro, data-methods, footer.
- Location: `app/components/story-page.vue`
- Contains: Step definitions (`steps` array of `{ body, from, to, xMax }`), data fetch (`useFetch("/data/balearic_gdp_pc.csv", { server: false })`), D3 CSV parsing, computed `sliced`/`xDomain`/`yDomain`, `scrollama` setup, scroll-arrow sticky calculation, Tailwind markup, inline SVG `<filter id="shadow">` reused by steps.
- Depends on: `scrollama`, `d3` (`csvParse`, `extent`), `./line-chart.vue` (type import `GdpDataPoint`).
- Used by: `app/pages/index.vue`.
- Purpose: Render and animate the GDP-per-capita line chart in SVG.
- Location: `app/components/line-chart.vue`
- Contains: Exports `interface GdpDataPoint`; imperative D3 pipeline (`initialize` / `update`) for scales, axes, lines, points, hover tooltip; transitions via `d3.transition().duration(800).ease(d3.easeCubicInOut)`; per-source styling maps (`sourceColors`, `sourceOrder`, `pointRadius`).
- Depends on: `d3` (namespace import).
- Used by: `app/components/story-page.vue` via `<line-chart :data :y-domain :x-domain />`.
- Purpose: Serve preprocessed CSVs to the browser.
- Location: `public/data/`
- Contains: `balearic_gdp_pc.csv` (spliced series consumed by the app), plus supporting/intermediate tables `balearic_ine_chainlinked_gdp_pc.csv`, `balearic_ine_gdp_pc_datalake.csv`, `roses_wolf_selected_comparison.csv`.
- Depends on: Nothing at runtime.
- Used by: `story-page.vue` via `useFetch`.
- Purpose: Produce the public CSVs from Rosés-Wolf + Eurostat/INE inputs with sanity checks.
- Location: `scripts/extend_gdp.py`
- Contains: Loaders for Rosés-Wolf and Eurostat, NUTS correspondence resolution, chain-linking at a 2022 anchor, seam/growth/coverage/outlier/level checks, CSV + text-report output.
- Depends on: `pandas` (external Python environment, not in `package.json`).
- Used by: Operated manually by the developer; not invoked by the Nuxt runtime.
## Data Flow
- Component-local Vue refs only (`activeStep`, `scrollArrowHeight`, etc.) in `story-page.vue`.
- No Pinia, no Vuex, no Nuxt state composables.
- Mutable D3 selections are held in module-scope `let` bindings inside `line-chart.vue`'s `<script setup>` (`xScale`, `yScale`, `linesG`, `pointsG`, `tooltipG`, …) and reset by `initialize()`.
## Key Abstractions
- Purpose: Single row of the plotted GDP-per-capita series.
- Examples: `app/components/line-chart.vue` (exports interface), `app/components/story-page.vue` (type import).
- Pattern: Exported TypeScript `interface` co-located with the consumer component; imported via a Vue SFC type import (`import type { GdpDataPoint } from "./line-chart.vue"`).
- Purpose: Narrative beat that controls the chart window.
- Examples: `steps` array in `app/components/story-page.vue` (literal `{ body, from, to, xMax }`).
- Pattern: Plain inline data array indexed by `activeStep`; no separate config file.
- Purpose: Keep SVG in sync with reactive props.
- Examples: `initialize()` / `update(animate)` in `app/components/line-chart.vue`, driven by `watch([() => props.data, () => props.xDomain], …)`.
- Pattern: Enter/update/exit joins with key functions (`d => d.source` for series paths, `` `${d.source}-${d.year}` `` for points).
- Purpose: Differentiate Rosés-Wolf (`RW`) vs INE (`INE`) marks.
- Examples: `sourceColors`, `sourceOrder`, `pointRadius`, `sourceWidth` in `app/components/line-chart.vue`.
- Pattern: `Map<string, …>` / pure functions keyed on `d.source`.
## Entry Points
- Location: `app/app.vue`
- Triggers: Nuxt runtime on any route.
- Responsibilities: Render `<NuxtPage />`.
- Location: `app/pages/index.vue`
- Triggers: Navigation to `/` (the only route).
- Responsibilities: Render `<story-page />`.
- Location: `nuxt.config.ts`
- Triggers: Build/dev server startup.
- Responsibilities: Register `@nuxt/eslint` and `@nuxtjs/tailwindcss`, inject Google Fonts `<link>` tags, set `vite.optimizeDeps.exclude: ["d3"]`, `compatibilityDate: "2025-07-15"`.
- Location: `eslint.config.mjs`
- Triggers: `eslint` invocations.
- Responsibilities: Re-export `withNuxt()` from `.nuxt/eslint.config.mjs`.
- Location: `scripts/extend_gdp.py`
- Triggers: `python scripts/extend_gdp.py [--workspace ... --rw-path ... --eurostat-path ... --output-csv ...]`.
- Responsibilities: Produce chain-linked GDP CSV + sanity report.
## Error Handling
- Front end: `parsed` computed returns `[]` when `gdpCsv.value` is not a string and filters out NaN years/values before plotting; `sliced` / `xDomain` / `yDomain` return safe defaults (`[]`, `[1900, 1990]`, `[0, 1]`) when the data or step is missing; `line-chart.vue` short-circuits `update()` with `if (!ready) return` and clears paths/points on empty data.
- Hover positioning clamps tooltip `tx` / `ty` within `MARGIN` bounds to avoid overflow.
- Data pipeline: Custom `PipelineError` raised on missing inputs, failed Eurostat unit guard (`CLV` required, `CP` / `PPS` rejected), empty datasets, or failed seam-continuity check; `main()` catches it and exits non-zero with `raise SystemExit(f"ERROR: {exc}")`.
## Cross-Cutting Concerns
<!-- GSD:architecture-end -->

<!-- GSD:skills-start source:skills/ -->
## Project Skills

No project skills found. Add skills to any of: `.claude/skills/`, `.agents/skills/`, `.cursor/skills/`, or `.github/skills/` with a `SKILL.md` index file.
<!-- GSD:skills-end -->

<!-- GSD:workflow-start source:GSD defaults -->
## GSD Workflow Enforcement

Before using Edit, Write, or other file-changing tools, start work through a GSD command so planning artifacts and execution context stay in sync.

Use these entry points:
- `/gsd-quick` for small fixes, doc updates, and ad-hoc tasks
- `/gsd-debug` for investigation and bug fixing
- `/gsd-execute-phase` for planned phase work

Do not make direct repo edits outside a GSD workflow unless the user explicitly asks to bypass it.
<!-- GSD:workflow-end -->



<!-- GSD:profile-start -->
## Developer Profile

> Profile not yet configured. Run `/gsd-profile-user` to generate your developer profile.
> This section is managed by `generate-claude-profile` -- do not edit manually.
<!-- GSD:profile-end -->
