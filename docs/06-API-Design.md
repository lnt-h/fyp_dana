# DaNavi — REST API Contract

Version 1.3 | 2026-10-19 | Status: design baseline for review. Document control and evidence status: [Index](00-INDEX.md).

## Contract ownership and boundary

Base path /api/v1. This document owns the reviewed endpoint, DTO, validation, response and semantic contract. A local `openapi.json` may be generated for tooling but is intentionally not tracked. The intended machine-readable format is [OpenAPI 3.0.3](https://spec.openapis.org/oas/v3.0.3.html), not a claim that it is the latest version or that a running API exists.
Public reads expose published English content only and apply an IP-aware public-read rate limit in addition to infrastructure abuse controls. Private endpoints authenticate JWT/session and verify owner plus every nested resource's parent membership before data or provider access. Inaccessible foreign IDs return 404 consistently to avoid disclosure. P1 is excluded from this P0 contract.

## P0 operations

| Method/path | Input or behaviour | Auth |
|---|---|---|
| POST /auth/register | email/password, validation and password hash | Public |
| POST /auth/login | returns access and refresh session | Public |
| POST /auth/refresh | rotates refresh token | Session |
| POST /auth/logout | revokes session | Session |
| POST /account/delete | password reauthentication, explicit confirmation and owner-data cascade | Owner |
| GET /places | q/category/tags/bbox/near/radius/cursor filters | Public |
| GET /places/{id} | facts with provenance, media, audio availability | Public |
| GET /saved | caller saves | Owner |
| PUT /saved/{placeId} | idempotent save published place | Owner |
| DELETE /saved/{placeId} | idempotent unsave | Owner |
| POST /trips | preferences and dates → draft trip | Owner |
| GET /trips | caller trips | Owner |
| GET /trips/{id} | aggregate, revision, stops, route status | Owner |
| PATCH /trips/{id} | constraints/title with expectedRevision | Owner |
| POST /trips/{id}/build | expectedRevision → proposal and warnings, synchronous 200 | Owner |
| POST /trips/{id}/proposals/{pid}/accept | expectedRevision; revalidate publication/expiry → planned trip | Owner |
| POST /trips/{id}/stops | placeId/dayId/position/duration/expectedRevision | Owner |
| PATCH /trips/{id}/stops/{sid} | duration/day change with expectedRevision | Owner |
| DELETE /trips/{id}/stops/{sid} | expectedRevision | Owner |
| PUT /trips/{id}/days/{dayId}/stops/order | complete orderedStopIds + expectedRevision | Owner |
| GET /trips/{id}/route | legs/polyline/freshness, nullable unavailable durations | Owner |
| POST /trips/{id}/route/refresh | expectedRevision → route or unavailable | Owner |
| POST /trips/{id}/start | expectedRevision; confirm provisional warnings | Owner |
| POST /trips/{id}/stops/{sid}/arrivals | method/time and GPS quality evidence if gps | Owner |
| POST /trips/{id}/stops/{sid}/complete | transition current stop; activate next | Owner |
| POST /trips/{id}/stops/{sid}/skip | transition current stop; activate next | Owner |
| GET /places/{id}/audio-guide | locale → approved asset metadata/URL/offline-rights metadata, or audio_unavailable; guest playback is preview-bounded by client/media policy | Public |
| POST /ai/ask | question, placeId and/or owned tripId, locale | User |

## HTTP and errors

Success: register/create-trip 201; save/unsave/logout/account-delete 204 without body; other operations 200. Provider_unavailable is HTTP503 with Error, not a successful Ask response. Build may return 200 provisional for route-only failure when model/constraint validation succeeds. Route refresh failure returns 503; GET shows reconciled unavailable/stale data.
Error shape: code, message, optional details, requestId. Never return stack traces/provider secrets. 400 malformed input; 401 invalid session or failed reauthentication; 404 absent/inaccessible resource; 409 state/revision/key mismatch; 422 known constraint or invalid model output; 426 app version below the supported minimum; 429 quota; 500 safe unexpected error; 503 dependency failure. Simulation outside demo is 403. Responses are specified per operation rather than listing irrelevant errors on every endpoint.
Stable error codes include validation_error, unauthenticated, reauthentication_failed, not_found, revision_conflict, state_conflict, idempotency_mismatch, request_in_progress, proposal_expired, invalid_proposal, constraint_violation, client_version_unsupported, quota_exceeded, provider_unavailable and simulation_disabled. A retryable error includes a safe explanation; HTTP429 uses Retry-After when known. Dynamic limits must be visible in validation details without exposing secrets.

## Client/API compatibility contract

Every mobile request sends `X-DaNavi-App-Version` as a semantic version. The API returns `X-DaNavi-API-Version` and `X-DaNavi-Min-App-Version`. A client older than the configured minimum receives HTTP426 with `client_version_unsupported`, safe upgrade details and no provider/mutation work. Version comparison and rollout configuration are server-owned; documentation does not invent the minimum value. Web/curation callers use an explicitly identified client and the same reviewed compatibility policy. The OpenAPI component defines these reusable headers; implementation must bind them across operations and contract tests.

## Identity

Register accepts normalised email and the configured 12–128-character password proposal; no truncation. Login verifies supplied credentials without applying a registration minimum that rejects existing passwords. Password hash algorithm/parameters require a trial. JWT carries subject and session identifier; protected requests validate signature/issuer/audience/expiry plus session owner/not-revoked/not-expired. Refresh rotates the stored token hash atomically; simultaneous use of the old token cannot create two valid replacements. Logout takes the refresh token, revokes the matching session, and is idempotent for a well-formed already-revoked/unknown token. It discloses no account existence.

`POST /account/delete` accepts `password` plus `confirmation="DELETE"`; it requires a valid session and fresh password reauthentication. The transaction deletes the user and cascades sessions, trips, trip_days, trip_stops, route_legs, day_start_legs, arrival_events, itinerary_proposals, saved_places and idempotency_records. On failure it rolls back and never reports success. Security-log/backup retention follows O-08 and is disclosed separately; the endpoint does not claim immediate physical backup purge. P0 has no password recovery, so a user who cannot reauthenticate cannot delete through the app.

## Pagination, filtering and locale

Default limit 20/max50. Places sort by normalised name then ID; trips and saved records sort newest-first with ID tie-breakers. Cursor binds the caller where private, filters, locale and ordering; invalid/mismatched cursor is 400. Cursor pagination is not snapshot isolation: document behavior if curated records change between pages.
Search normalises Unicode/case, removes Vietnamese diacritics and maps `đ` to `d`; it matches reviewed English names, Vietnamese names, alias arrays and romanization. Test accented/unaccented aliases, the four categories, tags and unpublished exclusions. Category uses `Culture`, `Beach`, `Food` or `Nature`; urban places use Culture plus tags. Comma-separated tags use AND matching. `bbox` is west,south,east,north with ordered bounded coordinates. `near` is lat,lng with positive radius metres. `bbox` and `near` are mutually exclusive; near/radius must be paired. Public search/list/detail receive IP-aware quotas and HTTP429 with Retry-After when known.
locale accepts vi/en for forward compatibility and defaults to `en`. P0 returns reviewed English content; Vietnamese names and romanization are search aliases, not a Vietnamese content fallback. If a non-English locale has no reviewed content, return a typed availability state without substituting unreviewed translation. Audio never silently falls back language. Ask P0 accepts `en`; `locale_unavailable` is retired for the English request. Sources expose `sourceLanguage`; reviewed English translation metadata links to origin and review status.

## Trip semantics

Create returns draft/revision0. Preferences contain startDate, `dayCount=1`, startPoint, `startPointSource`, optional `startPointPresetId`, interests, pace, dailyStart/dailyEnd, qualitative budgetPreference and `transportMode=car`. Source is `map_pin`, `current_location` or `preset`; `preset` requires a reviewed preset ID matching the coordinates. `dailyStart < dailyEnd` within one local day; dates use Asia/Ho_Chi_Minh. Budget is not a numeric guaranteed cost. Maximum stop/duration limits remain configured after O-04; the retained `trip_days` schema does not expose multi-day P0 requests.
PATCH requires at least title or preferences plus expectedRevision. Preferences can change only in draft; otherwise 409 preserves the accepted plan. Title can change in any state with revision. Draft has no required stop/day records. Stop edits require planned/active; completed/current prefix is fixed during active travel. Removing the last stop of a planned day persists the explicit edit but creates a blocking empty_day warning.
Build returns proposalId/baseRevision/status(valid|provisional)/expiresAt/days/warnings/routeStatus/modelVersion/corpusVersion. Nonempty days use published unique candidate IDs. Known infeasibility returns 422, not a valid preview. Accept is invoked by **Save & customize**, rechecks owner/trip/revision/expiry/fact versions and creates a planned aggregate atomically; stop edits are rejected before acceptance. Start requires nonempty stops, no severity=error warnings and acknowledgement of uncertainty/cache warnings; otherwise 422/409. Travel progression requires expectedRevision; arrival has its own unique event contract and does not advance progression revision.
Warnings include code/message/severity and optional placeId. routeStatus fresh does not imply complete feasibility. [Blueprint](12-Blueprint.md) owns the complete action matrix.

## Routing and schedule

The P0 day has an explicit start-to-first-stop leg; inter-stop legs connect stops within that day. Proposal startLeg references toPlaceId; persisted startLeg references dayId/toStopId. GET route returns dayStartLegs and inter-stop legs. Provider duration/distance/fetchedAt/`car`/revision are recorded; no LLM travel estimates. Stale/unavailable responses use null estimates and no current polyline. Provider attribution/warnings must be preserved; caching/retention must follow approved provider terms.
Edit response marks affected routes/ETAs stale. Refresh runs outside the trip transaction and applies only to the same revision; older concurrent results cannot replace newer results. The server can project expired persisted legs as stale/null on GET without mutating the database. [Google Compute Routes](https://developers.google.com/maps/documentation/routes/compute-route-over) is the integration reference; supported regional behavior and terms must be verified during trial. The mobile app constructs Google/Apple Maps HTTPS directions from the reviewed entrance; no new navigation endpoint or offline-route contract is added.

## Arrival and media

GPS requires detectedAt, accuracyMeters, distanceMeters and dwellSeconds. Manual/simulated methods make no GPS claim. **I've arrived** uses `manual` and is the primary path. GPS reports are accepted only for current-stop foreground/resume fixes within configured age/plausibility; simulation requires demo mode. No continuous location endpoint/history is included. External-map return first GETs the trip/current stop, then obtains a fresh device fix. A pending local report is not synced until acknowledged.
Audio available requires URL/urlExpiresAt/duration/transcript/version/human_recorded type plus asset revision, bytes and `offlineCacheAllowed`. Expiry is null only for an approved nonexpiring URL; unavailable has no URL. Missing POI is 404; missing guide/language returns 200 unavailable. URL expiry is separate from asset availability: refresh metadata on expired access URL. GET guide never enqueues synthesis. Exact event replay must not start another automatic playback. Guest preview duration/access is client/media policy; full active-trip caching is allowed only when metadata grants offline use.

## Trip essentials cache

No cache-specific server mutation or offline route/map endpoint is added. At Start Trip, mobile reuses `GET /trips/{id}`, `GET /places/{id}` and `GET /places/{id}/audio-guide` to prefetch accepted-stop English text, transcripts and authorised audio. It stores trip/place/asset revisions and invalidates mismatches. Partial download is reported honestly; offline Complete/Skip/Arrival remains a locally pending mutation until the server confirms its original idempotency key.

## Revision and idempotency

Required Idempotency-Key: create trip, build, accept, start, arrival, complete and skip. Before the first send, mobile persists the key, endpoint/resource IDs, canonical request hash/payload reference and pending state in protected local storage; suspend/kill recovery restores and reconciles it. Owner/path/key scope and canonical request hash are durable server-side. Authenticate access before replay. Same request returns the original outcome; mismatched payload is 409; in-progress is typed 409. New intent/new retry after failure uses a new key after reconciliation; a network/process retry uses the original key. Deadline/recovery and expired media semantics are in Blueprint. Client GET/reconciles after timeout or stale replay response.
PATCH/add-stop/reorder/delete-stop use expectedRevision to prevent repeat mutation; save/unsave use natural idempotency. DELETE stop places revision in the query. Read/build-preview/route-refresh do not increment itinerary revision; trip/progress mutations do. No 202/polling job contract exists in P0.

## Ask response

Ask requires authentication, an English question plus placeId and/or owned tripId; when both exist, place must belong to permitted trip context. `question` is nonblank and bounded. The request is single-turn and has no conversation/history field; any visible history is client-only. Context validation precedes embedding/model calls. A grounded response contains the answer, answer-level supporting source cards/citations and/or factReferences, and requestId. `insufficient_evidence` contains an English explanation with empty evidence arrays and no unsupported factual answer. A verified citation ID is necessary but does not establish claim entailment; held-out evaluation assesses support. Claim-level citation presentation is stretch.
Example below is a schema fixture, not a POI fact or measured model response:
```json
{
  "status": "insufficient_evidence",
  "answer": "The reviewed sources do not contain enough evidence to answer this question.",
  "citations": [],
  "factReferences": [],
  "requestId": "fixture-request-001"
}
```

## Optional backlog and evolution

P1 extensions (Google identity, private landmark uploads/recognition and editable STT) have FR/US/UC identifiers but require a new reviewed API/media lifecycle before activation. Their earlier endpoint sketches are not part of the mandatory contract. No collections, weather, taste jobs or TTS endpoints.
Add optional fields compatibly; breaking changes require a new API major version and migration notice. Reconcile generated implementation OpenAPI with this design and run real request/schema tests before acceptance. Design JSON validation alone cannot prove authentication, transaction or model behavior.
