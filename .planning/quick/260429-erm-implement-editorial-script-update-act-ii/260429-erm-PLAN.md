# Quick Task 260429-erm: Implement Editorial Script

**Created:** 2026-04-29
**Status:** Ready

## Goal

Align the scrollytelling site with the editorial script in `balearic-tourism-story.md`. Act I (story-page.vue's 12 scroll steps + opening prose) stays as-is. The work is:

1. Update Act II copy and chart configs to match script steps 8-16
2. Add tourist arrivals line to Act II chart (the "scissors" visual)
3. Add Act III prose section (hypotheses, no chart)
4. Add Act IV closing prose section (no chart)

## Plan 1: Implement Editorial Script

### Task 1: Add arrivals line to Act II chart

**Files:** `app/components/act2-chart.vue`, `app/components/act2-story-section.vue`
**Action:**
- In `act2-story-section.vue`: fetch `tourist_arrivals.csv`, parse it, compute a sliced arrivals array based on active step config, pass as prop to `act2-chart`
- In `act2-chart.vue`: accept `arrivalsData` and `arrivalsYDomain` props, add a right-side y2 axis and blue arrivals path, render it underneath the GDP lines
- Each step config gains `showArrivals: boolean` (true from step 0 onward)
- Arrivals line always uses absolute y-scale (not affected by pct-eu15 axis switch)

**Verify:** Arrivals line renders in blue alongside GDP lines in Act II
**Done:** Arrivals line visible in Act II chart from first step, persists through axis switch

### Task 2: Update Act II copy and step configs

**Files:** `app/components/act2-story-section.vue`
**Action:**
- Replace `act2Steps` array with 9 steps matching script's Steps 8-16
- Update `act2Configs` to match the script's per-step visibility:
  - Step 0 (script 8): IB only + arrivals
  - Step 1 (script 9): IB + Extremadura + arrivals
  - Step 2 (script 10): IB highlight + Extremadura + arrivals
  - Step 3 (script 11): All peers visible + arrivals
  - Step 4 (script 12): All peers muted, IB highlight + arrivals
  - Step 5 (script 13): Axis switch to pct-eu15, all visible + arrivals
  - Step 6 (script 14): The scissors — IB highlight, peak band, arrivals prominent
  - Step 7 (script 15): Selected peers return (Ireland highlight) + arrivals
  - Step 8 (script 16): Strip to IB only + eu15 ref + arrivals

**Verify:** Scrolling through Act II shows correct copy and chart transitions per step
**Done:** 9 steps with copy matching the script

### Task 3: Add Act III and Act IV prose sections

**Files:** `app/components/story-page.vue`
**Action:**
- After `<act2-story-section />`, add Act III section: a short prose section with 5 bullet hypotheses (Baumol, monoculture, low-wage lock-in, Spanish productivity stagnation, island constraints)
- After Act III, add Act IV section: the "Granddaughter Returns" closing prose (3 paragraphs from the script)
- Move Data & Methods section and footer to remain at the bottom

**Verify:** Act III and IV render as prose sections between Act II and the footer
**Done:** Both sections present with correct copy
