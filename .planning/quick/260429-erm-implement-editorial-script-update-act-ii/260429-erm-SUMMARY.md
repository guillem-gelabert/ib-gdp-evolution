# Quick Task 260429-erm: Implement Editorial Script — Summary

**Completed:** 2026-04-29
**Commit:** c52c96a

## What Changed

### Act II Chart — Arrivals Line (act2-chart.vue)
- Added `arrivalsData`, `arrivalsYDomain`, and `showArrivals` props
- Renders a blue (`#1f6feb`) secondary line on its own y-scale (right axis with M-formatted ticks)
- Arrivals path renders beneath GDP comparison lines for correct z-order
- End-label "Tourist arrivals" appended to the label set when arrivals visible
- Arrivals line is unaffected by the real-eur → pct-eu15 axis switch (always absolute scale)

### Act II Story Copy & Configs (act2-story-section.vue)
- Replaced 10 steps with 9 steps matching script's Steps 8-16
- Copy now follows the editorial script verbatim: The Question → Extremadura Enters → The Shape Is the Same → And Not Just Extremadura → The Pivot → The Axis Switch → The Scissors → Peers Continue → The Hinge
- Each config now includes `showArrivals: true`
- Fetches `tourist_arrivals.csv` and passes parsed arrivals + y-domain to `act2-chart`

### Act III Prose (story-page.vue)
- New `#act3` section with "Why?" heading
- Five hypothesis bullets: Baumol productivity ceiling, monoculture risk, low-wage lock-in, Spanish productivity stagnation, island constraints
- Italicized editorial disclaimer at bottom

### Act IV Prose (story-page.vue)
- New `#act4` section — "The Granddaughter Returns"
- Three paragraphs closing the narrative arc (grandmother, continental story, tourism-as-shape)
- Positioned between Act III and Data & Methods

## Files Modified
- `app/components/act2-chart.vue` — arrivals rendering
- `app/components/act2-story-section.vue` — copy, configs, data fetching
- `app/components/story-page.vue` — Act III + IV sections

## Not Changed
- Act I (story-page.vue scroll steps and opening prose) — preserved as-is per instruction
- line-chart.vue — no changes needed
- Data files — existing CSVs used directly
