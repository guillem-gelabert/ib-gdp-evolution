# Codebase Concerns

**Analysis Date:** 2026-04-23

## Tech Debt

**Dead multi-source scaffolding in line chart:**
- Issue: Helper functions `sourceColor`, `sourceWidth`, `sourceOpacity`, `pointOpacity` are all no-ops that ignore their `source` argument and return a single constant. The `sourceColors` Map is declared but only read through the no-op `sourceColor` (which ignores it). Only `pointRadius` and `sourceOrder` still branch on source. This is leftover scaffolding from when RW and INE were rendered as two visually-distinct series.
- Files: `app/components/line-chart.vue` (lines 41–71, 300–324)
- Impact: Misleading to readers; suggests behavior that doesn't exist. The `_source` underscore-prefixed params signal intentional unused args, but the indirection adds noise without benefit.
- Fix approach: Either (a) delete the no-op helpers and inline constants (`LINE_COLOR`, `2.5`, `1`), or (b) restore per-source styling by reading from `sourceColors`/adding `sourceWidths` maps and driving them from props.

**Hard-coded chart dimensions and styling duplicated from Tailwind theme:**
- Issue: `WIDTH=928`, `HEIGHT=400`, `MARGIN={top:16,right:30,bottom:36,left:80}`, `DURATION=800`, and color literals (`#660000`, `#D6D5D3`, `#6B6B6B`, `#FAF7F0`, `#2F2F2F`, `#8C8A85`, `#FAF7F0` stroke) are all embedded in the component. `#660000` duplicates `accent` in Tailwind theme; `#D6D5D3` duplicates `rule`; `#FAF7F0` has no counterpart but is near `cream-alt`.
- Files: `app/components/line-chart.vue` (lines 22–25, 41, 78, 82, 171, 180, 191, 206–207, 215, 226, 319); duplicated theme values in `tailwind.config.ts` (lines 7–16).
- Impact: Changing the brand palette requires edits in two places and risks drift. Chart does not adapt to dark mode or theme variants.
- Fix approach: Expose colors as CSS custom properties in a global stylesheet, reference them via `getComputedStyle(document.documentElement)` inside the chart, or pass them as props. Extract `WIDTH`/`HEIGHT`/`MARGIN` into a config object that can be overridden.

**Font family string duplicated across eight d3 selections:**
- Issue: The literal `"DM Mono, Courier New, monospace"` is repeated on every axis tick, tooltip text, and label styling call in the chart.
- Files: `app/components/line-chart.vue` (lines 80, 178, 213, 219, 224)
- Impact: Any font change requires updating five call-sites. Already drifts from the Tailwind `font-body` token (`'"DM Mono"', '"Courier New"', monospace` — note the quoted family name).
- Fix approach: Hoist to a `CHART_FONT` constant; better, set `font-family` once on the `<svg>` element and let children inherit.

**Module-scope mutable chart state:**
- Issue: `xScale`, `yScale`, `xAxisG`, `linesG`, `hoverLine`, `pointsG`, `tooltipG`, `tooltipBg`, `tooltipYear`, `tooltipSource`, `tooltipValue`, `lineGen`, `ready`, and `valueFormat` are declared with `let`/`const` at script top-level inside `<script setup>`.
- Files: `app/components/line-chart.vue` (lines 27–40)
- Impact: In Nuxt/Vue 3 with `<script setup>`, each component instance gets its own script closure, so this currently works; however, any future attempt to render two `<line-chart>` instances on the same page (comparison view, small multiples) will have the first instance's refs clobbered by the second because they're accessed through shared `let` bindings in a single closure per invocation. This is a latent bug disguised as working code.
- Fix approach: Move all `let` declarations inside a single `initialize()`-owned object or wrap them in a `ref({...})`.

**Two watchers can both trigger `initialize()` on first prop resolution:**
- Issue: The `yDomain` watcher runs `initialize()` when `ready` is true; the `[data, xDomain]` watcher runs `initialize()` when `ready` is false and `update()` otherwise. If `yDomain` and `data` resolve in the same microtask, the full SVG can be torn down and rebuilt twice.
- Files: `app/components/line-chart.vue` (lines 336–354)
- Impact: Visible flicker on first paint and wasted work; `onMounted` → `initialize` → both watchers fire immediately due to deep-watch semantics.
- Fix approach: Consolidate into a single watcher that computes whether to re-initialize (yDomain changed) vs update (data/xDomain changed) vs no-op.

