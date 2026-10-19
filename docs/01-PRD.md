# DaNavi — Product Requirements

Version 1.3 | 2026-10-19 | Status: product scope selected; technical and academic review still required. Document control and evidence status: [Index](00-INDEX.md).

## Purpose and scope

A mobile companion for international first-time visitors to explore curated Da Nang places in English, build an editable one-day itinerary, and receive source-aware help during a visit. One developer; prioritise a complete vertical slice, explainable design and measurable evaluation. Exact deadline and academic requirements remain pending in Decisions.

Core journey: Welcome → Home → Explore/Detail → preferences → Generate/login gate when needed → structured Preview → **Save & customize** → Edit → route preview → Trip Ready → external directions/Active Trip → **I've arrived** or foreground dwell → human-recorded Audio/contextual Ask → next stop → Completed. Optional P1 is separate from this P0 journey.

## Release scope

| Priority | Features |
|---|---|
| P0 | English-first curated POIs, alias search, detail/map, one-day preferences, authenticated AI itinerary, editable accepted stops, car route preview, Start Trip, external directions handoff, foreground/manual arrival, five flagship human audio guides, authenticated single-turn RAG, basic saves, read-only trip essentials cache, account deletion |
| P1 | Landmark recognition (provider TBD), Speech-to-Text input, Google OAuth |
| Future | Visual Taste, Travel DNA, CLIP/image recommendations, Six Degrees, weather adaptation, notifications, collections, multi-day planning, full offline maps/routing |
| Removed | TTS, full AI voice conversation, background GPS, in-app turn-by-turn navigation, P0 password recovery, microservices, initial Redis, booking/payment, social |

P1 starts only after P0 passes the core demo. Guests can Explore, open Detail and play an audio preview. Save, Ask and Generate require basic email/password identity. The Generate gate preserves the completed form through login, returns to the form and waits for a second explicit Generate tap. Guest taste/merge is removed.

## Requirements and acceptance criteria

IDs remain stable in this baseline. Retired IDs are not reused; see [Project Decisions](09-Project-Decisions.md).

