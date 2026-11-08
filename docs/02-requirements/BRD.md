# Business Requirements Document — Gonarra

| Field | Value |
|---|---|
| Title | Business Requirements Document — Gonarra |
| Version | 2.0 |
| Date | 2026-11-09 |
| Owner | Lê Ngọc Tấn Hiền (student author, product owner, operator) |
| Approver | trantrongminh, FYP mentor (full name and title pending, OQ-001) |
| Status | Draft — [Pending] mentor sign-off at M0 (DEC-013, DEC-015, DEC-022, DEC-023, DEC-025 and DEC-028 need explicit confirmation; OQ-131, OQ-132, OQ-133, OQ-135) |
| Lineage | Condensed from BRD 0.4 and the re-baseline requirements 1.2 (DEC-013..DEC-028). IDs preserved; withdrawn or merged IDs are listed, never renumbered. Full previous text at git tag `docs-sdlc-full`. |

This document holds the business half of the requirements: product, personas, objectives and metrics, scope,
business rules, provider-data rules, constraints, assumptions and glossary. The functional and non-functional
requirements, traceability and release criteria are in the [PRD](../03-analysis/PRD.md). Decisions, open questions
and risks are maintained only in the [decision log](../decisions.md). Elicitation records:
[SRC-100](interviews/SRC-100-elicitation-session-2026-11-04.md) (2026-11-04) and
[SRC-105](interviews/SRC-105-re-baseline-session-2026-11-06.md) (re-baseline, 2026-11-06).

## 1. Product and personas

Gonarra (working name) is a bilingual (VI/EN) AI travel planner and grounded local assistant for **Đà Nẵng**,
including the Hội An area (part of Đà Nẵng since the 2025 merger). A traveler describes a 1–3 day trip in
Vietnamese or English, receives a proposal built from auto-published, source-checked places (and, when the catalog
is thin, web-found places that are always labelled `WEB_UNVERIFIED`), sees whether each day fits (timeline, map,
Plan Health with calendar rules), edits it and keeps it only by an explicit Save. On site the traveler uses a
bilingual place card, asks the Guide about Đà Nẵng and receives answers with sources and trust labels, and hands
off to booking partners.

The thesis claim is a *source-checked local layer*: every place, fact and answer carries an attributed source, a
source-check date and a trust label, and a user study measures this against ChatGPT/Gemini (DEC-020). Since
DEC-022 no content is reviewed by a human: `VERIFIED` means "passed Gonarra's automated source checks", and no copy
claims human review. Descriptions and facts may be summarised or extracted by AI **from supplied sources only** and
are labelled "Summarised from sources" (DEC-025, DEC-028).

| Persona | Description |
|---|---|
| P-01 Linh | Domestic weekend traveler, 27, Android, Vietnamese; 2 days in Đà Nẵng with a friend; wants a plan that fits and a driver-ready address. |
| P-02 Tom | International first-time visitor, 34, iPhone, English only; 2 relaxed days in the Hội An area; cannot read Vietnamese addresses, distrusts unsourced AI answers. |
| P-03 Operator (rev. 1, DEC-022; was Curator) | Lê Ngọc Tấn Hiền at a terminal: maintains the CSV sheet and the closure-rule YAML, runs the ingestion and enrichment CLIs, watches the release-gate count and can unpublish a place in an emergency. No review UI. |
| P-04 Study participant | P-01/P-02 profiles under consent, using pseudonymous study accounts. |

## 2. Objectives and metrics

| ID | Objective (outcome) | Metrics |
|---|---|---|
| BO-001 | Travelers obtain a valid 1–3 day Đà Nẵng itinerary from trusted, labelled local content with little effort | MET-001, MET-002, MET-003 |
| BO-002 | Travelers can judge feasibility (hours, legs, calendar) and change a trip without losing their choices | MET-004, MET-005, MET-006 |
| BO-003 | Travelers act on local information they can trust, recognise uncertainty and see what is unverified | MET-007, MET-008, MET-014 |
| BO-004 | The project operates a private Đà Nẵng service on free tiers, with an automatically source-checked catalog above the release gate (rev. 1, DEC-022) | MET-011 |
| BO-005 | The product is evaluated with real users against ChatGPT/Gemini before submission | MET-014, MET-001..003 |

