# ADR-004 — Gemini as a bounded proposal engine with deterministic validation and scheduling

| Field | Value |
|---|---|
| Status | **Superseded by ADR-013 (2026-11-06, DEC-014).** Kept as history |
| Date | 2026-11-04 (0.2: 2026-11-05; superseded 2026-11-06) |
| Version | 0.2 |
| Owner / decider | Lê Ngọc Tấn Hiền |
| Approver | trantrongminh, FYP mentor ([Pending]) |
| Decision source | plan.md §7, BRU-002, BRU-006; narrowed by DEC-008 and DEC-011 (ADR-011) |

## Context (as of 0.2)

AI may not create a place or fact; distances and durations come only from a routing provider; conflicts must be
flagged in 100% of conflict-set cases. Gemini on the free tier has limited quota and data-use risk. No account
identifiers, contact data or precise location may be sent to AI. The owner's 2026-11-04 stack review excluded
agent frameworks.

## Decision (as of 0.2)

- Gemini is called only by the AI gateway through the Google GenAI SDK with schema-constrained output.
- Input: a bounded DTO of published place IDs and approved attributes for one city, preferences and locale; never
  account IDs, contact details or traveler coordinates.
- Output: one ranked pool of place IDs for the trip, a rationale per pick, optional advisory day hints. Unknown,
  unpublished, cross-city or duplicate IDs fail validation; one bounded repair, then a typed error. The model does
  not assign days, order stops or set times (DEC-011; ADR-011).
- Model ID, prompt version and manifest revision are recorded with each preview revision.

## Options (as of 0.2)

| Option | Verdict | Why |
|---|---|---|
| A. Gemini ranks supplied IDs; code validates, schedules, scores health | Chosen in 0.2 | Facts and feasibility deterministic |
| B. LLM generates the full itinerary | Rejected | Invented places and times |
| C. Agent framework (Agno/AgentOS) with tools | Rejected in 0.2 | Not in the approved stack at the time |
| D. Rule-based selection only | Rejected | Weak free-text handling in two languages |

## What ADR-013 changes

- Option C is now accepted in a bounded form: Agno `Agent` objects for three roles (selector, researcher,
  grounded writer), each with a Pydantic `output_schema`, under a deterministic Gonarra orchestrator; no Agno Team
  leader, Workflow or AgentOS.
- Single-provider Gemini becomes per-role model chains (Gemini → Groq) with a quota ledger and a rule-based
  fallback so planning completes without AI.
- The selector may return `unmet_requests`, which can trigger the research agent (ADR-014).
- Unchanged and carried forward: bounded input DTO, ID validation, one repair, no days/order/times from a model,
  redaction, recording of model and prompt versions.

## Drivers

BRU-002, BRU-006, BR-005, BR-046, MET-004, MET-007, RSK-002, RSK-003.
