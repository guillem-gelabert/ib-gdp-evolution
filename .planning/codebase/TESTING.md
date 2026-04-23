# Testing Patterns

**Analysis Date:** 2026-04-23

## Test Framework

**Runner:**
- None installed. No test runner, no test files.
- `package.json` declares no test-related dependencies (no Vitest, Jest, Playwright, Cypress, `@vue/test-utils`, `@nuxt/test-utils`, `happy-dom`, or `jsdom`).
- No test config files exist (no `vitest.config.*`, `jest.config.*`, `playwright.config.*`, `cypress.config.*`).

**Assertion Library:**
- Not applicable.

**Run Commands:**
- No `test` script in `package.json`. Available scripts are limited to Nuxt lifecycle:

```bash
pnpm dev           # Run dev server
pnpm build         # Build for production
pnpm generate      # Static site generation
pnpm preview       # Preview built site
pnpm postinstall   # nuxt prepare (runs automatically)
```

## Test File Organization

**Location:**
- Not applicable. A repo-wide search for `*.test.*` and `*.spec.*` (excluding `node_modules`) returns zero files.

**Naming:**
- Not established.

**Structure:**
- Not established.

## Test Structure

Not applicable — no tests exist.

## Mocking

Not applicable — no tests exist.

## Fixtures and Factories

**Test Data:**
- Not applicable.

**Production data fixtures (not tests, but related):**
- Static CSVs live in `public/data/` and are loaded at runtime via `useFetch("/data/...")`:
  - `public/data/balearic_gdp_pc.csv` — canonical series consumed by `app/components/story-page.vue`
  - `public/data/balearic_ine_chainlinked_gdp_pc.csv`
  - `public/data/balearic_ine_gdp_pc_datalake.csv`
  - `public/data/roses_wolf_selected_comparison.csv`
- Data-prep scripts in `scripts/` (e.g. `scripts/extend_gdp.py`) are manual-run Python utilities, not tests.

## Coverage

**Requirements:** None enforced. No coverage tooling configured.

**View Coverage:**
- Not applicable.

## Test Types

**Unit Tests:**
- None.

**Component Tests:**
- None. `@vue/test-utils` and `@nuxt/test-utils` are not installed.

**Integration Tests:**
- None.

**E2E Tests:**
- None. No Playwright or Cypress setup.

**Visual / Snapshot Tests:**
- None.

## Manual Verification Workflow

Current quality signal relies on:
- **TypeScript** via `nuxt prepare` (generated tsconfig references in `tsconfig.json`) — catches type errors at build time
- **ESLint** via `@nuxt/eslint` module (`eslint.config.mjs`) — no dedicated `lint` script; runs through editor integration and `nuxt prepare`
- **Manual browser verification** of the scrollytelling interaction in `app/components/story-page.vue` against D3 rendering in `app/components/line-chart.vue`
- **Build success** via `pnpm build` / `pnpm generate` as implicit smoke test

## Common Patterns

Not applicable — no tests exist.

## Notes for Adding Tests

If tests are introduced later, recommended starting points for this Nuxt 4 + Vue 3 + D3 project:

- **Unit/component:** Vitest + `@nuxt/test-utils` + `happy-dom` — Nuxt's first-party testing stack; integrates with the auto-import system
- **File placement:** Co-locate as `*.test.ts` next to the component (e.g. `app/components/line-chart.test.ts`) or under a top-level `tests/` directory
- **D3-heavy components:** Prefer testing pure helpers (`yearToDate`, `pointRadius`, `sourceColor` in `app/components/line-chart.vue`) by extracting them to a separate module; full SVG rendering assertions are brittle
- **E2E:** Playwright against the scrollytelling flow in `app/components/story-page.vue`, driving `scrollama` step transitions and asserting chart data slices
- Add a `test` script to `package.json` before introducing any test file

---

*Testing analysis: 2026-04-23*
