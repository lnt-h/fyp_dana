# ADR-008 — Photo identification restricted to published places within 300 m

| Field | Value |
|---|---|
| Status | Proposed (mentor approval at M0). Re-affirmed 2026-11-06 (DEC-019, DEC-021) |
| Date | 2026-11-04 (1.0: 2026-11-06) |
| Version | 1.0 |
| Owner / decider | Lê Ngọc Tấn Hiền |
| Approver | trantrongminh, FYP mentor ([Pending]) |
| Decision source | BR-017, BR-040, ASM-009 |

## Context

Travelers identify a nearby published place from a photo and get "not recognised" otherwise. "Nearby" is 300 m.
Precise location may not be sent to AI. Targets: ≥ 85% correct (MET-009), ≥ 90% "not recognised" for
out-of-catalog photos. Photo identification is second in the cut order.

## Decision

- Mobile takes a photo and one foreground location fix (no background permission), strips image metadata and
  uploads both over HTTPS.
- The Guide module queries published places within 300 m with PostGIS; with no candidate it returns "not
  recognised" without any model call.
- Otherwise the vision call receives the image plus candidate IDs, bilingual names and short reviewed descriptions,
  never coordinates, and accepts only an ID from that set or "none". `WEB_UNVERIFIED` candidates are never offered.
- Photo and coordinates are processed in memory and never stored or logged. Photo processing by Gemini is disclosed
  in study consent.

## Options

| Option | Verdict | Why |
|---|---|---|
| A. PostGIS 300 m filter, closed-set vision choice | **Chosen** | Cannot invent places; location never reaches AI |
| B. Open-world recognition | Rejected | Invents or misnames places |
| C. Google Lens / Places photo search | Rejected | No API fit; data restrictions; cost |
| D. On-device embedding model | Rejected | Model size and reference images beyond schedule |

## Consequences

- Positive: measurable closed-set accuracy; privacy boundary holds.
- Negative: places just beyond 300 m or with poor GPS are "not recognised" (manual search offered).

## Drivers

BR-017, BR-040, BR-046, ASM-009, MET-009, DC-006, QAS-13, RSK-034.
