# DaNavi — User stories and screen traceability

Version 1.3 | 2026-10-19 | Status: product scope selected; v1.3 screen/test alignment drafted for review. Document control and evidence status: [Index](00-INDEX.md).

## Story index

| Story | BRD | Requirement | Priority | Outcome | Use case | Screens |
|---|---|---|---|---|---|---|
| US-01 | BIZ-01 | FR-POI-01 | P0 | publish validated places | UC-15 | UI-01, UI-03 |
| US-02 | BIZ-01 | FR-EXP-01 | P0 | search places | UC-02 | UI-01 |
| US-03 | BIZ-01 | FR-PLC-01 | P0 | inspect place facts | UC-02 | UI-03 |
| US-04 | BIZ-01 | FR-MAP-01 | P0 | select places on a map | UC-03 | UI-02, UI-07 |
| US-05 | BIZ-05 | FR-SAV-01 | P0 | save and unsave places | UC-04 | UI-03, UI-11 |
| US-06 | BIZ-05 | FR-AUTH-01 | P0 | register and maintain a session | UC-01 | UI-12, UI-13 |
| US-07 | BIZ-02 | FR-PREF-01 | P0 | enter trip constraints | UC-05 | UI-04 |
| US-08 | BIZ-02 | FR-TRP-02 | P0 | review and accept an AI proposal | UC-06 | UI-05, UI-06 |
| US-09 | BIZ-02 | FR-TRP-03 | P0 | edit itinerary stops | UC-07 | UI-06 |
| US-10 | BIZ-02 | FR-TRP-04 | P0 | inspect route provenance | UC-06, UC-07 | UI-06, UI-07 |
| US-11 | BIZ-03 | FR-TRV-01 | P0 | progress through my trip | UC-08 | UI-08 |
| US-12 | BIZ-03 | FR-TRV-02 | P0 | record arrival safely | UC-09 | UI-08, UI-09 |
| US-13 | BIZ-03 | FR-TRV-03 | P0 | listen to reviewed recorded audio | UC-10 | UI-09 |
| US-14 | BIZ-04 | FR-AI-01 | P0 | ask about a place with sources | UC-11 | UI-03, UI-14 |
| US-15 | BIZ-07 | FR-CAM-01 | P1 | identify a supported landmark | UC-12 | UI-15 |
| US-16 | BIZ-07 | FR-STT-01 | P1 | dictate and edit a question | UC-13 | UI-14, UI-16 |
| US-17 | BIZ-07 | FR-AUTH-02 | P1 | use Google login | UC-14 | UI-12 |
| US-18 | BIZ-05 | FR-AUTH-03 | P0 | delete my account safely | UC-16 | UI-13, UI-20 |
| US-19 | BIZ-03 | FR-TRV-04 | P0 | use external directions and return safely | UC-17 | UI-07, UI-08, UI-09 |
| US-20 | BIZ-03 | FR-OFF-01 | P0 | cache trip essentials honestly | UC-18 | UI-07, UI-08, UI-09 |

## Acceptance criteria

### US-01 — publish validated places

As a curator, I want to publish validated places, so that visitors see reliable content.

Priority: P0. Trace: BIZ-01 → FR-POI-01 → UC-15; screens UI-01, UI-03; verification TC-01.

Given missing sources/entrance coordinates/source language/translation review/media rights, When I validate an import, Then publication is blocked with row errors. Given 15–20 valid reviewed records across Culture, Beach, Food and Nature, When published, Then they appear in the public corpus; only approved assets are eligible for preview or caching.

### US-02 — search places

As a traveler, I want to search places, so that I find appropriate stops.

Priority: P0. Trace: BIZ-01 → FR-EXP-01 → UC-02; screens UI-01; verification TC-02, TC-03.

Given a reviewed English name, Vietnamese name, romanized alias or tag, When I search/filter, Then the same matching published record appears without inventing translated content. Given no matches/network failure, Then empty/retry actions appear. Phase 3 adds alias-search verification from TC-41 onward.

### US-03 — inspect place facts

As a traveler, I want to inspect place facts, so that I can judge whether to visit.

Priority: P0. Trace: BIZ-01 → FR-PLC-01 → UC-02; screens UI-03; verification TC-04.

Given unknown hours/price, When I open detail, Then facts remain labelled unknown. Verified facts show source/date; unpublished IDs are inaccessible publicly.

### US-04 — select places on a map

As a traveler, I want to select places on a map, so that I can orient myself.

Priority: P0. Trace: BIZ-01 → FR-MAP-01 → UC-03; screens UI-02, UI-07; verification TC-05.

Given Explore/itinerary markers, When I select a marker, Then the matching place/stop opens; numbered pins follow stop sequence.

### US-05 — save and unsave places

As a traveler, I want to save and unsave places, so that I can return to my choices.

Priority: P0. Trace: BIZ-05 → FR-SAV-01 → UC-04; screens UI-03, UI-11; verification TC-23.

