# ADR-011 — Deterministic scheduling with Google OR-Tools over a Google Routes matrix

| Field | Value |
|---|---|
| Status | Accepted by the owner (SRC-100 A-021, 2026-11-04); mentor review at the design gate [Pending] |
| Date | 2026-11-04 |
| Owner / decider | Lê Ngọc Tấn Hiền |
| Approver | trantrongminh, FYP mentor ([Pending]) |
| Parent | GONARRA-SAD 0.1 §4.0; prompt `design/SAD_prompt.md` v2.0 |
| Decision source | DEC-008, owner-level stack review relayed 2026-11-04 — **Accepted** (SRC-100 A-021) |

## Context

Each day's stops need an order and arrival/departure times that respect opening hours and the traveler's day
window (BR-007, BR-008), with leg values from Google Routes only (BRU-006). Locked stops must keep place, day and
duration on regeneration (BR-035, MET-005 = 0). ADR-004 limits Gemini to selecting and ranking published IDs.
Budget allows only free tools (CON-001).

## Drivers

BR-007, BR-008, BR-009, BR-026, BR-032, BR-035, BRU-006, MET-004, MET-005, CON-001, QAS-01, QAS-03.

## Options considered

| Option | Pros | Cons | Verdict |
|---|---|---|---|
| A. Google OR-Tools (Python, Apache-2.0) routing solver with time windows; inputs: visit durations + Google Routes Compute Route Matrix (WALK/DRIVE) for the selected candidates | Free, local, deterministic with fixed parameters; native time-window and fixed-node constraints; testable | Native wheel adds image size; solve time must be bounded | **Chosen** |
| B. LLM-only ordering and timing | No solver code | Non-deterministic; can ignore hours; breaks BRU-006 | Rejected |
| C. Google Route Optimization API | Managed solver | Paid service; contradicts CON-001; sends trip data to another provider | Rejected |
| D. Greedy nearest-neighbour heuristic | Trivial to code | Ignores time windows; poor orders; conflicts left to the traveler | Rejected |

## Decision

- Gemini selects and ranks candidate published place IDs per day and writes rationales (ADR-004).
- Routing CMP-009 requests a Compute Route Matrix (WALK and/or DRIVE per the traveler's allowed modes) for the
  selected places plus the day start point; values are reused only within provider terms (OQ-031); unavailable
  pairs are marked, never estimated.
- Planning CMP-008 builds one OR-Tools model per day: time windows from known opening hours for that date and the
  day window; service time = visit duration; transit = matrix duration; locked stops are fixed constraints
  (place, day, duration; relative order among locks); optional (droppable) nodes with penalties from Gemini ranks
  let the solver drop low-ranked stops that cannot fit.
- The solver runs in a thread pool with a configured time limit and fixed parameters; the result is then checked by
  the deterministic validator, which computes conflicts and Plan Health (unknown hours → WARNING; outside known
  hours, unavailable leg or day overrun → BLOCKED).
- Manual edits (BR-010, BR-027..BR-031) do not re-run selection; they re-time the day deterministically with the
  traveler's order kept, measuring only changed legs, so the traveler's choices are not reordered.

## Consequences

- Positive: MET-004/MET-005 become solver/validator properties; no paid optimizer.
- Negative: adds `ortools` to `apps/api` (arm64 wheel must build in the multi-arch CI image); route-matrix
  calls count against the Routes free quota (RSK-003); solver time limit needs a value (OQ-030).
- Changes `plan.md` §7.1, which lets the model propose order and durations — tracked as SAD difference D-4 / OQ-007.

## Verification

Conflict set (MET-004 = 100%), regeneration set (MET-005 = 0), determinism test (same inputs → same plan).
