# Danang TourGuide — Detailed use cases

Version 1.2 | 2026-10-12 | Status: design baseline for review. Document control and evidence status: [Index](00-INDEX.md).

## Boundary and actors

Danang TourGuide boundary includes mobile/API/curation workflow; providers are secondary external actors. Traveler can explore/listen publicly; private trips/saves/Ask require authentication. Curator works through restricted scripts. [Scenarios diagram](diagrams/scenarios-view.drawio) uses actor associations and system boundary; not every relationship needs include/extend.

## Shared contract

Private cases authenticate the caller and verify owner/parent membership. Rejected writes leave existing records unchanged; an uncertain network outcome requires reconciliation using GET before a new action. Provider calls use bounded deadlines. Accessibility applies to all displayed outcomes. Case-specific preconditions and exceptions below take precedence over generic workflow descriptions.

P1 cases UC-12–14 are optional backlog specifications, excluded from P0 delivery and acceptance. UC-15 is a curator CLI workflow, not a traveler-facing administration screen.

## UC-01 — Register/login/refresh/logout

Primary actor: Traveler. Secondary actors: none required beyond system dependencies.
Trigger: Register/login/refresh/logout. Preconditions: User supplies credentials or valid refresh token.
Trace: US-06 / FR-AUTH-01 / BIZ-05. Priority: P0.

### Main success flow

1. User submits credentials.
2. Identity validates/hashes or verifies credentials.
3. System issues access and refresh session.
4. User accesses private data.

### Alternatives and exceptions

2a. Invalid input → 400; incorrect credentials/expired refresh → 401. 3a. Rotated-token replay is rejected. Logout revokes refresh session.

### Postconditions and data

Success: Authenticated session or revoked logout session. Data: users/sessions; no plain passwords/tokens.

## UC-02 — Search or open published place

Primary actor: Traveler. Secondary actors: none required beyond system dependencies.
Trigger: Search or open published place. Preconditions: Curated published corpus is available.
Trace: US-02 / FR-EXP-01 / BIZ-01; US-03 / FR-PLC-01 / BIZ-01. Priority: P0.

### Main success flow

1. Traveler submits search/filter.
2. System returns paginated published matches.
3. Traveler selects a place.
4. System shows facts/sources, images and audio availability.

### Alternatives and exceptions

2a. No match → empty state. 2b. Network error → retry. 4a. Unknown facts remain unknown; missing/unpublished POI → 404.

### Postconditions and data

Success: Correct published detail without invented facts. Data: name/category/tags; locale; provenance.

## UC-03 — Select a map marker

Primary actor: Traveler. Secondary actors: Map provider.
Trigger: Select a map marker. Preconditions: Published coordinates or authorised itinerary exist.
Trace: US-04 / FR-MAP-01 / BIZ-01. Priority: P0.

### Main success flow

1. System loads map and appropriate pins.
2. Traveler selects pin.
3. System opens matching place or ordered stop.

### Alternatives and exceptions

1a. Map/provider failure → list fallback. 3a. Missing route → unavailable labels; no invented time.

### Postconditions and data

Success: Selection corresponds to intended place/stop. Data: coordinates; stop sequence; nullable legs.

## UC-04 — Save/unsave place

Primary actor: Authenticated traveler. Secondary actors: none required beyond system dependencies.
Trigger: Save/unsave place. Preconditions: Valid session; published place for save.
Trace: US-05 / FR-SAV-01 / BIZ-05. Priority: P0.

### Main success flow

1. Traveler requests save.
2. System verifies published place/owner and inserts idempotently.
3. Traveler requests saved list or unsave.
4. System returns/removes only owner rows.

### Alternatives and exceptions

2a. Repeated save creates no duplicate. 4a. Repeated unsave remains successful. Foreign ownership never exposes rows.

### Postconditions and data

Success: Owner saved list reflects intended action. Data: owner and place IDs.

## UC-05 — Create/update trip preferences

Primary actor: Authenticated traveler. Secondary actors: none required beyond system dependencies.
Trigger: Create/update trip preferences. Preconditions: Valid session.
Trace: US-07 / FR-PREF-01 / BIZ-02. Priority: P0.

### Main success flow

1. Traveler supplies dates/start/interests/pace/window/budget/mode.
2. System validates configured ranges.
3. System creates or revises owner draft.

### Alternatives and exceptions