**`yearToDate` uses day index 0:**
- Issue: `new Date(y, 0, 0)` resolves to **31 December of year y−1** (JavaScript `Date` treats day 0 as the last day of the previous month). A year labelled 1900 is actually plotted at 1899-12-31.
- Files: `app/components/line-chart.vue` (line 74)
- Impact: Every point is shifted one day earlier than intended; the x-axis ticks (also driven through `xScale`) show 1900 but the domain endpoint sits on 1899-12-31. Visually imperceptible at year granularity but semantically wrong and a trap for any future sub-year interpolation or tooltip formatting.
- Fix approach: Use `new Date(y, 0, 1)` for January 1 or `new Date(Date.UTC(y, 0, 1))` to avoid timezone drift.

**`as any` type escapes in d3 selection/transition chains:**
- Issue: Six `as any` casts bypass typing for `d3.axisBottom` calls, transition chaining, and join key functions.
- Files: `app/components/line-chart.vue` (lines 185, 250, 270, 272, 288, 311)
- Impact: D3 typing errors silently pass, `d: any` keys lose autocomplete, refactors can compile with broken runtime behavior.
- Fix approach: Type the selections correctly with `d3.Selection<SVGGElement, unknown, null, undefined>` (already done for declarations but cast away at use sites). For joins, type data as `GdpDataPoint` instead of `any`.

**Inconsistent default x-axis fallback:**
- Issue: When data is empty and no xDomain is provided, `update()` falls back to `[1900, 1930]`, but `initialize()` falls back to `[1900, 1950]`.
- Files: `app/components/line-chart.vue` (lines 153–154 vs 242–243)
- Impact: Flash of wrong range during initial mount-with-empty-data edge case.
- Fix approach: Hoist a single `DEFAULT_X_DOMAIN` constant.

**Narrative content hard-coded inside component:**
- Issue: The 12-step narrative (`steps` array with body copy, year ranges, `xMax` keyframes) lives inside `story-page.vue`. Changes to prose require editing a Vue component file.
- Files: `app/components/story-page.vue` (lines 304–377)
- Impact: Editors/writers cannot touch copy without Vue familiarity. Translation (e.g. Catalan/Spanish versions for a Balearic audience) requires component duplication.
- Fix approach: Extract to `public/data/steps.json` or a dedicated `content/` directory if adopting Nuxt Content.

**Prose facts embedded as literals:**
- Issue: "45.5% of Balearic GDP", "€36,093 in 2024", "© 2024 GGS" are hard-coded strings that will go stale. GDP share and 2024 figure should be sourced from the data; copyright year should auto-update or match the current milestone.
- Files: `app/components/story-page.vue` (lines 143, 152, 283)
- Impact: Copyright footer already reads 2024 while today is 2026. Data-journalism credibility depends on keeping cited figures accurate; literals drift silently.
- Fix approach: Drive the 2024 figure from a `computed` over parsed CSV; replace footer year with `new Date().getFullYear()` or tie to milestone metadata.

**Scrollytelling scroller not torn down on unmount:**
- Issue: `scrollama()` instance is created in `onMounted` but `scroller.destroy()` is never called. Only the resize listener is cleaned up.
- Files: `app/components/story-page.vue` (lines 432–458 setup; 460–462 teardown)
- Impact: On HMR during development and on route changes if the app grows beyond this single page, scrollama keeps its IntersectionObservers and leaks DOM references.
- Fix approach: In `onBeforeUnmount`, call `scroller.destroy()` alongside the `removeEventListener`.

**Scroll-arrow sticky math is fragile:**
- Issue: `computeArrowStickyTop` reads `hero.value.querySelector(":scope > div")` and computes a page-relative `scrollArrowStickyTop` from `getBoundingClientRect().bottom + window.scrollY`. Relies on hero's DOM shape (first child `div`).
- Files: `app/components/story-page.vue` (lines 414–426)
- Impact: Any layout change to the hero section (adding a wrapper, reordering) silently breaks the scroll arrow. No fallback if `contentEl` is null (it early-returns, leaving the initial 418px guess which may be wrong for small viewports).
- Fix approach: Give the content div an explicit `ref` (`heroContent`) and read from that instead of querying by position.

