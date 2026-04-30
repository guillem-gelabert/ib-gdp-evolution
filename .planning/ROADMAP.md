# Roadmap: IB GDP Evolution

## Milestones

- ✅ **v1.0 Act I Chart Upgrade** — Phase 1 shipped 2026-04-23. Snapshot in `.planning/milestones/v2.0-ROADMAP.md`.
- ✅ **v2.0 Act II — Who Else Got Richer** — Phases 2-4 shipped 2026-04-23 in documented local-proxy mode. Archive: `.planning/milestones/v2.0-ROADMAP.md`.
- ✅ **v3.0 Full Act II ETL** — Phase 5 shipped 2026-04-30. Archive: `.planning/milestones/v3.0-ROADMAP.md`.
- 📋 **Next milestone** — TBD (run `/gsd-new-milestone` to start)

## Phases

<details>
<summary>✅ v3.0 Full Act II ETL (Phase 5) — SHIPPED 2026-04-30</summary>

- [x] Phase 5: Full Act II ETL (3/3 plans) — completed 2026-04-29

Replaced the `--act2-local-proxy` data path with a data-lake-backed Eurostat pipeline. Ingested 3 Eurostat datasets, built an adapter layer with API fallback, chain-linked all 7 series to Rosés-Wolf at 2019, and emitted `public/data/act2_*.csv` with 8/8 sanity checks PASS and baseline-regression correlation = 1.0000.

</details>

## Progress

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 5. Full Act II ETL | v3.0 | 3/3 | Complete | 2026-04-29 |

---
*Last updated: 2026-04-30 — v3.0 Full Act II ETL shipped and archived*
