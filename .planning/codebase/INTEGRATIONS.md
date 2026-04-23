# External Integrations

**Analysis Date:** 2026-04-23

## APIs & External Services

**Fonts (runtime, browser):**
- Google Fonts — stylesheet and font files loaded from `fonts.googleapis.com` / `fonts.gstatic.com` with preconnect hints.
  - Location: `nuxt.config.ts` `app.head.link` — fetches `Instrument Serif`, `DM Mono`, `Literata`, `Source Sans 3`.
  - SDK/Client: Plain `<link rel="stylesheet">` (no SDK).
  - Auth: None (public CDN).

**No other runtime third-party APIs detected.** No Stripe, Supabase, Firebase, AWS, Sentry, PostHog, Analytics, or similar SDKs in `package.json` or under `app/`.

## Data Storage

**Databases:**
- None. The app has no backend persistence layer.

**File Storage (static assets served by Nuxt):**
- Local filesystem only — CSV datasets shipped in `public/data/`:
  - `public/data/balearic_gdp_pc.csv` — primary dataset consumed at runtime by `app/components/story-page.vue` (`useFetch("/data/balearic_gdp_pc.csv")`). Schema: `year,gdp_pc,source,unit`. Spans 1900–2024 combining Rosés–Wolf historical series (`RW`) and INE chain-linked modern series.
  - `public/data/balearic_ine_chainlinked_gdp_pc.csv` — intermediate INE chain-linked output. Schema: `series,year,value,unit,method`.
  - `public/data/balearic_ine_gdp_pc_datalake.csv` — raw INE GDP per capita extracted from the external data-lake. Schema: `series,year,value,unit,source_note` (e.g., `INE CRE 2024 from data-lake source 01KPVCVSTJQZDPAVR8E975SCE3`).
  - `public/data/roses_wolf_selected_comparison.csv` — selected Rosés & Wolf historical GDP-pc comparison (~192 rows). Schema: `series,year,value,unit`.

**Caching:**
- None (no Redis, no SWR config, no Nitro storage overrides).

## Authentication & Identity

**Auth Provider:**
- None. The site is a public static story/dataviz; no login, sessions, or user state.

## Monitoring & Observability

**Error Tracking:**
- None detected.

**Logs:**
- Browser `console` only (no structured logging library).

## CI/CD & Deployment

**Hosting:**
- Not declared in repo. The `nuxt generate` script (`package.json`) indicates static deployment is intended.

**CI Pipeline:**
- None detected (no `.github/workflows/`, `.gitlab-ci.yml`, `circle.yml`, etc.).

## Environment Configuration

**Required env vars:**
- None. No `useRuntimeConfig`, no `process.env` references in `app/`, no `.env*` files committed (`.gitignore` lists `.env`, `.env.*` with `!.env.example` allowlisted, but `.env.example` is absent).

**Secrets location:**
- Not applicable at app runtime.
- `.cursor/mcp.json` (developer-only, not shipped) contains a Cursor MCP `X-Goog-Api-Key` header for the `stitch` MCP server — this is IDE tooling configuration, not an app runtime integration. Not imported by `app/` or `scripts/`.

## Webhooks & Callbacks

**Incoming:**
- None. App is static; no server routes defined (`server/` directory absent).

**Outgoing:**
- None.

## Static Data Pipeline (offline, developer-run)

**Script:** `scripts/extend_gdp.py` (Python 3, uses `pandas`).

**Inputs (read from local filesystem):**
- Looks in `workspace/data/` and `workspace/public/data/` (`find_input_file` in `scripts/extend_gdp.py`).
- Reads CSV/XLSX via `pd.read_csv` / `pd.read_excel`.

**External data provenance (not fetched by the script — pre-exported):**
- **INE (Instituto Nacional de Estadística, Spain)** — CRE 2024 GDP per capita series, sourced via the external `data-lake` project (referenced as `INE CRE 2024 from data-lake source 01KPVCVSTJQZDPAVR8E975SCE3` in `public/data/balearic_ine_gdp_pc_datalake.csv`).
- **Rosés & Wolf** — historical Spanish regional GDP-pc dataset (1860–2015), used for the pre-2000 Balearic series (`public/data/roses_wolf_selected_comparison.csv`).

**External tooling dependencies (developer workstation only):**
- `data-lake` — local MCP server at `/Users/guillem/vault/projects/personal/data-lake` (referenced in `.cursor/mcp.json`). Used by the developer via Cursor to extract INE source data; not invoked by the app or by `scripts/extend_gdp.py`.

**Outputs:**
- Writes back into `public/data/` (consumed directly by the browser at runtime).

## Runtime Data Fetching

**Client-side:**
- Single fetch in `app/components/story-page.vue:379`:
  ```ts
  const { data: gdpCsv } = await useFetch("/data/balearic_gdp_pc.csv", { ... });
  ```
  Parsed with `csvParse` from `d3` (`import { csvParse, extent as d3Extent } from "d3"`).

---

*Integration audit: 2026-04-23*