Given a guest taps Save, Then the app opens the login gate and never performs a private write anonymously. Given my account, When I save twice, Then one row exists. When I unsave twice, Then it remains absent. Another account cannot access my saves.

### US-06 — register and maintain a session

As a traveler, I want to register and maintain a session, so that my trips remain private.

Priority: P0. Trace: BIZ-05 → FR-AUTH-01 → UC-01; screens UI-12, UI-13; verification TC-24, TC-25.

Given valid registration/login, Then a renewable session is issued. Expired/revoked credentials and another owner ID cannot access private data. Logout revokes the refresh session. P0 provides no password-recovery flow and must show no misleading recovery promise.

### US-07 — enter trip constraints

As a traveler, I want to enter trip constraints, so that the plan reflects my needs.

Priority: P0. Trace: BIZ-02 → FR-PREF-01 → UC-05; screens UI-04; verification TC-06.

Given `dayCount` other than 1, transport other than `car`, invalid time bounds or a missing/invalid start point, When submitted, Then field errors appear without model calls. The start point comes from a map pin, current location or a reviewed preset and stores its source. A guest can complete the local form; an authenticated Generate creates the owner-scoped draft. Preference update after acceptance returns 409 and preserves the old trip.

### US-08 — review and accept an AI proposal

As an authenticated traveler, I want to review and accept an AI proposal, so that I control my planned itinerary.

Priority: P0. Trace: BIZ-02 → FR-TRP-02 → UC-06; screens UI-05, UI-06; verification TC-07, TC-08, TC-09, TC-22, TC-26.

Given a guest has completed preferences, When Generate is tapped, Then login opens, the form survives, the user returns to it and must tap Generate again; authentication never auto-runs AI. Given curated candidates, When generated, Then a validated structured preview and warnings appear; unknown IDs are rejected. **Save & customize** accepts with the current revision atomically and only then enables editing. Timeout/old revision preserves the prior plan. Phase 3 adds gate-preservation verification from TC-43 onward.

### US-09 — edit itinerary stops

As an authenticated traveler, I want to edit itinerary stops, so that I can adjust my day.

Priority: P0. Trace: BIZ-02 → FR-TRP-03 → UC-07; screens UI-06; verification TC-11, TC-12.

Given my current revision, When I edit, Then changes are atomic and affected routes stale. Invalid permutations/old revisions fail; current and visited stops remain immutable in an active trip. Empty/known-conflicting days block Start until corrected.

### US-10 — inspect route provenance

As an authenticated traveler, I want to inspect route provenance, so that I recognise uncertain travel times.

Priority: P0. Trace: BIZ-02 → FR-TRP-04 → UC-06, UC-07; screens UI-06, UI-07; verification TC-10, TC-11.

Given Routes success for P0 mode `car`, Then legs show mode/fetch time/revision. Given failure, Then duration is null with unavailable state. AI never supplies operational route durations. The map is a route preview, not turn-by-turn navigation.

### US-11 — progress through my trip

As an authenticated traveler, I want to progress through my trip, so that I know my next stop.

Priority: P0. Trace: BIZ-03 → FR-TRV-01 → UC-08; screens UI-08; verification TC-13.

Given a one-day planned trip with nonempty stops, no blocking conflicts and acknowledged uncertainty warnings, When started, Then one stop is current and the essentials prefetch begins. Complete/skip activates the next; the last transition completes the trip. An offline action is visibly pending until server reconciliation.

### US-12 — record arrival safely

As an authenticated traveler, I want to record arrival safely, so that guidance matches the current place.

Priority: P0. Trace: BIZ-03 → FR-TRV-02 → UC-09; screens UI-08, UI-09; verification TC-14, TC-15, TC-16, TC-30.

Given the current stop and an explicit **I've arrived** action or accurate foreground/resume dwell from a fresh fix, When arrival is reported repeatedly, Then one event exists. Denied/weak GPS keeps manual arrival available; simulation is labelled and rejected outside demo mode.

### US-13 — listen to reviewed recorded audio

As a traveler, I want to listen to reviewed English recorded audio, so that I learn about the place.

Priority: P0. Trace: BIZ-03 → FR-TRV-03 → UC-10; screen UI-09; verification TC-17, TC-18, TC-30, TC-40, TC-42.

Given approved human audio, a guest can play its bounded preview. In an authenticated active trip, playback/progress/transcript work and an offline-authorised asset may use the trip cache. Auto-play defaults off and occurs once per stop after opt-in. Missing audio remains unavailable without synthesis. Five flagship audio guides are P0; ten are stretch.

### US-14 — ask about a place with sources

As an authenticated traveler, I want to ask about a place with sources, so that I can check the answer.

Priority: P0. Trace: BIZ-04 → FR-AI-01 → UC-11; screens UI-03, UI-14; verification TC-19, TC-20, TC-21, TC-22, TC-29.

