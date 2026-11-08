# ADR-013 — Agno multi-agent planner (three roles) with a deterministic Gonarra orchestrator

| Field | Value |
|---|---|
| Status | Proposed; accepted by the owner (DEC-014); mentor review at M0 [Pending] |
| Date | 2026-11-06 |
| Version | 0.1 (reconstructed from [SAD](../architecture/SAD.md) §3.1–3.3 and DEC-014, DEC-018) |
| Owner / decider | Lê Ngọc Tấn Hiền |
| Approver | trantrongminh, FYP mentor ([Pending]) |
| Decision source | DEC-008, DEC-011, DEC-014, DEC-018, DEC-022 ([decisions](../../decisions.md)); supersedes ADR-004 |

> **Model pins updated by DEC-026 (2026-11-08).** Live probe: `gemini-2.5-flash`/`-lite` and Groq
> `llama-3.3-70b-versatile` answer 404 for new keys. `selector`: `gemini-3.6-flash` → `gemini-3.5-flash-lite` → Groq
> `openai/gpt-oss-120b`; `grounded_writer` RATIONALE: `gemini-3.5-flash-lite` → Groq, GUIDE_ANSWER: `gemini-3.6-flash`
> → Groq; `researcher`: Groq `openai/gpt-oss-120b` only (no Gemini fallback, ADR-014). `gemini-3.7/3.8-flash` avoided
> (24–30 s default thinking). DEC-025 adds an offline use of `grounded_writer` (description enrichment, CLI only).
> The Places tool of the `researcher` is not used in the demo (DEC-023).

## Context

ADR-004 used one Gemini call as a bounded proposal engine and excluded agent frameworks. The re-baseline (DEC-014,
DEC-015, DEC-017) adds a runtime research agent with tools, city-level Guide answers and per-role free-tier fallback
chains (Gemini → Groq, DEC-018). Domain logic, scheduling, validation and authorization must stay out of prompts and
model output; Plan Health and the solver are deterministic code (ADR-011). One developer, a 2 GiB host, no workers.

## Decision

- **Three Agno `Agent` roles inside `apps/api`**, built only in `app/agents/` (models and quota in `app/ai/`),
  pinned `agno==3.1.12`:
  - `selector` — ranks a pool of ≤ 50 published Đà Nẵng place IDs (redacted `CandidateDto[]`, no coordinates); no
    tools; output `SelectionResult`; IDs ⊆ pool, no duplicates, must-sees present; one repair, then a rule-based
    fallback so planning completes without AI.
  - `researcher` — Groq only; tools `tavily_search`, `fetch_page`, `places_check` with adapter caps (≤ 2 searches,
    ≤ 3 fetches, ≤ 3 Places checks); runs only when the catalog pool is thin, requests are unmet or Guide evidence is
    insufficient (ADR-014).
  - `grounded_writer` — profiles `RATIONALE` and `GUIDE_ANSWER`; writes only from supplied evidence; claims whose
    evidence IDs are not in the supplied set are dropped; zero claims → `INSUFFICIENT_EVIDENCE`.
- **Deterministic orchestrator.** `planning/workflows.py` and `guide/workflow.py` are Gonarra async step-runners that
  own ordering, retries, quota reservation and persistence, and emit SSE stages. No LLM team leader, no Agno `Team` or
  `Workflow`, no AgentOS. Model calls run outside database transactions.
- **Validation.** Every structured output is validated by Pydantic plus domain rules; unknown catalog IDs or fields,
  model-supplied distances, durations, hours, prices or facts are validation failures. Groq (JSON mode) output is
  re-validated with the same schema.
- **Quota and degradation.** Every call reserves budget in `ai_quota_ledger`; an exhausted chain degrades (rule-based
  selection, null rationales, research skipped, `INSUFFICIENT_EVIDENCE`) and never fails a save.
- **Privacy.** A fail-closed `Redactor` keeps account IDs, contact data and precise location out of every prompt and
  search (BR-046). Agents get no generic SQL, shell, filesystem or HTTP tool.
- **Publishing (DEC-022).** No agent publishes a place or writes `place_facts`, `place_closure_rules` or publications;
  publishing is the deterministic gate in code (ADR-012).

## Options

| Option | Verdict | Why |
|---|---|---|
| A. Agno agents per role + deterministic Gonarra orchestrator | **Chosen** | Typed tools, `output_schema`, retries and `agno.eval` without giving control flow to a model |
| B. Single bounded Gemini call (ADR-004) | Superseded | No tool use for research; no per-role fallback |
| C. Agno Team / LLM team leader / AgentOS | Rejected | Non-deterministic control flow; extra service; harder to test |
| D. Hand-written provider SDK calls only | Rejected | Re-implements tool loops, retries and evals |

## Consequences

- Positive: each role is testable with mocks (dependency overrides) and evals; orchestration is reproducible
  (NFR-032); planning works with no AI at all.
- Negative: Agno API churn (RSK-014) — mitigated by the exact pin and the two-module import boundary enforced by
  `import-linter`; Groq JSON mode needs double validation.

## Drivers

BRU-002, BRU-006, FR-025, FR-056, FR-058, FR-099, FR-106, BR-046, NFR-032, RSK-003, RSK-014, ASM-021, OQ-126.