2a. Invalid dates/window/coordinates → field errors; no model call. 3a. Preferences update only in draft; otherwise 409 preserves existing plan. Title-only updates use current revision. Old revision → 409.

### Postconditions and data

Success: Persisted validated preferences. Data: TripPreferences; title; expectedRevision for edit.

## UC-06 — Build then accept itinerary

Primary actor: Authenticated traveler. Secondary actors: AI and Routes providers.
Trigger: Build then accept itinerary. Preconditions: Draft/planned trip; configured limits; current revision.
Trace: US-08 / FR-TRP-02 / BIZ-02; US-10 / FR-TRP-04 / BIZ-02. Priority: P0.

### Main success flow

1. Traveler requests generation.
2. System checks owner/revision/idempotency and loads published candidates.
3. AI proposes IDs/order/durations; backend validates.
4. Routes resolves travel legs and scheduler checks constraints.
5. System stores preview and shows warnings.
6. Traveler explicitly accepts.
7. System revalidates versions and persists plan atomically.

### Alternatives and exceptions

3a. Malformed/unknown ID → rejected proposal. 4a. Known conflict → 422/constraints to revise; unknown facts/unavailable route → provisional preview. 3b/4b. Timeout → 503 retaining old plan. 7a. Expired/stale/changed corpus → 409/422 and regenerate.

### Postconditions and data

Success: Owner planned trip, ordered stops and route provenance. Data: trip/revision/key; candidate corpus; proposal ID.

## UC-07 — Add/remove/reorder/change duration

Primary actor: Authenticated traveler. Secondary actors: none required beyond system dependencies.
Trigger: Add/remove/reorder/change duration. Preconditions: Editable owner trip; matching revision.
Trace: US-09 / FR-TRP-03 / BIZ-02; US-10 / FR-TRP-04 / BIZ-02. Priority: P0.

### Main success flow

1. Traveler submits edit/full reorder permutation.
2. System validates ownership/membership and immutable current/visited prefix.
3. System atomically updates order/durations, increments revision and marks affected legs stale.
4. Route refresh recalculates outside transaction and applies only to same revision.

### Alternatives and exceptions

2a. Invalid permutation/membership → 400/404. 3a. Revision conflict → 409; no partial writes. 4a. Provider failure → unavailable; later revision → discard stale result.

### Postconditions and data

Success: Saved edits preserved with honest route freshness. Data: stop/day IDs; duration; orderedStopIds; revision.

## UC-08 — Start/complete/skip stops

Primary actor: Authenticated traveler. Secondary actors: none required beyond system dependencies.
Trigger: Start/complete/skip stops. Preconditions: Planned trip with nonempty days, no blocking warnings and acknowledgement of uncertainties.
Trace: US-11 / FR-TRV-01 / BIZ-03. Priority: P0.

### Main success flow

1. Traveler starts trip.
2. System marks active and first current stop.
3. Traveler completes/skips current stop.
4. System atomically activates next or completes trip.

### Alternatives and exceptions

1a. Invalid state/old revision → 409; empty day/known conflict or missing uncertainty acknowledgement → 422. 3a. Noncurrent or already terminal stop → 409 except exact replay. Pause only stops local watcher; resume reconciles state.

### Postconditions and data

Success: One current stop or completed trip. Data: trip/current stop; revision; acknowledgement/key.

## UC-09 — GPS dwell or manual arrival

Primary actor: Authenticated traveler. Secondary actors: none required beyond system dependencies.
Trigger: GPS dwell or manual arrival. Preconditions: Active trip/current stop; foreground watcher for GPS.
Trace: US-12 / FR-TRV-02 / BIZ-03. Priority: P0.

### Main success flow

1. App checks current-stop target, accuracy and dwell.
2. App sends arrival evidence and stable event key.
3. Backend verifies owner/state/plausibility and deduplicates by stop.
4. App shows arrival method and audio/Ask actions.

### Alternatives and exceptions

1a. Denied/weak GPS → manual arrival. 2a. Offline → local pending badge/retry; no synced claim. 3a. Wrong stop → conflict; simulation rejected outside demo. 3b. Prior identical event → return original even after progression.

### Postconditions and data

Success: One labelled arrival event; stop not automatically completed. Data: method/time; optional accuracy/distance; demo flag.

## UC-10 — Play audio or opt-in arrival playback

