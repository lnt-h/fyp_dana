# Danang TourGuide — Product Requirements

Version 1.0 | 2026-09-30 | Approved direction; implementation not yet verified.

## Purpose and scope
A mobile companion for exploring curated Da Nang places, building an editable itinerary, and receiving reliable information during a visit. One developer; prioritise a complete vertical slice, explainable design and measurable evaluation. Exact deadline remains pending; do not inherit the previous eight-month schedule.

Core journey: Explore → preferences/constraints → structured AI itinerary → edit/reorder → map → Start Trip → GPS arrival → human-recorded audio → contextual Ask AI → optional landmark scan → next stop.

## Release scope
| Priority | Features |
|---|---|
| P0 | Curated POI, explore/search, detail, map, simple preferences, AI itinerary, editable stops, routing, Start Trip, foreground GPS arrival/manual fallback, human audio, contextual RAG, basic saves |
| P1 | Gemini Vision landmark recognition, Speech-to-Text input, Google OAuth |
| Future | Visual Taste, Travel DNA, CLIP/image recommendations, Six Degrees, weather adaptation, notifications, collections, offline mode |
| Removed | TTS, full AI voice conversation, microservices, initial Redis, booking/payment, social |

P1 starts only after P0 passes the core demo. Basic email/password identity supports cross-device private trips and saves; public Explore requires no account. Guest taste/merge is removed.

## Requirements and acceptance criteria
IDs remain stable in this baseline. Removed legacy IDs are not reused; see [Project Decisions](09-Project-Decisions.md).

| ID | Priority | Requirement and acceptance |
|---|---|---|
| FR-POI-01 | P0 | Publish 30–50 curated POIs. Every published POI has a name, validated coordinates, tags/category, description, source references and licensed/authorised imagery. Unknown hours/prices stay unknown. |
| FR-EXP-01 | P0 | Search names/categories/tags, including Vietnamese names; filter category; no result yields a useful empty state. |
| FR-PLC-01 | P0 | Detail shows verified facts, sources, images and audio availability; distinguishes missing and outdated operational facts. |
| FR-MAP-01 | P0 | Explore pins and numbered itinerary pins are selectable; selection opens the correct POI detail/stop. |
| FR-PREF-01 | P0 | Collect trip date/day count, start point, interests, pace, time window, budget preference and transport mode. Validate inputs; no photo inference. |
| FR-TRP-02 | P0 | AI proposes JSON itinerary from backend-supplied candidates. Reject unknown/unpublished IDs and invalid schema; flag unsatisfied constraints. |
| FR-TRP-03 | P0 | Add/remove/reorder stops and edit visit duration. Apply edits atomically; update schedule/legs or mark stale. Changes are never silently overwritten. |
| FR-TRP-04 | P0 | Route legs use Routes responses; record mode and fetch time. Unavailable route durations are null, never invented by AI. |
| FR-TRV-01 | P0 | Start a valid planned trip, display current/next stop, complete or skip a stop and finish trip. Only one current stop at a time. |
| FR-TRV-02 | P0 | Foreground app detects arrival only for current stop using accuracy/radius/dwell checks. Record one event per stop; denied/poor GPS offers manual arrival. Simulation is labelled. |
| FR-TRV-03 | P0 | 10–15 flagship POIs have reviewed human-recorded audio. Auto-play opt-in at Start Trip; arrival plays once when enabled. Play/pause/progress/transcript available. No asset means unavailable, never TTS. |
| FR-AI-01 | P0 | Ask AI uses current POI/trip, verified facts and retrieved source passages. Return answer with validated references or explicit insufficient-evidence/provider-unavailable state. |
| FR-SAV-01 | P0 | Authenticated user can save/unsave and list places; repeated save does not duplicate records; users cannot access another user's saves. |
| FR-AUTH-01 | P0 | Email/password login and session renewal; protect private trips/saves and AI trip context by ownership. |
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
| NFR-USAB-01 | ≥80% core UAT task completion; mean SUS ≥68 target | At least five independent participants; report actual results |
| NFR-TRUST-01 | No invented operational facts/POI IDs in evaluation set | Golden evaluation, claim-level review; not a universal correctness guarantee |

## Demo gate
All P0 critical cases pass; core flow runs entirely in-app. Demonstrate live AI and honest failure states; simulated GPS/route fixtures clearly labelled. Dataset/media rights checked. No unresolved major access-control or fabricated-fact defects. All requirement coverage and actual results recorded in [Test Plan](08-Test-Plan.md).
