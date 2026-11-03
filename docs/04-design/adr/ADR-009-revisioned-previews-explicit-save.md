# ADR-009 — Server-held revisioned previews, explicit Save, optimistic revisions and idempotency

| Field | Value |
|---|---|
| Status | Proposed (pending mentor approval at the design gate) |
| Date | 2026-11-04 |
| Owner / decider | Lê Ngọc Tấn Hiền |
| Approver | trantrongminh, FYP mentor ([Pending]) |
| Parent | GONARRA-SAD 0.1 §4.0; prompt `design/SAD_prompt.md` v2.0 |
| Decision source | BR-011, BR-012, BR-033, API.md, DATABASE-DESIGN.md (SRC-007) |

## Context

An itinerary persists only on explicit Save (BR-011); failures must not change the saved itinerary (BR-012) or lose
unsaved edits (BR-033); MET-006 = 0 under failure injection. Every edit needs routing and scheduling on the server
(BR-032). Late provider results must not overwrite newer revisions (SRC-003).

## Drivers

BR-011, BR-012, BR-032, BR-033, MET-006, QAS-02.

## Options considered

| Option | Pros | Cons | Verdict |
|---|---|---|---|
| A. Server preview with immutable revisions bound to trip base revision; Save atomically promotes one revision; idempotency keys | Survives app restarts and failures; one source for timeline and map | More tables; expiry cleanup | **Chosen** |
| B. Draft only on the device; send final itinerary on Save | Simple server | Server cannot recalculate legs; lost on device failure | Rejected |
| C. Autosave edits into the trip | Never lose edits | Violates BR-011 | Rejected |

## Decision

Generation, edits and regeneration append preview revisions only if their parent is still current. Save checks
owner, expiry, Plan Health not BLOCKED, publication eligibility and both expected revisions, then in one
transaction replaces the saved days/stops/legs and increments the trip revision. Replayable operations carry
idempotency keys scoped by owner and operation. Mobile CMP-020 keeps not-yet-acknowledged edits until the server
confirms them. Expired previews are removed by the jobs runner (expiry value: OQ-030).

## Consequences

- Positive: MET-006 is enforceable; concurrent/stale writers get a conflict.
- Negative: preview storage grows; bounded by expiry.
