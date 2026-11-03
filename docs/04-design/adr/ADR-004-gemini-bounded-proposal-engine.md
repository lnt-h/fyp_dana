# ADR-004 — Gemini as a bounded proposal engine with deterministic validation and scheduling

| Field | Value |
|---|---|
| Status | Proposed (pending mentor approval at the design gate) |
| Date | 2026-11-04 |
| Owner / decider | Lê Ngọc Tấn Hiền |
| Approver | trantrongminh, FYP mentor ([Pending]) |
| Parent | GONARRA-SAD 0.1 §4.0; prompt `design/SAD_prompt.md` v2.0 |
| Decision source | Agent brief (AI), plan.md §7, BRU-002, BRU-006; narrowed by DEC-008 (ADR-011) |

## Context

AI itinerary generation is common; Gonarra's value is trust and feasibility (BRD §3.5). AI may not create a place
or fact (BRU-002); distances and durations come only from a routing provider (BRU-006). Conflicts must be flagged
in 100% of conflict-set cases (MET-004). Gemini is used on the free tier (CON-001), whose data-use terms are a risk
(RSK-002) and whose quotas are limited (RSK-003). No account identifiers, contact data or precise location may be
sent to AI (BR-046).

## Drivers

BRU-002, BRU-006, BR-005, BR-006, BR-008, BR-046, MET-004, MET-007, RSK-002, RSK-003, QAS-01, QAS-05.

## Options considered

| Option | Pros | Cons | Verdict |
|---|---|---|---|
| A. Gemini selects/ranks supplied published IDs and writes rationale; deterministic code validates, schedules (ADR-011) and computes Plan Health | Facts and feasibility are deterministic and testable; AI adds preference matching | Two-stage pipeline to build | **Chosen** |
| B. LLM generates the full itinerary (places, times, travel) | Fast to prototype | Invented places/times; violates BRU-002/BRU-006; untestable | Rejected |
| C. Agent framework (Agno/AgentOS) with tools | Flexible orchestration | Not part of the approved stack (owner stack review 2026-11-04); tools widen the attack surface (SRC-003) | Rejected |
| D. No AI; rule-based selection only | Fully deterministic | Weak handling of free-text requests in two languages (BR-005) | Rejected |

## Decision

- Gemini is called only by the AI gateway (CMP-012) through the Google GenAI SDK with schema-constrained output.
- Planning input: a bounded DTO of published place IDs and approved attributes for one city, the traveler's
  preferences and locale — never account IDs, contact details or coordinates of the traveler.
- Planning output: selected place IDs per day with ranks and a rationale. Unknown, unpublished, cross-city or
  duplicate IDs are validation failures; one bounded repair attempt, then a typed recoverable error.
- Order, times, legs and Plan Health are computed deterministically (ADR-011, BRU-006).
- Model ID, prompt version and corpus/manifest revision are recorded with each preview revision.
- The same gateway serves embeddings (ADR-010) and vision (ADR-008) with the same redaction rule.

## Consequences

- Positive: MET-004/MET-005 are deterministic properties; prompt-injection impact is bounded to choosing among
  supplied IDs.
- Negative: rationale text may mention facts; the rationale is shown as AI text and facts on screen come from the
  catalog. Free-tier quotas cap throughput (quota guard in CMP-014).
- Follow-up: OQ-032 (models, quotas, terms). The amendment to `plan.md` §6/§7.1 (Agno mention; model scope) is
  tracked with OQ-007.

## Verification

Golden planning set (ASM-011) with injected unknown/cross-city IDs (AC-006); payload inspection (AC-046).
