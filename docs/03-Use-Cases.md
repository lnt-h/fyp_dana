# DaNavi — Detailed use cases

Version 1.3 | 2026-10-19 | Status: product scope selected; technical review still required. Document control and evidence status: [Index](00-INDEX.md).

## Boundary and actors

DaNavi includes the mobile app, API and curation workflow; map, Routes, AI, media and identity dependencies are secondary external actors. A guest can Explore, open Detail and play bounded audio previews. Save, Ask and Generate require authentication. The mobile app may hand off directions to Google Maps or Apple Maps but does not become a turn-by-turn navigation system. Curator works through restricted scripts. [Scenarios diagram](diagrams/scenarios-view.drawio) uses actor associations and system boundary; not every relationship needs include/extend.

## Shared contract

Private cases authenticate the caller and verify owner/parent membership. A login gate does not auto-repeat the protected action: after authentication, restore the prior screen/state and require explicit confirmation again. Rejected writes leave existing records unchanged; an uncertain network outcome requires reconciliation using GET before a new action. Provider calls use bounded deadlines. Accessibility applies to all displayed outcomes. Case-specific preconditions and exceptions below take precedence over generic workflow descriptions.

P1 cases UC-12–14 are optional backlog specifications, excluded from P0 delivery and acceptance. UC-15 is a curator CLI workflow, not a traveler-facing administration screen. UC-16–18 are P0 additions for account deletion, external directions reconciliation and trip essentials caching.

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

2a. Invalid input → 400; incorrect credentials/expired refresh → 401. 3a. Rotated-token replay is rejected. Logout revokes refresh session. P0 exposes no password-recovery path and does not promise one.

### Postconditions and data

Success: Authenticated session or revoked logout session. Data: users/sessions; no plain passwords/tokens.

## UC-02 — Search or open published place

Primary actor: Traveler. Secondary actors: none required beyond system dependencies.
Trigger: Search or open published place. Preconditions: Curated published corpus is available.
Trace: US-02 / FR-EXP-01 / BIZ-01; US-03 / FR-PLC-01 / BIZ-01. Priority: P0.

### Main success flow

1. Traveler submits an English/Vietnamese/romanized name, tag or category filter.
2. System returns paginated published matches.
3. Traveler selects a place.
4. System shows facts/sources, images and audio availability.

### Alternatives and exceptions

2a. No match → empty state. 2b. Network error → retry. 4a. Unknown facts remain unknown; missing/unpublished POI → 404. Alias matching opens the same reviewed English content and does not invent a translation.

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

1. Traveler requests save; if unauthenticated, the app opens login and waits for another explicit Save after return.
2. System verifies published place/owner and inserts idempotently.
3. Traveler requests saved list or unsave.
4. System returns/removes only owner rows.

### Alternatives and exceptions

2a. Repeated save creates no duplicate. 4a. Repeated unsave remains successful. Foreign ownership never exposes rows.

### Postconditions and data

Success: Owner saved list reflects intended action. Data: owner and place IDs.

## UC-05 — Create/update trip preferences

Primary actor: Traveler; authenticated traveler for persistence. Secondary actors: location service for the optional current-location shortcut.
Trigger: Create/update trip preferences. Preconditions: The app can hold a local form; a valid session is required before an owner draft is created.
Trace: US-07 / FR-PREF-01 / BIZ-02. Priority: P0.

### Main success flow

1. Traveler supplies a trip date, fixed `dayCount=1`, start point, interests, pace, same-day window and qualitative budget; P0 mode is fixed to `car`.
2. Traveler selects the required start coordinates by map pin, current location or one of 3–4 reviewed presets; the app records `map_pin`, `current_location` or `preset` as source.
3. System validates configured ranges locally before any model call.
4. If authenticated, the system creates or revises the owner draft.

### Alternatives and exceptions

2a. Location denied → map pin and presets remain available. 3a. Invalid date/window/coordinates, `dayCount != 1` or non-`car` mode → field errors; no model call. 4a. A guest keeps the form locally and proceeds to the login gate only when Generate is tapped. 4b. Preferences update only in draft; otherwise 409 preserves the existing plan. Title-only updates use current revision. Old revision → 409.

### Postconditions and data

Success: Validated local preferences, and for an authenticated request a persisted owner draft. Data: TripPreferences; start coordinates/source; title; expectedRevision for edit.

## UC-06 — Build then accept itinerary

Primary actor: Authenticated traveler. Secondary actors: AI and Routes providers.
Trigger: Generate then accept itinerary. Preconditions: Complete validated form; authentication before generation; draft/planned trip, configured limits and current revision for the server request.
Trace: US-08 / FR-TRP-02 / BIZ-02; US-10 / FR-TRP-04 / BIZ-02. Priority: P0.

### Main success flow