**`await useFetch` with `server: false` disables SSR for a data-journalism page:**
- Issue: `useFetch("/data/balearic_gdp_pc.csv", { server: false })` is awaited at the top level of `<script setup>`. `server: false` means the CSV is fetched only on the client, and the awaited promise runs against a `null` value during SSR.
- Files: `app/components/story-page.vue` (lines 379–381)
- Impact: The page is effectively client-rendered for chart data. Search engines, social-media previews, and accessibility tools see a page without the data. Also adds a loading gap and FOUC. Given this is a published narrative, SEO and first-paint content are higher-stakes than typical.
- Fix approach: Drop `server: false` so Nuxt fetches during SSR; keep `useFetch` or switch to a static import (`import csv from '~/public/data/balearic_gdp_pc.csv?raw'`) since the CSV is small (~27 rows) and ships in the bundle already.

**`nuxt.config.ts` excludes d3 from Vite dep optimization without explanation:**
- Issue: `vite: { optimizeDeps: { exclude: ["d3"] } }` disables Vite's pre-bundling of d3.
- Files: `nuxt.config.ts` (lines 25–27)
- Impact: Slower cold dev server starts (d3 has many sub-packages); unclear why this exists. Appears cargo-culted from an SSR troubleshooting issue.
- Fix approach: Remove the exclude and verify dev/build both work, or add a comment explaining the reason (e.g. "ESM/CJS interop bug with d3 X.Y.Z in Nuxt Z").

**Nuxt starter README left unchanged:**
- Issue: `README.md` is the default "Nuxt Minimal Starter" boilerplate. No mention of the project purpose, data sources, commands specific to this repo (pnpm is the lockfile, but README lists four package managers), or how to regenerate the CSV via `scripts/extend_gdp.py`.
- Files: `README.md`
- Impact: New contributors (or future-you) cannot discover that `pnpm dev` is the canonical command or that the CSV is produced by a Python pipeline.
- Fix approach: Replace with a project-specific README that includes purpose, data provenance, build commands, and the Python pipeline invocation.

## Known Bugs

**`activeStep` defaults to 0 before the reader enters the scrollytelling section:**
- Symptoms: When the page loads, the sticky figure is pre-rendered with step 0's `from/to/xMax` (1900–1910, xMax=1990) even though the reader is still on the hero. When they finally scroll past the intro and hit the first step, the chart animates from the identical state (no change) instead of animating in from an empty state.
- Files: `app/components/story-page.vue` (line 297 default; 452–454 setup)
- Trigger: Page load → scroll to first step.
- Workaround: None visible to user; minor polish issue. Could also be intentional but looks like an oversight.

**Step `from: 1900, to: 1910` shows a single decadal data point:**
- Symptoms: The first narrative step renders a line with only two points (1900 and 1910) because Rosés-Wolf data is decadal until 1950. The line is visible but the story text refers to "the line on this chart" before there's a visible trajectory (step 3 is the first to say "Notice how little it moves").
- Files: `app/components/story-page.vue` (lines 305–310); data in `public/data/balearic_gdp_pc.csv`.
- Trigger: First scroll step.
- Workaround: None. Narrative design choice — worth flagging for UAT review.

**Multiple uncommitted data files and deletions in working tree:**
- Symptoms: `git status` shows modified `line-chart.vue`, `app.vue`, `nuxt.config.ts`; untracked `story-page.vue`, `pages/index.vue`, `tailwind.config.ts`, `scripts/extend_gdp.py`, three new CSVs in `public/data/`, and a deleted `public/data/ib-gdp-absolute.csv`. A `scripts/__pycache__/extend_gdp.cpython-314.pyc` bytecode file is also untracked.
- Files: repo root (git working tree).
- Trigger: State at analysis time; unrelated to code behavior but indicates an in-progress refactor that is unreviewed.
- Workaround: Not a runtime bug — flagged so it's not lost in a rebase.

