# ADR-010 — Grounded Guide: structured facts + place-scoped evidence, citation validation, streamed by SSE

| Field | Value |
|---|---|
| Status | Proposed (pending mentor approval at the design gate) |
| Date | 2026-11-04 (0.3: 2026-11-05) |
| Version | 0.3 (0.1 → 0.2: DA-GONARRA-01 fixes F-01, embedding before publication; 0.2 → 0.3: DEC-010 two-tier retrieval, sectioned chunks, DEC-012 embedding on write, model-consistency rule) |
| Owner / decider | Lê Ngọc Tấn Hiền |
| Approver | trantrongminh, FYP mentor ([Pending]) |
| Parent | GONARRA-SAD 0.1 §4.0; prompt `design/SAD_prompt.md` v2.0 |
| Decision source | BR-015, BR-038, DATA.md, plan.md §8; DEC-010 and DEC-012 (SRC-100 A-028) |

## Context

Answers must cite reviewed sources (BR-015, MET-007 ≥ 95%) or state insufficient evidence (BR-038, MET-008 ≥ 90%).
Runtime web search is out of scope (BRD §5.2). Operational facts are structured and separately reviewable
(SRC-003). The catalog is small (about 250 places, a handful of narrative chunks per place and locale, ASM-030) and
every Guide session is already scoped to one published place (API-024). Vietnamese embedding quality of the Gemini
embedding model is unmeasured (OQ-032), so a similarity threshold on place-scoped questions risks false
`insufficient_evidence` outcomes that would hurt MET-007/MET-008. Content changes by republication, so retrieval
must follow the pinned publication, never a live index.

## Drivers

BR-015, BR-038, BR-024, BR-025, MET-007, MET-008, QAS-06, OQ-032.

## Options considered

| Option | Pros | Cons | Verdict |
|---|---|---|---|
| A. Two tiers. **Tier 1 (place-scoped, v1):** evidence = all approved facts pinned by the current publication plus all approved chunks of the pinned corpus revision for that place and locale; no question embedding, no threshold. **Tier 2 (city-scoped, roadmap):** hybrid lexical (pg_trgm / full-text) ∪ pgvector top-k with a threshold | Deterministic and testable; immune to embedding quality for the 90% case; no Gemini embed call per question; one place's chunks fit in one prompt | Tier 2 needs calibration later; chunks must be authored in bounded sections | **Chosen** |
| B. Vector-only retrieval with threshold for every question (0.2 design) | Uniform pipeline | Threshold tuning on unverified Vietnamese embeddings; false refusals; one embed call per question | Rejected for Tier 1, kept as part of Tier 2 |
| C. Long-context: send all content of all places each time | Simple | Token/quota cost; weaker citation control | Rejected |
| D. Model with web search grounding | Broad coverage | Out of scope; unreviewed sources | Rejected |

## Decision

1. **Evidence unit = sectioned chunk.** Each place has, per locale, at most one approved chunk per section
   (`OVERVIEW`, `HISTORY`, `HIGHLIGHTS`, `VISIT_TIPS`, `ETIQUETTE`, `ACCESS`), 1–4000 characters, each linked to at
   least one captured source revision (`knowledge_chunk_sources`; gate `CHUNK_WITHOUT_SOURCE`). Operational facts
   (hours, admission, address, entrance, …) stay in `place_facts` and are never written into chunks.
2. **Tier 1 (v1, place-scoped).** For a question in a session scoped to place P and locale L: evidence = every
   approved fact pinned by P's current publication (with source, `verified_at`, freshness) + every approved chunk of
   the corpus revision pinned by that publication for locale L (fallback: the other locale's chunks, answered in L).
   No question embedding, no similarity threshold. If the evidence set is empty → `INSUFFICIENT_EVIDENCE` without any
   model call. Otherwise the model answers only from the supplied evidence and must cite evidence IDs; citations not
   in the supplied set are removed and an answer left without a valid citation becomes `INSUFFICIENT_EVIDENCE`.
3. **Tier 2 (roadmap, not in the v1 contract).** City-scoped questions retrieve candidates by hybrid search:
   lexical (pg_trgm on NFC-normalised, diacritic-folded text) ∪ pgvector cosine top-k over `vw_guide_chunks`,
   merged and cut by a threshold calibrated on the frozen evaluation sets (ASM-011). Tier 2 needs a new API
   operation and a new ADR revision before release.
4. **Embedding on write (DEC-012, ADR-012).** The curation API computes the embedding of a new or changed chunk
   (by `content_sha256`) synchronously through the AI gateway and records `embedding_model`; the CLI `embed`
   command remains for backfill and for re-embedding after a model change. Embeddings are derived data: a model
   change re-embeds approved chunks in place and does not create a new corpus revision.
5. **Model consistency rule.** The embedding model used for a question (Tier 2) must equal `embedding_model` of
   every chunk in the searched corpus; a mismatch is a configuration error (`ai_unavailable`) until
   `cli embed --reembed-all` has completed. The model ID is pinned in configuration (OQ-032).
6. **Freshness and cache.** Staleness is computed at read time from `verified_at` (180 days, ASM-008); no job
   re-indexes anything. An optional answer cache is keyed by (place_id, publication_revision, locale, normalised
   question hash, model ID, prompt version), so a republication invalidates it by construction.
7. Answers stream over SSE and are stored with citations in the traveler's session (retention per ASM-010/OQ-004).

## Consequences

- Positive: MET-007/MET-008 are checkable claim-by-claim; Tier 1 has no retrieval misses and no embed quota cost;
  content updates reach the Guide through the normal publish step; the vector index is ready for Tier 2 without
  reprocessing.
- Negative: Tier 1 prompt size grows with the number of sections (bounded: ≤ 6 chunks × 4000 chars per locale);
  Tier 2 calibration (threshold, Vietnamese lexical configuration) is deferred to OQ-032.
- Changes: `knowledge_chunks.section` (schema), `CandidateReview.chunks[]` (API-035), blueprint §3.8.5.

## Verification

Guide answer sample ≥ 50 and out-of-catalog set ≥ 30 (ASM-011) on the first 30 Hội An places; contract test that
every citation ID is in the supplied evidence; test that a republished chunk is used and the superseded one is not.
