# Phase 2: Data Pipeline Extension (v2.0) — Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-04-23
**Phase:** 02-data-pipeline-extension-v2-0
**Areas discussed:** EU-15 population source, INE format for Spanish peers, IB file handling, output CSV layout

---

## EU-15 Population Source (pre-2000)

| Option | Description | Selected |
|--------|-------------|----------|
| RW Excel internal | Extract population from `roseswolf_regionalgdp_v7.xlsx` directly | ✓ |
| Maddison Project | Download Maddison country population 1820-2018 separately and join | |
| Skip weighting pre-2000 | Use unweighted mean of EU-15 per-capitas | |

**User's choice:** RW Excel includes population — extract from `roseswolf_regionalgdp_v7.xlsx`
**Notes:** Keeps the EU-15 weighting internally consistent with the same source used for per-capita GDP values pre-2000.

---

## INE Format for Spanish Peer Regions

| Option | Description | Selected |
|--------|-------------|----------|
| Pre-downloaded local files | Script reads from local directory; recommend combined Spain Excel | ✓ |
| URL download at runtime | Script fetches from INE API or direct URL | |
| Combined Spain Excel | INE offers one file with all CCAA | (part of pre-downloaded) |

**User's choice:** "I don't know" — assistant resolved to pre-downloaded local files following existing pipeline convention
**Notes:** INE `cid=1254736167628` offers combined Spain Excel with all CCAA. Same `load_ine_excel` parsing as current IB pipeline. User to pre-download and place in input directory.

---

## IB File Handling

| Option | Description | Selected |
|--------|-------------|----------|
| Replace in-place | `balearic_gdp_pc.csv` becomes 2020-anchor; Act I reads same file | |
| New file for Act II | Keep Act I file as 2022-anchor; new `act2_*.csv` files for Act II | ✓ |
| Act II file only | Don't touch `balearic_gdp_pc.csv` at all | |

**User's choice:** "Use same chain-linking method/strategy/anchors as in the current implementation for act 1" — interpreted as: don't modify Act I files; Act II gets its own separately anchored series.
**Notes:** `balearic_gdp_pc.csv` remains untouched. IB is recomputed at 2020 anchor and written as `act2_balearic_islands.csv`.

---

## Output CSV Layout

| Option | Description | Selected |
|--------|-------------|----------|
| Single combined file | All 8 series in one tidy CSV; chart loads one file | |
| One CSV per series | Separate file per series; chart fetches in parallel | ✓ |
| Both | Combined + individual files | |

**User's choice:** Separate files (one per series)
**Notes:** File schema `year,gdp_pc,source,unit` matches existing `balearic_gdp_pc.csv` for consistency.

---

## Claude's Discretion

- Internal structure of `load_roseswolf_population()` function
- Whether to generate a combined manifest/index file alongside per-series CSVs
- Interpolation strategy for decadal RW values in EU-15 weighting

## Deferred Ideas

- Runtime INE API fetching
- `--series` selective rebuild CLI flag
- Validation dashboard from sanity checks
