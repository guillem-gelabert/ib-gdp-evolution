# Milestones

## v2.0 — Act II: Who Else Got Richer

- **Status:** Shipped 2026-04-23, archived 2026-04-27
- **Scope:** 4 phases, 9 plans, 2 shipped story acts in the repo
- **Archive:** `.planning/milestones/v2.0-ROADMAP.md`, `.planning/milestones/v2.0-REQUIREMENTS.md`, `.planning/milestones/v2.0-MILESTONE-AUDIT.md`

**Key accomplishments:**

1. Upgraded the Act I chart with hidden points, nearest-x hover, editorial line distortion, marker endcap, and an 800 ms reveal.
2. Added a shipped Act II local-proxy data pipeline that emits the comparison CSV set needed by the frontend.
3. Built a dedicated Act II comparison chart with multi-line rendering, per-series state, and animated real-euro to EU-15-relative axis transitions.
4. Integrated Act II into the story flow as a separate scrollama scene with preloaded datasets and narrative choreography for Steps 8-17.
5. Verified the shipped scope with `pnpm generate` and `python3 scripts/extend_gdp.py --act2-local-proxy`.

**Known gaps carried forward:**

- Browser-based UAT for the full Act I + Act II reading flow is still manual.
- Full raw-input ETL support for Act II remains deferred behind missing upstream inputs.
- GSD CLI milestone parsing still disagrees with the now-archived artifact state in this repo.
