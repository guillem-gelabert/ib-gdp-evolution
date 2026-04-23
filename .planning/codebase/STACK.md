# Technology Stack

**Analysis Date:** 2026-04-23

## Languages

**Primary:**
- TypeScript (via Nuxt's generated `tsconfig.*.json` references in `tsconfig.json`) — used for Vue SFC `<script setup lang="ts">` blocks (`app/components/line-chart.vue`, `app/components/story-page.vue`) and config (`nuxt.config.ts`, `tailwind.config.ts`).
- Vue 3 SFC (`.vue`) — the entire UI layer (`app/app.vue`, `app/pages/index.vue`, `app/components/*.vue`).

**Secondary:**
- Python 3 — offline data pipeline only, not runtime (`scripts/extend_gdp.py`, shebang `#!/usr/bin/env python3`, uses `pandas`).
- JavaScript (ESM, `.mjs`) — ESLint config (`eslint.config.mjs`).

## Runtime

**Environment:**
- Node.js — required by Nuxt 4 (no `.nvmrc` or `engines` field declared in `package.json`; pnpm lockfile records dependencies requiring `node >= 20`).
- Nitro server runtime — bundled by Nuxt (inferred from `.gitignore` entries `.nitro`, `.output`).

**Package Manager:**
- pnpm (workspace configured via `pnpm-workspace.yaml`, lockfile `pnpm-lock.yaml` at `lockfileVersion: '9.0'`).
- Lockfile: present (`pnpm-lock.yaml`).

## Frameworks

**Core:**
- `nuxt` ^4.4.2 — full-stack Vue meta-framework (`nuxt.config.ts`). `compatibilityDate: "2025-07-15"`.
- `vue` ^3.5.32 — UI rendering (composition API with `<script setup>`).
- `vue-router` ^5.0.4 — routing (implicit via Nuxt file-based routing: `app/pages/index.vue`).

**Testing:**
- Not detected. No `jest.config.*`, `vitest.config.*`, or `*.test.*` / `*.spec.*` files in the repository.

**Build/Dev:**
- Vite 7.x — bundler used by Nuxt (configured in `nuxt.config.ts` under `vite: { optimizeDeps: { exclude: ["d3"] } }`).
- `@nuxt/eslint` 1.15.2 — ESLint integration; generated config consumed via `./.nuxt/eslint.config.mjs` in `eslint.config.mjs`.
- `@nuxtjs/tailwindcss` 6.14.0 — Tailwind CSS Nuxt module (registered in `nuxt.config.ts` `modules`).

## Key Dependencies

**Critical:**
- `d3` ^7.9.0 — SVG chart rendering for the GDP line chart (`app/components/line-chart.vue`: `d3.scaleTime`, `d3.scaleLinear`, `d3.line`, `d3.axisLeft`, `d3.transition`, `d3.format`). Excluded from Vite dep optimization in `nuxt.config.ts`.
- `@types/d3` ^7.4.3 — TypeScript typings for d3.
- `scrollama` ^3.2.0 — scrollytelling step tracking (`app/components/story-page.vue`: `import scrollama from "scrollama"`).

**Infrastructure:**
- `@nuxt/eslint` 1.15.2 — linting integration.
- `@nuxtjs/tailwindcss` 6.14.0 — utility CSS integration.

**Python (pipeline, not runtime):**
- `pandas` — CSV/Excel ingestion and chain-linking transforms (`scripts/extend_gdp.py`: `pd.read_csv`, `pd.read_excel`).

## Configuration

**Environment:**
- No `.env` files present. `.gitignore` allows only `.env.example` (not present).
- No `useRuntimeConfig()` usage detected in `app/`. No runtime secrets or env-driven feature flags.
- Build is fully static/client-side: data is loaded from `public/data/*.csv` via `useFetch`.

**Build:**
- `nuxt.config.ts` — Nuxt modules, head `<link>` preconnect + Google Fonts stylesheet, Vite `optimizeDeps` exclusion for d3, devtools enabled.
- `tailwind.config.ts` — theme extension with custom editorial color palette (`cream`, `ink`, `accent`, etc.) and font families (`Instrument Serif`, `DM Mono`, `Literata`, `Source Sans 3`).
- `tsconfig.json` — delegates to Nuxt-generated `./.nuxt/tsconfig.{app,server,shared,node}.json` via `references`.
- `eslint.config.mjs` — flat config, wraps Nuxt's generated config with `withNuxt()`.
- `pnpm-workspace.yaml` — declares `ignoredBuiltDependencies: [@parcel/watcher, esbuild, unrs-resolver]`.

## Platform Requirements

**Development:**
- Node.js (>=20 per transitive dep `@parcel/watcher`).
- pnpm (install via `pnpm install`).
- Dev server: `pnpm dev` (`nuxt dev`) on `http://localhost:3000`.
- Optional: Python 3 + `pandas` for regenerating CSVs via `scripts/extend_gdp.py`.

**Production:**
- Static site generation target via `pnpm generate` (`nuxt generate`) — all data lives under `public/data/` so the app can be deployed as static HTML/JS to any static host. `nuxt build` + `nuxt preview` also available.
- No hosting platform configuration committed (no `vercel.json`, `netlify.toml`, `Dockerfile`, etc.).

## Scripts

Defined in `package.json`:
```bash
pnpm dev         # nuxt dev
pnpm build       # nuxt build
pnpm generate    # nuxt generate (static export)
pnpm preview     # nuxt preview
# postinstall: nuxt prepare (regenerates .nuxt/)
```

---

*Stack analysis: 2026-04-23*