| ID | Metric | Formula / data | Target |
|---|---|---|---|
| MET-001 | Planning task completion | Participants who save a valid itinerary ÷ participants (study) | ≥ 80% |
| MET-002 | Time to first proposal | Median minutes from first request to first displayed proposal (study) | ≤ 3 min |
| MET-003 | Perceived usability | Mean SUS score (post-task questionnaire) | ≥ 70 |
| MET-004 | Conflict detection | Conflict-set scenarios (incl. calendar cases) whose blocking conflict is flagged ÷ scenarios | 100% |
| MET-005 | Lock integrity | Locked stops whose place, day or duration changed after regeneration | 0 |
| MET-006 | Saved-trip integrity | Saved itineraries changed without Save + unsaved edits lost, under failure injection | 0 |
| MET-007 | Guide grounding | Sampled answers fully supported by their cited evidence ÷ sampled answers (independent check, OQ-111) | ≥ 95% |
| MET-008 | Correct refusal | Out-of-evidence questions answered `insufficient_evidence` ÷ such questions | ≥ 90% |
| MET-011 rev. 3 | Catalog coverage — release gate (rev. 2 by DEC-022, rev. 3 by DEC-025) | Auto-published bilingual Đà Nẵng places that pass the automated publication gate, and of those the places in the Hội An area codes (`hoi-an-old-town`, `hoi-an-beaches-islands`); weekly from `GET /v1/admin/cities/summary`; plus a random 10% `audit-sample` CSV hand-checked by the owner and reported as an accuracy figure (a measurement, not a review; it includes AI-extracted facts, DEC-028) | ≥ 100 Đà Nẵng; ≥ 30 Hội An area; audit accuracy reported |
| MET-014 | Comparative accuracy and trust | Per participant, the same Đà Nẵng prompt in Gonarra and in ChatGPT or Gemini: errors per day (closed place, wrong hours, non-existent place), trust rating (Likert), whether the trust label was noticed | Gonarra errors/day < baseline; label noticed by a majority; targets fixed in the [test plan](../07-verification/TEST_PLAN.md) before the study |

Withdrawn as standalone metrics (thresholds kept where named): MET-009 → FR-061 acceptance; MET-010 → NFR-012;
MET-012 → NFR-033; MET-013 → CON-003 (10–15 consenting participants, ≥ 4 per language, by 2027-01-31).

## 3. Scope

**One city: Đà Nẵng**, including the Hội An area. The `cities` table keeps the multi-city model, but only `da-nang`
is enabled; Hà Nội, TP. Hồ Chí Minh and Huế are roadmap. One trip = one city, 1–3 days.

| Priority | Items |
|---|---|
| Must | Place search; proposal from a prompt plus preferences; timeline and map (iPhone / Apple Maps first for the demo, Android map deferred: DEC-023, OQ-135); Plan Health including calendar rules; edits and explicit Save; place card; city-level text Guide with sources; trust label on every surface; catalog-first research agent with an existence check and auto-promotion (Google Places in the design; open-data matching under DEC-023, OQ-134); booking handoff links (Agoda, Booking.com, Klook, 12Go); accounts and account deletion; automated ingestion pipeline (Wikidata, OSM, Wikipedia, Wikimedia Commons photos, owner CSV; DEC-024) with a deterministic publication gate, grounded AI-summarised descriptions (DEC-025) and AI-extracted facts from supplied sources (DEC-028); owner-maintained closure-rule YAML; operator takedown and release-gate count (DEC-022) |
| Should | Stop lock with single-day regeneration; voice questions (on-device STT/TTS); photo identification of published places within 300 m; Today view; trip deletion |
| Could | Indicative stay prices (LiteAPI), behind a flag, never stored |
| Won't (roadmap) | Other cities; multi-city trips; in-app booking or payment; flights; social features; check-in or GPS arrival detection; audio tours; turn-by-turn navigation; **unlabelled** web content; an LLM team leader or AgentOS service; human curator review, a review queue or an admin SPA (DEC-022) |

