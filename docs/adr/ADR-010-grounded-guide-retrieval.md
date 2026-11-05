# ADR-010 — Grounded Guide: city-level hybrid retrieval, labelled web fallback, citation validation

| Field | Value |
|---|---|
| Status | Proposed (mentor approval at M0) |
| Date | 2026-11-04 (1.0: 2026-11-06) |
| Version | 1.0 (0.3 → 1.0: DEC-017 city-level Guide in v1; entity/lexical/vector legs with RRF; deterministic labelled web fallback; DEC-015 removes "runtime web search out of scope") |
| Owner / decider | Lê Ngọc Tấn Hiền |
| Approver | trantrongminh, FYP mentor ([Pending]) |
| Decision source | BR-015, BR-038; DEC-010, DEC-012 (SRC-100); DEC-015, DEC-017 (SRC-105) |

## Context

The owner wants "ask anything about Đà Nẵng" (A-036) in VI and EN. Answers must cite reviewed sources (MET-007 ≥
95%) or state insufficient evidence (MET-008 ≥ 90%). Vietnamese embedding quality is unmeasured, so a vector-only
threshold risks false refusals. The research agent (ADR-014) is now in scope, so a web fallback is possible if it is
labelled. Facts and chunks are reviewed separately; content changes only by republication.

## Decision

1. **Evidence units.** `place_facts` (operational, structured) and sectioned `knowledge_chunks` (1–4000 chars, one
   approved chunk per section, locale and scope). City-scope chunks have `place_id` NULL and sections
   `CITY_OVERVIEW`, `GETTING_AROUND`, `EVENTS_CALENDAR`, `PRACTICAL`. Facts never live in chunks.
2. **Place-scoped session** (`guide_sessions.scope = PLACE`): evidence = every approved fact and every approved
   chunk of the pinned publication for the locale (fallback to the other locale); no embedding, no threshold.
3. **City-scoped session** (`scope = CITY`, v1): three legs over approved content of the enabled city, merged by
   reciprocal rank fusion: entity (trigram on place names and aliases → that place's facts and chunks), lexical
   (trigram on chunk text), vector (pgvector HNSW cosine top-k, question embedding cached in
   `query_embedding_cache`). Bound: ≤ 8 chunks plus all approved facts of ≤ 3 places. No similarity threshold; the
   writer decides sufficiency claim by claim.
4. **Web fallback (deterministic).** Only when the evidence set is empty, the feature flag is on and quota allows,
   the orchestrator runs the researcher (ADR-014); its evidence enters the prompt labelled `WEB_UNVERIFIED` and the
   answer status becomes `ANSWERED_WEB_UNVERIFIED`. The model never decides whether to search.
5. **Citation validation.** The writer returns claims with `evidence_ids`; claims whose IDs are not in the supplied
   set are dropped; zero remaining claims → `INSUFFICIENT_EVIDENCE`. Citations are stored in
   `guide_message_citations` with `evidence_kind` FACT, CHUNK or WEB; WEB citations carry URL and `fetched_at`.
6. **Embedding on write** (ADR-012): chunks are embedded when saved; the question embedding model must equal every
   chunk's `embedding_model`, else `ai_unavailable` until re-embedding completes. Model pinned per OQ-126.
7. **Streaming and history.** Validated text streams over SSE; code rebuilds the last 4 turns as context; answers
   are stored with citations in the traveler's session.

## Options

| Option | Verdict | Why |
|---|---|---|
| A. Place-scoped full evidence + city-scoped hybrid RRF + labelled deterministic web fallback | **Chosen** | Deterministic, testable; no threshold tuning on unverified Vietnamese embeddings |
| B. Vector-only with threshold | Rejected | False refusals; one embed call per question |
| C. Long context: all content of all places | Rejected | Quota; weak citation control |
| D. Model-driven web search grounding (model decides to search) | Rejected | Unreviewed sources without a label; non-deterministic |

## Consequences

- Positive: MET-007/MET-008 checkable claim by claim; the Vietnamese local-assistant gap is addressed; web
  answers are always visibly labelled.
- Negative: recall of trigram legs for Vietnamese is an assumption (ASM-019); web fallback spends Tavily and Groq
  quota (RSK-013); city-scope chunks must be authored for Đà Nẵng.

## Drivers

BR-015, BR-038, BR-024, BR-025, MET-007, MET-008, MET-014, QAS-06, ASM-019, OQ-126.