## Security Considerations

**External Google Fonts stylesheet:**
- Risk: Loads fonts from `fonts.googleapis.com` via a `<link rel="stylesheet">`. Each page view leaks IP + User-Agent to Google.
- Files: `nuxt.config.ts` (lines 8–22)
- Current mitigation: `preconnect` hints only; no `crossorigin="anonymous"` on the stylesheet link itself (only on `fonts.gstatic.com` preconnect).
- Recommendations: Self-host the four font families with `@fontsource/*` packages or Nuxt Fonts module; removes the third-party request, improves offline dev, and avoids privacy/GDPR footgun for a Spain-targeted publication.

**No Content Security Policy:**
- Risk: Static deploy ships without `Content-Security-Policy` or `X-Frame-Options` headers. d3 and scrollama are trusted, but any future `v-html` addition would have no defense-in-depth.
- Files: `nuxt.config.ts` (no `routeRules` or `nitro.routeRules` with headers).
- Current mitigation: None.
- Recommendations: Add `nitro.routeRules['/**'] = { headers: { 'Content-Security-Policy': "default-src 'self'; img-src 'self' data:; style-src 'self' https://fonts.googleapis.com 'unsafe-inline'; font-src 'self' https://fonts.gstatic.com; ..." } }`. Re-verify after self-hosting fonts (simpler policy).

**No input surfaces to exploit:**
- Risk: Minimal — app has no user input, no query params read, no cookies, no auth, no API.
- Current mitigation: Static site.
- Recommendations: Keep it that way. If a "share year range" feature is added later, validate the URL params before feeding them into the xDomain.

## Performance Bottlenecks

**Full SVG re-initialization on `yDomain` change:**
- Problem: The `yDomain` watcher calls `initialize()`, which calls `svgEl.selectAll("*").remove()` and rebuilds every axis, label, tooltip group, and points group from scratch. Since `yDomain` is a `computed` over `parsed.value`, it is stable after first resolution — but any deep change to `parsed.value` (e.g. refetched CSV in a future scenario) will tear down the chart instead of transitioning it.
- Files: `app/components/line-chart.vue` (lines 143–235, 336–342)
- Cause: y-axis is drawn once inside `initialize()`, so `update()` cannot re-draw it. Any yDomain change therefore requires full init.
- Improvement path: Draw the y-axis inside `update()` like the x-axis, keep a reference `yAxisG`, and transition it on yDomain change. Then reserve `initialize()` for real mount.

**800ms transition on every step scroll:**
- Problem: Every step change triggers an 800ms cubic-ease transition on both the x-axis and the line paths. Users who scroll quickly or use `prefers-reduced-motion` get queued animations.
- Files: `app/components/line-chart.vue` (line 25 `DURATION`; lines 268–273)
- Cause: No check for `prefers-reduced-motion`; no transition interruption when a new step arrives mid-animation (d3 does handle interruption automatically on the same selection, but there is no fast-forward).
- Improvement path: Read `matchMedia('(prefers-reduced-motion: reduce)')` and set `DURATION` to 0 when true. Consider clamping the duration dynamically based on scroll velocity.

**CSV fetched, parsed, and filtered on every step on the client:**
- Problem: `parsed` is a `computed` so it only runs when `gdpCsv.value` changes (once). `sliced` filters on every `activeStep` change — fine for 27 rows. Potential issue arrives if the dataset grows (e.g. annual series back to 1850 across multiple regions).
- Files: `app/components/story-page.vue` (lines 383–400)
- Cause: Linear filter per step.
- Improvement path: Pre-compute an index `year → row` and slice by index boundaries. Not needed at current scale; flag it before extending the dataset.

**Google Fonts request is render-blocking:**
- Problem: The stylesheet has no `media="print" onload` trick and no `&display=swap` enforcement at the Nuxt level (it is already in the URL — good). Still, the request blocks first paint until Google responds.
- Files: `nuxt.config.ts` (lines 19–21)
- Cause: Cross-origin stylesheet reference.
- Improvement path: Self-host fonts (see Security section — one fix addresses both issues).

## Fragile Areas

