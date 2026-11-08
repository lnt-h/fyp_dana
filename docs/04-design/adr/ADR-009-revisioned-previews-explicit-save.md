# ADR-009 — Server-held revisioned previews, explicit Save, optimistic revisions and idempotency

| Field | Value |
|---|---|
| Status | Proposed (mentor approval at M0). Re-affirmed 2026-11-06 (DEC-019, DEC-021) |
| Date | 2026-11-04 (1.0: 2026-11-06) |
| Version | 1.0 |
| Owner / decider | Lê Ngọc Tấn Hiền |
| Approver | trantrongminh, FYP mentor ([Pending]) |
| Decision source | BR-011, BR-012, BR-033 |

## Context

An itinerary persists only on explicit Save; failures must not change the saved itinerary or lose unsaved edits
(MET-006 = 0 under failure injection). Every edit needs routing and scheduling on the server. Late provider or
agent results must not overwrite newer revisions.

## Decision

- Generation, edits and regeneration append `preview_revisions` only if their parent is still current; revisions
  are immutable and record model, prompt and corpus versions, `research_used` and `agent_run_id`.
- Save checks owner, expiry, Plan Health not BLOCKED, publication eligibility of every `VERIFIED` stop, the
  traveler's acknowledgement when a `WEB_UNVERIFIED` stop is present (OQ-128) and both expected revisions, then in
  one transaction replaces the saved days, stops and legs and increments the trip revision.
- Replayable operations carry an `Idempotency-Key` scoped by owner and operation.
- Mobile keeps not-yet-acknowledged edits in its draft store until the server confirms them.
- Expired previews are removed by the jobs runner.

## Options

| Option | Verdict | Why |
|---|---|---|
| A. Server preview with immutable revisions; Save promotes one revision; idempotency keys | **Chosen** | Survives restarts and failures; one source for timeline and map |
| B. Draft only on the device | Rejected | Server cannot recalculate legs; lost on device failure |
| C. Autosave edits into the trip | Rejected | Violates explicit Save |

## Consequences

- Positive: MET-006 is enforceable; stale writers get a `revision_conflict`.
- Negative: preview storage grows; bounded by expiry.

## Drivers

BR-011, BR-012, BR-032, BR-033, MET-006, QAS-02, OQ-128.