| ID | Priority | Requirement and acceptance |
|---|---|---|
| FR-POI-01 | P0 | Publish 15–20 curated POIs across Culture, Beach, Food and Nature; represent urban places as Culture plus tags. Every published POI has an English display name/content reviewed against its sources, validated entrance coordinates, tags/category, description, source references, source language and licensed/authorised imagery. Unknown hours/prices stay unknown. Thirty POIs are stretch, not P0. |
| FR-EXP-01 | P0 | Search reviewed English names, Vietnamese names, romanized aliases, categories and tags; filter the four P0 categories; no result yields a useful empty state. Alias matching does not substitute unreviewed translated content. |
| FR-PLC-01 | P0 | Detail shows verified facts, sources, images and audio availability; distinguishes missing and outdated operational facts. |
| FR-MAP-01 | P0 | Explore pins and numbered itinerary pins are selectable; selection opens the correct POI detail/stop. |
| FR-PREF-01 | P0 | Collect trip date, fixed `dayCount=1`, required start coordinates/source, interests, pace, same-day time window, qualitative budget preference and fixed P0 transport `car`. Start source is `map_pin`, `current_location` or curated `preset`; no address autocomplete. Validate configured bounds. A guest may fill the local form, but only an authenticated request creates or updates an owner-scoped draft. Preferences are editable only in draft. No photo inference. |
| FR-TRP-02 | P0 | Generate requires authentication; the login round trip preserves inputs and never auto-submits. AI proposes a JSON itinerary from backend-supplied candidates. Reject unknown/unpublished/duplicate IDs, empty days, invalid schema and known infeasibility. Unknown facts/routes yield a provisional preview; **Save & customize** explicitly accepts after revalidating revision/expiry/facts, after which editing becomes available. |
| FR-TRP-03 | P0 | Add/remove/reorder stops and edit visit duration. Apply edits atomically with revision checks; invalidate affected schedule/legs. Active current/visited prefix is immutable. An empty/conflicting planned day blocks Start until corrected. Changes are never silently overwritten. |
| FR-TRP-04 | P0 | Route legs use Routes responses for the single P0 mode `car`; record mode and fetch time. Unavailable route durations are null, never invented by AI. In-app route presentation is preview only. |
| FR-TRV-01 | P0 | Start a nonempty accepted trip with no blocking constraints and acknowledged uncertainties, initiate the FR-OFF-01 prefetch, display current/next stop, complete/skip and finish. Exactly one current stop while active; none when draft/planned/completed. Offline mutations are labelled pending until reconciliation. |
| FR-TRV-02 | P0 | **I've arrived** is the primary arrival action. In foreground, including after return from external directions, the app may detect arrival only for the current stop using a fresh fix plus accuracy/radius/dwell checks. Record one event per stop; denied/poor GPS offers manual arrival. Simulation is labelled. |
| FR-TRV-03 | P0 | Five flagship POIs have reviewed English human-recorded audio; ten are stretch. Guests may hear a clearly bounded preview. For an authenticated active trip, auto-play opt-in occurs at Start Trip and arrival plays once when enabled. Play/pause/progress/transcript are available. No asset means unavailable, never TTS. |
| FR-TRV-04 | P0 | From the current stop, open Google Maps or Apple Maps through an HTTPS directions URL using the reviewed entrance coordinates and `car` mode. On foreground return, fetch a fresh location and reconcile active-trip/current-stop state before offering dwell, **I've arrived**, complete or skip. Do not claim in-app turn-by-turn or background tracking. |
| FR-AI-01 | P0 | Ask requires authentication and uses current POI/trip, verified facts and retrieved source passages. Each server request is single-turn; any visible history is client-only and is not sent as an implicit conversation. Return an answer with answer-level validated source cards or explicit insufficient-evidence/provider-unavailable state. Claim-level support is measured; claim-level citation presentation is stretch. |
| FR-SAV-01 | P0 | Authenticated user can save/unsave and list places; repeated save does not duplicate records; users cannot access another user's saves. |
| FR-AUTH-01 | P0 | Email/password registration/login, rotating refresh, session-checked logout and ownership protection for private trips/saves/AI context. Password recovery is not included in P0 and must not be implied. |
| FR-AUTH-03 | P0 | A signed-in user can request account deletion through `POST /account/delete` after password reauthentication and explicit confirmation. Success revokes all sessions and hard-deletes owner trips, trip days/stops, route/day-start legs, arrival events, proposals, saves and idempotency records through defined cascades. Security-log and backup retention follows O-08 and is disclosed honestly. Before public Google Play release, provide the required discoverable external deletion-request web resource and accurate Data safety declaration. |
| FR-OFF-01 | P0 | At Start Trip, prefetch read-only text, transcript and offline-authorised audio for accepted stops within a configured size limit. Bind the cache to itinerary/content revisions and invalidate stale entries. Show per-item/overall completion and allow retry or continue online-only; never claim a complete download after failure. No offline map/routing. Offline complete/skip/arrival actions remain pending and reconcile before being shown as synced. |
| FR-CAM-01 | P1 | Captured landmark image may identify a published corpus POI or return unknown; never create a POI from model output. |
| FR-STT-01 | P1 | Microphone input becomes editable text; submission follows FR-AI-01. No spoken AI response. |
| FR-AUTH-02 | P1 | Google sign-in is an alternate login method with verified tokens and deliberate account linking. |

## Business rules

BR-01: POI IDs must belong to the published corpus. BR-02: hours, prices and entrance coordinates come from curated records, never model output. BR-03: historical claims and English translations require reviewed sources and source-language metadata. BR-04: travel times come from Routes, with freshness metadata. BR-05: AI proposals require backend validation and explicit acceptance before editing; edits are preserved. BR-06: no evidence means no factual answer. BR-07: displayed source cards must support the answer; evaluation separately measures claim support. BR-08: uncertain budget/hours must prevent guarantees of feasibility. BR-09: public access is limited to Explore, Detail and bounded audio preview; Save, Ask and Generate require authentication. BR-10: external directions do not imply background arrival tracking. BR-11: cached data is revision-bound and read-only; pending offline actions are not represented as server-confirmed. BR-12: account deletion does not imply immediate physical removal from retained backups when O-08 specifies otherwise.

## Measurable quality targets (proposed acceptance baseline)

| ID | Target | Measurement |
|---|---|---|
| NFR-SEC-01 | No cross-user access in ownership tests; TLS, password hashing, server secrets | Integration tests and configuration inspection |
| NFR-PER-01 | Non-AI list/detail API p95 ≤2s at 10 concurrent test users; measure end-to-end itinerary generation against the proposed 60-second deadline without calling an unmeasured target met | Seeded final corpus; report server/provider/mobile-network latency separately |
| NFR-REL-01 | Provider calls have bounded timeout/retry; no duplicate build/arrival; active trip and pending stable keys recover after process kill; API exposes minimum-app compatibility and rejects unsupported clients explicitly | Timeout, replay, relaunch and version-gate tests; total request deadline/version policy documented in implementation |
| NFR-ACC-01 | Screen-reader labels, scalable text and measured contrast for core screens | Native device manual checks; document limits, do not claim whole-app WCAG certification |
| NFR-USAB-01 | ≥80% core UAT task completion; mean SUS ≥68 target | Proposed minimum five independent participants; report actual results and sample limitations |
| NFR-TRUST-01 | Zero observed invented operational facts/POI IDs; proposed ≥90% claim support and ≥90% appropriate refusal on labelled held-out subsets | Golden evaluation, claim-level review; not a universal correctness guarantee |