**Chart depends on parent sizing via `w-full max-w-[1200px]`:**
- Files: `app/components/line-chart.vue` (line 2); `app/components/story-page.vue` (line 174)
- Why fragile: The SVG uses `preserveAspectRatio="xMidYMid meet"` with a fixed `viewBox` of 928×400. On narrow viewports it scales down uniformly, which makes tooltip hit targets (r=3–4px) very small on mobile. There is no responsive re-layout of margins or font sizes.
- Safe modification: Test on 375px-wide viewport before touching margins. Prefer adding breakpoint-aware font sizes via CSS rather than changing d3 attrs.
- Test coverage: None.

**Scrollytelling figure positioning uses `-mt-[87.5vh]`:**
- Files: `app/components/story-page.vue` (line 191)
- Why fragile: Article is pulled up by 87.5% of viewport height to overlap the sticky figure. Any change to figure height (e.g. adding a subtitle) breaks the alignment. Magic number with no comment.
- Safe modification: Keep the figure at exactly `h-screen` and the offset at 87.5vh together; changing one requires changing the other.
- Test coverage: Visual only, none automated.

**`scrollArrowStickyTop` math assumes hero's first child is the content div:**
- Files: `app/components/story-page.vue` (lines 414–426)
- Why fragile: `hero.value.querySelector(":scope > div")` — the first div child happens to be the content wrapper (`<div class="relative z-10 ...">`). Moving the `aria-hidden` spacer above it (currently after it) would silently break the arrow.
- Safe modification: Add an explicit `ref="heroContent"` to the content div.
- Test coverage: None.

## Scaling Limits

**Single-page, single-dataset assumption:**
- Current capacity: One chart, 27 data points, 12 narrative steps.
- Limit: The `line-chart.vue` component breaks when rendered twice in the same page (module-scope `let` state — see Tech Debt) and does not support multiple series visually distinct from each other (no-op source helpers).
- Scaling path: To support small multiples or comparison with other regions, rebuild the chart to: (a) own its d3 state per instance, (b) actually use the `sourceColors`/`sourceWidths` maps, (c) accept a legend or render its own.

## Dependencies at Risk

**`vue-router` listed as top-level dependency at `^5.0.4`:**
- Risk: Nuxt 4 manages vue-router internally. A direct `"vue-router": "^5.0.4"` in `package.json` can conflict with Nuxt's bundled version and causes duplicate module resolution warnings. Also, vue-router 5 is a newer major that may not match Nuxt 4's expected 4.x line.
- Files: `package.json` (line 20)
- Impact: Works today; silent breakage or version drift risk on upgrade.
- Migration plan: Remove the explicit `vue-router` dependency unless you need a specific feature from it. Let Nuxt pin the correct version.

**`@nuxt/eslint` and `@nuxtjs/tailwindcss` listed under `dependencies` not `devDependencies`:**
- Risk: Ship into production bundle metadata and grow install size on the server image. Not a runtime correctness issue.
- Files: `package.json` (lines 13–14)
- Impact: Slower installs in CI; confusing for auditors.
- Migration plan: Move to `devDependencies`.

**No lockfile strategy for the Python pipeline:**
- Risk: `scripts/extend_gdp.py` imports `pandas` but there is no `requirements.txt`, `pyproject.toml`, or `uv.lock` in the repo. The script also references inputs (`roseswolf_regionalgdp_v7.xlsx`, `eurostat_nama_10r_2gdp.csv`, `nuts_correspondence.csv`) that are not in the repo.
- Files: `scripts/extend_gdp.py` (lines 11, 532–544)
- Impact: CSV output is not reproducible from a clean clone.
- Migration plan: Add `scripts/requirements.txt` with pinned pandas/openpyxl versions (and anything else it imports). Document where the three raw inputs come from in a sidecar README or at the top of the script.

## Missing Critical Features

**No accessibility affordances on the SVG chart:**
- Problem: The chart `<svg>` has no `role`, no `aria-label`, no `aria-labelledby`, no `<title>` or `<desc>` child. Data points carry only mouse handlers (`mouseenter`/`mousemove`/`mouseleave`) — no `focus`/`blur`, no `tabindex`, no keyboard navigation, no touch events.
- Blocks: Screen-reader users cannot access the data. Keyboard-only users cannot inspect values. Touch users can sometimes trigger tooltips via emulated mouseenter but cannot dismiss them cleanly.
- Files: `app/components/line-chart.vue` (line 2 svg; lines 315–329 points).

