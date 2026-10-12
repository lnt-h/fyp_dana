# Danang TourGuide — Product Requirements

Version 1.2 | 2026-10-12 | Status: design baseline for review. Document control and evidence status: [Index](00-INDEX.md).

## Purpose and scope

A mobile companion for exploring curated Da Nang places, building an editable itinerary, and receiving reliable information during a visit. One developer; prioritise a complete vertical slice, explainable design and measurable evaluation. Exact deadline and academic requirements remain pending in Decisions.

Core journey: Explore → preferences/constraints → structured AI itinerary → edit/reorder → map → Start Trip → GPS arrival → human-recorded audio → contextual Ask AI → next stop. Optional P1 is separate from this P0 journey.

## Release scope

| Priority | Features |
|---|---|
| P0 | Curated POI, explore/search, detail, map, simple preferences, AI itinerary, editable stops, routing, Start Trip, foreground GPS arrival/manual fallback, human audio, contextual RAG, basic saves |
| P1 | Landmark recognition (provider TBD), Speech-to-Text input, Google OAuth |
| Future | Visual Taste, Travel DNA, CLIP/image recommendations, Six Degrees, weather adaptation, notifications, collections, offline mode |
| Removed | TTS, full AI voice conversation, microservices, initial Redis, booking/payment, social |

P1 starts only after P0 passes the core demo. Basic email/password identity supports cross-device private trips and saves; public Explore requires no account. Guest taste/merge is removed.

## Requirements and acceptance criteria

IDs remain stable in this baseline. Retired IDs are not reused; see [Project Decisions](09-Project-Decisions.md).

| ID | Priority | Requirement and acceptance |
|---|---|---|
| FR-POI-01 | P0 | Publish 30–50 curated POIs. Every published POI has a name, validated coordinates, tags/category, description, source references and licensed/authorised imagery. Unknown hours/prices stay unknown. |
| FR-EXP-01 | P0 | Search names/categories/tags, including Vietnamese names; filter category; no result yields a useful empty state. |
| FR-PLC-01 | P0 | Detail shows verified facts, sources, images and audio availability; distinguishes missing and outdated operational facts. |
| FR-MAP-01 | P0 | Explore pins and numbered itinerary pins are selectable; selection opens the correct POI detail/stop. |
| FR-PREF-01 | P0 | Collect trip date/day count, start point, interests, pace, same-day time window, qualitative budget preference and transport mode. Validate configured bounds; preferences editable only in draft. No photo inference. |
| FR-TRP-02 | P0 | AI proposes JSON itinerary from backend-supplied candidates. Reject unknown/unpublished/duplicate IDs, empty days, invalid schema and known infeasibility. Unknown facts/routes yield a provisional preview; explicit acceptance revalidates revision/expiry/facts. |
| FR-TRP-03 | P0 | Add/remove/reorder stops and edit visit duration. Apply edits atomically with revision checks; invalidate affected schedule/legs. Active current/visited prefix is immutable. An empty/conflicting planned day blocks Start until corrected. Changes are never silently overwritten. |
| FR-TRP-04 | P0 | Route legs use Routes responses; record mode and fetch time. Unavailable route durations are null, never invented by AI. |
| FR-TRV-01 | P0 | Start a nonempty accepted trip with no blocking constraints and acknowledged uncertainties, display current/next stop, complete/skip and finish. Exactly one current stop while active; none when draft/planned/completed. |
| FR-TRV-02 | P0 | Foreground app detects arrival only for current stop using accuracy/radius/dwell checks. Record one event per stop; denied/poor GPS offers manual arrival. Simulation is labelled. |
| FR-TRV-03 | P0 | 10–15 flagship POIs have reviewed human-recorded audio. Auto-play opt-in at Start Trip; arrival plays once when enabled. Play/pause/progress/transcript available. No asset means unavailable, never TTS. |
| FR-AI-01 | P0 | Ask AI uses current POI/trip, verified facts and retrieved source passages. Return answer with validated references or explicit insufficient-evidence/provider-unavailable state. |
| FR-SAV-01 | P0 | Authenticated user can save/unsave and list places; repeated save does not duplicate records; users cannot access another user's saves. |
| FR-AUTH-01 | P0 | Email/password registration/login, rotating refresh, session-checked logout and ownership protection for private trips/saves/AI context. |
| FR-CAM-01 | P1 | Captured landmark image may identify a published corpus POI or return unknown; never create a POI from model output. |
| FR-STT-01 | P1 | Microphone input becomes editable text; submission follows FR-AI-01. No spoken AI response. |
| FR-AUTH-02 | P1 | Google sign-in is an alternate login method with verified tokens and deliberate account linking. |

## Business rules