Won't items stay on the post-FYP roadmap with extension points but no implementation (DEC-004).

- **Cut order if late (DEC-003 rev. 1):** prices → photo → voice → lock/regeneration → iOS. **Never cut** bilingual
  content, the Đà Nẵng catalog gate (MET-011 rev. 3) or explicit Save.
- **Release gate:** MET-011 rev. 3 met (≥ 100 auto-published bilingual Đà Nẵng places passing the code gate,
  ≥ 30 in the Hội An area codes, 10% owner audit sample reported). The full release criteria (Must FRs, quality
  thresholds, Should/Could handling) are in [PRD §5](../03-analysis/PRD.md#5-release-and-acceptance-criteria).
- **Naming:** "Gonarra" is a working name; app name, slug, URL scheme, bundle IDs, deep links and hostnames do not
  change without a naming decision.

## 4. Business rules

| ID | Rule |
|---|---|
| BRU-002 rev. 2 | (Rev. 1 by DEC-022; rev. 2 by DEC-028.) A model may **propose** a `WEB_UNVERIFIED` candidate only through the research schema (name, source URL, existence-check identifier, Gonarra's existence verdict). It never publishes a place — publishing is the deterministic automated gate in code — and never invents facts, hours, prices, distances or durations. A model may **extract** a fact from supplied sources only: the fact must cite a supplied evidence id; code parses hours and prices into the fact shapes and rejects contact data; the fact is stored with `origin = AI_EXTRACTED`, a `STRONG`/`WEAK` grounding flag and its source link, and shown as "Summarised from sources". Anything else is rejected and stays unknown. |
| BRU-003 rev. 1 | (Revised by DEC-022; was "only after curator review".) A place is `VERIFIED` (published) only after it passes the automated publication gate: VI and EN content present, location inside the Đà Nẵng boundary, category set, every shown fact backed by an attributed source revision, licence recorded. Copy shows "Source-checked · <date>" / "Đã đối chiếu nguồn · <date>" and never claims human review. A web-found place stays `WEB_UNVERIFIED` until it is auto-promoted and published by the gate. |
| BRU-004 | Provider data is stored only under a named provider policy (provider, field, purpose, class, TTL); unknown combinations are not stored. |
| BRU-005 | Indicative prices are shown at viewing time only and never stored with a trip. |
| BRU-006 rev. 1 | (Revised by DEC-023.) Travel distance and duration come only from the configured routing provider (Google Routes in the design; self-hosted Valhalla intended for production), never from a model. **Time-boxed exception:** when `GONARRA_ENVIRONMENT` is `development`, `test` or `demo`, a straight-line estimate (haversine × 1.35) may be used; each such leg is marked `estimated`, raises the INFO conflict `LEG_ESTIMATED`, is shown with "≈" and is never cached. Staging and production never use estimates (the provider refuses to start). |
| BRU-007 | Each trip covers one city — Đà Nẵng, including the Hội An area — and 1–3 days. |
| BRU-008 | Logs contain no access tokens, precise locations, questions or transcripts, or full AI prompts. |

BRU-001 remains withdrawn (duplicate of FR-040). Persistence of trips only on explicit Save is FR-040; the privacy
rule BR-046 (nothing identifying reaches AI or search providers) is specified with the NFRs in the
[PRD](../03-analysis/PRD.md#3-non-functional-requirements).

## 5. Provider-data rules (summary of ADR-006)

- Every provider field is classified `CANONICAL`, `EPHEMERAL` (with TTL), `IDENTIFIER_ONLY` or `DENY` under a named
  policy row; unknown provider/field/purpose combinations are denied (BRU-004). Raw provider bodies are never logged.
- **Demo exception (DEC-023):** no Google Maps Platform product is called in the FYP demo; the Google rules below
  apply whenever Google is configured.
- Google Places: only `place_id` is stored canonically; lat/lng are ephemeral (≤ 30 days, pending OQ-124);
  `business_status` and opening hours are `DENY` — used at check time, never persisted.
- Google Routes: pairwise distance and duration cached ≤ 30 days keyed by (from, to, mode); day-start anchors are
  fixed points, never user GPS; straight-line estimates exist only in development/test/demo and are never cached
  (BRU-006 rev. 1).
- Tavily and fetched pages: search results and extracted text are ephemeral caches (7 days, pending OQ-122); a
  fetched page's URL, hash and `retrieved_at` are kept as an immutable source revision, which is the provenance of
  any AI-summarised description or AI-extracted fact (DEC-025, DEC-028).
- Open data (Wikidata; OSM via Overpass under ODbL with "© OpenStreetMap contributors"; Wikipedia extracts;
  Wikimedia Commons photos limited to CC0/PD/CC BY/CC BY-SA with a named author, hot-linked) keeps licence and
  attribution per source and per file and displays it (FR-008, FR-016; DEC-024).
- LiteAPI prices are never stored (BRU-005).
- Nothing identifying is sent to any provider: no account IDs, contact data or precise location (BR-046). Free-tier
  terms allow providers to use inputs, so the redactor is a correctness feature (RSK-002).

## 6. Constraints and assumptions

| ID | Statement | Impact if wrong / validation |
|---|---|---|
| CON-001 | Free tiers only: Gemini, Groq, Tavily, Google Maps Platform monthly credit (not used for the demo, DEC-023), Clerk free plan; AWS credits (USD 200) if hosted there. | Quota caps and fallback chains in the design (FR-106); provider terms re-read before coding against them. |
| CON-002 / ASM-004 rev. 1 | One person operates everything; no human review of catalog content (DEC-022); ≥ 15 places auto-published per week from 2026-11-16. | < 10/week for two weeks triggers the cut order; weekly count in `progress.md`. |
| CON-003 / ASM-002 | FYP submission early February 2027 (planning date 2027-02-01); study with 10–15 consenting participants (≥ 4 per language) by 2027-01-31. | Confirm the date with the faculty (OQ-002); ethics and consent (OQ-004). |
| CON-005 | Stack: Expo SDK 58 + Clerk (mobile); Python 3.12 FastAPI + SQLAlchemy 2 + Alembic; PostgreSQL 16 + PostGIS + pgvector; OR-Tools; `agno==3.1.12` with imports confined to `app/agents/` and `app/ai/`. | Pins from the day-1 spike (OQ-126, DEC-026). |
| ASM-017 | The Hội An area contains ≥ 30 places that can pass the gate. | MET-011 rev. 3 missed; count after 4 weeks of ingestion (2026-12-15). |
| ASM-018 | Tavily free tier (≈ 1 000 credits/month) covers development, enrichment runs and the study with daily caps and 300 credits reserved. | Research disabled near the study; ledger in `ai_quota_ledger` (OQ-122). |
| ASM-019 | Hybrid retrieval with `pg_trgm` + pgvector gives acceptable Vietnamese recall without `unaccent`/tsvector. | Guide misses evidence; retrieval spike on the Guide golden set (2027-01-06). |
| ASM-020 | Free-tier models extract facts from VI/EN pages well enough for `WEB_UNVERIFIED` candidates and AI-extracted facts. | Precision too low; manual count in the research spike and the audit sample. |
| ASM-021 | Agno agents run in-process in FastAPI without workers within a 2 GiB host. | Architecture change; load test before the study (2026-11-20). |
| ASM-022 | The post-merger Đà Nẵng boundary and the Hội An area can be defined from a licensed open dataset. | `OUTSIDE_CITY` rejects Hội An places; travel-area list instead of wards (OQ-121). |

Live risks (RSK-xxx) are tracked in the [decision log](../decisions.md#4-live-assumptions-and-risks).

## 7. Glossary

| Term | Definition |
|---|---|
| Published place (`VERIFIED`) | A place that passed the automated publication gate with attributed sources and VI/EN content; "source-checked", not human-reviewed; the only kind the selector may pick. |
| Automated publication gate | Deterministic code check that auto-publishes a candidate when VI and EN content, an in-boundary location, a category, an attributed source revision for each shown fact and a recorded licence are present; actor `system:gonarra-pipeline`. |
| Candidate place | An imported or auto-promoted place that has not passed the gate; never visible to travelers. |
| Operator | The owner acting through the operator allow-list: emergency unpublish and release-gate count only (was "curator"). |
| Web-found place (`WEB_UNVERIFIED`) | A place found by the research agent on the open web, checked for existence, shown with source URL and fetched date; saveable as a stop; caps Plan Health at `WARNING`. |
| Trust label | The `VERIFIED` / `WEB_UNVERIFIED` marker shown on every surface that names a place or cites evidence. |
| AI summary | A VI or EN description written by the grounded writer from supplied source text only (`translation_origin = AI_SUMMARY`), labelled "Tóm tắt từ nguồn" / "Summarised from sources" (DEC-025). |
| AI-extracted fact | An operational fact (address, opening hours, admission price) extracted from supplied sources with a cited evidence id (`origin = AI_EXTRACTED`, grounding `STRONG`/`WEAK`), labelled "Summarised from sources" with its source link (DEC-028). |
| Operational fact | A fact that affects a visit: opening hours, admission, address, entrance, closure; "unknown" when unsupported; stale after 180 days. |
| Area | A travel area of Đà Nẵng (e.g. Hội An Old Town, Sơn Trà) used for filtering, the gate and closure rules; not an administrative ward. |
| Proposal / preview revision | An unsaved, immutable itinerary version produced or edited; becomes the trip only on explicit Save. |
| Saved itinerary | The trip version the traveler explicitly saved; carries a revision number. |
| Leg | Travel between two consecutive stops; mode, distance and duration from the routing provider; in development/test/demo possibly an estimate marked `estimated` and shown with "≈". |
| Blocking conflict | A conflict with severity `BLOCKING` (e.g. closed at the planned time or date, leg unavailable, day window exceeded) that prevents Save. |
| Plan Health | Deterministic feasibility status `GOOD` / `WARNING` / `BLOCKED` with reasons, including calendar and trust conflicts; `INFO` conflicts never change it. |
| Closure rule | Owner-maintained calendar data in the versioned YAML file (weekly, date, lunar, season, ticket validity) applied by Plan Health; never written by a model. |
| Place card | The on-site view of a stop: names, driver address, entrance, dated facts, trust label, closure rules, directions. |
| Guide | City-, place- or trip-scoped grounded Q&A with validated citations; `insufficient_evidence` when the evidence does not support an answer. |
| Research agent | The Agno `researcher` role (Tavily search, page fetch, existence check) that proposes `WEB_UNVERIFIED` candidates and web evidence when the catalog is thin. |
| Curator queue | Withdrawn term (DEC-022); replaced by auto-promotion (FR-101 rev. 1). |

## 8. Change history

| Version | Date | Author | Change |
|---|---|---|---|
| 0.1–0.4 | 2026-11-04 | Lê Ngọc Tấn Hiền (drafted with Claude Code) | Kit-based BRD for five cities (BR-001..BR-050), two audit fix rounds; kept at tag `docs-sdlc-full` |
| 2.0 | 2026-11-09 | Lê Ngọc Tấn Hiền (drafted with Claude Code) | Rewritten from the condensed re-baseline requirements 1.2 (Đà Nẵng only, DEC-013..DEC-025) plus DEC-028 (BRU-002 rev. 2) under DEC-029; functional and non-functional requirements moved to the PRD |
