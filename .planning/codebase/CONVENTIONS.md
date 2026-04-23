# Coding Conventions

**Analysis Date:** 2026-04-23

## Framework & Language Baseline

- **Nuxt 4** (`^4.4.2`) with Vue 3 (`^3.5.32`) and TypeScript
- Single-file components (`.vue`) using `<script setup lang="ts">` exclusively — no Options API, no plain JS
- TypeScript config is delegated to Nuxt-generated references in `tsconfig.json`; no custom compiler options
- ESLint via `@nuxt/eslint` module with default Nuxt ruleset (see `eslint.config.mjs` — no custom rules added)
- Tailwind CSS via `@nuxtjs/tailwindcss` (v6) with theme extensions in `tailwind.config.ts` (colors, fontFamily only)

## Naming Patterns

**Files:**
- Vue components: `kebab-case.vue` — e.g. `line-chart.vue`, `story-page.vue` in `app/components/`
- Pages: `kebab-case.vue` — e.g. `app/pages/index.vue`
- Config files: lowercase with dots — `nuxt.config.ts`, `tailwind.config.ts`, `eslint.config.mjs`

**Component tags in templates:**
- Kebab-case, matching filename — `<line-chart />`, `<story-page />`, `<NuxtPage />` (Nuxt built-ins stay PascalCase)

**Functions:**
- `camelCase` for all functions — `styleXAxis`, `hideTooltip`, `showTooltip`, `yearToDate`, `pointRadius`, `computeArrowStickyTop`, `handleResize`
- Prefix unused parameters with `_` — `function sourceColor(_source: string)`, `.on("mouseenter", (_event, d) => …)`

**Variables:**
- `camelCase` for locals, refs, and computeds — `xScale`, `tooltipBg`, `activeStep`, `gdpCsv`, `parsed`, `sliced`, `yDomain`
- Module-level mutable D3 state uses `let` with full generic types (see `app/components/line-chart.vue` lines 27–39)

**Constants:**
- `UPPER_SNAKE_CASE` for module-level immutable values — `WIDTH`, `HEIGHT`, `MARGIN`, `DURATION`, `LINE_COLOR` in `app/components/line-chart.vue`

**Types / Interfaces:**
- `PascalCase` — `GdpDataPoint` (exported inline from `app/components/line-chart.vue` line 9)
- Interfaces defined in the component that owns them; re-imported via `import type` (see `app/components/story-page.vue` line 292)

## Code Style

**Formatting:**
- 2-space indentation
- Double quotes (`"..."`) for all strings — both in TS and HTML attributes
- Semicolons terminate statements
- Trailing commas on multi-line object/array literals and type parameters
- No Prettier config committed; style is consistent manually and enforced via Nuxt ESLint defaults

**Linting:**
- `@nuxt/eslint` auto-generates flat config from `.nuxt/eslint.config.mjs`
- No custom rules added — accept Nuxt/Vue 3 defaults
- Run: `pnpm nuxt prepare` to regenerate; no dedicated `lint` script in `package.json`

## Import Organization

**Order (observed in `app/components/line-chart.vue` and `app/components/story-page.vue`):**
1. External libraries (`d3`, `scrollama`)
2. Type-only imports from local files (`import type { GdpDataPoint } from "./line-chart.vue"`)

**D3 import style:**
- Namespace import in heavy D3 consumers — `import * as d3 from "d3"` (`app/components/line-chart.vue` line 6)
- Named imports when only a few helpers are needed — `import { csvParse, extent as d3Extent } from "d3"` (`app/components/story-page.vue` line 291)
- `@types/d3` provides full typings; keep namespace form when using many primitives

**Nuxt auto-imports (never imported explicitly):**
- Vue reactivity: `ref`, `computed`, `watch`
- Lifecycle: `onMounted`, `onBeforeUnmount`
- Data fetching: `useFetch`
- If it looks like a Vue/Nuxt composable and there is no import, it is auto-imported — do not add explicit imports

**Path aliases:**
- Default Nuxt aliases (`~/`, `@/` → project root); not used in current code, prefer relative imports within `app/components/`

## Vue 3 Component Patterns

**Script block:**
- Always `<script setup lang="ts">` — never `<script lang="ts">` with `defineComponent`
- Template first, script after (see both components)
- No `<style>` blocks — all styling via Tailwind utility classes

**Props:**
- Type-only generic form: `const props = defineProps<{ data: Array<GdpDataPoint>; yDomain?: [number, number] }>()`
- Optional props use `?` and are resolved with nullish coalescing: `props.xDomain?.[0] ?? d3.min(...)`

**Template refs:**
- `const svg = ref(null)` for untyped SVG roots when passed directly to D3
- Typed refs for DOM interaction: `const figure = ref<HTMLElement>()`, `const scrollArrow = ref<SVGSVGElement | null>(null)`
- Use `ref="svg"` in template to bind

**Reactivity:**
- Derived data via `computed<T>(...)` with explicit generic when the shape is not obvious (`app/components/story-page.vue` lines 383, 396, 408)
- Side-effects on prop changes via `watch([() => props.a, () => props.b], ..., { deep: true })` — pass getters, not the prop directly
- Early-return guard pattern: `if (!ready) { initialize(); return }` inside watchers (`app/components/line-chart.vue` lines 347–351)

**Lifecycle:**
- Initialize D3 in `onMounted`
- Always pair `window.addEventListener` in `onMounted` with removal in `onBeforeUnmount` (see `app/components/story-page.vue` lines 428–462)

## D3 Usage Patterns

Canonical reference: `app/components/line-chart.vue`.

**Initialization vs. update split:**
- `initialize()` runs once: clears the SVG (`svgEl.selectAll("*").remove()`), creates scales, appends static groups (axes, lines, points, tooltip), and flips a module-level `ready` flag. Called from `onMounted` and when domains change structurally.
- `update(animate: boolean)` rebinds data on the existing groups using the general update pattern. Called on data/xDomain changes.

**Module-level selection state:**
- D3 selections held in `let` declarations typed as `d3.Selection<SVGGElement, unknown, null, undefined>` so `initialize()` can assign and `update()` can reuse them (lines 27–39).

**Enter/update/exit:**
- Use `.data(…, keyFn).join(enterFn, updateFn, exitFn)` with a stable key (`(d: any) => \`${d.source}-${d.year}\``)
- Put static attributes inside the enter branch; dynamic attributes after `.join(...)`

**Transitions:**
- `d3.transition().duration(DURATION).ease(d3.easeCubicInOut)` for coordinated axis animations
- Cast transitions where TS overload resolution fails: `xAxisG.transition(t as any) as any` — acceptable pragmatic cast in this codebase

**Scales & axes:**
- Time axis over years built from `new Date(year, 0, 0)` via `yearToDate(y)` helper
- Axis styling via `.call(styleXAxis)` helper — never inline large style chains

**Formatting:**
- Use `d3.format(",.0f")` at module level (`valueFormat` on line 40), reuse across tooltips

**Data loading:**
- CSV via Nuxt `useFetch` with `{ server: false }` (client-only), then `d3.csvParse(gdpCsv.value)` in a `computed` (`app/components/story-page.vue` lines 379–394)
- Coerce fields with `+d.year!` and `parseFloat(d.gdp_pc!)`, filter `Number.isNaN`, then `.sort()`

**Vite config:**
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

---

*Convention analysis: 2026-04-23*
