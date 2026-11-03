# ADR-010 — Grounded Guide: structured facts + pgvector retrieval with citation validation, streamed by SSE

| Field | Value |
|---|---|
| Status | Proposed (pending mentor approval at the design gate) |
| Date | 2026-11-04 |
| Version | 0.2 (0.1 → 0.2: DA-GONARRA-01 fixes F-01, embedding before publication) |
| Owner / decider | Lê Ngọc Tấn Hiền |
| Approver | trantrongminh, FYP mentor ([Pending]) |
| Parent | GONARRA-SAD 0.1 §4.0; prompt `design/SAD_prompt.md` v2.0 |
| Decision source | BR-015, BR-038, DATA.md, plan.md §8 |

## Context

Answers must cite reviewed sources (BR-015, MET-007 ≥ 95%) or state insufficient evidence (BR-038, MET-008 ≥ 90%).
Runtime web search is out of scope (BRD §5.2). Operational facts are structured and separately reviewable
(SRC-003).

## Drivers

BR-015, BR-038, BR-024, BR-025, MET-007, MET-008, QAS-06.

## Options considered

| Option | Pros | Cons | Verdict |
|---|---|---|---|
| A. Operational facts from structured rows; narrative from reviewed chunks in pgvector filtered by place + locale; model answers only from supplied evidence; citations validated; threshold → insufficient evidence | Grounded; measurable; no extra store | Retrieval quality depends on chunking | **Chosen** |
| B. Long-context: send all place content each time | Simple | Token/quota cost; weaker citation control | Rejected |
| C. Model with web search grounding | Broad coverage | Out of scope; unreviewed sources | Rejected |

## Decision

Embeddings of reviewed chunks are computed by the CLI before publication, so a place is searchable from its first publication (ADR-012), through the AI gateway.
A question is embedded, chunks are retrieved for the scoped place and locale above a similarity threshold, facts
are added with source, verification date and freshness, and the model must cite IDs from that set; uncited or
foreign citations are rejected; no evidence → `insufficient_evidence` without generation. Answers stream over
SSE and are stored with citations in the traveler's session (retention per ASM-010/OQ-004).

## Consequences

- Positive: MET-007/MET-008 are checkable claim-by-claim.
- Negative: threshold tuning on the frozen evaluation sets (ASM-011).
