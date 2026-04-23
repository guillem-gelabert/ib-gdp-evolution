---
title: "Act II — Datastory Implementation Decisions"
date: 2026-04-23
context: "Pre-v2.0 milestone exploration — crystallized from /gsd-do → /gsd-explore session"
source: "act2.md (narrative spec, Steps 8–17)"
---

# Act II — Datastory Implementation Decisions

Captured during Socratic exploration before kicking off milestone v2.0. These decisions
should be treated as locked inputs by the downstream `/gsd-new-milestone`, requirements,
and roadmap phases — they have been explicitly confirmed by the user.

## 1. Narrative spec

Authoritative narrative: `act2.md` (repo root), Steps 8–17.

Core argument: *"The climb was common, the fall is ours."* Act II reveals that IB's
post-1960 GDP-per-capita climb was continental, not tourism-specific, and that IB is
one of the few European regions that peaked (~1990) and then drifted down relative to
the EU average.

**Rhetorical hinges (do not lose in implementation):**

- Extremadura is the primary comparison — the argument "rests almost entirely" on it
  (see craft notes in `act2.md`).
- The Step 13 axis switch ("real €" → "% of EU-15 average, EU-15 = 100") is described
  as "the single most important chart transition in the piece." It must be a held,
  choreographed moment.
- The piece ends on observation, not explanation. No "why" in Act II.

## 2. Milestone framing

- **New milestone:** `v2.0` (not a phase appended to `v1.0`).
- **Phase outline (subject to refinement in `/gsd-new-milestone`):**
  1. Data pipeline extension (peer regions/countries + EU-15 reference)
  2. Act II chart component (multi-line, two axis modes, choreography primitives)
  3. Act II scrollytelling (Steps 8–17, pre-loaded data, step-driven state machine)

## 3. Data — chain-linking

- **Anchor year:** `2020` (NOT the current `extend_gdp.py` value of 2022).
  - Implication: IB's existing `public/data/balearic_ine_chainlinked_gdp_pc.csv` must be
    regenerated on the 2020 anchor for seam consistency across all series.
- **Seam:** RW 1900–1999, institutional data 2000+.
  - Countries → Eurostat (CLV chain-linked real volume; guard in `extend_gdp.py`).
  - Spanish regions → INE (chain-linked, same methodology as existing IB series).
- **Reuse:** extend `scripts/extend_gdp.py` rather than forking. Expected deltas:
  - Parameterize `ANCHOR_YEAR` (or change constant to 2020 + regenerate all).
  - Support non-NUTS2 series identifiers (country ISO codes for IE/PT/MT; INE codes
    for ES41/ES43/ES45 etc.).
  - Accept multiple institutional data inputs (Eurostat + INE) in one run, matched
    per series by source.
- **Sanity checks kept:** seam continuity, growth-rate preservation, gap detection,
  outlier guard, level plausibility, Eurostat CLV unit guard.

## 4. Data — peer set (locked)

From `act2.md`, explicitly named:

| Series              | Scope         | RW code (expected) | Post-2000 source |
|---------------------|---------------|--------------------|------------------|
| Balearic Islands    | Spanish NUTS2 | ES53               | INE              |
| Extremadura         | Spanish NUTS2 | ES43               | INE              |
| Galicia             | Spanish NUTS2 | ES11               | INE              |
| Castilla-La Mancha  | Spanish NUTS2 | ES42               | INE              |
| Portugal            | Country       | PT                 | Eurostat         |
| Ireland             | Country       | IE                 | Eurostat         |
| Malta               | Country       | MT                 | Eurostat         |

- Extremadura is primary; Galicia + Castilla-La Mancha are fallbacks/amplifiers per
  craft notes.
- Ireland is optional narratively but rhetorically useful (proves post-1990 climbing
  was possible). Keep it unless data is awkward.
- Malta is rhetorical ballast; retain.

## 5. Data — EU-15 reference

- **Construction:** GDP-weighted per-capita average across the 15 EU-15 member
  countries (BE, DK, DE, IE, GR, ES, FR, IT, LU, NL, AT, PT, FI, SE, UK).
  - Composition is held constant across the whole 1900–2024 window (we're using
    EU-15 as an analytical benchmark, not modelling membership dates).
- **Computation:** `sum(per_capita_i × population_i) / sum(population_i)` per year.
- **Implementation:** Python, same pipeline as peer series. Pre-2000 from RW +
  population source (RW population if present, otherwise Maddison/PWT — to be
  resolved in Phase 1). Post-2000 Eurostat publishes EU-15 aggregate directly.
- **Role in chart:** appears as a secondary line in "real €" mode; in Step 13 it
  animates/flattens into the horizontal y=100 baseline as the axis re-scales to
  "% of EU-15 average."

## 6. Chart component

- **New component** — do NOT extend `app/components/line-chart.vue`.
  - Shared utilities (Perlin-noise line distortion, arrowhead marker, D3 axis
    helpers) may be extracted into a `composables/` or `utils/` module for reuse,
    but Act II renders its own SVG structure.
- **Supports:**
  - N peer lines + IB line + EU-15 reference, with independent fade/highlight state
  - Two axis modes: `real-eur` and `pct-eu15` (EU-15 = 100)
  - Animated transition between modes where:
    - The EU-15 line morphs to the horizontal y=100 baseline
    - All other lines re-scale in the same tween
  - Step-driven visibility/highlighting (which lines are in color, which are gray)

## 7. Scrollytelling

- **Pre-load** all peer series + EU-15 reference on component mount. No lazy loading.
- **Steps 8–17** from `act2.md` map to scrollama steps; each step emits a state that
  the chart consumes (active lines, highlighted line, axis mode, annotations).
- **Axis transition** at Step 13 is itself a scroll step (not a user toggle) — a
  single held moment with a longer dwell than surrounding steps.
- **Peak-and-drift shading** (Step 15: "A shaded band marks 'peak.'") — treat as a
  chart annotation primitive, not a hard-coded overlay.

## 8. Out of scope for v2.0

- No "why" narrative (Act III territory per craft notes).
- No user-driven axis toggle (scroll-only).
- No backfilling of IB Act I chart changes beyond the 2020-anchor regeneration.
- No new data sources beyond RW + Eurostat + INE + (population source TBD for EU-15).

## 9. Open items for milestone kickoff

These are not blockers but must be resolved by the end of Phase 1 planning:

- Population data source for EU-15 weighting (RW vs. Maddison vs. PWT).
- Precise INE table / Eurostat dataset IDs for 2000+ data ingestion.
- Whether to keep the 2022-anchor IB file as a legacy artifact or replace it
  in-place.
- Exact styling treatment for the "peak" shaded band in Step 15.

---
*Captured: 2026-04-23 via /gsd-explore.*
