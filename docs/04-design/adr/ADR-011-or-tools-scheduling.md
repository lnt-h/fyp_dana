# ADR-011 — Deterministic multi-day scheduling with Google OR-Tools over a Google Routes matrix

| Field | Value |
|---|---|
| Status | Accepted by the owner (SRC-100 A-021, 2026-11-04; multi-day model A-028, 2026-11-05); mentor review at the design gate [Pending] |
| Date | 2026-11-04 (0.2: 2026-11-05) |
| Version | 0.2 (0.1 → 0.2: DEC-011 — one multi-day model with days as vehicles; Gemini ranks a pool instead of assigning days) |
| Owner / decider | Lê Ngọc Tấn Hiền |
| Approver | trantrongminh, FYP mentor ([Pending]) |
| Parent | GONARRA-SAD 0.1 §4.0; prompt `design/SAD_prompt.md` v2.0 |
| Decision source | DEC-008 (SRC-100 A-021); DEC-011 (SRC-100 A-028) |

## Context

Each day's stops need an order and arrival/departure times that respect opening hours and the traveler's day
window (BR-007, BR-008), with leg values from Google Routes only (BRU-006). Locked stops must keep place, day and
duration on regeneration (BR-035, MET-005 = 0). ADR-004 limits Gemini to selecting and ranking published IDs.
Budget allows only free tools (CON-001). In the 0.1 design Gemini also assigned places to days and the solver ran
one model per day; because the model receives no distances (BR-046 withholds traveler location and the DTO carries
no coordinates), it clustered days poorly, forcing the solver to drop stops and the pipeline to repair.

## Drivers

BR-007, BR-008, BR-009, BR-026, BR-032, BR-035, BRU-006, MET-004, MET-005, CON-001, QAS-01, QAS-03.

## Options considered

| Option | Pros | Cons | Verdict |
|---|---|---|---|
| A. One OR-Tools routing model per proposal: days are vehicles, nodes are (place, day) copies with that date's opening window, disjunctions keep at most one copy per place, drop penalties follow Gemini ranks, locks are mandatory nodes on their day; inputs: visit durations + one Routes matrix (WALK/DRIVE) over the pool | Day assignment and order come from distances and hours, not from a model that cannot see them; fewer drops and repairs; still free, local, deterministic | Larger model (pool × days nodes); time limit must be bounded | **Chosen** |
| B. Gemini assigns days, OR-Tools solves each day (0.1 design) | Smaller models | Poor day clustering; repair loops; non-deterministic day split | Superseded |
| C. LLM-only ordering and timing | No solver code | Non-deterministic; can ignore hours; breaks BRU-006 | Rejected |
| D. Google Route Optimization API | Managed solver | Paid service; contradicts CON-001; sends trip data to another provider | Rejected |
| E. Greedy nearest-neighbour heuristic | Trivial to code | Ignores time windows; poor orders; conflicts left to the traveler | Rejected |

## Decision

- **Selection (ADR-004).** Gemini returns one ranked pool of candidate published place IDs for the whole trip
  (size capped by configuration, about 6–8 per day), with a rationale per pick and optional advisory day hints. The
  validator checks IDs ∈ candidate set, city, duplicates; one bounded repair, then a typed error.
- **Routing (CMP-009).** One Compute Route Matrix over the pool plus the day start points, per allowed mode; values
  reused only within provider terms (OQ-031); unavailable pairs are marked, never estimated.
- **Scheduling (CMP-008).** One OR-Tools routing model per proposal: vehicle d = day d with its day window; node
  (p, d) for each pool place p and day d, allowed only on vehicle d, time window = known opening interval of p on
  that date ∩ day window (UNKNOWN hours → day window only, later a WARNING); service time = suggested visit duration
  (or the traveler's edited duration); transit = matrix duration for the chosen mode. A disjunction over the copies
  of p allows at most one visit; the drop penalty decreases with Gemini rank, must-sees get a prohibitive penalty,
  locked stops are mandatory on their locked day with their duration and keep relative order among locks. Day
  hints from Gemini are advisory only (not constraints) in v1. Fixed first-solution strategy, fixed search
  parameters and a time limit (OQ-030) make the result deterministic for identical inputs.
- **Regeneration of one day (BR-013).** All other days are copied unchanged; the solver runs a single-vehicle model
  for the target day over the pool minus places used on other days, with that day's locks mandatory.
- **Validation.** The deterministic validator computes conflicts and Plan Health (unknown hours → WARNING; outside
  known hours, unavailable leg or day overrun → BLOCKED).
- **Manual edits (BR-010, BR-027..BR-031)** never re-run selection or the solver: the Retimer re-times the day with
  the traveler's order kept, measuring only changed legs.

## Consequences

- Positive: MET-004/MET-005 are solver/validator properties; day assignment is distance- and hours-aware; fewer
  Gemini repair calls; no paid optimizer.
- Negative: model size ≈ pool × days nodes (≤ 72 at the caps); the solver time limit (OQ-030) must be set from the
  first spike; `ortools` arm64 wheel in the multi-arch image.
- Changes `plan.md` §7.1 (tracked as SAD difference D-4 / OQ-007); supersedes blueprint §3.8.2 "day solver".

## Verification

Conflict set (MET-004 = 100%), regeneration set (MET-005 = 0), determinism test (same inputs → same plan), and a
clustering check on the golden set: no proposal day contains a leg longer than the configured maximum when a
shorter feasible assignment exists.