1. Traveler requests generation.
2. If the traveler is a guest, the app preserves the completed form, opens login, returns to the form and waits for a second explicit Generate tap.
3. System checks owner/revision/idempotency and loads published candidates.
4. AI proposes IDs/order/durations; backend validates one day and known corpus IDs.
5. Routes resolves `car` legs and the scheduler checks constraints.
6. System stores Preview and shows warnings.
7. Traveler taps **Save & customize**.
8. System revalidates versions and persists the accepted plan atomically; editing is enabled only now.

### Alternatives and exceptions

2a. Login is cancelled/fails → the local form remains and no model call occurs. 4a. Malformed/unknown ID → rejected proposal. 5a. Known conflict → 422/constraints to revise; unknown facts/unavailable route → provisional preview. 4b/5b. Timeout → 503 retaining the old plan. 8a. Expired/stale/changed corpus → 409/422 and regenerate.

### Postconditions and data

Success: Owner accepted one-day plan, ordered stops and `car` route provenance. Data: trip/revision/key; candidate corpus; proposal ID.

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

1. Traveler starts trip and acknowledges any uncertainty/cache warning.
2. System runs UC-18 prefetch and marks the trip active with its first current stop according to the Start contract.
3. Traveler completes/skips the current stop.
4. System atomically activates the next stop or completes the trip.

### Alternatives and exceptions

1a. Invalid state/old revision → 409; empty day/known conflict or missing uncertainty acknowledgement → 422. 2a. Cache failure offers retry or clearly labelled online-only continuation; it does not claim complete. 3a. A completion/skip made offline is visibly pending until reconciliation. Noncurrent or already terminal stop → 409 except exact replay. Pause only stops local watcher; resume reconciles state.

### Postconditions and data

Success: One current stop or completed trip. Data: trip/current stop; revision; acknowledgement/key.

## UC-09 — GPS dwell or manual arrival

Primary actor: Authenticated traveler. Secondary actors: none required beyond system dependencies.
Trigger: **I've arrived** or foreground/resume dwell. Preconditions: Active trip/current stop; foreground watcher for GPS helper.
Trace: US-12 / FR-TRV-02 / BIZ-03. Priority: P0.

### Main success flow

1. Traveler taps **I've arrived**, or the foreground app checks the current-stop target using a fresh report, accuracy and dwell.
2. App sends arrival evidence and stable event key.
3. Backend verifies owner/state/plausibility and deduplicates by stop.
4. App shows arrival method and audio/Ask actions.

### Alternatives and exceptions

1a. Denied/weak GPS → **I've arrived** remains the primary manual path. 2a. Offline → local pending badge/retry; no synced claim. 3a. Wrong stop → conflict; simulation rejected outside demo. 3b. Prior identical event → return original even after progression.

### Postconditions and data

Success: One labelled arrival event; stop not automatically completed. Data: method/time; optional accuracy/distance; demo flag.

## UC-10 — Play audio or opt-in arrival playback

Primary actor: Guest for preview; authenticated traveler for active-trip playback. Secondary actors: Media storage.
Trigger: Play preview/full audio or opt in to arrival playback. Preconditions: Published POI; approved English human audio and applicable rights.
Trace: US-13 / FR-TRV-03 / BIZ-03. Priority: P0.

### Main success flow

1. System obtains reviewed audio metadata, rights and access URL or a valid cached asset.
2. A guest plays only the bounded preview; an authenticated traveler taps full play or opted-in active-trip arrival plays once.
3. Player supports pause/seek/progress/transcript for the allowed asset.

### Alternatives and exceptions

1a. Missing asset/language/offline right → unavailable for that path; no synthesis. 2a. Connection failure → retry/transcript or valid cache. Interruptions update the player; intentional replay is allowed.

### Postconditions and data

Success: Reviewed human audio preview/full asset heard within access/rights rules, or honest unavailable state. Data: place/locale; asset version/duration/transcript/rights/cache revision.

## UC-11 — Ask question

Primary actor: Authenticated traveler. Secondary actors: Embedding/LLM provider.
Trigger: Ask question. Preconditions: Valid session; published place or owned trip context.
Trace: US-14 / FR-AI-01 / BIZ-04. Priority: P0.

### Main success flow

1. Traveler submits a single question and explicit place/trip context; a guest is gated to login before any model call.
2. Backend constructs permitted context and loads facts without accepting client history as conversation memory.
3. System retrieves reviewed compatible chunks.
4. Model drafts sourced answer; backend validates format/IDs/facts.
5. App shows answer and source links.

### Alternatives and exceptions

2a. Foreign trip → 404. 3a. Empty/weak/conflicting evidence → insufficient_evidence. 4a. Unsupported factual output → withheld. Provider timeout → unavailable; injected instructions cannot change allowlist.

### Postconditions and data