Given a guest taps Ask, Then login is required before any model call. Given authorised context and sufficient reviewed evidence, Then the single-turn answer displays supporting source cards. Visible history remains client-only and is not server conversation context. Absent/conflicting evidence yields uncertainty. Injected instructions cannot broaden context or create facts.

### US-15 — identify a supported landmark

As an authenticated traveler, I want to identify a supported landmark, so that I can inspect its curated detail.

Priority: P1. Trace: BIZ-07 → FR-CAM-01 → UC-12; screens UI-15; verification TC-31.

Given a supported image, Then a corpus candidate may be proposed for confirmation. Unknown/ambiguous scenes never create places; denied camera offers manual selection.

### US-16 — dictate and edit a question

As an authenticated traveler, I want to dictate and edit a question, so that I can use speech input.

Priority: P1. Trace: BIZ-07 → FR-STT-01 → UC-13; screens UI-14, UI-16; verification TC-32.

Given microphone permission, Then speech becomes editable text submitted through Ask. Failure/denial falls back to typing; answers remain text.

### US-17 — use Google login

As a traveler, I want to use Google login, so that I have another sign-in method.

Priority: P1. Trace: BIZ-07 → FR-AUTH-02 → UC-14; screens UI-12; verification TC-33.

Given verified provider token, Then deliberate account linking applies. Unverified or mismatched identity cannot take over an existing email account.

### US-18 — delete my account safely

As a signed-in traveler, I want to delete my account, so that I can remove my private DaNavi data.

Priority: P0. Trace: BIZ-05 → FR-AUTH-03 → UC-16; screens UI-13, UI-20; verification TC-38.

Given I explicitly confirm and re-enter the correct password, When I request deletion, Then all sessions are revoked and owner trips, days, stops, legs, arrivals, proposals, saves and idempotency records are hard-deleted through documented cascades. A wrong password or partial failure leaves the account usable and does not claim success. The confirmation discloses the approved security-log and backup-retention policy; P0 has no forgotten-password recovery route.

### US-19 — use external directions and return safely

As an active-trip traveler, I want directions in a familiar map app and a safe return to DaNavi, so that I can reach the reviewed entrance without losing trip state.

Priority: P0. Trace: BIZ-03 → FR-TRV-04 → UC-17; screens UI-07, UI-08, UI-09; verification TC-39.

Given the current stop, When I open directions, Then DaNavi uses an HTTPS Google/Apple Maps handoff with the reviewed entrance and car mode. When DaNavi returns to foreground, Then it refreshes the current trip/stop, requests a fresh location fix and offers **I've arrived** as the primary action; dwell is only a foreground helper. Failure to open the external app leaves the route preview and manual path available.

### US-20 — cache trip essentials honestly

As an active-trip traveler, I want essential stop content available during weak connectivity, so that I can continue without being told unavailable content was downloaded.

Priority: P0. Trace: BIZ-03 → FR-OFF-01 → UC-18; screens UI-07, UI-08, UI-09; verification TC-30, TC-40, TC-44.

Given I start an accepted trip, When prefetch runs, Then text, transcripts and offline-authorised audio show per-item and overall progress within the configured limit. Stale revisions are invalidated. Failure offers retry or continue online-only and never reports complete. No map or route is cached. Offline complete/skip/arrival actions remain visibly pending until reconciled.

## Cross-cutting quality

| Requirement | BRD | Design responsibility | Verification |
|---|---|---|---|
| NFR-SEC-01 | BIZ-05, BIZ-06 | Identity/all private modules | TC-24, TC-25, TC-38 |
| NFR-PER-01 | BIZ-06 | Places/database | TC-27 |
| NFR-REL-01 | BIZ-06 | Trips/AI/Routing/cache/versioning | TC-22, TC-26, TC-30, TC-40, TC-44, TC-45 |
| NFR-ACC-01 | BIZ-06 | Native UI | TC-28 |
| NFR-USAB-01 | BIZ-06 | Core journey | UAT-01, UAT-02, UAT-03, UAT-04, UAT-05 |
| NFR-TRUST-01 | BIZ-01, BIZ-04, BIZ-06 | Places/AI/Routing | TC-08, TC-19, TC-20, TC-21, TC-29 |

## Screen ownership

Every allocated UI ID is defined in [UI design](07-UI-UX-Design.md). The editable P0 concept frames are represented in [wireframes](UI_UX_design/wireframes.html). UI-10 is retired, UI-19 identifies Trips and UI-20 identifies account-deletion confirmation; retired IDs are never reused. Optional P1 screens are excluded from P0 acceptance. Curator CLI is an engineering workflow, not a new admin app screen. Split implementation tasks smaller than stories; preserve FR IDs when refining acceptance.

## Review status

v1.3 product direction, screen IDs and planned tests are drafted; story acceptance criteria still await product/technical review. No runtime result is claimed. Reviewer names TBD.
