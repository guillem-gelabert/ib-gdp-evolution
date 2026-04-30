# Phase 3: Act II Chart Component - Context

**Gathered:** 2026-04-23
**Status:** Executed

## Boundary

Build a new Act II comparison chart that can:

- render multiple peer lines
- switch between real EUR and `% of EU-15`
- animate the axis transition
- reuse Act I editorial styling instead of duplicating it

## Decision

Use local-proxy Act II CSVs generated in Phase 2 so the chart can ship without fabricating a full ETL completion state.
