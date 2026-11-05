# ADR-011 — Deterministic multi-day scheduling with Google OR-Tools over a cached Google Routes matrix

| Field | Value |
|---|---|
| Status | Accepted by the owner (SRC-100 A-021, A-028; SRC-105 A-035); mentor review at M0 [Pending] |
| Date | 2026-11-04 (0.3: 2026-11-06) |
| Version | 0.3 (0.2 → 0.3: DEC-016 per-date effective windows from calendar rules, new conflict types, web candidates in the pool, pairwise Routes cache with fixed anchors) |
| Owner / decider | Lê Ngọc Tấn Hiền |
| Approver | trantrongminh, FYP mentor ([Pending]) |
| Decision source | DEC-008, DEC-011 (SRC-100); DEC-015, DEC-016, DEC-018 (SRC-105) |

## Context

Stops need a day, an order and times that respect opening hours, closures on the trip dates and the day window,
with leg values from Google Routes only. Calendar errors (weekly closures, Tết, lunar lantern nights, same-day
tickets) are the most common competitor fault. Routes elements are the fastest-exhausted free quota. The LLM only
selects and writes (A-035).

## Decision

- **Pool.** Published places of the enabled city selected by the `selector` (ADR-013) plus this request's
  `web_place_candidates` that passed `places_check` (ADR-014). Visit durations come from the catalog bounds, the
  traveler's edits or a default for web candidates.
- **Effective windows.** For each (place, date) the calendar module expands `place_closure_rules` (WEEKLY, DATE,
  LUNAR_DATE, SEASON, TICKET_VALIDITY; effects CLOSED, PARTIAL, EVENT, NOTICE) and intersects the result with the
  opening-hours fact and the day window. UNKNOWN hours → day window only, later a warning.
- **Routing.** Pairwise `routes_matrix_cache(from, to, mode)` 30 d; only misses are fetched. Day starts are fixed
  anchors (never user GPS). WALK is requested only for pairs ≤ 2.5 km. Unavailable pairs are marked, never estimated.
  CLI `routes warm` pre-fills the catalog.
- **Model.** One OR-Tools routing model per proposal: vehicle d = day d with its window; node (p, d) per pool place
  and day with that date's effective window; service time = visit duration; transit = cached duration for the
  chosen mode; a disjunction over the copies of p allows at most one visit; drop penalty decreases with selector
  rank, must-sees prohibitive, locked stops mandatory on their day. Day hints are advisory. Fixed search parameters
  and time limit make the result deterministic.
- **Regeneration of one day.** Other days copied unchanged; single-vehicle model over the pool minus places used
  elsewhere, with that day's locks mandatory; only uncached pairs are fetched.
- **Plan Health (code).** Blocking: `CLOSED_AT_PLANNED_TIME`, `CLOSED_ON_DATE`, `LEG_UNAVAILABLE`,
  `LEG_MODE_RESTRICTED`, `DAY_WINDOW_EXCEEDED`, `WEB_PLACE_UNRESOLVED`. Warning: `OPENING_HOURS_UNKNOWN`,
  `FACT_STALE`, `MUST_SEE_NOT_INCLUDED`, `LUNAR_EVENT_CONFLICT`, `TICKET_VALIDITY`, `SEASONAL_WARNING`,
  `WEB_PLACE_UNVERIFIED` (caps the plan at WARNING). Each conflict carries `rule_id`, `date` and `stop_ids[]`.
- **Manual edits** never re-run selection or the solver; the retimer keeps the traveler's order and measures only
  changed legs.

## Options

| Option | Verdict | Why |
|---|---|---|
| A. One multi-day OR-Tools model, days as vehicles, per-date windows, cached matrix | **Chosen** | Day assignment follows distances and calendars; free; deterministic |
| B. LLM assigns days, solver per day (0.1) | Superseded | Poor clustering; repair loops |
| C. LLM-only ordering and timing | Rejected | Ignores hours; non-deterministic |
| D. Google Route Optimization API | Rejected | Paid; trip data to another provider |
| E. Greedy heuristic | Rejected | Ignores time windows |

## Consequences

- Positive: MET-004/MET-005 are solver and validator properties; calendar-conflict recall is testable at 100%;
  Routes usage is bounded by the cache and anchors.
- Negative: lunar algorithm and festival dates need golden tests and official verification (OQ-125, DEP-013);
  model size ≈ pool × days nodes (≤ 72); `ortools` arm64 wheel in the image.

## Drivers

BR-007, BR-008, BR-009, BR-013, BR-026, BR-035, BRU-006, MET-004, MET-005, CON-001, DEC-016, OQ-125.