Success: Grounded single-turn answer with answer-level source cards, or explicit refusal/failure. Any visible history remains client-only. Data: question; place/trip; locale; source/chunk/fact IDs; no server conversation record.

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

1. Curator records source language, translation review, source/media/offline rights and checks facts/entrance coordinates.
2. Curator imports draft POI/media/chunks.
3. Validator reports missing/inconsistent fields.
4. Curator approves reviewed version and publishes.

### Alternatives and exceptions

3a. Rights/source/coordinate failure → no publication. Edited source chunks remain excluded until reviewed/reembedded. No public admin endpoint.

### Postconditions and data

Success: Traceable approved English-first corpus. Data: source language/revision; translation review; POI fields/aliases; media/offline-rights metadata; embedding config.

## UC-16 — Delete account with reauthentication

Primary actor: Authenticated traveler. Secondary actors: none required beyond system dependencies.
Trigger: Confirm account deletion. Preconditions: Active account/session and access to the current password.
Trace: US-18 / FR-AUTH-03 / BIZ-05. Priority: P0.

### Main success flow

1. Traveler opens account deletion and reads the irreversible-data and retention disclosure.
2. Traveler explicitly confirms and submits the current password.
3. Identity reauthenticates without logging or storing the plain password.
4. System executes the documented deletion transaction/cascades for sessions, trips, trip days/stops, route/day-start legs, arrival events, proposals, saves and idempotency records.
5. App clears local private data/cache, ends the session and returns to the public flow.

### Alternatives and exceptions

2a. User cancels → no write. 3a. Wrong/missing password → reject and keep the account/data unchanged. 4a. Transaction/cascade failure → roll back and do not claim deletion. A user who forgot the password has no P0 recovery/deletion route. Security logs and backups follow the disclosed O-08 policy rather than an unsupported immediate-purge claim.

### Postconditions and data

Success: Owner account/private relational data are no longer active or accessible and all sessions are revoked; retained security-log/backup copies follow O-08. Data: deletion audit metadata without forbidden private payloads, as approved by retention policy.

## UC-17 — Open external directions and reconcile on return

Primary actor: Authenticated traveler. Secondary actors: Google Maps or Apple Maps; location service.
Trigger: Open directions for the current stop. Preconditions: Active trip/current stop and reviewed entrance coordinates.
Trace: US-19 / FR-TRV-04 / BIZ-03. Priority: P0.

### Main success flow

1. DaNavi constructs an HTTPS directions URL for the current stop's reviewed entrance and P0 `car` mode.
2. The OS opens the selected external map app/web experience.
3. When DaNavi returns to foreground, it fetches authoritative trip/current-stop state.
4. It requests a fresh location fix and may run the foreground dwell helper against only that current stop.
5. It presents **I've arrived** as the primary action plus current-stop Audio/Ask/complete/skip actions according to reconciled state.

### Alternatives and exceptions

1a. Missing/invalid entrance → do not hand off; show reviewed location/error. 2a. Open failure → retain in-app route preview and retry/manual options. 3a. Offline → retain last known state labelled stale and queue only permitted pending actions. 4a. Permission denied/weak fix → no automatic arrival; manual **I've arrived** remains available. No background watcher is started.

### Postconditions and data

Success: External directions open without changing trip state, and return uses authoritative current-stop state plus a fresh foreground fix. Data: no provider navigation history required; local lifecycle state and optional location report follow privacy policy.

## UC-18 — Prefetch and use trip essentials cache

Primary actor: Authenticated traveler. Secondary actors: Media/object storage.
Trigger: Start an accepted trip. Preconditions: Accepted one-day trip; known content/itinerary revisions; rights metadata for audio.
Trace: US-20 / FR-OFF-01 / BIZ-03. Priority: P0.

### Main success flow

1. App calculates eligible stop text, transcripts and offline-authorised audio plus total size before/during Start Trip.
2. App prefetches within the configured size limit and shows per-item/overall progress.
3. Cache records the itinerary revision and each content/asset revision.
4. While offline, the app reads only matching cached essentials and labels any complete/skip/arrival write as pending.
5. On connectivity/foreground recovery, the app reconciles server state before marking pending writes synced.

### Alternatives and exceptions

1a. Audio lacks offline rights or exceeds the limit → exclude it with an explanation; text/transcript may continue. 2a. Partial/network/storage failure → show partial state and offer retry or online-only continuation; never label complete. 3a. Itinerary/content revision changes → invalidate the affected entry before use. 4a. Maps and routing are never represented as available offline. 5a. Conflict → fetch authoritative state and ask the user to resolve when automatic idempotent replay is unsafe.

### Postconditions and data

Success: Eligible revision-matched essentials are readable offline and pending mutations are honest. Data: content/asset revision, size, rights flag, cache status and local pending operation key; no offline map/route store.