**No linear/text fallback for the narrative:**
- Problem: The entire story is driven by scroll-step animation. Users with `prefers-reduced-motion`, screen readers, or assistive tech that can't scroll sequentially see the narrative text but the chart only reflects step 0 (1900–1910).
- Blocks: Equitable access to the full argument; SEO extraction of the peak/trough numbers.
- Files: `app/components/story-page.vue` (figure section lines 169–217).

**Catalan label without `lang` attribute:**
- Problem: "PIB per Càpita" is Catalan; the rest of the page is English. The document has no `<html lang>` override and this label has no `lang="ca"` wrapper.
- Blocks: Screen readers mispronounce; crawler language detection gets confused.
- Files: `app/components/story-page.vue` (line 178).

**No error/empty states for CSV fetch failures:**
- Problem: `useFetch` returns `data`, `error`, `pending` but only `data` is consumed. If the CSV 404s or returns malformed content, the chart silently renders empty.
- Blocks: Debugging; user trust.
- Files: `app/components/story-page.vue` (lines 379–381, 383–394).

**No `<html lang>` attribute set via Nuxt head:**
- Problem: `nuxt.config.ts` does not set `app.head.htmlAttrs.lang`. Nuxt defaults to no value.
- Blocks: Accessibility, SEO.
- Files: `nuxt.config.ts` (lines 6–24).

**No Open Graph / Twitter Card metadata:**
- Problem: No `og:title`, `og:description`, `og:image`, `twitter:card` meta tags. For a shareable data-journalism piece, social previews will be blank.
- Blocks: Social reach.
- Files: `nuxt.config.ts`; none of the pages set `useSeoMeta`/`useHead`.

**Compiled Python bytecode committed-adjacent (`.pyc` untracked in working tree):**
- Problem: `scripts/__pycache__/extend_gdp.cpython-314.pyc` exists in the working directory. `.gitignore` does not list `__pycache__/` or `*.pyc`.
- Blocks: Risk of accidental commit of binary artifacts.
- Files: `.gitignore`.

## Test Coverage Gaps

**No test infrastructure:**
- What's not tested: Everything. No `vitest.config.*`, `jest.config.*`, `*.test.*`, `*.spec.*`, `cypress/`, or `playwright.config.*` files exist.
- Files: entire repo.
- Risk: Chart regressions (off-by-one years, tooltip math, scale inversion), scrollama wiring bugs, and CSV parsing regressions will be caught only by manual scroll-through. The `yearToDate(y, 0, 0)` bug documented above would have been caught by a single assertion.
- Priority: High for the chart math (`yearToDate`, `showTooltip` positioning), medium for scroll wiring, low for visual presentation.

**No tests for the Python pipeline:**
- What's not tested: `scripts/extend_gdp.py` — a 600-line chain-linking pipeline with seven sanity checks, unit guards, and anchor arithmetic. The checks are self-validating at runtime but there are no fixture-based tests for the parser functions (`normalize_columns`, `parse_number`, `melt_wide_years`, `identify_code_column`, `identify_year_value_columns`, `enforce_eurostat_unit_guard`).
- Files: `scripts/extend_gdp.py`.
- Risk: Silent CSV format drift from upstream (Eurostat/Rosés-Wolf) breaks the pipeline at the next regeneration.
- Priority: Medium — the script has defensive guards, but unit tests around column detection and the anchor-year seam would pay off at the next data update.

**No CI running type checks or lint:**
- What's not tested: TypeScript types and ESLint rules are configured (`@nuxt/eslint`, `eslint.config.mjs`) but there is no `lint`/`typecheck` script in `package.json` and no GitHub Actions workflow.
- Files: `package.json` (lines 5–11); no `.github/workflows/`.
- Risk: `as any` escapes, missing null checks, and unused imports accumulate.
- Priority: Medium — add `"lint": "eslint ."` and `"typecheck": "nuxt typecheck"` scripts and a simple CI workflow.

---

*Concerns audit: 2026-04-23*