## Demo gate

All P0 critical cases pass across the mobile flow and its declared external directions handoff. Demonstrate live AI, login-gate form preservation, return reconciliation, cache/pending states and honest provider failures; simulated GPS/route fixtures are clearly labelled. Dataset, translation, media and offline-use rights are checked. No unresolved major access-control, deletion-cascade or fabricated-fact defects. All requirement coverage and actual results are recorded in [Test Plan](08-Test-Plan.md).

## Business trace, personas and interface requirements

| Requirement group | BRD source |
|---|---|
| FR-POI-01, FR-EXP-01, FR-PLC-01, FR-MAP-01 | BIZ-01 |
| FR-PREF-01, FR-TRP-02, FR-TRP-03, FR-TRP-04 | BIZ-02 |
| FR-TRV-01, FR-TRV-02, FR-TRV-03, FR-TRV-04, FR-OFF-01 | BIZ-03 |
| FR-AI-01 | BIZ-04 |
| FR-AUTH-01, FR-AUTH-03, FR-SAV-01 | BIZ-05 |
| NFR-SEC-01, NFR-PER-01, NFR-REL-01, NFR-ACC-01, NFR-USAB-01, NFR-TRUST-01 | BIZ-06 |
| FR-CAM-01, FR-STT-01, FR-AUTH-02 | BIZ-07 |

Primary persona (hypothesis): an English-speaking international first-time visitor to Da Nang who can use a mobile map but needs help matching place names, planning a feasible day and understanding local places. Secondary: a returning or better-informed international visitor who wants quick edits and sourced explanations. Curator: developer responsible for publication and narration workflow; a bilingual reviewer checks English translations against the source language. Research must validate these hypotheses.

Operating environment: mobile phone with map/GPS/audio support; device/OS minimum versions TBD through compatibility spike. GPS arrival is foreground/resume only; audio listening needs no microphone permission. Public access covers Explore, Detail and preview audio; Save, Ask and Generate require a session. External interfaces are Google/Apple Maps HTTPS handoff, a map/route provider for geography/legs, language model and text embeddings for planning/RAG, and storage for reviewed media. Communication uses authenticated HTTPS requests for private data. Provider/network failure never fabricates content, claims false sync/download success or silently overwrites plans.

Capacity baseline: 15–20 published POIs, five narrated flagship POIs and 10 concurrent acceptance-test users. Thirty POIs and ten audio guides are stretch. No enterprise-scale target or production uptime SLA is committed. Restore rehearsal records RPO/RTO before deployment; recovery targets are agreed with budget. P0 app copy and reviewed content are English; search retains reviewed Vietnamese names and romanized aliases. Display local times explicitly in the Da Nang `Asia/Ho_Chi_Minh` zone and prices in VND. P0 planning is one day and car/ride-hailing only; maximum stops and duration bounds remain O-04.

Business rules and every FR/NFR map to [stories](11-User-Stories.md), [traceability](14-Traceability.md), UI states and test plan. Success measures include completion/SUS, constraint-invalid proposals, unsupported facts and duplicate arrival events. Collect aggregate counts/latencies with model/corpus version; raw questions/GPS/images are not default analytics.

## Requirements review and release

v1.3 direction selected by user 2026-10-19. This version is the working requirements specification for review. Academic objective confirmation and trial-dependent limits remain open; resolve each before its dependent gate. Follow [review checklist](18-Document-Review.md).

## Acceptance interpretation

P0 behavior is required; quantitative corpus, performance, evaluation and sampling targets are project proposals recorded in Decisions and subject to review, not institutional mandates. Tests use fixed datasets/configurations and report denominators. A feature cannot be declared passed from documentation coverage alone. Audio automatic playback is guarded per trip/stop across retries/resume; users may intentionally replay.
Source facts, planning estimates and provider estimates are different data classes. Suggested visit duration is an estimate; budgetPreference is qualitative; route fetch time is not a guaranteed live ETA. Known conflicts block acceptance/Start, while unknown facts are disclosed. Preference changes after acceptance require a new draft and preserve the previous trip.
