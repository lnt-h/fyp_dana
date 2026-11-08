# ADR-011 — Deterministic multi-day scheduling with Google OR-Tools over a cached Google Routes matrix

| Field | Value |
|---|---|
| Status | Accepted by the owner (SRC-100 A-021, A-028; SRC-105 A-035); mentor review at M0 [Pending] |
| Date | 2026-11-04 (0.3: 2026-11-06) |
| Version | 0.3 (0.2 → 0.3: DEC-016 per-date effective windows from calendar rules, new conflict types, web candidates in the pool, pairwise Routes cache with fixed anchors) |
| Owner / decider | Lê Ngọc Tấn Hiền |
| Approver | trantrongminh, FYP mentor ([Pending]) |
| Decision source | DEC-008, DEC-011 (SRC-100); DEC-015, DEC-016, DEC-018 (SRC-105) |

> **Superseded in part by DEC-023 (2026-11-08).** "Google Routes only" now reads "the configured routing provider"
> (BRU-006 rev. 1): `GONARRA_ROUTES_PROVIDER` = `auto` | `google` | `estimate` | `none`. In `development`, `test` and
> `demo` a haversine `EstimateProvider` (× 1.35 detour) may supply legs; they carry `Leg.estimated = true` and the
> Plan Health conflict `LEG_ESTIMATED` with the new severity `INFO`, which never changes the plan status; the UI shows
> "≈"; estimates are never cached and the provider refuses to start in `staging` or `production` (RSK-106). The
> intended production router is self-hosted Valhalla (OSM, `motor_scooter` costing); Google Routes stays pluggable
> (OQ-132). Web candidates are not scheduled until the open-data existence check exists (OQ-134). The decision text
> below is kept as history.
>
> **Amended by DEC-030 (2026-11-09).** `OPENING_HOURS_UNKNOWN` is INFO, not WARNING; see "Amendment 2026-11-09
> (DEC-030)" under Plan Health below.
>
> **Amended 2026-11-09 (mode restrictions handled in scheduling).** See "Amendment 2026-11-09 (mode restrictions)"
> under Model below.

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
  opening-hours fact and the day window. UNKNOWN hours → day window only, later an INFO notice (amended by DEC-030,
  see below).
- **Routing.** Pairwise `routes_matrix_cache(from, to, mode)` 30 d; only misses are fetched. Day starts are fixed
  anchors (never user GPS). WALK is requested only for pairs ≤ 2.5 km. Unavailable pairs are marked, never estimated.
  CLI `routes warm` pre-fills the catalog.
- **Model.** One OR-Tools routing model per proposal: vehicle d = day d with its window; node (p, d) per pool place
  and day with that date's effective window; service time = visit duration; transit = cached duration for the
  chosen mode; a disjunction over the copies of p allows at most one visit; drop penalty decreases with selector
  rank, must-sees prohibitive, locked stops mandatory on their day. Day hints are advisory. Fixed search parameters
  and time limit make the result deterministic.
- **Amendment 2026-11-09 (mode restrictions).** A calendar rule with `restricted_modes` (e.g. the Hội An Old Town
  car-free hours) is handled by the scheduler, not only reported. For each date and each ordered pair of stops that
  a rule covering both restricts in the plan's mode: if the traveler allows WALK, WALK is not restricted and the
  routing provider's walking leg is ≤ 1.5 km and ≤ 20 min, the pair uses WALK on that date (the solver's transit and
  the snapshot leg both take the provider's walking duration and distance; walking matrix only between the
  restricted places, through the quota ledger). Otherwise the solver may not depart along that arc inside the
  restricted window (all day = arc removed), so it reorders or drops a stop. Durations always come from the routing
  provider. Zone geometry is not modelled (no drive-to-edge segments); a leg is restricted when both stops are
  covered, as Plan Health checks. `LEG_MODE_RESTRICTED` stays BLOCKING and now appears only when no valid
  alternative was applied (e.g. a manual edit). The other blocking calendar types are already avoided by
  construction (closed dates have no node copy; visits stay inside the effective windows and the day window); a
  place left out because it is closed or unreachable on every trip date adds the `stops_left_out` assumption.
  A rule with `restricted_modes` qualifies legs only: it never closes a place and never narrows its opening hours
  (the Old Town 15:00–22:00 rule once made every Old Town visit start at 15:00; fixed 2026-11-09).
- **Amendment 2026-11-09 (same-day tickets).** A `TICKET_VALIDITY` rule with `valid_same_day` (the Hội An Old Town
  ticket) groups the places it covers (`StopSpec.ticket_group`). When the first solution spreads a group over
  several days, the solver pins the group to the day that already serves most of it and re-solves; the move is
  kept only when every stop of the group can be served that day and no stop is lost, so a plan never buys the
  same ticket twice. Ties go to the lowest day index (deterministic); locks are never overridden.
- **Regeneration of one day.** Other days copied unchanged; single-vehicle model over the pool minus places used
  elsewhere, with that day's locks mandatory; only uncached pairs are fetched.
- **Plan Health (code).** Blocking: `CLOSED_AT_PLANNED_TIME`, `CLOSED_ON_DATE`, `LEG_UNAVAILABLE`,
  `LEG_MODE_RESTRICTED`, `DAY_WINDOW_EXCEEDED`, `WEB_PLACE_UNRESOLVED`. Warning: `FACT_STALE`, `MUST_SEE_NOT_INCLUDED`, `LUNAR_EVENT_CONFLICT`, `TICKET_VALIDITY`, `SEASONAL_WARNING`,
  `WEB_PLACE_UNVERIFIED` (caps the plan at WARNING). Info (never changes the status): `OPENING_HOURS_UNKNOWN`
  (DEC-030), `LEG_ESTIMATED` (DEC-023). Each conflict carries `rule_id`, `date` and `stop_ids[]`.
- **Amendment 2026-11-09 (DEC-030).** Originally unknown opening hours raised a WARNING. With about 94 % of the
  catalog's hours unknown, almost every plan showed WARNING for missing data, not for a plan problem. Unknown hours
  are now INFO: the stop is still scheduled inside the day window only, no hours are invented ("unknown stays
  unknown"), the notice is still returned and the app aggregates it into one note. Overall health is GOOD unless a
  WARNING or BLOCKING conflict exists (or a `WEB_UNVERIFIED` stop caps it). Calendar and closed-on-date rules are
  unchanged.
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
