# ADR-008 — Photo identification restricted to published places within 300 m

| Field | Value |
|---|---|
| Status | Proposed (pending mentor approval at the design gate) |
| Date | 2026-11-04 |
| Owner / decider | Lê Ngọc Tấn Hiền |
| Approver | trantrongminh, FYP mentor ([Pending]) |
| Parent | GONARRA-SAD 0.1 §4.0; prompt `design/SAD_prompt.md` v2.0 |
| Decision source | Agent brief (AI vision), BR-017, BR-040, ASM-009 |

## Context

Travelers should identify a nearby published place from a photo (BR-017) and get "not recognised" otherwise
(BR-040). "Nearby" is 300 m (ASM-009). Precise location may not be sent to AI (BR-046). Targets: ≥ 85% correct
(MET-009), ≥ 90% "not recognised" for out-of-catalog photos (AC-040). Photo ID is second in the cut order.

## Drivers

BR-017, BR-040, BR-046, ASM-009, MET-009, AC-040, DC-006, QAS-13.

## Options considered

| Option | Pros | Cons | Verdict |
|---|---|---|---|
| A. Server filters published places within 300 m with PostGIS; Gemini vision chooses among those candidate IDs or "none"; validator checks the ID is in the set | Closed-world, cannot invent places; location never reaches AI; zero AI calls when no candidates | Depends on GPS accuracy (RSK-034) | **Chosen** |
| B. Open-world recognition (vision model names the place) | Recognises anything | Invents/mis-names places; breaks BRU-002 | Rejected |
| C. Google Lens / Places photo search | Strong recognition | No API fit; provider data restrictions; cost | Rejected |
| D. On-device embedding model vs reference images | No upload | Model size, per-place reference images and tuning beyond schedule | Rejected |

## Decision

Mobile CMP-022 takes a photo and one foreground location fix (no background permission), strips image metadata,
and uploads both over HTTPS. Guide CMP-010 queries published places whose geometry/entrance lies within 300 m; if
none, it returns "not recognised" without calling AI. Otherwise the AI gateway sends the image and the candidates'
IDs, bilingual names and short reviewed descriptions — not the coordinates — and accepts only an ID from that set
or "none". Photo and coordinates are processed in memory and not stored or logged. Disclosure of photo processing
by Gemini is part of study consent (RSK-002).

## Consequences

- Positive: measurable, closed-set accuracy; privacy boundary holds.
- Negative: places just beyond 300 m or with poor GPS are "not recognised" (manual search offered).