Primary actor: Traveler. Secondary actors: Media storage.
Trigger: Play audio or opt-in arrival playback. Preconditions: Published POI; approved human audio for locale.
Trace: US-13 / FR-TRV-03 / BIZ-03. Priority: P0.

### Main success flow

1. System obtains reviewed audio metadata and access URL.
2. Traveler taps play or opted-in arrival plays once.
3. Player supports pause/seek/progress/transcript.

### Alternatives and exceptions

1a. Missing asset/language → unavailable; no synthesis. 2a. Connection failure → retry/transcript. Interruptions update player; intentional replay allowed.

### Postconditions and data

Success: Reviewed human audio heard or honest unavailable state. Data: place/locale; asset version/duration/transcript.

## UC-11 — Ask question

Primary actor: Authenticated traveler. Secondary actors: Embedding/LLM provider.
Trigger: Ask question. Preconditions: Valid session; published place or owned trip context.
Trace: US-14 / FR-AI-01 / BIZ-04. Priority: P0.

### Main success flow

1. Traveler submits question/context.
2. Backend constructs permitted context and loads facts.
3. System retrieves reviewed compatible chunks.
4. Model drafts sourced answer; backend validates format/IDs/facts.
5. App shows answer and source links.

### Alternatives and exceptions

2a. Foreign trip → 404. 3a. Empty/weak/conflicting evidence → insufficient_evidence. 4a. Unsupported factual output → withheld. Provider timeout → unavailable; injected instructions cannot change allowlist.

### Postconditions and data

Success: Grounded answer or explicit refusal/failure. Data: question; place/trip; locale; source/chunk/fact IDs.

## UC-12 — Capture landmark image (P1)

Primary actor: Authenticated traveler. Secondary actors: Vision/storage provider.
Trigger: Capture landmark image (P1). Preconditions: P1 enabled; permission; private upload policy agreed.
Trace: US-15 / FR-CAM-01 / BIZ-07. Priority: P1.

### Main success flow

1. User captures image.
2. System validates private short-lived upload.
3. Vision proposes supported corpus candidates.
4. User confirms candidate or selects manually.

### Alternatives and exceptions

1a. Denied camera → manual selection. 3a. Unknown/ambiguous → labelled result; never create a POI. Expired media is removed.

### Postconditions and data

Success: Confirmed existing POI or unknown. Data: private media ID; candidate corpus.

## UC-13 — Dictate question (P1)

Primary actor: Authenticated traveler. Secondary actors: none required beyond system dependencies.
Trigger: Dictate question (P1). Preconditions: P1 enabled; microphone permission.
Trace: US-16 / FR-STT-01 / BIZ-07. Priority: P1.

### Main success flow

1. User records short question.
2. System transcribes into editable text.
3. User edits/confirms and submits through UC-11.

### Alternatives and exceptions

1a. Denied permission/failure → keyboard. No spoken answer/TTS.

### Postconditions and data

Success: Confirmed text question. Data: temporary audio; editable transcript.

## UC-14 — Google sign-in (P1)

Primary actor: Traveler. Secondary actors: Google identity.
Trigger: Google sign-in (P1). Preconditions: P1 enabled; verified identity integration.
Trace: US-17 / FR-AUTH-02 / BIZ-07. Priority: P1.

### Main success flow

1. User obtains provider token.
2. Backend verifies token issuer/audience/subject.
3. User completes deliberate linking when required.
4. System issues owner session.

### Alternatives and exceptions

2a. Invalid token → rejection. 3a. Email collision without linking proof cannot take over account.

### Postconditions and data

Success: Authenticated intended account. Data: verified provider subject; linking proof.

## UC-15 — Import and publish reviewed content

Primary actor: Developer/curator. Secondary actors: none required beyond system dependencies.
Trigger: Import and publish reviewed content. Preconditions: Restricted ingestion access; source/media/narration review.
Trace: US-01 / FR-POI-01 / BIZ-01. Priority: P0.

### Main success flow

1. Curator records sources/rights and checks facts/coordinates.
2. Curator imports draft POI/media/chunks.
3. Validator reports missing/inconsistent fields.
4. Curator approves reviewed version and publishes.

### Alternatives and exceptions

3a. Rights/source/coordinate failure → no publication. Edited source chunks remain excluded until reviewed/reembedded. No public admin endpoint.

### Postconditions and data

Success: Traceable approved corpus. Data: source revision; POI fields; media metadata; embedding config.