BR-01: POI IDs must belong to published corpus. BR-02: hours, prices and coordinates come from curated records, never model output. BR-03: historical claims require reviewed sources. BR-04: travel times come from Routes, with freshness metadata. BR-05: AI proposals require backend validation and user acceptance; edits are preserved. BR-06: no evidence means no factual answer. BR-07: citations must support the associated claim, not merely point to an existing source. BR-08: uncertain budget/hours must prevent guarantees of feasibility.

## Measurable quality targets (proposed acceptance baseline)

| ID | Target | Measurement |
|---|---|---|
| NFR-SEC-01 | No cross-user access in ownership tests; TLS, password hashing, server secrets | Integration tests and configuration inspection |
| NFR-PER-01 | Non-AI list/detail API p95 ≤2s at 10 concurrent test users | Seeded final corpus; report server latency separately from mobile network |
| NFR-REL-01 | Provider calls have bounded timeout/retry; no duplicate build/arrival | Timeout and replay tests; total request deadline documented in implementation |
| NFR-ACC-01 | Screen-reader labels, scalable text and measured contrast for core screens | Native device manual checks; document limits, do not claim whole-app WCAG certification |
| NFR-USAB-01 | ≥80% core UAT task completion; mean SUS ≥68 target | Proposed minimum five independent participants; report actual results and sample limitations |
| NFR-TRUST-01 | Zero observed invented operational facts/POI IDs; proposed ≥90% claim support and ≥90% appropriate refusal on labelled held-out subsets | Golden evaluation, claim-level review; not a universal correctness guarantee |

## Demo gate

All P0 critical cases pass; core flow runs entirely in-app. Demonstrate live AI and honest failure states; simulated GPS/route fixtures clearly labelled. Dataset/media rights checked. No unresolved major access-control or fabricated-fact defects. All requirement coverage and actual results recorded in [Test Plan](08-Test-Plan.md).

## Business trace, personas and interface requirements

| Requirement group | BRD source |
|---|---|
| FR-POI-01, FR-EXP-01, FR-PLC-01, FR-MAP-01 | BIZ-01 |
| FR-PREF-01, FR-TRP-02, FR-TRP-03, FR-TRP-04 | BIZ-02 |
| FR-TRV-01, FR-TRV-02, FR-TRV-03 | BIZ-03 |
| FR-AI-01 | BIZ-04 |
| FR-AUTH-01, FR-SAV-01 | BIZ-05 |
| NFR-SEC-01, NFR-PER-01, NFR-REL-01, NFR-ACC-01, NFR-USAB-01, NFR-TRUST-01 | BIZ-06 |
| FR-CAM-01, FR-STT-01, FR-AUTH-02 | BIZ-07 |

Primary persona (hypothesis): Vietnamese traveler unfamiliar with Da Nang who can use a mobile map but wants help planning and understanding places. Secondary: traveler who knows some places and wants quick edits and sourced explanations. Curator: developer responsible for publication and narration review. Research must validate these hypotheses.

Operating environment: online mobile phone with map/GPS/audio support; device/OS minimum versions TBD through compatibility spike. GPS arrival is foreground only; audio listening needs no microphone permission. Public discovery is unauthenticated; saves/trips/Ask require a user session. External interface requirements: map/route provider for geography/legs, language model and text embeddings for planning/RAG, storage for reviewed media. Communication uses authenticated HTTPS requests for private data. Provider/network failure never fabricates content or silently overwrites plans.

Capacity baseline: 30–50 published POIs, 10–15 narrated POIs, 10 concurrent acceptance-test users. No enterprise-scale target or production uptime SLA is committed. Restore rehearsal records RPO/RTO before deployment; recovery targets are agreed with budget. Localization P0 Vietnamese; unavailable English content explicitly labelled. Dates use Asia/Ho_Chi_Minh. Final day-count/transport limits remain O-04; proposed development slice is one day.

Business rules and every FR/NFR map to [stories](11-User-Stories.md), [traceability](14-Traceability.md), UI states and test plan. Success measures include completion/SUS, constraint-invalid proposals, unsupported facts and duplicate arrival events. Collect aggregate counts/latencies with model/corpus version; raw questions/GPS/images are not default analytics.

## Requirements review and release

Scope selected by user 2026-10-12. This version is the working requirements specification for review. Academic objective confirmation and trial-dependent limits remain open; resolve each before its dependent gate. Follow [review checklist](18-Document-Review.md).

## Acceptance interpretation

P0 behavior is required; quantitative corpus, performance, evaluation and sampling targets are project proposals recorded in Decisions and subject to review, not institutional mandates. Tests use fixed datasets/configurations and report denominators. A feature cannot be declared passed from documentation coverage alone. Audio automatic playback is guarded per trip/stop across retries/resume; users may intentionally replay.
Source facts, planning estimates and provider estimates are different data classes. Suggested visit duration is an estimate; budgetPreference is qualitative; route fetch time is not a guaranteed live ETA. Known conflicts block acceptance/Start, while unknown facts are disclosed. Preference changes after acceptance require a new draft and preserve the previous trip.
